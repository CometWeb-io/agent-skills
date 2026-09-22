"""Eval data a skill ships has to be read by something.

test_skill_eval_harnesses.py runs the packages that carry a
scripts/run_evals.py. Other eval files ship without one, and two of them —
competitive-intelligence's and design-partner-finder's behavioural suites — were
read by nothing at all. That is how they drifted to different shapes: one spells
the expectation key `expect`, the other spelled it `expected`, and no run would
ever have disagreed with either.

Each unharnessed file names the gated thing that covers it. Declared explicitly
rather than matched by filename, so a genuinely unread file cannot hide among
them.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HARNESS = "scripts/run_evals.py"
VALIDATOR = "scripts/validate_evals.py"

COVERED_ELSEWHERE = {
    ("ai-humanize", "evaluation/redteam-cases.json"):
        "skills/ai-humanize/tests/test_redteam_score_regressions.py",
    ("ebook-publisher", "evaluation/cases.json"):
        "skills/ebook-publisher/tests/test_ebook_check.py",
    ("competitive-intelligence", "evals/evals.json"):
        "tooling/tests/test_model_eval_suites.py",
    ("design-partner-finder", "evals/evals.json"):
        "tooling/tests/test_model_eval_suites.py",
}


def packages() -> list[Path]:
    return sorted(p.parent for p in ROOT.glob("skills/*/SKILL.md"))


def eval_files(package: Path) -> list[str]:
    found: list[str] = []
    for directory in ("evals", "evaluation"):
        base = package / directory
        if base.is_dir():
            found += sorted(p.relative_to(package).as_posix() for p in base.rglob("*.json"))
    return found


@pytest.mark.parametrize("package", packages(), ids=lambda p: p.name)
def test_every_eval_file_is_read_by_something(package: Path) -> None:
    if (package / HARNESS).is_file():
        return  # test_skill_eval_harnesses.py runs it
    if (package / VALIDATOR).is_file():
        return  # test_roaster_eval_validators.py runs it
    orphans = [
        relative for relative in eval_files(package)
        if (package.name, relative) not in COVERED_ELSEWHERE
    ]
    assert not orphans, (
        f"{package.name} ships {orphans} with no {HARNESS} or {VALIDATOR} and no declared cover. "
        f"Add the harness, or list the file in COVERED_ELSEWHERE with the gated "
        f"test that reads it."
    )


@pytest.mark.parametrize("entry", sorted(COVERED_ELSEWHERE), ids=lambda e: f"{e[0]}/{e[1]}")
def test_declared_cover_still_describes_reality(entry: tuple[str, str]) -> None:
    """Stop the declaration list from outliving the files it excuses."""
    skill, relative = entry
    package = ROOT / "skills" / skill
    assert (package / relative).is_file(), f"{skill}/{relative} no longer exists"
    assert not (package / HARNESS).is_file(), (
        f"{skill} now ships {HARNESS}, so the harness test covers it; drop the declaration"
    )
    cover = COVERED_ELSEWHERE[entry]
    assert (ROOT / cover).is_file(), f"{skill}/{relative} names a missing cover: {cover}"


@pytest.mark.parametrize("skill", ["content-roaster", "repo-roaster", "science-roaster"])
def test_roaster_eval_validator_passes(skill: str) -> None:
    package = ROOT / "skills" / skill
    proc = subprocess.run(
        [sys.executable, VALIDATOR], cwd=package, capture_output=True, text=True, timeout=120
    )
    assert proc.returncode == 0, f"{skill} eval validator failed:\n{proc.stdout}\n{proc.stderr}"
