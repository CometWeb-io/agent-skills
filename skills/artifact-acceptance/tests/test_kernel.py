import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("artifact_acceptance_kernel", ROOT / "scripts" / "kernel.py")
KERNEL = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(KERNEL)


def evidence(candidate_id="candidate-1"):
    return {
        "candidate_id": candidate_id,
        "locator": "page-1",
        "observed_at": "2026-09-21T12:00:00+02:00",
        "source": "render-check",
    }


def gate(gate_id="gate-1", required=True, state="PASS"):
    result = {"gate_id": gate_id, "required": required, "state": state}
    if state == "PASS":
        result["evidence"] = [evidence()]
    return result


def payload(**overrides):
    result = {
        "candidate": {"id": "candidate-1"},
        "contract": {"id": "contract-1"},
        "gates": [gate()],
    }
    result.update(overrides)
    return result


def test_profile_gate_must_be_required():
    result = KERNEL.decide(
        payload(
            profile="GENERAL",
            gates=[
                gate("brief_compliance", required=False),
                gate("claim_integrity"),
            ],
        )
    )

    assert result == {
        "verdict": "DEFER",
        "errors": ["profile-missing-gate:brief_compliance"],
    }


@pytest.mark.parametrize(
    ("field", "value", "expected_error"),
    [
        ("required", None, "gate[0]:required"),
        ("required", "true", "gate[0]:required"),
        ("na_allowed", None, "gate[0]:na-allowed"),
        ("open", None, "finding[0]:open"),
        ("blocks_acceptance", None, "finding[0]:blocks_acceptance"),
    ],
)
def test_non_boolean_gate_and_finding_flags_defer(field, value, expected_error):
    candidate = payload()
    if field in {"required", "na_allowed"}:
        candidate["gates"][0][field] = value
    else:
        candidate["findings"] = [{"severity": "MAJOR", field: value}]

    result = KERNEL.decide(candidate)

    assert result["verdict"] == "DEFER"
    assert result["errors"] == [expected_error]


@pytest.mark.parametrize(
    ("field", "value", "expected_error"),
    [
        ("required_gate_bypass", None, "control[0]:required_gate_bypass"),
        ("waiver", None, "control[0]:waiver"),
    ],
)
def test_non_boolean_control_flags_defer(field, value, expected_error):
    candidate = payload(
        controls=[
            {
                "severity": "MINOR",
                "issue": "minor issue",
                "owner": "owner",
                "revisit_condition": "next review",
                field: value,
            }
        ]
    )

    result = KERNEL.decide(candidate)

    assert result["verdict"] == "NOT_READY"
    assert result["errors"] == [expected_error]


@pytest.mark.parametrize(
    ("path", "value", "expected_verdict"),
    [
        (("mode",), [], "DEFER"),
        (("profile",), {}, "DEFER"),
        (("minimum_gate_evidence_grade",), [], "DEFER"),
        (("gates", 0, "state"), [], "DEFER"),
        (("gates", 0, "evidence_grade"), {}, "DEFER"),
        (("findings", 0, "severity"), {}, "DEFER"),
        (("controls", 0, "severity"), [], "NOT_READY"),
        (("traceability", 0, "gate_id"), {}, "DEFER"),
    ],
)
def test_malformed_enum_values_fail_closed_without_type_error(path, value, expected_verdict):
    candidate = payload()
    if path[0] == "gates" and path[-1] == "evidence_grade":
        candidate["minimum_gate_evidence_grade"] = "A"
    elif path[0] == "findings":
        candidate["findings"] = [{"severity": "MAJOR"}]
    elif path[0] == "controls":
        candidate["controls"] = [
            {
                "severity": "MINOR",
                "issue": "minor issue",
                "owner": "owner",
                "revisit_condition": "next review",
            }
        ]
    elif path[0] == "traceability":
        candidate.update(
            {
                "mode": "DEEP",
                "criteria_ids": ["criterion-1"],
                "traceability": [{"criterion_id": "criterion-1", "gate_id": "gate-1"}],
            }
        )

    target = candidate
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = value

    result = KERNEL.decide(candidate)

    assert result["verdict"] == expected_verdict
    assert result["errors"]
