#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from portfolio_kernel import (classify_lane, detect_capacity_conflicts, rank_items,
                              render_human_brief, route_delegation, validate_report,
                              validate_invariants, _urgency)


def completeness_checks() -> list[str]:
    """Exercise complete and partial validation with independent bad inputs."""
    base = {'protocol_version': '1.0', 'as_of': '2026-11-06T10:00:00+01:00',
            'horizon': '14d', 'primary_goal': 'Focus', 'portfolio_scope': ['product'],
            'capacity': {'source': 'unknown'}, 'coverage': {'calendar': 'unavailable'},
            'readiness': {'status': 'PROVISIONAL', 'reason': 'Capacity unknown'}}
    invalid = [
        ('protocol_version', '0', 'protocol_version'), ('as_of', '2026-11-06T10:00:00', 'as_of'),
        ('horizon', '', 'horizon'), ('primary_goal', '', 'primary_goal'),
        ('portfolio_scope', [''], 'portfolio_scope'), ('capacity', {}, 'capacity.source'),
        ('coverage', {}, 'coverage'), ('readiness', [], 'readiness'),
        ('readiness', {'status': 'BAD'}, 'readiness.status'),
        ('readiness', {'status': 'PROVISIONAL'}, 'readiness.reason'),
        ('primary_goal', 'UNKNOWN', 'unknown goal'),
        ('capacity', {'source': 'relative-only', 'hours': 2}, 'relative-only'),
        ('capacity', {'source': 'provided', 'hours': -1}, 'capacity.hours'),
        ('now', 'invalid', 'now must be a list'), ('now', [None], 'now[0] must be an object'),
        ('now', [{'done_when': 'done', 'evidence': ['ref'], 'goal_alignment': 6}], 'goal_alignment'),
        ('now', [{'done_when': 'done', 'evidence': ['ref'], 'days_to_deadline': '3'}], 'days_to_deadline'),
    ]
    failures = []
    for field, value, expected in invalid:
        errors = validate_report({**base, field: value})
        if not any(expected in error for error in errors):
            failures.append(f'completeness: {field}={value!r} did not report {expected}')
    if validate_invariants(None) != ['report must be a JSON object']:
        failures.append('partial validation must reject a non-object')
    if not any('capacity' in error for error in validate_invariants({'capacity': []})):
        failures.append('partial validation must reject non-object capacity')
    valid_action = {'done_when': 'done', 'evidence': [{'source': 'email', 'locator': 'thread'}]}
    if validate_report({**base, 'now': [valid_action]}):
        failures.append('documented object evidence should be accepted')
    try:
        _urgency('3')
    except ValueError:
        pass
    else:
        failures.append('urgency must reject non-integer input')
    return failures


def main() -> int:
    argparse.ArgumentParser(description='Run the bundled Portfolio Operator golden cases.').parse_args()
    cases = json.loads((ROOT / 'evals' / 'golden-cases.json').read_text(encoding='utf-8'))
    failures: list[str] = []
    for case in cases:
        kind = case['kind']
        name = case['name']
        try:
            if 'expected_error' in case:
                # The call must refuse the input with exactly this message.
                func, arg = {'ranking': (rank_items, 'items'),
                             'lane': (classify_lane, 'item'),
                             'delegation': (route_delegation, 'item'),
                             'conflict': (detect_capacity_conflicts, 'items'),
                             'render': (render_human_brief, 'report')}[kind]
                try:
                    func(case[arg])
                except ValueError as exc:
                    actual = str(exc)
                else:
                    actual = None
                expected = case['expected_error']
            elif kind == 'ranking':
                ranked = rank_items(case['items'])
                actual = ranked[0]['id']
                expected = case['expected_first']
                # A score inside one gate class never changes the leader, so a
                # ranking case can also pin every score it produces.
                scores = {str(row.get('id')): row['priority_score'] for row in ranked}
                if 'expected_scores' in case and scores != case['expected_scores']:
                    failures.append(f"{name}: expected scores {case['expected_scores']!r}, got {scores!r}")
                    continue
            elif kind == 'lane':
                actual = classify_lane(case['item'])
                expected = case['expected']
            elif kind == 'delegation':
                actual = route_delegation(case['item'])
                expected = case['expected']
            elif kind == 'conflict':
                actual = len(detect_capacity_conflicts(case['items'], capacity_source=case.get('capacity_source', 'unknown')))
                expected = case['expected_count']
            elif kind == 'validation':
                errors = validate_report(case['report'])
                actual = not errors
                expected = case['expected_valid']
                if 'expected_errors' in case and errors != case['expected_errors']:
                    failures.append(f"{name}: expected errors {case['expected_errors']!r}, got {errors!r}")
                    continue
            elif kind == 'render':
                # The brief is what the user reads. Assert on what must appear and
                # on what must not: portfolio_outcome replacing internal action text
                # is a rule of the skill, and only an absence check can prove it.
                brief = render_human_brief(case['report'])
                actual = (all(s in brief for s in case.get('expected_contains', ()))
                          and not any(s in brief for s in case.get('expected_absent', ())))
                expected = True
            else:
                failures.append(f"{name}: unknown kind {kind}")
                continue
            if actual != expected:
                failures.append(f"{name}: expected {expected!r}, got {actual!r}")
        except Exception as exc:
            failures.append(f"{name}: raised {type(exc).__name__}: {exc}")

    golden_failures = len(failures)
    failures.extend(completeness_checks())

    if failures:
        print(f"{len(cases) - golden_failures}/{len(cases)} golden cases passed; failures below")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print(f"{len(cases)}/{len(cases)} passed")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
