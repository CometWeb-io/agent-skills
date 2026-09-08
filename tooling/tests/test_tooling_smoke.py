"""Smoke tests for repo tooling."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

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
