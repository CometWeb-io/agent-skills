#!/usr/bin/env python3
"""Offline, allowlist-only receipt snapshots, OTLP/HTTP log payloads and resource drift.

No host/model execution, prices, prompt/output reads, network requests or collector
configuration. Free-form identities are exported only as SHA-256 fingerprints.
"""
from __future__ import annotations

import argparse
from decimal import Decimal
import hashlib
import json
import math
import os
from pathlib import Path
import stat
import time
from typing import Any

from audit_contracts import HEX64, MAX_JSON, array, index, loads, require

SCHEMA = "cometweb.runtime-observability/v1"
HASH_FIELDS = ("plan_sha256", "candidate_sha256", "payload_sha256", "benchmark_sha256",
               "rubric_sha256", "host_config_sha256", "run_config_sha256")
METRICS = ("input_tokens", "output_tokens", "elapsed_seconds", "cost_usd", "num_turns",
           "tool_calls", "retries", "reasoning_tokens", "context_tokens", "peak_memory_bytes")
CONDITIONS = {"plugin", "baseline", "native", "tools", "skill"}
HOSTS = {"claude", "codex", "cursor", "chatgpt", "qwen-code", "qoder", "lingma", "alibaba-skills-portal"}
STATUSES = {"executed": "completed", "not_run": "not_run", "error": "error", "setup_error": "error",
            "timeout": "error", "capture_limit": "error"}


def _sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _identity(value: Any) -> str | None:
    # No raw model, task, run, case or CLI-version strings cross the export boundary.
    return _sha(value) if isinstance(value, str) and value.strip() else None


def _hash(value: Any) -> str | None:
    require(value is None or isinstance(value, str) and bool(HEX64.fullmatch(value)), "invalid fingerprint")
    return value


def _frozen(data: dict, name: str) -> str | None:
    nested = data.get("frozen_hashes", {})
    require(isinstance(nested, dict), "invalid frozen hashes")
    direct, frozen = data.get(name), nested.get(name)
    require(direct is None or frozen is None or direct == frozen, "inconsistent frozen identity")
    return _hash(direct if direct is not None else frozen)


def _read(path: Path) -> dict:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(descriptor, "rb") as handle:
        info = os.fstat(handle.fileno())
        require(stat.S_ISREG(info.st_mode) and not path.is_symlink() and info.st_size <= MAX_JSON, "unsafe or oversized receipt file")
        return loads(handle.read(MAX_JSON + 1))


def _schema(data: dict, kind: str, versions: tuple[int, ...] = (1, 2)) -> None:
    require(data.get("schema") in {f"cometweb.real-host-eval-{kind}/v{v}" for v in versions}, "unsupported receipt schema")


def _number(value: Any, *, integer: bool) -> int | float | None:
    require(value is None or (type(value) in ({int} if integer else {int, float})
            and 0 <= value <= 2**63 - 1 and math.isfinite(value)), "invalid observed measurement")
    return value


def _display(value: Decimal) -> int | float:
    return int(value) if value == value.to_integral_value() else float(value)


def _metrics(record: dict) -> dict:
    resources = record.get("resources")
    if resources is None:
        resources = {}
    require(isinstance(resources, dict), "invalid resources")
    values = {}
    for field in METRICS:
        if field in record and field in resources:
            require(record[field] == resources[field], "conflicting resource observations")
        raw = record.get(field, resources.get(field))
        values[field] = _number(raw, integer=field not in {"elapsed_seconds", "cost_usd"})
    if "cost_source" in record and "cost_source" in resources:
        require(record["cost_source"] == resources["cost_source"], "conflicting cost provenance")
    source = record.get("cost_source", resources.get("cost_source"))
    if values["cost_usd"] is not None and source != "host_reported":
        values["cost_usd"] = None  # Price estimates and unlabelled numbers are not actual cost.
    if record["status"] == "not_run":
        require(all(value is None for value in values.values()), "unexecuted job carries execution measurements")
    return values


def _check_status(grade: dict | None, name: str, *, completed: bool) -> str | None:
    if grade is None or not completed:
        return None
    checks = grade.get("checks", {})
    require(isinstance(checks, dict), "invalid structural checks")
    check = checks.get(name, {})
    require(isinstance(check, dict), "invalid structural check")
    status = check.get("status")
    return status if isinstance(status, str) and status in {"pass", "fail"} else None


