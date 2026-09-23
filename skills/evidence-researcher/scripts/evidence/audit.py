"""Research gate audit."""
from __future__ import annotations

from typing import Any, Dict

from .constants import POLICY_VERSION, SCHEMA_VERSION, VERSION
from .coverage_ops import coverage
from .identity import pack_hash
from .validators import validate_ledger


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
        elif cov["critical_gaps"] or cov["material_gaps"]:
            status = "PARTIAL"
            reason = "critical or material evidence gap remains open"
        elif cov["material_claim_count"] == 0:
            status = "PARTIAL"
            reason = "no material research scope has been assessed"
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

