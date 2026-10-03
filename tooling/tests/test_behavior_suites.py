"""Offline behavior suites: every skill that ships a script has one, and the runner is not hollow.

tooling/run_behavior_evals.py runs each skill's scripts the way its references
tell a user to and pins what comes back. These tests prove each rule of that
runner fails on a suite that breaks it, then check the tree is covered.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tooling"))
import run_behavior_evals as runner  # noqa: E402

SCRIPT = '''import json, sys
payload = json.loads(open(sys.argv[1]).read()) if len(sys.argv) > 1 else json.load(sys.stdin)
if not isinstance(payload, dict):
    print("payload is not an object", file=sys.stderr)
    raise SystemExit(2)
errors = [] if payload.get("mode") in {"A", "B"} else ["mode:invalid"]
print(json.dumps({"status": "INVALID" if errors else "VALID", "errors": errors}))
raise SystemExit(1 if errors else 0)
'''


def case(cid: str, kind: str = "accept", **extra) -> dict:
    data = {"id": cid, "kind": kind, "behavior": "a stated behavior", "run": ["scripts/check.py", "{input}"],
            "input": {"mode": "A"}, "expect": {"exit_code": 0, "json": {"status": "VALID", "errors": []}}}
    data.update(extra)
    return data


def good_cases() -> list[dict]:
    return [
        case("valid"),
        case("invalid", "refuse", input={"mode": "C"},
             expect={"exit_code": 1, "json": {"status": "INVALID", "errors": ["mode:invalid"]}}),
        case("not-object", "boundary", run=["scripts/check.py"], stdin=[1], input=None,
             expect={"exit_code": 2, "stderr_contains": ["not an object"]}),
    ]


@pytest.fixture
def tree(tmp_path, monkeypatch):
    skills, behavior = tmp_path / "skills", tmp_path / "evals" / "behavior"
    (skills / "demo" / "scripts").mkdir(parents=True)
    (skills / "demo" / "scripts" / "check.py").write_text(SCRIPT, encoding="utf-8")
    monkeypatch.setattr(runner, "SKILLS", skills)
    monkeypatch.setattr(runner, "BEHAVIOR", behavior)
    monkeypatch.setattr(runner, "ROOT", tmp_path)

    def write(cases=None, **top) -> tuple[int, list[str]]:
        cases = good_cases() if cases is None else cases
        for row in cases:
            if row.get("input", 0) is None:
                del row["input"]
        suite = {"schema": runner.COMMAND_SCHEMA, "skill": "demo", "cases": cases, **top}
        (behavior / "demo").mkdir(parents=True, exist_ok=True)
        (behavior / "demo" / "suite.json").write_text(json.dumps(suite), encoding="utf-8")
        return runner.run_command_suite("demo")
    return write


def test_a_good_suite_passes(tree) -> None:
    assert tree() == (3, [])


def test_a_skill_with_scripts_and_no_suite_fails(tree) -> None:
    count, problems = runner.run_command_suite("demo")
    assert count == 0 and problems == ["demo: ships scripts but has no evals/behavior/demo/suite.json"]


def test_a_changed_value_is_reported_with_its_path(tree) -> None:
    cases = good_cases()
    cases[1]["expect"]["json"]["errors"] = ["mode:missing"]
    assert tree(cases)[1] == ["demo#invalid: errors is ['mode:invalid'], expected ['mode:missing']"]


def test_a_wrong_exit_code_is_reported(tree) -> None:
    cases = good_cases()
    cases[1]["expect"]["exit_code"] = 0
    problems = tree(cases)[1]
    assert len(problems) == 1 and problems[0].startswith("demo#invalid: exit code 1, expected 0")


def test_a_missing_path_is_not_a_match(tree) -> None:
    cases = good_cases()
    cases[0]["expect"]["json"]["errors.0"] = "x"
    assert tree(cases)[1] == ["demo#valid: errors.0 is missing"]


def test_output_text_and_lengths_are_checked(tree) -> None:
    cases = good_cases()
    cases[0]["expect"].update({"stdout_contains": ["VALID"], "stdout_absent": ["INVALID"],
                               "json_len": {"errors": 0, "$": 2}})
    assert tree(cases) == (3, [])
    cases[0]["expect"].update({"stdout_absent": ["VALID"], "json_len": {"errors": 1}})
    assert tree(cases)[1] == ["demo#valid: errors has length 0, expected 1", "demo#valid: stdout contains 'VALID'"]


def test_files_and_placeholders_land_in_a_scratch_directory(tree) -> None:
    cases = good_cases()
    cases[0].pop("input")
    cases[0].update(run=["scripts/check.py", "{tmp}/nested/payload.json"],
                    files={"nested/payload.json": {"mode": "B"}})
    assert tree(cases) == (3, [])
    cases[0]["files"] = {"../outside.json": {"mode": "B"}}
    assert tree(cases)[1] == ["demo#valid: file '../outside.json' escapes the scratch directory"]


LIBRARY = '''
def review(payload, strict=False):
    if not isinstance(payload, dict):
        raise TypeError("payload must be an object")
    return {"status": "VALID" if payload.get("ok") or not strict else "INVALID"}
'''


def test_a_library_function_is_called_with_json_args(tree, tmp_path) -> None:
    (tmp_path / "skills" / "demo" / "scripts" / "lib.py").write_text(LIBRARY, encoding="utf-8")
    cases = good_cases() + [
        {"id": "call-strict", "kind": "refuse", "behavior": "strict review refuses", "run": ["scripts/lib.py"],
         "call": "review", "args": [{"ok": False}, True], "expect": {"exit_code": 0, "json": {"status": "INVALID"}}},
        {"id": "call-raises", "kind": "boundary", "behavior": "a list is refused", "run": ["scripts/lib.py"],
         "call": "review", "args": [[]], "expect": {"exit_code": 1, "stderr_contains": ["payload must be an object"]}},
    ]
    assert tree(cases) == (5, [])
    cases[3]["expect"]["json"]["status"] = "VALID"
    assert tree(cases)[1] == ["demo#call-strict: status is 'INVALID', expected 'VALID'"]


@pytest.mark.parametrize("extra,problem", [
    ({"call": "review"}, "call needs args, a list of the function's arguments"),
    ({"call": "not a name", "args": []}, "call must name a function"),
    ({"call": "review", "args": [], "stdin": "{}"}, "a call takes its arguments from args only"),
    ({"args": []}, "args belongs to a call"),
])
def test_call_cases_are_checked(tree, tmp_path, extra, problem) -> None:
    (tmp_path / "skills" / "demo" / "scripts" / "lib.py").write_text(LIBRARY, encoding="utf-8")
    row = {"id": "c", "kind": "accept", "behavior": "b", "run": ["scripts/lib.py"],
           "expect": {"exit_code": 0, "json": {"status": "VALID"}}, **extra}
    assert f"demo#c: {problem}" in tree(good_cases() + [row])[1]


@pytest.mark.parametrize("mutate,problem", [
    (lambda c: c.pop(), "demo: needs at least 3 cases"),
    (lambda c: c[1].update(kind="accept"), "demo: no refuse case"),
    (lambda c: c[0].update(kind="happy"), "demo#valid: kind must be one of ['accept', 'boundary', 'refuse']"),
    (lambda c: c[0].update(behavior=" "), "demo#valid: state the behavior the case holds"),
    (lambda c: c[0].update(run=["tooling/x.py"]), "demo#valid: 'tooling/x.py' is not a script under scripts/"),
    (lambda c: c[0].update(expect={"exit_code": 0}),
     "demo#valid: an exit code alone pins nothing; add json or output text"),
    (lambda c: c[0].update(expect={"json": {}}), "demo#valid: expect.exit_code is required"),
    (lambda c: c[0].update(expected={}), "demo#valid: unknown keys ['expected']"),
    (lambda c: c[2].update(id="valid"), "demo#valid: id must be unique and non-empty"),
])
def test_suite_shape_is_checked_before_anything_runs(tree, mutate, problem) -> None:
    cases = good_cases()
    mutate(cases)
    count, problems = tree(cases)
    assert count == 0 and problem in problems


def test_suite_must_name_its_schema_and_skill(tree) -> None:
    assert tree(schema="other")[1] == ["demo: suite schema must be cometweb.behavior-suite/v1"]
    assert tree(skill="else")[1] == ["demo: suite names skill 'else'"]


def test_coverage_counts_cases_per_skill(tree) -> None:
    assert runner.coverage() == [("demo", 0)]
    tree()
    assert runner.coverage() == [("demo", 3)]


def test_every_skill_with_scripts_has_offline_behavior_cases() -> None:
    missing = [skill for skill, count in runner.coverage() if count < runner.MIN_COMMAND_CASES]
    assert not missing, f"skills that ship scripts without a behavior suite: {missing}"
