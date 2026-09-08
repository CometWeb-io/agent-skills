#!/usr/bin/env python3
"""Deterministic kernel for Evidence Researcher v2.

The kernel validates and audits evidence packs. It never discovers facts or decides
whether a source is substantively true; those remain model/tool responsibilities.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

VERSION = "2.0.0"
SCHEMA_VERSION = "2.0"
POLICY_VERSION = "evidence-policy-v2"

TRACKING_KEYS = {
    "fbclid", "gclid", "dclid", "msclkid", "mc_cid", "mc_eid", "ref", "ref_src",
}

CLAIM_TYPES = {
    "law_regulation", "regulatory_guidance", "security_advisory", "vendor_policy",
    "competitor_pricing", "official_technical_docs", "repository_behavior",
    "internal_metric", "internal_process_state", "company_announcement", "market_metric",
    "academic_evidence", "historical_fact", "current_fact", "product_behavior",
    "qualitative_experience", "doctrine_framework", "service_status", "dataset_fact",
}

LIVE_VERIFICATION_TYPES = {
    "law_regulation", "regulatory_guidance", "security_advisory", "vendor_policy",
    "competitor_pricing", "internal_metric", "internal_process_state", "service_status",
}

DEFAULT_TTL_DAYS = {
    "law_regulation": 0,
    "regulatory_guidance": 0,
    "security_advisory": 0,
    "vendor_policy": 7,
    "competitor_pricing": 3,
    "internal_metric": 1,
    "internal_process_state": 1,
    "service_status": 0,
    "official_technical_docs": 30,
    "repository_behavior": 30,
    "company_announcement": 30,
    "market_metric": 30,
    "current_fact": 7,
    "product_behavior": 30,
    "qualitative_experience": 90,
    "academic_evidence": 365,
    "dataset_fact": 365,
    "historical_fact": 3650,
    "doctrine_framework": 3650,
}

MATERIALITIES = {"critical", "material", "supporting"}
TEMPORAL_SENSITIVITIES = {"high", "medium", "low", "static"}
EPISTEMIC_KINDS = {"FACT", "INFERENCE"}
CLAIM_STATUSES = {
    "VERIFIED", "SUPPORTED_INFERENCE", "PARTIAL", "UNSUPPORTED", "CONTRADICTED", "UNKNOWN"
}
CONFIDENCE_LEVELS = {"high", "medium", "low"}
SOURCE_CLASSES = {
    "LIVE_WEB", "PRIVATE_KNOWLEDGE", "USER_FILE", "REPOSITORY", "DATABASE_SYSTEM_OF_RECORD",
    "ACADEMIC_SOURCE", "HUMAN_EXPERT_EVIDENCE", "DECISION_MEMORY", "FRAMEWORK",
}
SOURCE_ROLES = {"SYSTEM_OF_RECORD", "PRIMARY", "OFFICIAL", "SECONDARY", "AGGREGATOR", "EXPERT", "DOCTRINE"}
PROVENANCE_LANES = {"PUBLIC", "PRIVATE", "USER_SUPPLIED"}
ADMISSION_STATUSES = {"ACCEPTED", "CONTEXT_ONLY", "REJECTED"}
DIRECTIONS = {"SUPPORT", "CONTRADICT", "CONTEXT"}
FIT_LEVELS = {"high", "medium", "low", "unknown"}
MEASUREMENT_LEVELS = {"high", "medium", "low", "unknown", "not_applicable"}
TEMPORAL_STATUSES = {"CURRENT", "NEAR_EXPIRY", "STALE", "SUPERSEDED", "DRAFT", "NOT_YET_EFFECTIVE", "UNKNOWN"}
RESEARCH_STATUSES = {"READY", "PARTIAL", "REFRESH_REQUIRED", "BLOCKED_BY_CONTRADICTION"}
SEARCH_PURPOSES = {"SUPPORT", "FALSIFIER", "RETRACTION", "VERSION", "NEGATIVE_CASE", "ABSENCE_TEST", "LINEAGE"}
FALSIFIER_PURPOSES = {"FALSIFIER", "RETRACTION", "VERSION", "NEGATIVE_CASE", "ABSENCE_TEST"}
SEARCH_LANES = {"PUBLIC", "PRIVATE", "USER_SUPPLIED", "REPOSITORY", "DATABASE", "HUMAN"}
CONTRADICTION_RESOLUTIONS = {
    "RESOLVED_SCOPE", "RESOLVED_TIME", "RESOLVED_DEFINITION", "RESOLVED_METHOD",
    "RESOLVED_SUPERSEDED", "RESOLVED_AUTHORITY", "UNRESOLVED",
}
PRIMARY_ROLES = {"PRIMARY", "OFFICIAL", "SYSTEM_OF_RECORD"}


def _json_dump(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))


def _load_json(value: str) -> Any:
    path = Path(value)
    if path.exists() and path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return json.loads(value)


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    return dt if dt.tzinfo is not None else None


def _norm_text(value: Any) -> str:
    return " ".join(str(value or "").strip().casefold().split())


def canonical_url(url: str) -> str:
    parts = urlsplit(url.strip())
    filtered: List[Tuple[str, str]] = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        low = key.casefold()
        if low.startswith("utm_") or low in TRACKING_KEYS:
            continue
        filtered.append((key, value))
    filtered.sort(key=lambda item: (item[0], item[1]))
    scheme = parts.scheme.lower()
    netloc = parts.netloc.lower()
    path = parts.path or "/"
    query = urlencode(filtered, doseq=True)
    return urlunsplit((scheme, netloc, path, query, ""))


def make_id(kind: str, value: str) -> str:
    prefixes = {
        "research": "res", "claim": "clm", "source": "src", "evidence": "ev",
        "contradiction": "ctr", "search": "srch", "gap": "gap", "watch": "watch",
    }
    if kind not in prefixes:
        raise ValueError(f"unsupported kind: {kind}")
    digest = hashlib.sha256(_norm_text(value).encode("utf-8")).hexdigest()[:12]
    return f"{prefixes[kind]}_{digest}"


def source_policy(claim_type: str) -> Dict[str, Any]:
    return {
        "claim_type": claim_type,
        "default_ttl_days": DEFAULT_TTL_DAYS.get(claim_type),
        "requires_live_verification": claim_type in LIVE_VERIFICATION_TYPES,
        "known_claim_type": claim_type in CLAIM_TYPES,
        "policy_version": POLICY_VERSION,
    }


def temporal_status(source: Dict[str, Any], as_of_text: str, claim_type: Optional[str] = None) -> Dict[str, Any]:
    as_of = _parse_dt(as_of_text)
    if as_of is None:
        return {"temporal_status": "UNKNOWN", "reason": "as_of must be timezone-aware ISO 8601", "policy_version": POLICY_VERSION}

    ctype = str(claim_type or source.get("claim_type") or "current_fact")
    state = str(source.get("source_state") or "final").strip().casefold()

    if source.get("superseded_by_source_id") or source.get("superseded_by") or state in {"superseded", "withdrawn"}:
        return {"temporal_status": "SUPERSEDED", "reason": "source is superseded or withdrawn", "policy_version": POLICY_VERSION}
    if state == "draft":
        return {"temporal_status": "DRAFT", "reason": "source_state is draft", "policy_version": POLICY_VERSION}

    parsed: Dict[str, Optional[datetime]] = {}
    for field in ("published_at", "effective_from", "effective_to", "last_verified_at", "expires_at"):
        parsed[field] = _parse_dt(source.get(field))
        if source.get(field) and parsed[field] is None:
            return {"temporal_status": "UNKNOWN", "reason": f"invalid {field}", "policy_version": POLICY_VERSION}

    published_at = parsed["published_at"]
    effective_from = parsed["effective_from"]
    effective_to = parsed["effective_to"]
    last_verified = parsed["last_verified_at"]
    expires_at = parsed["expires_at"]

    if effective_from and effective_from > as_of:
        return {"temporal_status": "NOT_YET_EFFECTIVE", "reason": "effective_from is after as_of", "policy_version": POLICY_VERSION}
    if effective_to and effective_to < as_of:
        return {"temporal_status": "STALE", "reason": "effective_to is before as_of", "policy_version": POLICY_VERSION}
    if published_at and published_at > as_of:
        return {"temporal_status": "UNKNOWN", "reason": "published_at is after as_of", "policy_version": POLICY_VERSION}
    if expires_at and expires_at < as_of:
        return {"temporal_status": "STALE", "reason": "expires_at is before as_of", "policy_version": POLICY_VERSION}
    if last_verified and last_verified > as_of + timedelta(minutes=5):
        return {"temporal_status": "UNKNOWN", "reason": "last_verified_at is materially after as_of", "policy_version": POLICY_VERSION}

    requires_live = bool(source.get("requires_live_verification")) or ctype in LIVE_VERIFICATION_TYPES
    if requires_live:
        if not source.get("verified_for_research"):
            return {
                "temporal_status": "UNKNOWN",
                "reason": "live verification required but verified_for_research is not true",
                "requires_live_verification": True,
                "policy_version": POLICY_VERSION,
            }
        if last_verified is None:
            return {
                "temporal_status": "UNKNOWN",
                "reason": "live verification requires last_verified_at",
                "requires_live_verification": True,
                "policy_version": POLICY_VERSION,
            }
        return {
            "temporal_status": "CURRENT",
            "reason": "live authority inspected for this research run",
            "requires_live_verification": True,
            "policy_version": POLICY_VERSION,
        }

    ttl_days = source.get("freshness_ttl_days")
    if ttl_days is None:
        ttl_days = DEFAULT_TTL_DAYS.get(ctype)
    if ttl_days is None:
        if last_verified is None:
            return {"temporal_status": "UNKNOWN", "reason": "no freshness policy and no last_verified_at", "policy_version": POLICY_VERSION}
        return {"temporal_status": "CURRENT", "reason": "verified and no stricter freshness policy applies", "policy_version": POLICY_VERSION}

    try:
        ttl = float(ttl_days)
    except (TypeError, ValueError):
        return {"temporal_status": "UNKNOWN", "reason": "invalid freshness_ttl_days", "policy_version": POLICY_VERSION}
    if last_verified is None:
        return {"temporal_status": "UNKNOWN", "reason": "last_verified_at required by freshness policy", "policy_version": POLICY_VERSION}

    expiry = last_verified + timedelta(days=max(ttl, 0.0))
    if as_of > expiry:
        return {
            "temporal_status": "STALE", "reason": "verification age exceeds freshness policy",
            "computed_expires_at": expiry.isoformat(), "policy_version": POLICY_VERSION,
        }
    if ttl > 0 and as_of >= last_verified + timedelta(days=ttl * 0.8):
        return {
            "temporal_status": "NEAR_EXPIRY", "reason": "verification is within final 20 percent of freshness window",
            "computed_expires_at": expiry.isoformat(), "policy_version": POLICY_VERSION,
        }
    return {
        "temporal_status": "CURRENT", "reason": "verification is within freshness policy",
        "computed_expires_at": expiry.isoformat(), "policy_version": POLICY_VERSION,
    }


def fingerprint_source(source: Dict[str, Any]) -> str:
    key = "|".join([
        _norm_text(source.get("canonical_ref")),
        _norm_text(source.get("source_version")),
        _norm_text(source.get("content_hash")),
        _norm_text(source.get("title")),
    ])
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def pack_hash(ledger: Dict[str, Any]) -> str:
    clean = copy.deepcopy(ledger)
    for field in ("pack_hash", "research_status", "stop_reason"):
        clean.pop(field, None)
    payload = json.dumps(clean, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _id_index(rows: Iterable[Dict[str, Any]], field: str) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        value = row.get(field)
        if isinstance(value, str) and value:
            out[value] = row
    return out


def _claim_needs_freshness(claim: Dict[str, Any]) -> bool:
    if claim.get("temporal_sensitivity") in {"high", "medium"}:
        return True
    return claim.get("claim_type") not in {"historical_fact", "doctrine_framework"} and claim.get("temporal_sensitivity") != "static"


def _dependency_cycles(claims: List[Dict[str, Any]]) -> List[List[str]]:
    graph = {str(c.get("claim_id")): [str(x) for x in c.get("depends_on_claim_ids", [])] for c in claims if c.get("claim_id")}
    cycles: List[List[str]] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def dfs(node: str, stack: List[str]) -> None:
        if node in visiting:
            try:
                start = stack.index(node)
                cycle = stack[start:] + [node]
            except ValueError:
                cycle = [node, node]
            if cycle not in cycles:
                cycles.append(cycle)
            return
        if node in visited:
            return
        visiting.add(node)
        stack.append(node)
        for nxt in graph.get(node, []):
            if nxt in graph:
                dfs(nxt, stack)
        stack.pop()
        visiting.remove(node)
        visited.add(node)

    for node in graph:
        dfs(node, [])
    return cycles


def _source_lineage_cycles(sources: List[Dict[str, Any]]) -> List[List[str]]:
    graph = {str(s.get("source_id")): [str(x) for x in s.get("derived_from_source_ids", [])] for s in sources if s.get("source_id")}
    cycles: List[List[str]] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def dfs(node: str, stack: List[str]) -> None:
        if node in visiting:
            try:
                start = stack.index(node)
                cycle = stack[start:] + [node]
            except ValueError:
                cycle = [node, node]
            if cycle not in cycles:
                cycles.append(cycle)
            return
        if node in visited:
            return
        visiting.add(node)
        stack.append(node)
        for nxt in graph.get(node, []):
            if nxt in graph:
                dfs(nxt, stack)
        stack.pop()
        visiting.remove(node)
        visited.add(node)

    for node in graph:
        dfs(node, [])
    return cycles


def validate_ledger(ledger: Dict[str, Any]) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []
    if not isinstance(ledger, dict):
        return {"valid": False, "errors": ["ledger root must be an object"], "warnings": [], "kernel_version": VERSION}

    if str(ledger.get("schema_version") or "") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}; use migrate-v1 for v1 ledgers")

    contract = ledger.get("research_contract")
    if not isinstance(contract, dict):
        errors.append("research_contract must be an object")
        contract = {}
    if not contract.get("question"):
        errors.append("research_contract.question is required")
    if contract.get("mode") not in {"QUICK", "STANDARD", "DEEP"}:
        errors.append("research_contract.mode must be QUICK, STANDARD, or DEEP")
    if contract.get("privacy_lane") and contract.get("privacy_lane") not in PROVENANCE_LANES:
        errors.append("research_contract.privacy_lane is invalid")
    if not ledger.get("research_id"):
        errors.append("research_id is required")

    claims = ledger.get("claims", [])
    sources = ledger.get("sources", [])
    evidence = ledger.get("evidence", [])
    contradictions = ledger.get("contradictions", [])
    searches = ledger.get("searches", [])
    gaps = ledger.get("gaps", [])
    for name, rows in (("claims", claims), ("sources", sources), ("evidence", evidence), ("contradictions", contradictions), ("searches", searches), ("gaps", gaps)):
        if not isinstance(rows, list):
            errors.append(f"{name} must be a list")
    claims = claims if isinstance(claims, list) else []
    sources = sources if isinstance(sources, list) else []
    evidence = evidence if isinstance(evidence, list) else []
    contradictions = contradictions if isinstance(contradictions, list) else []
    searches = searches if isinstance(searches, list) else []
    gaps = gaps if isinstance(gaps, list) else []

    id_specs = [
        (claims, "claim_id", "claim"), (sources, "source_id", "source"), (evidence, "evidence_id", "evidence"),
        (contradictions, "contradiction_id", "contradiction"), (searches, "search_id", "search"), (gaps, "gap_id", "gap"),
    ]
    ids_by_kind: Dict[str, set[str]] = {}
    for rows, field, kind in id_specs:
        seen: set[str] = set()
        for i, row in enumerate(rows):
            if not isinstance(row, dict):
                errors.append(f"{kind}s[{i}] must be an object")
                continue
            value = row.get(field)
            if not value:
                errors.append(f"{kind}s[{i}].{field} is required")
            elif str(value) in seen:
                errors.append(f"duplicate {field}: {value}")
            else:
                seen.add(str(value))
        ids_by_kind[kind] = seen

    claim_ids = ids_by_kind.get("claim", set())
    source_ids = ids_by_kind.get("source", set())
    evidence_ids = ids_by_kind.get("evidence", set())

    for i, claim in enumerate(claims):
        if not isinstance(claim, dict):
            continue
        cid = claim.get("claim_id") or f"claims[{i}]"
        if not claim.get("claim_text"):
            errors.append(f"{cid}.claim_text is required")
        ctype = claim.get("claim_type")
        if not ctype:
            errors.append(f"{cid}.claim_type is required")
        elif ctype not in CLAIM_TYPES:
            warnings.append(f"{cid} uses unregistered claim_type {ctype}; define authority/freshness explicitly")
        if claim.get("materiality") not in MATERIALITIES:
            errors.append(f"{cid}.materiality is invalid")
        if claim.get("temporal_sensitivity") not in TEMPORAL_SENSITIVITIES:
            errors.append(f"{cid}.temporal_sensitivity is invalid")
        epistemic = claim.get("epistemic_kind")
        if epistemic not in EPISTEMIC_KINDS:
            errors.append(f"{cid}.epistemic_kind must be FACT or INFERENCE")
        status = claim.get("status")
        if status not in CLAIM_STATUSES:
            errors.append(f"{cid}.status is invalid")
        if claim.get("confidence") not in CONFIDENCE_LEVELS:
            errors.append(f"{cid}.confidence must be high, medium, or low")
        deps = claim.get("depends_on_claim_ids", [])
        if not isinstance(deps, list):
            errors.append(f"{cid}.depends_on_claim_ids must be a list")
            deps = []
        for dep in deps:
            if dep not in claim_ids:
                errors.append(f"{cid} depends on unknown claim_id {dep}")
            if dep == claim.get("claim_id"):
                errors.append(f"{cid} cannot depend on itself")
        if epistemic == "FACT" and status == "SUPPORTED_INFERENCE":
            errors.append(f"{cid} is FACT but uses SUPPORTED_INFERENCE status")
        if epistemic == "INFERENCE":
            if status == "VERIFIED":
                errors.append(f"{cid} is INFERENCE and cannot be marked VERIFIED")
            if status == "SUPPORTED_INFERENCE" and not deps:
                errors.append(f"{cid} is SUPPORTED_INFERENCE without dependencies")

    for cycle in _dependency_cycles([c for c in claims if isinstance(c, dict)]):
        errors.append("claim dependency cycle: " + " -> ".join(cycle))

    source_fingerprints: Dict[str, List[str]] = {}
    canonical_groups: Dict[str, set[str]] = {}
    for i, source in enumerate(sources):
        if not isinstance(source, dict):
            continue
        sid = source.get("source_id") or f"sources[{i}]"
        if not source.get("title"):
            errors.append(f"{sid}.title is required")
        if not source.get("canonical_ref"):
            errors.append(f"{sid}.canonical_ref is required")
        if source.get("source_class") not in SOURCE_CLASSES:
            errors.append(f"{sid}.source_class is invalid")
        if source.get("source_role") not in SOURCE_ROLES:
            errors.append(f"{sid}.source_role is invalid")
        if source.get("provenance_lane") not in PROVENANCE_LANES:
            errors.append(f"{sid}.provenance_lane is invalid")
        derived = source.get("derived_from_source_ids", [])
        if not isinstance(derived, list):
            errors.append(f"{sid}.derived_from_source_ids must be a list")
            derived = []
        for parent in derived:
            if parent not in source_ids:
                errors.append(f"{sid} derives from unknown source_id {parent}")
            if parent == source.get("source_id"):
                errors.append(f"{sid} cannot derive from itself")
        fp = fingerprint_source(source)
        source_fingerprints.setdefault(fp, []).append(str(source.get("source_id")))
        cref = _norm_text(source.get("canonical_ref"))
        if cref:
            canonical_groups.setdefault(cref, set()).add(str(source.get("independence_group") or ""))

    for cycle in _source_lineage_cycles([src for src in sources if isinstance(src, dict)]):
        errors.append("source lineage cycle: " + " -> ".join(cycle))

    for fp, sids in source_fingerprints.items():
        if len(sids) > 1:
            warnings.append(f"duplicate source fingerprint across source_ids: {', '.join(sorted(sids))}")
    for cref, groups in canonical_groups.items():
        nonempty = {g for g in groups if g}
        if len(nonempty) > 1:
            warnings.append(f"same canonical_ref assigned to multiple independence groups: {cref}")

    accepted_support_by_claim: Dict[str, List[Dict[str, Any]]] = {}
    accepted_contradict_by_claim: Dict[str, List[Dict[str, Any]]] = {}
    for i, edge in enumerate(evidence):
        if not isinstance(edge, dict):
            continue
        eid = edge.get("evidence_id") or f"evidence[{i}]"
        cid = edge.get("claim_id")
        sid = edge.get("source_id")
        if cid not in claim_ids:
            errors.append(f"{eid} references unknown claim_id {cid}")
        if sid not in source_ids:
            errors.append(f"{eid} references unknown source_id {sid}")
        if edge.get("direction") not in DIRECTIONS:
            errors.append(f"{eid}.direction is invalid")
        if edge.get("admission") not in ADMISSION_STATUSES:
            errors.append(f"{eid}.admission is invalid")
        if edge.get("authority_fit") not in FIT_LEVELS:
            errors.append(f"{eid}.authority_fit is invalid")
        if edge.get("directness") not in FIT_LEVELS:
            errors.append(f"{eid}.directness is invalid")
        if edge.get("scope_fit") not in FIT_LEVELS:
            errors.append(f"{eid}.scope_fit is invalid")
        if edge.get("measurement_quality") not in MEASUREMENT_LEVELS:
            errors.append(f"{eid}.measurement_quality is invalid")
        if edge.get("direction") == "CONTEXT" and edge.get("admission") == "ACCEPTED":
            errors.append(f"{eid} is CONTEXT but marked ACCEPTED; use CONTEXT_ONLY")
        if edge.get("admission") == "CONTEXT_ONLY" and edge.get("direction") != "CONTEXT":
            warnings.append(f"{eid} is CONTEXT_ONLY but direction is not CONTEXT")
        if edge.get("admission") == "ACCEPTED" and not edge.get("locator"):
            warnings.append(f"{eid} is ACCEPTED without a pinpoint locator")
        if edge.get("admission") == "ACCEPTED" and edge.get("direction") in {"SUPPORT", "CONTRADICT"}:
            if edge.get("authority_fit") == "unknown" or edge.get("directness") == "unknown":
                warnings.append(f"{eid} accepted without explicit authority/directness assessment")
        if edge.get("admission") == "ACCEPTED" and cid in claim_ids:
            if edge.get("direction") == "SUPPORT":
                accepted_support_by_claim.setdefault(str(cid), []).append(edge)
            elif edge.get("direction") == "CONTRADICT":
                accepted_contradict_by_claim.setdefault(str(cid), []).append(edge)

    completed_falsifier_claims: set[str] = set()
    for i, search in enumerate(searches):
        if not isinstance(search, dict):
            continue
        sid = search.get("search_id") or f"searches[{i}]"
        cid = search.get("claim_id")
        if cid not in claim_ids:
            errors.append(f"{sid} references unknown claim_id {cid}")
        if search.get("purpose") not in SEARCH_PURPOSES:
            errors.append(f"{sid}.purpose is invalid")
        if search.get("source_lane") not in SEARCH_LANES:
            errors.append(f"{sid}.source_lane is invalid")
        if not isinstance(search.get("completed"), bool):
            errors.append(f"{sid}.completed must be boolean")
        result_ids = search.get("result_source_ids", [])
        if not isinstance(result_ids, list):
            errors.append(f"{sid}.result_source_ids must be a list")
            result_ids = []
        for source_id in result_ids:
            if source_id not in source_ids:
                errors.append(f"{sid} references unknown result source_id {source_id}")
        if search.get("purpose") == "ABSENCE_TEST":
            basis = search.get("absence_basis")
            if not isinstance(basis, dict) or not basis.get("expected_location") or not basis.get("detection_logic") or not basis.get("coverage_limitations"):
                errors.append(f"{sid} ABSENCE_TEST requires expected_location, detection_logic, and coverage_limitations")
        if contract.get("privacy_lane") in {"PRIVATE", "USER_SUPPLIED"} and search.get("source_lane") == "PUBLIC":
            if search.get("sanitized_for_external") is not True:
                errors.append(f"{sid} public search from a non-public research lane must set sanitized_for_external=true")
        if search.get("completed") and search.get("purpose") in FALSIFIER_PURPOSES and cid in claim_ids:
            completed_falsifier_claims.add(str(cid))

    for claim in claims:
        if not isinstance(claim, dict):
            continue
        cid = str(claim.get("claim_id") or "")
        if claim.get("materiality") in {"critical", "material"}:
            if claim.get("contradiction_tested") and cid not in completed_falsifier_claims:
                errors.append(f"{cid} says contradiction_tested=true without a completed falsifier search record")
            if not claim.get("contradiction_tested"):
                warnings.append(f"{cid} has no contradiction search coverage")
        if claim.get("epistemic_kind") == "FACT" and claim.get("status") == "VERIFIED" and claim.get("materiality") in {"critical", "material"}:
            if not accepted_support_by_claim.get(cid):
                errors.append(f"{cid} is VERIFIED without ACCEPTED SUPPORT evidence")

    evidence_by_id = _id_index([e for e in evidence if isinstance(e, dict)], "evidence_id")
    contradiction_claim_ids: set[str] = set()
    for i, row in enumerate(contradictions):
        if not isinstance(row, dict):
            continue
        xid = row.get("contradiction_id") or f"contradictions[{i}]"
        cid = row.get("claim_id")
        if cid in claim_ids:
            contradiction_claim_ids.add(str(cid))
        if cid not in claim_ids:
            errors.append(f"{xid} references unknown claim_id {cid}")
        if row.get("resolution") not in CONTRADICTION_RESOLUTIONS:
            errors.append(f"{xid}.resolution is invalid")
        if row.get("severity") not in MATERIALITIES:
            errors.append(f"{xid}.severity is invalid")
        eids = row.get("evidence_ids", [])
        if not isinstance(eids, list):
            errors.append(f"{xid}.evidence_ids must be a list")
            eids = []
        for eid in eids:
            edge = evidence_by_id.get(eid)
            if not edge:
                errors.append(f"{xid} references unknown evidence_id {eid}")
            elif edge.get("claim_id") != cid:
                errors.append(f"{xid} references evidence {eid} tied to a different claim")

    for cid, edges in accepted_contradict_by_claim.items():
        if edges and cid not in contradiction_claim_ids:
            errors.append(f"{cid} has ACCEPTED CONTRADICT evidence without a contradiction record")

    for i, gap in enumerate(gaps):
        if not isinstance(gap, dict):
            continue
        gid = gap.get("gap_id") or f"gaps[{i}]"
        cid = gap.get("claim_id")
        if cid and cid not in claim_ids:
            errors.append(f"{gid} references unknown claim_id {cid}")
        if gap.get("severity") not in {"critical", "material", "minor"}:
            errors.append(f"{gid}.severity is invalid")
        if not gap.get("what_closes_it"):
            warnings.append(f"{gid} has no what_closes_it")

    current_material = [
        c for c in claims if isinstance(c, dict) and c.get("materiality") in {"critical", "material"} and _claim_needs_freshness(c)
    ]
    if current_material and _parse_dt(contract.get("as_of")) is None:
        errors.append("timezone-aware research_contract.as_of is required for material time-sensitive claims")

    return {
        "valid": not errors,
        "errors": sorted(set(errors)),
        "warnings": sorted(set(warnings)),
        "schema_version": SCHEMA_VERSION,
        "kernel_version": VERSION,
        "policy_version": POLICY_VERSION,
    }


def _accepted_edges_for_claim(evidence: List[Dict[str, Any]], claim_id: str, direction: str) -> List[Dict[str, Any]]:
    return [
        e for e in evidence
        if e.get("claim_id") == claim_id and e.get("direction") == direction and e.get("admission") == "ACCEPTED"
    ]


def _falsifier_searches(searches: List[Dict[str, Any]], claim_id: str) -> List[Dict[str, Any]]:
    return [s for s in searches if s.get("claim_id") == claim_id and s.get("completed") and s.get("purpose") in FALSIFIER_PURPOSES]


def _support_freshness(
    claim: Dict[str, Any],
    support_edges: List[Dict[str, Any]],
    sources_by_id: Dict[str, Dict[str, Any]],
    as_of: Optional[str],
) -> Tuple[bool, List[Dict[str, Any]], int]:
    if claim.get("epistemic_kind") == "INFERENCE" or not _claim_needs_freshness(claim):
        return True, [], 0
    if not as_of:
        return False, [], 0
    checks: List[Dict[str, Any]] = []
    admissible_count = 0
    stale_accepted_count = 0
    for edge in support_edges:
        source = sources_by_id.get(str(edge.get("source_id")))
        if not source:
            continue
        result = temporal_status(source, as_of, str(claim.get("claim_type") or "current_fact"))
        status = result.get("temporal_status")
        checks.append({"evidence_id": edge.get("evidence_id"), "source_id": source.get("source_id"), **result})
        if status in {"CURRENT", "NEAR_EXPIRY"} and edge.get("authority_fit") in {"high", "medium"}:
            admissible_count += 1
        elif status not in {"CURRENT", "NEAR_EXPIRY"}:
            stale_accepted_count += 1
    return admissible_count > 0, checks, stale_accepted_count


def coverage(ledger: Dict[str, Any]) -> Dict[str, Any]:
    contract = ledger.get("research_contract") if isinstance(ledger.get("research_contract"), dict) else {}
    claims = [c for c in ledger.get("claims", []) if isinstance(c, dict)]
    sources = [s for s in ledger.get("sources", []) if isinstance(s, dict)]
    evidence = [e for e in ledger.get("evidence", []) if isinstance(e, dict)]
    searches = [s for s in ledger.get("searches", []) if isinstance(s, dict)]
    contradictions = [c for c in ledger.get("contradictions", []) if isinstance(c, dict)]
    gaps = [g for g in ledger.get("gaps", []) if isinstance(g, dict)]
    sources_by_id = _id_index(sources, "source_id")
    claims_by_id = _id_index(claims, "claim_id")
    as_of = contract.get("as_of")

    material_claims = [c for c in claims if c.get("materiality") in {"critical", "material"}]
    critical_claims = [c for c in material_claims if c.get("materiality") == "critical"]

    claim_rows: List[Dict[str, Any]] = []
    fact_ready = inference_ready = accepted_support_count = primary_count = falsifier_count = freshness_count = 0
    authority_count = 0
    all_independence_groups: set[str] = set()
    unknown_independence_edges = 0

    for claim in material_claims:
        cid = str(claim.get("claim_id") or "")
        support_edges = _accepted_edges_for_claim(evidence, cid, "SUPPORT")
        contradict_edges = _accepted_edges_for_claim(evidence, cid, "CONTRADICT")
        support_sources = [sources_by_id.get(str(e.get("source_id"))) for e in support_edges]
        support_sources = [s for s in support_sources if s]
        has_primary = any(s.get("source_role") in PRIMARY_ROLES for s in support_sources)
        has_authority = any(e.get("authority_fit") in {"high", "medium"} and e.get("directness") in {"high", "medium"} for e in support_edges)
        falsifiers = _falsifier_searches(searches, cid)
        freshness_ok, temporal_checks, stale_supports = _support_freshness(claim, support_edges, sources_by_id, as_of)
        groups = set()
        unknown_groups = 0
        for source in support_sources:
            group = str(source.get("independence_group") or "").strip()
            if group:
                groups.add(group)
                all_independence_groups.add(group)
            else:
                unknown_groups += 1
                unknown_independence_edges += 1

        dep_ids = [str(x) for x in claim.get("depends_on_claim_ids", [])]
        deps_ready = all(
            claims_by_id.get(dep, {}).get("status") in {"VERIFIED", "SUPPORTED_INFERENCE"}
            for dep in dep_ids
        ) if dep_ids else False

        if claim.get("epistemic_kind") == "FACT":
            ready = claim.get("status") == "VERIFIED" and bool(support_edges) and has_authority and freshness_ok and bool(falsifiers) and bool(claim.get("contradiction_tested"))
            if ready:
                fact_ready += 1
        else:
            ready = claim.get("status") == "SUPPORTED_INFERENCE" and deps_ready and bool(falsifiers) and bool(claim.get("contradiction_tested"))
            if ready:
                inference_ready += 1

        if support_edges:
            accepted_support_count += 1
        if has_primary:
            primary_count += 1
        if has_authority:
            authority_count += 1
        if falsifiers:
            falsifier_count += 1
        if freshness_ok:
            freshness_count += 1

        claim_rows.append({
            "claim_id": cid,
            "materiality": claim.get("materiality"),
            "epistemic_kind": claim.get("epistemic_kind"),
            "status": claim.get("status"),
            "ready": ready,
            "accepted_support": bool(support_edges),
            "accepted_contradiction_count": len(contradict_edges),
            "authority_admissible_support": has_authority,
            "primary_or_system_of_record_support": has_primary,
            "falsifier_search_completed": bool(falsifiers),
            "falsifier_search_count": len(falsifiers),
            "freshness_admissible": freshness_ok,
            "stale_or_unknown_accepted_support_count": stale_supports,
            "temporal_checks": temporal_checks,
            "independence_group_count": len(groups),
            "unknown_independence_support_count": unknown_groups,
            "dependencies_ready": deps_ready if claim.get("epistemic_kind") == "INFERENCE" else None,
        })

    critical_ids = {str(c.get("claim_id")) for c in critical_claims}
    material_ids = {str(c.get("claim_id")) for c in material_claims}
    unresolved_critical = []
    unresolved_material = []
    for row in contradictions:
        if row.get("resolution") != "UNRESOLVED":
            continue
        cid = str(row.get("claim_id") or "")
        if cid in critical_ids:
            unresolved_critical.append(row.get("contradiction_id"))
        elif cid in material_ids:
            unresolved_material.append(row.get("contradiction_id"))

    critical_gaps = [g.get("gap_id") for g in gaps if g.get("severity") == "critical"]
    material_gaps = [g.get("gap_id") for g in gaps if g.get("severity") == "material"]

    def rate(n: int, d: int) -> Optional[float]:
        return round(n / d, 4) if d else None

    ready_count = sum(1 for row in claim_rows if row["ready"])
    return {
        "material_claim_count": len(material_claims),
        "critical_claim_count": len(critical_claims),
        "material_ready_rate": rate(ready_count, len(material_claims)),
        "accepted_support_rate": rate(accepted_support_count, len(material_claims)),
        "authority_admissible_rate": rate(authority_count, len(material_claims)),
        "primary_or_system_of_record_rate": rate(primary_count, len(material_claims)),
        "contradiction_test_rate": rate(falsifier_count, len(material_claims)),
        "freshness_admissible_rate": rate(freshness_count, len(material_claims)),
        "accepted_independence_group_count": len(all_independence_groups),
        "unknown_independence_support_count": unknown_independence_edges,
        "unresolved_critical_contradictions": unresolved_critical,
        "unresolved_material_contradictions": unresolved_material,
        "critical_gaps": critical_gaps,
        "material_gaps": material_gaps,
        "claims": claim_rows,
        "schema_version": SCHEMA_VERSION,
        "kernel_version": VERSION,
        "policy_version": POLICY_VERSION,
    }


def audit(ledger: Dict[str, Any]) -> Dict[str, Any]:
    validation = validate_ledger(ledger)
    cov = coverage(ledger)

    if cov["unresolved_critical_contradictions"]:
        status = "BLOCKED_BY_CONTRADICTION"
        reason = "critical unresolved contradiction"
    else:
        freshness_fail = any(
            row["epistemic_kind"] == "FACT" and not row["freshness_admissible"]
            for row in cov["claims"]
        )
        if freshness_fail:
            status = "REFRESH_REQUIRED"
            reason = "material time-sensitive claim lacks fresh admissible support"
        elif not validation["valid"]:
            status = "PARTIAL"
            reason = "ledger validity is incomplete"
        elif cov["unresolved_material_contradictions"]:
            status = "PARTIAL"
            reason = "material unresolved contradiction remains"
        elif cov["critical_gaps"]:
            status = "PARTIAL"
            reason = "critical evidence gap remains open"
        elif any(not row["ready"] for row in cov["claims"]):
            status = "PARTIAL"
            reason = "one or more material claims do not satisfy the evidence gate"
        else:
            status = "READY"
            reason = "material evidence gate satisfied"

    return {
        "research_status": status,
        "reason": reason,
        "validation": validation,
        "coverage": cov,
        "pack_hash": pack_hash(ledger),
        "schema_version": SCHEMA_VERSION,
        "kernel_version": VERSION,
        "policy_version": POLICY_VERSION,
    }


def refresh_plan(ledger: Dict[str, Any]) -> Dict[str, Any]:
    contract = ledger.get("research_contract") if isinstance(ledger.get("research_contract"), dict) else {}
    as_of = contract.get("as_of")
    claims = [c for c in ledger.get("claims", []) if isinstance(c, dict) and c.get("materiality") in {"critical", "material"}]
    sources = [s for s in ledger.get("sources", []) if isinstance(s, dict)]
    evidence = [e for e in ledger.get("evidence", []) if isinstance(e, dict)]
    sources_by_id = _id_index(sources, "source_id")
    items = []
    seen = set()
    for claim in claims:
        cid = str(claim.get("claim_id") or "")
        if claim.get("epistemic_kind") != "FACT" or not _claim_needs_freshness(claim):
            continue
        for edge in _accepted_edges_for_claim(evidence, cid, "SUPPORT"):
            source = sources_by_id.get(str(edge.get("source_id")))
            if not source or not as_of:
                continue
            key = (cid, str(source.get("source_id")))
            if key in seen:
                continue
            seen.add(key)
            result = temporal_status(source, as_of, str(claim.get("claim_type") or "current_fact"))
            status = result.get("temporal_status")
            items.append({
                "claim_id": cid,
                "source_id": source.get("source_id"),
                "temporal_status": status,
                "action": (
                    "REFRESH_NOW" if status in {"STALE", "SUPERSEDED", "DRAFT", "NOT_YET_EFFECTIVE", "UNKNOWN"}
                    else "REFRESH_SOON" if status == "NEAR_EXPIRY"
                    else "REVERIFY_ON_NEXT_MATERIAL_RUN" if str(claim.get("claim_type")) in LIVE_VERIFICATION_TYPES
                    else "NO_ACTION"
                ),
                "computed_expires_at": result.get("computed_expires_at"),
                "reason": result.get("reason"),
            })
    return {
        "as_of": as_of,
        "refresh_required": any(i["action"] == "REFRESH_NOW" for i in items),
        "refresh_soon": any(i["action"] == "REFRESH_SOON" for i in items),
        "items": items,
        "kernel_version": VERSION,
    }


def delta(old: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    old_claims = _id_index([c for c in old.get("claims", []) if isinstance(c, dict)], "claim_id")
    new_claims = _id_index([c for c in new.get("claims", []) if isinstance(c, dict)], "claim_id")
    old_sources = [s for s in old.get("sources", []) if isinstance(s, dict)]
    new_sources = [s for s in new.get("sources", []) if isinstance(s, dict)]
    old_by_fp = {fingerprint_source(s): s for s in old_sources}
    new_by_fp = {fingerprint_source(s): s for s in new_sources}

    added_claims = sorted(set(new_claims) - set(old_claims))
    removed_claims = sorted(set(old_claims) - set(new_claims))
    changed_claims = []
    for cid in sorted(set(old_claims) & set(new_claims)):
        before = old_claims[cid]
        after = new_claims[cid]
        changes = {}
        for field in ("claim_text", "claim_type", "materiality", "status", "confidence"):
            if before.get(field) != after.get(field):
                changes[field] = {"old": before.get(field), "new": after.get(field)}
        if changes:
            changed_claims.append({"claim_id": cid, "changes": changes})

    added_sources = [new_by_fp[fp].get("source_id") for fp in sorted(set(new_by_fp) - set(old_by_fp))]
    removed_sources = [old_by_fp[fp].get("source_id") for fp in sorted(set(old_by_fp) - set(new_by_fp))]
    old_by_ref = {_norm_text(s.get("canonical_ref")): s for s in old_sources if s.get("canonical_ref")}
    new_by_ref = {_norm_text(s.get("canonical_ref")): s for s in new_sources if s.get("canonical_ref")}
    source_version_changes = []
    for ref in sorted(set(old_by_ref) & set(new_by_ref)):
        before = old_by_ref[ref].get("source_version")
        after = new_by_ref[ref].get("source_version")
        if before != after:
            source_version_changes.append({"canonical_ref": new_by_ref[ref].get("canonical_ref"), "old": before, "new": after})

    old_ctr = _id_index([c for c in old.get("contradictions", []) if isinstance(c, dict)], "contradiction_id")
    new_ctr = _id_index([c for c in new.get("contradictions", []) if isinstance(c, dict)], "contradiction_id")
    contradiction_changes = []
    for cid in sorted(set(old_ctr) & set(new_ctr)):
        if old_ctr[cid].get("resolution") != new_ctr[cid].get("resolution"):
            contradiction_changes.append({
                "contradiction_id": cid,
                "old": old_ctr[cid].get("resolution"),
                "new": new_ctr[cid].get("resolution"),
            })

    return {
        "old_pack_hash": pack_hash(old),
        "new_pack_hash": pack_hash(new),
        "added_claim_ids": added_claims,
        "removed_claim_ids": removed_claims,
        "changed_claims": changed_claims,
        "added_source_ids": added_sources,
        "removed_source_ids": removed_sources,
        "source_version_changes": source_version_changes,
        "contradiction_resolution_changes": contradiction_changes,
        "kernel_version": VERSION,
    }


def _legacy_fit(value: Any) -> str:
    if isinstance(value, str) and value in FIT_LEVELS:
        return value
    if isinstance(value, dict):
        vals = [str(v) for v in value.values() if isinstance(v, str)]
        if any(v == "low" for v in vals):
            return "low"
        if any(v == "medium" for v in vals):
            return "medium"
        if vals and all(v in {"high", "not_applicable"} for v in vals):
            return "high"
    return "unknown"


def _legacy_measurement(value: Any) -> str:
    if isinstance(value, str) and value in MEASUREMENT_LEVELS:
        return value
    return "unknown"


def migrate_v1(old: Dict[str, Any]) -> Dict[str, Any]:
    if str(old.get("schema_version") or "").startswith("2") or old.get("research_contract"):
        raise ValueError("input already appears to be v2")
    question = str(old.get("research_question") or "")
    as_of = str(old.get("as_of") or "")
    mode = str(old.get("mode") or "STANDARD")
    research_id = make_id("research", f"{question}|{as_of}|{mode}")

    claims = []
    for c in old.get("claims", []):
        if not isinstance(c, dict):
            continue
        claims.append({
            "claim_id": c.get("claim_id") or make_id("claim", str(c.get("claim_text") or "")),
            "claim_text": c.get("claim_text"),
            "claim_type": c.get("claim_type") or "current_fact",
            "materiality": c.get("materiality") or "supporting",
            "epistemic_kind": "FACT",
            "temporal_sensitivity": c.get("temporal_sensitivity") or "low",
            "scope": c.get("scope") or {},
            "depends_on_claim_ids": [],
            "contradiction_tested": bool(c.get("contradiction_tested")),
            "status": c.get("status") if c.get("status") in CLAIM_STATUSES else "UNKNOWN",
            "confidence": c.get("confidence") if c.get("confidence") in CONFIDENCE_LEVELS else "low",
            "notes": c.get("notes"),
        })

    sources = []
    edges = []
    old_edge_map: Dict[Tuple[str, str, str], str] = {}
    for row in old.get("evidence", []):
        if not isinstance(row, dict):
            continue
        old_eid = str(row.get("evidence_id") or make_id("evidence", json.dumps(row, sort_keys=True)))
        canonical_ref = row.get("canonical_url") or row.get("source_ref") or f"legacy:{old_eid}"
        source_id = make_id("source", f"{canonical_ref}|{row.get('source_version') or ''}|{row.get('title') or ''}")
        source = {
            "source_id": source_id,
            "title": row.get("title") or old_eid,
            "canonical_ref": canonical_ref,
            "source_class": row.get("source_class") if row.get("source_class") in SOURCE_CLASSES else "LIVE_WEB",
            "source_role": row.get("source_role") if row.get("source_role") in SOURCE_ROLES else "SECONDARY",
            "provenance_lane": "PRIVATE" if row.get("source_class") in {"PRIVATE_KNOWLEDGE", "DATABASE_SYSTEM_OF_RECORD"} else "USER_SUPPLIED" if row.get("source_class") == "USER_FILE" else "PUBLIC",
            "independence_group": row.get("independence_group"),
            "independence_confidence": row.get("independence_confidence"),
            "source_state": row.get("source_state") or "final",
            "published_at": row.get("published_at"),
            "effective_from": row.get("effective_from"),
            "effective_to": row.get("effective_to"),
            "last_verified_at": row.get("last_verified_at"),
            "expires_at": row.get("expires_at"),
            "source_version": row.get("source_version"),
            "superseded_by_source_id": None,
            "requires_live_verification": bool(row.get("requires_live_verification")),
            "verified_for_research": bool(row.get("verified_for_research")),
            "freshness_ttl_days": row.get("freshness_ttl_days"),
            "derived_from_source_ids": [],
            "content_hash": row.get("content_hash"),
            "notes": row.get("notes"),
        }
        if not any(s.get("source_id") == source_id for s in sources):
            sources.append(source)

        for direction, field in (("SUPPORT", "supports_claim_ids"), ("CONTRADICT", "contradicts_claim_ids")):
            for cid in row.get(field, []) or []:
                edge_id = make_id("evidence", f"{old_eid}|{cid}|{direction}")
                old_edge_map[(old_eid, str(cid), direction)] = edge_id
                edges.append({
                    "evidence_id": edge_id,
                    "claim_id": cid,
                    "source_id": source_id,
                    "direction": direction,
                    "locator": row.get("locator") or "legacy-row",
                    "evidence_form": row.get("evidence_form") or "paraphrase",
                    "summary": row.get("summary") or row.get("notes"),
                    "authority_fit": _legacy_fit(row.get("authority_fit")),
                    "directness": _legacy_fit(row.get("directness")),
                    "scope_fit": _legacy_fit(row.get("scope_fit")),
                    "measurement_quality": _legacy_measurement(row.get("measurement_quality")),
                    "admission": row.get("admission") if row.get("admission") in ADMISSION_STATUSES else "CONTEXT_ONLY",
                    "notes": f"migrated from {old_eid}",
                })

    searches = []
    for claim in claims:
        if claim.get("contradiction_tested"):
            cid = str(claim.get("claim_id"))
            searches.append({
                "search_id": make_id("search", f"legacy-falsifier|{cid}"),
                "claim_id": cid,
                "purpose": "FALSIFIER",
                "source_lane": "PUBLIC",
                "query_summary": "Migrated v1 contradiction_tested flag; original query unavailable",
                "completed": True,
                "completed_at": as_of or None,
                "result_source_ids": [],
                "novelty_count": None,
                "notes": "Migration shim only; rerun falsifier search for high-stakes use.",
            })

    contradictions = []
    for row in old.get("contradictions", []):
        if not isinstance(row, dict):
            continue
        cid = str(row.get("claim_id") or "")
        migrated_ids = []
        for old_eid in row.get("evidence_ids", []) or []:
            for direction in ("SUPPORT", "CONTRADICT"):
                eid = old_edge_map.get((str(old_eid), cid, direction))
                if eid:
                    migrated_ids.append(eid)
        contradictions.append({
            "contradiction_id": row.get("contradiction_id") or make_id("contradiction", f"{cid}|{migrated_ids}"),
            "claim_id": cid,
            "evidence_ids": migrated_ids,
            "type": row.get("type") or "unknown",
            "severity": row.get("severity") if row.get("severity") in MATERIALITIES else "material",
            "resolution": row.get("resolution") if row.get("resolution") in CONTRADICTION_RESOLUTIONS else "UNRESOLVED",
            "explanation": row.get("explanation"),
            "resolution_basis_evidence_ids": [],
        })

    gaps = []
    for i, row in enumerate(old.get("gaps", [])):
        if isinstance(row, dict):
            gap = dict(row)
            gap.setdefault("gap_id", make_id("gap", f"legacy|{i}|{json.dumps(row, sort_keys=True)}"))
            gap.setdefault("severity", "material")
            gap.setdefault("gap_type", "other")
            gap.setdefault("what_closes_it", "Re-evaluate migrated gap")
        else:
            gap = {
                "gap_id": make_id("gap", f"legacy|{i}|{row}"), "claim_id": None, "severity": "material",
                "gap_type": "other", "description": str(row), "what_closes_it": "Re-evaluate migrated gap",
            }
        gaps.append(gap)

    return {
        "schema_version": SCHEMA_VERSION,
        "research_id": research_id,
        "research_contract": {
            "question": question,
            "objective": None,
            "scope": old.get("scope") or {},
            "as_of": as_of,
            "mode": mode if mode in {"QUICK", "STANDARD", "DEEP"} else "STANDARD",
            "consumers": [],
            "constraints": [],
            "known_facts": [],
            "known_unknowns": [],
            "privacy_lane": "PUBLIC",
        },
        "claims": claims,
        "sources": sources,
        "evidence": edges,
        "contradictions": contradictions,
        "searches": searches,
        "gaps": gaps,
        "research_status": "PARTIAL",
        "stop_reason": "migrated_from_v1_requires_review",
        "migration": {"from": "1.x", "to": SCHEMA_VERSION, "warning": "legacy contradiction searches were not reconstructable"},
    }


def stop_decision(ledger: Dict[str, Any], no_novelty_rounds: int, expected_information_gain: float, research_cost: float) -> Dict[str, Any]:
    result = audit(ledger)
    if result["research_status"] != "READY":
        return {
            "stop": False,
            "reason": f"research gate is {result['research_status']}",
            "research_status": result["research_status"],
            "kernel_version": VERSION,
        }
    saturation = int(no_novelty_rounds) >= 2
    voi_exhausted = float(expected_information_gain) <= float(research_cost)
    if saturation or voi_exhausted:
        return {
            "stop": True,
            "reason": "evidence gate is ready and marginal research value is exhausted",
            "saturation": saturation,
            "voi_exhausted": voi_exhausted,
            "kernel_version": VERSION,
        }
    return {
        "stop": False,
        "reason": "evidence gate is ready but another bounded research round may still add value",
        "saturation": saturation,
        "voi_exhausted": voi_exhausted,
        "kernel_version": VERSION,
    }


def template(question: str, as_of: str, mode: str) -> Dict[str, Any]:
    research_id = make_id("research", f"{question}|{as_of}|{mode}")
    return {
        "schema_version": SCHEMA_VERSION,
        "research_id": research_id,
        "research_contract": {
            "question": question,
            "objective": None,
            "scope": {},
            "as_of": as_of,
            "mode": mode,
            "consumers": [],
            "constraints": [],
            "known_facts": [],
            "known_unknowns": [],
            "privacy_lane": "PUBLIC",
        },
        "claims": [],
        "sources": [],
        "evidence": [],
        "contradictions": [],
        "searches": [],
        "gaps": [],
        "research_status": "PARTIAL",
        "stop_reason": None,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evidence Researcher deterministic kernel v2")
    parser.add_argument("--version", action="version", version=VERSION)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("canonical-url")
    p.add_argument("--url", required=True)

    p = sub.add_parser("make-id")
    p.add_argument("--kind", choices=["research", "claim", "source", "evidence", "contradiction", "search", "gap", "watch"], required=True)
    p.add_argument("--value", required=True)

    p = sub.add_parser("source-policy")
    p.add_argument("--claim-type", required=True)

    p = sub.add_parser("temporal")
    p.add_argument("--source-json", required=True)
    p.add_argument("--as-of", required=True)
    p.add_argument("--claim-type")

    p = sub.add_parser("fingerprint-source")
    p.add_argument("--source-json", required=True)

    p = sub.add_parser("pack-hash")
    p.add_argument("--ledger-json", required=True)

    for name in ("validate", "coverage", "audit", "refresh-plan", "migrate-v1"):
        p = sub.add_parser(name)
        p.add_argument("--ledger-json", required=True)

    p = sub.add_parser("delta")
    p.add_argument("--old-ledger-json", required=True)
    p.add_argument("--new-ledger-json", required=True)

    p = sub.add_parser("stop")
    p.add_argument("--ledger-json", required=True)
    p.add_argument("--no-novelty-rounds", type=int, default=0)
    p.add_argument("--expected-information-gain", type=float, default=1.0)
    p.add_argument("--research-cost", type=float, default=0.0)

    p = sub.add_parser("template")
    p.add_argument("--question", required=True)
    p.add_argument("--as-of", required=True)
    p.add_argument("--mode", choices=["QUICK", "STANDARD", "DEEP"], default="STANDARD")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.command == "canonical-url":
            print(canonical_url(args.url))
        elif args.command == "make-id":
            print(make_id(args.kind, args.value))
        elif args.command == "source-policy":
            _json_dump(source_policy(args.claim_type))
        elif args.command == "temporal":
            _json_dump(temporal_status(_load_json(args.source_json), args.as_of, args.claim_type))
        elif args.command == "fingerprint-source":
            print(fingerprint_source(_load_json(args.source_json)))
        elif args.command == "pack-hash":
            print(pack_hash(_load_json(args.ledger_json)))
        elif args.command == "validate":
            _json_dump(validate_ledger(_load_json(args.ledger_json)))
        elif args.command == "coverage":
            _json_dump(coverage(_load_json(args.ledger_json)))
        elif args.command == "audit":
            _json_dump(audit(_load_json(args.ledger_json)))
        elif args.command == "refresh-plan":
            _json_dump(refresh_plan(_load_json(args.ledger_json)))
        elif args.command == "migrate-v1":
            _json_dump(migrate_v1(_load_json(args.ledger_json)))
        elif args.command == "delta":
            _json_dump(delta(_load_json(args.old_ledger_json), _load_json(args.new_ledger_json)))
        elif args.command == "stop":
            _json_dump(stop_decision(_load_json(args.ledger_json), args.no_novelty_rounds, args.expected_information_gain, args.research_cost))
        elif args.command == "template":
            _json_dump(template(args.question, args.as_of, args.mode))
        else:
            parser.error("unsupported command")
    except (ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
