"""Tests for CW-AIP v2 evidence/decision validators."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str):
    path = ROOT / name
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


evidence = _load("validate_evidence_envelope.py")
decision = _load("validate_decision_envelope.py")


def _evidence(**overrides):
    data = {
        "schema": "cometweb.evidence/v2",
        "research_contract": "pricing claims",
        "mode": "STANDARD",
        "as_of": "2026-09-08T12:00:00Z",
        "material_claims": [
            {
                "claim_id": "c1",
                "text": "Growth is 299 PLN",
                "epistemic_kind": "FACT",
                "status": "VERIFIED",
                "materiality": "critical",
            }
        ],
        "sources": [{"source_id": "s1"}],
        "evidence_edges": [
            {
                "edge_id": "e1",
                "claim_id": "c1",
                "source_id": "s1",
                "direction": "SUPPORT",
                "admission": "ACCEPTED",
            }
        ],
        "gaps": [],
        "contradictions": [],
        "readiness": "READY",
        "evidence_pack_hash": "abc",
    }
    data.update(overrides)
    return data


def _decision(**overrides):
    data = {
        "schema": "cometweb.decision/v2",
        "decision_question": "Raise Growth price?",
        "profile": "LIGHT",
        "as_of": "2026-09-08T12:00:00Z",
        "verdict": "TEST",
        "option": "A/B +10%",
        "gates": [{"gate_id": "legal", "status": "CLEAR"}],
        "blockers": [],
        "controls": ["cap exposure"],
        "evidence_deps": ["ev-1"],
        "snapshot_hash": "snap",
        "human_approval": "not_required",
    }
    data.update(overrides)
    return data


def test_evidence_valid():
    evidence.validate(_evidence())


def test_evidence_rejects_verified_inference():
    data = _evidence(
        material_claims=[
            {
                "claim_id": "c1",
                "text": "inferred",
                "epistemic_kind": "INFERENCE",
                "status": "VERIFIED",
                "materiality": "material",
            }
        ]
    )
    with pytest.raises(ValueError):
        evidence.validate(data)


def test_evidence_rejects_unknown_edge_source():
    data = _evidence()
    data["evidence_edges"][0]["source_id"] = "missing"
    with pytest.raises(ValueError):
        evidence.validate(data)


def test_decision_valid():
    decision.validate(_decision())


def test_decision_go_blocked_by_gate():
    with pytest.raises(ValueError):
        decision.validate(
            _decision(verdict="GO", gates=[{"gate_id": "legal", "status": "BLOCK"}])
        )


def test_decision_go_with_blockers_fails():
    with pytest.raises(ValueError):
        decision.validate(_decision(verdict="GO", blockers=["missing evidence"]))
