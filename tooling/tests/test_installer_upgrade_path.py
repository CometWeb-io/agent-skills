"""Upgrade path: rerunning an installer after `git pull` follows the skill set.

INSTALL.md promises that `git pull` plus a rerun of the installer adds new
skills and drops retired ones. These tests drive that through a real clone so
the fixture reproduces what git actually leaves on disk, including the ignored
`__pycache__` directories that keep a deleted skill's folder alive.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HOST_VARIABLES = {
    "codex": "CODEX_SKILLS_DIR",
    "claude": "CLAUDE_SKILLS_DIR",
    "cursor": "CURSOR_SKILLS_DIR",
}


def git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.com",
         "-c", "commit.gpgsign=false", "-c", "init.defaultBranch=main", *args],
        cwd=cwd, check=True, capture_output=True, text=True,
    )


def write_skill(skills: Path, name: str, *, with_script: bool = False) -> None:
    package = skills / name
    package.mkdir(parents=True)
    (package / "SKILL.md").write_text(f"---\nname: {name}\ndescription: fixture\n---\n", encoding="utf-8")
    if with_script:
        (package / "scripts").mkdir()
        (package / "scripts" / "kernel.py").write_text("VALUE = 1\n", encoding="utf-8")


def make_checkout(tmp_path: Path, names: list[str], *, scripts: set[str] = frozenset()) -> Path:
    checkout = tmp_path / "checkout"
    shutil.copytree(ROOT / "scripts", checkout / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
    for name in names:
        write_skill(checkout / "skills", name, with_script=name in scripts)
    return checkout


def run(checkout: Path, host: str, tmp_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = {
        **os.environ,
        "HOME": str(tmp_path / "home"),
        HOST_VARIABLES[host]: str(tmp_path / host),
        "CURSOR_RULES_DIR": str(tmp_path / "rules"),
        "SKILLS_BACKUP_DIR": str(tmp_path / "backups"),
        "SKILLS_REPLACE_CONFLICTS": "0",
    }
    return subprocess.run([str(checkout / "scripts" / f"install-{host}.sh"), *args],
                          env=env, capture_output=True, text=True, check=False, timeout=30)


def installed(tmp_path: Path, host: str) -> dict[str, Path]:
    return {entry.name: Path(os.readlink(entry)) for entry in (tmp_path / host).iterdir()}


@pytest.fixture
def upstream_and_clone(tmp_path: Path) -> tuple[Path, Path]:
    """A published repo with two skills and a user's clone of it."""
    upstream = make_checkout(tmp_path, ["kept", "retired"], scripts={"retired"})
    upstream = upstream.rename(tmp_path / "upstream")
    (upstream / ".gitignore").write_text("__pycache__/\n*.py[cod]\n", encoding="utf-8")
    git(upstream, "init", "-q")
    git(upstream, "add", "-A")
    git(upstream, "commit", "-qm", "initial skills")
    clone = tmp_path / "clone"
    git(tmp_path, "clone", "-q", str(upstream), str(clone))
    return upstream, clone


@pytest.mark.parametrize("host", HOST_VARIABLES)
def test_rerun_after_git_pull_adds_new_and_prunes_retired_skills(
    host: str, tmp_path: Path, upstream_and_clone: tuple[Path, Path]
) -> None:
    upstream, clone = upstream_and_clone
    first = run(clone, host, tmp_path)
    assert first.returncode == 0, first.stderr
    assert set(installed(tmp_path, host)) == {"kept", "retired"}
    # The user ran the retired skill's script once, so Python left a cache behind.
    cache = clone / "skills" / "retired" / "scripts" / "__pycache__"
    cache.mkdir()
    (cache / "kernel.cpython-312.pyc").write_bytes(b"\x00")

    git(upstream, "rm", "-rq", "skills/retired")
    write_skill(upstream / "skills", "added")
    git(upstream, "add", "-A")
    git(upstream, "commit", "-qm", "add one skill, retire another")
    git(clone, "pull", "-q", "--ff-only")
    assert (clone / "skills" / "retired").is_dir(), "fixture must reproduce the ignored-cache residue"

    second = run(clone, host, tmp_path)
    assert second.returncode == 0, second.stderr
    assert "WARN: skipping" in second.stderr and "retired" in second.stderr
    assert "linked added" in second.stdout
    assert "pruned stale link retired" in second.stdout
    links = installed(tmp_path, host)
    assert set(links) == {"kept", "added"}
    assert all(target == clone / "skills" / name for name, target in links.items())

    third = run(clone, host, tmp_path)
    assert third.returncode == 0, third.stderr
    assert "linked" not in third.stdout.replace("already linked", "")
    assert set(installed(tmp_path, host)) == {"kept", "added"}
    assert not (tmp_path / "backups").exists()


