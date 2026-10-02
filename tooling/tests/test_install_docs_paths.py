"""Repo-root commands named in per-skill INSTALL.md files must exist."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# Backticked repo-root paths such as `tooling/package_skill.py` or
# `scripts/install-claude.sh`, optionally preceded by a runner.
REPO_PATH = re.compile(r"`(?:\./)?(?:uv run python |python3? )?((?:tooling|scripts)/[\w./-]+)")


def test_install_docs_name_only_existing_repo_tools():
    missing = []
    for doc in sorted(ROOT.glob("skills/*/INSTALL.md")):
        text = doc.read_text(encoding="utf-8")
        for path in REPO_PATH.findall(text):
            path = path.rstrip(".")
            if not (ROOT / path).exists() and not (doc.parent / path).exists():
                missing.append(f"{doc.relative_to(ROOT)}: {path}")
    assert not missing, "INSTALL.md names files that do not exist:\n" + "\n".join(missing)


def test_install_docs_package_their_own_skill():
    for doc in sorted(ROOT.glob("skills/*/INSTALL.md")):
        skill = doc.parent.name
        for named in re.findall(r"tooling/package_skill\.py ([a-z0-9-]+)", doc.read_text(encoding="utf-8")):
            assert named == skill, f"{doc.relative_to(ROOT)} packages {named}, not {skill}"
