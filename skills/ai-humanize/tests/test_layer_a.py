from pathlib import Path
import importlib.util
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("layer_a_clean", ROOT / "scripts" / "layer_a_clean.py")
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)


class LayerATests(unittest.TestCase):
    def test_removes_zero_width_space_without_collapsing_spaces(self):
        text = "A\u200bB  C\t\tD"
        cleaned, report = MOD.clean_text(text)
        self.assertEqual(cleaned, "AB  C\t\tD")
        self.assertEqual(report["chars_removed"], 1)

    def test_replaces_exotic_space_one_for_one(self):
        cleaned, report = MOD.clean_text("A\u00a0 B")
        self.assertEqual(cleaned, "A  B")
        self.assertEqual(report["chars_replaced"], 1)

    def test_markdown_preserves_fenced_code_and_indentation(self):
        text = "Intro\u200b\n\n```python\nif x:\n    print('x')\n```\n\n    - nested\n"
        cleaned, _ = MOD.clean_text(text, profile="markdown")
        self.assertEqual(cleaned, "Intro\n\n```python\nif x:\n    print('x')\n```\n\n    - nested\n")

    def test_markdown_preserves_inline_code(self):
        text = "Use `a\u200bb` in prose\u200b."
        cleaned, _ = MOD.clean_text(text, profile="markdown")
        self.assertEqual(cleaned, "Use `a\u200bb` in prose.")

    def test_markdown_preserves_indented_fence_with_longer_closer(self):
        text = "   ```python\n    x = 'a\u200bb'\n   ````\nOutside\u200b.\n"
        cleaned, _ = MOD.clean_text(text, profile="markdown")
        self.assertEqual(cleaned, "   ```python\n    x = 'a\u200bb'\n   ````\nOutside.\n")

    def test_preserves_family_emoji_zwj(self):
        text = "Family: 👨‍👩‍👧‍👦"
        cleaned, _ = MOD.clean_text(text)
        self.assertEqual(cleaned, text)

    def test_preserves_subdivision_flag_tag_sequence(self):
        england = "\U0001F3F4\U000E0067\U000E0062\U000E0065\U000E006E\U000E0067\U000E007F"
        cleaned, _ = MOD.clean_text(england)
        self.assertEqual(cleaned, england)

    def test_preserves_complex_script_joiner(self):
        text = "می\u200cروم"
        cleaned, _ = MOD.clean_text(text)
        self.assertEqual(cleaned, text)

    def test_bidi_controls_can_be_preserved_explicitly(self):
        text = "abc\u2067עברית\u2069def"
        stripped, _ = MOD.clean_text(text)
        preserved, _ = MOD.clean_text(text, preserve_bidi_controls=True)
        self.assertNotEqual(stripped, text)
        self.assertEqual(preserved, text)

    def test_default_nfc_does_not_compatibility_fold_ligature(self):
        text = "oﬃce"
        cleaned, _ = MOD.clean_text(text)
        self.assertEqual(cleaned, text)

    def test_nfkc_is_opt_in(self):
        cleaned, report = MOD.clean_text("oﬃce", normalization="nfkc")
        self.assertEqual(cleaned, "office")
        self.assertTrue(report["normalized"])

    def test_aggressive_homoglyph_is_opt_in(self):
        text = "pаypal"  # Cyrillic a
        conservative, _ = MOD.clean_text(text)
        aggressive, _ = MOD.clean_text(text, aggressive_homoglyphs=True)
        self.assertEqual(conservative, text)
        self.assertEqual(aggressive, "paypal")

    def test_check_mode_is_non_destructive_and_signals_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "draft.txt"
            path.write_text("A\u200bB", encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "layer_a_clean.py"), str(path), "--check"],
                text=True,
                capture_output=True,
            )
            self.assertEqual(proc.returncode, 1)
            self.assertEqual(path.read_text(encoding="utf-8"), "A\u200bB")


if __name__ == "__main__":
    unittest.main()
