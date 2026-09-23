#!/usr/bin/env python3
"""Deterministic routing evals against the canonical route_skill implementation."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "evals" / "routing" / "suite.json"
REGISTRY = ROOT / "registry" / "skills.json"
POLICY = ROOT / "registry" / "routing-policy.json"

sys.path.insert(0, str(ROOT / "tooling"))
from route_skill import route  # noqa: E402


def load_signals() -> dict[str, list[tuple[int, str]]]:
    """Registry signal inventory for tests; scoring itself uses route_skill."""
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    signals: dict[str, list[tuple[int, str]]] = {}
    for skill in data["skills"]:
        sid = skill["id"]
        raw = skill.get("routing_signals") or []
        if not raw and not skill.get("alias_of"):
            raise AssertionError(f"{sid}: registry.routing_signals is empty (no soft fallback)")
        signals[sid] = [(int(weight), str(pattern)) for weight, pattern in raw]
    return signals


SIGNALS = load_signals()


def route_result(prompt: str) -> dict:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    return route(prompt, registry, policy)


def score_prompt(prompt: str) -> dict[str, int]:
    return route_result(prompt)["scores"]


def classify(prompt: str) -> str | None:
    return route_result(prompt)["primary_skill"]


def load_suite() -> dict:
    data = json.loads(SUITE.read_text(encoding="utf-8"))
    if "cases" not in data or not isinstance(data["cases"], list):
        raise AssertionError("suite.json must contain cases[]")
    return data


def validate_case(case: dict, index: int) -> None:
    required = ("id", "prompt", "expected_primary_skill", "must_not_trigger", "reason")
    for key in required:
        if key not in case:
            raise AssertionError(f"case[{index}] missing {key}")


def main() -> int:
    global SIGNALS
    SIGNALS = load_signals()
    data = load_suite()
    known = set(SIGNALS)
    failures: list[str] = []
    for index, case in enumerate(data["cases"]):
        validate_case(case, index)
        expected = case["expected_primary_skill"]
        if expected is not None and expected not in known:
            failures.append(f"{case['id']}: unknown expected skill {expected!r}")
            continue
        result = route_result(case["prompt"])
        predicted = result["primary_skill"]
        if predicted != expected:
            failures.append(
                f"{case['id']}: expected {expected}, got {predicted!r} "
                f"(status={result['status']}, candidates={result['candidates']}, "
                f"scores={result['scores']}) — {case['reason']}"
            )
        for blocked in case["must_not_trigger"]:
            if predicted == blocked or blocked in result["candidates"]:
                failures.append(
                    f"{case['id']}: must_not_trigger {blocked} but appeared "
                    f"(primary={predicted!r}, candidates={result['candidates']}) — {case['reason']}"
                )

    if failures:
        for line in failures:
            print(f"FAIL: {line}", file=sys.stderr)
        print(f"\n{len(failures)} routing eval failure(s)", file=sys.stderr)
        return 1

    print(f"OK: {len(data['cases'])} routing eval cases passed (canonical route_skill)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
