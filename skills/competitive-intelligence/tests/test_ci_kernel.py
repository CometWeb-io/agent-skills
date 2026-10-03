#!/usr/bin/env python3
import importlib.util
import pathlib
import tempfile
import copy
import json
import random
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

    def test_unknown_competitor_tier_is_rejected(self):
        # A tier outside 1-3 used to be scored silently: "tier1" as tier 1
        # (factor 1.00) and 4 as tier 3 (factor 0.70).
        event = {"relevance": 1, "magnitude": 1, "confidence": 1, "novelty": 1, "persistence": 1}
        for bad in ("tier1", 4, 0, 1.5, True, None):
            with self.subTest(tier=bad):
                with self.assertRaisesRegex(ValueError, "competitor_tier must be 1, 2 or 3"):
                    K.materiality_score({**event, "competitor_tier": bad})
        self.assertEqual(K.materiality_score({**event, "competitor_tier": "2"})["tier_factor"], 0.85)
        self.assertEqual(K.materiality_score({**event, "competitor_tier": 3.0})["tier_factor"], 0.70)
        self.assertEqual(K.materiality_score(event)["tier_factor"], 1.00)

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


class NoPhantomChangeTests(unittest.TestCase):
    """A delta digest is only useful if "nothing changed" survives a round trip.

    Competitor monitoring reruns on a schedule and most runs find nothing. If
    re-serialising a snapshot — different key order, same content — produced
    changes, every quiet week would read as movement and the digest would train
    its reader to ignore it.
    """

    def setUp(self):
        base = CompetitiveIntelligenceKernelTests("run")
        base.setUp()
        self.old, self.new = base.old, base.new

    def test_identical_snapshots_produce_no_changes(self):
        self.assertEqual(K.diff_snapshots(self.old, copy.deepcopy(self.old))["changes"], [])

    def test_key_order_does_not_create_changes(self):
        def reorder(value, rnd):
            if isinstance(value, dict):
                items = list(value.items())
                rnd.shuffle(items)
                return {k: reorder(v, rnd) for k, v in items}
            if isinstance(value, list):
                return [reorder(v, rnd) for v in value]
            return value

        for seed in range(4):
            with self.subTest(seed=seed):
                shuffled = reorder(copy.deepcopy(self.old), random.Random(seed))
                self.assertEqual(K.diff_snapshots(self.old, shuffled)["changes"], [])

    def test_diff_is_deterministic(self):
        first = json.dumps(K.diff_snapshots(self.old, self.new), sort_keys=True)
        second = json.dumps(K.diff_snapshots(self.old, self.new), sort_keys=True)
        self.assertEqual(first, second)

    def test_a_real_change_is_still_detected(self):
        self.assertTrue(K.diff_snapshots(self.old, self.new)["changes"])


class AtomicWriteTests(unittest.TestCase):
    """The temporary file must not have a name an attacker can plant in advance."""

    def test_planted_symlink_at_the_old_predictable_name_is_not_followed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            outside = root / "outside.txt"
            outside.write_text("keep", encoding="utf-8")
            work = root / "ws"
            work.mkdir()
            target = work / "config.json"
            (work / "config.json.tmp").symlink_to(outside)
            K._atomic_write_json(target, {"a": 1})
            self.assertEqual(outside.read_text(encoding="utf-8"), "keep")
            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), {"a": 1})
            self.assertFalse(target.is_symlink())

    def test_written_file_is_private_and_no_temporary_is_left(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp) / "snap.json"
            K._atomic_write_json(target, {"b": [1, 2]})
            self.assertEqual(target.stat().st_mode & 0o777, 0o600)
            self.assertEqual(sorted(p.name for p in pathlib.Path(tmp).iterdir()), ["snap.json"])

    def test_failed_rename_removes_the_temporary_and_keeps_the_original(self):
        from unittest import mock

        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp) / "current.json"
            target.write_text('{"old": true}\n', encoding="utf-8")
            with mock.patch.object(K.os, "replace", side_effect=OSError("disk full")):
                with self.assertRaises(OSError):
                    K._atomic_write_json(target, {"new": True})
            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), {"old": True})
            self.assertEqual(sorted(p.name for p in pathlib.Path(tmp).iterdir()), ["current.json"])

    def test_unserializable_value_creates_no_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(TypeError):
                K._atomic_write_json(pathlib.Path(tmp) / "x.json", {"bad": object()})
            self.assertEqual(list(pathlib.Path(tmp).iterdir()), [])
