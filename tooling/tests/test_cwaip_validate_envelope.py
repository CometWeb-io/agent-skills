"""Tests for universal CW-AIP v2 envelope validator."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load():
    path = ROOT / "validate_envelope.py"
    spec = importlib.util.spec_from_file_location("validate_envelope", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


mod = _load()


def _evidence_payload():
    return {
        "schema": "cometweb.evidence/v2",
        "research_contract": "pricing",
        "mode": "QUICK",
        "as_of": "2026-09-08T12:00:00Z",
        "material_claims": [
            {
                "claim_id": "c1",
                "text": "x",
                "epistemic_kind": "FACT",
                "status": "VERIFIED",
                "materiality": "supporting",
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


def test_full_envelope_ok():
    payload = _evidence_payload()
    digest = mod.payload_hash(payload)
    envelope = {
        "id": "ev-1",
        "type": "EvidenceEnvelope",
        "producer": "evidence-researcher",
        "producer_version": "1.0.2",
        "protocol_version": "2.0",
        "subject": "pricing",
        "generated_at": "2026-09-08T12:00:00Z",
        "as_of": "2026-09-08T12:00:00Z",
        "sensitivity": "internal",
        "dependencies": [],
        "payload": payload,
        "payload_hash": digest,
    }
    mod.validate_envelope(envelope, final=True)


def test_final_rejects_pending_hash():
    payload = _evidence_payload()
    envelope = {
        "id": "ev-1",
        "type": "EvidenceEnvelope",
        "producer": "evidence-researcher",
        "producer_version": "1.0.2",
        "protocol_version": "2.0",
        "subject": "pricing",
        "generated_at": "2026-09-08T12:00:00Z",
        "as_of": "2026-09-08T12:00:00Z",
        "sensitivity": "internal",
        "dependencies": [],
        "payload": payload,
        "payload_hash": "pending",
    }
    with pytest.raises(ValueError):
        mod.validate_envelope(envelope, final=True)


def test_rejects_bad_core_protocol():
    payload = _evidence_payload()
    envelope = {
        "id": "ev-1",
        "type": "EvidenceEnvelope",
        "producer": "evidence-researcher",
        "producer_version": "1.0.2",
        "protocol_version": "nonsense",
        "subject": "pricing",
        "generated_at": "2026-09-08T12:00:00Z",
        "as_of": "2026-09-08T12:00:00Z",
        "sensitivity": "internal",
        "dependencies": [],
        "payload": payload,
        "payload_hash": mod.payload_hash(payload),
    }
    with pytest.raises(ValueError):
        mod.validate_envelope(envelope)
