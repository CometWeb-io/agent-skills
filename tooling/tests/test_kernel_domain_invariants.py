"""Invariants the domain kernels promise, checked across their whole range.

Example-based tests pin one input each, so a sign error or a clamp that hides a
bad value survives them. These walk the range instead: severity must never soften
as a dimension worsens, a gate must fire regardless of severity, a dependency
cycle must be caught however it is shaped, and a timestamp that cannot be trusted
must not read as the freshest evidence available.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def kernel(skill: str, script: str):
    path = ROOT / "skills" / skill / "scripts" / script
    spec = importlib.util.spec_from_file_location(f"probe_{skill.replace('-', '_')}_{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# --- customer-ops ---------------------------------------------------------

SEVERITY_RANK = {"NOT_INCIDENT": -1, "SEV5": 0, "SEV4": 1, "SEV3": 2, "SEV2": 3, "SEV1": 4}


def severity(**overrides) -> str:
    data = {"impact": 2, "breadth": 2, "workaround": 2}
    data.update(overrides)
    return kernel("customer-ops", "customer_ops_kernel.py").incident_severity(data)["customer_impact_severity"]


@pytest.mark.parametrize("dimension", ["impact", "breadth", "workaround"])
@pytest.mark.parametrize("lower", range(4))
def test_worsening_a_dimension_never_softens_severity(dimension: str, lower: int) -> None:
    worse = severity(**{dimension: lower + 1})
    better = severity(**{dimension: lower})
    assert SEVERITY_RANK[worse] >= SEVERITY_RANK[better], (
        f"{dimension} {lower}->{better} but {lower + 1}->{worse}"
    )


@pytest.mark.parametrize("flag,gate", [
    ("confirmed_security_incident", "security"),
    ("confirmed_privacy_incident", "privacy"),
    ("confirmed_data_loss", "data_loss"),
    ("legal_signal", "legal"),
])
def test_specialist_gate_fires_even_below_incident_threshold(flag: str, gate: str) -> None:
    """A gate is not a score: it must not be averaged away by low severity."""
    data = {"impact": 0, "breadth": 0, "workaround": 0, flag: True}
    result = kernel("customer-ops", "customer_ops_kernel.py").incident_severity(data)
    assert result["customer_impact_severity"] == "NOT_INCIDENT"
    assert gate in result["specialist_gates"]
    assert result["specialist_gate_required"] is True


# --- repo-to-roadmap ------------------------------------------------------

def graph(*pairs):
    return [{"id": i, "depends_on": list(d)} for i, d in pairs]


@pytest.mark.parametrize("label,items,valid", [
    ("chain", graph(("a", []), ("b", ["a"]), ("c", ["b"])), True),
    ("two-node cycle", graph(("a", ["b"]), ("b", ["a"])), False),
    ("three-node cycle", graph(("a", ["c"]), ("b", ["a"]), ("c", ["b"])), False),
    ("self loop", graph(("a", ["a"])), False),
    ("missing dependency", graph(("a", ["nope"])), False),
    ("duplicate id", graph(("a", []), ("a", [])), False),
])
def test_dependency_graph_validity(label: str, items: list, valid: bool) -> None:
    assert kernel("repo-to-roadmap", "roadmap_kernel.py").graph_report(items)["valid"] is valid


def test_a_healthy_node_beside_a_cycle_is_not_implicated() -> None:
    report = kernel("repo-to-roadmap", "roadmap_kernel.py").graph_report(
        graph(("x", []), ("a", ["b"]), ("b", ["a"]))
    )
    assert report["cycle_nodes"] == ["a", "b"]


# --- product-operator -----------------------------------------------------

AS_OF = "2026-09-18T12:00:00Z"


@pytest.mark.parametrize("observed,expected", [
    ("2026-09-18T00:00:00Z", "CURRENT"),
    ("2026-08-26T00:00:00Z", "CURRENT"),
    ("2026-08-24T00:00:00Z", "NEAR_EXPIRY"),
    ("2026-08-09T00:00:00Z", "STALE"),
    ("2099-01-01T00:00:00Z", "UNKNOWN"),
])
def test_evidence_freshness_bands(observed: str, expected: str) -> None:
    module = kernel("product-operator", "operator_kernel.py")
    assert module.evidence_freshness({"observed_at": observed, "max_age_days": 30}, AS_OF) == expected


@pytest.mark.parametrize("authority,ok", [("github", True), ("blog", False), ("hearsay", False)])
def test_evidence_authority_for_implemented_stage(authority: str, ok: bool) -> None:
    module = kernel("product-operator", "operator_kernel.py")
    assert module.evidence_authority_ok({"authority": authority, "source": authority}, "implemented") is ok
