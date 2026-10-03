"""install-codex.sh targets the documented user location and migrates the old one.

Codex documents `$HOME/.agents/skills` for user skills
(https://developers.openai.com/codex/skills). Earlier installs linked into
`$CODEX_HOME/skills` (`~/.codex/skills`). With the default target the installer
links the new location, then moves this checkout's old links into the backup
directory; it never touches anything else in the old directory. Every test runs
under a temporary HOME, so the machine's real Codex directories are never read.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def make_checkout(tmp_path: Path, names: tuple[str, ...] = ("alpha", "beta")) -> Path:
    checkout = tmp_path / "checkout"
    shutil.copytree(ROOT / "scripts", checkout / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
    for name in names:
        (checkout / "skills" / name).mkdir(parents=True)
        (checkout / "skills" / name / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: {name} skill\n---\n", encoding="utf-8")
    return checkout


def run(checkout: Path, home: Path, *args: str, **extra: str) -> subprocess.CompletedProcess[str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith(("CODEX_", "SKILLS_"))}
    env.update({"HOME": str(home), "SKILLS_BACKUP_DIR": str(home / "backups"), **extra})
    return subprocess.run([str(checkout / "scripts" / "install-codex.sh"), *args], env=env,
                          capture_output=True, text=True, check=False, timeout=30)


def links(directory: Path) -> dict[str, str]:
    if not directory.is_dir():
        return {}
    return {p.name: os.readlink(p) for p in directory.iterdir() if p.is_symlink()}


def legacy_install(checkout: Path, home: Path) -> Path:
    """The layout an earlier installer left behind."""
    legacy = home / ".codex" / "skills"
    legacy.mkdir(parents=True)
    for skill in sorted((checkout / "skills").iterdir()):
        (legacy / skill.name).symlink_to(checkout / "skills" / skill.name)
    return legacy


def test_default_target_is_the_documented_agents_skills_directory(tmp_path: Path) -> None:
    checkout, home = make_checkout(tmp_path), tmp_path / "home"
    result = run(checkout, home)
    assert result.returncode == 0, result.stderr
    skills = checkout / "skills"
    assert links(home / ".agents" / "skills") == {"alpha": str(skills / "alpha"), "beta": str(skills / "beta")}
    assert not (home / ".codex" / "skills").exists()


def test_hosts_json_names_the_documented_and_legacy_locations() -> None:
    codex = json.loads((ROOT / "registry" / "hosts.json").read_text(encoding="utf-8"))["hosts"]["openai-codex"]
    assert codex["skill_dirs"] == ["~/.agents/skills"]
    assert codex["legacy_skill_dirs"] == ["~/.codex/skills"]
    assert codex["skill_location"]["source"] == "https://developers.openai.com/codex/skills"


def test_old_links_move_to_the_backup_and_foreign_entries_stay(tmp_path: Path) -> None:
    checkout, home = make_checkout(tmp_path), tmp_path / "home"
    legacy = legacy_install(checkout, home)
    own = legacy / "my-own-skill"
    own.mkdir()
    (own / "SKILL.md").write_text("mine", encoding="utf-8")
    other = tmp_path / "other-checkout" / "skills" / "alpha"
    other.mkdir(parents=True)
    (legacy / "gamma").symlink_to(other)

    result = run(checkout, home)
    assert result.returncode == 0, result.stderr
    assert "migrated 2 Codex skill links" in result.stdout
    assert sorted(links(home / ".agents" / "skills")) == ["alpha", "beta"]
    assert sorted(p.name for p in legacy.iterdir()) == ["gamma", "my-own-skill"]
    backups = [p for p in (home / "backups").rglob("codex-legacy-*")]
    assert sorted(p.name for p in backups) == ["codex-legacy-alpha", "codex-legacy-beta"]
    assert all(os.readlink(p).startswith(str(checkout / "skills")) for p in backups)

    again = run(checkout, home)
    assert again.returncode == 0, again.stderr
    assert "migrat" not in again.stdout and "moved" not in again.stdout
    assert sorted(p.name for p in legacy.iterdir()) == ["gamma", "my-own-skill"]


def test_dry_run_reports_the_migration_and_writes_nothing(tmp_path: Path) -> None:
    checkout, home = make_checkout(tmp_path), tmp_path / "home"
    legacy = legacy_install(checkout, home)
    before = links(legacy)
    result = run(checkout, home, "--dry-run")
    assert result.returncode == 0, result.stderr
    assert "would move legacy link alpha" in result.stdout
    assert "would migrate 2 Codex skill links" in result.stdout
    assert links(legacy) == before
    assert not (home / ".agents").exists()
    assert not (home / "backups").exists()


def test_legacy_directory_aliased_to_the_target_is_not_emptied(tmp_path: Path) -> None:
    checkout, home = make_checkout(tmp_path), tmp_path / "home"
    (home / ".agents" / "skills").mkdir(parents=True)
    (home / ".codex").mkdir(parents=True)
    (home / ".codex" / "skills").symlink_to(home / ".agents" / "skills")
    for _ in range(2):
        result = run(checkout, home)
        assert result.returncode == 0, result.stderr
        assert "moved" not in result.stdout
    assert sorted(links(home / ".agents" / "skills")) == ["alpha", "beta"]


def test_codex_home_sets_the_legacy_directory(tmp_path: Path) -> None:
    checkout, home = make_checkout(tmp_path), tmp_path / "home"
    codex_home = tmp_path / "custom-codex"
    (codex_home / "skills").mkdir(parents=True)
    (codex_home / "skills" / "alpha").symlink_to(checkout / "skills" / "alpha")
    result = run(checkout, home, CODEX_HOME=str(codex_home))
    assert result.returncode == 0, result.stderr
    assert "migrated 1 Codex skill links" in result.stdout
    assert not list((codex_home / "skills").iterdir())


def test_explicit_target_keeps_the_old_path_and_touches_nothing_else(tmp_path: Path) -> None:
    checkout, home = make_checkout(tmp_path), tmp_path / "home"
    legacy = legacy_install(checkout, home)
    result = run(checkout, home, CODEX_SKILLS_DIR=str(legacy))
    assert result.returncode == 0, result.stderr
    assert "already linked alpha" in result.stdout
    assert sorted(links(legacy)) == ["alpha", "beta"]
    assert not (home / ".agents").exists()


def test_uninstall_removes_links_from_both_locations(tmp_path: Path) -> None:
    checkout, home = make_checkout(tmp_path), tmp_path / "home"
    assert run(checkout, home).returncode == 0
    legacy = legacy_install(checkout, home)
    result = run(checkout, home, "--uninstall")
    assert result.returncode == 0, result.stderr
    assert "removed 4 Codex skill links" in result.stdout
    assert not links(home / ".agents" / "skills") and not links(legacy)


@pytest.mark.parametrize("bad", ["a/../b"])
def test_legacy_directory_with_climb_out_fails_before_any_change(tmp_path: Path, bad: str) -> None:
    checkout, home = make_checkout(tmp_path), tmp_path / "home"
    result = run(checkout, home, CODEX_HOME=str(tmp_path / bad))
    assert result.returncode != 0
    assert not (home / ".agents").exists()
