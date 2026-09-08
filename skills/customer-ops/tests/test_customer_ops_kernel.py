#!/usr/bin/env python3
import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("customer_ops_kernel", ROOT / "scripts" / "customer_ops_kernel.py")
mod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(mod)


class PriorityTests(unittest.TestCase):
    def test_p0_requires_critical_active_harm(self):
        out = mod.priority_assess({
            "impact": 4, "urgency": 4, "breadth": 4, "recurrence": 1,
            "workaround": 4, "customer_risk": 0, "strategic_value": 0,
        })
        self.assertEqual(out["operational_priority"], "P0")

    def test_strategic_account_does_not_inflate_operational_priority(self):
        out = mod.priority_assess({
            "impact": 1, "urgency": 1, "breadth": 1, "recurrence": 0,
            "workaround": 1, "customer_risk": 0, "strategic_value": 4,
        })
        self.assertEqual(out["operational_priority"], "P3")
        self.assertEqual(out["account_escalation"], "EXPEDITED")

    def test_low_value_account_can_still_be_p0(self):
        out = mod.priority_assess({
            "impact": 4, "urgency": 4, "breadth": 3, "recurrence": 1,
            "workaround": 4, "customer_risk": 0, "strategic_value": 0,
        })
        self.assertEqual(out["operational_priority"], "P0")
        self.assertEqual(out["account_escalation"], "STANDARD")

    def test_security_gate_is_separate_from_priority(self):
        out = mod.priority_assess({
            "impact": 1, "urgency": 1, "breadth": 1, "recurrence": 0,
            "workaround": 1, "security_signal": True,
        })
        self.assertEqual(out["operational_priority"], "P3")
        self.assertTrue(out["specialist_gate_required"])
        self.assertIn("security", out["specialist_gates"])

    def test_operational_modifier_raises_at_most_one_band(self):
        out = mod.priority_assess({
            "impact": 2, "urgency": 1, "breadth": 4, "recurrence": 4,
            "workaround": 4,
        })
        self.assertEqual(out["base_priority"], "P2")
        self.assertEqual(out["operational_priority"], "P1")

    def test_rank_score_is_tie_break_only(self):
        out = mod.priority_assess({
            "impact": 2, "urgency": 1, "breadth": 1, "recurrence": 1,
            "workaround": 1,
        })
        self.assertIn("Tie-break", out["rank_score_note"])


class RetentionTests(unittest.TestCase):
    def base(self, **overrides):
        data = {k: 0 for k in mod.RETENTION_DIMENSIONS}
        data.update(overrides)
        return data

    def test_explicit_cancel_intent_is_high(self):
        out = mod.churn_risk(self.base(cancel_intent=3))
        self.assertEqual(out["risk_level"], "HIGH")
        self.assertEqual(out["expressed_exit_intent"], "EXPLICIT")

    def test_explicit_exit_plus_pressure_is_critical(self):
        out = mod.churn_risk(self.base(cancel_intent=3, support_pain=3))
        self.assertEqual(out["risk_level"], "CRITICAL")

    def test_no_signal_has_unknown_evidence_grade(self):
        out = mod.churn_risk(self.base())
        self.assertEqual(out["risk_level"], "LOW")
        self.assertEqual(out["evidence_grade"], "UNKNOWN")

    def test_evidence_grade_high_requires_direct_and_independent(self):
        out = mod.churn_risk(self.base(
            support_pain=2, direct_evidence_count=1, independent_source_count=2,
            evidence_current=True,
        ))
        self.assertEqual(out["evidence_grade"], "HIGH")

    def test_conflicted_evidence_is_visible(self):
        out = mod.churn_risk(self.base(
            support_pain=3, relationship_risk=2, evidence_conflicted=True,
        ))
        self.assertEqual(out["evidence_grade"], "CONFLICTED")

    def test_retention_output_never_claims_probability(self):
        out = mod.churn_risk(self.base(usage_decline=2, renewal_pressure=2))
        self.assertNotIn("probability", {k.lower() for k in out.keys()})
        self.assertIn("not churn probability", out["disclaimer"])


