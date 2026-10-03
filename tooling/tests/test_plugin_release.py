"""A shipped skill change must come with a plugin version bump.

`claude plugin update` refreshes an installed plugin only when the manifest
version changes. Branch hardening-2026-10-r2 changed 23 skill VERSIONs while
the plugin stayed at 2.0.2, so an update would have kept every user on the old
skills. These tests run the gate against throwaway git repositories.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tooling"))
import plugin_release  # noqa: E402

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git is required for merge-base checks")


def git(repo: Path, *args: str) -> str:
    env = {
        "GIT_AUTHOR_NAME": "Example", "GIT_AUTHOR_EMAIL": "dev@example.com",
        "GIT_COMMITTER_NAME": "Example", "GIT_COMMITTER_EMAIL": "dev@example.com",
        "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1", "HOME": str(repo),
        "PATH": os.environ.get("PATH", ""),
    }
    return subprocess.run(
        ["git", *args], cwd=repo, env=env, check=True, capture_output=True, text=True
    ).stdout.strip()


def write_skill(repo: Path, skill: str, version: str) -> None:
    package = repo / "skills" / skill
    package.mkdir(parents=True, exist_ok=True)
    (package / "SKILL.md").write_text(f"---\nname: {skill}\ndescription: demo\n---\n", encoding="utf-8")
    (package / "VERSION").write_text(version + "\n", encoding="utf-8")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A repo whose `main` shipped plugin 1.0.0 with alpha 1.0.0, on a feature branch."""
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-q", "-b", "main")
    (root / "VERSION").write_text("1.0.0\n", encoding="utf-8")
    write_skill(root, "alpha", "1.0.0")
    (root / "registry").mkdir()
    assert plugin_release.main(["--record", "--root", str(root), "--base", "main"]) == 0
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "release 1.0.0")
    git(root, "checkout", "-q", "-b", "feature")
    return root


def check(root: Path, *extra: str) -> int:
    return plugin_release.main(["--check", "--root", str(root), "--base", "main", *extra])


def test_unchanged_tree_passes(repo: Path) -> None:
    assert check(repo, "--require-base") == 0


@pytest.mark.parametrize(
    "change",
    [
        lambda root: write_skill(root, "alpha", "1.0.1"),
        lambda root: write_skill(root, "beta", "1.0.0"),
        lambda root: shutil.rmtree(root / "skills" / "alpha"),
    ],
    ids=["skill-version-bumped", "skill-added", "skill-removed"],
)
def test_skill_change_without_plugin_bump_fails(repo: Path, change, capsys: pytest.CaptureFixture[str]) -> None:
    change(repo)
    assert check(repo) == 1
    assert "Bump VERSION" in capsys.readouterr().err


