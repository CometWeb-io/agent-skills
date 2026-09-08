#!/usr/bin/env python3
import copy
import importlib.util
import unittest
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[1] / "scripts" / "readiness_engine.py"
spec = importlib.util.spec_from_file_location("readiness_engine", ENGINE)
engine = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(engine)

AS_OF = "2026-08-25T22:03:05+02:00"
CANDIDATE = "abc1234"


def release():
    return {
        "id": "v2.0.0",
        "commit_sha": CANDIDATE,
        "environment": "production",
        "as_of": AS_OF,
    }


def scope(**flag_overrides):
    flags = {k: "no" for k in engine.SCOPE_FLAG_KEYS}
    flags.update(flag_overrides)
    return {
        "audience": "external",
        "commercial": "free",
        "risk_assessment_complete": True,
        "governance_surfaces": [],
        "risk_flags": flags,
    }


def evidence(level="verified", candidate=True):
    data = {
        "summary": "candidate-specific evidence",
        "last_verified_at": AS_OF,
        "source_type": "ci",
    }
    if candidate:
        data["candidate_ref"] = CANDIDATE
    return data


def check(check_id, gate, domain, **overrides):
    base = {
        "id": check_id,
        "gate": gate,
        "domain": domain,
        "title": check_id,
        "status": "pass",
        "severity": "critical",
        "binding": True,
        "evidence_level": "verified",
        "required_evidence": "verified",
        "freshness": "current",
        "evidence": evidence(),
    }
    base.update(overrides)
    return base


def green_checks():
    return [
        check("product.acceptance", "release_scope_acceptance", "product"),
        check("qa.candidate", "candidate_verification", "qa"),
        check("security.release", "security_release", "security"),
        check("ops.delivery", "release_delivery", "ops"),
        check("ops.recovery", "recovery_strategy", "ops"),
        check("ops.observability", "observability", "ops"),
        check(
            "docs.operator",
            "operator_docs",
            "docs",
            severity="major",
            evidence_level="supported",
            required_evidence="supported",
            evidence={"summary": "runbook reviewed", "last_verified_at": AS_OF, "source_type": "repo"},
        ),
        check(
            "support.path",
            "support_path",
            "support",
            severity="major",
            evidence_level="supported",
            required_evidence="supported",
            evidence={"summary": "support escalation route reviewed", "last_verified_at": AS_OF, "source_type": "docs"},
        ),
    ]


def green_manifest():
    return {
        "manifest_version": 2,
        "profile": "saas_web",
        "mode": "standard",
        "release": release(),
        "scope": scope(),
        "checks": green_checks(),
        "governance_gates": [],
    }