class IncidentTests(unittest.TestCase):
    def test_broad_critical_outage_is_sev1(self):
        out = mod.incident_severity({
            "impact": 4, "breadth": 4, "workaround": 4, "critical_function": True,
        })
        self.assertEqual(out["customer_impact_severity"], "SEV1")

    def test_security_gate_does_not_relabel_customer_severity(self):
        out = mod.incident_severity({
            "impact": 1, "breadth": 1, "workaround": 1,
            "critical_function": False, "confirmed_security_incident": True,
        })
        self.assertEqual(out["customer_impact_severity"], "SEV3")
        self.assertIn("security", out["specialist_gates"])

    def test_non_incident_stays_non_incident(self):
        out = mod.incident_severity({
            "impact": 0, "breadth": 0, "workaround": 0, "critical_function": False,
        })
        self.assertEqual(out["customer_impact_severity"], "NOT_INCIDENT")


class DeadlineTests(unittest.TestCase):
    def test_provider_native_paused_wins(self):
        out = mod.deadline_status({"native_status": "paused"})
        self.assertEqual(out["status"], "PAUSED")
        self.assertEqual(out["source"], "native_status")

    def test_authoritative_due_at_at_risk(self):
        out = mod.deadline_status({
            "now": "2026-08-25T10:46:00+02:00",
            "due_at": "2026-08-25T11:00:00+02:00",
            "warning_minutes": 15,
        })
        self.assertEqual(out["status"], "AT_RISK")

    def test_authoritative_due_at_breached(self):
        out = mod.deadline_status({
            "now": "2026-08-25T11:01:00+02:00",
            "due_at": "2026-08-25T11:00:00+02:00",
        })
        self.assertEqual(out["status"], "BREACHED")

    def test_start_plus_target_is_not_enough_for_provider_sla(self):
        out = mod.deadline_status({
            "start_at": "2026-08-25T10:00:00+02:00",
            "now": "2026-08-25T10:46:00+02:00",
            "target_minutes": 60,
        })
        self.assertEqual(out["status"], "UNKNOWN")

    def test_continuous_clock_must_be_explicit(self):
        out = mod.deadline_status({
            "clock_mode": "continuous",
            "start_at": "2026-08-25T10:00:00+02:00",
            "now": "2026-08-25T10:46:00+02:00",
            "target_minutes": 60,
            "warning_minutes": 15,
        })
        self.assertEqual(out["status"], "AT_RISK")
        self.assertEqual(out["source"], "explicit_continuous_clock_fallback")

    def test_timezone_is_required(self):
        out = mod.deadline_status({
            "now": "2026-08-25T10:46:00",
            "due_at": "2026-08-25T11:00:00+02:00",
        })
        self.assertEqual(out["status"], "UNKNOWN")


class DedupeTests(unittest.TestCase):
    def test_dedupe_key_is_stable(self):
        a = mod.dedupe_key({
            "symptom": " Export returns EMPTY CSV ", "component": "Reports",
            "environment": "prod", "trigger": ">1000 rows", "error_signature": "",
        })
        b = mod.dedupe_key({
            "symptom": "export returns empty csv", "component": "reports",
            "environment": "prod", "trigger": ">1000 rows", "error_signature": "",
        })
        self.assertEqual(a["dedupe_key"], b["dedupe_key"])
        self.assertEqual(a["decision"], "CANDIDATE_ONLY")

    def test_pair_similarity_never_auto_merges(self):
        row = {
            "symptom": "export returns empty csv", "component": "reports",
            "environment": "prod", "trigger": "more than 1000 rows", "error_signature": "E42",
        }
        out = mod.dedupe_pair({"left": row, "right": dict(row)})
        self.assertEqual(out["decision"], "LIKELY_SAME_CANDIDATE")
        self.assertIn("Never auto-merge", out["note"])

    def test_different_symptom_is_distinct_candidate(self):
        left = {"symptom": "export returns empty csv", "component": "reports", "environment": "prod", "trigger": "large export", "error_signature": "E42"}
        right = {"symptom": "login button misaligned", "component": "auth", "environment": "staging", "trigger": "mobile safari", "error_signature": "UI"}
        out = mod.dedupe_pair({"left": left, "right": right})
        self.assertEqual(out["decision"], "DISTINCT_CANDIDATE")


