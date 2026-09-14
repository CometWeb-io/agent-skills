"""Publication tooling must never mutate anything it was only asked to inspect."""
from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]


def inventory(root: Path) -> dict[str, str]:
    return {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in root.rglob("*")
        if p.is_file()
    }


def run(script: str, *arguments: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(ROOT / "tooling" / script), *arguments],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=30,
    )


@pytest.mark.parametrize(
    "arguments, expected",
    [([], 1), (["--skill", "ai-humanize"], 1), (["--skip-safety"], 2)],
)
def test_export_has_no_side_effects(tmp_path, arguments, expected):
    (tmp_path / "private-note.txt").write_text("Keep this file local.")
    before = inventory(tmp_path)
    result = run(
        "publish_public_dry_run.py", "--root", str(tmp_path), *arguments, cwd=tmp_path
    )
    # Unapproved export exits 1; an attempt to bypass the safety scan is not a
    # recognized option at all and exits 2.
    assert result.returncode == expected, result.stderr
    assert inventory(tmp_path) == before
    assert not (tmp_path / "dist").exists()
