#!/usr/bin/env python3
import importlib.util
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("ci_kernel", ROOT / "scripts" / "ci_kernel.py")
K = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(K)


class CompetitiveIntelligenceKernelTests(unittest.TestCase):
    def setUp(self):
        self.old = K._read_json(ROOT / "tests" / "fixtures" / "acme-old.json")
        self.new = K._read_json(ROOT / "tests" / "fixtures" / "acme-new.json")

    def test_snapshot_validation(self):
        self.assertTrue(K.validate_snapshot(self.old)["valid"])

    def test_diff_ignores_capture_timestamp(self):
        report = K.diff_snapshots(self.old, self.new)
        paths = {c["field_path"] for c in report["changes"]}
        self.assertNotIn("captured_at", paths)

    def test_pricing_change_is_classified(self):
        report = K.diff_snapshots(self.old, self.new)
        pricing = [c for c in report["changes"] if c["field_path"] == "state.pricing.tiers.pro_monthly"]
        self.assertEqual(len(pricing), 1)
        self.assertEqual(pricing[0]["category"], "PRICING_PACKAGING")
        self.assertEqual(pricing[0]["before"], 39)
        self.assertEqual(pricing[0]["after"], 49)

    def test_scalar_list_changes_are_granular(self):
        report = K.diff_snapshots(self.old, self.new)
        added = [c for c in report["changes"] if c["change_type"] == "ADDED"]
        self.assertTrue(any(c["after"] == "AI Assistant" for c in added))
        self.assertTrue(any(c["after"] == "Enterprise" for c in added))

    def test_event_key_is_stable(self):
        event = {
            "competitor_id": "acme",
            "category": "PRICING_PACKAGING",
            "field_path": "state.pricing.tiers.pro_monthly",
            "before": 39,
            "after": 49,
        }
        self.assertEqual(K.event_key_from_json(event), K.event_key_from_json(dict(event)))

    def test_materiality_thresholds(self):
        high = K.materiality_score({
            "relevance": 1,
            "magnitude": 0.9,
            "confidence": 1,
            "novelty": 0.9,
            "persistence": 0.8,
            "competitor_tier": 1,
        })
        self.assertEqual(high["severity"], "CRITICAL")
        low = K.materiality_score({
            "relevance": 0.2,
            "magnitude": 0.1,
            "confidence": 0.4,
            "novelty": 0.2,
            "persistence": 0.2,
            "competitor_tier": 3,
        })
        self.assertIn(low["severity"], {"NOISE", "LOW"})

    def test_freshness(self):
        current = K.freshness("2026-08-24T00:00:00Z", 7, "2026-08-25T00:00:00Z")
        stale = K.freshness("2026-08-01T00:00:00Z", 7, "2026-08-25T00:00:00Z")
        self.assertEqual(current["status"], "CURRENT")
        self.assertEqual(stale["status"], "STALE")

    def test_workspace_snapshot_acceptance_and_event_dedupe(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td) / ".competitive-intelligence"
            init = K.init_workspace(root, "Our Product")
            self.assertTrue(pathlib.Path(init["config_path"]).exists())

            first = K.accept_snapshot(root, ROOT / "tests" / "fixtures" / "acme-old.json")
            self.assertTrue(pathlib.Path(first["snapshot_path"]).exists())
            self.assertTrue(pathlib.Path(first["current_path"]).exists())
            self.assertTrue(first["state_changed"])

            second = K.accept_snapshot(root, ROOT / "tests" / "fixtures" / "acme-new.json")
            self.assertEqual(second["change_count"], 3)
            self.assertTrue(second["state_changed"])

            event = {
                "competitor_id": "acme",
                "category": "PRICING_PACKAGING",
                "field_path": "state.pricing.tiers.pro_monthly",
                "before": 39,
                "after": 49,
                "first_observed_at": "2026-08-25T10:00:00Z",
                "verification_state": "CONFIRMED",
                "materiality": {"score": 82, "severity": "CRITICAL"},
                "disposition": "DEEP_DIVE",
            }
            appended = K.append_event(root, event)
            duplicate = K.append_event(root, event)
            self.assertTrue(appended["appended"])
            self.assertFalse(duplicate["appended"])
            self.assertTrue(duplicate["duplicate"])

            revised = dict(event)
            revised["verification_state"] = "RETRACTED"
            revision = K.append_event(root, revised)
            self.assertTrue(revision["appended"])
            self.assertTrue(revision["revision"])


if __name__ == "__main__":
    unittest.main()
