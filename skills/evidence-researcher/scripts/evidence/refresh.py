"""Refresh plan for time-sensitive support evidence."""
from __future__ import annotations

from typing import Any, Dict

from .constants import LIVE_VERIFICATION_TYPES, VERSION
from .coverage_ops import _accepted_edges_for_claim
from .temporal_eval import temporal_status
from .util import _claim_needs_freshness, _id_index


def refresh_plan(ledger: Dict[str, Any]) -> Dict[str, Any]:
    contract = ledger.get("research_contract") if isinstance(ledger.get("research_contract"), dict) else {}
    as_of = contract.get("as_of")
    all_claims = _id_index([c for c in ledger.get("claims", []) if isinstance(c, dict)], "claim_id")
    needed = {cid for cid, c in all_claims.items() if c.get("materiality") in {"critical", "material"}}
    pending = list(needed)
    while pending:
        claim = all_claims.get(pending.pop(), {})
        for dep in claim.get("depends_on_claim_ids", []):
            if dep in all_claims and dep not in needed:
                needed.add(dep)
                pending.append(dep)
    claims = [c for cid, c in all_claims.items() if cid in needed]
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
            result = temporal_status(source, as_of, str(claim.get("claim_type") or "current_fact"), research_id=ledger.get("research_id"), research_started_at=contract.get("started_at"))
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
    affected = {i["claim_id"] for i in items if i["action"] == "REFRESH_NOW"}
    dependent = set()
    while True:
        extra = {c["claim_id"] for c in claims if c.get("epistemic_kind") == "INFERENCE"
                 and set(c.get("depends_on_claim_ids", [])) & affected} - affected
        if not extra:
            break
        dependent.update(extra)
        affected.update(extra)
    return {
        "dependent_claim_ids": sorted(dependent),
        "as_of": as_of,
        "refresh_required": any(i["action"] == "REFRESH_NOW" for i in items),
        "refresh_soon": any(i["action"] == "REFRESH_SOON" for i in items),
        "items": items,
        "kernel_version": VERSION,
    }

