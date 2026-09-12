"""Keep the retired writer out of packages, routing and sync generators.

Historical changelog mentions remain valid; this checks operational definitions.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
RETIRED = {"ai-antipattern-writing", "ai-anti-pattern-writing", "ai-anti-pattern"}


def check_writer_retirement(root: Path) -> None:
    assert (root / "skills/ai-humanize/SKILL.md").is_file(), "Keep canonical ai-humanize"
    entries = json.loads((root / "registry/skills.json").read_text(encoding="utf-8"))["skills"]
    assert isinstance(entries, list) and entries, "Skill registry must be non-empty"
    assert any(entry.get("id") == "ai-humanize" for entry in entries)
    for name in RETIRED:
        path = root / "skills" / name
        assert not path.exists() and not path.is_symlink(), f"Retired package restored: {name}"
    for entry in entries:
        assert entry.get("id") not in RETIRED, "Retired registry entry restored"
        assert entry.get("alias_of") not in RETIRED, "Alias points to retired writer"
        for dependency in entry.get("dependencies", []):
            assert dependency.rstrip("?") not in RETIRED, "Dependency points to retired writer"
    # Inspect text only. Never execute a self-mutating migration during this test.
    for script in (root / ".sync-work").glob("*.py"):
        source = script.read_text(encoding="utf-8")
        for name in RETIRED:
            pattern = r"(?m)^\s*['\"]" + re.escape(name) + r"['\"]\s*:"
            assert not re.search(pattern, source), f"Retired writer in sync definitions: {script.name}"


def test_repository_has_only_canonical_writer():
    check_writer_retirement(ROOT)


@pytest.fixture
def sample_repo(tmp_path):
    (tmp_path / "skills/ai-humanize").mkdir(parents=True)
    (tmp_path / "skills/ai-humanize/SKILL.md").write_text("# Fixture", encoding="utf-8")
    (tmp_path / "registry").mkdir()
    (tmp_path / "registry/skills.json").write_text(
        json.dumps({"skills": [{"id": "ai-humanize", "dependencies": []}]}), encoding="utf-8"
    )
    return tmp_path


def test_canonical_writer_is_accepted(sample_repo):
    check_writer_retirement(sample_repo)


@pytest.mark.parametrize("name", sorted(RETIRED))
def test_retired_package_is_rejected(sample_repo, name):
    (sample_repo / "skills" / name).mkdir()
    with pytest.raises(AssertionError, match="Retired package"):
        check_writer_retirement(sample_repo)


@pytest.mark.parametrize("field,value", [
    ("id", "ai-antipattern-writing"),
    ("alias_of", "ai-antipattern-writing"),
    ("dependencies", ["ai-antipattern-writing?"]),
])
def test_retired_routing_is_rejected(sample_repo, field, value):
    path = sample_repo / "registry/skills.json"
    registry = json.loads(path.read_text(encoding="utf-8"))
    entry = {"id": "other", "dependencies": []}
    entry[field] = value
    registry["skills"].append(entry)
    path.write_text(json.dumps(registry), encoding="utf-8")
    with pytest.raises(AssertionError):
        check_writer_retirement(sample_repo)


def test_sync_cannot_reintroduce_writer(sample_repo):
    folder = sample_repo / ".sync-work"
    folder.mkdir()
    (folder / "apply_latest_skills.py").write_text(
        'PACKAGES = {\n"ai-antipattern-writing": {"version": "1.0.0"}\n}\n', encoding="utf-8"
    )
    with pytest.raises(AssertionError, match="sync definitions"):
        check_writer_retirement(sample_repo)


def test_history_is_not_erased(sample_repo):
    (sample_repo / "skills/ai-humanize/CHANGELOG.md").write_text(
        "Previously named ai-antipattern-writing.\n", encoding="utf-8"
    )
    check_writer_retirement(sample_repo)
