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


def bounded(profile="SALES", reviewer="content-roaster"):
    return {
        "profile": profile, "candidate_id": "offer-v2", "contract_id": "one-review-v1",
        "required_stages": [reviewer, "artifact-acceptance"],
        "policy_lock": {
            "pack_id": "bounded-review", "revision": "1", "sha256": "a" * 64,
            "locked_before_evaluation": True,
        },
        "stages": [{"skill": reviewer, "state": "PASS"},
                   {"skill": "artifact-acceptance", "state": "PASS"}],
    }


@pytest.mark.parametrize("profile", ["EDITORIAL", "SALES", "TECHNICAL_DOCS"])
@pytest.mark.parametrize("reviewer", ["content-reviewer", "content-roaster"])
def test_frozen_single_review_does_not_require_duplicate_review_or_recreation(profile, reviewer):
    assert kernel.validate(bounded(profile, reviewer))["status"] == "COMPLETE"


def test_deep_can_use_one_review_when_that_is_the_locked_contract():
    payload = bounded()
    payload["mode"] = "DEEP"
    assert kernel.validate(payload)["status"] == "COMPLETE"


@pytest.mark.parametrize("plan", [None, [], "content-roaster", {}, [None], [[]],
                                  ["unknown"], ["content-roaster", "content-roaster"],
                                  ["artifact-acceptance", "content-roaster"]])
def test_malformed_stage_plan_is_invalid_instead_of_falling_back(plan):
    payload = bounded()
    payload["required_stages"] = plan
    assert kernel.validate(payload)["status"] == "INVALID"


@pytest.mark.parametrize("plan", [["artifact-acceptance"], ["content-roaster"],
                                  ["content-writer", "artifact-acceptance"]])
def test_short_plan_cannot_remove_both_review_and_verification_safeguards(plan):
    payload = bounded()
    payload["required_stages"] = plan
    payload["stages"] = [{"skill": skill, "state": "PASS"} for skill in plan]
    assert kernel.validate(payload)["status"] == "INVALID"


def test_explicit_plan_requires_a_preexisting_policy_lock():
    payload = bounded()
    del payload["policy_lock"]
    assert "policy-lock:required" in kernel.validate(payload)["errors"]
    payload["policy_lock"] = {"pack_id": "p", "revision": "1", "sha256": "a" * 64,
                              "locked_before_evaluation": False}
    assert "policy-lock:not-prelocked" in kernel.validate(payload)["errors"]


@pytest.mark.parametrize("state,status", [("PENDING", "READY_FOR_NEXT"),
                                         ("BLOCKED", "BLOCKED"),
                                         ("CHANGES_REQUIRED", "BLOCKED")])
def test_single_review_cannot_close_without_passing_verification(state, status):
    payload = bounded()
    payload["stages"][1]["state"] = state
    assert kernel.validate(payload)["status"] == status


def test_short_plan_does_not_clear_unfixed_findings_or_conflicts():
    payload = bounded()
    payload["stages"][0]["state"] = "CHANGES_REQUIRED"
    assert kernel.validate(payload)["status"] == "CHANGES_REQUIRED"
    payload["stages"][0]["state"] = "PASS"
    payload["reconciliation"] = [{"status": "CONFLICT", "resolved": False}]
    assert kernel.validate(payload)["status"] == "NEEDS_RECONCILIATION"


def test_required_stage_cannot_be_skipped_in_an_explicit_plan():
    payload = bounded()
    payload["stages"][0].update(state="SKIPPED", skip_allowed=True, skip_rationale="Save time")
    assert kernel.validate(payload)["status"] == "INVALID"


def test_omitted_plan_preserves_legacy_profile_requirements():
    payload = bounded()
    del payload["required_stages"]
    result = kernel.validate(payload)
    assert (result["status"], result["next_stage"]) == ("READY_FOR_NEXT", "brief-architect")


@pytest.mark.parametrize("profile,plan", [
    ("SKILL_QUALITY", ["skill-evaluator"]),
    ("REPO_DEEP", ["repair-operator"]),
    ("RESEARCH", ["content-reviewer", "artifact-acceptance"]),
])
def test_short_plan_preserves_domain_specific_evidence_requirements(profile, plan):
    payload = bounded(profile)
    payload["required_stages"] = plan
    payload["stages"] = [{"skill": skill, "state": "PASS"} for skill in plan]
    assert kernel.validate(payload)["status"] == "INVALID"
