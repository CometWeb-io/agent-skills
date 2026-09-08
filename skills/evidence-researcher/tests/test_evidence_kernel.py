#!/usr/bin/env python3
import copy
import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "evidence_kernel.py"
SPEC = importlib.util.spec_from_file_location("evidence_kernel", SCRIPT)
EK = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(EK)


class EvidenceKernelV2Tests(unittest.TestCase):
    def base_ledger(self):
        claim_id = "clm_policy"
        source_id = "src_policy"
        return {
            "schema_version": "2.0",
            "research_id": "res_policy",
            "research_contract": {
                "question": "Does the vendor policy currently state X?",
                "objective": "Verify current policy wording",
                "scope": {"product": "Example"},
                "as_of": "2026-08-25T21:44:00+02:00",
                "mode": "STANDARD",
                "consumers": ["ai-council"],
                "constraints": [],
                "known_facts": [],
                "known_unknowns": [],
                "privacy_lane": "PUBLIC",
            },
            "claims": [
                {
                    "claim_id": claim_id,
                    "claim_text": "The vendor policy currently states X.",
                    "claim_type": "vendor_policy",
                    "materiality": "critical",
                    "epistemic_kind": "FACT",
                    "temporal_sensitivity": "high",
                    "scope": {},
                    "depends_on_claim_ids": [],
                    "contradiction_tested": True,
                    "status": "VERIFIED",
                    "confidence": "high",
                }
            ],
            "sources": [
                {
                    "source_id": source_id,
                    "title": "Official policy",
                    "canonical_ref": "https://example.com/policy",
                    "source_class": "LIVE_WEB",
                    "source_role": "OFFICIAL",
                    "provenance_lane": "PUBLIC",
                    "independence_group": "example-vendor",
                    "independence_confidence": "high",
                    "source_state": "final",
                    "published_at": None,
                    "effective_from": None,
                    "effective_to": None,
                    "last_verified_at": "2026-08-25T21:30:00+02:00",
                    "expires_at": None,
                    "source_version": None,
                    "superseded_by_source_id": None,
                    "requires_live_verification": False,
                    "verified_for_research": True,
                    "freshness_ttl_days": None,
                    "derived_from_source_ids": [],
                    "content_hash": None,
                }
            ],
            "evidence": [
                {
                    "evidence_id": "ev_policy_support",
                    "claim_id": claim_id,
                    "source_id": source_id,
                    "direction": "SUPPORT",
                    "locator": "Policy section 2",
                    "evidence_form": "paraphrase",
                    "summary": "Policy states X.",
                    "authority_fit": "high",
                    "directness": "high",
                    "scope_fit": "high",
                    "measurement_quality": "not_applicable",
                    "admission": "ACCEPTED",
                }
            ],
            "contradictions": [],
            "searches": [
                {
                    "search_id": "srch_policy_falsifier",
                    "claim_id": claim_id,
                    "purpose": "FALSIFIER",
                    "source_lane": "PUBLIC",
                    "query_summary": "Checked current policy, supersession and contrary vendor notices",
                    "completed": True,
                    "completed_at": "2026-08-25T21:35:00+02:00",
                    "result_source_ids": [source_id],
                    "novelty_count": 0,
                }
            ],
            "gaps": [],
            "research_status": "PARTIAL",
            "stop_reason": None,
        }

    def test_canonical_url_strips_tracking_and_fragment(self):
        url = "https://Example.com/page?utm_source=x&b=2&a=1#section"
        self.assertEqual(EK.canonical_url(url), "https://example.com/page?a=1&b=2")

    def test_make_id_is_stable_and_supports_v2_kinds(self):
        a = EK.make_id("source", " Example source ")
        b = EK.make_id("source", "example   source")
        self.assertEqual(a, b)
        self.assertTrue(a.startswith("src_"))
        self.assertTrue(EK.make_id("search", "x").startswith("srch_"))

    def test_source_policy_marks_live_classes(self):
        self.assertTrue(EK.source_policy("vendor_policy")["requires_live_verification"])
        self.assertFalse(EK.source_policy("historical_fact")["requires_live_verification"])

    def test_live_type_requires_run_specific_verification(self):
        source = self.base_ledger()["sources"][0]
        source["verified_for_research"] = False
        result = EK.temporal_status(source, "2026-08-25T21:44:00+02:00", "vendor_policy")
        self.assertEqual(result["temporal_status"], "UNKNOWN")

    def test_live_type_current_when_verified_for_run(self):
        source = self.base_ledger()["sources"][0]
        result = EK.temporal_status(source, "2026-08-25T21:44:00+02:00", "vendor_policy")
        self.assertEqual(result["temporal_status"], "CURRENT")

    def test_future_effective_source_is_not_yet_effective(self):
        source = self.base_ledger()["sources"][0]
        source["effective_from"] = "2026-09-01T00:00:00+02:00"
        result = EK.temporal_status(source, "2026-08-25T21:44:00+02:00", "vendor_policy")
        self.assertEqual(result["temporal_status"], "NOT_YET_EFFECTIVE")

    def test_superseded_source_is_superseded(self):
        source = self.base_ledger()["sources"][0]
        source["superseded_by_source_id"] = "src_new"
        result = EK.temporal_status(source, "2026-08-25T21:44:00+02:00", "vendor_policy")
        self.assertEqual(result["temporal_status"], "SUPERSEDED")

    def test_ready_v2_ledger(self):
        result = EK.audit(self.base_ledger())
        self.assertEqual(result["research_status"], "READY")
        self.assertTrue(result["validation"]["valid"])
        self.assertEqual(result["coverage"]["material_ready_rate"], 1.0)

    def test_missing_schema_version_is_invalid(self):
        ledger = self.base_ledger()
        ledger.pop("schema_version")
        result = EK.validate_ledger(ledger)
        self.assertFalse(result["valid"])
        self.assertTrue(any("schema_version" in e for e in result["errors"]))

    def test_inference_cannot_be_verified(self):
        ledger = self.base_ledger()
        ledger["claims"][0]["epistemic_kind"] = "INFERENCE"
        ledger["claims"][0]["status"] = "VERIFIED"
        ledger["claims"][0]["depends_on_claim_ids"] = []
        result = EK.validate_ledger(ledger)
        self.assertFalse(result["valid"])
        self.assertTrue(any("cannot be marked VERIFIED" in e for e in result["errors"]))

    def test_supported_inference_requires_dependencies(self):
        ledger = self.base_ledger()
        ledger["claims"][0]["epistemic_kind"] = "INFERENCE"
        ledger["claims"][0]["status"] = "SUPPORTED_INFERENCE"
        ledger["claims"][0]["depends_on_claim_ids"] = []
        result = EK.validate_ledger(ledger)
        self.assertFalse(result["valid"])
        self.assertTrue(any("without dependencies" in e for e in result["errors"]))

    def test_dependency_cycle_is_invalid(self):
        ledger = self.base_ledger()
        ledger["claims"] = [
            {
                "claim_id": "clm_a", "claim_text": "A", "claim_type": "historical_fact",
                "materiality": "supporting", "epistemic_kind": "INFERENCE", "temporal_sensitivity": "static",
                "scope": {}, "depends_on_claim_ids": ["clm_b"], "contradiction_tested": False,
                "status": "PARTIAL", "confidence": "low",
            },
            {
                "claim_id": "clm_b", "claim_text": "B", "claim_type": "historical_fact",
                "materiality": "supporting", "epistemic_kind": "INFERENCE", "temporal_sensitivity": "static",
                "scope": {}, "depends_on_claim_ids": ["clm_a"], "contradiction_tested": False,
                "status": "PARTIAL", "confidence": "low",
            },
        ]
        ledger["evidence"] = []
        ledger["searches"] = []
        result = EK.validate_ledger(ledger)
        self.assertFalse(result["valid"])
        self.assertTrue(any("dependency cycle" in e for e in result["errors"]))

    def test_contradiction_flag_requires_falsifier_record(self):
        ledger = self.base_ledger()
        ledger["searches"] = []
        result = EK.validate_ledger(ledger)
        self.assertFalse(result["valid"])
        self.assertTrue(any("without a completed falsifier search" in e for e in result["errors"]))

    def test_context_edge_cannot_be_accepted(self):
        ledger = self.base_ledger()
        ledger["evidence"][0]["direction"] = "CONTEXT"
        ledger["evidence"][0]["admission"] = "ACCEPTED"
        result = EK.validate_ledger(ledger)
        self.assertFalse(result["valid"])

    def test_accepted_edge_without_locator_warns(self):
        ledger = self.base_ledger()
        ledger["evidence"][0]["locator"] = None
        result = EK.validate_ledger(ledger)
        self.assertTrue(result["valid"])
        self.assertTrue(any("pinpoint locator" in w for w in result["warnings"]))

    def test_duplicate_source_fingerprint_warns(self):
        ledger = self.base_ledger()
        dup = copy.deepcopy(ledger["sources"][0])
        dup["source_id"] = "src_policy_dup"
        ledger["sources"].append(dup)
        result = EK.validate_ledger(ledger)
        self.assertTrue(result["valid"])
        self.assertTrue(any("duplicate source fingerprint" in w for w in result["warnings"]))

    def test_same_canonical_ref_multiple_independence_groups_warns(self):
        ledger = self.base_ledger()
        dup = copy.deepcopy(ledger["sources"][0])
        dup["source_id"] = "src_policy_dup"
        dup["independence_group"] = "different-origin"
        ledger["sources"].append(dup)
        result = EK.validate_ledger(ledger)
        self.assertTrue(result["valid"])
        self.assertTrue(any("multiple independence groups" in w for w in result["warnings"]))

    def test_current_authoritative_support_can_keep_claim_fresh_despite_old_accepted_support(self):
        ledger = self.base_ledger()
        old_source = copy.deepcopy(ledger["sources"][0])
        old_source.update({
            "source_id": "src_old", "canonical_ref": "https://example.com/old-policy",
            "last_verified_at": "2026-01-01T10:00:00+02:00", "verified_for_research": False,
            "source_role": "SECONDARY", "independence_group": "old-summary",
        })
        ledger["sources"].append(old_source)
        old_edge = copy.deepcopy(ledger["evidence"][0])
        old_edge.update({
            "evidence_id": "ev_old", "source_id": "src_old", "authority_fit": "medium", "directness": "medium",
        })
        ledger["evidence"].append(old_edge)
        result = EK.audit(ledger)
        self.assertEqual(result["research_status"], "READY")
        row = result["coverage"]["claims"][0]
        self.assertTrue(row["freshness_admissible"])
        self.assertEqual(row["stale_or_unknown_accepted_support_count"], 1)

    def test_no_fresh_support_requires_refresh(self):
        ledger = self.base_ledger()
        ledger["sources"][0]["verified_for_research"] = False
        result = EK.audit(ledger)
        self.assertEqual(result["research_status"], "REFRESH_REQUIRED")

    def test_unresolved_critical_contradiction_blocks_ready(self):
        ledger = self.base_ledger()
        ledger["evidence"].append({
            "evidence_id": "ev_conflict", "claim_id": "clm_policy", "source_id": "src_policy",
            "direction": "CONTRADICT", "locator": "Policy section 3", "evidence_form": "paraphrase",
            "summary": "Conflicting wording", "authority_fit": "high", "directness": "high",
            "scope_fit": "high", "measurement_quality": "not_applicable", "admission": "ACCEPTED",
        })
        ledger["contradictions"] = [{
            "contradiction_id": "ctr_policy", "claim_id": "clm_policy",
            "evidence_ids": ["ev_policy_support", "ev_conflict"], "type": "genuine_conflict",
            "severity": "critical", "resolution": "UNRESOLVED", "explanation": "Conflict",
            "resolution_basis_evidence_ids": [],
        }]
        result = EK.audit(ledger)
        self.assertEqual(result["research_status"], "BLOCKED_BY_CONTRADICTION")

    def test_critical_gap_prevents_ready(self):
        ledger = self.base_ledger()
        ledger["gaps"] = [{
            "gap_id": "gap_primary", "claim_id": "clm_policy", "severity": "critical",
            "gap_type": "access", "description": "Controlling appendix unavailable",
            "what_closes_it": "Retrieve the appendix",
        }]
        result = EK.audit(ledger)
        self.assertEqual(result["research_status"], "PARTIAL")

    def test_refresh_plan_marks_live_source_for_next_material_run(self):
        plan = EK.refresh_plan(self.base_ledger())
        self.assertFalse(plan["refresh_required"])
        self.assertEqual(plan["items"][0]["action"], "REVERIFY_ON_NEXT_MATERIAL_RUN")

    def test_pack_hash_is_stable_and_ignores_status_fields(self):
        ledger = self.base_ledger()
        a = EK.pack_hash(ledger)
        ledger["research_status"] = "READY"
        ledger["stop_reason"] = "done"
        ledger["pack_hash"] = "ignored"
        b = EK.pack_hash(ledger)
        self.assertEqual(a, b)

    def test_delta_detects_claim_and_source_changes(self):
        old = self.base_ledger()
        new = copy.deepcopy(old)
        new["claims"][0]["confidence"] = "medium"
        new_source = copy.deepcopy(new["sources"][0])
        new_source.update({"source_id": "src_new", "canonical_ref": "https://example.com/new-policy"})
        new["sources"].append(new_source)
        result = EK.delta(old, new)
        self.assertEqual(result["changed_claims"][0]["claim_id"], "clm_policy")
        self.assertIn("src_new", result["added_source_ids"])

    def test_stop_requires_ready_gate(self):
        ledger = self.base_ledger()
        ledger["sources"][0]["verified_for_research"] = False
        result = EK.stop_decision(ledger, 3, 0.0, 1.0)
        self.assertFalse(result["stop"])
        self.assertEqual(result["research_status"], "REFRESH_REQUIRED")

    def test_stop_on_ready_and_saturation(self):
        result = EK.stop_decision(self.base_ledger(), 2, 0.5, 0.1)
        self.assertTrue(result["stop"])
        self.assertTrue(result["saturation"])

    def test_v1_migration_normalizes_sources_and_edges(self):
        v1 = {
            "research_question": "Is X current?",
            "as_of": "2026-08-25T21:44:00+02:00",
            "mode": "STANDARD",
            "claims": [{
                "claim_id": "clm_x", "claim_text": "X is current", "claim_type": "vendor_policy",
                "materiality": "critical", "temporal_sensitivity": "high", "support_evidence_ids": ["ev_x"],
                "contradiction_evidence_ids": [], "contradiction_tested": True, "status": "VERIFIED", "confidence": "high",
            }],
            "evidence": [{
                "evidence_id": "ev_x", "title": "Official", "canonical_url": "https://example.com/x",
                "source_class": "LIVE_WEB", "source_role": "OFFICIAL", "claim_type": "vendor_policy",
                "authority_fit": "high", "directness": "high", "scope_fit": "high",
                "measurement_quality": "not_applicable", "independence_group": "example",
                "last_verified_at": "2026-08-25T21:30:00+02:00", "verified_for_research": True,
                "admission": "ACCEPTED", "supports_claim_ids": ["clm_x"], "contradicts_claim_ids": [],
            }],
            "contradictions": [], "gaps": [],
        }
        migrated = EK.migrate_v1(v1)
        self.assertEqual(migrated["schema_version"], "2.0")
        self.assertEqual(len(migrated["sources"]), 1)
        self.assertEqual(len(migrated["evidence"]), 1)
        self.assertEqual(migrated["evidence"][0]["claim_id"], "clm_x")
        self.assertTrue(migrated["migration"]["warning"])

    def test_v1_migration_output_valid_for_normal_case(self):
        v1 = {
            "research_question": "Historical fact?", "as_of": "2026-08-25T21:44:00+02:00", "mode": "QUICK",
            "claims": [{
                "claim_id": "clm_h", "claim_text": "Historical fact", "claim_type": "historical_fact",
                "materiality": "material", "temporal_sensitivity": "static", "support_evidence_ids": ["ev_h"],
                "contradiction_evidence_ids": [], "contradiction_tested": True, "status": "VERIFIED", "confidence": "high",
            }],
            "evidence": [{
                "evidence_id": "ev_h", "title": "Archive", "canonical_url": "https://example.com/archive",
                "source_class": "LIVE_WEB", "source_role": "PRIMARY", "authority_fit": "high", "directness": "high",
                "scope_fit": "high", "measurement_quality": "not_applicable", "independence_group": "archive",
                "last_verified_at": "2026-08-25T20:00:00+02:00", "verified_for_research": True,
                "admission": "ACCEPTED", "supports_claim_ids": ["clm_h"], "contradicts_claim_ids": [],
            }],
            "contradictions": [], "gaps": [],
        }
        migrated = EK.migrate_v1(v1)
        result = EK.validate_ledger(migrated)
        self.assertTrue(result["valid"], result["errors"])

    def test_source_lineage_cycle_is_invalid(self):
        ledger = self.base_ledger()
        second = copy.deepcopy(ledger["sources"][0])
        second.update({"source_id": "src_second", "canonical_ref": "https://example.com/second", "derived_from_source_ids": ["src_policy"]})
        ledger["sources"][0]["derived_from_source_ids"] = ["src_second"]
        ledger["sources"].append(second)
        result = EK.validate_ledger(ledger)
        self.assertFalse(result["valid"])
        self.assertTrue(any("source lineage cycle" in e for e in result["errors"]))

    def test_accepted_contradiction_requires_contradiction_record(self):
        ledger = self.base_ledger()
        ledger["evidence"].append({
            "evidence_id": "ev_hidden_opp", "claim_id": "clm_policy", "source_id": "src_policy",
            "direction": "CONTRADICT", "locator": "section 3", "evidence_form": "paraphrase",
            "summary": "Opposing text", "authority_fit": "high", "directness": "high",
            "scope_fit": "high", "measurement_quality": "not_applicable", "admission": "ACCEPTED",
        })
        result = EK.validate_ledger(ledger)
        self.assertFalse(result["valid"])
        self.assertTrue(any("without a contradiction record" in e for e in result["errors"]))

    def test_material_unresolved_contradiction_yields_partial(self):
        ledger = self.base_ledger()
        ledger["claims"][0]["materiality"] = "material"
        ledger["evidence"].append({
            "evidence_id": "ev_conflict_material", "claim_id": "clm_policy", "source_id": "src_policy",
            "direction": "CONTRADICT", "locator": "section 3", "evidence_form": "paraphrase",
            "summary": "Opposing text", "authority_fit": "high", "directness": "high",
            "scope_fit": "high", "measurement_quality": "not_applicable", "admission": "ACCEPTED",
        })
        ledger["contradictions"] = [{
            "contradiction_id": "ctr_material", "claim_id": "clm_policy",
            "evidence_ids": ["ev_policy_support", "ev_conflict_material"], "type": "genuine_conflict",
            "severity": "material", "resolution": "UNRESOLVED", "explanation": "Conflict",
            "resolution_basis_evidence_ids": [],
        }]
        result = EK.audit(ledger)
        self.assertEqual(result["research_status"], "PARTIAL")

    def test_absence_test_requires_explicit_design(self):
        ledger = self.base_ledger()
        ledger["searches"][0]["purpose"] = "ABSENCE_TEST"
        result = EK.validate_ledger(ledger)
        self.assertFalse(result["valid"])
        self.assertTrue(any("ABSENCE_TEST requires" in e for e in result["errors"]))
        ledger["searches"][0]["absence_basis"] = {
            "expected_location": "official registry",
            "detection_logic": "record would be indexed under exact identifier",
            "coverage_limitations": "registry may lag by one day",
        }
        result = EK.validate_ledger(ledger)
        self.assertTrue(result["valid"], result["errors"])

    def test_private_lane_public_search_requires_sanitization_marker(self):
        ledger = self.base_ledger()
        ledger["research_contract"]["privacy_lane"] = "PRIVATE"
        result = EK.validate_ledger(ledger)
        self.assertFalse(result["valid"])
        self.assertTrue(any("sanitized_for_external" in e for e in result["errors"]))
        ledger["searches"][0]["sanitized_for_external"] = True
        result = EK.validate_ledger(ledger)
        self.assertTrue(result["valid"], result["errors"])

    def test_falsifier_record_without_claim_flag_does_not_ready(self):
        ledger = self.base_ledger()
        ledger["claims"][0]["contradiction_tested"] = False
        result = EK.audit(ledger)
        self.assertEqual(result["research_status"], "PARTIAL")

    def test_v1_migration_handles_object_scope_fit(self):
        v1 = {
            "research_question": "Scope fit migration", "as_of": "2026-08-25T21:44:00+02:00", "mode": "STANDARD",
            "claims": [{
                "claim_id": "clm_scope", "claim_text": "Scoped fact", "claim_type": "historical_fact",
                "materiality": "material", "temporal_sensitivity": "static", "contradiction_tested": True,
                "status": "VERIFIED", "confidence": "high"
            }],
            "evidence": [{
                "evidence_id": "ev_scope", "title": "Archive", "canonical_url": "https://example.com/scope",
                "source_class": "LIVE_WEB", "source_role": "PRIMARY", "authority_fit": "high", "directness": "high",
                "scope_fit": {"jurisdiction": "high", "population": "medium"}, "measurement_quality": "not_applicable",
                "admission": "ACCEPTED", "supports_claim_ids": ["clm_scope"], "contradicts_claim_ids": []
            }],
            "contradictions": [], "gaps": []
        }
        migrated = EK.migrate_v1(v1)
        self.assertEqual(migrated["evidence"][0]["scope_fit"], "medium")



if __name__ == "__main__":
    unittest.main()
