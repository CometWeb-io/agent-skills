"""The front door must make incomplete sidecars visible to the user."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_incomplete_sidecar_requires_explicit_user_facing_disclosure():
    text = (ROOT / "SKILL.md").read_text()
    assert "NOT_CREATED" in text
    assert "NOT_VALIDATED" in text
    assert "reason" in text.lower()
    assert "do not claim" in text.lower()


def test_full_modes_and_readiness_are_not_sidecar_completion():
    text = (ROOT / "SKILL.md").read_text()
    for mode in ("STANDARD", "DEEP", "DELTA", "RELEASE"):
        assert mode in text
    assert "readiness" in text.lower() and "sidecar" in text.lower()
