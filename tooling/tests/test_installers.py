"""Installer contracts for canonical multi-host skill linking."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read_script(name: str) -> str:
    return (ROOT / "scripts" / name).read_text(encoding="utf-8")


def test_qwen_installer_uses_native_qwen_skill_dir():
    text = read_script("install-qwen.sh")
    assert 'QWEN_SKILLS_DIR:-$HOME/.qwen/skills' in text
    assert "list_skills" in text
    assert "ln -s" in text


def test_qoder_installer_uses_qoder_skill_dir():
    text = read_script("install-qoder.sh")
    assert 'QODER_SKILLS_DIR:-$HOME/.qoder/skills' in text
    assert "list_skills" in text
    assert "ln -s" in text


def test_lingma_installer_uses_lingma_skill_dir():
    text = read_script("install-lingma.sh")
    assert 'LINGMA_SKILLS_DIR:-$HOME/.lingma/skills' in text
    assert "list_skills" in text
    assert "ln -s" in text


def test_install_all_includes_every_local_target():
    text = read_script("install-all.sh")
    for name in (
        "install-cursor.sh",
        "install-claude.sh",
        "install-codex.sh",
        "install-qwen.sh",
        "install-qoder.sh",
        "install-lingma.sh",
    ):
        assert name in text


def test_codex_installer_never_deletes_an_existing_skill_directory(tmp_path):
    target = tmp_path / "codex-skills"
    existing = target / "ai-council"
    existing.mkdir(parents=True)
    marker = existing / "user-notes.md"
    marker.write_text("keep me", encoding="utf-8")

    env = os.environ.copy()
    env["CODEX_SKILLS_DIR"] = str(target)
    result = subprocess.run(
        [str(ROOT / "scripts" / "install-codex.sh")],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "exists and is not a symlink" in result.stderr
    assert marker.read_text(encoding="utf-8") == "keep me"
