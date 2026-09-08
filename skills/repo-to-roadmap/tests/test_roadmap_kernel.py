import copy
import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("roadmap_kernel", ROOT / "scripts" / "roadmap_kernel.py")
k = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(k)


def code_evidence(ref="code", direction="support", independence="code"):
    return {
        "source_ref": ref,
        "source_type": "code",
        "direction": direction,
        "directness": "direct",
        "freshness": "NOT_TIME_SENSITIVE",
        "scope_match": "exact",
        "independence_key": independence,
    }


def test_evidence(ref="test", independence="test"):
    return {
        "source_ref": ref,
        "source_type": "test",
        "direction": "support",
        "directness": "direct",
        "freshness": "NOT_TIME_SENSITIVE",
        "scope_match": "exact",
        "independence_key": independence,
    }


def behavior_claim(claim_id="C-1"):
    return {
        "claim_id": claim_id,
        "text": "Critical flow behaves as required",
        "claim_lane": "implementation",
        "claim_type": "behavior",
        "materiality": "high",
        "current_sensitive": False,
        "evidence": [code_evidence(), test_evidence()],
    }


def valid_item(item_id="R-1"):
    return {
        "id": item_id,
        "title": "Harden critical flow",
        "kind": "HARDEN",
        "outcome": "Critical flow satisfies the target requirement with direct verification",
        "problem_claim_refs": ["C-1"],
        "target_requirement_refs": ["T-1"],
        "capability_refs": ["CAP-1"],
        "why_now": "Required for the declared target state",
        "acceptance_criteria": [
            {
                "criterion": "Critical flow passes the required behavior",
                "verify_with": "integration test",
                "proof": "passing CI artifact at pinned ref",
            }
        ],
        "success_signal": "Critical flow verification stays green",
        "depends_on": [],
        "effort": "M",
        "impact": 4,
        "urgency": 3,
        "risk_reduction": 4,
        "strategic_alignment": 5,
        "enablement": 3,
        "reach": 4,
        "uncertainty": 1,
        "evidence_confidence": 0.88,
        "lane": "NEXT",
        "severity": "high",
        "non_goal": "Redesign unrelated surfaces",
    }


def valid_payload():
    return {
        "schema_version": "2.0",
        "assessment": {
            "mode": "STANDARD",
            "as_of": "2026-08-25T22:00:00+02:00",
            "repos": [{"name": "example/repo", "ref": "abc123"}],
        },
        "target_contract": {
            "target_profile": "CLIENT_READY",
            "requirements": [
                {
                    "id": "T-1",
                    "domain": "core_flow",
                    "requirement": "Critical client flow is directly verified",
                    "mandatory": True,
                    "applicability": "APPLIES",
                    "source": "user_goal",
                }
            ],
        },
        "coverage": [
            {"name": "product_flows", "status": "COMPLETE", "mandatory": True, "weight": 3},
            {"name": "ci_release", "status": "COMPLETE", "mandatory": True, "weight": 2},
        ],
        "claims": [behavior_claim()],
        "capabilities": [
            {
                "capability_id": "CAP-1",
                "name": "Critical flow",
                "state": "PARTIAL",
                "criticality": "high",
                "claim_refs": ["C-1"],
                "target_requirement_refs": ["T-1"],
                "confidence": 0.88,
            }
        ],
        "items": [valid_item()],
        "watch_dependencies": [],
    }


