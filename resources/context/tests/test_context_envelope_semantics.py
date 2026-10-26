"""Semantic extras for ContextEnvelope validator."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_context_envelope.py"
spec = importlib.util.spec_from_file_location("validate_context_envelope", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def _base(**overrides):
    data = {
        "schema": "cometweb.context/v2",
        "snapshot_id": "ctx-test",
        "generated_at": "2026-08-30T20:00:00Z",
        "goal": "test",
        "mode": "standard",
        "profile": "product",
        "baseline": {"status": "not_requested", "ref": None},
        "sources": [],
        "facts": [],
        "deltas": [],
        "conflicts": [],
        "gaps": [],
        "blocked_public_claims": [],
        "handoff": {"recommended_next_skill": None, "dependencies": [], "constraints": []},
    }
    data.update(overrides)
    return data


def test_fallback_sor_requires_authority_gap():
    bad = _base(
        sources=[
            {
                "source_id": "crm-csv",
                "source_type": "file",
                "authority": "system_of_record",
                "access": "fallback",
                "retrieved_at": "2026-08-30T20:00:00Z",
                "effective_at": None,
                "freshness": "fresh",
                "sensitivity": "confidential",
                "summary": "export",
                "evidence_ref": "file:1",
            }
        ]
    )
    with pytest.raises(ValueError, match="authority_gap"):
        module.validate(bad)


def test_confidential_statement_length_cap():
    bad = _base(
        sources=[
            {
                "source_id": "gmail",
                "source_type": "gmail",
                "authority": "secondary",
                "access": "connector",
                "retrieved_at": "2026-08-30T20:00:00Z",
                "effective_at": None,
                "freshness": "fresh",
                "sensitivity": "confidential",
                "summary": "mail",
                "evidence_ref": "gmail:1",
            }
        ],
        facts=[
            {
                "fact_id": "f1",
                "statement": "X" * 801,
                "source_ids": ["gmail"],
                "confidence": "low",
                "sensitivity": "confidential",
            }
        ],
    )
    with pytest.raises(ValueError, match="summary limit"):
        module.validate(bad)


# conflicts[].status is a closed vocabulary. Before it was checked, only the
# literal "resolved" triggered the basis rule, so "Resolved" or "closed" read
# as settled downstream without any basis.
@pytest.mark.parametrize("status", ["Resolved", "closed", None])
def test_conflict_status_outside_vocabulary_is_rejected(status):
    conflict = {"basis": None} if status is None else {"status": status}
    with pytest.raises(ValueError, match=r"conflicts\[0\] invalid status"):
        module.validate(_base(conflicts=[conflict]))


def test_unresolved_conflict_needs_no_basis():
    module.validate(_base(conflicts=[{"status": "unresolved_conflict"}]))


def test_confidence_vocabulary_is_a_bound_constant():
    assert module.CONFIDENCE == {"high", "medium", "low"}
    assert module.CONFLICT_STATUS == {"unresolved_conflict", "resolved"}
