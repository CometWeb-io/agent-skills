#!/usr/bin/env python3
"""Check supplied exact ratios and their displayed rounding; never evaluate prose."""
from __future__ import annotations

import argparse
from fractions import Fraction
import json
from pathlib import Path
import re
import sys

_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)
from ebook_check import ID, InputError, array, integer, load_json, obj, string

SCHEMA = 'cometweb.ebook-calculations/v1'
MODES = ('nearest_half_even', 'conservative_bounds')
DECIMAL = re.compile(r'-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?\Z')
MAX_INTEGER = 10 ** 1000


def fields(value: object, expected: set[str], where: str) -> dict:
    record = obj(value, where)
    if set(record) != expected:
        raise InputError(f'{where}: expected exactly {sorted(expected)}')
    return record


def ratio(value: object, where: str) -> tuple[dict, Fraction]:
    exact = fields(value, {'numerator', 'denominator', 'unit'}, where)
    numerator = integer(exact['numerator'], f'{where}.numerator')
    denominator = integer(exact['denominator'], f'{where}.denominator')
    if denominator == 0:
        raise InputError(f'{where}: zero denominator')
    if abs(numerator) >= MAX_INTEGER or abs(denominator) >= MAX_INTEGER:
        raise InputError(f'{where}: integers must have at most 1000 decimal digits')
    unit = string(exact['unit'], f'{where}.unit')
    if not unit.strip() or unit != unit.strip():
        raise InputError(f'{where}.unit: nonempty text without surrounding whitespace required')
    return exact, Fraction(numerator, denominator)


def display(value: object, where: str) -> tuple[dict, Fraction]:
    shown = fields(value, {'value', 'precision', 'unit'}, where)
    text = string(shown['value'], f'{where}.value')
    if len(text) > 1102 or not DECIMAL.fullmatch(text):
        raise InputError(f'{where}.value: a finite plain decimal string is required')
    precision = integer(shown['precision'], f'{where}.precision')
    if not 0 <= precision <= 100:
        raise InputError(f'{where}.precision: expected 0..100 decimal places')
    unit = string(shown['unit'], f'{where}.unit')
    if not unit.strip() or unit != unit.strip():
        raise InputError(f'{where}.unit: nonempty text without surrounding whitespace required')
    return shown, Fraction(text)


def rounded(value: Fraction, precision: int, direction: str) -> str:
    scale = 10 ** precision
    quotient, remainder = divmod(value.numerator * scale, value.denominator)
    if direction == 'upper':
        quotient += bool(remainder)
    elif direction == 'nearest_half_even':
        twice = remainder * 2
        quotient += twice > value.denominator or (twice == value.denominator and quotient % 2 != 0)
    elif direction != 'lower':
        raise InputError(f'Unknown rounding direction: {direction}')
    sign = '-' if quotient < 0 else ''
    whole, decimal = divmod(abs(quotient), scale)
    return f'{sign}{whole}.{decimal:0{precision}d}' if precision else f'{sign}{whole}'


def validate(data: object) -> dict:
    manifest = fields(data, {'schema', 'calculations'}, 'manifest')
    if manifest['schema'] != SCHEMA:
        raise InputError(f'Expected schema {SCHEMA}')
    calculations = array(manifest['calculations'], 'calculations')
    if not calculations:
        raise InputError('calculations: at least one record is required')
    checked, blockers, ids = [], [], set()
    for index, raw in enumerate(calculations):
        record = obj(raw, f'calculations[{index}]')
        mode = string(record.get('mode'), f'calculations[{index}].mode')
        if mode not in MODES:
            raise InputError(f'calculations[{index}]: unknown mode {mode!r}')
        endpoints = ('value',) if mode == 'nearest_half_even' else ('lower', 'upper')
        fields(record, {'id', 'mode', *endpoints}, f'calculations[{index}]')
        identity = string(record['id'], f'calculations[{index}].id')
        if not ID.fullmatch(identity) or identity in ids:
            raise InputError(f'calculations[{index}]: invalid or duplicate id')
        ids.add(identity)
        out = {'id': identity, 'mode': mode}
        exact_values, shown_values = {}, {}
        for endpoint in endpoints:
            where = f'{identity}.{endpoint}'
            pair = fields(record[endpoint], {'exact', 'displayed'}, where)
            exact, value = ratio(pair['exact'], f'{where}.exact')
            shown, shown_value = display(pair['displayed'], f'{where}.displayed')
            expected = rounded(value, shown['precision'], mode if len(endpoints) == 1 else endpoint)
            actual_precision = len(shown['value'].partition('.')[2])
            issues = []
            if shown['unit'] != exact['unit']:
                issues.append('unit_mismatch')
            if actual_precision != shown['precision']:
                issues.append('precision_mismatch')
            if shown_value != Fraction(expected):
                issues.append('rounding_mismatch')
            for code in issues:
                blockers.append({'code': code, 'detail': where})
            out[endpoint] = {'exact': exact, 'displayed': shown, 'expected': expected,
                             'reduced': {'numerator': value.numerator, 'denominator': value.denominator},
                             'matches': not issues}
            exact_values[endpoint], shown_values[endpoint] = value, shown_value
        if mode == 'conservative_bounds':
            if exact_values['lower'] > exact_values['upper']:
                raise InputError(f'{identity}: exact lower bound exceeds upper bound')
            lower, upper = out['lower'], out['upper']
            if lower['exact']['unit'] != upper['exact']['unit']:
                raise InputError(f'{identity}: exact bounds require the same unit')
            if lower['displayed']['precision'] != upper['displayed']['precision']:
                raise InputError(f'{identity}: bounds require the same displayed precision')
            if shown_values['lower'] > shown_values['upper']:
                blockers.append({'code': 'reversed_displayed_bounds', 'detail': identity})
        checked.append(out)
    return {'schema': 'cometweb.ebook-calculations-result/v1',
            'result': 'BLOCKED' if blockers else 'CALCULATIONS_MATCH',
            'calculations': checked, 'blockers': blockers,
            'limits': 'Checks supplied ratios, units and displayed decimals only; does not discover calculations, verify operands or unit semantics, parse a manuscript/PDF, or authorize publication.'}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    args = parser.parse_args(argv)
    try:
        result = validate(load_json(args.manifest))
    except (InputError, ValueError, OSError, RecursionError) as exc:
        print(json.dumps({'result': 'INPUT_ERROR', 'error': str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 0 if result['result'] == 'CALCULATIONS_MATCH' else 1


if __name__ == '__main__':
    sys.exit(main())
