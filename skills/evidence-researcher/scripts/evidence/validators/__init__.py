"""Composed ledger validators."""
from __future__ import annotations

from typing import Any, Dict

from ..constants import POLICY_VERSION, SCHEMA_VERSION, VERSION
from . import (
    claim_identity,
    contradictions,
    coverage,
    evidence_links,
    freshness,
    independence,
    schema,
    source_identity,
    temporal,
)
from .context import LedgerValidationState

_VALIDATORS = (
    schema.validate,
    claim_identity.validate,
    source_identity.validate,
    independence.validate,
    evidence_links.validate,
    contradictions.validate,
    coverage.validate,
    temporal.validate,
    freshness.validate,
)


def validate_ledger(ledger: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(ledger, dict):
        return {"valid": False, "errors": ["ledger root must be an object"], "warnings": [], "kernel_version": VERSION}

    state = LedgerValidationState()
    for validator in _VALIDATORS:
        validator(ledger, state)

    return {
        "valid": not state.errors,
        "errors": sorted(set(state.errors)),
        "warnings": sorted(set(state.warnings)),
        "schema_version": SCHEMA_VERSION,
        "kernel_version": VERSION,
        "policy_version": POLICY_VERSION,
    }
