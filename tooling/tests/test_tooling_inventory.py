"""docs/TOOLING.md lists every tooling script, and its Gate column is the truth.

Tools accumulated faster than anyone wrote down why: three scripts had no
mention outside their own tests, and one was still named as a step that no
longer existed. A script added without a row, a row left behind by a deleted
script, or a gate column that disagrees with check_all.GATES fails here.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TOOLING = ROOT / "tooling"
DOC = ROOT / "docs" / "TOOLING.md"


def _check_all():
    spec = importlib.util.spec_from_file_location("cw_inventory_check_all", TOOLING / "check_all.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve annotations through it
    spec.loader.exec_module(module)
    return module


check_all = _check_all()


def tools_on_disk() -> set[str]:
    found = {p.name for p in TOOLING.glob("*.py")} | {p.name for p in TOOLING.glob("*.sh")}
    found |= {f"core/{p.name}" for p in (TOOLING / "core").glob("*.py")}
    return found


def rows() -> dict[str, dict[str, str]]:
    table: dict[str, dict[str, str]] = {}
    for line in DOC.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 4 or not re.fullmatch(r"`[^`]+`", cells[0]):
            continue
        name = cells[0].strip("`")
        assert name not in table, f"{name} has two rows in docs/TOOLING.md"
        table[name] = {"what": cells[1], "gate": cells[2], "io": cells[3]}
    return table


def gates_running(tool: str) -> set[str]:
    path = f"tooling/{tool}"
    return {g.id for g in check_all.GATES if path in g.argv or path in (g.fix or ())}


def test_the_table_parser_finds_rows() -> None:
    # A format change that stopped the parser matching would make every check below vacuous.
    assert len(rows()) >= 50


def test_every_tool_has_a_row_and_every_row_a_tool() -> None:
    documented, present = set(rows()), tools_on_disk()
    assert not present - documented, f"add a row to docs/TOOLING.md for: {sorted(present - documented)}"
    assert not documented - present, f"docs/TOOLING.md lists scripts that do not exist: {sorted(documented - present)}"


@pytest.mark.parametrize("tool", sorted(tools_on_disk()))
def test_gate_column_matches_check_all(tool: str) -> None:
    row = rows().get(tool)
    assert row is not None, f"{tool} has no row in docs/TOOLING.md"
    listed = set(re.findall(r"`([a-z_]+)`", row["gate"]))
    if row["gate"] != "—":
        assert listed, f"{tool}: gate column must be gate ids in backticks or —"
    assert listed == gates_running(tool), (
        f"{tool}: docs/TOOLING.md says {sorted(listed) or '—'}, check_all.GATES runs it in "
        f"{sorted(gates_running(tool)) or 'no gate'}")


@pytest.mark.parametrize("tool", sorted(tools_on_disk()))
def test_every_row_says_what_and_what_it_touches(tool: str) -> None:
    row = rows()[tool]
    assert len(row["what"]) >= 20, f"{tool}: describe what it does"
    assert row["io"], f"{tool}: say what it reads and writes, or `library`"


def test_every_gate_script_is_inventoried() -> None:
    scripts = {t.removeprefix("tooling/") for g in check_all.GATES for t in (*g.argv, *(g.fix or ()))
               if t.startswith("tooling/") and t.endswith(".py") and "/tests/" not in t}
    assert scripts <= set(rows())


def test_the_index_links_the_inventory() -> None:
    assert "](TOOLING.md)" in (ROOT / "docs" / "README.md").read_text(encoding="utf-8")
