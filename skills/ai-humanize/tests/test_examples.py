from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
DEEP_FILES = sorted((ROOT / "examples").glob("*-deep*.md"))

PROHIBITED_OUTPUT_PATTERNS = [
    re.compile(r"\bIt's not about\b", re.I),
    re.compile(r"\bThis isn't\b", re.I),
    re.compile(r"\bTo nie abstrakcyjna\b", re.I),
    re.compile(r"\bW dzisiejszym dynamicznie\b", re.I),
    re.compile(r"\bIn today's rapidly\b", re.I),
]


class ExampleTests(unittest.TestCase):
    def test_deep_examples_have_before_and_after(self):
        self.assertTrue(DEEP_FILES)
        for path in DEEP_FILES:
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                self.assertRegex(text, r"(?m)^## (Before|Przed)")
                self.assertRegex(text, r"(?m)^## (After|Po) \(deep\)")

    def test_deep_outputs_do_not_reintroduce_signature_patterns(self):
        for path in DEEP_FILES:
            text = path.read_text(encoding="utf-8")
            split = re.split(r"(?m)^## (?:After|Po) \(deep\)\s*$", text, maxsplit=1)
            self.assertEqual(len(split), 2, path.name)
            output = re.split(r"(?m)^## ", split[1], maxsplit=1)[0]
            with self.subTest(path=path.name):
                for pattern in PROHIBITED_OUTPUT_PATTERNS:
                    self.assertIsNone(pattern.search(output), pattern.pattern)


if __name__ == "__main__":
    unittest.main()
