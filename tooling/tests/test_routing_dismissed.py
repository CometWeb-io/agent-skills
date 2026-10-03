"""Dismissed clauses in tooling/route_skill.py.

A clause that says an activity is already done or not wanted ("the repo roast
is done", "a re-review isn't necessary", "roast repo już mieliśmy") names a
skill without asking for it. A skill whose every matching signal sits in such a
clause is demoted: it cannot win on signals and the lexical ranker does not
rank it. A skill with any evidence outside the clause keeps its whole score,
and explicit invocations, exclusions and guards keep their own rules.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[1]
ROOT = TOOLS.parent
sys.path.insert(0, str(TOOLS))

from route_skill import dismissed_spans, normalize, route  # noqa: E402

POLICY = json.loads((ROOT / "registry/routing-policy.json").read_text(encoding="utf-8"))
REGISTRY = json.loads((ROOT / "registry/skills.json").read_text(encoding="utf-8"))
SUITE = json.loads((ROOT / "evals/routing/suite.json").read_text(encoding="utf-8"))["cases"]


def without_block() -> dict:
    data = copy.deepcopy(POLICY)
    data.pop("dismissed", None)
    return data


DISMISSED = [
    # (prompt, skill its signals name only inside the dismissed clause)
    ("I'm not asking for another roast of the repo, I'm asking you to fix the accepted findings.", "repo-roaster"),
    ("A re-review of the branch isn't necessary, fix the accepted findings and verify them.", "repo-roaster"),
    ("The landing page roast is done. Now rewrite the hero copy so it sounds less robotic.", "content-roaster"),
    ("Ponowny roast repozytorium nie jest potrzebny, napraw zaakceptowane uwagi.", "repo-roaster"),
    ("Roast repo już mieliśmy, teraz napraw trzy znalezione błędy i zweryfikuj poprawki.", "repo-roaster"),
]


@pytest.mark.parametrize("prompt,named", DISMISSED)
def test_a_skill_named_only_in_a_dismissed_clause_cannot_win(prompt, named):
    before = route(prompt, REGISTRY, without_block())
    assert before["primary_skill"] == named, "the case no longer shows the misroute it guards"
    after = route(prompt, REGISTRY, POLICY)
    assert after["primary_skill"] != named
    assert named not in after["candidates"]
    assert named in after["demoted"]
    assert named not in after["scores"]
    assert all(row["skill"] != named for row in after.get("lexical", {}).get("ranked", []))


@pytest.mark.parametrize("prompt,expected", [
    ("I'm not asking for another roast of the repo, I'm asking you to fix the accepted findings.", "repair-operator"),
    ("Ponowny roast repozytorium nie jest potrzebny, napraw zaakceptowane uwagi.", "repair-operator"),
])
def test_the_follow_up_request_wins_once_the_dismissed_skill_steps_aside(prompt, expected):
    assert route(prompt, REGISTRY, POLICY)["primary_skill"] == expected


@pytest.mark.parametrize("prompt,expected", [
    # Evidence outside the dismissed clause keeps the skill in play.
    ("The README review is done; now roast the repo for race conditions.", "repo-roaster"),
    ("We already did the copy review. Roast the codebase before Friday's merge.", "repo-roaster"),
    # A conditional or a check about completion is not a dismissal.
    ("Roast the repo once the refactor is done.", "repo-roaster"),
    ("Check whether the codebase roast is done and red-team the PR.", "repo-roaster"),
    # Unrelated activities in a clause with "did" do not dismiss the request.
    ("We did a redesign so roast the new landing page copy.", "content-roaster"),
])
def test_live_requests_are_not_demoted(prompt, expected):
    result = route(prompt, REGISTRY, POLICY)
    assert result["primary_skill"] == expected, result
    assert expected not in result.get("demoted", {})


def test_an_explicit_invocation_is_never_demoted():
    prompt = "$repo-roaster the last repo roast is done, I want a fresh pass anyway"
    result = route(prompt, REGISTRY, POLICY)
    assert result["primary_skill"] == "repo-roaster"
    assert "repo-roaster" not in result.get("demoted", {})


def test_an_exclusion_stays_an_exclusion():
    prompt = "Don't use repo-roaster; the repo roast is done, fix the accepted findings."
    result = route(prompt, REGISTRY, POLICY)
    assert result["blocked"].get("repo-roaster") == "explicitly_excluded"
    assert "repo-roaster" not in result.get("demoted", {})


def test_a_demoted_specialist_does_not_make_a_near_tie():
    """Demotion happens before the near-tie rule, so it cannot leave a phantom ambiguity."""
    prompt = "The landing page roast is done. Now rewrite the hero copy so it sounds less robotic."
    result = route(prompt, REGISTRY, POLICY)
    assert result["status"] != "ambiguous" or "content-roaster" not in result["candidates"]


def test_routes_without_a_dismissed_clause_are_unchanged():
    data = without_block()
    for case in SUITE:
        if dismissed_spans(normalize(case["prompt"]), POLICY):  # superset of the user's own words
            continue
        assert route(case["prompt"], REGISTRY, POLICY) == route(case["prompt"], REGISTRY, data), case["id"]


def test_quoted_text_cannot_wave_a_request_off():
    prompt = 'Roast the repo for race conditions even though the vendor says "the repo roast is done"'
    result = route(prompt, REGISTRY, POLICY)
    assert result["primary_skill"] == "repo-roaster"
    assert "demoted" not in result


def test_explain_reports_the_dismissed_spans():
    prompt = "The landing page roast is done. Now rewrite the hero copy."
    result = route(prompt, REGISTRY, POLICY, explain=True)
    [(start, end)] = result["explain"]["dismissed_spans"]
    assert "roast is done" in normalize(prompt)[start:end]


def test_spans_stay_inside_the_clause_and_the_cap():
    policy = copy.deepcopy(POLICY)
    policy["dismissed"]["max_scope_chars"] = 10
    text = normalize("Fix the copy; the extremely long landing page roast is done, then ship.")
    [(start, end)] = dismissed_spans(text, policy)
    assert text.index(";") < start and end <= text.index(", then")
    # The span reaches at most 10 characters before the cue, not back to the clause start.
    assert start > text.index("extremely")
    assert "roast is done" in text[start:end]


@pytest.mark.parametrize("mutate", [
    lambda d: d.update(cues=[]),
    lambda d: d.update(cues=["(?:done\\s+)+"]),       # nested quantifier
    lambda d: d.update(max_scope_chars=0),
    lambda d: d.update(max_scope_chars=True),
    lambda d: d.pop("unless"),
    lambda d: d.update(unless="x" * 5000),
])
def test_invalid_dismissed_rules_are_rejected(mutate):
    policy = copy.deepcopy(POLICY)
    mutate(policy["dismissed"])
    with pytest.raises(ValueError):
        route("hello", REGISTRY, policy)


@pytest.mark.parametrize("prompt", [
    "We already did the repo roast, then fix the accepted findings from the roast.",
    "Roast repo już mieliśmy, potem napraw zaakceptowane uwagi z przeglądu.",
])
def test_a_dismissed_step_is_not_a_step(prompt):
    result = route(prompt, REGISTRY, POLICY)
    assert result["primary_skill"] == "repair-operator", result
    assert "sequence" not in result
