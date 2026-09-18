"""The measurement that says whether a harness holds anything.

test_skill_eval_harnesses.py proves the harnesses run. This proves they bite — it was
built after inverting portfolio_kernel's priority comparator left all ten golden
cases green. Its own failure paths matter: the gate has to fall when a rule
stops being pinned, and the measurement has to stay honest about which modules
it looked at.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / "registry" / "eval-strength.json"
TABLE = ROOT / "docs" / "generated-eval-strength.md"


def load():
    spec = importlib.util.spec_from_file_location(
        "eval_strength", ROOT / "tooling" / "eval_strength.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rows() -> list[dict]:
    return json.loads(BASELINE.read_text(encoding="utf-8"))["skills"]


def test_guards_skips_only_what_a_harness_cannot_reach() -> None:
    module = load()
    source = (
        "if __name__ == '__main__':\n"
        "    if args.command == 'rank':\n"
        "        if item.get('blocks_current_goal'):\n"
        "            if False:\n"
        "        value = 1 if x else 2\n"
    )
    assert module.guard_lines(source) == [2], (
        "only the real guard counts: __main__ and CLI dispatch are unreachable from a "
        "harness, an already-dead branch is not a guard, and a ternary is not a branch"
    )


def test_a_dropped_guard_fails_the_check() -> None:
    module = load()
    baseline = {"skills": [{"id": "portfolio-operator", "guards": 61, "held": 55}]}
    current = [{"id": "portfolio-operator", "guards": 61, "held": 54}]
    problems = module.compare(current, baseline)
    assert problems and "55 -> 54" in problems[0]


def test_gaining_held_guards_is_never_a_failure() -> None:
    module = load()
    baseline = {"skills": [{"id": "portfolio-operator", "guards": 61, "held": 55}]}
    assert module.compare([{"id": "portfolio-operator", "guards": 61, "held": 61}], baseline) == []


def test_a_skill_missing_from_the_baseline_fails() -> None:
    module = load()
    problems = module.compare([{"id": "new-skill", "guards": 3, "held": 3}], {"skills": []})
    assert problems and "new-skill" in problems[0]


def test_a_harness_that_disappeared_fails() -> None:
    module = load()
    baseline = {"skills": [{"id": "gone", "guards": 3, "held": 3}]}
    problems = module.compare([], baseline)
    assert problems and "gone" in problems[0]


def test_kernels_follow_the_name_the_harness_uses(tmp_path) -> None:
    module = load()
    package = tmp_path / "demo"
    (package / "scripts").mkdir(parents=True)
    (package / "scripts" / "run_evals.py").write_text(
        "from demo_kernel import run\nPATH = 'scripts/other_kernel.py'\n", encoding="utf-8")
    for name in ("demo_kernel.py", "other_kernel.py", "unrelated.py"):
        (package / "scripts" / name).write_text("x = 1\n", encoding="utf-8")
    found = {p.name for p in module.kernels(package)}
    assert found == {"demo_kernel.py", "other_kernel.py"}
    assert module.unexercised(package, module.kernels(package)) == ["unrelated.py"]


def test_baseline_covers_every_shipped_harness() -> None:
    recorded = {row["id"] for row in rows()}
    shipped = {p.parent.parent.name for p in ROOT.glob("skills/*/scripts/run_evals.py")}
    assert recorded == shipped, f"baseline {sorted(recorded)} != shipped {sorted(shipped)}"


def test_baseline_never_records_a_harness_that_holds_nothing() -> None:
    for row in rows():
        assert row["held"] > 0, (
            f"{row['id']}: not one guard is held. The harness runs and proves nothing; "
            f"recording that as a baseline would freeze it that way."
        )


def test_table_matches_the_baseline() -> None:
    text = TABLE.read_text(encoding="utf-8")
    for row in rows():
        assert f"| `{row['id']}` | {row['guards']} | {row['held']} |" in text, (
            f"{row['id']} in {TABLE.name} disagrees with the baseline; "
            f"regenerate with --update --table"
        )
