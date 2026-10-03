"""Normative rules survive a front-door diet.

Shrinking SKILL.md moves detail into references/. That is only safe when every
MUST/NEVER/gate the skill relied on is still somewhere an agent will read it:
either in SKILL.md itself, or in a reference that SKILL.md names on a line that
says when to open it. A pointer without a trigger is a file nobody loads.

Each participating skill keeps an inventory at tests/front-door-rules.json. This
test pins it in both directions:

- every inventoried rule is present, verbatim, in the file it claims;
- a rule kept behind a pointer has that pointer in SKILL.md with a load trigger;
- every normative sentence in SKILL.md is inventoried, so a new rule cannot be
  added to the front door and later dropped without anyone noticing.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
INVENTORIES = sorted((ROOT / "skills").glob("*/tests/front-door-rules.json"))

NORMATIVE = re.compile(r"\b(never|must|do not|cannot)\b", re.IGNORECASE)
TRIGGER = re.compile(r"\b(read|open|load|before|when|if|only when)\b", re.IGNORECASE)


def _squash(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _body(text: str) -> str:
    if text.startswith("---"):
        return text.split("\n---", 1)[1]
    return text


def _blocks(text: str) -> list[str]:
    """Paragraphs, list items and table cells, with hard-wrapped lines rejoined."""
    blocks: list[str] = []
    current: list[str] = []
    lines = text.splitlines()

    def flush() -> None:
        if current:
            blocks.append(" ".join(current))
            current.clear()

    for index, raw in enumerate(lines):
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("```"):
            flush()
            continue
        if line.startswith("|"):
            flush()
            following = lines[index + 1].strip() if index + 1 < len(lines) else ""
            if re.fullmatch(r"\|[\s:|-]+\|", line) or re.fullmatch(r"\|[\s:|-]+\|", following):
                continue  # separator row, or the header row above it
            blocks.extend(cell.strip() for cell in line.strip("|").split("|"))
            continue
        if re.match(r"([-*]|\d+\.|- \[[ x]\])\s", line):
            flush()
            line = re.sub(r"^([-*]|\d+\.)\s+(\[[ x]\]\s+)?", "", line)
        current.append(line)
    flush()
    return blocks


def _normative_sentences(skill_md: str) -> list[str]:
    found = []
    for block in _blocks(_body(skill_md)):
        for sentence in re.split(r"(?<=[.!?])\s+", block):
            if NORMATIVE.search(sentence):
                found.append(sentence)
    return found


def _with_intro(lines: list[str], index: int) -> str:
    """A list item or table row, plus the sentence that introduces its list.

    "Read when the trigger applies:" above a table is the trigger for every row.
    """
    text = lines[index]
    if not re.match(r"\s*([-*|]|\d+\.)", text):
        return text
    for above in range(index - 1, -1, -1):
        line = lines[above].strip()
        if not line or re.match(r"([-*|]|\d+\.)", line):
            continue
        return text + " " + line
    return text


def _load(path: Path) -> tuple[Path, dict]:
    return path.parents[1], json.loads(path.read_text(encoding="utf-8"))


def test_inventories_exist() -> None:
    assert INVENTORIES, "no skill ships tests/front-door-rules.json"


@pytest.mark.parametrize("inventory", INVENTORIES, ids=lambda p: p.parents[1].name)
def test_inventory_is_well_formed(inventory: Path) -> None:
    skill_dir, data = _load(inventory)
    assert data["skill"] == skill_dir.name
    ids = [rule["id"] for rule in data["rules"]]
    assert len(ids) == len(set(ids)), "duplicate rule ids"
    for rule in data["rules"]:
        assert rule["text"].strip(), rule["id"]
        assert rule["where"] == "SKILL.md" or rule["where"].startswith("references/"), rule


@pytest.mark.parametrize("inventory", INVENTORIES, ids=lambda p: p.parents[1].name)
def test_every_rule_is_where_it_claims(inventory: Path) -> None:
    skill_dir, data = _load(inventory)
    missing = []
    for rule in data["rules"]:
        target = skill_dir / rule["where"]
        if not target.is_file() or _squash(rule["text"]) not in _squash(target.read_text(encoding="utf-8")):
            missing.append(f"{rule['id']} ({rule['where']}): {rule['text']}")
    assert not missing, "rules dropped or reworded without updating the inventory:\n" + "\n".join(missing)


@pytest.mark.parametrize("inventory", INVENTORIES, ids=lambda p: p.parents[1].name)
def test_deferred_rules_have_a_triggered_pointer(inventory: Path) -> None:
    skill_dir, data = _load(inventory)
    skill_md = _body((skill_dir / "SKILL.md").read_text(encoding="utf-8"))
    lines = skill_md.splitlines()
    unreachable = []
    for where in sorted({r["where"] for r in data["rules"] if r["where"] != "SKILL.md"}):
        hits = [i for i, line in enumerate(lines) if where in line]
        if not any(TRIGGER.search(line) for line in (_with_intro(lines, i) for i in hits)):
            unreachable.append(where)
    assert not unreachable, (
        "SKILL.md must point at these references on a line that says when to load them: "
        + ", ".join(unreachable)
    )


@pytest.mark.parametrize("inventory", INVENTORIES, ids=lambda p: p.parents[1].name)
def test_every_front_door_rule_is_inventoried(inventory: Path) -> None:
    skill_dir, data = _load(inventory)
    pinned = [_squash(r["text"]) for r in data["rules"] if r["where"] == "SKILL.md"]
    sentences = _normative_sentences((skill_dir / "SKILL.md").read_text(encoding="utf-8"))
    loose = [s for s in sentences if not any(p in _squash(s) for p in pinned)]
    assert not loose, "normative sentences in SKILL.md with no inventory entry:\n" + "\n".join(loose)


def test_detector_sees_a_dropped_rule(tmp_path: Path) -> None:
    """The check must fail when a rule disappears, or it proves nothing."""
    skill = tmp_path / "skills" / "demo"
    (skill / "tests").mkdir(parents=True)
    (skill / "references").mkdir()
    (skill / "SKILL.md").write_text("---\nname: demo\n---\nRead `references/x.md` before acting.\n")
    (skill / "references" / "x.md").write_text("Something else entirely.\n")
    inventory = skill / "tests" / "front-door-rules.json"
    inventory.write_text(json.dumps({"skill": "demo", "rules": [
        {"id": "gone", "text": "Never ship on a guess", "where": "references/x.md"},
    ]}))
    with pytest.raises(AssertionError, match="gone"):
        test_every_rule_is_where_it_claims(inventory)


def test_detector_sees_an_untriggered_pointer(tmp_path: Path) -> None:
    skill = tmp_path / "skills" / "demo"
    (skill / "tests").mkdir(parents=True)
    (skill / "references").mkdir()
    (skill / "SKILL.md").write_text("---\nname: demo\n---\nSee `references/x.md`.\n")
    (skill / "references" / "x.md").write_text("Never ship on a guess.\n")
    inventory = skill / "tests" / "front-door-rules.json"
    inventory.write_text(json.dumps({"skill": "demo", "rules": [
        {"id": "kept", "text": "Never ship on a guess", "where": "references/x.md"},
    ]}))
    with pytest.raises(AssertionError, match="references/x.md"):
        test_deferred_rules_have_a_triggered_pointer(inventory)


def test_detector_sees_an_uninventoried_rule(tmp_path: Path) -> None:
    skill = tmp_path / "skills" / "demo"
    (skill / "tests").mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: demo\n---\nNever merge on Fridays.\n")
    inventory = skill / "tests" / "front-door-rules.json"
    inventory.write_text(json.dumps({"skill": "demo", "rules": []}))
    with pytest.raises(AssertionError, match="Fridays"):
        test_every_front_door_rule_is_inventoried(inventory)
