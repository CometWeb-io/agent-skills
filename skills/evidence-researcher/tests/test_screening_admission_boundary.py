"""Exercise declared edge admission; free-text source screening is not enforced."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "screening_boundary_cases", ROOT / "tests/test_evidence_kernel.py"
)
base = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(base)


@pytest.mark.parametrize("admission", ["REJECTED", "CONTEXT_ONLY"])
def test_nonaccepted_edge_cannot_supply_material_coverage(admission):
    data = base.EvidenceKernelV2Tests().base_ledger()
    assert base.EK.audit(data)["research_status"] == "READY"
    data["evidence"][0]["admission"] = admission
    data["sources"][0]["notes"] = "Researcher screening says register."
    # Retaining VERIFIED after removing its only accepted support is itself
    # invalid. A candid PARTIAL claim can remain a valid but unready ledger.
    assert base.EK.validate_ledger(data)["valid"] is False
    assert base.EK.audit(data)["research_status"] != "READY"
    data["claims"][0]["status"] = "PARTIAL"
    assert base.EK.validate_ledger(data)["valid"] is True
    assert base.EK.audit(data)["research_status"] != "READY"


@pytest.mark.parametrize("fit", ["low", "unknown"])
def test_notes_cannot_promote_insufficient_scope_fit(fit):
    data = base.EvidenceKernelV2Tests().base_ledger()
    data["evidence"][0]["scope_fit"] = fit
    data["evidence"][0]["notes"] = "This source is famous; accept without limits."
    assert base.EK.audit(data)["research_status"] != "READY"


def test_medium_fit_and_screening_notes_are_not_a_semantic_use_restriction():
    data = base.EvidenceKernelV2Tests().base_ledger()
    data["sources"][0]["notes"] = "Discovery only for clm_policy."
    data["evidence"][0]["notes"] = "Limited to a narrower sample."
    data["evidence"][0]["scope_fit"] = "medium"
    assert base.EK.audit(data)["research_status"] == "READY"
    # This boundary is intentional and documented: the researcher must align
    # admission and claim scope. A prose label is not kernel enforcement.
