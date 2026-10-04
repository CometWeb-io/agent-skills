"""Regression tests for longform publication admission gates."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_evals  # noqa: E402
from publication_kernel import infer_stage, validate_report  # noqa: E402


@pytest.fixture
def valid_report() -> dict:
    report, _ = run_evals.build_scenario("build_valid")
    return copy.deepcopy(report)


def test_stale_volatile_supporting_fact_is_rejected(valid_report: dict) -> None:
    valid_report["claim_uses"][0].update({
        "materiality": "SUPPORTING",
        "volatile_current": True,
    })
    valid_report["sources"][1]["freshness"] = "STALE"

    assert "VOLATILE_CLAIM_STALE_EVIDENCE" in validate_report(valid_report)


def test_empty_publication_evidence_record_cannot_infer_published(valid_report: dict) -> None:
    valid_report["current_stage"] = "PUBLISHED"
    valid_report["publication_evidence"] = [{}]

    errors = validate_report(valid_report)

    assert infer_stage(valid_report) == "RELEASE_READY"
    assert "PUBLISHED_WITHOUT_EVIDENCE" in errors
    assert "PUBLICATION_EVIDENCE_REQUIRED_FIELD_MISSING:type" in errors
    assert "PUBLICATION_EVIDENCE_REQUIRED_FIELD_MISSING:locator" in errors


def test_lifecycle_flags_require_strict_booleans(valid_report: dict) -> None:
    valid_report["lifecycle"]["release_ready"] = "true"

    errors = validate_report(valid_report)

    assert "FIELD_TYPE_INVALID:lifecycle.release_ready" in errors
    assert infer_stage(valid_report) == "FORMAT_READY"


@pytest.mark.parametrize("field", ("id", "system", "locator", "authorized", "freshness", "observed_at"))
def test_source_records_require_all_contract_fields(valid_report: dict, field: str) -> None:
    valid_report["sources"][0].pop(field)

    errors = validate_report(valid_report)

    assert f"SOURCE_REQUIRED_FIELD_MISSING:{field}" in errors
