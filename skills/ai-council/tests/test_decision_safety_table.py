"""Adversarial table: the Council's admission chain never yields GO past an unresolved state.

Each row feeds evidence rows through `freshness_gate` and hands its status, with
the gate inputs, to `gate_verdict` — the path the Council follows from temporal
truth to a verdict. Unresolved blockers, pending or denied approval, stale or
missing material evidence, and missing required gate answers must each keep the
verdict away from GO.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "council_kernel.py"
_spec = importlib.util.spec_from_file_location("council_safety_table_subject", SCRIPT)
k = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(k)

AS_OF = "2026-09-13T10:00:00+00:00"
FRESH = "2026-09-13T09:00:00+00:00"
OLD = "2025-01-01T00:00:00+00:00"


def _row(**changes):
    return {"claim_id": "c1", "claim_type": "general_web", "material": True, "last_verified_at": FRESH, **changes}


def _admit(rows, **gate):
    freshness = k.freshness_gate(rows, AS_OF)
    args = dict(proposed_verdict="GO", confidence=0.99, required_confidence_value=0.8,
                reversible_experiment_available=False, freshness_status=freshness["status"])
    args.update(gate)
    return k.gate_verdict(**args)


CASES = [
    ("clean", [_row()], {}, "GO"),
    ("approval-granted", [_row()], {"human_approval_required": True, "human_approved": True}, "GO"),
    ("required-gate-clear", [_row()], {"required_gatekeepers": ["legal"], "gate_statuses": {"legal": "CLEAR"}}, "GO"),
    # Unresolved blockers.
    ("gate-block", [_row()], {"gate_statuses": {"legal": "BLOCK"}}, "NO-GO"),
    ("gate-block-lowercase", [_row()], {"gate_statuses": {"legal": " block "}}, "NO-GO"),
    ("gate-block-with-approval", [_row()],
     {"gate_statuses": {"legal": "BLOCK"}, "human_approval_required": True, "human_approved": True}, "NO-GO"),
    ("gate-block-on-test", [_row()], {"proposed_verdict": "TEST", "gate_statuses": {"legal": "BLOCK"}}, "NO-GO"),
    ("gate-counsel-required", [_row()], {"gate_statuses": {"legal": "COUNSEL_REQUIRED"}}, "DEFER"),
    ("gate-unknown-status", [_row()], {"gate_statuses": {"legal": "WAIVED"}}, "DEFER"),
    ("controls-not-implemented", [_row()], {"gate_statuses": {"finance": "CLEAR_WITH_CONTROLS"}}, "DEFER"),
    ("critical-gap", [_row()], {"critical_gap": "pricing elasticity"}, "DEFER"),
    # Human approval required but not given.
    ("approval-required-missing", [_row()], {"human_approval_required": True}, "DEFER"),
    ("approval-required-missing-on-test", [_row()],
     {"proposed_verdict": "TEST", "human_approval_required": True}, "DEFER"),
    # Stale or missing material evidence.
    ("no-evidence", [], {}, "DEFER"),
    ("stale-material", [_row(last_verified_at=OLD)], {}, "DEFER"),
    ("expired-material", [_row(expires_at="2026-09-13T09:30:00+00:00")], {}, "DEFER"),
    ("draft-material", [_row(draft=True)], {}, "DEFER"),
    ("superseded-material", [_row(superseded_by="c2")], {}, "DEFER"),
    ("unregistered-policy", [_row(claim_type="vibes")], {}, "DEFER"),
    ("stale-relabelled-non-material", [_row(last_verified_at=OLD, material=False)], {}, "DEFER"),
    ("only-non-material-rows", [_row(material=False), _row(claim_id="c2", material=False)], {}, "DEFER"),
    ("material-string-false", [_row(last_verified_at=OLD, material="false")], {}, "DEFER"),
    ("one-stale-among-fresh", [_row(), _row(claim_id="c2", last_verified_at=OLD)], {}, "DEFER"),
    ("fresh-plus-non-material-stale", [_row(), _row(claim_id="c2", last_verified_at=OLD, material=False)], {}, "GO"),
    # Missing required answers.
    ("required-gate-absent", [_row()], {"required_gatekeepers": ["legal"]}, "DEFER"),
    ("required-gate-not-required", [_row()],
     {"required_gatekeepers": ["legal"], "gate_statuses": {"legal": "NOT_REQUIRED"}}, "DEFER"),
    ("required-gate-name-mismatch", [_row()],
     {"required_gatekeepers": ["legal"], "gate_statuses": {"Legal": "CLEAR"}}, "DEFER"),
    ("unknown-verdict", [_row()], {"proposed_verdict": "APPROVE"}, "DEFER"),
]


@pytest.mark.parametrize("name,rows,gate,expected", CASES, ids=[c[0] for c in CASES])
def test_admission_chain_table(name, rows, gate, expected) -> None:
    assert _admit(rows, **gate) == expected


def test_non_material_only_freshness_is_not_ready() -> None:
    report = k.freshness_gate([_row(material=False)], AS_OF)
    assert report["status"] == "REFRESH_REQUIRED"
    assert report["decision_ready"] is False
    assert report["reason"] == "no material evidence rows supplied"
