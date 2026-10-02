"""Tests for CW-AIP v2 evidence/decision validators."""

from __future__ import annotations

import importlib.util
import json
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


@pytest.mark.parametrize("approval", ["required", "pending", "denied"])
def test_decision_go_rejects_unresolved_or_denied_approval(approval):
    # Only "required" used to be checked, so a GO next to a denied approval passed.
    with pytest.raises(ValueError, match=f"human_approval={approval}"):
        decision.validate(_decision(verdict="GO", human_approval=approval))


@pytest.mark.parametrize("approval", ["not_required", "granted", None])
def test_decision_go_accepts_settled_approval(approval):
    data = _decision(verdict="GO", human_approval=approval)
    if approval is None:
        data.pop("human_approval")
    decision.validate(data)


@pytest.mark.parametrize("approval", ["pending", "denied"])
def test_decision_non_go_verdicts_may_wait_for_approval(approval):
    decision.validate(_decision(verdict="DEFER", human_approval=approval))


def test_decision_rejects_duplicate_gate_ids():
    # A CLEAR duplicate must not be able to shadow a BLOCK for the same gate.
    gates = [{"gate_id": "legal", "status": "BLOCK"}, {"gate_id": "legal", "status": "CLEAR"}]
    with pytest.raises(ValueError, match="duplicate gate_id: legal"):
        decision.validate(_decision(verdict="TEST", gates=gates))


def test_evidence_rejects_duplicate_source_ids():
    data = _evidence(sources=[{"source_id": "s1"}, {"source_id": "s1", "url": "https://example.com/other"}])
    with pytest.raises(ValueError, match="duplicate source_id: s1"):
        evidence.validate(data)


def test_evidence_rejects_duplicate_edge_ids():
    data = _evidence()
    data["evidence_edges"].append({**data["evidence_edges"][0], "direction": "CONTRADICT"})
    with pytest.raises(ValueError, match="duplicate edge_id: e1"):
        evidence.validate(data)


@pytest.mark.parametrize(
    "edge_change",
    [
        {"admission": "REJECTED"},
        {"admission": "CONTEXT_ONLY"},
        {"direction": "CONTEXT"},
        {"direction": "CONTRADICT"},
    ],
)
def test_evidence_verified_claim_needs_accepted_support(edge_change):
    data = _evidence()
    data["evidence_edges"][0].update(edge_change)
    with pytest.raises(ValueError, match="VERIFIED requires an ACCEPTED SUPPORT"):
        evidence.validate(data)


def test_evidence_verified_claim_without_any_edge_is_rejected():
    with pytest.raises(ValueError, match="VERIFIED requires"):
        evidence.validate(_evidence(evidence_edges=[]))


def test_evidence_unverified_claim_needs_no_edge():
    data = _evidence(evidence_edges=[], readiness="NOT_READY")
    data["material_claims"][0]["status"] = "UNKNOWN"
    evidence.validate(data)


@pytest.mark.parametrize("module", [evidence, decision], ids=["evidence", "decision"])
def test_cli_reports_failures_without_traceback(module, tmp_path, capsys):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    assert module.main([str(bad)]) == 1
    assert module.main([str(tmp_path / "absent.json")]) == 1
    assert module.main([]) == 2
    err = capsys.readouterr().err
    assert "FAIL: " in err and "cannot read" in err and "usage:" in err


def test_cli_accepts_wrapped_and_bare_payloads(tmp_path, capsys):
    bare = tmp_path / "bare.json"
    bare.write_text(json.dumps(_decision()), encoding="utf-8")
    wrapped = tmp_path / "wrapped.json"
    wrapped.write_text(json.dumps({"type": "DecisionEnvelope", "payload": _decision()}), encoding="utf-8")
    assert decision.main([str(bare)]) == 0
    assert decision.main([str(wrapped)]) == 0
    listed = tmp_path / "list.json"
    listed.write_text("[]", encoding="utf-8")
    assert decision.main([str(listed)]) == 1
    assert "payload must be an object" in capsys.readouterr().err


@pytest.mark.parametrize("module", [evidence, decision], ids=["evidence", "decision"])
@pytest.mark.parametrize("flag", ["-h", "--help"])
def test_help_flag_prints_usage_instead_of_reading_a_file(module, flag, capsys):
    assert module.main([flag]) == 0
    out, err = capsys.readouterr()
    assert out.startswith("usage: ") and not err
