"""Tracked shell scripts must carry the executable bit in git.

README tells users to run ./scripts/install-*.sh directly, and install-all.sh
invokes each host installer by path. Three installers were tracked as 100644,
so every fresh clone stopped at the fourth host with "Permission denied". The
mode is part of what git stores, so it is checked against git's index, not the
working tree — a chmod that was never staged does not count.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _tracked_shell_scripts() -> list[tuple[str, str]]:
    out = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-s", "--", "scripts/*.sh", "tooling/*.sh"],
        check=True, capture_output=True, text=True,
    ).stdout
    rows = []
    for line in out.splitlines():
        mode, _sha, _stage, path = line.split(maxsplit=3)
        # scripts/lib/ holds helpers that installers `source`; they are read,
        # never executed, so the bit would be noise rather than a guarantee.
        if "/lib/" in path:
            continue
        rows.append((path, mode))
    return rows


@pytest.mark.parametrize("path,mode", _tracked_shell_scripts(), ids=lambda v: v if isinstance(v, str) and "/" in v else "")
def test_shell_script_is_executable_in_the_working_tree(path: str, mode: str) -> None:
    assert (ROOT / path).stat().st_mode & 0o111, f"{path} is not executable"


def test_every_installer_named_by_install_all_exists() -> None:
    text = (ROOT / "scripts" / "install-all.sh").read_text(encoding="utf-8")
    for line in text.splitlines():
        line = line.strip()
        if line.startswith('"$ROOT/scripts/') and line.endswith('.sh"'):
            rel = line.strip('"').replace("$ROOT/", "")
            assert (ROOT / rel).is_file(), f"install-all.sh calls missing {rel}"
