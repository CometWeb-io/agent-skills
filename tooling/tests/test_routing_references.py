"""Development regressions for local targets, review sources and short refusals."""
import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tooling"))
from route_skill import route  # noqa: E402

REGISTRY = json.loads((ROOT / "registry/skills.json").read_text())
POLICY = json.loads((ROOT / "registry/routing-policy.json").read_text())


@pytest.mark.parametrize("prompt,steps", [
    ("Fact-check the deck, then roast it, then gate the final version.",
     ["evidence-researcher", "content-reviewer", "artifact-acceptance"]),
    ("Verify the claims in the proposal, then roadmap the work it implies.",
     ["evidence-researcher", "repo-to-roadmap"]),
    ("Fact-check the proposal, then roadmap the resulting work.",
     ["evidence-researcher", "repo-to-roadmap"]),
    ("Zweryfikuj twierdzenia w prezentacji, potem zroastuj ją, następnie odbierz wersję końcową.",
     ["evidence-researcher", "content-reviewer", "artifact-acceptance"]),
    ("Zweryfikuj twierdzenia w ofercie, potem opracuj roadmapę.",
     ["evidence-researcher", "repo-to-roadmap"]),
    ("Fact-check the codebase claims, then roast it, then gate the final version.",
     ["evidence-researcher", "repo-roaster", "release-readiness"]),
    ("Fact-check the manuscript, then roast it.",
     ["evidence-researcher", "science-roaster"]),
    ("Verify the claims in the white paper against original sources, then roast it.",
     ["evidence-researcher", "content-reviewer"]),
    ("Napraw zaakceptowane uwagi, potem zroastuj repo.",
     ["repair-operator", "repo-roaster"]),
    ("Fix the issues from the previous repo roast, then roast the codebase again.",
     ["repair-operator", "repo-roaster"]),
])
def test_local_targets_and_review_inputs_make_distinct_steps(prompt, steps):
    result = route(prompt, REGISTRY, POLICY)
    assert (result["status"], result["primary_skill"]) == ("workflow", "skill-orchestrator"), result
    assert result["sequence"] == steps
    assert result["mode"] == "deterministic_proxy"
    assert result["runtime_acceptance"] == "not_assessed"


@pytest.mark.parametrize("prompt", [
    "Fix the issues from yesterday's repo roast.",
    "Resolve the defects raised by our earlier codebase review.",
    "Address the problems reported by the last repository audit.",
    "Napraw błędy z wczorajszego roastu repo.",
    "Zamknij uwagi po ostatnim audycie repozytorium.",
    "Roast of the codebase? No. Fix the accepted findings.",
    "Roast repozytorium? Nie! Popraw zaakceptowane uwagi.",
    "Roast the repo? Nope. Review the copy? No. Fix the accepted findings.",
])
def test_a_review_source_or_refused_question_does_not_request_a_new_roast(prompt):
    result = route(prompt, REGISTRY, POLICY, explain=True)
    assert (result["status"], result["primary_skill"]) == ("single_skill", "repair-operator"), result
    assert "repo-roaster" not in result["candidates"]
    assert "sequence" not in result
    assert result["explain"]["dismissed_spans"]


@pytest.mark.parametrize("prompt", [
    "Roast it, then gate it.",
    "Explain what a roadmap is, then give an example.",
    "Explain how to roadmap the work.",
    "Do not roadmap the project.",
    "Nie opracuj roadmapy, tylko popraw literówkę.",
    "Do not fix the issues from yesterday's repo roast.",
    "Nie naprawiaj uwag po ostatnim audycie repo.",
    "Roast of the codebase? No.",
    "Roast repo? Nie.",
    "The issues from yesterday's repo roast are in the attached file.",
    "Fix the CSS typo.",
    "Popraw literówkę w przycisku.",
    'The vendor wrote "Fact-check the deck, then roast it, then gate the final version."',
    'The report says "Fix the issues from yesterday\'s repo roast."',
    'The client wrote "Roast repo? No."',
    " " * 4096,
])
def test_unresolved_conceptual_negated_quoted_and_plain_coding_requests_abstain(prompt):
    result = route(prompt, REGISTRY, POLICY)
    assert (result["status"], result["primary_skill"], result["candidates"]) == ("no_skill", None, []), result


@pytest.mark.parametrize("prompt,expected", [
    ("Fact-check the deck, then do not roast it.", "evidence-researcher"),
    ("Zweryfikuj twierdzenia w prezentacji, potem nie zroastuj jej.", "evidence-researcher"),
    ("Roast of the codebase? No problem. Proceed.", "repo-roaster"),
    ("Roast of the codebase? Yes. Do it.", "repo-roaster"),
    ('Roast the repo. The client said "No."', "repo-roaster"),
    ("Fix the accepted findings. Roast the codebase again.", "repo-roaster"),
])
def test_live_positive_requests_remain_live(prompt, expected):
    result = route(prompt, REGISTRY, POLICY)
    assert result["primary_skill"] == expected, result


def test_two_possible_targets_do_not_invent_a_pronoun_owner():
    result = route("Fact-check the deck about the codebase, then roast it.", REGISTRY, POLICY)
    assert result["primary_skill"] == "evidence-researcher", result
    assert "sequence" not in result


@pytest.mark.parametrize("excluded", ["content-reviewer", "skill-orchestrator"])
def test_context_does_not_bypass_explicit_exclusions(excluded):
    result = route(f"Without {excluded}: Fact-check the deck, then roast it.", REGISTRY, POLICY)
    assert result["blocked"][excluded] == "explicitly_excluded"
    assert excluded not in result["candidates"]
    assert result["primary_skill"] != excluded
    if excluded == "content-reviewer":
        assert result["primary_skill"] == "evidence-researcher", result


def test_context_does_not_lower_the_step_score_floor():
    policy = copy.deepcopy(POLICY)
    policy["sequence"]["min_step_score"] = 100
    result = route("Fact-check the deck, then roast it, then gate the final version.", REGISTRY, policy)
    assert "sequence" not in result


def test_host_invocation_remains_authoritative():
    result = route("Fact-check the deck, then roast it.", REGISTRY, POLICY, invoked=("evidence-researcher",))
    assert result["primary_skill"] == "evidence-researcher"
    assert "sequence" not in result


@pytest.mark.parametrize("prompt,expected", [
    ("Choose a journal for this finished manuscript based on scope and acceptance prospects.", None),
    ("Wybierz czasopismo dla gotowego manuskryptu według dopasowania i szans przyjęcia.", None),
    ("Plan the follow-up experiment after the negative results.", "research-program-operator"),
    ("Zaplanuj kolejne badanie po nieudanym eksperymencie.", "research-program-operator"),
])
def test_journal_selection_is_not_research_program_governance(prompt, expected):
    result = route(prompt, REGISTRY, POLICY)
    assert result["primary_skill"] == expected, result
    assert result["status"] == ("no_skill" if expected is None else "single_skill")


def test_journal_choice_label_conflict_stays_visible_without_relabelling():
    from routing_coverage import labelled_prompts

    source = json.loads((ROOT / "skills/science-roaster/evals/trigger-evals.json").read_text())[17]
    assert source == {
        "query": "Decide which journal we should submit to based on fit and acceptance strategy.",
        "should_trigger": False,
        "near_miss": "research-program-operator",
    }
    row = next(r for r in labelled_prompts(REGISTRY, [], root=ROOT)
               if r["source"] == "trigger-evals:science-roaster:17")
    assert row["expected"] == "research-program-operator"
    assert route(row["prompt"], REGISTRY, POLICY)["status"] == "no_skill"
