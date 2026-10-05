#!/usr/bin/env python3
"""Unit tests for web-app-auditor validate_report.py protocol invariants."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent


def _load_validator():
    path = ROOT / "scripts" / "validate_report.py"
    spec = importlib.util.spec_from_file_location("validate_report", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["validate_report"] = module
    spec.loader.exec_module(module)
    return module


validate_report = _load_validator()
validate = validate_report.validate


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _contract_trace() -> dict:
    return {
        "schema": "cometweb.contract-trace/v1",
        "revision": "a" * 40,
        "build": "build-1",
        "environment": "staging",
        "journey_id": "save",
        "claim": "bounded",
        "nodes": [
            {"id": "ui", "kind": "ui"},
            {"id": "api", "kind": "api"},
            {"id": "job", "kind": "job"},
            {"id": "durable", "kind": "durable"},
        ],
        "evidence": [
            {"id": "E1", "channel": "browser", "locator": "browser-run-1"},
            {"id": "E2", "channel": "joined", "locator": "joined-run-1"},
        ],
        "edges": [
            {"id": "ui-api", "from": "ui", "to": "api", "kind": "request", "state": "pass", "evidence_ids": ["E1"]},
            {"id": "api-job", "from": "api", "to": "job", "kind": "job", "state": "pass", "evidence_ids": ["E2"]},
            {"id": "job-durable", "from": "job", "to": "durable", "kind": "durable", "state": "pass", "evidence_ids": ["E2"]},
        ],
        "scenarios": [
            {"id": "happy", "kind": "happy", "status": "pass", "evidence_ids": ["E2"]},
            {"id": "null", "kind": "null_partial", "status": "pass", "evidence_ids": ["E2"]},
            {"id": "retry", "kind": "retry_duplicate", "status": "pass", "evidence_ids": ["E2"]},
            {"id": "tenant", "kind": "wrong_tenant", "status": "pass", "evidence_ids": ["E2"]},
            {"id": "rollback", "kind": "rollback", "status": "pass", "evidence_ids": ["E2"]},
        ],
    }


def _contract_report() -> dict:
    report = copy.deepcopy(_load("report-valid.json"))
    trace = _contract_trace()
    report["mode"] = "contract-trace"
    report["verdict"] = "incomplete"
    report["contractTrace"] = {
        "trace": trace,
        "result": validate_report.contract_trace_kernel.result(trace),
    }
    return report


class ValidateReportTests(unittest.TestCase):
    def test_valid_fixture_passes(self) -> None:
        result = validate(_load("report-valid.json"))
        self.assertEqual(result.errors, [])

    def test_invalid_fixture_fails(self) -> None:
        result = validate(_load("report-invalid.json"))
        self.assertTrue(result.errors)
        joined = "\n".join(result.errors)
        self.assertIn("incomplete", joined.lower())

    def test_blocker_with_ship_verdict_fails(self) -> None:
        report = _load("report-valid.json")
        report = copy.deepcopy(report)
        report["counts"]["blocker"] = 1
        report["verdict"] = "ship"
        report["findings"].append(
            {
                "id": "F-002",
                "kind": "defect",
                "severity": "blocker",
                "confidence": "high",
                "title": "Checkout unavailable",
                "where": {"route": "/billing", "viewport": "1280x800", "persona": "owner"},
                "repro": ["Open /billing"],
                "expected": "Checkout should load.",
                "expectedBasis": ["product-requirement"],
                "actual": "500 error",
                "evidence": ["E-001"],
                "impact": "Cannot pay",
                "rootCause": "unknown",
            }
        )
        result = validate(report)
        self.assertTrue(any("ship" in e.lower() for e in result.errors))

    def test_heuristic_blocker_without_basis_fails(self) -> None:
        report = _load("report-valid.json")
        report = copy.deepcopy(report)
        report["findings"][0]["severity"] = "blocker"
        report["findings"][0]["expectedBasis"] = ["heuristic"]
        report["counts"] = {
            "blocker": 1,
            "major": 0,
            "minor": 0,
            "nit": 0,
            "needsRepro": 0,
            "recommendations": 0,
        }
        report["verdict"] = "do_not_ship"
        result = validate(report)
        self.assertTrue(any("heuristic" in e.lower() or "blocker" in e.lower() for e in result.errors))

    def test_missing_evidence_reference_fails(self) -> None:
        report = _load("report-valid.json")
        report = copy.deepcopy(report)
        report["findings"][0]["evidence"] = ["E-999"]
        result = validate(report)
        self.assertTrue(any("E-999" in e or "evidence" in e.lower() for e in result.errors))

    def test_coverage_accounting_mismatch_fails(self) -> None:
        report = _load("report-valid.json")
        report = copy.deepcopy(report)
        report["coverage"]["tested"] = 99
        result = validate(report)
        self.assertTrue(result.errors)

    def test_wrong_schema_version_fails(self) -> None:
        report = _load("report-valid.json")
        report = copy.deepcopy(report)
        report["schemaVersion"] = "1.0"
        result = validate(report)
        self.assertTrue(any("schemaVersion" in e for e in result.errors))

    def test_contract_trace_report_requires_a_bound_kernel_result(self) -> None:
        report = _contract_report()
        self.assertEqual(validate(report).errors, [])

        report["contractTrace"]["result"]["result"] = "incomplete"
        result = validate(report)
        self.assertTrue(any("does not match" in error for error in result.errors))

    def test_incomplete_contract_trace_cannot_authorize_shipping(self) -> None:
        report = _contract_report()
        report["contractTrace"]["trace"]["claim"] = "incomplete"
        report["contractTrace"]["result"] = validate_report.contract_trace_kernel.result(
            report["contractTrace"]["trace"]
        )
        report["verdict"] = "ship"
        report["counts"] = {key: 0 for key in report["counts"]}
        report["findings"] = []
        report["coverage"] = {
            "totalInScope": 5,
            "tested": 5,
            "sampled": 0,
            "policyBlocked": 0,
            "environmentBlocked": 0,
            "unreachable": 0,
        }
        result = validate(report)
        self.assertTrue(any("incomplete contract trace" in error for error in result.errors))

    def test_browser_only_backend_proof_invalidates_contract_report(self) -> None:
        report = _contract_report()
        report["contractTrace"]["trace"]["edges"][1]["evidence_ids"] = ["E1"]
        report["contractTrace"]["result"] = validate_report.contract_trace_kernel.result(
            report["contractTrace"]["trace"]
        )
        result = validate(report)
        self.assertTrue(any("browser-evidence" in error for error in result.errors))

    def test_malformed_contract_trace_fails_closed(self) -> None:
        report = _contract_report()
        report["contractTrace"]["trace"]["nodes"] = None
        report["contractTrace"]["result"] = {
            "schema": "cometweb.contract-trace-result/v1",
            "status": "INVALID",
            "result": "incomplete",
            "errors": ["nodes:required-non-empty-list"],
        }
        result = validate(report)
        self.assertTrue(result.errors)

    def test_documented_validator_statuses_pass(self) -> None:
        for status in ("passed", "warnings", "not run"):
            with self.subTest(status=status):
                report = copy.deepcopy(_load("report-valid.json"))
                report["validator"] = status
                self.assertEqual(validate(report).errors, [])

    def test_undocumented_validator_statuses_fail(self) -> None:
        for status in ("pending", "bogus"):
            with self.subTest(status=status):
                report = copy.deepcopy(_load("report-valid.json"))
                report["validator"] = status
                result = validate(report)
                self.assertTrue(any("validator" in error for error in result.errors))

    def test_cli_valid_fixture_exits_zero(self) -> None:
        import subprocess

        proc = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "validate_report.py"),
                str(FIXTURES / "report-valid.json"),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)

    def test_cli_invalid_fixture_exits_nonzero(self) -> None:
        import subprocess

        proc = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "validate_report.py"),
                str(FIXTURES / "report-invalid.json"),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(proc.returncode, 0)

    def test_cli_missing_report_is_not_reported_as_encoding_error(self) -> None:
        import subprocess

        proc = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "validate_report.py"),
                str(FIXTURES / "does-not-exist.json"),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 2)
        self.assertIn("file not found", proc.stderr)
        self.assertNotIn("UTF-8", proc.stderr)

    def test_cli_invalid_utf8_report_has_encoding_error(self) -> None:
        import subprocess
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.json"
            path.write_bytes(b"\xff")
            proc = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "validate_report.py"),
                    str(path),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(proc.returncode, 2)
        self.assertIn("UTF-8", proc.stderr)


if __name__ == "__main__":
    unittest.main()
