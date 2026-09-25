"""Behavioral contracts for the local host installers."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


HOSTS = {
    "codex": "CODEX_SKILLS_DIR",
    "claude": "CLAUDE_SKILLS_DIR",
    "cursor": "CURSOR_SKILLS_DIR",
    "qwen": "QWEN_SKILLS_DIR",
    "qoder": "QODER_SKILLS_DIR",
    "lingma": "LINGMA_SKILLS_DIR",
}


def install(
    host: str, target: Path, backup: Path, *, rules: Path | None = None,
    root: Path = ROOT, replace_conflicts: bool = False,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env[HOSTS[host]] = str(target)
    env["SKILLS_BACKUP_DIR"] = str(backup)
    env["SKILLS_REPLACE_CONFLICTS"] = "1" if replace_conflicts else "0"
    if rules is not None:
        env["CURSOR_RULES_DIR"] = str(rules)
    return subprocess.run(
        [str(root / "scripts" / f"install-{host}.sh")],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize("host", HOSTS)
def test_installer_links_every_canonical_skill_and_is_idempotent(host: str, tmp_path: Path) -> None:
    target, backup = tmp_path / "skills", tmp_path / "backups"
    rules = tmp_path / "rules"
    first = install(host, target, backup, rules=rules)
    assert first.returncode == 0, first.stderr
    assert "32" in first.stdout
    expected = {path.parent.name for path in (ROOT / "skills").glob("*/SKILL.md")}
    assert len(expected) == 32
    assert {path.name for path in target.iterdir()} == expected
    assert all((target / name).resolve() == ROOT / "skills" / name for name in expected)

    second = install(host, target, backup, rules=rules)
    assert second.returncode == 0, second.stderr
    assert not backup.exists()


@pytest.mark.parametrize("host", HOSTS)
@pytest.mark.parametrize("conflict_kind", ["directory", "file", "foreign_symlink"])
def test_installer_preserves_conflicting_skill_as_backup(
    host: str, conflict_kind: str, tmp_path: Path
) -> None:
    target, backup = tmp_path / "skills", tmp_path / "backups"
    existing = target / "ai-council"
    target.mkdir()
    foreign = tmp_path / "foreign-skill"
    if conflict_kind == "directory":
        existing.mkdir()
        (existing / "user-notes.md").write_text("keep me", encoding="utf-8")
    elif conflict_kind == "file":
        existing.write_text("keep me", encoding="utf-8")
    else:
        foreign.mkdir()
        existing.symlink_to(foreign, target_is_directory=True)
    result = install(host, target, backup, rules=tmp_path / "rules", replace_conflicts=True)
    assert result.returncode == 0, result.stderr
    assert existing.is_symlink()
    assert existing.resolve() == ROOT / "skills" / "ai-council"
    backups = list(backup.glob("*/ai-council"))
    assert len(backups) == 1
    if conflict_kind == "directory":
        assert (backups[0] / "user-notes.md").read_text(encoding="utf-8") == "keep me"
    elif conflict_kind == "file":
        assert backups[0].read_text(encoding="utf-8") == "keep me"
    else:
        assert backups[0].is_symlink() and backups[0].resolve() == foreign


@pytest.mark.parametrize("host", HOSTS)
@pytest.mark.parametrize("conflict_kind", ["directory", "file", "foreign_symlink"])
def test_installer_rejects_conflict_before_linking_any_skill(
    host: str, conflict_kind: str, tmp_path: Path
) -> None:
    target, backup = tmp_path / "skills", tmp_path / "backups"
    existing = target / "skill-orchestrator"
    target.mkdir()
    foreign = tmp_path / "foreign-skill"
    if conflict_kind == "directory":
        existing.mkdir()
        (existing / "user-notes.md").write_text("keep me", encoding="utf-8")
    elif conflict_kind == "file":
        existing.write_text("keep me", encoding="utf-8")
    else:
        foreign.mkdir()
        existing.symlink_to(foreign, target_is_directory=True)

    result = install(host, target, backup, rules=tmp_path / "rules")
    assert result.returncode != 0
    assert "conflict" in result.stderr.lower()
    assert {path.name for path in target.iterdir()} == {"skill-orchestrator"}
    if conflict_kind == "directory":
        assert (existing / "user-notes.md").read_text(encoding="utf-8") == "keep me"
    elif conflict_kind == "file":
        assert existing.read_text(encoding="utf-8") == "keep me"
    else:
        assert existing.is_symlink() and existing.resolve() == foreign
    assert not backup.exists()


def test_cursor_installer_preserves_custom_routing_rule(tmp_path: Path) -> None:
    rules = tmp_path / "rules"
    rules.mkdir()
    custom = rules / "cometweb-agent-skills.mdc"
    custom.write_text("my custom routing", encoding="utf-8")
    result = install("cursor", tmp_path / "skills", tmp_path / "backups", rules=rules)
    assert result.returncode == 0, result.stderr
    assert custom.read_text(encoding="utf-8") == "my custom routing"


def test_cursor_installer_rejects_foreign_rule_link_before_linking_skills(tmp_path: Path) -> None:
    rules = tmp_path / "rules"
    rules.mkdir()
    foreign = tmp_path / "foreign-rule.mdc"
    foreign.write_text("my rule", encoding="utf-8")
    rule = rules / "cometweb-agent-skills.mdc"
    rule.symlink_to(foreign)
    target, backup = tmp_path / "skills", tmp_path / "backups"

    result = install("cursor", target, backup, rules=rules)
    assert result.returncode != 0
    assert "conflict" in result.stderr.lower()
    assert rule.is_symlink() and rule.resolve() == foreign
    assert not target.exists() or not list(target.iterdir())
    assert not backup.exists()


def test_installer_fails_before_mutation_when_skill_entrypoint_is_missing(tmp_path: Path) -> None:
    checkout = tmp_path / "checkout"
    shutil.copytree(ROOT / "scripts", checkout / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
    valid = checkout / "skills" / "valid"
    valid.mkdir(parents=True)
    (valid / "SKILL.md").write_text("---\nname: valid\ndescription: valid\n---\n", encoding="utf-8")
    (checkout / "skills" / "incomplete").mkdir()
    target = tmp_path / "target"
    env = os.environ.copy()
    env["CODEX_SKILLS_DIR"] = str(target)
    env["SKILLS_BACKUP_DIR"] = str(tmp_path / "backups")
    result = subprocess.run([str(checkout / "scripts" / "install-codex.sh")], env=env, capture_output=True, text=True, check=False, timeout=10)
    assert result.returncode != 0
    assert "incomplete" in result.stderr
    assert not target.exists() or not list(target.iterdir())


@pytest.mark.parametrize("host", HOSTS)
@pytest.mark.parametrize("target_kind", ["source", "source_alias", "source_child", "source_alias_child", "source_parent"])
def test_installer_rejects_target_overlapping_source_tree(
    host: str, target_kind: str, tmp_path: Path
) -> None:
    checkout = tmp_path / "checkout"
    shutil.copytree(ROOT / "scripts", checkout / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
    skill = checkout / "skills" / "valid"
    skill.mkdir(parents=True)
    entrypoint = skill / "SKILL.md"
    entrypoint.write_text("---\nname: valid\ndescription: valid\n---\n", encoding="utf-8")
    targets = {
        "source": checkout / "skills",
        "source_child": skill / "host-skills",
        "source_parent": checkout,
    }
    if target_kind in {"source_alias", "source_alias_child"}:
        alias = tmp_path / "source-alias"
        alias.symlink_to(checkout / "skills", target_is_directory=True)
        target = alias if target_kind == "source_alias" else alias / "valid" / "host-skills"
    else:
        target = targets[target_kind]

    result = install(host, target, tmp_path / "backups", rules=tmp_path / "rules", root=checkout)
    assert result.returncode != 0
    assert "source" in result.stderr.lower()
    assert skill.is_dir() and not skill.is_symlink()
    assert entrypoint.is_file()
    assert not (skill / "host-skills").exists()
    assert not (tmp_path / "backups").exists()
