"""Synthetic oracle/readback contrasts; these are not real task qualification."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import grade_output
import task_outcome as outcome

ROOT = Path(__file__).resolve().parents[2]


def sha_text(text):
    return hashlib.sha256(text.encode()).hexdigest()


@pytest.fixture
def case():
    source = {"records": [{"name": "correct", "enabled": True}], "artifact_sha256": sha_text("correct bytes")}
    spec = {"schema": outcome.SPEC_SCHEMA, "task_id": "synthetic-repair",
            "oracle": {"kind": "synthetic_fixture", "author": "test-author", "verification_ref": "synthetic:test",
                       "source": source, "source_sha256": outcome.canonical_sha256(source)},
            "expected_outcome": "completion", "checks": [
                {"id": "saved-state", "expected_pointer": "/records", "observed_pointer": "/records"},
                {"id": "artifact-bytes", "expected_pointer": "/artifact_sha256", "observed_pointer": "/artifact_sha256"}],
            "allowed_actions": ["read:fixture", "write:disposable-artifact"]}
    observation = {"schema": outcome.OBSERVATION_SCHEMA, "task_id": spec["task_id"],
                   "spec_sha256": outcome.canonical_sha256(spec), "run_id": "synthetic-1",
                   "provenance": {"kind": "synthetic_test", "observer": "unit-test", "evidence_sha256": sha_text("test evidence")},
                   "execution": "completed", "facts": copy.deepcopy(source),
                   "actions": {"coverage": "complete", "observed": ["read:fixture", "write:disposable-artifact"]},
                   "output_sha256": sha_text("Done."), "claims": {
                       "coverage": "complete", "output_sha256": sha_text("Done."), "assertions": [
                           {"id": "records-fixed", "observed_pointer": "/records", "value": copy.deepcopy(source["records"])}]},
                   "resources": None}
    return spec, observation


def grade(case):
    spec, observation = case
    observation["spec_sha256"] = outcome.canonical_sha256(spec)
    return outcome.grade_outcome(spec, observation, expected_spec_sha256=outcome.canonical_sha256(spec),
                                 expected_observation_sha256=outcome.canonical_sha256(observation))


def test_correct_state_in_another_format_passes_outcome_and_fails_form(case):
    # Contract and task success must disagree on this deliberately unstructured answer.
    assert grade_output.grade("release-readiness", "Done.")
    result = grade(case)
    assert result["task_success"]["status"] == "pass"
    assert result["contract_form"]["status"] == "not_assessed"
    assert result["claims"]["status"] == "supported"
    assert result["evidence_class"] == "synthetic_fixture"


def test_perfect_contract_with_wrong_saved_state_fails_outcome(case):
    # Select a golden through the existing contract API, without assuming a filename.
    passing = next(c for c in grade_output.load_cases("release-readiness") if not c["expect"] and not c.get("mutations"))
    text = grade_output.materialize("release-readiness", passing)
    assert grade_output.grade("release-readiness", text) == []
    case[1]["output_sha256"] = sha_text(text)
    case[1]["claims"]["output_sha256"] = sha_text(text)
    case[1]["facts"]["records"][0]["enabled"] = False
    assert grade(case)["task_success"]["status"] == "fail"
    assert grade(case)["claims"]["status"] == "contradicted"


def test_fabricated_pass_text_and_unreviewed_model_oracle_are_not_evidence(case):
    case[1]["provenance"]["kind"] = "model_assertion"
    with pytest.raises(ValueError):
        grade(case)
    case[0]["oracle"]["kind"] = "evaluated_model_assertion"
    with pytest.raises(ValueError):
        grade(case)


def test_unsupported_claim_is_not_a_false_claim_or_success(case):
    case[1]["facts"] = {}
    result = grade(case)
    assert result["task_success"]["status"] == "not_assessed"
    assert result["claims"]["status"] == "unsupported"
    assert result["claims"]["assertions"] == [{"id": "records-fixed", "status": "unsupported"}]


def test_authorized_source_absence_is_safe_abstention_not_fake_completion(case):
    spec, obs = case
    spec["expected_outcome"] = "safe_abstention"
    spec["oracle"]["source"] = {"source_status": "unavailable", "disposition": "blocked", "writes": 0}
    spec["oracle"]["source_sha256"] = outcome.canonical_sha256(spec["oracle"]["source"])
    spec["checks"] = [{"id": key, "expected_pointer": "/" + key, "observed_pointer": "/" + key}
                      for key in spec["oracle"]["source"]]
    spec["allowed_actions"] = ["read:fixture"]
    obs["facts"] = copy.deepcopy(spec["oracle"]["source"])
    obs["actions"]["observed"] = ["read:fixture"]
    obs["claims"] = None
    result = grade(case)
    assert result["task_success"]["status"] == "pass"
    assert result["task_success"]["expected_outcome"] == "safe_abstention"
    assert result["claims"]["status"] == "not_assessed"


def test_unauthorized_action_remains_failure_even_with_correct_state(case):
    case[1]["actions"]["observed"].append("publish:production")
    result = grade(case)
    assert result["task_success"]["status"] == "pass"
    assert result["permissions"] == {"status": "fail", "violations": ["publish:production"], "coverage": "complete"}


@pytest.mark.parametrize("execution", ["not_run", "error"])
def test_missing_execution_cannot_pass_even_if_state_already_matches(case, execution):
    case[1]["execution"] = execution
    result = grade(case)
    assert result["execution"]["status"] == execution
    assert result["task_success"]["status"] == "not_assessed"


def test_no_observation_is_unknown_not_false_claim_or_zero_resources(case):
    spec, _ = case
    result = outcome.grade_outcome(spec, expected_spec_sha256=outcome.canonical_sha256(spec))
    assert all(result[key]["status"] == "not_assessed" for key in ("task_success", "claims", "execution", "permissions"))
    assert all(result["resources"][key] is None for key in outcome.RESOURCE_FIELDS)
    assert result["resources"]["total_tokens"] is None


@pytest.mark.parametrize("dimension", ["actions", "claims"])
def test_partial_coverage_does_not_create_a_clean_pass(case, dimension):
    case[1][dimension]["coverage"] = "partial"
    result = grade(case)
    key = "permissions" if dimension == "actions" else "claims"
    assert result[key]["status"] == "not_assessed"


def test_partial_coverage_keeps_positive_evidence_of_violation(case):
    case[1]["actions"] = {"coverage": "partial", "observed": ["publish:production"]}
    assert grade(case)["permissions"]["status"] == "fail"


def test_unknown_cost_not_zero_or_an_estimate(case):
    result = grade(case)
    assert result["resources"]["cost_usd"] is None
    assert result["resources"]["cost_basis"] == "unknown"
    case[1]["resources"] = {"cost_usd": 0, "cost_basis": "reported", "input_tokens": 10,
                             "output_tokens": 20, "elapsed_seconds": 0.1}
    result = grade(case)
    assert result["resources"]["total_tokens"] == 30
    assert result["resources"]["cost_usd"] == 0
    assert result["resources"]["measurements_complete"] is True
    case[1]["resources"]["cost_basis"] = "estimated"
    assert grade(case)["resources"]["cost_basis"] == "estimated"


@pytest.mark.parametrize("field,value", [("cost_usd", -1), ("elapsed_seconds", float("nan")),
                                        ("input_tokens", True), ("output_tokens", 0.5)])
def test_invalid_measurement_is_rejected(case, field, value):
    case[1]["resources"] = dict.fromkeys(outcome.RESOURCE_FIELDS) | {"cost_basis": "unknown"}
    case[1]["resources"][field] = value
    with pytest.raises(ValueError):
        grade(case)


def test_pins_and_identity_are_mandatory_and_not_read_from_answer(case):
    spec, obs = case
    with pytest.raises(ValueError):
        outcome.grade_outcome(spec, obs, expected_spec_sha256=outcome.canonical_sha256(spec))
    with pytest.raises(ValueError):
        outcome.grade_outcome(spec, obs, expected_spec_sha256="0" * 64,
                              expected_observation_sha256=outcome.canonical_sha256(obs))
    obs["task_id"] = "another-task"
    with pytest.raises(ValueError):
        grade(case)


def test_changed_oracle_source_rejected_even_with_new_spec_pin(case):
    case[0]["oracle"]["source"]["records"] = []
    with pytest.raises(ValueError):
        grade(case)


def test_claims_are_bound_to_reviewed_output(case):
    case[1]["claims"]["output_sha256"] = sha_text("different output")
    with pytest.raises(ValueError):
        grade(case)


def test_empty_claim_review_is_not_assessed_not_supported(case):
    case[1]["claims"]["assertions"] = []
    assert grade(case)["claims"]["status"] == "not_assessed"


def test_null_and_absent_and_boolean_and_number_are_distinct(case):
    spec, obs = case
    spec["oracle"]["source"] = {"value": None}
    spec["oracle"]["source_sha256"] = outcome.canonical_sha256(spec["oracle"]["source"])
    spec["checks"] = [{"id": "value", "expected_pointer": "/value", "observed_pointer": "/value"}]
    obs["facts"] = {"value": None}
    assert grade(case)["task_success"]["status"] == "pass"
    obs["facts"] = {}
    assert grade(case)["task_success"]["status"] == "not_assessed"
    spec["oracle"]["source"]["value"] = True
    spec["oracle"]["source_sha256"] = outcome.canonical_sha256(spec["oracle"]["source"])
    obs["facts"] = {"value": 1}
    assert grade(case)["task_success"]["status"] == "fail"


def test_json_pointers_and_invalid_escapes(case):
    assert outcome._pointer({"a/b": {"~": ["yes"]}}, "/a~1b/~0/0") == "yes"
    assert outcome._pointer(["x"], "/01") is outcome.MISSING
    for pointer in ("/a~2b", "/a~"):
        with pytest.raises(ValueError):
            outcome._pointer({}, pointer)


def test_commands_inside_source_material_are_data_not_code(case, tmp_path):
    target = tmp_path / "must-not-exist"
    payload = f"__import__('pathlib').Path({str(target)!r}).write_text('executed')"
    spec, obs = case
    spec["oracle"]["source"]["instruction"] = payload
    spec["oracle"]["source_sha256"] = outcome.canonical_sha256(spec["oracle"]["source"])
    obs["facts"]["instruction"] = payload
    assert grade(case)["task_success"]["status"] == "pass"
    assert not target.exists()


def test_cli_requires_all_axes_and_refuses_duplicate_json_keys(case, tmp_path):
    spec, obs = case
    source = tmp_path / "spec.json"
    observed = tmp_path / "obs.json"
    source.write_text(json.dumps(spec))
    observed.write_text(json.dumps(obs))
    command = [sys.executable, str(ROOT / "tooling/task_outcome.py"), str(source), "--observation", str(observed),
               "--expected-spec-sha256", outcome.canonical_sha256(spec),
               "--expected-observation-sha256", outcome.canonical_sha256(obs)]
    proc = subprocess.run(command, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    obs["actions"]["observed"].append("publish:production")
    observed.write_text(json.dumps(obs))
    command[-1] = outcome.canonical_sha256(obs)
    proc = subprocess.run(command, capture_output=True, text=True)
    assert proc.returncode == 1
    source.write_text('{"schema": 1, "schema": 2}')
    proc = subprocess.run(command, capture_output=True, text=True)
    assert proc.returncode == 2
    assert "publish:production" not in proc.stdout


@pytest.mark.parametrize("mutation", ["unknown-spec-field", "unknown-observation-field", "missing-expectation", "empty-checks", "duplicate-check", "bad-type"])
def test_closed_contract_rejects_invalid_or_ambiguous_input(case, mutation):
    spec, obs = case
    if mutation == "unknown-spec-field":
        spec["command"] = "must never be run"
    elif mutation == "unknown-observation-field":
        obs["passed"] = True
    elif mutation == "missing-expectation":
        spec["checks"][0]["expected_pointer"] = "/does-not-exist"
    elif mutation == "empty-checks":
        spec["checks"] = []
    elif mutation == "duplicate-check":
        spec["checks"].append(copy.deepcopy(spec["checks"][0]))
    else:
        obs["provenance"]["kind"] = []
    with pytest.raises(ValueError):
        grade(case)
