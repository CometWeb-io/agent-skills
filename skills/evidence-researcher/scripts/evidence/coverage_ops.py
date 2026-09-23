"""Coverage scoring and related evidence helpers."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from .constants import (
    FALSIFIER_PURPOSES,
    POLICY_VERSION,
    PRIMARY_ROLES,
    SCHEMA_VERSION,
    VERSION,
)
from .temporal_eval import temporal_status
from .util import _claim_needs_freshness, _id_index, _parse_dt


def _accepted_edges_for_claim(evidence: List[Dict[str, Any]], claim_id: str, direction: str) -> List[Dict[str, Any]]:
    return [
        e for e in evidence
        if e.get("claim_id") == claim_id and e.get("direction") == direction and e.get("admission") == "ACCEPTED"
    ]


def _falsifier_searches(searches: List[Dict[str, Any]], claim_id: str, as_of: Optional[str] = None) -> List[Dict[str, Any]]:
    clock = _parse_dt(as_of)
    return [s for s in searches if s.get("claim_id") == claim_id and s.get("completed") is True
            and s.get("purpose") in FALSIFIER_PURPOSES
            and isinstance(s.get("query_summary"), str) and s["query_summary"].strip()
            and _parse_dt(s.get("completed_at")) is not None and clock is not None
            and _parse_dt(s["completed_at"]) <= clock]


def _edge_quality(edge: Dict[str, Any]) -> bool:
    """All dimensions must hold on the same evidence edge, not across a mixture."""
    return (all(edge.get(field) in {"high", "medium"} for field in ("authority_fit", "directness", "scope_fit"))
            and edge.get("measurement_quality") in {"high", "medium", "not_applicable"}
            and isinstance(edge.get("locator"), str) and bool(edge["locator"].strip()))


def _independence_components(sources: List[Dict[str, Any]]) -> Dict[str, str]:
    """Collapse declared lineage and identical references; do not certify independence."""
    parents = {s["source_id"]: s["source_id"] for s in sources if isinstance(s.get("source_id"), str)}
    def find(sid):
        while parents[sid] != sid:
            parents[sid] = parents[parents[sid]]
            sid = parents[sid]
        return sid
    def join(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parents[max(ra, rb)] = min(ra, rb)
    seen = {}
    for source in sources:
        sid = source.get("source_id")
        if sid not in parents:
            continue
        for field in ("independence_group", "canonical_ref", "content_hash"):
            value = source.get(field)
            if not isinstance(value, str) or not value.strip():
                continue
            key = (field, value.strip())
            if key in seen:
                join(sid, seen[key])
            else:
                seen[key] = sid
        for prior in source.get("derived_from_source_ids", []):
            if prior in parents:
                join(sid, prior)
    return {sid: find(sid) for sid in parents}


def _support_freshness(
    claim: Dict[str, Any],
    support_edges: List[Dict[str, Any]],
    sources_by_id: Dict[str, Dict[str, Any]],
    as_of: Optional[str],
    research_id: Optional[str] = None,
    research_started_at: Optional[str] = None,
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
        result = temporal_status(source, as_of, str(claim.get("claim_type") or "current_fact"), research_id=research_id, research_started_at=research_started_at)
        status = result.get("temporal_status")
        checks.append({"evidence_id": edge.get("evidence_id"), "source_id": source.get("source_id"), **result})
        if status in {"CURRENT", "NEAR_EXPIRY"} and _edge_quality(edge):
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
    as_of = contract.get("as_of")

    material_claims = [c for c in claims if c.get("materiality") in {"critical", "material"}]
    critical_claims = [c for c in material_claims if c.get("materiality") == "critical"]

    claim_rows: List[Dict[str, Any]] = []
    accepted_support_count = primary_count = falsifier_count = freshness_count = 0
    authority_count = 0
    all_independence_groups: set[str] = set()
    unknown_independence_edges = 0

    components = _independence_components(sources)
    relevant_gaps = {g.get("claim_id") for g in gaps if g.get("severity") in {"critical", "material"}}
    unresolved_ids = {c.get("claim_id") for c in contradictions if c.get("resolution") == "UNRESOLVED"}
    all_rows = {}
    for claim in claims:
        cid = str(claim.get("claim_id") or "")
        support_edges = _accepted_edges_for_claim(evidence, cid, "SUPPORT")
        contradict_edges = _accepted_edges_for_claim(evidence, cid, "CONTRADICT")
        support_sources = [sources_by_id.get(str(e.get("source_id"))) for e in support_edges]
        support_sources = [s for s in support_sources if s]
        has_primary = any(s.get("source_role") in PRIMARY_ROLES for s in support_sources)
        has_authority = any(_edge_quality(e) for e in support_edges)
        falsifiers = _falsifier_searches(searches, cid, as_of)
        freshness_ok, temporal_checks, stale_supports = _support_freshness(claim, support_edges, sources_by_id, as_of, ledger.get("research_id"), contract.get("started_at"))
        groups = set()
        unknown_groups = 0
        for source in support_sources:
            group = str(source.get("independence_group") or "").strip()
            if group:
                groups.add(components[source["source_id"]])
                if claim.get("materiality") in {"critical", "material"}:
                    all_independence_groups.add(components[source["source_id"]])
            else:
                unknown_groups += 1
                if claim.get("materiality") in {"critical", "material"}:
                    unknown_independence_edges += 1

        dep_ids = [str(x) for x in claim.get("depends_on_claim_ids", [])]
        falsifier_ok = bool(falsifiers) and claim.get("contradiction_tested") is True
        # Supporting facts need evidence too; a falsifier is mandatory when material.
        requires_falsifier = claim.get("materiality") in {"critical", "material"}
        local_gate = (falsifier_ok or not requires_falsifier) and cid not in relevant_gaps and cid not in unresolved_ids
        ready = (claim.get("epistemic_kind") == "FACT" and claim.get("status") == "VERIFIED"
                 and bool(support_edges) and has_authority and freshness_ok and local_gate)
        deps_ready = False
        all_rows[cid] = {"ready": ready, "dependency_ids": dep_ids, "local_gate": local_gate,
                         "inference": claim.get("epistemic_kind") == "INFERENCE",
                         "status": claim.get("status")}
        if claim.get("materiality") not in {"critical", "material"}:
            continue

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

    # No recursion limit and no promotion from nominal VERIFIED labels alone.
    # Cycles and missing dependencies never enter the ready set.
    ready_ids = {cid for cid, row in all_rows.items() if row["ready"]}
    remaining = {cid for cid, row in all_rows.items() if row["inference"]}
    while remaining:
        newly_ready = {cid for cid in remaining if all_rows[cid]["status"] == "SUPPORTED_INFERENCE"
                       and all_rows[cid]["local_gate"] and all_rows[cid]["dependency_ids"]
                       and set(all_rows[cid]["dependency_ids"]) <= ready_ids}
        if not newly_ready:
            break
        ready_ids.update(newly_ready)
        remaining.difference_update(newly_ready)
    for row in claim_rows:
        item = all_rows[row["claim_id"]]
        row["ready"] = row["claim_id"] in ready_ids
        if item["inference"]:
            row["dependencies_ready"] = bool(item["dependency_ids"]) and set(item["dependency_ids"]) <= ready_ids

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

