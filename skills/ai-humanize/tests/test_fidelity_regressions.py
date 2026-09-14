"""Regression cases for numeric sign/threshold preservation, using the actual guard."""
from pathlib import Path
import importlib.util
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('candidate_fidelity_guard', ROOT / 'scripts/rewrite_guard.py')
GUARD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GUARD)


class NumericFidelityTests(unittest.TestCase):
    pass


DRIFT = [
    ('unicode_negative', 'Wynik to −5.', 'Wynik to 5.'),
    ('unicode_polarity', 'Wynik to −5.', 'Wynik to +5.'),
    ('signed_unit', 'Wynik to −5 ms.', 'Wynik to 5 ms.'),
    ('signed_currency', 'Saldo: −5 EUR.', 'Saldo: 5 EUR.'),
    ('less_to_more', 'Limit: x < 10.', 'Limit: x > 10.'),
    ('less_equal_to_more_equal', 'Limit: x ≤ 10.', 'Limit: x ≥ 10.'),
    ('inclusive_to_exclusive', 'Limit: x ≤ 10.', 'Limit: x < 10.'),
    ('ascii_inclusive', 'Limit: x <= 10.', 'Limit: x >= 10.'),
    ('equality', 'Warunek: x = 10.', 'Warunek: x != 10.'),
    ('unicode_not_equal', 'Warunek: x ≠ 10.', 'Warunek: x = 10.'),
    ('no_spacing', 'Warunek: x<10.', 'Warunek: x>10.'),
    ('negative_threshold', 'Limit: x ≥ −5.', 'Limit: x ≥ 5.'),
    ('decimal_threshold', 'Limit: x ≤ 1.5.', 'Limit: x ≥ 1.5.'),
    ('comma_threshold', 'Limit: x ≤ 1,5.', 'Limit: x ≥ 1,5.'),
    ('deleted_comparison', 'Limit: x <= 10.', 'Limit: x 10.'),
]
EQUIVALENT = [
    ('signed_number_glyph', 'Wynik to −5.', 'Wynik to -5.'),
    ('signed_unit_glyph', 'Wynik to −5 ms.', 'Wynik to -5 ms.'),
    ('signed_currency_glyph', 'Saldo: −5 EUR.', 'Saldo: -5 EUR.'),
    ('less_equal_glyph', 'Limit: x ≤ 10.', 'Limit: x <= 10.'),
    ('more_equal_glyph', 'Limit: x ≥ 10.', 'Limit: x >= 10.'),
    ('not_equal_glyph', 'Warunek: x ≠ 10.', 'Warunek: x != 10.'),
    ('comparison_spacing', 'Warunek: x < 10.', 'Warunek: x<10.'),
]

def make_case(before, after, expected):
    def test(self):
        result = GUARD.compare(before, after, strict=True)
        self.assertEqual(result['passed'], expected, result)
    return test

for name, before, after in DRIFT:
    setattr(NumericFidelityTests, 'test_reject_' + name, make_case(before, after, False))
for name, before, after in EQUIVALENT:
    setattr(NumericFidelityTests, 'test_allow_' + name, make_case(before, after, True))


class NumericBoundaryTests(unittest.TestCase):
    def test_quote_remains_exact(self):
        self.assertFalse(GUARD.compare('„−5”', '„-5”', strict=True)['passed'])

    def test_inline_code_remains_exact(self):
        self.assertFalse(GUARD.compare('`−5`', '`-5`', strict=True)['passed'])

    def test_url_remains_exact(self):
        self.assertFalse(GUARD.compare('https://example.com/−5', 'https://example.com/-5', strict=True)['passed'])

    def test_arrow_is_not_a_numeric_threshold(self):
        self.assertFalse(GUARD.extract('Przejdź -> 10 wyników.')['numeric_constraints'])

    def test_blockquote_prefix_is_not_a_numeric_threshold(self):
        self.assertFalse(GUARD.extract('> 10 wyników.')['numeric_constraints'])

    def test_actual_comparison_inside_blockquote_is_checked(self):
        self.assertFalse(GUARD.compare('> limit: x < 10', '> limit: x > 10', strict=True)['passed'])

    def test_semantic_warning_does_not_claim_semantic_proof(self):
        result = GUARD.compare('Funkcja nie działa.', 'Funkcja działa.', strict=True)
        self.assertTrue(result['passed'])  # backward-compatible hard-invariant meaning
        self.assertIn('negation', result['semantic_risk_markers'])

    def test_bad_utf8_is_a_controlled_cli_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            before, after = Path(tmp)/'before.txt', Path(tmp)/'after.txt'
            before.write_bytes(b'\xff'); after.write_text('valid')
            proc = subprocess.run([sys.executable, str(ROOT/'scripts/rewrite_guard.py'), str(before), str(after)], capture_output=True, text=True, timeout=5)
            self.assertEqual(proc.returncode, 2)
            self.assertNotIn('Traceback', proc.stderr)


if __name__ == '__main__':
    unittest.main()
