#!/usr/bin/env python3
"""Evaluate policy admission separately from historical regex-signal fixtures."""
import argparse
import json
from pathlib import Path
from route_skill import ROOT, route


def evaluate(registry: dict, policy: dict, suite: dict) -> dict:
    if not isinstance(suite, dict) or not isinstance(suite.get('cases'), list) or not suite['cases']:
        raise ValueError("empty or malformed policy suite")
    results, seen = [], set()
    for case in suite["cases"]:
        if not isinstance(case, dict) or not isinstance(case.get('id'), str) or not case['id'] or case['id'] in seen:
            raise ValueError("invalid or duplicate eval case ID")
        if not {'expected_status','expected_primary_skill'} & case.keys() and not case.get('must_not_trigger'):
            raise ValueError("case must specify an expectation")
        forbidden = case.get('must_not_trigger', [])
        if not isinstance(forbidden, list) or any(not isinstance(s, str) for s in forbidden):
            raise ValueError("invalid forbidden skill list")
        seen.add(case["id"])
        result = route(case.get("prompt"), registry, policy, invoked=case.get("invoked", []))
        passed = True
        if 'expected_status' in case:
            passed = passed and result['status'] == case['expected_status']
        if 'expected_primary_skill' in case:
            passed = passed and result['primary_skill'] == case['expected_primary_skill']
        for sid in forbidden:
            passed = passed and sid != result["primary_skill"] and sid not in result["candidates"]
        results.append({"id": case["id"], "passed": passed, "actual": result})
    return {"schema": "cometweb.policy-evals/v1", "kind": "deterministic_policy", "passed": sum(r["passed"] for r in results), "total": len(results), "results": results, "runtime_acceptance": "not_assessed"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--suite", type=Path, default=Path('evals/routing/policy-suite.json'))
    args = parser.parse_args()
    read = lambda p: json.loads((args.root / p).read_text())
    report = evaluate(read("registry/skills.json"), read("registry/routing-policy.json"), read(args.suite))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return int(report["passed"] != report["total"])


if __name__ == "__main__":
    raise SystemExit(main())
