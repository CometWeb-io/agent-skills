"""A front door has to be followable as written.

An executing model reads SKILL.md first and often nothing else until a line
tells it to. Three defects make that first read misleading even when every
other gate is green:

- A backticked token the package never defines anywhere else. content-writer
  told the writer to choose `EVIDENCE_BACKED` while its kernel only accepts
  `EVIDENCE_REQUIRED`, and feedback-integrator offered a `RUNTIME` root layer
  its kernel rejects. A value that exists only in the front door is either a
  typo or a contract nothing enforces.
- A reference file SKILL.md never names. Nothing will ever load it, so the
  rules inside it are dead.
- One sentence that says to read three or more references at once. It gives no
  trigger, so a model either loads everything up front or guesses; a table or
  list that says when each file is needed does neither.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
FRONT_DOORS = sorted(ROOT.glob("skills/*/SKILL.md"))

TOKEN = re.compile(r"`([A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*)`")

# Values defined by the front door itself and not used anywhere else in the
# package. Each entry names its skill so it cannot excuse the same word in
# another package.
FRONT_DOOR_ONLY = {
    # Run modes: chosen by the model, never written into a kernel payload.
    ("competitive-intelligence", "CLAIM_CHECK"),
    ("competitive-intelligence", "DELTA"),
    ("competitive-intelligence", "EXEC_BRIEF"),
}

SKIPPED_PARTS = {"tests", "__pycache__"}


def _package_text(skill_dir: Path) -> str:
    chunks = []
    for path in sorted(skill_dir.rglob("*")):
        if not path.is_file() or path.name in {"SKILL.md", "CHANGELOG.md"}:
            continue
        if SKIPPED_PARTS.intersection(path.relative_to(skill_dir).parts):
            continue
        try:
            chunks.append(path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, OSError):
            continue
    return "\n".join(chunks)


def _paragraphs(text: str) -> list[str]:
    paragraphs, current = [], []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "```", "|", "-", "*")) or re.match(r"\d+\.\s", stripped):
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        current.append(stripped)
    if current:
        paragraphs.append(" ".join(current))
    return paragraphs


def test_front_doors_are_found() -> None:
    assert len(FRONT_DOORS) >= 30


@pytest.mark.parametrize("doc", FRONT_DOORS, ids=lambda p: p.parent.name)
def test_every_front_door_token_is_defined_in_the_package(doc: Path) -> None:
    skill = doc.parent.name
    package = _package_text(doc.parent)
    unknown = sorted(
        token
        for token in set(TOKEN.findall(doc.read_text(encoding="utf-8")))
        if (skill, token) not in FRONT_DOOR_ONLY and not re.search(rf"\b{token}\b", package)
    )
    assert not unknown, (
        f"{skill}/SKILL.md names {unknown}, which no reference, script or contract in the "
        "package defines; use the value the kernel accepts"
    )


def test_front_door_only_entries_are_still_relevant() -> None:
    for skill, token in sorted(FRONT_DOOR_ONLY):
        doc = ROOT / "skills" / skill / "SKILL.md"
        assert f"`{token}`" in doc.read_text(encoding="utf-8"), f"drop ({skill}, {token}) from FRONT_DOOR_ONLY"
        assert not re.search(rf"\b{token}\b", _package_text(doc.parent)), (
            f"{token} is now defined in {skill}'s package; drop it from FRONT_DOOR_ONLY"
        )


@pytest.mark.parametrize("doc", FRONT_DOORS, ids=lambda p: p.parent.name)
def test_every_reference_is_named_by_the_front_door(doc: Path) -> None:
    references = doc.parent / "references"
    if not references.is_dir():
        pytest.skip("no references/")
    text = doc.read_text(encoding="utf-8")
    orphans = sorted(path.name for path in references.glob("*.md") if path.name not in text)
    assert not orphans, f"{doc.parent.name}/SKILL.md never names {orphans}; nothing will load them"


TRIGGER = re.compile(r"\b(when|whenever|before|after|if|for|while|only)\b", re.IGNORECASE)
REFERENCE = re.compile(r"`?references/[\w.-]+`?")


def _untriggered(sentence: str) -> int:
    """References in a sentence whose own clause says nothing about when to read them."""
    tails = REFERENCE.split(sentence)[1:]
    return sum(1 for tail in tails if not TRIGGER.search(tail))


@pytest.mark.parametrize("doc", FRONT_DOORS, ids=lambda p: p.parent.name)
def test_no_sentence_loads_three_references_without_a_trigger(doc: Path) -> None:
    bulk = [
        sentence[:100]
        for paragraph in _paragraphs(doc.read_text(encoding="utf-8"))
        for sentence in re.split(r"(?<=[.!?])\s+(?=[A-Z])", paragraph)
        if sentence.startswith("Read ")
        and len(REFERENCE.findall(sentence)) >= 3
        and _untriggered(sentence) >= 2
    ]
    assert not bulk, (
        f"{doc.parent.name}/SKILL.md loads several references in one sentence: {bulk}; "
        "say when each one is needed"
    )
