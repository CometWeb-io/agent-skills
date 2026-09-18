"""Shared helpers for the cometweb-context tests.

These were previously imported from a sibling test module, which only resolves
under pytest's prepend import mode and made one test file a dependency of
another. Keeping them here, next to the tests and imported through an explicit
sys.path entry, matches how tooling/tests already reaches its own modules and
works whichever import mode a runner picks.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def load_script(name: str):
    """Import a skill script by path; the scripts are not an installed package."""
    path = SCRIPTS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader, f"cannot load {path}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_valid_envelope() -> dict:
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
