#!/usr/bin/env python3
"""Deterministic eval cases for competitor-profiling.

Each case in evals/cases.json gives an input and the exact errors the
output-contract validator must return. Pin the exact list, not just "invalid":
a case that only asserts failure holds no single rule.

The rules live in scripts/output_contract.py, not here: eval_strength.py
measures a harness by disabling each `if` guard in the modules it imports, and
logic written inside this file is never measured.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from output_contract import validate  # noqa: E402


def cases() -> list[dict]:
    path = ROOT / "evals" / "cases.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else []


def run_case(case: dict) -> tuple[bool, str]:
    actual = validate(case["input"])
    expected = case["expected_errors"]
    return actual == expected, f"expected {expected}, got {actual}"


def main() -> int:
    args = sys.argv[1:]
    usage = "usage: run_evals.py [-h]\n  Runs evals/cases.json; takes no other arguments."
    if args in (["-h"], ["--help"]):
        print(usage)
        return 0
    if args:
        print(f"{usage}\nrun_evals.py: error: unrecognized arguments: {' '.join(args)}",
              file=sys.stderr)
        return 2
    rows = cases()
    if not rows:
        print("FAIL: no eval cases in evals/cases.json")
        return 1
    failures = []
    for case in rows:
        ok, detail = run_case(case)
        if not ok:
            failures.append({"id": case.get("id"), "detail": detail})
    print(json.dumps({"total": len(rows), "passed": len(rows) - len(failures),
                      "failures": failures,
                      "status": "PASS" if not failures else "FAIL"}, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
