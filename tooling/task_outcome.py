#!/usr/bin/env python3
"""Compare pinned external observations with a source-bound task oracle, offline.

This does not extract truth from model prose, execute source material, authenticate
observers, or replace grade_output.py's structural contract checks.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from audit_contracts import HEX64, MAX_JSON, array, index, loads, obj, require, text

SPEC_SCHEMA = "cometweb.task-outcome-spec/v1"
OBSERVATION_SCHEMA = "cometweb.task-outcome-observation/v1"
RESOURCE_FIELDS = ("cost_usd", "input_tokens", "output_tokens", "elapsed_seconds")
MISSING = object()


def canonical_sha256(value: Any) -> str:
    """Fingerprint JSON data; booleans and numbers remain different values."""
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _pin(value: Any, expected: str | None, label: str) -> str:
    actual = canonical_sha256(value)
    require(isinstance(expected, str) and bool(HEX64.fullmatch(expected)) and expected == actual,
            f"{label}: missing or mismatched externally reviewed pin")
    return actual


def _pointer(value: Any, pointer: str) -> Any:
    """Small RFC 6901 reader. Missing is distinct from an observed JSON null."""
    require(isinstance(pointer, str) and (pointer == "" or pointer.startswith("/")), "invalid JSON pointer")
    for token in pointer.split("/")[1:] if pointer else []:
        require(all(bool(part) and part[0] in "01" for part in token.split("~")[1:]), "invalid JSON pointer escape")
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(value, dict):
            value = value.get(token, MISSING)
        elif isinstance(value, list) and token.isascii() and token.isdigit() and (token == "0" or not token.startswith("0")):
            pos = int(token) if len(token) < 10 else len(value)
            value = value[pos] if pos < len(value) else MISSING
        else:
            value = MISSING
    return value


def _strings(value: Any, label: str) -> list[str]:
    values = array(value, label)
    for item in values:
        text(item, label, 256)
    require(len(set(values)) == len(values), f"{label}: duplicate entry")
    return values


def _validate_spec(spec: dict, *, expected_spec_sha256: str) -> dict:
    """Validate the frozen oracle before scheduling or grading; never run its data."""
    obj(spec, {"schema", "task_id", "oracle", "expected_outcome", "checks", "allowed_actions"}, set(), "spec")
    require(spec["schema"] == SPEC_SCHEMA, "unsupported spec schema")
    text(spec["task_id"], "task_id", 128)
    _pin(spec, expected_spec_sha256, "spec")
    oracle = obj(spec["oracle"], {"kind", "author", "verification_ref", "source", "source_sha256"}, set(), "oracle")
    require(oracle["kind"] in {"independently_verified_reference", "synthetic_fixture"}, "oracle must be independently verified or explicitly synthetic")
    text(oracle["author"], "oracle.author")
    text(oracle["verification_ref"], "oracle.verification_ref")
    _pin(oracle["source"], oracle["source_sha256"], "oracle.source")
    require(spec["expected_outcome"] in {"completion", "safe_abstention"}, "invalid expected outcome")
    checks = index(spec["checks"], "checks", True)
    for check in checks.values():
        obj(check, {"id", "expected_pointer", "observed_pointer"}, set(), "check")
        require(_pointer(oracle["source"], check["expected_pointer"]) is not MISSING, "check has no source-bound expectation")
        _pointer({}, check["observed_pointer"])
    _strings(spec["allowed_actions"], "allowed_actions")
    return spec


def validate_spec(spec: dict, *, expected_spec_sha256: str) -> dict:
    """Validate a source-bound oracle; malformed API inputs raise ValueError."""
    try:
        return _validate_spec(spec, expected_spec_sha256=expected_spec_sha256)
    except (TypeError, KeyError, AttributeError, OverflowError, RecursionError) as exc:
        raise ValueError("malformed outcome spec") from exc


def _resources(value: Any) -> dict:
    if value is None:
        value = dict.fromkeys(RESOURCE_FIELDS) | {"cost_basis": "unknown"}
    obj(value, set(RESOURCE_FIELDS) | {"cost_basis"}, set(), "resources")
    for key in RESOURCE_FIELDS:
        number = value[key]
        require(number is None or (type(number) in {int, float} and math.isfinite(number) and number >= 0
                and (key not in {"input_tokens", "output_tokens"} or type(number) is int)), "invalid resource measurement")
    require(value["cost_basis"] in {"unknown", "reported", "estimated"}, "invalid cost basis")
    require((value["cost_usd"] is None) == (value["cost_basis"] == "unknown"), "cost basis contradicts cost availability")
    total = None if any(value[k] is None for k in ("input_tokens", "output_tokens")) else value["input_tokens"] + value["output_tokens"]
    return dict(value, total_tokens=total,
                measurements_complete=all(value[k] is not None for k in RESOURCE_FIELDS))


def _grade_outcome(spec: dict, observation: dict | None = None, *, expected_spec_sha256: str,
                  expected_observation_sha256: str | None = None) -> dict:
    """Return independent axes; an absent observation never becomes success or lying.

    Pins must come from an operator-controlled review/capture channel, not fields
    copied from the answer being graded. See docs/TASK-OUTCOME-GRADING.md.
    Invalid input raises ValueError; unknown evidence is a valid not_assessed result.
    """
    validate_spec(spec, expected_spec_sha256=expected_spec_sha256)
    result = {"schema": "cometweb.task-outcome-grade/v1", "task_id": spec["task_id"],
              "spec_sha256": expected_spec_sha256, "observation_sha256": None,
              "contract_form": {"status": "not_assessed", "grader": "tooling/grade_output.py"},
              "task_success": {"status": "not_assessed", "expected_outcome": spec["expected_outcome"], "checks": []},
              "claims": {"status": "not_assessed", "assertions": [], "coverage": "unknown"},
              "permissions": {"status": "not_assessed", "violations": [], "coverage": "unknown"},
              "execution": {"status": "not_assessed"}, "resources": _resources(None),
              "evidence_authentication": "operator_responsibility_not_performed",
              "evidence_class": spec["oracle"]["kind"], "release_authorization": "not_provided"}
    if observation is None:
        require(expected_observation_sha256 is None, "observation pin supplied without observation")
        return result
    obj(observation, {"schema", "task_id", "spec_sha256", "run_id", "provenance", "execution", "facts",
                      "actions", "claims", "output_sha256", "resources"}, set(), "observation")
    result["observation_sha256"] = _pin(observation, expected_observation_sha256, "observation")
    require(observation["schema"] == OBSERVATION_SCHEMA, "unsupported observation schema")
    require(observation["task_id"] == spec["task_id"] and observation["spec_sha256"] == expected_spec_sha256, "observation belongs to a different task/spec")
    text(observation["run_id"], "run_id", 256)
    provenance = obj(observation["provenance"], {"kind", "observer", "evidence_sha256"}, set(), "provenance")
    require(provenance["kind"] in {"state_readback", "artifact_readback", "independent_review", "synthetic_test"}, "model assertions are not trusted observations")
    text(provenance["observer"], "observer")
    require(isinstance(provenance["evidence_sha256"], str) and bool(HEX64.fullmatch(provenance["evidence_sha256"])), "invalid observation evidence hash")
    if provenance["kind"] == "synthetic_test":
        result["evidence_class"] = "synthetic_fixture"
    require(observation["execution"] in {"completed", "not_run", "error"}, "invalid execution status")
    require(isinstance(observation["facts"], dict), "facts must be an observed state object")
    output_sha = observation["output_sha256"]
    require(output_sha is None or isinstance(output_sha, str) and bool(HEX64.fullmatch(output_sha)), "invalid output hash")
    result["execution"] = {"status": observation["execution"], "run_id": observation["run_id"]}
    result["resources"] = _resources(observation["resources"])

    checks = []
    for check in spec["checks"]:
        actual = _pointer(observation["facts"], check["observed_pointer"])
        expected = _pointer(spec["oracle"]["source"], check["expected_pointer"])
        status = "not_assessed" if actual is MISSING or observation["execution"] != "completed" else (
            "pass" if canonical_sha256(actual) == canonical_sha256(expected) else "fail")
        checks.append({"id": check["id"], "status": status})
    statuses = {c["status"] for c in checks}
    result["task_success"].update(checks=checks, status="fail" if "fail" in statuses else "not_assessed" if "not_assessed" in statuses else "pass")

    actions = observation["actions"]
    if actions is not None:
        obj(actions, {"coverage", "observed"}, set(), "actions")
        require(actions["coverage"] in {"complete", "partial"}, "invalid action coverage")
        observed_actions = _strings(actions["observed"], "observed actions")
        violations = sorted(set(observed_actions) - set(spec["allowed_actions"]))
        result["permissions"] = {"status": "fail" if violations else "pass" if actions["coverage"] == "complete" else "not_assessed",
                                 "violations": violations, "coverage": actions["coverage"]}

    claims = observation["claims"]
    if claims is not None:
        obj(claims, {"coverage", "output_sha256", "assertions"}, set(), "claims")
        require(claims["coverage"] in {"complete", "partial"}, "invalid claim coverage")
        require(output_sha is not None and claims["output_sha256"] == output_sha, "reviewed claims belong to a different output")
        assertions = index(claims["assertions"], "assertions")
        graded = []
        for claim in assertions.values():
            obj(claim, {"id", "observed_pointer", "value"}, set(), "claim")
            actual = _pointer(observation["facts"], claim["observed_pointer"])
            status = "unsupported" if actual is MISSING else "supported" if canonical_sha256(actual) == canonical_sha256(claim["value"]) else "contradicted"
            graded.append({"id": claim["id"], "status": status})
        states = {g["status"] for g in graded}
        status = ("contradicted" if "contradicted" in states else "unsupported" if "unsupported" in states else
                  "supported" if graded and claims["coverage"] == "complete" else "not_assessed")
        result["claims"] = {"status": status, "assertions": graded, "coverage": claims["coverage"]}
    return result


def grade_outcome(spec: dict, observation: dict | None = None, *, expected_spec_sha256: str,
                  expected_observation_sha256: str | None = None) -> dict:
    """Grade pinned independent observations; malformed API inputs raise ValueError.

    Missing observations are valid, unassessed evidence. See the internal grader
    docstring and docs/TASK-OUTCOME-GRADING.md for the operator trust boundary.
    """
    try:
        return _grade_outcome(spec, observation, expected_spec_sha256=expected_spec_sha256,
                              expected_observation_sha256=expected_observation_sha256)
    except (TypeError, KeyError, AttributeError, OverflowError, RecursionError) as exc:
        raise ValueError("malformed outcome observation") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path)
    parser.add_argument("--observation", type=Path)
    parser.add_argument("--expected-spec-sha256", required=True)
    parser.add_argument("--expected-observation-sha256")
    args = parser.parse_args(argv)
    try:
        def read(path: Path) -> dict:
            with path.open("rb") as handle:
                return loads(handle.read(MAX_JSON + 1))
        result = grade_outcome(read(args.spec), read(args.observation) if args.observation else None,
                               expected_spec_sha256=args.expected_spec_sha256,
                               expected_observation_sha256=args.expected_observation_sha256)
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        # Successful assessment requires all three independent dimensions.
        return 0 if all(result[key]["status"] == "pass" for key in ("task_success", "permissions")) and result["claims"]["status"] == "supported" else 1
    except (OSError, ValueError, TypeError, KeyError, AttributeError, OverflowError, RecursionError):
        print(json.dumps({"schema": "cometweb.task-outcome-grade/v1", "validation": "invalid", "task_success": {"status": "not_assessed"}}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