class ReadinessEngineV2Tests(unittest.TestCase):
    def test_green_manifest_go(self):
        result = engine.evaluate(green_manifest())
        self.assertEqual(result["verdict"], "GO")
        self.assertEqual(result["risk_tier"], "R1")
        self.assertEqual(result["evidence_coverage"], 100.0)
        self.assertFalse(result["missing_required_gates"])

    def test_missing_required_gate_defers(self):
        manifest = green_manifest()
        manifest["checks"] = [c for c in manifest["checks"] if c["gate"] != "recovery_strategy"]
        result = engine.evaluate(manifest)
        self.assertEqual(result["verdict"], "DEFER")
        self.assertIn("recovery_strategy", result["missing_required_gates"])

    def test_required_gate_must_be_binding(self):
        manifest = green_manifest()
        next(c for c in manifest["checks"] if c["gate"] == "observability")["binding"] = False
        result = engine.evaluate(manifest)
        self.assertEqual(result["verdict"], "DEFER")
        self.assertIn("observability", result["missing_required_gates"])

    def test_unknown_risk_flag_defers(self):
        manifest = green_manifest()
        manifest["scope"]["risk_flags"]["auth_change"] = "unknown"
        result = engine.evaluate(manifest)
        self.assertEqual(result["verdict"], "DEFER")
        self.assertIn("risk_flag:auth_change", result["scope_gaps"])

    def test_incomplete_risk_assessment_defers(self):
        manifest = green_manifest()
        manifest["scope"]["risk_assessment_complete"] = False
        result = engine.evaluate(manifest)
        self.assertEqual(result["verdict"], "DEFER")

    def test_high_risk_release_requires_deep(self):
        manifest = green_manifest()
        manifest["scope"] = scope(auth_change="yes")
        manifest["checks"].append(check("security.authz", "auth_access_control", "security"))
        result = engine.evaluate(manifest)
        self.assertEqual(result["risk_tier"], "R3")
        self.assertEqual(result["verdict"], "DEFER")
        self.assertEqual(result["required_mode_floor"], "deep")

    def test_high_risk_deep_can_go(self):
        manifest = green_manifest()
        manifest["mode"] = "deep"
        manifest["scope"] = scope(auth_change="yes")
        manifest["checks"].append(check("security.authz", "auth_access_control", "security"))
        result = engine.evaluate(manifest)
        self.assertEqual(result["verdict"], "GO")
        self.assertEqual(result["thresholds"]["min_coverage"], 98.0)

    def test_security_binding_failure_no_go(self):
        manifest = green_manifest()
        security = next(c for c in manifest["checks"] if c["gate"] == "security_release")
        security["status"] = "fail"
        security["evidence_level"] = "claimed"
        result = engine.evaluate(manifest)
        self.assertEqual(result["verdict"], "NO_GO")
        self.assertIn("security.release", [x["id"] for x in result["blocking_failures"]])

    def test_fail_with_missing_evidence_becomes_unknown(self):
        manifest = green_manifest()
        security = next(c for c in manifest["checks"] if c["gate"] == "security_release")
        security["status"] = "fail"
        security["evidence_level"] = "missing"
        result = engine.evaluate(manifest)
        self.assertEqual(result["verdict"], "DEFER")
        self.assertIn("security.release", [x["id"] for x in result["binding_unknowns"]])

    def test_claimed_binding_pass_defers(self):
        manifest = green_manifest()
        qa = next(c for c in manifest["checks"] if c["gate"] == "candidate_verification")
        qa["evidence_level"] = "claimed"
        result = engine.evaluate(manifest)
        self.assertEqual(result["verdict"], "DEFER")

    def test_binding_pass_requires_structured_timestamp(self):
        manifest = green_manifest()
        qa = next(c for c in manifest["checks"] if c["gate"] == "candidate_verification")
        qa["evidence"] = {"summary": "CI passed", "candidate_ref": CANDIDATE}
        result = engine.evaluate(manifest)
        self.assertEqual(result["verdict"], "DEFER")

    def test_verified_binding_pass_requires_candidate_match(self):
        manifest = green_manifest()
        qa = next(c for c in manifest["checks"] if c["gate"] == "candidate_verification")
        qa["evidence"]["candidate_ref"] = "different-commit"
        result = engine.evaluate(manifest)
        self.assertEqual(result["verdict"], "DEFER")
        self.assertIn("qa.candidate", [x["id"] for x in result["evidence_downgrades"]])

    def test_stale_binding_pass_defers(self):
        manifest = green_manifest()
        next(c for c in manifest["checks"] if c["gate"] == "recovery_strategy")["freshness"] = "stale"
        result = engine.evaluate(manifest)
        self.assertEqual(result["verdict"], "DEFER")

    def test_controlled_pass_requires_owner_mitigation_and_due(self):
        manifest = green_manifest()
        docs = next(c for c in manifest["checks"] if c["gate"] == "operator_docs")
        docs.update({"status": "pass_with_controls", "control_owner": "", "mitigation": "", "control_due": ""})
        result = engine.evaluate(manifest)
        self.assertEqual(result["verdict"], "DEFER")

    def test_expired_control_defers(self):
        manifest = green_manifest()
        docs = next(c for c in manifest["checks"] if c["gate"] == "operator_docs")
        docs.update({
            "status": "pass_with_controls",
            "control_owner": "ops",
            "mitigation": "pair operator on launch",
            "control_due": "2026-08-24T12:00:00+02:00",
        })
        result = engine.evaluate(manifest)
        self.assertEqual(result["verdict"], "DEFER")

    def test_valid_controlled_pass_go_with_controls(self):
        manifest = green_manifest()
        docs = next(c for c in manifest["checks"] if c["gate"] == "operator_docs")
        docs.update({
            "status": "pass_with_controls",
            "control_owner": "ops",
            "mitigation": "pair operator on launch",
            "control_due": "2026-08-27T12:00:00+02:00",
        })
        result = engine.evaluate(manifest)
        self.assertEqual(result["verdict"], "GO_WITH_CONTROLS")

    def test_accepted_risk_for_nonbinding_major(self):
        manifest = green_manifest()
        manifest["checks"].append({
            "id": "docs.minor_gap",
            "domain": "docs",
            "status": "accepted_risk",
            "severity": "major",
            "binding": False,
            "evidence_level": "supported",
            "required_evidence": "supported",
            "freshness": "current",
            "evidence": {"summary": "known docs gap", "last_verified_at": AS_OF},
            "risk_acceptance": {
                "approved_by": "release-owner",
                "owner": "docs",
                "rationale": "not needed for critical launch path",
                "mitigation": "support has workaround",
                "expires_at": "2026-08-30T12:00:00+02:00",
            },
        })
        result = engine.evaluate(manifest)
        self.assertEqual(result["verdict"], "GO_WITH_CONTROLS")
        self.assertEqual(result["accepted_risks"][0]["id"], "docs.minor_gap")

    def test_accepted_risk_for_binding_check_is_invalid(self):
        manifest = green_manifest()
        manifest["checks"][0]["status"] = "accepted_risk"
        with self.assertRaises(engine.ManifestError):
            engine.evaluate(manifest)

    def test_paid_product_requires_billing_entitlements_gate(self):
        manifest = green_manifest()
        manifest["scope"]["commercial"] = "paid"
        result = engine.evaluate(manifest)
        self.assertEqual(result["verdict"], "DEFER")
        self.assertIn("billing_entitlements", result["missing_required_gates"])

    def test_billing_change_requires_two_billing_gates_and_deep(self):
        manifest = green_manifest()
        manifest["scope"] = scope(billing_change="yes")
        manifest["scope"]["commercial"] = "paid"
        manifest["mode"] = "deep"
        manifest["checks"].extend([
            check("billing.entitlements", "billing_entitlements", "billing"),
            check("billing.transitions", "billing_state_transitions", "billing"),
        ])
        result = engine.evaluate(manifest)
        self.assertEqual(result["verdict"], "GO")
        self.assertEqual(result["risk_tier"], "R3")

    def test_governance_surface_missing_gate_defers(self):
        manifest = green_manifest()
        manifest["scope"]["governance_surfaces"] = ["legal"]
        result = engine.evaluate(manifest)
        self.assertEqual(result["verdict"], "DEFER")
        self.assertIn("legal", result["missing_governance_gates"])

    def test_governance_block_no_go(self):
        manifest = green_manifest()
        manifest["scope"]["governance_surfaces"] = ["legal"]
        manifest["governance_gates"] = [{"surface": "legal", "status": "block", "evidence": {"summary": "binding legal blocker"}}]
        result = engine.evaluate(manifest)
        self.assertEqual(result["verdict"], "NO_GO")

    def test_governance_clear_requires_evidence(self):
        manifest = green_manifest()
        manifest["scope"]["governance_surfaces"] = ["legal"]
        manifest["governance_gates"] = [{"surface": "legal", "status": "clear"}]
        result = engine.evaluate(manifest)
        self.assertEqual(result["verdict"], "DEFER")

    def test_governance_clear_with_controls_is_conditional(self):
        manifest = green_manifest()
        manifest["scope"]["governance_surfaces"] = ["legal"]
        manifest["governance_gates"] = [{
            "surface": "legal",
            "status": "clear_with_controls",
            "evidence": {"summary": "reviewed current terms", "last_verified_at": AS_OF},
            "control_owner": "ops",
            "control": "limit release geography",
            "control_due": "2026-08-30T12:00:00+02:00",
        }]
        result = engine.evaluate(manifest)
        self.assertEqual(result["verdict"], "GO_WITH_CONTROLS")


    def test_governance_clear_with_timestamp_can_go(self):
        manifest = green_manifest()
        manifest["scope"]["governance_surfaces"] = ["legal"]
        manifest["governance_gates"] = [{
            "surface": "legal",
            "status": "clear",
            "evidence": {"summary": "current release-specific review", "last_verified_at": AS_OF},
        }]
        result = engine.evaluate(manifest)
        self.assertEqual(result["verdict"], "GO")

    def test_required_governance_not_required_does_not_satisfy_gate(self):
        manifest = green_manifest()
        manifest["scope"]["governance_surfaces"] = ["privacy"]
        manifest["governance_gates"] = [{
            "surface": "privacy",
            "status": "not_required",
            "rationale": "attempted bypass",
        }]
        result = engine.evaluate(manifest)
        self.assertEqual(result["verdict"], "DEFER")

    def test_explicit_unlisted_governance_block_still_blocks(self):
        manifest = green_manifest()
        manifest["governance_gates"] = [{
            "surface": "reputation",
            "status": "block",
            "evidence": {"summary": "known release blocker"},
        }]
        result = engine.evaluate(manifest)
        self.assertEqual(result["verdict"], "NO_GO")

    def test_gate_domain_mismatch_is_invalid(self):
        manifest = green_manifest()
        manifest["checks"][0]["gate"] = "security_release"
        with self.assertRaises(engine.ManifestError):
            engine.evaluate(manifest)

    def test_sensitive_data_derives_privacy_gate_and_required_check(self):
        manifest = green_manifest()
        manifest["scope"] = scope(sensitive_data_change="yes")
        manifest["mode"] = "deep"
        manifest["checks"].append(check("security.data", "sensitive_data_handling", "security"))
        result = engine.evaluate(manifest)
        self.assertIn("privacy", result["required_governance_surfaces"])
        self.assertIn("privacy", result["missing_governance_gates"])
        self.assertEqual(result["verdict"], "DEFER")

    def test_lower_threshold_override_cannot_weaken_risk_floor(self):
        manifest = green_manifest()
        manifest["thresholds"] = {"go_score": 1, "conditional_score": 1, "min_coverage": 1}
        result = engine.evaluate(manifest)
        self.assertEqual(result["thresholds"]["go_score"], 88.0)
        self.assertEqual(result["thresholds"]["min_coverage"], 90.0)

    def test_na_requires_reason(self):
        manifest = green_manifest()
        manifest["checks"].append({
            "id": "billing.na",
            "domain": "billing",
            "status": "na",
            "severity": "minor",
            "binding": False,
            "applicable": False,
        })
        with self.assertRaises(engine.ManifestError):
            engine.evaluate(manifest)

    def test_missing_artifact_identity_defers(self):
        manifest = green_manifest()
        manifest["release"].pop("commit_sha")
        result = engine.evaluate(manifest)
        self.assertEqual(result["verdict"], "DEFER")
        self.assertIn("artifact_identity", result["release_identity_gaps"])

    def test_snapshot_hash_is_deterministic(self):
        manifest = green_manifest()
        a = engine.evaluate(copy.deepcopy(manifest))["snapshot_hash"]
        b = engine.evaluate(copy.deepcopy(manifest))["snapshot_hash"]
        self.assertEqual(a, b)

    def test_compare_reports_new_blocker(self):
        previous = green_manifest()
        current = copy.deepcopy(previous)
        security = next(c for c in current["checks"] if c["gate"] == "security_release")
        security["status"] = "fail"
        security["evidence_level"] = "claimed"
        delta = engine.compare(current, previous)
        self.assertEqual(delta["previous_verdict"], "GO")
        self.assertEqual(delta["current_verdict"], "NO_GO")
        self.assertIn("security.release", delta["new_blockers"])


if __name__ == "__main__":
    unittest.main()