def test_renamed_skill_moves_its_link(tmp_path: Path, upstream_and_clone: tuple[Path, Path]) -> None:
    upstream, clone = upstream_and_clone
    assert run(clone, "codex", tmp_path).returncode == 0
    git(upstream, "mv", "skills/kept", "skills/kept-v2")
    git(upstream, "commit", "-qm", "rename a skill")
    git(clone, "pull", "-q", "--ff-only")

    result = run(clone, "codex", tmp_path)
    assert result.returncode == 0, result.stderr
    assert set(installed(tmp_path, "codex")) == {"kept-v2", "retired"}
    assert "pruned stale link kept" in result.stdout


def test_dry_run_after_pull_reports_the_upgrade_without_writing(
    tmp_path: Path, upstream_and_clone: tuple[Path, Path]
) -> None:
    upstream, clone = upstream_and_clone
    assert run(clone, "codex", tmp_path).returncode == 0
    git(upstream, "rm", "-rq", "skills/retired")
    write_skill(upstream / "skills", "added")
    git(upstream, "add", "-A")
    git(upstream, "commit", "-qm", "change skill set")
    git(clone, "pull", "-q", "--ff-only")

    preview = run(clone, "codex", tmp_path, "--dry-run")
    assert preview.returncode == 0, preview.stderr
    assert "would link added" in preview.stdout
    assert "would prune stale link retired" in preview.stdout
    assert set(installed(tmp_path, "codex")) == {"kept", "retired"}


def test_directory_with_real_content_but_no_skill_md_still_fails(tmp_path: Path) -> None:
    checkout = make_checkout(tmp_path, ["kept"])
    stray = checkout / "skills" / "half-written"
    (stray / "references").mkdir(parents=True)
    (stray / "references" / "notes.md").write_text("draft", encoding="utf-8")
    (stray / "__pycache__").mkdir()
    (stray / "__pycache__" / "x.pyc").write_bytes(b"\x00")

    result = run(checkout, "codex", tmp_path)
    assert result.returncode != 0
    assert "missing skill entrypoint" in result.stderr and "half-written" in result.stderr
    assert not (tmp_path / "codex").exists()


def test_cursor_relinks_a_rule_left_by_the_legacy_fallback(tmp_path: Path) -> None:
    checkout = make_checkout(tmp_path, ["kept"])
    (checkout / "docs").mkdir()
    (checkout / "rules").mkdir()
    (checkout / "rules" / "cometweb-agent-skills.mdc").write_text("generated", encoding="utf-8")
    (checkout / "extras").mkdir()
    legacy = checkout / "extras" / "cursor-routing.mdc"
    legacy.write_text("legacy", encoding="utf-8")
    rule = tmp_path / "rules" / "cometweb-agent-skills.mdc"
    rule.parent.mkdir()
    rule.symlink_to(legacy)

    preview = run(checkout, "cursor", tmp_path, "--dry-run")
    assert preview.returncode == 0, preview.stderr
    assert "would relink routing rule" in preview.stdout
    assert Path(os.readlink(rule)) == legacy

    result = run(checkout, "cursor", tmp_path)
    assert result.returncode == 0, result.stderr
    assert Path(os.readlink(rule)) == checkout / "rules" / "cometweb-agent-skills.mdc"
    assert not (tmp_path / "backups").exists()

    assert run(checkout, "cursor", tmp_path, "--uninstall").returncode == 0
    assert not rule.exists() and not rule.is_symlink()
