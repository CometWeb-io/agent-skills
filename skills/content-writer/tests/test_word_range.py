import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "word_range.py"


class WordRangeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.body = Path(self.temp.name) / "body.md"
        self.body.write_text("one two three", encoding="utf-8")

    def run_cli(self, *args, body=None):
        result = subprocess.run(
            [sys.executable, "-B", str(SCRIPT), str(body or self.body), *args],
            capture_output=True, text=True, timeout=5,
        )
        return result.returncode, json.loads(result.stdout)

    def test_inclusive_bounds_and_one_sided_ranges(self):
        for args, verdict in [
            (("--min-words", "3", "--max-words", "3"), "PASS"),
            (("--min-words", "2", "--max-words", "3"), "PASS"),
            (("--min-words", "3", "--max-words", "4"), "PASS"),
            (("--min-words", "4"), "FAIL"),
            (("--max-words", "2"), "FAIL"),
            (("--min-words", "0"), "PASS"),
        ]:
            with self.subTest(args=args):
                code, result = self.run_cli(*args)
                self.assertEqual(code, 1 if verdict == "FAIL" else 0)
                self.assertEqual(result["verdict"], verdict)
                self.assertEqual(result["word_count"], 3)
                self.assertTrue(result["checked_bounds"])

    def test_no_bounds_counts_without_claiming_range_checked(self):
        code, result = self.run_cli()
        self.assertEqual(code, 0)
        self.assertEqual(result, {
            "verdict": "COUNTED", "word_count": 3, "min_words": None,
            "max_words": None, "checked_bounds": False,
        })

    def test_unicode_whitespace_without_normalizing_or_parsing_markdown(self):
        self.body.write_text(
            "#\tZażółć\u00a0gęślą\u2003jaźń\n[link](https://example.com) "
            "don't state-of-the-art 中文\u200b文\n```py\nprint('a b')\n```", encoding="utf-8",
        )
        code, result = self.run_cli("--min-words", "12", "--max-words", "12")
        self.assertEqual(code, 0)
        self.assertEqual(result["word_count"], 12)

    def test_empty_body_and_zero_bounds(self):
        self.body.write_text("\n\t\u00a0", encoding="utf-8")
        code, result = self.run_cli("--min-words", "0", "--max-words", "0")
        self.assertEqual((code, result["word_count"], result["verdict"]), (0, 0, "PASS"))
        code, result = self.run_cli("--min-words", "1")
        self.assertEqual((code, result["verdict"]), (1, "FAIL"))

    def test_invalid_bounds_fail_with_json(self):
        for args in [
            ("--min-words", "-1"), ("--max-words", "-1"),
            ("--min-words", "4", "--max-words", "3"),
            ("--min-words", "1.5"), ("--max-words", "text"),
        ]:
            with self.subTest(args=args):
                code, result = self.run_cli(*args)
                self.assertEqual(code, 2)
                self.assertEqual(result["verdict"], "ERROR")
                self.assertIsNone(result["word_count"])
                self.assertFalse(result["checked_bounds"])

    def test_unreadable_or_malformed_body_fails(self):
        self.body.write_bytes(b"\xff")
        for path in [self.body, self.body.parent, self.body.parent / "missing.md"]:
            with self.subTest(path=path):
                code, result = self.run_cli("--max-words", "10", body=path)
                self.assertEqual((code, result["verdict"]), (2, "ERROR"))
                self.assertIsNone(result["word_count"])

    @unittest.skipUnless(hasattr(os, "mkfifo"), "requires FIFO support")
    def test_special_file_is_rejected_without_reading(self):
        fifo = self.body.parent / "body.fifo"
        os.mkfifo(fifo)
        code, result = self.run_cli(body=fifo)
        self.assertEqual((code, result["verdict"]), (2, "ERROR"))


if __name__ == "__main__":
    unittest.main()
