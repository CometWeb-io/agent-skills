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


