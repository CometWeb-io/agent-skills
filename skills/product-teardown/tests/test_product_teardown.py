#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load_module(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = load_module("validator", ROOT / "scripts" / "validate_pattern_ledger.py")
scorer = load_module("scorer", ROOT / "scripts" / "score_patterns.py")


def valid_ledger(verdict: str = "ADOPT") -> dict:
    experiment = None
    if verdict == "EXPERIMENT":
        experiment = {
            "hypothesis": "Undo reduces destructive-action failures.",
            "test_type": "staged_rollout",
            "primary_metric": "destructive action recovery rate",
            "guardrail": "data integrity incidents",
            "baseline": "current recovery rate",
            "success_rule": "meaningful recovery increase with no integrity regression",
            "timebox_or_sample": "one staged cohort",
            "kill_criteria": "integrity or permission regression",
            "changes_verdict": "positive result promotes to ADOPT; negative result rejects",
        }

    transfer = {
        "problem_fit": 0.90,
        "mechanism_fit": 0.90,
        "source_evidence_strength": 0.90,
        "destination_evidence_strength": 0.85,
        "implementation_feasibility": 0.85,
        "expected_upside": 0.80,
        "reversibility": 0.90,
        "maintenance_fit": 0.80,
        "strategic_fit": 0.80,
        "differentiation": 0.60,
        "dependency_risk": 0.15,
        "complexity_tax": 0.15,
        "opportunity_cost": 0.15,
        "legal_ip_risk": 0.05,
        "security_privacy_risk": 0.05,
        "measurement_risk": 0.10,
    }

    return {
        "schema_version": "2.0",
        "shape": "SOURCE_TO_TARGET",
        "mode": "DEEP",
        "as_of": "2026-08-25T21:45:00+02:00",
        "source_targets": [
            {"id": "SRC-1", "name": "Source", "kind": "product", "version": "observed", "observed_at": "2026-08-25"}
        ],
        "destination": {"name": "Target", "kind": "repo_product"},
        "evidence": [
            {
                "evidence_id": "E-1",
                "subject": "source",
                "target_id": "SRC-1",
                "source": "source product",
                "locator": "delete flow",
                "source_type": "live_product",
                "claim_lane": "source_behavior",
                "claim_state": "OBSERVED",
                "observed_at": "2026-08-25",
                "note": "Undo is visible after deletion.",
                "confidence": 0.95,
                "independence_group": "source-live",
            },
            {
                "evidence_id": "E-2",
                "subject": "destination",
                "target_id": "DEST",
                "source": "target support",
                "locator": "recovery incidents",
                "source_type": "destination_internal",
                "claim_lane": "destination_problem",
                "claim_state": "OBSERVED",
                "observed_at": "2026-08-25",
                "note": "Users cannot recover accidental deletion.",
                "confidence": 0.90,
                "independence_group": "target-support",
            },
        ],
        "patterns": [
            {
                "id": "PT-1",
                "name": "Reversible destructive actions",
                "family_id": None,
                "category": "interaction",
                "problem": "Users need recovery from accidental destructive actions.",
                "mechanism": "Delay irreversible commitment and expose bounded undo.",
                "source_observation": "Source exposes undo after deletion.",
                "evidence_ids": ["E-1"],
                "target_evidence_ids": ["E-2"],
                "transfer": transfer,
                "gates": {"legal_ip": "clear", "security_privacy": "clear"},
                "implementation": {
                    "transfer_mode": "REIMPLEMENT",
                    "target_surfaces": ["delete flow"],
                    "prerequisites": ["reversible delete state"],
                    "steps": ["add reversible state", "surface undo", "instrument recovery"],
                    "effort_band": "medium",
                    "uncertainty": "medium",
                    "success_metric": "recovery rate",
                    "rollback": "disable undo and restore current behavior",
                    "kill_criteria": "integrity regression",
                },
                "experiment": experiment,
                "interactions": {
                    "requires": [],
                    "enables": [],
                    "conflicts_with": [],
                    "substitutes_for": [],
                    "bundles_with": [],
                },
                "confidence": {"source": 0.95, "mechanism": 0.85, "destination": 0.90, "execution": 0.80, "overall": 0.85},
                "verdict": verdict,
                "decision_reason": "Target problem is evidenced and transfer is feasible.",
            }
        ],
    }


class ValidatorTests(unittest.TestCase):
    def test_valid_adopt(self):
        self.assertEqual(validator.validate(valid_ledger("ADOPT")), [])

    def test_valid_experiment(self):
        self.assertEqual(validator.validate(valid_ledger("EXPERIMENT")), [])

    def test_adopt_requires_destination_problem_evidence(self):
        payload = valid_ledger("ADOPT")
        payload["evidence"][1]["claim_lane"] = "destination_constraint"
        errors = validator.validate(payload)
        self.assertTrue(any("ADOPT requires OBSERVED destination_problem evidence" in error for error in errors))

    def test_experiment_requires_spec(self):
        payload = valid_ledger("EXPERIMENT")
        payload["patterns"][0]["experiment"] = None
        errors = validator.validate(payload)
        self.assertTrue(any("EXPERIMENT requires experiment object" in error for error in errors))

    def test_blocked_gate_cannot_adopt(self):
        payload = valid_ledger("ADOPT")
        payload["patterns"][0]["gates"]["legal_ip"] = "block"
        errors = validator.validate(payload)
        self.assertTrue(any("ADOPT requires clear/not_required mandatory gates" in error for error in errors))

    def test_interaction_reference_must_exist(self):
        payload = valid_ledger("ADOPT")
        payload["patterns"][0]["interactions"]["requires"] = ["PT-404"]
        errors = validator.validate(payload)
        self.assertTrue(any("references unknown pattern: PT-404" in error for error in errors))


class ScorerTests(unittest.TestCase):
    def test_strong_pattern_suggests_adopt(self):
        pattern = valid_ledger("ADOPT")["patterns"][0]
        result = scorer.score_pattern(pattern)
        self.assertEqual(result["suggested_action"], "ADOPT")
        self.assertGreaterEqual(result["heuristic_score"], 76)

    def test_no_target_evidence_caps_at_candidate(self):
        pattern = valid_ledger("ADOPT")["patterns"][0]
        pattern["target_evidence_ids"] = []
        pattern["transfer"]["destination_evidence_strength"] = 0.0
        result = scorer.score_pattern(pattern)
        self.assertEqual(result["suggested_action"], "CANDIDATE")
        self.assertTrue(result["score_components"]["target_evidence_ceiling_applied"])

    def test_gate_overrides_high_score(self):
        pattern = valid_ledger("ADOPT")["patterns"][0]
        pattern["gates"]["security_privacy"] = "review"
        result = scorer.score_pattern(pattern)
        self.assertEqual(result["suggested_action"], "REVIEW_REQUIRED")

    def test_low_value_pattern_can_reject(self):
        pattern = valid_ledger("ADOPT")["patterns"][0]
        for key in scorer.POSITIVE_WEIGHTS:
            pattern["transfer"][key] = 0.20
        for key in scorer.PENALTY_WEIGHTS:
            pattern["transfer"][key] = 0.80
        pattern["transfer"]["destination_evidence_strength"] = 0.40
        pattern["target_evidence_ids"] = ["E-2"]
        result = scorer.score_pattern(pattern)
        self.assertEqual(result["suggested_action"], "REJECT")


if __name__ == "__main__":
    unittest.main()
