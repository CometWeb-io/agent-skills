import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "quality_loop_regressions", Path(__file__).parents[1] / "scripts/kernel.py",
)
kernel = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(kernel)


def completed(profile="EDITORIAL"):
    return {
        "profile": profile, "candidate_id": "candidate-1", "contract_id": "contract-1",
        "stages": [{"skill": skill, "state": "PASS"} for skill in kernel.PROFILES[profile]],
    }


@pytest.mark.parametrize("profile", ["EDITORIAL", "SALES", "TECHNICAL_DOCS", "RESEARCH", "REPO_DEEP"])
def test_later_pass_does_not_clear_specialist_changes_required(profile):
    payload = completed(profile)
    specialist = payload["stages"][0]
    specialist["state"] = "CHANGES_REQUIRED"
    result = kernel.validate(payload)
    assert result["status"] == "CHANGES_REQUIRED"
    assert result["next_stage"] == specialist["skill"]
    specialist["state"] = "PASS"
    assert kernel.validate(payload)["status"] == "COMPLETE"


def test_reviewer_changes_still_route_to_pending_repair_before_revalidation():
    payload = completed()
    payload["stages"][2]["state"] = "CHANGES_REQUIRED"
    payload["stages"][4]["state"] = "PENDING"
    result = kernel.validate(payload)
    assert (result["status"], result["next_stage"]) == ("READY_FOR_NEXT", "repair-operator")
    payload["stages"][4]["state"] = "PASS"
    result = kernel.validate(payload)
    assert (result["status"], result["next_stage"]) == ("CHANGES_REQUIRED", "content-reviewer")


@pytest.mark.parametrize("value", [[], {}, None, 0])
@pytest.mark.parametrize("path,error", [
    (("adaptive_depth", "recommended_mode"), "adaptive_depth:invalid"),
    (("quality_debt", 0, "severity"), "debt[0]:severity"),
    (("quality_debt", 0, "status"), "debt[0]:status"),
    (("runtime_lifecycle", "state"), "runtime_lifecycle:state"),
    (("runtime_lifecycle", "stability_status"), "runtime_lifecycle:stability-status"),
    (("runtime_lifecycle", "paired_status"), "runtime_lifecycle:paired-status"),
])
def test_malformed_optional_enums_fail_closed(path, error, value):
    payload = completed()
    payload.update({
        "adaptive_depth": {"recommended_mode": "STANDARD"},
        "as_of": "2026-10-11T12:00:00+00:00",
        "quality_debt": [{"severity": "NOTE", "status": "OPEN"}],
        "runtime_lifecycle": {"state": "NOT_REQUESTED"},
    })
    target = payload
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    result = kernel.validate(payload)
    assert result["status"] == "INVALID"
    assert result["errors"] == [error]
