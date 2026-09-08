#!/usr/bin/env python3
"""Deterministic routing eval proxy — signals loaded from registry/skills.json only."""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "evals" / "routing" / "suite.json"
REGISTRY = ROOT / "registry" / "skills.json"


def load_signals() -> dict[str, list[tuple[int, str]]]:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    signals: dict[str, list[tuple[int, str]]] = {}
    for skill in data["skills"]:
        sid = skill["id"]
        raw = skill.get("routing_signals") or []
        if not raw and skill.get("trigger_examples"):
            raw = [[10, re.escape(ex.casefold()[:64])] for ex in skill["trigger_examples"][:5]]
        signals[sid] = [(int(weight), str(pattern)) for weight, pattern in raw]
    return signals


SIGNALS = load_signals()


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def score_prompt(prompt: str) -> dict[str, int]:
    text = normalize(prompt)
    scores: dict[str, int] = {}
    for skill, patterns in SIGNALS.items():
        total = 0
        for weight, pattern in patterns:
            if re.search(pattern, text, re.I):
                total += weight
        if total:
            scores[skill] = total
    return scores


def classify(prompt: str) -> str | None:
    scores = score_prompt(prompt)
    if not scores:
        return None
    return max(scores, key=scores.get)


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
    # Reload in case registry changed since import
    global SIGNALS
    SIGNALS = load_signals()
    data = load_suite()
    known = set(SIGNALS)
    failures: list[str] = []
    for index, case in enumerate(data["cases"]):
        validate_case(case, index)
        expected = case["expected_primary_skill"]
        if expected not in known:
            failures.append(f"{case['id']}: unknown expected skill {expected!r}")
            continue
        predicted = classify(case["prompt"])
        if predicted != expected:
            scores = score_prompt(case["prompt"])
            failures.append(
                f"{case['id']}: expected {expected}, got {predicted!r} "
                f"(scores={scores}) — {case['reason']}"
            )
        for blocked in case["must_not_trigger"]:
            if predicted == blocked:
                failures.append(
                    f"{case['id']}: must_not_trigger {blocked} but was primary — {case['reason']}"
                )

    if failures:
        for line in failures:
            print(f"FAIL: {line}", file=sys.stderr)
        print(f"\n{len(failures)} routing eval failure(s)", file=sys.stderr)
        return 1

    print(f"OK: {len(data['cases'])} routing eval cases passed (signals from registry)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
