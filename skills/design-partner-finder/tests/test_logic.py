from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import assess_partner_health  # noqa: E402
import score_candidate  # noqa: E402
import select_cohort  # noqa: E402


class ScoreResearchTests(unittest.TestCase):
    def good_payload(self):
        return {
            "candidate": "GoodCo",
            "engagement_mode": "DESIGN_PARTNER",
            "ratings": {
                "problem_evidence": 5,
                "representativeness": 4,
                "urgency": 5,
                "learning_value": 5,
                "implementation_plausibility": 4,
                "stakeholder_path": 4,
                "credibility": 4,
                "commercial_optionality": 3,
                "reference_network_value": 2,
            },
            "evidence_confidence": 4,
            "contradiction_risk": 1,
            "customization_risk": 1,
            "conflict_risk": 0,
            "professional_contact_path": True,
            "exploration_mode": False,
        }

    def test_priority_discovery_for_strong_research_candidate(self):
        result = score_candidate.score(self.good_payload(), "research")
        self.assertEqual(result["status"], "PRIORITY_DISCOVERY")
        self.assertEqual(result["recommended_action"], "CONTACT_FOR_DISCOVERY")

    def test_logo_without_pain_is_rejected(self):
        p = self.good_payload()
        p["ratings"]["problem_evidence"] = 1
        p["ratings"]["reference_network_value"] = 5
        result = score_candidate.score(p, "research")
        self.assertEqual(result["status"], "REJECT")
        self.assertLessEqual(result["score"], 49)

    def test_unverified_material_claim_holds(self):
        p = self.good_payload()
        p["ratings"]["credibility"] = 1
        result = score_candidate.score(p, "research")
        self.assertEqual(result["status"], "HOLD_VERIFY")

    def test_exploration_allows_low_representativeness_without_hard_reject(self):
        p = self.good_payload()
        p["ratings"]["representativeness"] = 1
        p["exploration_mode"] = True
        result = score_candidate.score(p, "research")
        self.assertNotEqual(result["status"], "REJECT")

    def test_string_boolean_is_rejected(self):
        p = self.good_payload()
        p["professional_contact_path"] = "false"
        with self.assertRaises(ValueError):
            score_candidate.score(p, "research")


class ScoreLiveTests(unittest.TestCase):
    def good_payload(self):
        return {
            "candidate": "ReadyCo",
            "engagement_mode": "DESIGN_PARTNER",
            "live_evidence_confirmed": True,
            "ratings": {
                "problem_confirmed": 5,
                "urgency_confirmed": 4,
                "user_champion_access": 4,
                "implementation_readiness": 4,
                "feedback_commitment": 5,
                "decision_procurement_feasibility": 3,
                "mutual_value_alignment": 5,
                "pilot_measurability": 4,
                "transferability": 4,
            },
            "customization_risk": 1,
            "conflict_risk": 0,
            "commercial_commitment": 0,
            "security_privacy_blocker": False,
            "legal_contract_blocker": False,
        }

    def test_live_candidate_can_be_partner_ready(self):
        result = score_candidate.score(self.good_payload(), "live")
        self.assertEqual(result["status"], "PARTNER_READY")

    def test_public_only_cannot_be_partner_ready(self):
        p = self.good_payload()
        p["live_evidence_confirmed"] = False
        result = score_candidate.score(p, "live")
        self.assertEqual(result["status"], "HOLD_VERIFY")

    def test_paid_pilot_requires_commercial_alignment(self):
        p = self.good_payload()
        p["engagement_mode"] = "PAID_PILOT"
        p["commercial_commitment"] = 0
        result = score_candidate.score(p, "live")
        self.assertEqual(result["status"], "ALIGNMENT_REQUIRED")
        self.assertIn("paid_pilot_commercial_commitment_insufficient", result["alignment_reasons"])

    def test_lighthouse_requires_reference_permission_for_lighthouse_readiness(self):
        p = self.good_payload()
        p["engagement_mode"] = "LIGHTHOUSE"
        p["reference_permission"] = None
        result = score_candidate.score(p, "live")
        self.assertEqual(result["status"], "ALIGNMENT_REQUIRED")

    def test_bespoke_pressure_caps_readiness(self):
        p = self.good_payload()
        p["customization_risk"] = 5
        result = score_candidate.score(p, "live")
        self.assertNotEqual(result["status"], "PARTNER_READY")
        self.assertLessEqual(result["score"], 64)


