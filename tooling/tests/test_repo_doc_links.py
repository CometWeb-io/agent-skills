"""Links in every Markdown file in the repository have to resolve.

That is the front-of-house documents (README, CONTRIBUTING, INSTALL, docs/,
profiles/, protocol/), the routing and eval notes, the host rule files
(`.mdc`), and every skill package's own Markdown. A link that 404s on GitHub
or inside an installed package is the first thing a reader notices. Relative
targets must exist, and a `#fragment` must match a heading in the target file
the way GitHub slugs it. External URLs are not fetched: the suite runs offline.
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

# Build output, caches and environments are not documentation.
SKIP_PARTS = {".git", ".venv", "venv", "node_modules", "dist", "build", "__pycache__",
              ".pytest_cache", ".ruff_cache", ".mypy_cache"}
DOCS = sorted(
    path
    for pattern in ("*.md", "*.mdc")
    for path in ROOT.rglob(pattern)
    if path.is_file() and not SKIP_PARTS.intersection(path.relative_to(ROOT).parts)
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
    names = {p.relative_to(ROOT).as_posix() for p in DOCS}
    assert {"README.md", "CONTRIBUTING.md", "docs/README.md", "docs/ROUTING.md", "profiles/cometweb/PROFILE.md",
            "evals/routing/README.md", ".github/PULL_REQUEST_TEMPLATE.md", "extras/cursor-routing.mdc",
            "skills/ai-council/SKILL.md"} <= names
    # Every Markdown file the repository tracks is swept, skill packages included.
    assert len(names) >= 500, len(names)
    assert sum(len(destinations(p.read_text(encoding="utf-8"))) for p in DOCS) >= 200


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
