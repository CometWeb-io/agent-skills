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
        "                pass\n"
        "        value = 1 if x else 2\n"
    )
    assert module.guard_lines(source) == [2], (
        "only the real guard counts: __main__ and CLI dispatch are unreachable from a "
        "harness, an already-dead branch is not a guard, and a ternary is not a branch"
    )


def test_inline_and_elif_guards_are_measured_too() -> None:
    # The compact kernels write most rules on one line. Counting only block-form
    # `if` lines reported rubric-designer at 2 guards when it has 29, and every
    # one-line rule was invisible to the gate however weak its cases were.
    module = load()
    source = (
        "def check(x, args):\n"
        "    \"\"\"\n"
        "    if this line is prose in a docstring: it is not a guard\n"
        "    \"\"\"\n"
        "    if not x: errors.append('x:required')\n"
        "    elif x == {'a': 1}: return 2\n"
        "    elif args.command == 'rank': return 3\n"
        "    if x[1:2] == 'a:b': y = lambda q: q\n"
        "    if (x and\n"
        "            x):\n"
        "        pass\n"
        "    if True: pass\n"
    )
    assert module.guard_lines(source) == [4, 5, 7], (
        "one-line and elif guards count; docstring prose, CLI dispatch, a condition "
        "that spans lines and an already-constant branch do not"
    )
    lines = source.splitlines(keepends=True)
    assert module.disable(lines[4]) == "    if False: errors.append('x:required')\n"
    assert module.disable(lines[5]) == "    elif False: return 2\n"
    assert module.disable(lines[7]) == "    if False: y = lambda q: q\n", (
        "the colon inside a slice, a string or a lambda must not end the condition"
    )


def test_disabled_guard_still_compiles() -> None:
    module = load()
    source = "def f(x):\n    if x: return 1\n    elif x is None:\n        return 2\n    return 3\n"
    lines = source.splitlines(keepends=True)
    for index in module.guard_lines(source):
        mutated = "".join(lines[:index] + [module.disable(lines[index])] + lines[index + 1:])
        compile(mutated, "<mutant>", "exec")


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


def test_a_harness_that_holds_nothing_is_named_with_the_reason() -> None:
    module = load()
    rows = [
        {"id": "no-module", "guards": 0, "held": 0, "modules": []},
        {"id": "loose", "guards": 4, "held": 0, "modules": ["demo_kernel.py"]},
        {"id": "fine", "guards": 4, "held": 1, "modules": ["demo_kernel.py"]},
    ]
    problems = module.hollow(rows)
    assert [p.split(":")[0] for p in problems] == ["no-module", "loose"]
    assert "Rules written inside run_evals.py are never mutated" in problems[0]
    assert "none of 4 guard(s) in demo_kernel.py is held" in problems[1]
    baseline = {"skills": [{"id": r["id"], "guards": r["guards"], "held": r["held"]} for r in rows]}
    assert module.compare(rows, baseline)[:2] == problems


def test_update_refuses_to_record_a_hollow_harness(tmp_path, monkeypatch, capsys) -> None:
    """--update used to write the baseline and print OK; the suite then failed."""
    module = load()
    target = tmp_path / "eval-strength.json"
    monkeypatch.setattr(module, "BASELINE", target)
    monkeypatch.setattr(module, "current", lambda: [
        {"id": "new-skill", "guards": 0, "held": 0, "modules": [], "unexercised": [], "unheld": []}])
    assert module.main(["--update"]) == 1
    assert not target.exists()
    assert "new-skill" in capsys.readouterr().err
