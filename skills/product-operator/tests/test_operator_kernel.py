import importlib.util
import pathlib
import unittest

MODULE_PATH = pathlib.Path(__file__).parents[1] / "scripts" / "operator_kernel.py"
spec = importlib.util.spec_from_file_location("operator_kernel", MODULE_PATH)
kernel = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(kernel)


def ev(stage, source, claim="proof", freshness="CURRENT", claim_type=None):
    return {
        "stage": stage,
        "source": source,
        "authority": source,
        "locator": "x",
        "claim": claim,
        "claim_type": claim_type or stage,
        "freshness_status": freshness,
    }


class ProductOperatorKernelTests(unittest.TestCase):
    def test_low_materiality_polish_stays_later(self):
        row = {
            "id": "polish",
            "impact": 2,
            "goal_alignment": 2,
            "urgency": 1,
            "dependency_leverage": 0,
            "risk_reduction": 1,
            "learning_value": 0,
            "effort": 1,
            "confidence": 0.9,
            "evidence_strength": 0.9,
        }
        self.assertEqual(kernel.rank_candidate(row)["priority_tier"], "LATER")

    def test_high_impact_low_evidence_becomes_verify_now(self):
        row = {
            "id": "uncertain",
            "impact": 5,
            "goal_alignment": 5,
            "urgency": 4,
            "dependency_leverage": 4,
            "risk_reduction": 4,
            "learning_value": 5,
            "effort": 1,
            "confidence": 0.4,
            "evidence_strength": 0.4,
            "verify_first": True,
        }
        self.assertEqual(kernel.rank_candidate(row)["priority_tier"], "VERIFY_NOW")

    def test_learning_value_can_prioritize_uncertainty_reduction(self):
        row = {
            "id": "instrument",
            "impact": 2,
            "goal_alignment": 4,
            "urgency": 2,
            "dependency_leverage": 2,
            "risk_reduction": 2,
            "learning_value": 5,
            "effort": 1,
            "confidence": 0.85,
            "evidence_strength": 0.8,
        }
        self.assertIn(kernel.rank_candidate(row)["priority_tier"], {"NOW", "NEXT"})

    def test_notion_done_without_code_is_plan_ahead_of_code(self):
        item = {
            "id": "billing",
            "states": {"planned": "DONE", "implemented": "UNKNOWN", "verified": "UNKNOWN", "shipped": "UNKNOWN", "outcome": "UNKNOWN"},
            "evidence": [ev("planned", "notion")],
        }
        codes = {i["code"] for i in kernel.reconcile_item(item)}
        self.assertIn("PLAN_AHEAD_OF_CODE", codes)

    def test_wrong_authority_for_implementation_is_detected(self):
        item = {
            "id": "billing",
            "states": {"planned": "DONE", "implemented": "PRESENT", "verified": "UNKNOWN", "shipped": "UNKNOWN", "outcome": "UNKNOWN"},
            "evidence": [ev("planned", "notion"), ev("implemented", "notion")],
        }
        codes = {i["code"] for i in kernel.reconcile_item(item)}
        self.assertIn("IMPLEMENTED_EVIDENCE_WRONG_AUTHORITY", codes)

    def test_stale_required_current_evidence_blocks_admissibility(self):
        item = {
            "id": "checkout",
            "states": {"implemented": "PRESENT"},
            "evidence": [dict(ev("implemented", "github", freshness="STALE"), required_current=True)],
        }
        codes = {i["code"] for i in kernel.reconcile_item(item)}
        self.assertIn("CURRENT_EVIDENCE_NOT_ADMISSIBLE", codes)

    def test_shipped_outcome_gap_requires_outcome_required(self):
        item = {
            "id": "export",
            "states": {"planned": "DONE", "implemented": "PRESENT", "verified": "PASS", "shipped": "PRESENT", "outcome": "UNKNOWN"},
            "outcome_required": True,
            "evidence": [
                ev("planned", "notion"),
                ev("implemented", "github"),
                ev("verified", "test"),
                ev("shipped", "deployment"),
            ],
        }
        codes = {i["code"] for i in kernel.reconcile_item(item)}
        self.assertIn("SHIP_WITHOUT_OUTCOME_EVIDENCE", codes)

    def test_dependency_sequence_places_prerequisite_first(self):
        candidates = [
            {"id": "B", "depends_on": ["A"], "impact": 5, "goal_alignment": 5, "urgency": 5, "dependency_leverage": 4, "risk_reduction": 3, "effort": 1, "confidence": 0.9, "evidence_strength": 0.9},
            {"id": "A", "impact": 3, "goal_alignment": 4, "urgency": 4, "dependency_leverage": 5, "risk_reduction": 2, "effort": 1, "confidence": 0.9, "evidence_strength": 0.9},
        ]
        result = kernel.sequence_candidates(candidates)
        self.assertEqual([x["id"] for x in result["execution_order"]], ["A", "B"])
        self.assertTrue(result["is_acyclic"])

    def test_dependency_cycle_is_detected(self):
        candidates = [
            {"id": "A", "depends_on": ["B"], "impact": 3, "goal_alignment": 3, "effort": 1, "confidence": 0.9, "evidence_strength": 0.9},
            {"id": "B", "depends_on": ["A"], "impact": 3, "goal_alignment": 3, "effort": 1, "confidence": 0.9, "evidence_strength": 0.9},
        ]
        result = kernel.sequence_candidates(candidates)
        self.assertFalse(result["is_acyclic"])
        self.assertEqual(result["cycle_action_ids"], ["A", "B"])

    def test_readiness_blocked_by_current_evidence_gap(self):
        result = kernel.readiness_report({
            "goal_known": True,
            "material_current_evidence_block": True,
            "coverage": {"github": "verified", "notion": "verified", "product_context": "verified"},
        })
        self.assertEqual(result["status"], "BLOCKED")

    def test_readiness_provisional_with_missing_notion(self):
        result = kernel.readiness_report({
            "goal_known": True,
            "coverage": {"github": "verified", "notion": "unavailable", "product_context": "verified"},
        })
        self.assertEqual(result["status"], "PROVISIONAL")

    def test_snapshot_hash_is_deterministic(self):
        report = {"as_of": "2026-08-25T22:03:12+02:00", "target": "x", "goal": "ship", "horizon": "release", "state_items": []}
        a = kernel.snapshot_report(report)
        b = kernel.snapshot_report(report)
        self.assertEqual(a["snapshot_hash"], b["snapshot_hash"])
        self.assertEqual(a["state_fingerprint"], b["state_fingerprint"])

    def test_delta_detects_stage_transition(self):
        old = {"as_of": "2026-08-25T20:00:00+02:00", "target": "x", "goal": "ship", "horizon": "release", "state_items": [{"id": "A", "states": {"implemented": "UNKNOWN"}}]}
        new = {"as_of": "2026-08-25T22:00:00+02:00", "target": "x", "goal": "ship", "horizon": "release", "state_items": [{"id": "A", "states": {"implemented": "PRESENT"}, "evidence": [ev("implemented", "github")]}]}
        result = kernel.delta_reports(old, new)
        self.assertTrue(any(x.get("stage") == "implemented" and x.get("after") == "PRESENT" for x in result["state_transitions"]))

    def test_delta_flags_priority_thrash_when_state_is_identical(self):
        base = {"as_of": "2026-08-25T20:00:00+02:00", "target": "x", "goal": "ship", "horizon": "release", "state_items": [], "blockers": [], "drift": []}
        old = dict(base, now=[{"id": "A"}])
        new = dict(base, as_of="2026-08-25T22:00:00+02:00", next=[{"id": "A"}])
        result = kernel.delta_reports(old, new)
        self.assertTrue(result["priority_thrash"])

    def test_report_rejects_unbounded_now(self):
        action = {
            "id": "A",
            "action": "Do thing",
            "why_now": "Needed",
            "done_when": "Done",
            "confidence": 0.9,
            "evidence": [{"source": "github", "locator": "x", "claim": "y", "claim_type": "implementation", "freshness_status": "CURRENT"}],
        }
        report = {
            "protocol_version": "2.0",
            "as_of": "2026-08-25T22:03:12+02:00",
            "mode": "STANDARD",
            "target": "owner/repo",
            "goal": "ship",
            "horizon": "release",
            "decision": "do work",
            "coverage": {"github": "verified", "notion": "verified", "product_context": "verified", "outcome_data": "not-required"},
            "readiness": {"status": "READY", "reasons": []},
            "now": [dict(action, id=str(i)) for i in range(4)],
            "next": [],
        }
        result = kernel.validate_report(report)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any("NOW may contain at most 3" in err for err in result["errors"]))

    def test_report_rejects_ready_with_inadmissible_current_evidence(self):
        report = {
            "protocol_version": "2.0",
            "as_of": "2026-08-25T22:03:12+02:00",
            "mode": "STANDARD",
            "target": "owner/repo",
            "goal": "ship",
            "horizon": "release",
            "decision": "verify",
            "coverage": {"github": "verified", "notion": "verified", "product_context": "verified", "outcome_data": "not-required"},
            "readiness": {"status": "READY", "reasons": []},
            "state_items": [{
                "id": "A",
                "states": {"implemented": "PRESENT"},
                "evidence": [dict(ev("implemented", "github", freshness="STALE"), required_current=True)],
            }],
            "now": [],
            "next": [],
        }
        result = kernel.validate_report(report)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any("readiness cannot be READY" in err for err in result["errors"]))

    def test_state_fingerprint_ignores_evidence_observation_timestamp_only(self):
        a = {"target": "x", "goal": "ship", "horizon": "release", "state_items": [{"id": "A", "states": {"implemented": "PRESENT"}, "evidence": [dict(ev("implemented", "github"), observed_at="2026-08-25T20:00:00+02:00")]}]}
        b = {"target": "x", "goal": "ship", "horizon": "release", "state_items": [{"id": "A", "states": {"implemented": "PRESENT"}, "evidence": [dict(ev("implemented", "github"), observed_at="2026-08-25T22:00:00+02:00")]}]}
        self.assertEqual(kernel.sha256_json(kernel.stable_state_payload(a)), kernel.sha256_json(kernel.stable_state_payload(b)))

    def test_delta_reports_new_and_resolved_blockers(self):
        old = {"target": "x", "goal": "ship", "horizon": "release", "state_items": [], "blockers": [{"id": "B1"}]}
        new = {"target": "x", "goal": "ship", "horizon": "release", "state_items": [], "blockers": [{"id": "B2"}]}
        result = kernel.delta_reports(old, new)
        self.assertEqual(result["resolved_blockers"], ["B1"])
        self.assertEqual(result["new_blockers"], ["B2"])

    def test_outcome_required_missing_data_is_provisional(self):
        result = kernel.readiness_report({"goal_known": True, "outcome_required": True, "coverage": {"github": "verified", "notion": "verified", "product_context": "verified", "outcome_data": "unavailable"}})
        self.assertEqual(result["status"], "PROVISIONAL")


if __name__ == "__main__":
    unittest.main()
