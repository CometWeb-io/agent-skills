from pathlib import Path
import importlib.util
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("rewrite_guard", ROOT / "scripts" / "rewrite_guard.py")
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)


class RewriteGuardTests(unittest.TestCase):
    def test_preserved_rewrite_passes(self):
        before = "Conversion moved from 3.1% to 4.0%. See https://example.com/a."
        after = "See https://example.com/a. Conversion changed from 3.1% to 4.0%."
        self.assertTrue(MOD.compare(before, after)["passed"])

    def test_unit_change_fails(self):
        result = MOD.compare("The limit is 10 MB.", "The limit is 10 KB.")
        self.assertFalse(result["passed"])
        self.assertIn("number_unit_pairs", result["missing_invariants"])

    def test_currency_change_fails(self):
        result = MOD.compare("The fee is 1200 EUR.", "The fee is 1200 USD.")
        self.assertFalse(result["passed"])
        self.assertIn("currency_amounts", result["missing_invariants"])

    def test_version_change_fails(self):
        result = MOD.compare("Use v2.3.0.", "Use v2.4.0.")
        self.assertFalse(result["passed"])
        self.assertIn("versions", result["missing_invariants"])

    def test_date_change_fails(self):
        result = MOD.compare("Ships 2026-08-25.", "Ships 2026-08-26.")
        self.assertFalse(result["passed"])
        self.assertIn("iso_dates", result["missing_invariants"])

    def test_quote_change_fails(self):
        result = MOD.compare('She wrote, “do not ship”.', 'She wrote, “ship now”.')
        self.assertFalse(result["passed"])
        self.assertIn("quoted_spans", result["missing_invariants"])

    def test_protected_single_name_fails(self):
        result = MOD.compare("Alice approved it.", "Bob approved it.", protected_terms=["Alice"])
        self.assertFalse(result["passed"])
        self.assertIn("protected_terms", result["missing_invariants"])

    def test_tilde_fence_change_fails(self):
        before = "~~~python\nprint('a')\n~~~\n"
        after = "~~~python\nprint('b')\n~~~\n"
        result = MOD.compare(before, after)
        self.assertFalse(result["passed"])
        self.assertIn("fenced_code_blocks", result["missing_invariants"])

    def test_indented_fence_with_longer_closer_is_protected(self):
        before = "   ```python\nprint('a')\n   ````\n"
        after = "   ```python\nprint('b')\n   ````\n"
        result = MOD.compare(before, after)
        self.assertFalse(result["passed"])
        self.assertIn("fenced_code_blocks", result["missing_invariants"])

    def test_path_change_fails(self):
        result = MOD.compare("Edit src/app/main.py.", "Edit src/app/core.py.")
        self.assertFalse(result["passed"])
        self.assertIn("paths", result["missing_invariants"])

    def test_path_trailing_punctuation_is_not_part_of_invariant(self):
        result = MOD.compare("Edit src/app/main.py.", "Before editing src/app/main.py, read the note.")
        self.assertTrue(result["passed"])

    def test_proper_name_does_not_cross_sentence_boundary(self):
        before = "The beta does not support SSO. It is limited."
        after = "The beta does not support SSO. Until launch, it is limited."
        a = MOD.extract(before)["proper_name_candidates"]
        b = MOD.extract(after)["proper_name_candidates"]
        self.assertNotIn("SSO. It", a)
        self.assertNotIn("SSO. Until", b)

    def test_uuid_change_fails(self):
        before = "Request 123e4567-e89b-12d3-a456-426614174000 failed."
        after = "Request 123e4567-e89b-12d3-a456-426614174001 failed."
        result = MOD.compare(before, after)
        self.assertFalse(result["passed"])
        self.assertIn("uuids", result["missing_invariants"])

    def test_cve_change_fails(self):
        result = MOD.compare("Patch CVE-2026-12345.", "Patch CVE-2026-54321.")
        self.assertFalse(result["passed"])
        self.assertIn("cves", result["missing_invariants"])

    def test_cli_env_issue_hash_change_fails(self):
        before = "Run --dry-run with API_BASE_URL for PROJ-42 at 8f4a2c1."
        after = "Run --force with API_URL for PROJ-43 at 9a4b2c1."
        result = MOD.compare(before, after)
        self.assertFalse(result["passed"])
        self.assertIn("cli_flags", result["missing_invariants"])
        self.assertIn("env_identifiers", result["missing_invariants"])
        self.assertIn("issue_ids", result["missing_invariants"])
        self.assertIn("hashes", result["missing_invariants"])

    def test_semantic_negation_change_warns(self):
        result = MOD.compare("The beta does not support SSO.", "The beta supports SSO.")
        self.assertTrue(result["passed"])
        self.assertIn("negation", result["semantic_risk_markers"])
        self.assertTrue(any("semantic fidelity" in w for w in result["warnings"]))

    def test_repeated_invariant_can_be_consolidated(self):
        result = MOD.compare("Project X ships today. Project X is stable.", "Project X ships today and is stable.")
        self.assertTrue(result["passed"])

    def test_added_invariant_warns_by_default(self):
        result = MOD.compare("The limit is 10 MB.", "The limit is 10 MB and 20 GB.")
        self.assertTrue(result["passed"])
        self.assertTrue(result["added_invariants"])

    def test_added_invariant_fails_in_strict_mode(self):
        result = MOD.compare("The limit is 10 MB.", "The limit is 10 MB and 20 GB.", strict=True)
        self.assertFalse(result["passed"])
        self.assertTrue(result["added_invariants"])


if __name__ == "__main__":
    unittest.main()
