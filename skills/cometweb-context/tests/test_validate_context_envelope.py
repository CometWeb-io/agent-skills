import importlib.util
import json
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_context_envelope.py"
spec = importlib.util.spec_from_file_location("validate_context_envelope", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def _valid(**overrides):
    data = {
        "schema": "cometweb.context/v2",
        "snapshot_id": "ctx-test",
        "generated_at": "2026-08-30T20:00:00Z",
        "goal": "test",
        "mode": "standard",
        "profile": "product",
        "baseline": {"status": "not_requested", "ref": None},
        "sources": [
            {
                "source_id": "src-repo",
                "source_type": "github",
                "authority": "primary",
                "access": "connector",
                "retrieved_at": "2026-08-30T20:00:00Z",
                "effective_at": None,
                "freshness": "fresh",
                "sensitivity": "internal",
                "summary": "Insight main HEAD",
                "evidence_ref": "github:CometWeb-Insight#abc",
            }
        ],
        "facts": [
            {
                "fact_id": "f-001",
                "statement": "Insight main is healthy",
                "source_ids": ["src-repo"],
                "confidence": "high",
                "sensitivity": "internal",
            }
        ],
        "deltas": [],
        "conflicts": [],
        "gaps": [],
        "blocked_public_claims": [],
        "handoff": {"recommended_next_skill": None, "dependencies": [], "constraints": []},
    }
    data.update(overrides)
    return data


def test_minimal_valid_envelope():
    module.validate(_valid())


def test_rejects_invalid_profile():
    with pytest.raises(ValueError):
        module.validate(_valid(profile="banana"))


def test_rejects_invalid_authority():
    data = _valid()
    data["sources"][0]["authority"] = "whatever"
    with pytest.raises(ValueError):
        module.validate(data)


def test_rejects_invalid_access_and_sensitivity():
    data = _valid()
    data["sources"][0]["access"] = "magic"
    with pytest.raises(ValueError):
        module.validate(data)
    data = _valid()
    data["sources"][0]["sensitivity"] = "public-ish"
    with pytest.raises(ValueError):
        module.validate(data)


def test_rejects_non_object_facts():
    with pytest.raises(ValueError):
        module.validate(_valid(facts="hello"))


def test_rejects_unknown_source_id():
    data = _valid()
    data["facts"][0]["source_ids"] = ["non-existing-source"]
    with pytest.raises(ValueError):
        module.validate(data)


def test_delta_without_baseline_forbids_deltas():
    data = _valid(mode="delta", baseline={"status": "unavailable", "ref": None}, deltas=[{"delta_id": "d1", "statement": "x"}])
    with pytest.raises(ValueError):
        module.validate(data)


def test_resolved_conflict_requires_basis():
    data = _valid(
        conflicts=[
            {
                "conflict_id": "c1",
                "status": "resolved",
                "statements": [{"a": 1}, {"b": 2}],
                "basis": None,
            }
        ]
    )
    with pytest.raises(ValueError):
        module.validate(data)


def test_authority_gap_requires_missing_authority():
    data = _valid(
        gaps=[
            {
                "gap_id": "g1",
                "kind": "authority_gap",
                "statement": "CRM down",
                "missing_authority": None,
            }
        ]
    )
    with pytest.raises(ValueError):
        module.validate(data)


def test_blocked_claim_requires_reason():
    data = _valid(blocked_public_claims=[{"claim": "we grew 400%", "reason": ""}])
    with pytest.raises(ValueError):
        module.validate(data)


def test_schema_file_exists():
    assert module.SCHEMA_PATH.is_file()