def _snapshot(root: Path) -> dict:
    require(root.is_dir() and not root.is_symlink(), "receipt root must be a real directory")
    manifest, plan = _read(root / "manifest.json"), _read(root / "plan.json")
    _schema(manifest, "run")
    _schema(plan, "plan", (1, 2, 3))
    plan_sha = _hash(plan.get("plan_sha256"))
    if plan_sha is not None:
        require(plan_sha == _sha({k: v for k, v in plan.items() if k != "plan_sha256"}), "plan fingerprint mismatch")
    identity = {name: _frozen(manifest, name) for name in HASH_FIELDS}
    require(identity["plan_sha256"] is None or identity["plan_sha256"] == plan_sha, "manifest belongs to a different plan")
    for name in HASH_FIELDS[1:-1]:
        planned = _frozen(plan, name)
        require(planned is None or identity[name] is None or planned == identity[name], "manifest changes frozen plan identity")
    host = manifest.get("host")
    require(host is None or isinstance(host, str) and host in HOSTS, "unsupported host identifier")
    identity["host_version_sha256"] = _identity(manifest.get("host_version"))
    identity["host"] = host if identity["host_version_sha256"] is not None else None
    experiment = manifest.get("experiment", {})
    require(isinstance(experiment, dict), "invalid experiment metadata")
    identity["harness_sha256"] = _hash(experiment.get("harness_sha256"))
    identity["bundled_tools_sha256"] = _hash(experiment.get("bundled_tools_sha256"))
    condition_payloads = experiment.get("condition_payload_sha256", {})
    require(isinstance(condition_payloads, dict), "invalid condition payload metadata")
    tasks = index(plan.get("tasks"), "tasks", True)
    grades = {}
    grades_path = root / "grades.json"
    if grades_path.exists() or grades_path.is_symlink():
        bundle = _read(grades_path)
        _schema(bundle, "grades")
        require(bundle.get("plan_sha256") == plan_sha, "grades belong to a different plan")
        for grade in array(bundle.get("results"), "grade results"):
            require(isinstance(grade, dict) and isinstance(grade.get("run_id"), str), "invalid grade identity")
            require(grade["run_id"] not in grades, "duplicate grade identity")
            grades[grade["run_id"]] = grade
    runs = root / "runs"
    require(runs.is_dir() and not runs.is_symlink(), "runs must be a real directory")
    directories = sorted(runs.iterdir())
    require(len(directories) <= 500 and all(p.is_dir() and not p.is_symlink() for p in directories), "unsafe or oversized run inventory")
    rows, cells, run_ids = [], set(), set()
    for directory in directories:
        record = _read(directory / "record.json")
        _schema(record, "record")
        rid, tid = record.get("run_id"), record.get("task_id")
        require(isinstance(rid, str) and bool(rid) and rid not in run_ids and isinstance(tid, str) and tid in tasks, "unknown or duplicated run/task")
        run_ids.add(rid)
        task = tasks[tid]
        condition, repeat = record.get("condition"), record.get("repeat")
        require(isinstance(condition, str) and condition in CONDITIONS and type(repeat) is int and 0 <= repeat <= 2**31 - 1, "invalid run cell")
        cell = (tid, condition, repeat)
        require(cell not in cells, "duplicate run cell")
        cells.add(cell)
        status = record.get("status")
        require(isinstance(status, str) and status in STATUSES, "unknown execution status")
        declared = record.get("execution_status")
        expected = "EXECUTED" if status == "executed" else "NOT_RUN" if status == "not_run" else "ERROR"
        require(declared is None or declared == expected, "inconsistent execution status")
        for name in HASH_FIELDS:
            per_run = _frozen(record, name)
            require(per_run is None or per_run == identity[name], "run changes manifest identity")
        payload = _hash(record.get("condition_payload_sha256", condition_payloads.get(condition)))
        if condition in condition_payloads:
            require(payload == _hash(condition_payloads[condition]), "run changes condition payload identity")
        grade = grades.pop(rid, None)
        if grade is not None:
            require(all(grade.get(key) == record.get(key) for key in ("task_id", "condition", "repeat"))
                    and grade.get("run_status") == status, "grade changes run identity/status")
        case_id, source = task.get("case_id"), task.get("source")
        sources = plan.get("sources", {})
        require(isinstance(sources, dict), "invalid source inventory")
        source_sha = _hash(sources.get(source)) if isinstance(source, str) else None
        case_sha = _sha({"id": case_id, "source": source, "source_sha256": source_sha}) if _identity(case_id) and source_sha else None
        metadata = record.get("metadata_status", {})
        require(isinstance(metadata, dict), "invalid metadata status")
        model = record.get("model") if metadata.get("model") in {None, "host_reported"} and status != "not_run" else None
        completed = status == "executed"
        rows.append({"run_id_sha256": _identity(rid), "record_sha256": _sha(record),
                     "task_id_sha256": _identity(tid), "task_sha256": _sha(task), "case_sha256": case_sha,
                     "condition": condition, "repeat": repeat, "condition_payload_sha256": payload,
                     "model_sha256": _identity(model), "status": status, "execution": STATUSES[status],
                     "metrics": _metrics(record), "output_contract": _check_status(grade, "output", completed=completed),
                     "routing": _check_status(grade, "routing", completed=completed), "task_success": None})
    require(not grades, "grades contain runs absent from receipts")
    planned_jobs = _number(manifest.get("planned_jobs"), integer=True)
    return {"schema": SCHEMA, "identity": identity, "planned_jobs": planned_jobs, "rows": rows,
            "inventory_complete": planned_jobs is not None and planned_jobs == len(rows),
            "evidence_class": "synthetic_fixture" if manifest.get("evidence_class") == "synthetic_fixture" else "unverified_receipts",
            "evidence_authentication": "not_performed", "task_quality": "not_assessed", "design": "three_arm" if plan["schema"].endswith("/v3") else "legacy"}


