"""Suites a model runs, not a kernel — so the repository checks their shape.

test_skill_eval_harnesses.py runs the harnesses three skills ship. These two
files have no harness: they are prompts plus the behaviour a model using the skill should
show, and a person or an agent grades them. Nothing read them, so nothing would
have noticed that one spelled the expectation key `expect` and the other
`expected` — a grader written against one suite would silently find no
expectations in the other and report every case as passing.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

SUITES = (
    "skills/competitive-intelligence/evals/evals.json",
    "skills/design-partner-finder/evals/evals.json",
)


def load(relative: str) -> list[dict]:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


@pytest.mark.parametrize("relative", SUITES)
def test_suite_is_a_non_empty_list_of_cases(relative: str) -> None:
    cases = load(relative)
    assert isinstance(cases, list) and cases, f"{relative} holds no cases"
    for case in cases:
        assert isinstance(case, dict), f"{relative}: case is {type(case).__name__}, not an object"


@pytest.mark.parametrize("relative", SUITES)
def test_every_case_carries_a_prompt_and_expectations(relative: str) -> None:
    for case in load(relative):
        name = case.get("name")
        assert isinstance(name, str) and name.strip(), f"{relative}: a case has no name"
        prompt = case.get("prompt")
        assert isinstance(prompt, str) and prompt.strip(), f"{relative}/{name}: no prompt"
        expect = case.get("expect")
        assert isinstance(expect, list) and expect, (
            f"{relative}/{name}: `expect` must be a non-empty list. A case with nothing "
            f"to check reads as a pass to whoever grades it."
        )
        for line in expect:
            assert isinstance(line, str) and line.strip(), f"{relative}/{name}: empty expectation"


@pytest.mark.parametrize("relative", SUITES)
def test_case_names_are_unique(relative: str) -> None:
    names = [case["name"] for case in load(relative)]
    duplicates = sorted({n for n in names if names.count(n) > 1})
    assert not duplicates, f"{relative}: duplicate case names {duplicates}"


def test_both_suites_use_the_same_expectation_key() -> None:
    """The drift this file exists to stop."""
    keys = set()
    for relative in SUITES:
        for case in load(relative):
            keys |= set(case)
    assert keys == {"name", "prompt", "expect"}, (
        f"model-in-the-loop suites disagree on their shape: {sorted(keys)}. "
        f"One grader has to read both."
    )
