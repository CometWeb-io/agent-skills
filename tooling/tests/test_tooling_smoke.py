"""Smoke tests for repo tooling."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def test_validate_repo_exits_zero():
    proc = subprocess.run(
        [sys.executable, str(ROOT / "tooling" / "validate_repo.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout


def test_compatibility_exits_zero():
    proc = subprocess.run(
        [sys.executable, str(ROOT / "tooling" / "compatibility.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout


def _skill(tmp_path: Path, version: str) -> Path:
    skill = tmp_path / "demo-skill"
    skill.mkdir()
    (skill / "SKILL.md").write_text(
        "---\nname: demo-skill\ndescription: Synthetic fixture whose description is long enough "
        "to satisfy the eighty character minimum of the validator.\n---\n# Demo\n",
        encoding="utf-8",
    )
    (skill / "VERSION").write_text(version, encoding="utf-8")
    (skill / "LICENSE").write_text("Synthetic fixture license.\n", encoding="utf-8")
    return skill


def _validate_skill(skill: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(ROOT / "tooling" / "validate_skill.py"), str(skill)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def test_validate_skill_accepts_semver(tmp_path):
    proc = _validate_skill(_skill(tmp_path, "1.2.3-rc.1\n"))
    assert proc.returncode == 0, proc.stderr


@pytest.mark.parametrize("version", ["", "\n", "v1.0.0", "1.0", "01.0.0", "latest"])
def test_validate_skill_rejects_versions_the_packager_refuses(tmp_path, version):
    # package_skill.py rejects these at release time; the validator used to pass them.
    proc = _validate_skill(_skill(tmp_path, version))
    assert proc.returncode == 1
    assert "VERSION is not a semantic version" in proc.stderr


def test_validate_repo_reports_corrupt_registry_without_traceback(tmp_path, monkeypatch, capsys):
    sys.path.insert(0, str(ROOT / "tooling"))
    import validate_repo

    (tmp_path / "registry").mkdir()
    (tmp_path / "registry" / "skills.json").write_text("{not json", encoding="utf-8")
    monkeypatch.setattr(validate_repo, "ROOT", tmp_path)
    with pytest.raises(SystemExit) as exc:
        validate_repo.load_json(tmp_path / "registry" / "skills.json")
    assert exc.value.code == 1
    assert "FAIL: invalid JSON in registry/skills.json" in capsys.readouterr().err
    (tmp_path / "registry" / "skills.json").write_text("[]", encoding="utf-8")
    with pytest.raises(SystemExit):
        validate_repo.load_json(tmp_path / "registry" / "skills.json")
    assert "top-level JSON must be an object" in capsys.readouterr().err