class CommitmentTests(unittest.TestCase):
    def test_no_due_date_does_not_create_overdue(self):
        out = mod.commitment_status({"state": "OPEN"})
        self.assertEqual(out["status"], "OPEN")

    def test_commitment_due_soon(self):
        out = mod.commitment_status({
            "due_at": "2026-08-25T14:00:00+02:00",
            "now": "2026-08-25T12:00:00+02:00",
            "warning_minutes": 180,
        })
        self.assertEqual(out["status"], "DUE_SOON")

    def test_commitment_overdue(self):
        out = mod.commitment_status({
            "due_at": "2026-08-25T11:00:00+02:00",
            "now": "2026-08-25T12:00:00+02:00",
        })
        self.assertEqual(out["status"], "OVERDUE")


class TransitionAndGateTests(unittest.TestCase):
    def test_handoff_proposed_is_not_done(self):
        out = mod.transition_check({"entity": "handoff", "from_state": "PROPOSED", "to_state": "DONE"})
        self.assertFalse(out["allowed"])

    def test_handoff_requires_acceptance_path(self):
        out = mod.transition_check({"entity": "handoff", "from_state": "PROPOSED", "to_state": "ACCEPTED"})
        self.assertTrue(out["allowed"])

    def test_case_cannot_jump_resolved_to_closed(self):
        out = mod.transition_check({"entity": "case", "from_state": "RESOLVED", "to_state": "CLOSED"})
        self.assertFalse(out["allowed"])

    def test_case_verified_can_close(self):
        out = mod.transition_check({"entity": "case", "from_state": "VERIFIED", "to_state": "CLOSED"})
        self.assertTrue(out["allowed"])

    def test_github_gate_blocks_secret_publication(self):
        out = mod.case_gate({
            "stage": "GITHUB_READY",
            "customer_symptom": "export fails",
            "expected_behavior": "csv downloads",
            "actual_behavior": "empty file",
            "reproduction_state": "reproduced",
            "verification_criteria": "export 1001 rows works",
            "dedupe_search_status": "done",
            "privacy_preflight_status": "blocked",
            "repo_conventions_status": "done",
        })
        self.assertEqual(out["status"], "BLOCK")

    def test_close_blocks_without_verification(self):
        out = mod.case_gate({
            "stage": "CLOSED", "verified": False,
            "customer_followup_status": "sent",
        })
        self.assertEqual(out["status"], "BLOCK")

    def test_close_passes_after_verification_and_followup(self):
        out = mod.case_gate({
            "stage": "CLOSED", "verified": True,
            "customer_followup_status": "sent",
            "open_commitments_count": 0,
            "open_critical_handoffs_count": 0,
        })
        self.assertEqual(out["status"], "PASS")

    def test_customer_send_requires_authority_and_current_facts(self):
        out = mod.case_gate({
            "stage": "CUSTOMER_SEND", "message": "We fixed it.",
            "recipient_resolved": True, "facts_current": False,
            "write_authorized": False, "privacy_preflight_status": "clear",
        })
        self.assertEqual(out["status"], "BLOCK")
        self.assertGreaterEqual(len(out["blockers"]), 2)


class PrivacyTests(unittest.TestCase):
    def test_privacy_scan_redacts_email_and_bearer(self):
        out = mod.privacy_scan({"text": "Contact user@example.com Authorization: Bearer abcdefghijklmnop"})
        self.assertEqual(out["status"], "FINDINGS")
        self.assertNotIn("user@example.com", out["redacted_text"])
        self.assertNotIn("abcdefghijklmnop", out["redacted_text"])

    def test_privacy_scan_is_not_proof_of_safety(self):
        out = mod.privacy_scan({"text": "generic bug report"})
        self.assertEqual(out["status"], "NO_OBVIOUS_FINDINGS")
        self.assertIn("cannot prove", out["note"])


if __name__ == "__main__":
    unittest.main()
