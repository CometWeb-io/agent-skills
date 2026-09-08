#!/usr/bin/env python3
import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("customer_ops_kernel", ROOT / "scripts" / "customer_ops_kernel.py")
mod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(mod)

COMMANDS = {
    "priority-assess": mod.priority_assess,
    "score-case": mod.priority_assess,
    "churn-risk": mod.churn_risk,
    "incident-severity": mod.incident_severity,
    "deadline-status": mod.deadline_status,
    "sla-status": mod.deadline_status,
    "dedupe-key": mod.dedupe_key,
    "dedupe-pair": mod.dedupe_pair,
    "case-gate": mod.case_gate,
    "commitment-status": mod.commitment_status,
    "transition": mod.transition_check,
    "privacy-scan": mod.privacy_scan,
}


class GoldenCaseTests(unittest.TestCase):
    def test_golden_cases(self):
        rows = json.loads((ROOT / "tests" / "golden-cases.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(rows), 10)
        for row in rows:
            with self.subTest(row=row["name"]):
                self.assertIn(row["command"], COMMANDS)
                out = COMMANDS[row["command"]](row["input"])
                for key, expected in row["expect"].items():
                    self.assertEqual(out.get(key), expected, f"{row['name']}: {key}")


if __name__ == "__main__":
    unittest.main()
