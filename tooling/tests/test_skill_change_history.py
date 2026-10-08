"""Pin package identity/history checks without needing any model behavior."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import skill_change_history as history  # noqa: E402
from skill_change_history import check_package  # noqa: E402


@pytest.mark.parametrize("version,history,old,behavioral,expected", [
    ("1.0.0", "## [1.0.0]\nOriginal\n", "1.0.0", True, "newer package VERSION"),
    ("1.0.1", "## [1.0.0]\nOriginal\n", "1.0.0", True, "must describe VERSION"),
    ("1.0.1", "## [1.0.1]\nNew\n", "1.0.0", True, None),
    ("1.0.0", "## [1.0.0]\nOriginal\n", "1.0.0", False, None),
    ("0.1.0", "", None, True, "must describe VERSION"),
    ("0.1.0", "## [0.1.0]\nAdded\n", None, True, None),
])
def test_behavior_change_requires_version_and_matching_history(tmp_path, version, history, old, behavioral, expected):
    (tmp_path / "VERSION").write_text(version)
    (tmp_path / "CHANGELOG.md").write_text(history)
    errors = check_package(tmp_path, old, "## [1.0.0]\nOriginal\n", behavioral)
    if expected is None:
        assert not errors
    else:
        assert any(expected in error for error in errors)


def test_preexisting_entry_does_not_replace_updated_change_history(tmp_path):
    (tmp_path / "VERSION").write_text("1.0.1")
    history = "## [1.0.1]\nPreviously planned\n"
    (tmp_path / "CHANGELOG.md").write_text(history)
    assert any("changed CHANGELOG" in error for error in check_package(tmp_path, "1.0.0", history, True))


def test_missing_merge_base_never_reports_success(tmp_path, monkeypatch):
    monkeypatch.setattr(history, "merge_base", lambda *args: None)
    assert history.main(["--check", "--root", str(tmp_path), "--require-base"]) == 1


def test_invalid_version_is_rejected_even_for_new_package(tmp_path):
    (tmp_path / "VERSION").write_text("invalid")
    (tmp_path / "CHANGELOG.md").write_text("## invalid")
    with pytest.raises(history.ReleaseError):
        check_package(tmp_path, None, "", True)
