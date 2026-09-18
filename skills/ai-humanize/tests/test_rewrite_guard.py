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


class SemanticRiskOptInTests(unittest.TestCase):
    """pass/fail is an invariant verdict unless the caller opts in.

    A rewrite that inverts every claim keeps all hard invariants, so the guard
    passes by default and under --strict, whose documented job is added
    invariant-like tokens. That is defensible — negation and modality shift
    legitimately during paraphrase — but it left no way for automation to stop
    on a meaning flip except by parsing JSON.
    """

    BEFORE = "The beta does not support SSO. We are not committing to a date, and it may not ship in Q4 at all."
    INVERTED = "The beta now supports SSO. We are committing to a date, and it will ship in Q4."

    def test_inversion_still_passes_by_default_and_under_strict(self):
        for strict in (False, True):
            result = MOD.compare(self.BEFORE, self.INVERTED, strict=strict)
            self.assertTrue(result["passed"], f"strict={strict}")
            self.assertTrue(result["semantic_risk_markers"])

    def test_opt_in_fails_on_inversion(self):
        result = MOD.compare(self.BEFORE, self.INVERTED, fail_on_semantic_risk=True)
        self.assertFalse(result["passed"])
        self.assertTrue(result["fail_on_semantic_risk"])
        for marker in ("negation", "modality", "scope"):
            self.assertIn(marker, result["semantic_risk_markers"])

    def test_opt_in_does_not_fire_on_a_faithful_rewrite(self):
        result = MOD.compare(self.BEFORE, self.BEFORE, fail_on_semantic_risk=True)
        self.assertTrue(result["passed"])
        self.assertEqual(result["semantic_risk_markers"], {})

    def test_opt_in_is_not_free_and_fires_on_faithful_paraphrase(self):
        """Pin the cost of the flag rather than pretend it has none.

        "We are not committing to a date" -> "No date is committed" preserves
        meaning but drops a negation token, so the marker heuristic fires. That
        is why this is opt-in and why --strict deliberately does not imply it:
        a caller who turns it on is choosing false positives over a missed
        meaning flip, and should know which trade they made.
        """
        paraphrase = "The beta does not support SSO. No date is committed, and it may not ship in Q4 at all."
        strict_result = MOD.compare(self.BEFORE, paraphrase, fail_on_semantic_risk=True)
        self.assertFalse(strict_result["passed"])
        self.assertIn("negation", strict_result["semantic_risk_markers"])
        # The same paraphrase is accepted by the default invariant verdict.
        self.assertTrue(MOD.compare(self.BEFORE, paraphrase)["passed"])