class EvidenceTests(unittest.TestCase):
    def test_code_plus_test_can_verify_behavior(self):
        report = k.evidence_report(behavior_claim())
        self.assertEqual(report["status"], "SUPPORTED")
        self.assertTrue(report["verification_requirements_met"])
        self.assertEqual(report["confidence_band"], "VERIFIED")

    def test_code_presence_alone_cannot_verify_behavior(self):
        claim = behavior_claim()
        claim["evidence"] = [code_evidence()]
        report = k.evidence_report(claim)
        self.assertEqual(report["status"], "INSUFFICIENT_VERIFICATION")
        self.assertFalse(report["verification_requirements_met"])
        self.assertLessEqual(report["heuristic_confidence"], 0.68)

    def test_merged_pr_cannot_verify_release(self):
        claim = {
            "claim_id": "C-release",
            "text": "Feature is released",
            "claim_lane": "implementation",
            "claim_type": "release",
            "materiality": "high",
            "evidence": [{
                "source_ref": "pr:1",
                "source_type": "pr",
                "direction": "support",
                "directness": "direct",
                "freshness": "NOT_TIME_SENSITIVE",
                "scope_match": "exact",
                "independence_key": "pr:1",
            }],
        }
        report = k.evidence_report(claim)
        self.assertEqual(report["status"], "INSUFFICIENT_VERIFICATION")
        self.assertFalse(report["verification_requirements_met"])

    def test_stale_evidence_is_inadmissible_for_current_sensitive_claim(self):
        claim = {
            "claim_id": "C-current",
            "text": "Vendor currently supports the endpoint",
            "claim_lane": "external",
            "claim_type": "external_current",
            "materiality": "high",
            "current_sensitive": True,
            "evidence": [{
                "source_ref": "vendor",
                "source_type": "vendor_official",
                "direction": "support",
                "directness": "direct",
                "freshness": "STALE",
                "scope_match": "exact",
                "independence_key": "vendor-doc",
            }],
        }
        report = k.evidence_report(claim)
        self.assertEqual(report["status"], "STALE_EVIDENCE")
        self.assertEqual(report["admissible_evidence_count"], 0)

    def test_current_primary_evidence_can_verify_external_current(self):
        claim = {
            "claim_id": "C-current",
            "text": "Vendor currently supports the endpoint",
            "claim_lane": "external",
            "claim_type": "external_current",
            "materiality": "high",
            "current_sensitive": True,
            "evidence": [{
                "source_ref": "vendor",
                "source_type": "vendor_official",
                "direction": "support",
                "directness": "direct",
                "freshness": "CURRENT",
                "scope_match": "exact",
                "independence_key": "vendor-doc",
            }],
        }
        report = k.evidence_report(claim)
        self.assertTrue(report["verification_requirements_met"])
        self.assertEqual(report["status"], "SUPPORTED")

    def test_unknown_independence_is_grouped_conservatively(self):
        claim = {
            "claim_id": "C-2",
            "text": "Handler exists",
            "claim_lane": "implementation",
            "claim_type": "presence",
            "materiality": "medium",
            "evidence": [
                {**code_evidence("a"), "independence_key": ""},
                {**code_evidence("b"), "independence_key": ""},
            ],
        }
        report = k.evidence_report(claim)
        self.assertEqual(report["independent_support_groups"], 1)
        self.assertTrue(any("missing independence_key" in warning for warning in report["warnings"]))

    def test_strong_contradiction_surfaces_contested(self):
        claim = behavior_claim()
        claim["evidence"].append({
            "source_ref": "runtime-failure",
            "source_type": "runtime",
            "direction": "contradict",
            "directness": "direct",
            "freshness": "NOT_TIME_SENSITIVE",
            "scope_match": "exact",
            "independence_key": "runtime",
        })
        report = k.evidence_report(claim)
        self.assertEqual(report["status"], "CONTESTED")
        self.assertLessEqual(report["heuristic_confidence"], 0.49)

    def test_absence_requires_complete_negative_evidence_protocol(self):
        claim = {
            "claim_id": "C-abs",
            "text": "Export route is absent",
            "claim_lane": "implementation",
            "claim_type": "absence",
            "materiality": "high",
            "evidence": [{
                "source_ref": "inventory",
                "source_type": "inventory",
                "direction": "support",
                "directness": "direct",
                "freshness": "NOT_TIME_SENSITIVE",
                "scope_match": "exact",
                "independence_key": "tree",
            }],
            "absence_check": {"status": "NOT_FOUND_IN_SEARCH", "inventory_complete": False},
        }
        report = k.evidence_report(claim)
        self.assertEqual(report["status"], "INSUFFICIENT_VERIFICATION")
        self.assertFalse(report["verification_requirements_met"])

    def test_complete_negative_evidence_protocol_can_verify_absence(self):
        claim = {
            "claim_id": "C-abs",
            "text": "Export route is absent",
            "claim_lane": "implementation",
            "claim_type": "absence",
            "materiality": "high",
            "evidence": [{
                "source_ref": "inventory",
                "source_type": "inventory",
                "direction": "support",
                "directness": "direct",
                "freshness": "NOT_TIME_SENSITIVE",
                "scope_match": "exact",
                "independence_key": "tree",
            }],
            "absence_check": {
                "status": "ABSENCE_VERIFIED",
                "inventory_complete": True,
                "scopes_checked": ["apps/web"],
                "dynamic_registration_checked": True,
                "generated_or_config_driven_paths_checked": "NOT_APPLICABLE",
            },
        }
        report = k.evidence_report(claim)
        self.assertTrue(report["verification_requirements_met"])
        self.assertEqual(report["status"], "SUPPORTED")


