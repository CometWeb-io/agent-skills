"""Contradiction record validators."""
from __future__ import annotations

from typing import Any, Dict

from ..constants import CONTRADICTION_RESOLUTIONS, MATERIALITIES
from ..util import _id_index
from .context import LedgerValidationState


def validate(ledger: Dict[str, Any], state: LedgerValidationState) -> None:
    errors = state.errors
    claim_ids = state.claim_ids
    evidence = state.evidence
    contradictions = state.contradictions
    accepted_contradict_by_claim = state.accepted_contradict_by_claim

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

    state.contradiction_claim_ids = contradiction_claim_ids

    for cid, edges in accepted_contradict_by_claim.items():
        if edges and cid not in contradiction_claim_ids:
            errors.append(f"{cid} has ACCEPTED CONTRADICT evidence without a contradiction record")
