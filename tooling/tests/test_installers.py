"""Behavioral contracts for the local host installers."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
# Installers link every registered package; the count follows the registry.


HOSTS = {
    "codex": "CODEX_SKILLS_DIR",
    "claude": "CLAUDE_SKILLS_DIR",
    "cursor": "CURSOR_SKILLS_DIR",
    "qwen": "QWEN_SKILLS_DIR",
    "qoder": "QODER_SKILLS_DIR",
    "lingma": "LINGMA_SKILLS_DIR",
}


def skill_count() -> int:
    """Installed links per host, derived so adding a skill does not break this file.

    Pinned to the registry so an empty glob cannot pass vacuously.
    """
    names = {path.parent.name for path in (ROOT / "skills").glob("*/SKILL.md")}
    registry = json.loads((ROOT / "registry" / "skills.json").read_text(encoding="utf-8"))
    assert names and names == {entry["id"] for entry in registry["skills"]}
    return len(names)


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
    expected = {path.parent.name for path in (ROOT / "skills").glob("*/SKILL.md")}
    # Derived rather than hard-coded, so adding a skill does not break this test;
    # pinned to the registry so an empty glob cannot pass vacuously.
    registry = json.loads((ROOT / "registry" / "skills.json").read_text(encoding="utf-8"))
    assert expected == {entry["id"] for entry in registry["skills"]}
    assert f"OK: {len(expected)} " in first.stdout
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


@pytest.mark.parametrize("host", ["cursor", "codex"])
def test_installer_rejects_dotdot_path_escape(host: str, tmp_path: Path) -> None:
    """SKILLS_DIR values with a '..' component must fail closed in the shared helper."""
    intended = tmp_path / "intended-skills"
    intended.mkdir()
    # Keep the literal ".." component; Path.resolve() would collapse it.
    escape_target = intended / "nested" / ".." / ".." / "outside-escape"
    outside = tmp_path / "outside-escape"
    backup = tmp_path / "backups"
    rules_escape = intended / ".." / ".." / "rules-escape"

    result = install(
        host,
        escape_target,
        backup,
        rules=rules_escape if host == "cursor" else tmp_path / "rules",
    )
    assert result.returncode != 0, result.stdout
    assert ".." in result.stderr
    assert not outside.exists()
    assert not (tmp_path / "rules-escape").exists()
    assert list(intended.iterdir()) == [] or {p.name for p in intended.iterdir()} <= {"nested"}
    if (intended / "nested").exists():
        assert list((intended / "nested").iterdir()) == []
    assert not backup.exists()


def test_cursor_installer_rejects_dotdot_rules_dir(tmp_path: Path) -> None:
    target = tmp_path / "skills"
    backup = tmp_path / "backups"
    rules_escape = target / ".." / ".." / "rules-escape"
    result = install("cursor", target, backup, rules=rules_escape)
    assert result.returncode != 0
    assert ".." in result.stderr
    assert not (tmp_path / "rules-escape").exists()
    assert not target.exists() or not list(target.iterdir())
    assert not backup.exists()


def run_installer(
    host: str, target: Path, tmp_path: Path, *args: str, replace_conflicts: bool = False,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    # A throwaway HOME keeps any default the script might fall back to off the real one.
    env["HOME"] = str(tmp_path / "home")
    env[HOSTS[host]] = str(target)
    env["SKILLS_BACKUP_DIR"] = str(tmp_path / "backups")
    env["SKILLS_REPLACE_CONFLICTS"] = "1" if replace_conflicts else "0"
    env["CURSOR_RULES_DIR"] = str(tmp_path / "rules")
    return subprocess.run(
        [str(ROOT / "scripts" / f"install-{host}.sh"), *args],
        cwd=ROOT, env=env, capture_output=True, text=True, check=False,
    )


def tree(path: Path) -> dict[str, str]:
    """Snapshot of every entry below path, symlinks recorded by their literal target."""
    if not path.exists():
        return {}
    return {
        str(p.relative_to(path)): (f"-> {os.readlink(p)}" if p.is_symlink() else "dir" if p.is_dir() else p.read_text())
        for p in sorted(path.rglob("*"))
    }


@pytest.mark.parametrize("host", HOSTS)
def test_dry_run_reports_plan_and_writes_nothing(host: str, tmp_path: Path) -> None:
    target = tmp_path / "skills"
    result = run_installer(host, target, tmp_path, "--dry-run")
    assert result.returncode == 0, result.stderr
    assert "would link ai-council" in result.stdout
    assert "nothing written" in result.stdout
    assert not target.exists()
    assert not (tmp_path / "rules").exists()
    assert not (tmp_path / "backups").exists()
    assert not (tmp_path / "home").exists()


@pytest.mark.parametrize("host", HOSTS)
def test_dry_run_still_fails_closed_on_conflict(host: str, tmp_path: Path) -> None:
    target = tmp_path / "skills"
    (target / "ai-council").mkdir(parents=True)
    before = tree(tmp_path)
    result = run_installer(host, target, tmp_path, "--dry-run")
    assert result.returncode != 0
    assert "conflict" in result.stderr.lower()
    assert tree(tmp_path) == before


def test_dry_run_with_replacement_names_the_backup_without_moving_it(tmp_path: Path) -> None:
    target = tmp_path / "skills"
    (target / "ai-council").mkdir(parents=True)
    (target / "ai-council" / "notes.md").write_text("keep me", encoding="utf-8")
    before = tree(tmp_path)
    result = run_installer("codex", target, tmp_path, "--dry-run", replace_conflicts=True)
    assert result.returncode == 0, result.stderr
    assert f"would back up {target / 'ai-council'}" in result.stdout
    assert tree(tmp_path) == before


@pytest.mark.parametrize("host", HOSTS)
def test_uninstall_removes_only_links_into_this_checkout(host: str, tmp_path: Path) -> None:
    target = tmp_path / "skills"
    assert run_installer(host, target, tmp_path).returncode == 0
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    (target / "my-own-skill").symlink_to(foreign, target_is_directory=True)
    (target / "notes.txt").write_text("mine", encoding="utf-8")

    preview = run_installer(host, target, tmp_path, "--uninstall", "--dry-run")
    assert preview.returncode == 0, preview.stderr
    count = skill_count()
    assert f"would remove {count}" in preview.stdout
    assert len(list(target.iterdir())) == count + 2

    result = run_installer(host, target, tmp_path, "--uninstall")
    assert result.returncode == 0, result.stderr
    assert f"removed {count}" in result.stdout
    assert {p.name for p in target.iterdir()} == {"my-own-skill", "notes.txt"}
    assert (target / "my-own-skill").resolve() == foreign
    assert (ROOT / "skills" / "ai-council" / "SKILL.md").is_file()

    again = run_installer(host, target, tmp_path, "--uninstall")
    assert again.returncode == 0, again.stderr
    assert "removed 0" in again.stdout


def test_uninstall_keeps_a_user_directory_that_shares_a_skill_name(tmp_path: Path) -> None:
    target = tmp_path / "skills"
    (target / "ai-council").mkdir(parents=True)
    (target / "ai-council" / "notes.md").write_text("keep me", encoding="utf-8")
    result = run_installer("claude", target, tmp_path, "--uninstall")
    assert result.returncode == 0, result.stderr
    assert "skip ai-council" in result.stdout
    assert (target / "ai-council" / "notes.md").read_text(encoding="utf-8") == "keep me"


def test_uninstall_of_missing_target_is_a_no_op(tmp_path: Path) -> None:
    result = run_installer("codex", tmp_path / "never-installed", tmp_path, "--uninstall")
    assert result.returncode == 0, result.stderr
    assert not (tmp_path / "never-installed").exists()


def test_cursor_uninstall_removes_its_rule_but_keeps_a_custom_one(tmp_path: Path) -> None:
    target, rules = tmp_path / "skills", tmp_path / "rules"
    assert run_installer("cursor", target, tmp_path).returncode == 0
    rule = rules / "cometweb-agent-skills.mdc"
    assert rule.is_symlink()
    assert run_installer("cursor", target, tmp_path, "--uninstall").returncode == 0
    assert not rule.exists() and not rule.is_symlink()

    rule.write_text("my custom routing", encoding="utf-8")
    assert run_installer("cursor", target, tmp_path, "--uninstall").returncode == 0
    assert rule.read_text(encoding="utf-8") == "my custom routing"


def test_reinstall_prunes_links_to_a_retired_skill(tmp_path: Path) -> None:
    checkout = tmp_path / "checkout"
    shutil.copytree(ROOT / "scripts", checkout / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
    for name in ("kept", "retired"):
        (checkout / "skills" / name).mkdir(parents=True)
        (checkout / "skills" / name / "SKILL.md").write_text(f"---\nname: {name}\n---\n", encoding="utf-8")
    target = tmp_path / "target"
    env = {**os.environ, "HOME": str(tmp_path / "home"), "CODEX_SKILLS_DIR": str(target)}
    script = str(checkout / "scripts" / "install-codex.sh")
    assert subprocess.run([script], env=env, check=False, capture_output=True).returncode == 0
    shutil.rmtree(checkout / "skills" / "retired")
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    (target / "dangling-but-foreign").symlink_to(tmp_path / "gone")

    result = subprocess.run([script], env=env, check=False, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "pruned stale link retired" in result.stdout
    assert {p.name for p in target.iterdir()} == {"kept", "dangling-but-foreign"}


def test_every_host_installs_the_same_skill_set(tmp_path: Path) -> None:
    layouts = {}
    for host in HOSTS:
        target = tmp_path / host
        result = run_installer(host, target, tmp_path)
        assert result.returncode == 0, result.stderr
        layouts[host] = {p.name: os.readlink(p) for p in target.iterdir()}
    assert len({tuple(sorted(layout.items())) for layout in layouts.values()}) == 1


@pytest.mark.parametrize("host", HOSTS)
def test_unknown_argument_fails_before_any_write(host: str, tmp_path: Path) -> None:
    target = tmp_path / "skills"
    result = run_installer(host, target, tmp_path, "--force")
    assert result.returncode == 2
    assert "unknown argument: --force" in result.stderr
    assert not target.exists()


def test_help_lists_dry_run_and_uninstall(tmp_path: Path) -> None:
    result = run_installer("claude", tmp_path / "skills", tmp_path, "--help")
    assert result.returncode == 0
    assert "--dry-run" in result.stdout and "--uninstall" in result.stdout
    assert not (tmp_path / "skills").exists()


def install_all_env(tmp_path: Path) -> dict[str, str]:
    env = {**os.environ, "HOME": str(tmp_path / "home"), "SKILLS_BACKUP_DIR": str(tmp_path / "backups"),
           "SKILLS_REPLACE_CONFLICTS": "0", "CURSOR_RULES_DIR": str(tmp_path / "rules")}
    for host, variable in HOSTS.items():
        env[variable] = str(tmp_path / host)
    return env


def test_install_all_changes_no_host_when_a_later_host_conflicts(tmp_path: Path) -> None:
    (tmp_path / "lingma" / "ai-council").mkdir(parents=True)
    result = subprocess.run([str(ROOT / "scripts" / "install-all.sh")], env=install_all_env(tmp_path),
                            capture_output=True, text=True, check=False)
    assert result.returncode != 0
    assert "preflight failed for lingma" in result.stderr
    for host in HOSTS:
        if host != "lingma":
            assert not (tmp_path / host).exists(), f"{host} was changed before the preflight failed"
    assert not (tmp_path / "rules").exists()


def test_install_all_installs_then_uninstalls_every_host(tmp_path: Path) -> None:
    env = install_all_env(tmp_path)
    script = str(ROOT / "scripts" / "install-all.sh")
    installed = subprocess.run([script], env=env, capture_output=True, text=True, check=False)
    assert installed.returncode == 0, installed.stderr
    for host in HOSTS:
        assert len(list((tmp_path / host).iterdir())) == skill_count()
    removed = subprocess.run([script, "--uninstall"], env=env, capture_output=True, text=True, check=False)
    assert removed.returncode == 0, removed.stderr
    for host in HOSTS:
        assert list((tmp_path / host).iterdir()) == []
    assert not (tmp_path / "home").exists()
