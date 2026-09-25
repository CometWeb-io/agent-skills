"""The canonical orchestrator must package without repository-only links."""

from __future__ import annotations

from pathlib import Path

from package_skill import payload


ROOT = Path(__file__).resolve().parents[2]


def test_canonical_orchestrator_package_is_self_contained() -> None:
    entries, manifest = payload(ROOT, "skill-orchestrator")
    assert "SKILL.md" in entries
    assert manifest["skill"] == "skill-orchestrator"
