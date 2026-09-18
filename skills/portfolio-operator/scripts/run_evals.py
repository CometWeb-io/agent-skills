#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from portfolio_kernel import (classify_lane, detect_capacity_conflicts, rank_items,
                              render_human_brief, route_delegation, validate_report)


def main() -> int:
    cases = json.loads((ROOT / 'evals' / 'golden-cases.json').read_text(encoding='utf-8'))
    failures: list[str] = []
    for case in cases:
        kind = case['kind']
        name = case['name']
        try:
            if kind == 'ranking':
                actual = rank_items(case['items'])[0]['id']
                expected = case['expected_first']
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
                actual = not validate_report(case['report'])
                expected = case['expected_valid']
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