def read_receipts(root: Path) -> dict:
    """Read only manifest/plan/grades/record JSON, exporting a fixed privacy allowlist."""
    try:
        return _snapshot(Path(root))
    except (TypeError, KeyError, AttributeError, OverflowError, RecursionError) as exc:
        raise ValueError("malformed receipt fields") from exc


def _any(value: Any) -> dict:
    if value is None:
        return {}  # OTLP AnyValue with no oneof set means empty/unknown, never zero.
    if type(value) is bool:
        return {"boolValue": value}
    if type(value) is int:
        return {"intValue": str(value)}
    if type(value) is float:
        return {"doubleValue": value}
    if isinstance(value, str):
        return {"stringValue": value}
    if isinstance(value, list):
        return {"arrayValue": {"values": [_any(item) for item in value]}}
    return {"kvlistValue": {"values": [{"key": key, "value": _any(item)} for key, item in sorted(value.items())]}}


def export_otlp(root: Path) -> dict:
    """Build an ExportLogsServiceRequest JSON body; sending is always external."""
    snapshot = read_receipts(root)
    observed = str(time.time_ns())
    logs = [{"observedTimeUnixNano": observed, "body": _any({
        "schema": SCHEMA, "identity": snapshot["identity"], "evidence_class": snapshot["evidence_class"],
        "evidence_authentication": "not_performed", "inventory_complete": snapshot["inventory_complete"], **row})}
            for row in snapshot["rows"]]
    return {"resourceLogs": [{"resource": {"attributes": [{"key": "service.name", "value": {"stringValue": "cometweb-agent-skills-eval"}}]},
                              "scopeLogs": [{"scope": {"name": "tooling.runtime_observability"}, "logRecords": logs}]}]}


