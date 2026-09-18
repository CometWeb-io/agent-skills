import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _context_fixtures import load_script, build_valid_envelope as valid_envelope

import pytest

module = load_script("validate_context_envelope")


def test_valid_envelope():
    module.validate(valid_envelope())


def test_unknown_fact_source_fails():
    data = valid_envelope()
    data["facts"][0]["source_ids"] = ["missing"]
    with pytest.raises(ValueError, match="unknown source_ids"):
        module.validate(data)


def test_duplicate_source_id_fails():
    data = valid_envelope()
    data["sources"].append(dict(data["sources"][0]))
    with pytest.raises(ValueError, match="duplicate source_id"):
        module.validate(data)


def test_delta_requires_baseline_state():
    data = valid_envelope()
    data["mode"] = "delta"
    data["baseline"] = {"status": "not_requested", "ref": None}
    with pytest.raises(ValueError, match="delta mode requires"):
        module.validate(data)


def test_required_first_principles_cannot_be_not_required():
    data = valid_envelope()
    data["governance"]["first_principles"]["status"] = "not_required"
    with pytest.raises(ValueError, match="required First Principles"):
        module.validate(data)