class CohortTests(unittest.TestCase):
    def test_active_cohort_prefers_uncovered_must_answer_question(self):
        payload = {
            "size": 2,
            "questions": [
                {"id": "H1", "weight": 5, "desired_replications": 1, "must_cover": True},
                {"id": "H2", "weight": 5, "desired_replications": 1, "must_cover": True},
            ],
            "max_per_duplicate_key": 1,
            "candidates": [
                {"company": "A", "score": 95, "status": "PARTNER_READY", "segment": "x", "duplicate_key": "same", "learning_coverage": {"H1": 5}, "effort": 1, "risk": 0},
                {"company": "B", "score": 94, "status": "PARTNER_READY", "segment": "x", "duplicate_key": "same", "learning_coverage": {"H1": 5}, "effort": 1, "risk": 0},
                {"company": "C", "score": 84, "status": "PARTNER_READY", "segment": "y", "duplicate_key": "other", "learning_coverage": {"H2": 5}, "effort": 1, "risk": 0},
            ],
        }
        result = select_cohort.select(payload, "active_cohort")
        companies = {c["company"] for c in result["selected"]}
        self.assertIn("C", companies)
        self.assertTrue(result["cohort_complete"])
        self.assertEqual(result["must_cover_unmet"], [])

    def test_active_cohort_excludes_alignment_by_default(self):
        payload = {
            "size": 1,
            "questions": [{"id": "H1", "weight": 1, "desired_replications": 1}],
            "candidates": [
                {"company": "A", "score": 95, "status": "ALIGNMENT_REQUIRED", "learning_coverage": {"H1": 5}},
                {"company": "B", "score": 80, "status": "PARTNER_READY", "learning_coverage": {"H1": 4}},
            ],
        }
        result = select_cohort.select(payload, "active_cohort")
        self.assertEqual(result["selected"][0]["company"], "B")

    def test_outreach_slate_uses_research_statuses(self):
        payload = {
            "size": 1,
            "questions": [{"id": "H1", "weight": 1, "desired_replications": 1}],
            "candidates": [
                {"company": "A", "score": 91, "status": "PRIORITY_DISCOVERY", "learning_coverage": {"H1": 5}},
                {"company": "B", "score": 99, "status": "PARTNER_READY", "learning_coverage": {"H1": 5}},
            ],
        }
        result = select_cohort.select(payload, "outreach_slate")
        self.assertEqual(result["selected"][0]["company"], "A")


class PartnerHealthTests(unittest.TestCase):
    def base_payload(self):
        return {
            "partner": "ActiveCo",
            "ratings": {
                "workflow_usage": 4,
                "learning_yield": 5,
                "user_champion_engagement": 4,
                "implementation_progress": 4,
                "feedback_quality": 4,
                "transferability": 4,
                "value_signal": 4,
            },
            "bespoke_pressure": 1,
            "support_burden": 1,
            "blocker_persistence": 0,
            "willingness_to_buy": 0,
            "product_ready_for_conversion": False,
            "timing_capacity_blocker": False,
        }

    def test_good_partner_continues(self):
        result = assess_partner_health.assess(self.base_payload())
        self.assertEqual(result["status"], "CONTINUE")

    def test_bespoke_low_learning_partner_triggers_exit_review(self):
        p = self.base_payload()
        p["ratings"]["learning_yield"] = 1
        p["bespoke_pressure"] = 5
        result = assess_partner_health.assess(p)
        self.assertEqual(result["status"], "EXIT_REVIEW")

    def test_conversion_is_separate_and_requires_product_readiness(self):
        p = self.base_payload()
        p["product_ready_for_conversion"] = True
        p["willingness_to_buy"] = 4
        result = assess_partner_health.assess(p)
        self.assertEqual(result["status"], "CONVERSION_CANDIDATE")


if __name__ == "__main__":
    unittest.main()
