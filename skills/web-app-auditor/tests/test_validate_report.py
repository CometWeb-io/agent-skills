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


if __name__ == "__main__":
    unittest.main()