class PriorityTests(unittest.TestCase):
    def base_item(self):
        item = valid_item()
        item.pop("lane", None)
        return item

    def test_explicit_gate_block_becomes_blocker(self):
        item = self.base_item()
        item.update({"mandatory_gate": "security", "gate_status": "BLOCK", "evidence_confidence": 0.55})
        report = k.priority_report(item)
        self.assertEqual(report["lane"], "BLOCKER")

    def test_unverified_gate_becomes_verify_now_not_blocker(self):
        item = self.base_item()
        item.update({"mandatory_gate": "privacy", "gate_status": "UNVERIFIED", "evidence_confidence": 0.9})
        report = k.priority_report(item)
        self.assertEqual(report["lane"], "VERIFY_NOW")

    def test_weak_suspected_target_blocker_becomes_verify_now(self):
        item = self.base_item()
        item.update({"target_blocker": True, "evidence_confidence": 0.4})
        report = k.priority_report(item)
        self.assertEqual(report["lane"], "VERIFY_NOW")

    def test_strong_target_blocker_becomes_blocker(self):
        item = self.base_item()
        item.update({"target_blocker": True, "evidence_confidence": 0.85})
        report = k.priority_report(item)
        self.assertEqual(report["lane"], "BLOCKER")

    def test_gate_block_priority_is_sensitivity_stable(self):
        item = self.base_item()
        item.update({"mandatory_gate": "release", "gate_status": "BLOCK", "evidence_confidence": 0.8})
        report = k.sensitivity_report(item)
        self.assertEqual(report["stability"], "STABLE")
        self.assertEqual(report["lanes_seen"], ["BLOCKER"])


class GraphCoverageSnapshotTests(unittest.TestCase):
    def test_graph_detects_cycle(self):
        report = k.graph_report([
            {"id": "A", "depends_on": ["B"]},
            {"id": "B", "depends_on": ["A"]},
        ])
        self.assertFalse(report["valid"])
        self.assertEqual(report["cycle_nodes"], ["A", "B"])

    def test_graph_detects_missing_dependency(self):
        report = k.graph_report([{"id": "A", "depends_on": ["MISSING"]}])
        self.assertFalse(report["valid"])
        self.assertIn("A", report["missing_dependencies"])

    def test_graph_reports_transitive_leverage_and_chain(self):
        report = k.graph_report([
            {"id": "A", "depends_on": []},
            {"id": "B", "depends_on": ["A"]},
            {"id": "C", "depends_on": ["B"]},
            {"id": "D", "depends_on": ["A"]},
        ])
        self.assertTrue(report["valid"])
        leverage_a = next(row for row in report["dependency_leverage"] if row["id"] == "A")
        self.assertEqual(leverage_a["transitive_unblocks"], 3)
        self.assertEqual(report["critical_chain_by_hard_dependency_count"], ["A", "B", "C"])

    def test_not_applicable_requires_reason(self):
        report = k.coverage_report([{"name": "billing", "status": "NOT_APPLICABLE"}])
        self.assertEqual(report["scope_claim"], "COVERAGE_INVALID")
        self.assertTrue(report["errors"])

    def test_incomplete_mandatory_coverage_qualifies_scope(self):
        report = k.coverage_report([
            {"name": "source", "status": "COMPLETE", "mandatory": True, "weight": 3},
            {"name": "ci", "status": "PARTIAL", "mandatory": True, "weight": 1},
        ])
        self.assertEqual(report["scope_claim"], "WHOLE_PROJECT_SCOPE_QUALIFIED")
        self.assertIn("ci", report["incomplete_mandatory_domains"])

    def test_snapshot_hash_is_deterministic(self):
        payload = valid_payload()
        a = k.snapshot_report(payload)
        b = k.snapshot_report(copy.deepcopy(payload))
        self.assertEqual(a["snapshot_hash"], b["snapshot_hash"])

    def test_delta_changed_claim_invalidates_linked_item_and_dependents(self):
        before = valid_payload()
        second = valid_item("R-2")
        second["problem_claim_refs"] = ["C-1"]
        second["capability_refs"] = ["CAP-1"]
        second["depends_on"] = ["R-1"]
        before["items"].append(second)
        after = copy.deepcopy(before)
        after["claims"][0]["text"] = "Critical flow behavior changed"
        report = k.delta_report(before, after)
        self.assertIn("C-1", report["changed_claim_ids"])
        self.assertEqual(set(report["revalidate_item_ids"]), {"R-1", "R-2"})
        self.assertEqual(report["roadmap_validity"], "REVALIDATE")


    def test_delta_claim_change_marks_unchanged_linked_capability_affected(self):
        before = valid_payload()
        after = copy.deepcopy(before)
        after["claims"][0]["text"] = "Critical flow behavior changed"
        report = k.delta_report(before, after)
        self.assertIn("CAP-1", report["affected_capability_ids"])
        self.assertIn("R-1", report["revalidate_item_ids"])

    def test_delta_target_change_revalidates_all_items(self):
        before = valid_payload()
        second = valid_item("R-2")
        second["depends_on"] = []
        before["items"].append(second)
        after = copy.deepcopy(before)
        after["target_contract"]["target_profile"] = "PAID_PRODUCTION"
        report = k.delta_report(before, after)
        self.assertTrue(report["target_contract_changed"])
        self.assertEqual(set(report["revalidate_item_ids"]), {"R-1", "R-2"})


