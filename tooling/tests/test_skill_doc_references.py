"""A path written inside a SKILL.md has to resolve.

These files are instructions an agent follows literally. A relative path that
points at nothing sends it looking in its own package for a script that ships
with a different skill — which is exactly what skill-orchestrator did with the
multiagent kernel. Absent-by-design local bindings are listed explicitly rather
than matched by pattern, so a genuinely missing file cannot hide among them.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

PACKAGE_DIRS = (
    "references", "scripts", "assets", "evals", "evaluation",
    "examples", "templates", "integration", "agents", "tests",
)
REFERENCE = re.compile(
    r"(?:^|[\s`(\[])((?:" + "|".join(PACKAGE_DIRS) + r")/[\w./-]+\.(?:py|md|json|svg|css|txt|yaml|yml|mdc))"
)

# Untracked on purpose: real values live beside the tracked placeholder and are
# gitignored. See the local-binding rule in AGENTS.md.
ABSENT_BY_DESIGN = {
    ("ai-council", "references/notion-bindings.local.json"),
    ("cometweb-context", "references/repos.local.txt"),
    ("cometweb-context", "references/source-registry.local.json"),
}


def skill_docs() -> list[Path]:
    return sorted(ROOT.glob("skills/*/SKILL.md"))


@pytest.mark.parametrize("doc", skill_docs(), ids=lambda p: p.parent.name)
def test_skill_md_paths_resolve(doc: Path) -> None:
    package = doc.parent
    missing = sorted(
        ref
        for ref in set(REFERENCE.findall(doc.read_text(encoding="utf-8")))
        if not (package / ref).exists() and (package.name, ref) not in ABSENT_BY_DESIGN
    )
    assert not missing, f"{package.name}/SKILL.md points at missing files: {missing}"


def test_absent_by_design_entries_are_still_relevant() -> None:
    """Stop the allowlist from outliving the files it excuses."""
    for skill, relative in sorted(ABSENT_BY_DESIGN):
        package = ROOT / "skills" / skill
        assert package.is_dir(), f"allowlist names a skill that no longer exists: {skill}"
        assert not (package / relative).exists(), (
            f"{skill}/{relative} now exists; drop it from ABSENT_BY_DESIGN"
        )
