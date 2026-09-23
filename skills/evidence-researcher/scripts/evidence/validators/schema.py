"""Root schema and collection shape validators."""
from __future__ import annotations

from typing import Any, Dict

from ..constants import PROVENANCE_LANES, SCHEMA_VERSION
from .context import LedgerValidationState


def validate(ledger: Dict[str, Any], state: LedgerValidationState) -> None:
    errors = state.errors
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
    state.contract = contract

    claims = ledger.get("claims", [])
    sources = ledger.get("sources", [])
    evidence = ledger.get("evidence", [])
    contradictions = ledger.get("contradictions", [])
    searches = ledger.get("searches", [])
    gaps = ledger.get("gaps", [])
    for name, rows in (("claims", claims), ("sources", sources), ("evidence", evidence), ("contradictions", contradictions), ("searches", searches), ("gaps", gaps)):
        if not isinstance(rows, list):
            errors.append(f"{name} must be a list")
    state.claims = claims if isinstance(claims, list) else []
    state.sources = sources if isinstance(sources, list) else []
    state.evidence = evidence if isinstance(evidence, list) else []
    state.contradictions = contradictions if isinstance(contradictions, list) else []
    state.searches = searches if isinstance(searches, list) else []
    state.gaps = gaps if isinstance(gaps, list) else []

    id_specs = [
        (state.claims, "claim_id", "claim"), (state.sources, "source_id", "source"), (state.evidence, "evidence_id", "evidence"),
        (state.contradictions, "contradiction_id", "contradiction"), (state.searches, "search_id", "search"), (state.gaps, "gap_id", "gap"),
    ]
    ids_by_kind: dict[str, set[str]] = {}
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

    state.claim_ids = ids_by_kind.get("claim", set())
    state.source_ids = ids_by_kind.get("source", set())
