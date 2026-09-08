import ast
import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
KERNEL = ROOT / "scripts" / "council_kernel.py"
spec = importlib.util.spec_from_file_location("council_kernel", KERNEL)
k = importlib.util.module_from_spec(spec)
spec.loader.exec_module(k)


class CouncilKernelV5Tests(unittest.TestCase):
    def test_no_duplicate_top_level_function_names(self):
        tree = ast.parse(KERNEL.read_text(encoding="utf-8"))
        names = [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        self.assertEqual(len(names), len(set(names)))

    def test_fast_budget_has_three_advisers(self):
        self.assertEqual(k.mode_budget("FAST")["adviser_count"], 3)
        profile = k.profile_problem("Mały test CTA, pilot reversible")
        experts = k.route_experts(profile, k.mode_budget("FAST")["adviser_count"])
        self.assertEqual(len(experts), 3)

    def test_high_irreversible_never_fast(self):
        contract = k.compile_decision_contract(
            "Czy przejąć konkurenta za milion? Duża inwestycja, trudna do odwrócenia",
            {"financial_impact": 0.95, "strategic_impact": 0.9, "uncertainty": 0.8},
        )
        self.assertEqual(k.choose_council_mode(contract), "DEEP")

    def test_fast_framework_budget_is_enforced(self):
        contract = k.compile_decision_contract("Mały test pricingu oferty", {"risk_level": "low", "financial_impact": 0.1, "strategic_impact": 0.1, "uncertainty": 0.2})
        plan = k.plan_council(contract, "FAST")
        self.assertLessEqual(len(plan["frameworks"]["matches"]), 1)

    def test_unknown_independence_does_not_inflate_coverage(self):
        rows = [
            {"accepted": True, "critical_area": "market_demand", "source_quality": 1.0, "directness": 1.0}
            for _ in range(20)
        ]
        report = k.evidence_coverage_report(rows, ["market_demand"])
        self.assertEqual(report["independent_source_count"], 0)
        self.assertEqual(report["unknown_independence_sources"], 20)
        self.assertLessEqual(report["overall"], 0.55)

    def test_gate_is_symmetric_for_low_confidence_no_go(self):
        result = k.gate_verdict("NO-GO", 0.6, 0.8, True)
        self.assertEqual(result, "TEST")

    def test_block_cannot_be_majority_overridden(self):
        result = k.gate_verdict("GO", 0.99, 0.8, True, gate_statuses={"legal": "BLOCK"}, controls_implemented=True)
        self.assertEqual(result, "NO-GO")

    def test_counsel_required_defers(self):
        result = k.gate_verdict("GO", 0.99, 0.8, True, gate_statuses={"legal": "COUNSEL_REQUIRED"})
        self.assertEqual(result, "DEFER")

    def test_full_experiment_contract(self):
        spec = k.build_experiment_spec(
            "H", "conversion", "10%", ">=12%", "<9%", "14d", "5000 PLN", "1000 sessions",
            ["refunds <= baseline"], "2pp", ["security incident", "CAC > 600"], "wtp_gap", "cac_under_450", "growth", "2026-09-15",
        )
        for field in ("hypothesis", "primary_metric", "baseline", "pass_threshold", "fail_threshold", "duration", "budget", "sample", "guardrails", "kill_criteria", "decision_rule", "evidence_gap_addressed", "assumption_key"):
            self.assertIn(field, spec)
        self.assertTrue(spec["kill_criteria"])

    def test_same_model_consensus_is_adjusted_down(self):
        memos = [
            {"expert_id": f"e{i}", "vote": "GO", "frameworks": ["strategic_choice"], "independence_groups": ["g1"], "claim_ids": ["c1"]}
            for i in range(5)
        ]
        report = k.consensus_report(memos)
        self.assertEqual(report["raw_consensus"], 1.0)
        self.assertLess(report["adjusted_consensus"], 1.0)
        self.assertLess(report["effective_independent_perspectives"], 5)

    def test_minority_sentinel_protects_unique_material_dissent(self):
        memos = [
            {"expert_id": "strategy", "vote": "GO", "independence_groups": ["g1"], "assumptions": []},
            {"expert_id": "product_customer", "vote": "GO", "independence_groups": ["g1"], "assumptions": []},
            {"expert_id": "legal", "role_class": "gatekeeper", "vote": "DEFER", "independence_groups": ["legal-primary"], "decision_impact": 1.0,
             "assumptions": [{"key": "law_applies", "importance": 1.0, "uncertainty": 0.8}]},
        ]
        report = k.minority_sentinel(memos)
        self.assertTrue(report["must_surface"])
        self.assertEqual(report["protected_minority"][0]["expert_id"], "legal")

    def test_voi_recommends_evidence_when_positive(self):
        report = k.value_of_information(0.35, 300000, 5000, 1000)
        self.assertGreater(report["net_value_of_information"], 0)
        self.assertEqual(report["recommendation"], "GATHER_EVIDENCE")

    def test_stop_rule_never_stops_with_unresolved_mandatory_gate(self):
        report = k.deliberation_stop(0.01, 1.0, 5, unresolved_mandatory_gate=True)
        self.assertFalse(report["stop"])

    def test_legal_router_detects_privacy_and_ai(self):
        report = k.route_legal_risk("Deploy AI employee scoring under GDPR in EU", {"jurisdictions": ["EU"]})
        self.assertTrue(report["required"])
        self.assertIn("privacy_data_protection", report["legal_domains"])
        self.assertIn("ai_regulation", report["legal_domains"])
        self.assertIn("employment", report["legal_domains"])

    def test_decision_key_changes_with_material_context(self):
        a = k.make_decision_key("Czy wejść na rynek?", "2026-08-24", {"decision_type": "market_entry", "options": ["DE"]})
        b = k.make_decision_key("Czy wejść na rynek?", "2026-08-24", {"decision_type": "market_entry", "options": ["FR"]})
        self.assertNotEqual(a, b)

    def test_framework_utility_not_double_wrapped(self):
        report = k.framework_usefulness(True, False, False, False, False)
        self.assertEqual(report["utility_score"], 0.25)
        self.assertIsInstance(report["utility_score"], float)

    def test_golden_decisions(self):
        cases = json.loads((ROOT / "tests" / "golden-decisions.json").read_text(encoding="utf-8"))
        for case in cases:
            with self.subTest(case=case["name"]):
                contract = k.compile_decision_contract(case["query"], case.get("context") or {})
                mode = k.choose_council_mode(contract)
                plan = k.plan_council(contract, mode)
                if case.get("expected_mode"):
                    self.assertEqual(mode, case["expected_mode"])
                roles = set(plan["roles"]["advisers"] + plan["roles"]["specialists"] + plan["roles"]["gatekeepers"])
                for role in case.get("required_roles", []):
                    self.assertIn(role, roles)


    def test_plan_requires_temporal_truth_and_freshness_gate(self):
        contract = k.compile_decision_contract("Czy wejść na rynek niemiecki?", {"jurisdictions": ["EU"]})
        plan = k.plan_council(contract, "STANDARD")
        self.assertIn("temporal_truth", plan["required_stages"])
        self.assertIn("freshness_gate", plan["required_stages"])
        self.assertTrue(plan["temporal_requirements"]["as_of_required"])

    def test_material_law_requires_live_verification_for_decision(self):
        row = {"claim_id": "law", "claim_type": "law_regulation", "material": True,
               "last_verified_at": "2026-08-24T16:00:00+00:00", "verified_for_decision": False}
        report = k.evaluate_temporal_truth(row, "2026-08-24T17:00:00+00:00")
        self.assertEqual(report["status"], "STALE")
        self.assertFalse(report["admissible"])

    def test_verified_material_law_is_current(self):
        row = {"claim_id": "law", "claim_type": "law_regulation", "material": True,
               "last_verified_at": "2026-08-24T16:00:00+00:00", "verified_for_decision": True}
        report = k.evaluate_temporal_truth(row, "2026-08-24T17:00:00+00:00")
        self.assertEqual(report["status"], "CURRENT")
        self.assertTrue(report["admissible"])

    def test_future_effective_rule_is_not_current(self):
        row = {"claim_id": "future", "claim_type": "law_regulation", "material": True,
               "last_verified_at": "2026-08-24T16:00:00+00:00", "verified_for_decision": True,
               "effective_from": "2026-09-01T00:00:00+00:00"}
        report = k.evaluate_temporal_truth(row, "2026-08-24T17:00:00+00:00")
        self.assertEqual(report["status"], "NOT_YET_EFFECTIVE")
        self.assertFalse(report["admissible"])

    def test_superseded_source_is_not_admissible(self):
        row = {"claim_id": "old", "claim_type": "official_technical_docs", "material": True,
               "last_verified_at": "2026-08-24T16:00:00+00:00", "superseded_by": "v2"}
        report = k.evaluate_temporal_truth(row, "2026-08-24T17:00:00+00:00")
        self.assertEqual(report["status"], "SUPERSEDED")
        self.assertFalse(report["admissible"])

    def test_stale_competitor_price_blocks_freshness_gate(self):
        rows = [{"claim_id": "price", "claim_type": "competitor_pricing", "material": True,
                 "last_verified_at": "2026-08-23T10:00:00+00:00"}]
        report = k.freshness_gate(rows, "2026-08-24T17:00:00+00:00")
        self.assertEqual(report["status"], "REFRESH_REQUIRED")
        self.assertFalse(report["decision_ready"])

    def test_doctrine_is_versioned_not_ttl_based(self):
        report = k.evaluate_temporal_truth({"claim_id": "d", "claim_type": "doctrine", "material": False, "source_version": "book-v1"}, "2026-08-24T17:00:00+00:00")
        self.assertEqual(report["status"], "CURRENT")

    def test_source_authority_registry_is_claim_specific(self):
        legal = k.source_authority_for_claim("law_regulation")
        pricing = k.source_authority_for_claim("competitor_pricing")
        self.assertIn("official_legislation", legal["preferred_authority"])
        self.assertIn("official_competitor_pricing", pricing["preferred_authority"])
        self.assertNotEqual(legal["freshness_policy"], pricing["freshness_policy"])

    def test_internal_context_router_uses_system_of_record(self):
        report = k.route_internal_context("Sprawdź repo i aktualny branch na GitHub")
        self.assertIn("GitHub", report["primary"]["systems"])

    def test_high_materiality_watch_change_reopens_decision(self):
        deps = [{"dependency_id": "price", "operator": "changed", "previous": 10, "current": 12, "materiality": 0.9, "assumption_keys": ["pricing"]}]
        report = k.decision_validity_overlay({}, deps, "2026-08-24T17:00:00+00:00")
        self.assertEqual(report["status"], "REOPEN")
        self.assertIn("pricing", report["affected_assumptions"])

    def test_critical_unresolved_contradiction_blocks_readiness(self):
        claims = [{"claim_id": "c1", "material": True, "importance": 0.95, "contradiction_tested": True,
                   "opposing_evidence_count": 1, "contradiction_resolved": False}]
        report = k.contradiction_coverage(claims)
        self.assertFalse(report["decision_ready"])
        self.assertEqual(report["critical_unresolved_claim_ids"], ["c1"])

    def test_independence_grade_recognizes_human_and_model_diversity(self):
        memos = [
            {"expert_id": "a", "provider": "p1", "model_family": "m1", "independence_groups": ["g1"]},
            {"expert_id": "b", "provider": "p2", "model_family": "m2", "independence_groups": ["g2"]},
            {"expert_id": "c", "actor_type": "human"},
        ]
        report = k.independence_grade_report(memos)
        by_id = {r["expert_id"]: r["grade"] for r in report["grades"]}
        self.assertEqual(by_id["c"], "I4")
        self.assertEqual(by_id["a"], "I3")

    def test_forecast_score_perfect_predictions(self):
        report = k.forecast_score_report([{"probability": 1.0, "outcome": 1}, {"probability": 0.0, "outcome": 0}])
        self.assertEqual(report["brier_score"], 0.0)

    def test_base_rate_requires_enough_resolved_cases(self):
        rows = [{"memory_status": "Complete", "decision_type": "market_entry", "outcome": "Success", "regime_tags": ["b2b"]} for _ in range(4)]
        report = k.base_rate_report(rows, "market_entry", ["b2b"])
        self.assertEqual(report["n"], 4)
        self.assertFalse(report["usable_as_prior"])

    def test_portfolio_detects_capacity_conflict(self):
        decisions = [
            {"decision_id": "A", "resource_claims": {"engineering": 6}, "expected_value": 100},
            {"decision_id": "B", "resource_claims": {"engineering": 5}, "expected_value": 80},
        ]
        report = k.portfolio_report(decisions, {"engineering": 10})
        self.assertEqual(report["capacity_conflicts"][0]["over_by"], 1.0)

    def test_human_handoff_packet_is_bounded(self):
        packet = k.build_human_handoff_packet("legal", {"question": "Launch?", "decision_key": "d1", "jurisdictions": ["EU"]}, {"question": "Does Article X apply?"})
        self.assertEqual(packet["packet_type"], "COUNSEL_PACKET")
        self.assertTrue(packet["scope_is_bounded"])

    def test_sensitive_irreversible_tool_action_requires_human_approval(self):
        report = k.tool_authority_assessment({"write": True, "external_side_effect": True, "destructive": True, "irreversible": True})
        self.assertEqual(report["authority_class"], "T4")
        self.assertTrue(report["explicit_human_approval_required"])

    def test_gate_defers_when_freshness_not_clear(self):
        result = k.gate_verdict("GO", 0.99, 0.8, True, freshness_status="REFRESH_REQUIRED")
        self.assertEqual(result, "DEFER")

    def test_gate_defers_when_human_approval_missing(self):
        result = k.gate_verdict("GO", 0.99, 0.8, True, human_approval_required=True, human_approved=False)
        self.assertEqual(result, "DEFER")

    def test_temporal_eval_suite(self):
        cases = json.loads((ROOT / "tests" / "temporal-evals.json").read_text(encoding="utf-8"))
        for case in cases:
            with self.subTest(case=case["name"]):
                report = k.evaluate_temporal_truth(case["row"], case["as_of"])
                self.assertEqual(report["status"], case["expected_status"])
                self.assertEqual(report["admissible"], case["admissible"])

    def test_material_general_current_claim_without_verification_is_unknown(self):
        report = k.evaluate_temporal_truth({"claim_id": "g", "claim_type": "general_web", "material": True}, "2026-08-24T17:00:00+00:00")
        self.assertEqual(report["status"], "UNKNOWN")
        self.assertFalse(report["admissible"])


if __name__ == "__main__":
    unittest.main()
