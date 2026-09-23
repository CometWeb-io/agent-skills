"""Gap coverage validators for ledger validation."""
from __future__ import annotations

from typing import Any, Dict

from .context import LedgerValidationState


def validate(ledger: Dict[str, Any], state: LedgerValidationState) -> None:
    errors = state.errors
    warnings = state.warnings
    claim_ids = state.claim_ids
    gaps = state.gaps

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
