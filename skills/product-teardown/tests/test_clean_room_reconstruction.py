"""Regression tests for clean-room reconstruction controls."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


recon = load_module("validate_recon_map", ROOT / "scripts" / "validate_recon_map.py")
matrix = load_module("feature_matrix", ROOT / "scripts" / "feature_matrix.py")


def reconstruction_map() -> dict:
    return {
        "schema_version": "cometweb.reconstruction-map/v1",
        "source": {
            "name": "Reference app",
            "kind": "web_app",
            "ref": "https://example.invalid",
            "version": "observed-2026-10-04",
            "observed_at": "2026-10-04T00:00:00+02:00",
        },
        "destination": {
            "name": "CometWeb target",
            "kind": "repo_product",
            "ref": "working-tree",
            "version": "current",
            "observed_at": "2026-10-04T00:00:00+02:00",
        },
        "boundaries": {
            "allowed": ["public behavior", "mechanism-level adaptation"],
            "prohibited": ["private endpoints", "credentials", "proprietary data"],
            "default_transfer_mode": "REIMPLEMENT",
        },
        "evidence": [
            {
                "id": "E1",
                "subject": "source",
                "source": "reference app",
                "locator": "settings flow",
                "note": "The source exposes a recoverable state.",
                "claim_state": "OBSERVED",
                "confidence": 0.9,
            },
            {
                "id": "E2",
                "subject": "destination",
                "source": "target support notes",
                "locator": "recovery issue",
                "note": "The target has the corresponding problem.",
                "claim_state": "OBSERVED",
                "confidence": 0.8,
            },
        ],
        "screens": [{
            "id": "S1",
            "name": "Settings",
            "states": ["loading", "ready", "error"],
            "evidence_ids": ["E1"],
        }],
        "flows": [{
            "id": "F1",
            "name": "Recover an action",
            "steps": ["trigger", "recover", "confirm"],
            "evidence_ids": ["E1", "E2"],
        }],
        "features": [{
            "id": "FEAT1",
            "name": "Recoverable action",
            "priority": "must",
            "status": "done",
            "source_evidence_ids": ["E1"],
            "target_evidence_ids": ["E2"],
        }],
        "unknowns": ["Whether the recovery window needs a feature flag."],
    }


def evidence_rows() -> list[dict]:
    return [
        {"id": "E1", "subject": "source", "source": "reference", "locator": "flow"},
        {"id": "E2", "subject": "destination", "source": "target", "locator": "flow"},
        {"id": "E3", "subject": "source", "source": "reference", "locator": "screen"},
        {"id": "E4", "subject": "destination", "source": "target", "locator": "screen"},
        {"id": "E5", "subject": "source", "source": "reference", "locator": "scope"},
    ]


def feature_matrix() -> dict:
    return {
        "schema_version": "cometweb.feature-matrix/v1",
        "evidence": evidence_rows(),
        "features": [
            {
                "id": "F1",
                "name": "Must feature",
                "priority": "must",
                "status": "done",
                "source_evidence_ids": ["E1"],
                "target_evidence_ids": ["E2"],
            },
            {
                "id": "F2",
                "name": "Should feature",
                "priority": "should",
                "status": "partial",
                "source_evidence_ids": ["E3"],
                "target_evidence_ids": ["E4"],
            },
            {
                "id": "F3",
                "name": "Explicit cut",
                "priority": "could",
                "status": "skip",
                "source_evidence_ids": ["E5"],
                "target_evidence_ids": [],
                "scope_reason": "Outside the declared first slice.",
            },
        ],
    }


def test_reconstruction_map_accepts_valid_source_and_target_lanes():
    assert recon.validate(reconstruction_map()) == []


@pytest.mark.parametrize("mutation", [
    lambda payload: payload["features"][0].update(target_evidence_ids=["E1"]),
    lambda payload: payload["flows"][0].update(evidence_ids=["E404"]),
    lambda payload: payload["boundaries"].update(prohibited=["assets"]),
])
def test_reconstruction_map_rejects_boundary_or_evidence_drift(mutation):
    payload = reconstruction_map()
    mutation(payload)
    assert recon.validate(payload)


def test_feature_matrix_scores_only_evidence_linked_rows():
    payload = feature_matrix()
    assert matrix.validate(payload) == []
    result = matrix.score_matrix(payload)
    assert result["weighted_denominator"] == 5
    assert result["weighted_numerator"] == 4.0
    assert result["score"] == 0.8
    assert result["skipped_count"] == 1


@pytest.mark.parametrize("target_refs", [[], ["E404"], ["E1"]])
def test_feature_matrix_rejects_unproven_target_evidence(target_refs):
    payload = feature_matrix()
    payload["features"][0]["target_evidence_ids"] = target_refs
    assert matrix.validate(payload)
