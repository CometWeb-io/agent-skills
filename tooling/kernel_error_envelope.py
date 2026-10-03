#!/usr/bin/env python3
"""Hold every skill kernel to one error envelope for input it cannot use.

A host that builds a payload from the references gets it wrong sometimes: a
list where an object belongs, a string, `null`, a field of the wrong type. The
skill then has to say so in the shape the host already parses, not crash and
not answer in a shape of its own. Before this check, feedback-integrator
answered a non-object with `invalid[]` and no `errors`, content-writer reported
mode `DRAFT` for it although `FINAL` is the documented default, repair-operator
and rubric-designer dropped keys they document, and five command-line scripts
died with a traceback on a JSON file that held a list.

The envelope, for every `scripts/kernel.py` that a skill's contract declares as
taking a JSON payload (each has `evaluate_case`):

1. Any JSON value is answered with an object; nothing raises.
2. A payload that is not an object is refused with `errors` holding exactly one
   entry `<name>:not-object` (`payload:not-object` unless the reference names
   the payload, such as `brief` or `report`), the same entry whatever the
   wrong type was.
3. The status field (`status`, or `verdict` for a skill that decides) holds a
   value that is not a passing one; the passing values are the `pass` lists in
   the skill's `references/contract.json`.
4. Every refusal carries the keys the skill returns on all of its other
   refusals (taken from its own eval corpus), at their empty value: a host
   reading `missing_dimensions` or `effort_units` from an invalid result must
   find it there, whatever made the result invalid.
5. `errors` is always a list of strings, also for an empty object and for a
   valid case with one top-level field swapped for a value of the wrong type.

For every other script with an offline behaviour suite, each case that hands
the script a JSON object (as `input`, on stdin or in a `.json` file) is rerun
with `null`, a list and a string in its place, and the script must refuse it
without a Python traceback. Exit codes stay the script's own: some print
`valid: false` and exit 0 by design, and their suites pin that.

Run `python3 tooling/kernel_error_envelope.py` (exit 1 on any violation); it
also runs under pytest as `tooling/tests/test_kernel_error_envelope.py`.
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
BEHAVIOR = ROOT / "evals" / "behavior"
KERNEL = "scripts/kernel.py"
NOT_OBJECT = re.compile(r"^[a-z_]+:not-object$")
SHAPE_ERROR = re.compile(r"^[a-z_]+:not-(object|list)$")
NON_OBJECTS: tuple[Any, ...] = (None, [], [{}], "text", "", 0, 1.5, True)
# Values swapped into a valid case's top-level fields; each field gets every one
# whose JSON type differs from the original value's.
WRONG_TYPES: tuple[Any, ...] = ("text", 7, 2.5, True, None, [], ["x"], {}, {"x": 1})
CLI_NON_OBJECTS: tuple[Any, ...] = (None, [], "text")
TRACEBACK = "Traceback (most recent call last)"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader, f"cannot load {path}"
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.remove(str(path.parent))
    return module


def _contract(skill: str) -> dict:
    path = SKILLS / skill / "references" / "contract.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def library_kernels() -> list[str]:
    """Skills whose contract declares scripts/kernel.py as a JSON-payload kernel."""
    found = []
    for path in sorted(SKILLS.glob("*/" + KERNEL)):
        skill = path.parts[-3]
        spec = _contract(skill).get("scripts", {}).get(KERNEL, {})
        if spec.get("input") == "json" and spec.get("role") in {"kernel", "validator"}:
            found.append(skill)
    return found


def _passing(skill: str) -> set[str]:
    out: set[str] = set()
    for spec in _contract(skill).get("evals", []):
        out.update(spec.get("pass", []))
    return out


def _cases(skill: str) -> list[dict]:
    data = json.loads((SKILLS / skill / "evals" / "cases.json").read_text(encoding="utf-8"))
    rows = data.get("cases", []) if isinstance(data, dict) else data
    return [c for c in rows if isinstance(c, dict) and "raw_case" not in c and isinstance(c.get("input"), dict)]


def _status_key(result: dict) -> str | None:
    return "status" if "status" in result else ("verdict" if "verdict" in result else None)


def _shape_problems(label: str, result: Any) -> list[str]:
    if not isinstance(result, dict):
        return [f"{label}: returned {type(result).__name__}, not an object"]
    problems = []
    errors = result.get("errors")
    if not isinstance(errors, list) or not all(isinstance(e, str) for e in errors):
        problems.append(f"{label}: errors is {errors!r}, not a list of strings")
    if _status_key(result) is None:
        problems.append(f"{label}: has neither status nor verdict")
    return problems


def _call(kernel, case: Any) -> tuple[Any, str | None]:
    try:
        return kernel.evaluate_case(case), None
    except Exception as exc:  # noqa: BLE001 - any exception is the finding
        return None, f"{type(exc).__name__}: {exc}"


def _wrong_types(value: Any) -> list[Any]:
    def kind(v: Any) -> str:
        return "bool" if isinstance(v, bool) else ("number" if isinstance(v, (int, float)) else type(v).__name__)
    return [w for w in WRONG_TYPES if kind(w) != kind(value)]


def check_library_kernel(skill: str) -> list[str]:
    kernel = _load(SKILLS / skill / KERNEL, f"envelope_{skill.replace('-', '_')}")
    passing = _passing(skill)
    problems: list[str] = []

    # Rule 4 baseline: the keys every refusal of a well-formed payload carries.
    corpus = []
    for case in _cases(skill):
        if case.get("operation") is not None:
            continue
        result, crash = _call(kernel, case)
        if crash or not isinstance(result, dict):
            continue
        key = _status_key(result)
        if key and result.get(key) not in passing:
            corpus.append(result)
    clean = [r for r in corpus if not any(SHAPE_ERROR.match(e) for e in r.get("errors") or [] if isinstance(e, str))]
    required = set.intersection(*(set(r) for r in clean)) if clean else {"errors"}

    def refusal_problems(label: str, result: dict) -> list[str]:
        out = []
        key = _status_key(result)
        if key and result.get(key) in passing:
            out.append(f"{label}: {key} {result.get(key)!r} is a passing value")
        missing = sorted(required - set(result))
        if missing:
            out.append(f"{label}: refusal lacks {missing}, which every other refusal carries")
        return out

    names = set()
    # One line per distinct failure, naming the first non-object that hit it.
    refused: dict[str, list[str]] = {}
    for bad in NON_OBJECTS:
        for label, case in ((f"input {json.dumps(bad)}", {"input": bad}), (f"case {json.dumps(bad)}", bad)):
            result, crash = _call(kernel, case)
            found = [f"{label}: raised {crash}"] if crash else _shape_problems(label, result)
            if not found:
                errors = result["errors"]
                if len(errors) != 1 or not NOT_OBJECT.match(errors[0]):
                    found.append(f"{label}: errors is {errors!r}, expected one '<name>:not-object'")
                else:
                    names.add(errors[0])
                found += refusal_problems(label, result)
            for problem in found:
                refused.setdefault(problem.split(": ", 1)[1], []).append(label)
    for what, labels in sorted(refused.items()):
        more = f" (and {len(labels) - 1} more)" if len(labels) > 1 else ""
        problems.append(f"{skill}: {labels[0]}{more}: {what}")
    if len(names) > 1:
        problems.append(f"{skill}: a non-object payload is refused under several names {sorted(names)}")

    for result in corpus:
        if any(SHAPE_ERROR.match(e) for e in result.get("errors") or [] if isinstance(e, str)):
            problems += refusal_problems(f"{skill}: eval refusal {result.get('errors')}", result)

    result, crash = _call(kernel, {"input": {}})
    problems += [f"{skill}: input {{}}: raised {crash}"] if crash else _shape_problems(f"{skill}: input {{}}", result)

    # One line per field and failure, naming the first case and how many more hit it.
    swapped: dict[tuple[str, str], list[str]] = {}
    for case in _cases(skill):
        for field, value in case["input"].items():
            for wrong in _wrong_types(value):
                mutated = copy.deepcopy(case)
                mutated["input"][field] = wrong
                label = f"case {case.get('id')} with {field}={json.dumps(wrong)}"
                result, crash = _call(kernel, mutated)
                found = [f"raised {crash}"] if crash else [p.split(": ", 1)[1] for p in _shape_problems(label, result)]
                for what in found:
                    swapped.setdefault((field, what.split(":")[0]), []).append(f"{label}: {what}")
    for (field, _), hits in sorted(swapped.items()):
        more = f" (and {len(hits) - 1} more)" if len(hits) > 1 else ""
        problems.append(f"{skill}: wrong type in {field}: {hits[0]}{more}")
    return sorted(set(problems))


def _object_slots(case: dict) -> list[tuple[str, str | None]]:
    slots: list[tuple[str, str | None]] = []
    if "call" in case:
        return slots
    if isinstance(case.get("input"), dict):
        slots.append(("input", None))
    if isinstance(case.get("stdin"), dict):
        slots.append(("stdin", None))
    for name, content in (case.get("files") or {}).items():
        if name.endswith(".json") and isinstance(content, dict):
            slots.append(("files", name))
    return slots


def cli_probes() -> list[tuple[str, dict, str]]:
    """One mutated behaviour case per (skill, command, JSON slot, non-object value)."""
    probes, seen = [], set()
    for path in sorted(BEHAVIOR.glob("*/suite.json")):
        skill = path.parent.name
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not isinstance(data.get("cases"), list):
            continue
        for case in data["cases"]:
            if not isinstance(case, dict) or "run" not in case:
                continue
            command = tuple(a for a in case["run"][:2] if not a.startswith("{"))
            for kind, name in _object_slots(case):
                key = (skill, command, kind, name)
                if key in seen:
                    continue
                seen.add(key)
                for bad in CLI_NON_OBJECTS:
                    mutated = copy.deepcopy(case)
                    if kind == "files":
                        mutated["files"][name] = json.dumps(bad)
                    elif kind == "stdin":
                        mutated["stdin"] = json.dumps(bad)
                    else:
                        mutated["input"] = bad
                    mutated["id"] = f"{case.get('id')}[{kind}{':' + name if name else ''}={json.dumps(bad)}]"
                    probes.append((skill, mutated, " ".join(command)))
    return probes


def run_cli_probe(skill: str, case: dict) -> list[str]:
    """Run one mutated case and report a traceback; the exit code is not judged."""
    import subprocess

    runner = _load(ROOT / "tooling" / "run_behavior_evals.py", "envelope_behavior_runner")
    captured: dict[str, Any] = {}
    real_run = subprocess.run

    def capture(*args: Any, **kwargs: Any):
        proc = real_run(*args, **kwargs)
        captured["proc"] = proc
        return proc

    runner.subprocess = type("Subprocess", (), {"run": staticmethod(capture),
                                                "TimeoutExpired": subprocess.TimeoutExpired})
    case = {**case, "expect": {"exit_code": 0}}
    runner.run_command_case(skill, case)
    proc = captured.get("proc")
    if proc is None:
        return [f"{skill}#{case['id']}: did not run"]
    if TRACEBACK in proc.stderr:
        last = proc.stderr.strip().splitlines()[-1]
        return [f"{skill}#{case['id']}: traceback on non-object JSON: {last[:200]}"]
    return []


def check_cli(workers: int = 8) -> list[str]:
    probes = cli_probes()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = pool.map(lambda p: run_cli_probe(p[0], p[1]), probes)
    return sorted({problem for batch in results for problem in batch})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--skill", help="check one library kernel only")
    parser.add_argument("--no-cli", action="store_true", help="skip the command-line probes")
    args = parser.parse_args(argv)
    skills = [args.skill] if args.skill else library_kernels()
    problems = [p for skill in skills for p in check_library_kernel(skill)]
    if not args.no_cli and not args.skill:
        problems += check_cli()
    for problem in problems:
        print(problem)
    print(f"kernel error envelope: {len(skills)} library kernels"
          f"{'' if args.no_cli or args.skill else f', {len(cli_probes())} command probes'}, "
          f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