def test_record_refuses_to_reuse_a_released_version(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    write_skill(repo, "alpha", "1.1.0")
    assert plugin_release.main(["--record", "--root", str(repo), "--base", "main"]) == 1
    assert "never reused" in capsys.readouterr().err


def test_record_edited_by_hand_is_caught_by_the_merge_base(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Rewriting the record in place satisfies check 1; only the base comparison sees it."""
    write_skill(repo, "alpha", "1.1.0")
    record = repo / "registry" / "plugin-release.json"
    record.write_text(plugin_release.render_record("1.0.0", {"alpha": "1.1.0"}), encoding="utf-8")
    assert check(repo) == 1
    assert "not greater than 1.0.0" in capsys.readouterr().err


def test_bump_and_record_passes(repo: Path) -> None:
    write_skill(repo, "alpha", "1.1.0")
    (repo / "VERSION").write_text("1.1.0\n", encoding="utf-8")
    assert plugin_release.main(["--record", "--root", str(repo), "--base", "main"]) == 0
    assert check(repo, "--require-base") == 0
    assert json.loads((repo / "registry" / "plugin-release.json").read_text())["skills"] == {"alpha": "1.1.0"}


def test_bump_without_record_fails(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    write_skill(repo, "alpha", "1.1.0")
    (repo / "VERSION").write_text("1.1.0\n", encoding="utf-8")
    assert check(repo) == 1
    assert "--record" in capsys.readouterr().err


def test_missing_base_is_skipped_locally_but_fails_when_required(repo: Path) -> None:
    assert check(repo) == 0
    assert plugin_release.main(["--check", "--root", str(repo), "--base", "no-such-ref"]) == 0
    assert plugin_release.main(["--check", "--root", str(repo), "--base", "no-such-ref", "--require-base"]) == 1


def test_version_comparison_is_numeric_not_lexical() -> None:
    assert plugin_release.parse_version("2.10.0") > plugin_release.parse_version("2.9.9")


def test_this_repository_records_its_shipped_skills() -> None:
    """The committed record matches the tree, so a stale record fails here too."""
    assert plugin_release.check_record(ROOT) == []


def test_an_unreleased_bump_records_later_changes_in_the_same_branch(repo: Path) -> None:
    """1.1.0 is newer than the base, so it has not shipped; a second skill change
    in the same branch is recorded under it instead of forcing 1.2.0."""
    write_skill(repo, "alpha", "1.1.0")
    (repo / "VERSION").write_text("1.1.0\n", encoding="utf-8")
    assert plugin_release.main(["--record", "--root", str(repo), "--base", "main"]) == 0
    write_skill(repo, "beta", "0.1.0")
    assert check(repo) == 1
    assert plugin_release.main(["--record", "--root", str(repo), "--base", "main"]) == 0
    assert check(repo, "--require-base") == 0


def test_without_a_base_a_recorded_version_stays_final(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    write_skill(repo, "alpha", "1.1.0")
    assert plugin_release.main(["--record", "--root", str(repo), "--base", "no-such-ref"]) == 1
    assert "never reused" in capsys.readouterr().err


def test_ci_runs_the_gate_with_a_required_base() -> None:
    workflow = (ROOT / ".github" / "workflows" / "validate.yml").read_text(encoding="utf-8")
    assert "tooling/check_all.py --ci" in workflow
    assert "fetch-depth: 0" in workflow
    sys.path.insert(0, str(ROOT / "tooling"))
    import check_all

    gate = next(g for g in check_all.GATES if g.id == "plugin_release")
    assert "tooling/plugin_release.py" in gate.argv and "--check" in gate.argv
    assert gate.ci_args == ("--require-base",)


MANIFESTS = {
    "pyproject.toml": '[project]\nname = "demo"\nversion = "{v}"\n',
    "plugin.json": '{{\n  "name": "demo",\n  "version": "{v}"\n}}\n',
    ".claude-plugin/plugin.json": '{{\n  "name": "demo",\n  "version": "{v}",\n  "skills": "./skills"\n}}\n',
    ".cursor-plugin/plugin.json": '{{\n  "name": "demo",\n  "version": "{v}"\n}}\n',
    "uv.lock": 'version = 1\n\n[[package]]\nname = "other"\nversion = "{v}"\n\n'
               '[[package]]\nname = "demo"\nversion = "{v}"\nsource = {{ virtual = "." }}\n',
}


def write_manifests(root: Path, version: str) -> None:
    for relative, template in MANIFESTS.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(template.format(v=version), encoding="utf-8")


def bump(root: Path, level: str) -> int:
    return plugin_release.main(["--bump", level, "--root", str(root), "--base", "main"])


def test_bump_writes_every_version_and_records_the_set(repo: Path) -> None:
    """Five files and a lockfile carried the plugin version by hand; one command now does it."""
    write_manifests(repo, "1.0.0")
    write_skill(repo, "beta", "0.1.0")
    assert bump(repo, "minor") == 0
    assert (repo / "VERSION").read_text(encoding="utf-8").strip() == "1.1.0"
    for relative, template in MANIFESTS.items():
        expected = template.format(v="1.1.0")
        if relative == "uv.lock":  # only this project's own entry moves
            expected = MANIFESTS["uv.lock"].format(v="1.0.0").replace(
                'name = "demo"\nversion = "1.0.0"', 'name = "demo"\nversion = "1.1.0"')
        assert (repo / relative).read_text(encoding="utf-8") == expected, relative
    assert check(repo, "--require-base") == 0


def test_bump_counts_from_the_base_so_a_rerun_does_not_bump_twice(repo: Path) -> None:
    write_manifests(repo, "1.0.0")
    write_skill(repo, "alpha", "1.0.1")
    assert bump(repo, "patch") == 0
    assert bump(repo, "patch") == 0
    assert (repo / "VERSION").read_text(encoding="utf-8").strip() == "1.0.1"
    assert bump(repo, "minor") == 0  # a later, larger change on the same branch
    assert (repo / "VERSION").read_text(encoding="utf-8").strip() == "1.1.0"
    assert check(repo, "--require-base") == 0


def test_bump_refuses_an_unknown_level(repo: Path) -> None:
    with pytest.raises(SystemExit):
        bump(repo, "huge")
