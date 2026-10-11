"""Both independently installed prose packages must ship the same counting rule."""
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("resource", ["scripts/word_range.py", "references/word-range.md"])
def test_standalone_word_range_resources_match(resource):
    canonical = ROOT / "skills/content-writer" / resource
    deployed = ROOT / "skills/ai-humanize" / resource
    assert canonical.read_bytes() == deployed.read_bytes()