class ValidationTests(unittest.TestCase):
    def test_valid_payload_passes(self):
        report = k.validate_roadmap(valid_payload())
        self.assertTrue(report["valid"], report["errors"])

    def test_unknown_item_claim_ref_fails(self):
        payload = valid_payload()
        payload["items"][0]["problem_claim_refs"] = ["C-404"]
        report = k.validate_roadmap(payload)
        self.assertFalse(report["valid"])
        self.assertTrue(any("unknown claim refs" in error for error in report["errors"]))

    def test_acceptance_criteria_require_verification_and_proof(self):
        payload = valid_payload()
        payload["items"][0]["acceptance_criteria"] = ["works"]
        report = k.validate_roadmap(payload)
        self.assertFalse(report["valid"])
        self.assertTrue(any("acceptance_criteria[0]" in error for error in report["errors"]))

    def test_missing_capability_requires_verified_absence_claim(self):
        payload = valid_payload()
        payload["capabilities"][0]["state"] = "MISSING"
        report = k.validate_roadmap(payload)
        self.assertFalse(report["valid"])
        self.assertTrue(any("MISSING requires" in error for error in report["errors"]))

    def test_xl_item_requires_decomposition_note(self):
        payload = valid_payload()
        payload["items"][0]["effort"] = "XL"
        report = k.validate_roadmap(payload)
        self.assertFalse(report["valid"])
        self.assertTrue(any("XL item requires decomposition_note" in error for error in report["errors"]))

    def test_unverified_gate_cannot_be_now(self):
        payload = valid_payload()
        item = payload["items"][0]
        item.update({"mandatory_gate": "privacy", "gate_status": "UNVERIFIED", "lane": "NOW"})
        report = k.validate_roadmap(payload)
        self.assertFalse(report["valid"])
        self.assertTrue(any("unverified mandatory gate" in error for error in report["errors"]))


    def test_resolved_gate_requires_gate_basis(self):
        payload = valid_payload()
        item = payload["items"][0]
        item.update({"mandatory_gate": "security", "gate_status": "BLOCK", "lane": "BLOCKER"})
        report = k.validate_roadmap(payload)
        self.assertFalse(report["valid"])
        self.assertTrue(any("resolved mandatory gate requires gate_basis" in error for error in report["errors"]))

    def test_resolved_gate_with_basis_can_be_blocker(self):
        payload = valid_payload()
        item = payload["items"][0]
        item.update({
            "mandatory_gate": "security",
            "gate_status": "BLOCK",
            "gate_basis": "security-finding:SEC-1",
            "lane": "BLOCKER",
        })
        report = k.validate_roadmap(payload)
        self.assertTrue(report["valid"], report["errors"])

    def test_gate_blocker_requires_block_status(self):
        payload = valid_payload()
        item = payload["items"][0]
        item.update({"mandatory_gate": "security", "gate_status": "CLEAR", "lane": "BLOCKER"})
        report = k.validate_roadmap(payload)
        self.assertFalse(report["valid"])
        self.assertTrue(any("requires gate_status BLOCK" in error for error in report["errors"]))

    def test_non_gate_blocker_requires_strong_target_blocker(self):
        payload = valid_payload()
        item = payload["items"][0]
        item.update({"lane": "BLOCKER", "target_blocker": True, "evidence_confidence": 0.4})
        report = k.validate_roadmap(payload)
        self.assertFalse(report["valid"])
        self.assertTrue(any("non-gate BLOCKER requires" in error for error in report["errors"]))

    def test_stale_current_claim_cannot_drive_now_item(self):
        payload = valid_payload()
        payload["claims"] = [{
            "claim_id": "C-1",
            "text": "Current vendor requirement applies",
            "claim_lane": "external",
            "claim_type": "external_current",
            "materiality": "high",
            "current_sensitive": True,
            "evidence": [{
                "source_ref": "vendor",
                "source_type": "vendor_official",
                "direction": "support",
                "directness": "direct",
                "freshness": "STALE",
                "scope_match": "exact",
                "independence_key": "vendor",
            }],
        }]
        payload["items"][0]["lane"] = "NOW"
        report = k.validate_roadmap(payload)
        self.assertFalse(report["valid"])
        self.assertTrue(any("stale current-sensitive claims" in error for error in report["errors"]))


if __name__ == "__main__":
    unittest.main()
