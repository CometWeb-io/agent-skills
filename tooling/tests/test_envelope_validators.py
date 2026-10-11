"""Tests for CW-AIP v2 evidence/decision validators."""

from __future__ import annotations

import builtins
import importlib.util
import json
from pathlib import Path

import pytest

import grade_output

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
full_evidence = _load("validate_envelope.py")


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


PATHS = ["direct", "direct-fallback", "full", "full-fallback", "grader"]


def _check_evidence_path(payload, path, monkeypatch):
    if path.endswith("fallback"):
        original = builtins.__import__

        def without_jsonschema(name, *args, **kwargs):
            if name == "jsonschema" or name.startswith("jsonschema."):
                raise ImportError("test standard-library validation")
            return original(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", without_jsonschema)
    if path.startswith("direct"):
        evidence.validate(payload)
        return
    envelope = json.loads((ROOT.parent / "fixtures/cwaip-v2/evidence-final.json").read_text())
    envelope["payload"] = payload
    envelope["payload_hash"] = full_evidence.payload_hash(payload)
    if path == "grader":
        errors = grade_output.envelope_errors(envelope)
        if errors:
            raise ValueError("; ".join(errors))
    else:
        full_evidence.validate_envelope(envelope, final=True)


@pytest.mark.parametrize("path", PATHS)
@pytest.mark.parametrize("levels", [{"severity": "critical"}, {"materiality": "material"},
                                     {"severity": "supporting", "materiality": "critical"}])
@pytest.mark.parametrize("states", [{"resolution": "UNRESOLVED"}, {"status": "unresolved"},
                                     {"resolution": "UNRESOLVED", "status": "resolved"},
                                     {"resolution": "RESOLVED_SCOPE", "status": "unresolved"}])
def test_ready_rejects_either_declared_unresolved_state(path, levels, states, monkeypatch):
    payload = _evidence(contradictions=[{"claim_id": "c1", **levels, **states}])
    with pytest.raises(ValueError, match="unresolved material contradictions"):
        _check_evidence_path(payload, path, monkeypatch)


@pytest.mark.parametrize("path", PATHS)
@pytest.mark.parametrize("record_claim", [None, "c2", "unknown"])
def test_accepted_contradict_requires_record_for_same_known_claim(path, record_claim, monkeypatch):
    payload = _evidence()
    payload["material_claims"].append({**payload["material_claims"][0], "claim_id": "c2", "status": "UNKNOWN", "materiality": "supporting"})
    payload["evidence_edges"].append({**payload["evidence_edges"][0], "edge_id": "e2", "direction": "CONTRADICT"})
    if record_claim is not None:
        payload["contradictions"] = [{"claim_id": record_claim, "resolution": "RESOLVED_METHOD", "severity": "critical"}]
    with pytest.raises(ValueError, match="contradiction record|unknown claim_id"):
        _check_evidence_path(payload, path, monkeypatch)


@pytest.mark.parametrize("path", PATHS)
@pytest.mark.parametrize("row", [
    {"claim_id": "c1"},
    {"claim_id": "c1", "resolution": [] , "severity": "critical"},
    {"claim_id": "c1", "resolution": "UNKNOWN", "severity": "critical"},
    {"claim_id": "c1", "status": "resolved", "materiality": {}},
])
def test_partial_or_malformed_record_cannot_clear_contradict(path, row, monkeypatch):
    payload = _evidence(contradictions=[row])
    payload["evidence_edges"].append({**payload["evidence_edges"][0], "edge_id": "e2", "direction": "CONTRADICT"})
    with pytest.raises(ValueError):
        _check_evidence_path(payload, path, monkeypatch)


@pytest.mark.parametrize("path", PATHS)
@pytest.mark.parametrize("admission", ["REJECTED", "CONTEXT_ONLY"])
def test_inadmissible_contradict_needs_no_record(path, admission, monkeypatch):
    payload = _evidence()
    payload["evidence_edges"].append({**payload["evidence_edges"][0], "edge_id": "e2", "direction": "CONTRADICT", "admission": admission})
    _check_evidence_path(payload, path, monkeypatch)


@pytest.mark.parametrize("path", PATHS)
@pytest.mark.parametrize("state", ["RESOLVED_SCOPE", "RESOLVED_TIME", "RESOLVED_DEFINITION",
                                    "RESOLVED_METHOD", "RESOLVED_SUPERSEDED", "RESOLVED_AUTHORITY", "resolved"])
def test_declared_resolved_same_claim_record_is_admitted(path, state, monkeypatch):
    row = {"claim_id": "c1", "severity": "critical", "resolution": state}
    if state == "resolved":
        row = {"claim_id": "c1", "materiality": "critical", "status": state}
    payload = _evidence(contradictions=[row])
    payload["evidence_edges"].append({**payload["evidence_edges"][0], "edge_id": "e2", "direction": "CONTRADICT"})
    _check_evidence_path(payload, path, monkeypatch)


@pytest.mark.parametrize("path", PATHS)
@pytest.mark.parametrize("readiness", ["DEFER", "NOT_READY"])
def test_nonready_can_retain_declared_unresolved_contradiction(path, readiness, monkeypatch):
    payload = _evidence(readiness=readiness, contradictions=[{"claim_id": "c1", "resolution": "UNRESOLVED", "severity": "critical"}])
    _check_evidence_path(payload, path, monkeypatch)


@pytest.mark.parametrize("path", PATHS)
@pytest.mark.parametrize("materiality", ["critical", "material"])
@pytest.mark.parametrize("status", ["UNKNOWN", "PARTIAL", "UNSUPPORTED", "CONTRADICTED", "SUPPORTED_INFERENCE", "UNVERIFIED"])
@pytest.mark.parametrize("has_support", [False, True])
def test_ready_rejects_unverified_material_fact(path, materiality, status, has_support, monkeypatch):
    payload = _evidence()
    payload["material_claims"][0].update(materiality=materiality, status=status)
    if not has_support:
        payload["evidence_edges"] = []
    with pytest.raises(ValueError):
        _check_evidence_path(payload, path, monkeypatch)


@pytest.mark.parametrize("path", PATHS)
@pytest.mark.parametrize("readiness", ["NOT_READY", "DEFER"])
def test_nonready_retains_unverified_material_fact_without_support(path, readiness, monkeypatch):
    payload = _evidence(readiness=readiness, evidence_edges=[])
    payload["material_claims"][0]["status"] = "UNKNOWN"
    _check_evidence_path(payload, path, monkeypatch)


@pytest.mark.parametrize("path", PATHS)
def test_ready_can_retain_an_unknown_supporting_claim(path, monkeypatch):
    payload = _evidence()
    payload["material_claims"].append({**payload["material_claims"][0], "claim_id": "c2",
                                        "materiality": "supporting", "status": "UNKNOWN"})
    _check_evidence_path(payload, path, monkeypatch)


@pytest.mark.parametrize("path", PATHS)
@pytest.mark.parametrize("materiality", ["critical", "material"])
@pytest.mark.parametrize("status", ["UNKNOWN", "PARTIAL", "UNSUPPORTED", "CONTRADICTED", "UNVERIFIED"])
@pytest.mark.parametrize("has_support", [False, True])
def test_ready_rejects_unassessed_material_inference(path, materiality, status, has_support, monkeypatch):
    payload = _evidence()
    payload["material_claims"][0].update(epistemic_kind="INFERENCE", materiality=materiality, status=status)
    if not has_support:
        payload["evidence_edges"] = []
    with pytest.raises(ValueError):
        _check_evidence_path(payload, path, monkeypatch)


@pytest.mark.parametrize("path", PATHS)
@pytest.mark.parametrize("status", ["SUPPORTED", "SUPPORTED_INFERENCE"])
def test_ready_preserves_declared_supported_material_inference(path, status, monkeypatch):
    payload = _evidence()
    payload["material_claims"][0].update(epistemic_kind="INFERENCE", status=status)
    _check_evidence_path(payload, path, monkeypatch)


@pytest.mark.parametrize("path", PATHS)
@pytest.mark.parametrize("readiness", ["NOT_READY", "DEFER"])
def test_nonready_preserves_unknown_material_inference(path, readiness, monkeypatch):
    payload = _evidence(readiness=readiness, evidence_edges=[])
    payload["material_claims"][0].update(epistemic_kind="INFERENCE", status="UNKNOWN")
    _check_evidence_path(payload, path, monkeypatch)
