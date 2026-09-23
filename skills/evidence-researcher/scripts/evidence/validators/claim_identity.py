"""Claim field and dependency identity validators."""
from __future__ import annotations

from typing import Any, Dict

from ..constants import (
    CLAIM_STATUSES,
    CLAIM_TYPES,
    CONFIDENCE_LEVELS,
    EPISTEMIC_KINDS,
    MATERIALITIES,
    TEMPORAL_SENSITIVITIES,
)
from ..util import _dependency_cycles
from .context import LedgerValidationState


def validate(ledger: Dict[str, Any], state: LedgerValidationState) -> None:
    errors = state.errors
    warnings = state.warnings
    claims = state.claims
    claim_ids = state.claim_ids

    for i, claim in enumerate(claims):
        if not isinstance(claim, dict):
            continue
        cid = claim.get("claim_id") or f"claims[{i}]"
        if not claim.get("claim_text"):
            errors.append(f"{cid}.claim_text is required")
        if "contradiction_tested" in claim and type(claim["contradiction_tested"]) is not bool:
            errors.append(f"{cid}.contradiction_tested must be boolean")
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