def compare_receipts(reference: Path, current: Path, thresholds: dict) -> dict:
    """Descriptive paired resource drift, gated on exact identities and explicit limits."""
    require(isinstance(thresholds, dict) and bool(thresholds) and thresholds.keys() <= set(METRICS), "thresholds must name observed resource metrics")
    for rule in thresholds.values():
        require(isinstance(rule, dict) and set(rule) == {"max_increase"}, "each metric requires explicit max_increase")
        require(_number(rule["max_increase"], integer=False) is not None, "threshold must be a finite nonnegative number")
    before, after = read_receipts(reference), read_receipts(current)
    blockers = []
    required = (*HASH_FIELDS, "host", "host_version_sha256")
    if before["design"] == "three_arm" or after["design"] == "three_arm":
        required += ("harness_sha256", "bundled_tools_sha256")
    for name in required:
        left, right = before["identity"][name], after["identity"][name]
        if left is None or right is None:
            blockers.append("missing_identity:" + name)
        elif left != right:
            blockers.append("identity_mismatch:" + name)
    for name in ("harness_sha256", "bundled_tools_sha256"):
        if before["identity"][name] != after["identity"][name]:
            blockers.append("identity_mismatch:" + name)
    if any(not s["inventory_complete"] or not s["rows"] for s in (before, after)):
        blockers.append("incomplete_inventory")

    def cells(snapshot):
        return {(r["task_id_sha256"], r["condition"], r["repeat"]): r for r in snapshot["rows"]}

    old, new = cells(before), cells(after)
    if old.keys() != new.keys():
        blockers.append("unmatched_run_cells")
    for key in old.keys() & new.keys():
        left, right = old[key], new[key]
        for field in ("task_sha256", "case_sha256", "model_sha256"):
            if left[field] is None or right[field] is None:
                blockers.append("missing_identity:" + field)
            elif left[field] != right[field]:
                blockers.append("identity_mismatch:" + field)
        if (before["design"] == "three_arm" or after["design"] == "three_arm") and (left["condition_payload_sha256"] is None or right["condition_payload_sha256"] is None):
            blockers.append("missing_identity:condition_payload_sha256")
        if left["condition_payload_sha256"] != right["condition_payload_sha256"]:
            blockers.append("identity_mismatch:condition_payload_sha256")
        if any(r["execution"] != "completed" for r in (left, right)):
            blockers.append("missing_completed_execution")
    axes, pending = {}, {}
    conditions = sorted({r["condition"] for r in before["rows"] + after["rows"]})
    for condition in conditions:
        for field, rule in sorted(thresholds.items()):
            left = [r["metrics"][field] for r in before["rows"] if r["condition"] == condition]
            right = [r["metrics"][field] for r in after["rows"] if r["condition"] == condition]
            available = bool(left) and bool(right) and all(v is not None for v in left + right)
            if not available:
                blockers.append("missing_measurement:" + field)
            axis_id = condition + ":" + field
            means = [sum(Decimal(str(v)) for v in values) / len(values) for values in (left, right)] if available else [None, None]
            if available:
                delta = means[1] - means[0]
                pending[axis_id] = (_display(delta), "threshold_exceeded" if delta > Decimal(str(rule["max_increase"])) else "within_threshold")
            axes[axis_id] = {
                "condition": condition, "metric": field,
                "reference_mean": _display(means[0]) if available else None,
                "current_mean": _display(means[1]) if available else None,
                "max_increase": rule["max_increase"], "absolute_delta": None, "status": "not_assessed"}
    blockers = sorted(set(blockers))
    if blockers:
        for axis in axes.values():
            axis.update(reference_mean=None, current_mean=None)
    else:
        for axis_id, axis in axes.items():
            delta, status = pending[axis_id]
            axis.update(absolute_delta=delta, status=status)
    return {"schema": "cometweb.runtime-drift/v1", "comparison_status": "blocked" if blockers else "compared",
            "blockers": blockers, "axes": axes, "paired_cells": len(old.keys() & new.keys()),
            "conclusion_scope": "descriptive_supplied_receipts_only", "task_quality": "not_assessed",
            "evidence_classes": sorted({before["evidence_class"], after["evidence_class"]}),
            "model_qualification": "not_provided", "evidence_authentication": "not_performed"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    export = commands.add_parser("export")
    export.add_argument("receipts", type=Path)
    export.add_argument("--format", choices=("json", "otlp"), default="json")
    drift = commands.add_parser("drift")
    drift.add_argument("reference", type=Path)
    drift.add_argument("current", type=Path)
    drift.add_argument("--thresholds", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "export":
            result = export_otlp(args.receipts) if args.format == "otlp" else read_receipts(args.receipts)
            code = 0
        else:
            result = compare_receipts(args.reference, args.current, _read(args.thresholds))
            code = 0 if result["comparison_status"] == "compared" and all(a["status"] == "within_threshold" for a in result["axes"].values()) else 1
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return code
    except (OSError, ValueError, TypeError, KeyError, AttributeError, OverflowError, RecursionError):
        print(json.dumps({"schema": SCHEMA, "validation": "invalid", "task_quality": "not_assessed"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
