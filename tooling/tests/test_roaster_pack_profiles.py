"""select_review_packs.py accepts only the profiles its package's validator accepts."""
from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
# package -> the validator script whose PROFILES set is authoritative
PACKAGES = {
    "content-roaster": "validate_roast.py",
    "repo-roaster": "validate_repo_roast.py",
    "science-roaster": "validate_review.py",
}


def _run(skill: str, *args: str) -> subprocess.CompletedProcess[str]:
    script = ROOT / "skills" / skill / "scripts" / "select_review_packs.py"
    return subprocess.run([sys.executable, str(script), "--text", "Look at this draft", *args],
                          capture_output=True, text=True, check=False)


def _validator_profiles(skill: str) -> set[str]:
    source = (ROOT / "skills" / skill / "scripts" / PACKAGES[skill]).read_text(encoding="utf-8")
    line = next(row for row in source.splitlines() if row.startswith("PROFILES = "))
    return set(ast.literal_eval(line.split("=", 1)[1].strip()))


@pytest.mark.parametrize("skill", sorted(PACKAGES))
@pytest.mark.parametrize("profile", ["NOT_A_PROFILE", "landing_page", "full_repo", ""])
def test_profile_the_validator_rejects_is_refused(skill: str, profile: str) -> None:
    proc = _run(skill, "--profile", profile)
    assert proc.returncode != 0, proc.stdout
    assert "Traceback" not in proc.stderr
    assert "unknown profile" in proc.stderr


@pytest.mark.parametrize("skill", sorted(PACKAGES))
def test_every_validator_profile_is_accepted(skill: str) -> None:
    for profile in sorted(_validator_profiles(skill)):
        proc = _run(skill, "--profile", profile)
        assert proc.returncode == 0, (profile, proc.stderr)
        assert isinstance(json.loads(proc.stdout), list)


@pytest.mark.parametrize("skill", sorted(PACKAGES))
def test_pack_activation_profiles_are_validator_profiles(skill: str) -> None:
    allowed = _validator_profiles(skill)
    for pack in sorted((ROOT / "skills" / skill / "references" / "packs").glob("*.json")):
        profiles = json.loads(pack.read_text(encoding="utf-8")).get("activation", {}).get("profiles", [])
        assert set(profiles) <= allowed, (pack.name, sorted(set(profiles) - allowed))
