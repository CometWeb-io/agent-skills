"""Commands a SKILL.md shows must be runnable.

A skill file is copied from, not read around: an agent runs what it sees. So
every `scripts/*.py` named in a fenced bash block has to exist and answer
`--help` without falling over. cometweb-context's envelope validator did not —
it read `--help` as a filename and reported "INVALID: No such file" — which is
the sort of thing nobody notices until someone types the universal flag.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_REF = re.compile(r"(scripts/[\w./-]+\.py)")


def documented_scripts() -> list[tuple[str, str]]:
    found: set[tuple[str, str]] = set()
    for skill_md in sorted(ROOT.glob("skills/*/SKILL.md")):
        skill = skill_md.parent.name
        for block in re.findall(r"```bash\n(.*?)```", skill_md.read_text(encoding="utf-8"), re.S):
            for match in SCRIPT_REF.finditer(block):
                found.add((skill, match.group(1)))
    return sorted(found)


@pytest.mark.parametrize("skill,script", documented_scripts(), ids=lambda v: v)
def test_documented_script_exists(skill: str, script: str) -> None:
    assert (ROOT / "skills" / skill / script).is_file(), f"{skill}/SKILL.md documents a missing {script}"


@pytest.mark.parametrize("skill,script", documented_scripts(), ids=lambda v: v)
def test_documented_script_answers_help(skill: str, script: str) -> None:
    proc = subprocess.run(
        [sys.executable, script, "--help"],
        cwd=ROOT / "skills" / skill,
        capture_output=True, text=True, timeout=120,
    )
    output = (proc.stdout + proc.stderr).strip()
    assert proc.returncode == 0, f"{skill}/{script} --help exited {proc.returncode}: {output[:200]}"
    assert "usage" in output.lower(), f"{skill}/{script} --help printed no usage line: {output[:200]}"


def test_the_sweep_actually_found_scripts() -> None:
    # A regex that silently stops matching would turn this file into a no-op.
    scripts = documented_scripts()
    assert len(scripts) >= 15, f"only {len(scripts)} documented scripts found; check the extraction"
