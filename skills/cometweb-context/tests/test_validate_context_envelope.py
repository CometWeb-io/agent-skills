import importlib.util
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_context_envelope.py"
spec = importlib.util.spec_from_file_location("validate_context_envelope", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def valid_envelope():
    return {
        "schema": "cometweb.context/v2",
        "snapshot_id": "ctx-test",
        "generated_at": "2026-09-07T00:00:00+02:00",
        "goal": "test",
        "mode": "standard",
        "profile": "portfolio",
        "baseline": {"status": "not_requested", "ref": None},
        "sources": [
            {
                "source_id": "src-1",
                "source_type": "github",
                "authority": "system_of_record",
                "access": "connector",
                "retrieved_at": "2026-09-07T00:00:00+02:00",
                "effective_at": None,
                "freshness": "fresh",
                "sensitivity": "internal",
                "summary": "repo state",
                "evidence_ref": "repo@sha",
            }
        ],
        "facts": [
            {
                "fact_id": "f-1",
                "statement": "Current repo state was retrieved.",
                "source_ids": ["src-1"],
                "confidence": "high",
                "sensitivity": "internal",
            }
        ],
        "deltas": [],
        "conflicts": [],
        "gaps": [],
        "blocked_public_claims": [],
        "governance": {
            "first_principles": {
                "required": True,
                "status": "loaded",
                "source_ref": "cometweb/strategia/First Principles.md",
                "reason": "material portfolio decision",
            }
        },
        "handoff": {"recommended_next_skill": "product-operator", "dependencies": [], "constraints": []},
    }


def test_valid_envelope():
    module.validate(valid_envelope())


def test_unknown_fact_source_fails():
    data = valid_envelope()
    data["facts"][0]["source_ids"] = ["missing"]
    with pytest.raises(ValueError, match="unknown source_ids"):
        module.validate(data)


def test_duplicate_source_id_fails():
    data = valid_envelope()
    data["sources"].append(dict(data["sources"][0]))
    with pytest.raises(ValueError, match="duplicate source_id"):
        module.validate(data)


def test_delta_requires_baseline_state():
    data = valid_envelope()
    data["mode"] = "delta"
    data["baseline"] = {"status": "not_requested", "ref": None}
    with pytest.raises(ValueError, match="delta mode requires"):
        module.validate(data)


def test_required_first_principles_cannot_be_not_required():
    data = valid_envelope()
    data["governance"]["first_principles"]["status"] = "not_required"
    with pytest.raises(ValueError, match="required First Principles"):
        module.validate(data)
