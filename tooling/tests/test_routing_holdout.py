"""The frozen routing holdout stays frozen, unseen by tuning, and reports aggregates only."""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tooling"))
import check_all  # noqa: E402
import routing_holdout as ho  # noqa: E402


@pytest.fixture()
def tree(tmp_path: Path) -> Path:
    """A throwaway copy of the files the holdout check reads."""
    for rel in ("registry/skills.json", "registry/routing-policy.json"):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / rel, tmp_path / rel)
    shutil.copytree(ROOT / "evals/routing", tmp_path / "evals/routing")
    return tmp_path


def _paths(root: Path) -> tuple[Path, Path]:
    return root / "evals/routing/holdout.json", root / "evals/routing/holdout.lock.json"


def _edit(path: Path, change) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    change(data)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_live_holdout_is_intact():
    assert ho.problems() == []


def test_any_edit_without_a_version_bump_fails(tree):
    holdout, lock = _paths(tree)
    _edit(holdout, lambda d: d["cases"][0].update(prompt=d["cases"][0]["prompt"] + " Thanks."))
    found = ho.problems(holdout, lock, tree)
    assert any("changed without a version bump" in p for p in found), found


def test_whitespace_only_edit_still_counts_as_a_change(tree):
    holdout, lock = _paths(tree)
    holdout.write_text(holdout.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    assert any("changed without a version bump" in p for p in ho.problems(holdout, lock, tree))


def test_a_bump_must_be_recorded_and_a_recorded_version_cannot_be_rehashed(tree):
    holdout, lock = _paths(tree)
    _edit(holdout, lambda d: d.update(holdout_version="9.0.0"))
    assert any("not recorded in the lock" in p for p in ho.problems(holdout, lock, tree))
    ho.record(holdout, lock)
    assert ho.problems(holdout, lock, tree) == []
    _edit(holdout, lambda d: d["cases"][0].update(reason="reworded"))
    with pytest.raises(SystemExit, match="already recorded"):
        ho.record(holdout, lock)


def test_record_keeps_earlier_versions_and_the_measurement_log(tree):
    holdout, lock = _paths(tree)
    before = json.loads(lock.read_text(encoding="utf-8"))
    _edit(holdout, lambda d: d.update(holdout_version="9.0.0"))
    ho.record(holdout, lock)
    after = json.loads(lock.read_text(encoding="utf-8"))
    assert after["versions"][: len(before["versions"])] == before["versions"]
    assert after["measurements"] == before["measurements"]
    assert after["current"] == "9.0.0"


def test_a_holdout_prompt_copied_into_a_tuned_set_fails(tree):
    holdout, lock = _paths(tree)
    leaked = json.loads(holdout.read_text(encoding="utf-8"))["cases"][5]
    suite = tree / "evals/routing/suite.json"
    _edit(suite, lambda d: d["cases"].append(dict(leaked, id="leaked-copy")))
    found = ho.problems(holdout, lock, tree)
    assert any("is no longer held out" in p and leaked["id"] in p for p in found), found


def test_a_paraphrase_in_a_tuned_set_fails_as_a_near_duplicate(tree):
    holdout, lock = _paths(tree)
    case = next(c for c in json.loads(holdout.read_text(encoding="utf-8"))["cases"]
                if len(c["prompt"].split()) > 12)
    paraphrase = case["prompt"].rstrip(".?!") + " please"
    suite = tree / "evals/routing/suite.json"
    _edit(suite, lambda d: d["cases"].append(dict(case, id="leaked-paraphrase", prompt=paraphrase)))
    found = ho.problems(holdout, lock, tree)
    assert any("near-duplicates" in p for p in found), found


def test_version_1_covers_every_skill_active_at_the_freeze():
    data = json.loads(ho.HOLDOUT.read_text(encoding="utf-8"))
    positives = {c["expected_primary_skill"] for c in data["cases"] if c["kind"] == "positive"}
    assert len(positives) == 32 and ho.uncovered_skills() == []
    assert len(data["cases"]) >= 120
    assert {c["lang"] for c in data["cases"]} == {"en", "pl"}


def test_a_skill_added_after_the_freeze_is_reported_not_failed(tree):
    holdout, lock = _paths(tree)
    registry = tree / "registry/skills.json"
    _edit(registry, lambda d: d["skills"].append(dict(d["skills"][0], id="added-later")))
    assert ho.uncovered_skills(holdout, tree) == ["added-later"]
    assert not any("added-later" in p for p in ho.problems(holdout, lock, tree))


def test_measurement_carries_no_per_case_detail():
    result = ho.measure()
    assert set(result) == {"holdout_version", "sha256", "overall", "by_kind", "by_lang"}
    text = json.dumps(result)
    for case in json.loads(ho.HOLDOUT.read_text(encoding="utf-8"))["cases"]:
        assert case["id"] not in text
    ok, total = result["overall"]
    assert 0 <= ok <= total == len(json.loads(ho.HOLDOUT.read_text(encoding="utf-8"))["cases"])


def test_lock_records_a_baseline_measurement_for_the_current_version():
    lock = json.loads(ho.LOCK.read_text(encoding="utf-8"))
    current = [m for m in lock["measurements"] if m["holdout_version"] == lock["current"]]
    assert current and current[0]["label"].startswith("baseline")


def test_check_all_runs_the_integrity_gate():
    gate = next(g for g in check_all.GATES if g.id == "routing_holdout")
    assert "tooling/routing_holdout.py" in gate.argv and "--check" in gate.argv
