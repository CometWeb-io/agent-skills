"""Routing-suite coverage floors, hollow-case detection and pinned known gaps."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tooling"))
import routing_coverage as cov  # noqa: E402
import run_routing_evals  # noqa: E402
from run_blind_eval_harness import fingerprint  # noqa: E402
from run_policy_evals import evaluate  # noqa: E402

REGISTRY = json.loads((ROOT / "registry/skills.json").read_text(encoding="utf-8"))
POLICY = json.loads((ROOT / "registry/routing-policy.json").read_text(encoding="utf-8"))
SUITE = json.loads((ROOT / "evals/routing/suite.json").read_text(encoding="utf-8"))
GAPS = json.loads((ROOT / "evals/routing/known-gaps.json").read_text(encoding="utf-8"))


def _case(**overrides):
    case = {"id": "c1", "prompt": "Explain two plus two.", "expected_primary_skill": None,
            "allowed_secondary_skills": [], "must_not_trigger": [], "reason": "test"}
    case.update(overrides)
    return case


def test_live_suite_is_clean_and_every_active_skill_meets_the_floor():
    data = cov.report()
    assert data["problems"] == [], data["problems"]
    active = {s["id"] for s in REGISTRY["skills"] if s.get("lifecycle") == "active"}
    assert {row["id"] for row in data["skills"]} == active


def test_check_exits_zero_on_the_live_suite(capsys):
    assert cov.main(["--check"]) == 0
    assert "OK: routing coverage" in capsys.readouterr().out


@pytest.mark.parametrize("cases,needle", [
    ([_case(), _case(prompt="Something else")], "duplicate case id"),
    ([_case(), _case(id="c2", prompt="  EXPLAIN two-plus-two!! ")], "duplicates c1 after normalization"),
    ([_case(must_not_trigger=["repo-roastr"])], "unknown skill 'repo-roastr'"),
    ([_case(allowed_secondary_skills=["nope"])], "unknown skill 'nope'"),
    ([_case(expected_primary_skill="nope")], "unknown expected skill"),
    ([_case(expected_primary_skill="repo-roaster", must_not_trigger=["repo-roaster"])], "expects repo-roaster and forbids it"),
    ([_case(must_not_trigger=["repo-roaster", "repo-roaster"])], "repeats a skill"),
    ([_case(must_not_trigger="repo-roaster")], "must be a list"),
    ([_case(prompt="")], "prompt must be a non-empty string"),
    ([_case(id="")], "id must be a non-empty string"),
    (["not-an-object"], "case must be an object"),
    ([], "non-empty list"),
])
def test_structural_defects_are_reported(cases, needle):
    problems = cov.structural_problems(cases, REGISTRY)
    assert any(needle in p for p in problems), problems


def test_a_copied_registry_example_is_rejected():
    example = next(s for s in REGISTRY["skills"] if s["id"] == "repo-roaster")["trigger_examples"][0]
    problems = cov.structural_problems([_case(prompt=example.upper() + "!")], REGISTRY)
    assert any("copies registry repo-roaster.trigger_examples" in p for p in problems), problems


def test_floor_misses_name_the_skill_and_the_shortfall():
    rows = [{"id": "a", "positive": 3, "negative": 2}, {"id": "b", "positive": 2, "negative": 1}]
    assert cov.floor_problems(rows) == [
        "b: 2 positive routing case(s) < 3", "b: forbidden in 1 case(s) < 2"]


def test_coverage_splits_boundary_from_out_of_scope_negatives():
    cases = [_case(id="x", expected_primary_skill="content-roaster", must_not_trigger=["repo-roaster"]),
             _case(id="y", prompt="Roast me in a toast.", must_not_trigger=["repo-roaster"])]
    row = next(r for r in cov.coverage(cases, REGISTRY) if r["id"] == "repo-roaster")
    assert (row["positive"], row["negative"], row["boundary"], row["out_of_scope"]) == (0, 2, 1, 1)


def test_near_duplicates_are_paired_but_distinct_prompts_are_not():
    cases = [_case(id="a", prompt="Roast this codebase for retry bugs"),
             _case(id="b", prompt="Roast this codebase for retry bugs now"),
             _case(id="c", prompt="Plan my next 30 days")]
    assert cov.near_duplicates(cases) == [("a", "b", 0.86)]


def test_runner_fails_a_suite_with_hollow_cases(tmp_path, monkeypatch, capsys):
    broken = deepcopy(SUITE)
    broken["cases"].append(deepcopy(broken["cases"][0]))
    path = tmp_path / "suite.json"
    path.write_text(json.dumps(broken), encoding="utf-8")
    monkeypatch.setattr(run_routing_evals, "SUITE", path)
    assert run_routing_evals.main() == 1
    assert "duplicate case id" in capsys.readouterr().err


# Known gaps: pinned misroutes, so a routing fix announces itself.

def test_every_known_gap_still_reproduces():
    assert GAPS["cases"], "known-gaps.json should not be emptied silently"
    assert cov.gap_problems(GAPS, SUITE["cases"], REGISTRY, POLICY) == []


def test_a_fixed_gap_must_be_promoted():
    gaps = deepcopy(GAPS)
    gaps["cases"] = [dict(id="fixed", prompt="Run AI Council on this decision.",
                          expected_primary_skill="ai-council", must_not_trigger=[],
                          observed_primary_skill=None, observed_status="no_skill", reason="r")]
    problems = cov.gap_problems(gaps, [], REGISTRY, POLICY)
    assert any("promote it to suite.json" in p for p in problems), problems


def test_a_changed_misroute_must_be_rerecorded():
    gaps = deepcopy(GAPS)
    gaps["cases"] = [dict(gaps["cases"][0], observed_primary_skill="repo-roaster")]
    problems = cov.gap_problems(gaps, [], REGISTRY, POLICY)
    assert any("re-record it" in p for p in problems), problems


@pytest.mark.parametrize("mutation,needle", [
    (lambda g: g.update(schema="other"), "schema must be"),
    (lambda g: g["cases"][0].pop("reason"), "reason is required"),
    (lambda g: g["cases"][0].pop("observed_primary_skill"), "observed_primary_skill is required"),
    (lambda g: g["cases"][0].update(observed_primary_skill=g["cases"][0]["expected_primary_skill"]),
     "not a gap"),
])
def test_malformed_gaps_are_rejected(mutation, needle):
    gaps = deepcopy(GAPS)
    mutation(gaps)
    problems = cov.gap_problems(gaps, SUITE["cases"], REGISTRY, POLICY)
    assert any(needle in p for p in problems), problems


def test_a_gap_cannot_also_live_in_the_suite():
    suite_cases = [_case(prompt=GAPS["cases"][0]["prompt"])]
    problems = cov.gap_problems(GAPS, suite_cases, REGISTRY, POLICY)
    assert any("also in suite.json" in p for p in problems), problems


def test_trigger_eval_proxy_accounts_for_every_row():
    rows = {r["id"]: r for r in cov.trigger_eval_proxy(REGISTRY, POLICY)}
    for sid in ("content-roaster", "repo-roaster", "science-roaster"):
        data = json.loads((ROOT / "skills" / sid / "evals/trigger-evals.json").read_text(encoding="utf-8"))
        row = rows[sid]
        assert row["should_trigger"] == sum(r["should_trigger"] is True for r in data)
        assert row["should_not_trigger"] == sum(r["should_trigger"] is False for r in data)
        assert row["rejected"] + row["false_positive"] == row["should_not_trigger"]


def test_trigger_eval_floors_hold_and_are_attainable():
    rows = cov.trigger_eval_proxy(REGISTRY, POLICY)
    assert cov.trigger_eval_floor_problems(rows) == []
    by_id = {r["id"]: r for r in rows}
    for sid, floor in cov.TRIGGER_EVAL_FLOORS.items():
        row = by_id[sid]
        assert set(floor) <= {"recall", "rejected", "near_miss"}
        assert floor["recall"] <= row["should_trigger"]
        assert floor["rejected"] <= row["should_not_trigger"]
        assert floor["near_miss"] <= row["near_miss"]


def test_a_trigger_eval_floor_miss_names_the_skill_and_the_metric():
    rows = [{"id": "content-roaster", "recall": 3, "should_trigger": 18, "rejected": 18,
             "should_not_trigger": 18, "near_miss_routed": 7, "near_miss": 10}]
    problems = cov.trigger_eval_floor_problems(rows, {"content-roaster": {"recall": 14, "rejected": 18}})
    assert problems == ["trigger-evals content-roaster: recall 3/18 < floor 14"]
    missing = cov.trigger_eval_floor_problems([], {"repo-roaster": {"recall": 1}})
    assert missing and "no evals/trigger-evals.json" in missing[0]


@pytest.mark.parametrize("sid", sorted(cov.TRIGGER_EVAL_FLOORS))
def test_dropping_a_roasters_signals_fails_its_recall_floor(sid):
    registry = deepcopy(REGISTRY)
    for skill in registry["skills"]:
        if skill["id"] == sid:
            skill["routing_signals"] = skill["routing_signals"][:1]
    problems = cov.trigger_eval_floor_problems(cov.trigger_eval_proxy(registry, POLICY))
    assert any(p.startswith(f"trigger-evals {sid}: recall") for p in problems), problems


# The policy suite is unit-tested against a toy registry; it must also hold on the real one.

def test_policy_suite_passes_against_the_real_registry():
    suite = json.loads((ROOT / "evals/routing/policy-suite.json").read_text(encoding="utf-8"))
    report = evaluate(REGISTRY, POLICY, suite)
    failed = [r["id"] for r in report["results"] if not r["passed"]]
    assert not failed, failed


# Offline eval path determinism.

def test_blind_harness_fingerprint_ignores_the_run_timestamp():
    def run():
        proc = subprocess.run([sys.executable, str(ROOT / "tooling/run_blind_eval_harness.py")],
                              capture_output=True, text=True, check=True, cwd=ROOT)
        return json.loads(proc.stdout)
    first, second = run(), run()
    assert first["fingerprint"] == second["fingerprint"]
    assert first["fingerprint"] == fingerprint(first["reports"])
    changed = deepcopy(first["reports"])
    changed[0]["case_count"] += 1
    assert fingerprint(changed) != first["fingerprint"]


@pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")
def test_behavior_evals_survive_a_contributor_signing_config(tmp_path):
    config = tmp_path / "gitconfig"
    config.write_text("[commit]\n\tgpgsign = true\n[gpg]\n\tprogram = false\n", encoding="utf-8")
    env = {**os.environ, "GIT_CONFIG_GLOBAL": str(config)}
    proc = subprocess.run([sys.executable, str(ROOT / "tooling/run_behavior_evals.py")],
                          capture_output=True, text=True, cwd=ROOT, env=env, check=False)
    assert proc.returncode == 0, proc.stderr[-2000:]


# Confusion report over every labelled prompt in the repository.

def _row(prompt, forbidden=(), **expected):
    return {"source": "t", "prompt": prompt, "forbidden": list(forbidden), **expected}


def test_confusion_counts_misroutes_false_positives_and_unlabelled_rows():
    rows = [
        _row("Run AI Council on this decision.", expected="ai-council"),
        _row("Run AI Council on this decision, please.", expected="repo-roaster"),
        _row("Run AI Council on this choice.", ["ai-council"]),
        _row("What is two plus two?", expected=None),
    ]
    data = cov.confusion(rows, REGISTRY, POLICY)
    assert data["prompts"] == 4 and data["labelled"] == 3
    assert data["pairs"] == [["repo-roaster", "ai-council", 1]]
    by_id = {row["id"]: row for row in data["skills"]}
    assert by_id["repo-roaster"] == {"id": "repo-roaster", "expected": 1, "routed": 0,
                                     "misses": {"ai-council": 1}, "false_positives": 0}
    assert by_id["ai-council"]["false_positives"] == 1
    # The unlabelled forbidden-only row is an error but never an accuracy denominator.
    assert {err["expected"] for err in data["errors"]} == {"repo-roaster", "(unlabelled)"}
    splits = data["splits"]
    assert sum(s["labelled"] for s in splits.values()) == 3
    assert sum(s["correct"] for s in splits.values()) == 2
    assert sum(s["false_positive"] for s in splits.values()) == 1


def test_split_is_stable_and_ignores_case_and_punctuation():
    assert cov.split_of("Roast this repo!") == cov.split_of("roast this repo")
    halves = {cov.split_of(f"prompt number {i}") for i in range(40)}
    assert halves == {"tune", "holdout"}


def test_labelled_prompts_read_every_source(tmp_path):
    skill = tmp_path / "skills" / "repo-roaster" / "evals"
    skill.mkdir(parents=True)
    (skill / "trigger-evals.json").write_text(json.dumps([
        {"query": "roast the repo", "should_trigger": True},
        {"query": "roast the landing page", "should_trigger": False, "near_miss": "content-roaster"},
        {"query": "summarize this", "should_trigger": False, "near_miss": "summarization"},
    ]), encoding="utf-8")
    (skill / "real-host.json").write_text(json.dumps({"evals": [
        {"id": "a", "prompt": "red-team this PR", "should_trigger": True},
        {"id": "b", "prompt": "forced", "should_trigger": True, "force_skill_invocation": True},
        {"id": "c", "prompt": "write a poem", "should_trigger": False},
    ]}), encoding="utf-8")
    registry = {"skills": [{"id": "repo-roaster", "lifecycle": "active", "trigger_examples": ["x"],
                            "negative_trigger_examples": ["y"]},
                           {"id": "content-roaster", "lifecycle": "active"}]}
    rows = cov.labelled_prompts(registry, [_case(must_not_trigger=["repo-roaster"])], root=tmp_path)
    by_prompt = {row["prompt"]: row for row in rows}
    assert by_prompt["Explain two plus two."] == {"source": "suite:c1", "prompt": "Explain two plus two.",
                                                  "forbidden": ["repo-roaster"], "expected": None}
    assert by_prompt["roast the repo"]["expected"] == "repo-roaster"
    assert by_prompt["roast the landing page"]["expected"] == "content-roaster"
    # A near miss naming a task type, not a skill, is a forbidden-only row.
    assert "expected" not in by_prompt["summarize this"]
    assert by_prompt["red-team this PR"]["expected"] == "repo-roaster"
    assert "forced" not in by_prompt
    assert by_prompt["write a poem"]["forbidden"] == ["repo-roaster"] and "expected" not in by_prompt["write a poem"]
    assert by_prompt["x"]["expected"] == "repo-roaster"
    assert by_prompt["y"]["forbidden"] == ["repo-roaster"]


def test_live_labelled_prompts_have_no_false_positives():
    # Every negative label in the repo (suite must_not_trigger, should-not-trigger
    # rows, registry negatives) holds; misroutes left are boundary cases, not
    # a forbidden skill firing.
    data = cov.confusion_report()
    assert data["labelled"] > 300
    assert all(split["false_positive"] == 0 for split in data["splits"].values()), data["errors"]


def test_natural_real_host_prompts_route_to_their_skill():
    rows = [row for row in cov.labelled_prompts(REGISTRY, []) if row["source"].startswith("real-host:")]
    assert len(rows) >= 20
    data = cov.confusion(rows, REGISTRY, POLICY)
    assert data["errors"] == [], data["errors"]


def test_confusion_cli_is_read_only(capsys):
    assert cov.main(["--confusion"]) == 0
    out = capsys.readouterr().out
    assert "labelled prompts" in out and "tune:" in out and "holdout:" in out
    assert cov.main(["--confusion", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["schema"] == "cometweb.routing-confusion/v1"
