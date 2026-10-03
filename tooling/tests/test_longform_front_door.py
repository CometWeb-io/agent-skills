"""Longform Publisher's front door: a whole guardrail and per-reference load triggers.

Codex shortens skill descriptions to fit one shared listing budget; the shortest
cut observed for this package left about 546 characters. The 1.1.3 sentence
reorder still ended the "Do not use" clause past that point, so the model saw
"or low-level PDF/DOCX file manip..." and never the boundary's end. The
description is now held under CUT_SAFE characters in full.

The front door used to open with "Always read" over seven references (about
12 KB) on every run, including a one-line status question. Each reference now
has its own line that names when to open it, and the inventory in
tests/front-door-rules.json pins at least one rule per reference, so a
reference cannot lose its trigger without a test failing.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills" / "longform-publisher"
sys.path.insert(0, str(ROOT / "tooling"))

from compatibility import read_frontmatter  # noqa: E402
from host_smoke import do_not_clause_span  # noqa: E402

CUT_SAFE = 540
TRIGGER = re.compile(r"\b(before|after|when|if|only when)\b", re.IGNORECASE)
CONTROL_PLANE = (
    "references/state-model.md",
    "references/source-policy.md",
    "references/claim-use.md",
    "references/fidelity-gate.md",
    "references/format-lineage.md",
    "references/report-contract.md",
    "references/output-contract.md",
)


def _description() -> str:
    return " ".join(read_frontmatter(SKILL / "SKILL.md")["description"].split())


def _registry_description() -> str:
    skills = json.loads((ROOT / "registry" / "skills.json").read_text(encoding="utf-8"))["skills"]
    return next(s["description"] for s in skills if s["id"] == "longform-publisher")


def _load_section() -> list[str]:
    body = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    section = body.split("## 0. Load the control plane", 1)[1].split("\n## ", 1)[0]
    return [line.strip() for line in section.splitlines() if line.strip()]


def test_description_fits_the_shortest_observed_codex_cut() -> None:
    text = _description()
    assert len(text) <= CUT_SAFE, len(text)
    span = do_not_clause_span(text)
    assert span is not None, "description lost its 'Do not use' boundary"
    assert span[1] <= CUT_SAFE, span


def test_description_keeps_every_named_neighbour() -> None:
    text = _description()
    for neighbour in ("ebook-publisher", "evidence-researcher", "ai-humanize", "content-writer"):
        assert neighbour in text, neighbour
    assert text == _registry_description()


def test_no_reference_is_loaded_unconditionally() -> None:
    lines = _load_section()
    assert not any(re.match(r"always (read|load|open)\b", line, re.IGNORECASE) for line in lines), lines


def test_every_control_plane_reference_has_its_own_trigger() -> None:
    lines = _load_section()
    missing = []
    for ref in CONTROL_PLANE:
        own = [line for line in lines if ref in line and line.startswith("-")]
        if len(own) != 1 or not TRIGGER.search(own[0].split(ref, 1)[1]):
            missing.append(ref)
    assert not missing, "references without a load trigger on their own line: " + ", ".join(missing)


def test_every_control_plane_reference_pins_a_rule() -> None:
    inventory = json.loads((SKILL / "tests" / "front-door-rules.json").read_text(encoding="utf-8"))
    pinned = {rule["where"] for rule in inventory["rules"]}
    assert not [ref for ref in CONTROL_PLANE if ref not in pinned]
