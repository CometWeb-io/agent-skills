"""v1 → v2 ledger migration."""
from __future__ import annotations

import json
from typing import Any, Dict, Tuple

from .constants import (
    ADMISSION_STATUSES,
    CLAIM_STATUSES,
    CONFIDENCE_LEVELS,
    CONTRADICTION_RESOLUTIONS,
    FIT_LEVELS,
    MATERIALITIES,
    MEASUREMENT_LEVELS,
    SCHEMA_VERSION,
    SOURCE_CLASSES,
    SOURCE_ROLES,
)
from .identity import make_id


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
            "contradiction_tested": False,
            "legacy_contradiction_tested": c.get("contradiction_tested") is True,
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
            "requires_live_verification": row.get("requires_live_verification") is True,
            "verified_for_research": False,
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
        if claim.get("legacy_contradiction_tested"):
            cid = str(claim.get("claim_id"))
            searches.append({
                "search_id": make_id("search", f"legacy-falsifier|{cid}"),
                "claim_id": cid,
                "purpose": "FALSIFIER",
                "source_lane": "PUBLIC",
                "query_summary": "Migrated v1 contradiction_tested flag; original query unavailable",
                "completed": False,
                "completed_at": None,
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

