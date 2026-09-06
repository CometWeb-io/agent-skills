import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_context_envelope.py"
spec = importlib.util.spec_from_file_location("validate_context_envelope", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def test_minimal_valid_envelope():
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
    module.validate(data)
