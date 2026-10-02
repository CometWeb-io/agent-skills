"""Links in the repository's own documentation have to resolve.

test_skill_doc_references.py covers paths inside SKILL.md. The front-of-house
documents — README, CONTRIBUTING, INSTALL, docs/, profiles/, protocol/ — are
what a visitor reads first, and a link there that 404s on GitHub is the first
thing they notice. Relative targets must exist, and a `#fragment` must match a
heading in the target file the way GitHub slugs it. External URLs are not
fetched: the suite runs offline.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tooling"))

from markdown_resources import destinations, without_code  # noqa: E402

DOCS = sorted(
    {
        *(ROOT / name for name in ("README.md", "CONTRIBUTING.md", "INSTALL.md", "SECURITY.md", "AGENTS.md")),
        *ROOT.glob("docs/**/*.md"),
        *ROOT.glob("profiles/**/*.md"),
        *ROOT.glob("protocol/**/*.md"),
    }
)
EXTERNAL = re.compile(r"^(?:[a-z][a-z0-9+.-]*:|//)", re.I)


def github_slug(heading: str) -> str:
    text = re.sub(r"<[^>]+>", "", heading)
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = text.strip().lower().replace("`", "")
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def anchors(path: Path) -> set[str]:
    seen: dict[str, int] = {}
    result: set[str] = set()
    for line in without_code(path.read_text(encoding="utf-8")).splitlines():
        match = re.match(r"^ {0,3}#{1,6}\s+(.+?)\s*#*\s*$", line)
        if not match:
            continue
        slug = github_slug(match.group(1))
        count = seen.get(slug, 0)
        seen[slug] = count + 1
        result.add(slug if count == 0 else f"{slug}-{count}")
    return result


def broken_links(doc: Path) -> list[str]:
    problems = []
    for target in destinations(doc.read_text(encoding="utf-8")):
        if EXTERNAL.match(target):
            continue
        path_part, _, fragment = target.partition("#")
        resolved = (doc.parent / unquote(path_part)).resolve() if path_part else doc
        if not resolved.exists():
            problems.append(f"{target}: no such file")
            continue
        if fragment and resolved.suffix == ".md" and fragment.lower() not in anchors(resolved):
            problems.append(f"{target}: no heading #{fragment}")
    return problems


@pytest.mark.parametrize("doc", DOCS, ids=lambda p: str(p.relative_to(ROOT)))
def test_relative_links_resolve(doc: Path) -> None:
    assert broken_links(doc) == []


def test_the_sweep_covers_the_front_door() -> None:
    # A glob that silently matched nothing would turn this file into a no-op.
    names = {str(p.relative_to(ROOT)) for p in DOCS}
    assert {"README.md", "CONTRIBUTING.md", "docs/README.md", "profiles/cometweb/PROFILE.md"} <= names
    assert sum(len(destinations(p.read_text(encoding="utf-8"))) for p in DOCS) >= 50


def test_checker_reports_a_missing_file_and_a_missing_heading(tmp_path: Path) -> None:
    (tmp_path / "other.md").write_text("# Real heading\n", encoding="utf-8")
    doc = tmp_path / "doc.md"
    doc.write_text(
        "# Title\n\n[ok](other.md#real-heading) [self](#title) [web](https://example.com/x)\n"
        "[gone](missing.md) [bad](other.md#nope)\n\n```text\n[ignored](in-code.md)\n```\n",
        encoding="utf-8",
    )
    assert broken_links(doc) == ["missing.md: no such file", "other.md#nope: no heading #nope"]


def test_github_slugs_match_the_readme_contents_list() -> None:
    assert github_slug("How skills hand off: CW-AIP") == "how-skills-hand-off-cw-aip"
    assert github_slug("Pick a starting point") == "pick-a-starting-point"
