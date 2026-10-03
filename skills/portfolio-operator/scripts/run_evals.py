#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from portfolio_kernel import (classify_lane, detect_capacity_conflicts, rank_items,
                              render_human_brief, route_delegation, validate_report)


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

    if failures:
        print(f"{len(cases) - len(failures)}/{len(cases)} passed")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print(f"{len(cases)}/{len(cases)} passed")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
