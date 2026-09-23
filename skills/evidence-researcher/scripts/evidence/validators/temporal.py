"""Temporal as-of requirement for material time-sensitive claims."""
from __future__ import annotations

from typing import Any, Dict

from ..util import _claim_needs_freshness, _parse_dt
from .context import LedgerValidationState


def validate(ledger: Dict[str, Any], state: LedgerValidationState) -> None:
    errors = state.errors
    claims = state.claims
    contract = state.contract
    current_material = [
        c for c in claims if isinstance(c, dict) and c.get("materiality") in {"critical", "material"} and _claim_needs_freshness(c)
    ]
    if current_material and _parse_dt(contract.get("as_of")) is None:
        errors.append("timezone-aware research_contract.as_of is required for material time-sensitive claims")
