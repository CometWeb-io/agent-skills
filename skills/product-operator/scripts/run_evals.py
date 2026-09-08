#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
KERNEL_PATH = ROOT / "scripts" / "operator_kernel.py"
spec = importlib.util.spec_from_file_location("operator_kernel", KERNEL_PATH)
kernel = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(kernel)


def run_case(case: dict[str, Any]) -> tuple[bool, Any]:
    kind = case["kind"]
    payload = case["input"]
    expected = case["expect"]
    if kind == "reconcile_code":
        result = kernel.reconcile_items(payload)
        actual = {row["code"] for row in result["issues"]}
        return expected in actual, sorted(actual)
    if kind == "rank_tier":
        actual = kernel.rank_candidate(payload)["priority_tier"]
        return actual == expected, actual
    if kind == "sequence_order":
        actual = [row["id"] for row in kernel.sequence_candidates(payload)["execution_order"]]
        return actual == expected, actual
    if kind == "readiness_status":
        actual = kernel.readiness_report(payload)["status"]
        return actual == expected, actual
    if kind == "delta_thrash":
        result = kernel.delta_reports(payload["old"], payload["new"])
        actual = bool(result["priority_thrash"])
        return actual == expected, actual
    if kind == "validate_status":
        actual = kernel.validate_report(payload)["status"]
        return actual == expected, actual
    raise ValueError(f"unknown case kind: {kind}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Product Operator golden evals")
    parser.add_argument("--cases", default=str(ROOT / "evals" / "golden-cases.json"))
    args = parser.parse_args()
    cases = json.loads(pathlib.Path(args.cases).read_text(encoding="utf-8"))
    failures = []
    for case in cases:
        ok, actual = run_case(case)
        if not ok:
            failures.append({"id": case.get("id"), "expected": case.get("expect"), "actual": actual})
    result = {"status": "PASS" if not failures else "FAIL", "total": len(cases), "passed": len(cases) - len(failures), "failures": failures}
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
