"""Synthetic arithmetic and CLI regressions; not ebook or model qualification."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

PKG = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG / 'scripts'))
SPEC = importlib.util.spec_from_file_location('ebook_calculations', PKG / 'scripts/check_calculations.py')
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def endpoint(numerator=1, denominator=3, value='0.33', precision=2, unit='ratio'):
    return {'exact': {'numerator': numerator, 'denominator': denominator, 'unit': unit},
            'displayed': {'value': value, 'precision': precision, 'unit': unit}}


def manifest(value=None):
    return {'schema': mod.SCHEMA, 'calculations': [
        {'id': 'C1', 'mode': 'nearest_half_even', 'value': value or endpoint()}]}


def bounds(lower=None, upper=None):
    return {'schema': mod.SCHEMA, 'calculations': [
        {'id': 'B1', 'mode': 'conservative_bounds',
         'lower': lower or endpoint(), 'upper': upper or endpoint(2, 3, '0.67')}]}


class CalculationTests(unittest.TestCase):
    def assertMatches(self, data):
        self.assertEqual(mod.validate(data)['result'], 'CALCULATIONS_MATCH')

    def assertBlocked(self, data, code='rounding_mismatch'):
        result = mod.validate(data)
        self.assertEqual(result['result'], 'BLOCKED')
        self.assertIn(code, [x['code'] for x in result['blockers']])

    def test_terminating_and_repeating_decimals(self):
        for n, d, text in [(1, 3, '0.33'), (1, 8, '0.12'), (1, 4, '0.25'), (2, 3, '0.67')]:
            with self.subTest(text=text): self.assertMatches(manifest(endpoint(n, d, text)))

    def test_ties_are_half_even_in_both_directions(self):
        for n, d, text in [(1, 8, '0.12'), (3, 8, '0.38'), (-1, 8, '-0.12'), (-3, 8, '-0.38')]:
            with self.subTest(n=n): self.assertMatches(manifest(endpoint(n, d, text)))
        self.assertBlocked(manifest(endpoint(1, 8, '0.13')))

    def test_integer_precision_and_negative_denominator(self):
        self.assertMatches(manifest(endpoint(-5, 2, '-2', 0)))
        self.assertMatches(manifest(endpoint(1, -3, '-0.33')))

    def test_exact_expression_is_retained_without_mutation(self):
        data = manifest(endpoint(10, -30, '-0.33'))
        before = copy.deepcopy(data)
        result = mod.validate(data)['calculations'][0]['value']
        self.assertEqual(result['exact'], before['calculations'][0]['value']['exact'])
        self.assertEqual(result['reduced'], {'numerator': -1, 'denominator': 3})
        self.assertEqual(result['expected'], '-0.33')
        self.assertEqual(data, before)

    def test_conservative_bounds(self): self.assertMatches(bounds())

    def test_negative_bounds_round_toward_infinities(self):
        self.assertMatches(bounds(endpoint(-2, 3, '-0.67'), endpoint(-1, 3, '-0.33')))

    def test_equal_exact_bounds_and_terminating_bounds(self):
        self.assertMatches(bounds(endpoint(1, 3, '0.33'), endpoint(1, 3, '0.34')))
        self.assertMatches(bounds(endpoint(1, 4, '0.25'), endpoint(1, 4, '0.25')))

    def test_normal_rounding_can_be_inward_for_conservative_endpoint(self):
        self.assertMatches(manifest(endpoint(1, 6, '0.17')))
        self.assertBlocked(bounds(endpoint(1, 6, '0.17')))
        self.assertMatches(manifest(endpoint(1, 3, '0.33')))
        self.assertBlocked(bounds(upper=endpoint(1, 3, '0.33')))

    def test_outward_ties_differ_from_half_even(self):
        self.assertMatches(bounds(endpoint(1, 8, '0.12'), endpoint(1, 8, '0.13')))
        self.assertMatches(bounds(endpoint(-1, 8, '-0.13'), endpoint(-1, 8, '-0.12')))

    def test_rounding_is_exact_even_beyond_decimal_context_precision(self):
        denominator = 10 ** 100
        self.assertMatches(bounds(endpoint(denominator - 1, denominator, '0.99'),
                                  endpoint(denominator + 1, denominator, '1.01')))
        self.assertBlocked(bounds(endpoint(denominator - 1, denominator, '1.00'),
                                  endpoint(denominator + 1, denominator, '1.01')))

    def test_actual_value_is_compared(self): self.assertBlocked(manifest(endpoint(value='99.33')))

    def test_displayed_precision_is_compared(self):
        self.assertBlocked(manifest(endpoint(1, 2, '0.5')), 'precision_mismatch')

    def test_actual_unit_is_compared(self):
        data = manifest()
        data['calculations'][0]['value']['displayed']['unit'] = '%'
        self.assertBlocked(data, 'unit_mismatch')

    def test_empty_and_unknown_structure(self):
        for data in [[], {}, {'schema': mod.SCHEMA, 'calculations': []},
                     {'schema': 'unknown', 'calculations': []},
                     {'schema': mod.SCHEMA, 'calculations': 'bad'}]:
            with self.subTest(data=data), self.assertRaises(mod.InputError): mod.validate(data)

    def test_malformed_values_are_input_errors(self):
        cases = [('exact', 'numerator', True), ('exact', 'numerator', 0.3),
                 ('exact', 'numerator', '1'), ('exact', 'denominator', 0),
                 ('exact', 'denominator', None), ('exact', 'unit', ''),
                 ('displayed', 'value', 0.33), ('displayed', 'value', 'NaN'),
                 ('displayed', 'value', 'Infinity'), ('displayed', 'value', '1e-2'),
                 ('displayed', 'value', ' 0.33'), ('displayed', 'value', '00.33'),
                 ('displayed', 'precision', True), ('displayed', 'precision', -1),
                 ('displayed', 'precision', 101), ('displayed', 'precision', 2.0),
                 ('displayed', 'unit', []), ('displayed', 'unit', ' ratio '),
                 ('exact', 'numerator', 10 ** 1000)]
        for part, key, bad in cases:
            data = manifest()
            data['calculations'][0]['value'][part][key] = bad
            with self.subTest(part=part, key=key, bad=bad), self.assertRaises(mod.InputError):
                mod.validate(data)

    def test_unknown_modes_and_extra_fields(self):
        for change in [{'mode': 'round'}, {'mode': []}, {'id': 'bad id'}, {'expression': '1/3'}]:
            data = manifest(); data['calculations'][0].update(change)
            with self.subTest(change=change), self.assertRaises(mod.InputError): mod.validate(data)
        with self.assertRaises(mod.InputError):
            mod.rounded(mod.Fraction(1, 3), 2, 'unknown')

    def test_duplicate_ids_rejected(self):
        data = manifest(); data['calculations'] *= 2
        with self.assertRaises(mod.InputError): mod.validate(data)

    def test_reversed_exact_bounds_and_incompatible_units_rejected(self):
        for data in [bounds(endpoint(2, 3, '0.66'), endpoint(1, 3, '0.34')),
                     bounds(upper=endpoint(2, 3, '0.67', unit='%')),
                     bounds(upper=endpoint(2, 3, '0.7', precision=1))]:
            with self.subTest(data=data), self.assertRaises(mod.InputError): mod.validate(data)

    def test_reversed_displayed_bounds_are_a_failed_comparison(self):
        self.assertBlocked(bounds(endpoint(value='0.80'), endpoint(2, 3, '0.20')),
                           'reversed_displayed_bounds')

    def test_large_precision_and_zero(self):
        self.assertMatches(manifest(endpoint(1, 3, '0.' + '3' * 100, 100)))
        self.assertMatches(bounds(endpoint(0, 7, '-0.00'), endpoint(0, 9, '0.00')))


class CliTests(unittest.TestCase):
    def run_cli(self, raw):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'numbers.json'
            path.write_text(raw, encoding='utf-8')
            return subprocess.run([sys.executable, str(PKG / 'scripts/check_calculations.py'), str(path)],
                                  capture_output=True, text=True)

    def test_pass_and_fail_exit_codes(self):
        for data, status in [(manifest(), 0), (manifest(endpoint(value='0.34')), 1)]:
            result = self.run_cli(json.dumps(data))
            self.assertEqual(result.returncode, status, result.stdout + result.stderr)
            self.assertEqual(json.loads(result.stdout)['result'],
                             'CALCULATIONS_MATCH' if status == 0 else 'BLOCKED')

    def test_bad_json_is_error_without_traceback(self):
        for raw in ['{', '[]', '{"schema":1,"schema":2}', '{"x":NaN}', '{"x":Infinity}',
                    '{"x":' + '9' * 5000 + '}', json.dumps(manifest(endpoint(1, 0)))]:
            with self.subTest(raw=raw[:80]):
                result = self.run_cli(raw)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertEqual(json.loads(result.stdout)['result'], 'INPUT_ERROR')
                self.assertNotIn('Traceback', result.stderr)

    def test_missing_file_and_arguments(self):
        command = [sys.executable, str(PKG / 'scripts/check_calculations.py')]
        result = subprocess.run(command + ['/no-such-ebook-numbers.json'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)['result'], 'INPUT_ERROR')
        for args in [[], ['--unknown']]:
            result = subprocess.run(command + args, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn('Traceback', result.stderr)

    def test_directory_and_invalid_utf8(self):
        command = [sys.executable, str(PKG / 'scripts/check_calculations.py')]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'invalid.json'
            path.write_bytes(b'\xff')
            for target in [tmp, str(path)]:
                result = subprocess.run(command + [target], capture_output=True, text=True, timeout=5)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(json.loads(result.stdout)['result'], 'INPUT_ERROR')

    def test_unreadable_file(self):
        with patch('ebook_check.os.open', side_effect=PermissionError('unreadable')):
            with self.assertRaises(mod.InputError): mod.load_json(Path('unreadable.json'))

    @unittest.skipUnless(hasattr(os, 'mkfifo'), 'POSIX FIFO required')
    def test_special_files_do_not_block_either_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            fifo = Path(tmp) / 'numbers.json'
            os.mkfifo(fifo)
            commands = [
                [sys.executable, str(PKG / 'scripts/check_calculations.py')],
                [sys.executable, str(PKG / 'scripts/ebook_check.py'), 'validate'],
            ]
            for prefix in commands:
                for path in [fifo, Path('/dev/null')]:
                    args = prefix + [str(path)]
                    if 'validate' in prefix: args += ['--stage', 'research']
                    result = subprocess.run(args, capture_output=True, text=True, timeout=5)
                    self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                    self.assertEqual(json.loads(result.stdout)['result'], 'INPUT_ERROR')
                    self.assertNotIn('Traceback', result.stderr)

    def test_symlink_to_regular_file_still_supported(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'numbers.json'
            path.write_text(json.dumps(manifest()), encoding='utf-8')
            link = Path(tmp) / 'link.json'
            link.symlink_to(path)
            result = subprocess.run([sys.executable, str(PKG / 'scripts/check_calculations.py'), str(link)],
                                    capture_output=True, text=True, timeout=5)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
