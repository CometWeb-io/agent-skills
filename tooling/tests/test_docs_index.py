"""docs/README.md is the one map of the documentation, and each topic has one home.

Two kinds of drift this pins. A new document nobody links from the index is
invisible, so every document a reader might need must be listed. And when the
same instructions live in README, INSTALL, CONTRIBUTING and docs/, an edit to
one copy leaves the others wrong, so the details named below may appear only in
their home document; the rest link to it.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tooling"))

from markdown_resources import destinations, without_code  # noqa: E402

INDEX = ROOT / "docs" / "README.md"
SECTIONS = [
    "Start",
    "Using skills per host",
    "Writing a skill",
    "Evaluating",
    "Protocol (CW-AIP)",
    "Security",
    "Releasing",
]
# Documents deliberately left out of the index, each with the reason.
NOT_INDEXED = {
    "protocol/cw-interchange-v1.md": "a copy kept at its old path; the index links the canonical protocol/cw-aip-v1/",
}


def indexed() -> set[str]:
    found = set()
    for target in destinations(INDEX.read_text(encoding="utf-8")):
        path = target.partition("#")[0]
        if path and not re.match(r"^[a-z][a-z0-9+.-]*:", path, re.I):
            found.add((INDEX.parent / path).resolve().relative_to(ROOT).as_posix())
    return found


def documents() -> list[str]:
    paths = [
        *ROOT.glob("*.md"),
        *ROOT.glob("docs/**/*.md"),
        *ROOT.glob("protocol/**/*.md"),
        *ROOT.glob("profiles/**/*.md"),
        ROOT / "evals" / "routing" / "README.md",
    ]
    return sorted({p.relative_to(ROOT).as_posix() for p in paths if p != INDEX})


def test_index_sections_follow_the_reading_order() -> None:
    headings = re.findall(r"^## (.+)$", without_code(INDEX.read_text(encoding="utf-8")), re.M)
    assert headings[: len(SECTIONS)] == SECTIONS, headings


@pytest.mark.parametrize("doc", documents())
def test_every_document_is_indexed(doc: str) -> None:
    if doc in NOT_INDEXED:
        assert doc not in indexed(), f"{doc} is indexed now; drop it from NOT_INDEXED"
        return
    assert doc in indexed(), f"{doc} is not linked from docs/README.md"


def test_the_sweep_found_the_documents() -> None:
    found = set(documents())
    assert {"README.md", "INSTALL.md", "CONTRIBUTING.md", "SECURITY.md", "docs/ROUTING.md"} <= found
    assert len(found) >= 25


# detail -> the only document (outside CHANGELOG.md) that may state it
SINGLE_HOME = {
    "CLAUDE_SKILLS_DIR": "INSTALL.md",
    "SKILLS_REPLACE_CONFLICTS": "INSTALL.md",
    "SKILLS_BACKUP_DIR": "INSTALL.md",
    "already at the latest version": "INSTALL.md",
    "Make the evals real": "CONTRIBUTING.md",
    "Import marketplace": "docs/OPENAI-MARKETPLACE.md",
    "| `narrow_intent_guards` |": "docs/ROUTING.md",
}


@pytest.mark.parametrize("detail, home", sorted(SINGLE_HOME.items()))
def test_each_detail_has_one_home(detail: str, home: str) -> None:
    holders = sorted(
        doc for doc in documents()
        if doc != "CHANGELOG.md" and detail in (ROOT / doc).read_text(encoding="utf-8")
    )
    assert holders == [home], f"{detail!r} should live only in {home}; found in {holders}"


def test_readme_hands_details_to_their_homes() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for link in ("(INSTALL.md)", "(CONTRIBUTING.md#adding-a-skill)", "(docs/README.md)"):
        assert link in readme, link
