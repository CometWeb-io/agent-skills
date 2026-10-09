from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "brief_architect_kernel",
    ROOT / "scripts" / "kernel.py",
)
assert SPEC and SPEC.loader
kernel = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(kernel)


def make_brief(**overrides):
    brief = {
        "objective": "o",
        "audience": "a",
        "deliverables": ["d"],
        "evidence_policy": "CREATIVE",
        "acceptance_criteria": [
            {"id": "c", "check": "x", "observable": True},
        ],
    }
    brief.update(overrides)
    return brief


@pytest.mark.parametrize("priority", [[], {}], ids=["list", "dict"])
def test_readiness_rejects_unhashable_acceptance_priority(priority):
    result = kernel.readiness(
        make_brief(
            acceptance_criteria=[
                {
                    "id": "c",
                    "check": "x",
                    "observable": True,
                    "priority": priority,
                },
            ],
        ),
    )

    assert result["status"] == "INVALID"
    assert "acceptance_criteria[0]:priority" in result["errors"]


@pytest.mark.parametrize(
    ("field", "malformed", "expected_error"),
    [
        ("acceptance_criteria", None, "old.acceptance_criteria:not-list"),
        (
            "acceptance_criteria",
            [{"id": []}],
            "old.acceptance_criteria[0]:id",
        ),
        (
            "acceptance_criteria",
            [{"id": {}}],
            "old.acceptance_criteria[0]:id",
        ),
        (
            "acceptance_criteria",
            [{"id": "c", "priority": []}],
            "old.acceptance_criteria[0]:priority",
        ),
        (
            "protected_invariants",
            [{"id": []}],
            "old.protected_invariants[0]:invalid",
        ),
        (
            "protected_invariants",
            [{"id": {}}],
            "old.protected_invariants[0]:invalid",
        ),
    ],
)
def test_delta_rejects_malformed_collections(field, malformed, expected_error):
    old = make_brief(acceptance_criteria=[], protected_invariants=[])
    old[field] = malformed
    new = make_brief(acceptance_criteria=[], protected_invariants=[])

    result = kernel.delta(old, new)

    assert result == {
        "status": "INVALID",
        "material_changes": [],
        "requires_downstream_revalidation": True,
        "errors": [expected_error],
    }


@pytest.mark.parametrize(
    "field",
    ["acceptance_criteria", "protected_invariants"],
)
def test_delta_rejects_malformed_new_collection(field):
    old = make_brief(acceptance_criteria=[], protected_invariants=[])
    new = make_brief(acceptance_criteria=[], protected_invariants=[])
    new[field] = {}

    result = kernel.delta(old, new)

    assert result["status"] == "INVALID"
    assert result["requires_downstream_revalidation"] is True
    assert result["errors"] == [f"new.{field}:not-list"]
