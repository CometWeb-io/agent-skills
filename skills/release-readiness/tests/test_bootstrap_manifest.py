#!/usr/bin/env python3
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOT = ROOT / "scripts" / "bootstrap_manifest.py"
spec = importlib.util.spec_from_file_location("bootstrap_manifest", BOOT)
bootstrap = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(bootstrap)


def context(**flag_overrides):
    flags = {k: "no" for k in bootstrap.engine.SCOPE_FLAG_KEYS}
    flags.update(flag_overrides)
    return {
        "profile": "saas_web",
        "mode": "standard",
        "release": {
            "id": "v2.0",
            "commit_sha": "abc1234",
            "environment": "production",
            "as_of": "2026-08-25T22:03:05+02:00",
        },
        "scope": {
            "audience": "external",
            "commercial": "free",
            "risk_assessment_complete": True,
            "governance_surfaces": [],
            "risk_flags": flags,
        },
    }


class BootstrapTests(unittest.TestCase):
    def test_baseline_gates_are_created_unknown_and_binding(self):
        manifest = bootstrap.build(context())
        gates = {c["gate"] for c in manifest["checks"]}
        self.assertIn("recovery_strategy", gates)
        self.assertIn("candidate_verification", gates)
        self.assertTrue(all(c["binding"] for c in manifest["checks"]))
        self.assertTrue(all(c["status"] == "unknown" for c in manifest["checks"]))

    def test_billing_change_adds_billing_gates(self):
        ctx = context(billing_change="yes")
        ctx["mode"] = "deep"
        ctx["scope"]["commercial"] = "paid"
        manifest = bootstrap.build(ctx)
        gates = {c["gate"] for c in manifest["checks"]}
        self.assertIn("billing_entitlements", gates)
        self.assertIn("billing_state_transitions", gates)

    def test_sensitive_data_adds_privacy_placeholder(self):
        ctx = context(sensitive_data_change="yes")
        ctx["mode"] = "deep"
        manifest = bootstrap.build(ctx)
        self.assertEqual(manifest["governance_gates"][0]["surface"], "privacy")
        self.assertEqual(manifest["governance_gates"][0]["status"], "counsel_required")

    def test_unknown_flags_are_preserved_not_assumed_no(self):
        ctx = context()
        ctx["scope"]["risk_flags"].pop("auth_change")
        manifest = bootstrap.build(ctx)
        self.assertEqual(manifest["scope"]["risk_flags"]["auth_change"], "unknown")


if __name__ == "__main__":
    unittest.main()
