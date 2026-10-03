#!/usr/bin/env python3
from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import json
import os
import pathlib
import shutil
import sys
import tempfile
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


_EVIDENCE = {"source": "github", "locator": "src/a.py", "claim": "exists", "claim_type": "implementation",
             "freshness_status": "CURRENT"}

# A report that validates PASS with no warning. validate_report cases override it
# one field at a time, so the exact error list a case pins belongs to that field.
VALID_REPORT: dict[str, Any] = {
    "protocol_version": "2.2", "as_of": "2026-09-25T12:00:00Z", "mode": "STANDARD",
    "target": "fixture/product", "goal": "Verify plan safety", "horizon": "one week",
    "decision": "verify the release path",
    "coverage": {"github": "verified", "notion": "verified", "product_context": "verified",
                 "outcome_data": "not-required"},
    "readiness": {"status": "READY", "reasons": []},
    "blockers": [], "verify_now": [], "decision_now": [],
    "now": [{"id": "A", "action": "Ship A", "done_when": "A deployed", "why_now": "on the path",
             "confidence": 0.8, "evidence": [_EVIDENCE]}],
    "next": [], "later": [], "stop": [], "watch": [],
}


def _override(base: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    out = json.loads(json.dumps(base))
    for key in payload.get("__drop__", []):
        out.pop(key, None)
    out.update({key: value for key, value in payload.items() if key != "__drop__"})
    return out


EXAMPLE_BRIEF = ROOT / "examples" / "brief.synthetic.pl.json"
BRIEF_OPTIONAL_KEYS = ("environment", "revision", "config_fingerprint", "coverage_exclusions",
                       "outcome_required", "unresolved_gate", "critical_gap_open",
                       "material_unknowns_open", "material_current_evidence_block",
                       "blocker_resolutions")


# prepare_brief loads its own copy of the kernel, so its InputError is a different class.
INPUT_ERRORS = (kernel.InputError, prepare_brief.kernel.InputError)


def _brief_input(spec: dict[str, Any]) -> dict[str, Any]:
    """The bundled synthetic brief with one case's fields replaced or dropped."""
    return _override(prepare_brief.read(EXAMPLE_BRIEF), spec.get("overrides") or {})


def _brief_previous(spec: Any) -> Any:
    if spec is None:
        return None
    if "report_overrides" in spec:
        # A snapshot whose hashes are intact but whose report does not validate.
        return kernel.snapshot_report(_override(VALID_REPORT, spec["report_overrides"]))
    return prepare_brief.assemble(_brief_input(spec))["snapshot"]


def _brief_result(payload: dict[str, Any]) -> dict[str, Any]:
    return prepare_brief.assemble(_brief_input(payload), previous=_brief_previous(payload.get("previous")))


def _brief_summary(result: dict[str, Any]) -> dict[str, Any]:
    report = result["report"]
    lanes = ("verify_now", "decision_now", "now", "next", "later", "stop")
    return {
        "mode": report["mode"],
        "readiness": report["readiness"]["status"],
        "reasons": report["readiness"]["reasons"],
        "lanes": {lane: [row["id"] for row in report[lane]] for lane in lanes},
        "copied": sorted(key for key in BRIEF_OPTIONAL_KEYS if key in report),
        "decision_origin": report["decision_origin"],
        "baseline_guard_ids": report.get("baseline_guard_ids"),
        "delta_status": result["delta"]["comparison_status"] if result["delta"] is not None else None,
        "files": sorted(prepare_brief.artifacts(result)),
    }


def _brief_fields(payload: dict[str, Any], expected: dict[str, Any]) -> dict[str, Any]:
    try:
        summary = _brief_summary(_brief_result(payload))
    except INPUT_ERRORS as exc:
        return {"error": str(exc)}
    return {key: summary.get(key) for key in expected}


def _brief_render(payload: dict[str, Any], expected: dict[str, Any]) -> tuple[bool, Any]:
    try:
        text = prepare_brief.render(_brief_result(payload), payload.get("language", "pl"))
    except INPUT_ERRORS as exc:
        actual = {"error": str(exc)}
        return actual == expected, actual
    missing = [part for part in expected.get("contains", []) if part not in text]
    present = [part for part in expected.get("absent", []) if part in text]
    ok = "error" not in expected and bool(expected.get("contains") or expected.get("absent"))
    return ok and not missing and not present, {"missing": missing, "unexpected": present}


def _outcome(call: Any) -> dict[str, Any]:
    """InputError message, other exception type, or the call's value."""
    try:
        return {"value": call()}
    except INPUT_ERRORS as exc:
        return {"error": str(exc)}
    except Exception as exc:  # noqa: BLE001 - the type is the observation
        return {"exception": type(exc).__name__}


def _brief_read(payload: dict[str, Any]) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as tmp:
        base = pathlib.Path(tmp)
        source = base / "input.json"
        scenario = payload.get("scenario", "file")
        if scenario == "oversize":
            source.write_bytes(b" " * prepare_brief.MAX_INPUT + b"{}")
        else:
            source.write_text(payload.get("text", "{}"), encoding="utf-8")
        target = source
        if scenario == "symlink":
            target = base / "link.json"
            target.symlink_to(source)
        elif scenario == "directory":
            target = base / "folder"
            target.mkdir()
        return _outcome(lambda: prepare_brief.read(target))


def _brief_publish(payload: dict[str, Any]) -> dict[str, Any]:
    files = {name: b"x" for name in payload.get("files", ["brief.md"])}
    with tempfile.TemporaryDirectory() as tmp:
        base = pathlib.Path(tmp)
        scenario = payload["scenario"]
        output = base / "out"
        if scenario == "symlink":
            (base / "real").mkdir()
            output.symlink_to(base / "real")
        elif scenario == "missing_parent":
            output = base / "absent" / "out"
        elif scenario == "inside_skill":
            output = ROOT / ".eval-publish-probe"
        try:
            result = _outcome(lambda: prepare_brief.publish(files, output))
            if "value" in result:
                result = {"written": sorted(p.name for p in output.iterdir())}
        finally:
            if scenario == "inside_skill" and output.is_dir():
                shutil.rmtree(output)
        return result


def _kernel_cli(payload: dict[str, Any]) -> dict[str, Any]:
    """Run the kernel CLI in-process; `{tmp}` in argv names a scratch directory."""
    with tempfile.TemporaryDirectory() as tmp:
        for name, value in (payload.get("files") or {}).items():
            pathlib.Path(tmp, name).write_text(json.dumps(value), encoding="utf-8")
        argv = [arg.replace("{tmp}", tmp) for arg in payload["argv"]]
        out, err = io.StringIO(), io.StringIO()
        old_argv, old_cwd = sys.argv, os.getcwd()
        try:
            sys.argv = ["operator_kernel.py", *argv]
            os.chdir(tmp)
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = kernel.main()
        finally:
            sys.argv = old_argv
            os.chdir(old_cwd)
        error = None
        if err.getvalue().strip():
            error = json.loads(err.getvalue()).get("error")
        stdout = json.loads(out.getvalue()) if out.getvalue().strip() else None
        return {"exit": code, "error": error, "stdout_status": stdout.get("status") if isinstance(stdout, dict) else None}


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
    if kind == "plan_contract":
        # Each case overrides a valid, fully covered synthetic plan.
        source = {
            "target": "fixture/product", "goal": "Verify plan safety",
            "horizon": "one week", "as_of": "2026-09-25T00:00:00Z",
            "coverage": {"github": "verified", "notion": "verified", "product_context": "verified"},
            **payload,
        }
        try:
            result = kernel.build_plan(source)
        except kernel.InputError as exc:
            actual = {"error": str(exc)}
        else:
            actual = {
                "immediate": [row["id"] for row in result["immediate_actions"]],
                "next": [row["id"] for row in result["next_actions"]],
                "held": result["held_by_readiness_action_ids"],
            }
        return actual == expected, actual
    if kind == "freshness_status":
        actual = kernel.evidence_freshness(payload["evidence"], payload["as_of"])
        return actual == expected, actual
    if kind == "delta_thrash":
        result = kernel.delta_reports(payload["old"], payload["new"])
        actual = bool(result["priority_thrash"])
        return actual == expected, actual
    if kind == "validate_status":
        actual = kernel.validate_report(payload)["status"]
        return actual == expected, actual
    if kind == "validate_report":
        # Status alone passes whenever any other rule also fails; the exact error and
        # warning lists say which rule fired.
        result = kernel.validate_report(_override(VALID_REPORT, payload) if isinstance(payload, dict) else payload)
        return result == expected, result
    if kind == "delta_fields":
        result = kernel.delta_reports(payload["old"], payload["new"])
        actual = {key: result.get(key) for key in expected}
        return bool(expected) and actual == expected, actual
    if kind == "unwrap_kind":
        try:
            _, integrity = kernel.unwrap_report(payload)
        except kernel.InputError as exc:
            actual = {"error": str(exc)}
        else:
            actual = {"kind": integrity["kind"]}
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
    if kind == "snapshot_integrity":
        snapshot = kernel.snapshot_report(payload["report"])
        if payload.get("tamper_field"):
            snapshot[payload["tamper_field"]] = "tampered"
        try:
            kernel.unwrap_report(snapshot)
        except kernel.InputError:
            actual = "rejected"
        else:
            actual = "accepted"
        return actual == expected, actual
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
    if kind == "sequence_fields":
        result = kernel.sequence_candidates(payload)
        result["execution_order"] = [row["id"] for row in result["execution_order"]]
        actual = {key: result.get(key) for key in expected}
        return bool(expected) and actual == expected, actual
    if kind == "reconcile_stages":
        # The stage an issue is attributed to, not only that the code fired.
        result = kernel.reconcile_items(payload)
        actual = sorted([row["code"], row.get("stage")] for row in result["issues"])
        return actual == expected, actual
    if kind == "brief_fields":
        actual = _brief_fields(payload, expected)
        return bool(expected) and actual == expected, actual
    if kind == "brief_render":
        return _brief_render(payload, expected)
    if kind == "brief_read":
        actual = _brief_read(payload)
        return actual == expected, actual
    if kind == "brief_publish":
        actual = _brief_publish(payload)
        return actual == expected, actual
    if kind == "kernel_cli":
        actual = _kernel_cli(payload)
        actual = {key: actual.get(key) for key in expected}
        return bool(expected) and actual == expected, actual
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
