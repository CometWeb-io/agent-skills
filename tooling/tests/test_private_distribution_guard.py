"""The private workflow must neither export private files nor mutate a public checkout."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]


def inventory(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*") if p.is_file()}


@pytest.mark.parametrize("arguments, expected", [([], 0), (["--skill", "ai-humanize"], 1),
                                               (["--skip-safety"], 2)])
def test_export_has_no_side_effects(tmp_path, arguments, expected):
    (tmp_path / "private-note.txt").write_text("Keep this file local.")
    before = inventory(tmp_path)
    result = subprocess.run([sys.executable, str(ROOT / "tooling/publish_public_dry_run.py"),
                             "--root", str(tmp_path), *arguments],
                            cwd=tmp_path, capture_output=True, text=True, timeout=10)
    assert result.returncode == expected, result.stderr
    assert inventory(tmp_path) == before
    assert not (tmp_path / "dist").exists()
    if expected != 2:
        report = json.loads(result.stdout)
        assert report["status"] == "disabled"
        assert report["published"] is False
        assert report["filesystem_modified"] is False


@pytest.mark.parametrize("arguments", [[], ["--apply"], ["--apply", "--skip-rebuild"]])
def test_sync_preserves_target(tmp_path, arguments):
    (tmp_path / "keep.txt").write_text("Unrelated work.")
    before = inventory(tmp_path)
    result = subprocess.run([sys.executable, str(ROOT / "tooling/sync_public_repo.py"),
                             "--public-root", str(tmp_path), *arguments],
                            cwd=tmp_path, capture_output=True, text=True, timeout=10)
    assert result.returncode == 1
    assert json.loads(result.stdout)["status"] == "disabled"
    assert inventory(tmp_path) == before


def test_sync_does_not_create_a_missing_target(tmp_path):
    target = tmp_path / "missing"
    result = subprocess.run([sys.executable, str(ROOT / "tooling/sync_public_repo.py"),
                             "--public-root", str(target), "--apply"],
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 1
    assert not target.exists()
