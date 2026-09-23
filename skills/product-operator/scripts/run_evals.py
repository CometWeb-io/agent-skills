#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


KERNEL_PATH = ROOT / "scripts" / "operator_kernel.py"
kernel = _load("operator_kernel", KERNEL_PATH)
prepare_brief = _load("prepare_brief", ROOT / "scripts" / "prepare_brief.py")
self_check = _load("self_check", ROOT / "scripts" / "self_check.py")


def run_case(case: dict[str, Any]) -> tuple[bool, Any]:
    kind = case["kind"]
    payload = case["input"]
    expected = case["expect"]
    if kind == "reconcile_code":
        result = kernel.reconcile_items(payload)
        actual = {row["code"] for row in result["issues"]}
        # `expect` alone only proves a code fires. A guard whose removal swaps one
        # code for another then passes unnoticed, so a case may also pin what must
        # stay silent.
        forbidden = set(case.get("expect_absent") or ())
        return expected in actual and not (forbidden & actual), sorted(actual)
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
    if kind == "brief_readiness":
        result = prepare_brief.assemble(payload)
        actual = result["report"]["readiness"]["status"]
        return actual == expected, actual
    if kind == "brief_no_now_without_verify":
        result = prepare_brief.assemble(payload)
        has_now = bool(result["report"]["now"])
        has_verify = bool(result["report"]["verify_now"])
        ok = (not has_now) and has_verify and result["validation"]["status"] != "FAIL"
        return ok == expected, {"now": has_now, "verify_now": has_verify, "validation": result["validation"]["status"]}
    if kind == "brief_manifest_roundtrip":
        result = prepare_brief.assemble(payload)
        files = prepare_brief.artifacts(result)
        manifest = json.loads(files["BRIEF-MANIFEST.json"])
        ok = all(
            __import__("hashlib").sha256(files[name]).hexdigest() == digest
            for name, digest in manifest["files"].items()
        )
        return ok == expected, sorted(manifest["files"])
    if kind == "self_check_status":
        # Drive the package smoke path without spawning a nested process.
        required = [
            "SKILL.md", "VERSION", "LICENSE", "agents/openai.yaml", "assets/icon.svg",
            "scripts/prepare_brief.py", "scripts/self_check.py", "scripts/operator_kernel.py",
        ]
        ok = all((ROOT / name).is_file() and (ROOT / name).stat().st_size > 0 for name in required)
        sample = prepare_brief.read(ROOT / "examples" / "brief.synthetic.pl.json")
        assembled = prepare_brief.assemble(sample)
        ok = ok and assembled["validation"]["status"] != "FAIL"
        return ok == expected, ok
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
