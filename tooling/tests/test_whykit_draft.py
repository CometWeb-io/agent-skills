"""Behavior tests for the explicit CW-AIP v2 to WhyKit draft boundary."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tooling" / "whykit_draft.py"


def _load():
    spec = importlib.util.spec_from_file_location("whykit_draft", TOOL)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _hash(payload: dict) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(encoded.encode()).hexdigest()


def _wrap(kind: str, payload: dict, *, subject: str = "Release readiness") -> dict:
    return {
        "id": "run-2026-09-19",
        "type": kind,
        "producer": "product-operator",
        "producer_version": "2.2",
        "protocol_version": "2.0",
        "subject": subject,
        "generated_at": "2026-09-19T12:30:00Z",
        "as_of": "2026-09-19T12:00:00Z",
        "sensitivity": "internal",
        "dependencies": ["pack-17"],
        "payload": payload,
        "payload_hash": _hash(payload),
    }


def _evidence_envelope() -> dict:
    payload = {
        "schema": "cometweb.evidence/v2",
        "research_contract": "Can the release candidate ship?",
        "mode": "STANDARD",
        "as_of": "2026-09-19T12:00:00Z",
        "material_claims": [
            {
                "claim_id": "C-1",
                "text": "The deterministic validation suite passes.",
                "epistemic_kind": "FACT",
                "status": "VERIFIED",
                "materiality": "material",
            }
        ],
        "sources": [
            {
                "source_id": "S-1",
                "title": "Validation report",
                "location": "reports/validation.json",
            }
        ],
        "evidence_edges": [
            {
                "edge_id": "edge-1",
                "claim_id": "C-1",
                "source_id": "S-1",
                "direction": "SUPPORT",
                "admission": "ACCEPTED",
            }
        ],
        "gaps": [{"gap_id": "G-1", "description": "Release approval is pending", "blocking": False}],
        "contradictions": [],
        "readiness": "READY",
        "evidence_pack_hash": "sha256:" + "a" * 64,
    }
    return _wrap("EvidenceEnvelope", payload)


def _decision_envelope() -> dict:
    payload = {
        "schema": "cometweb.decision/v2",
        "decision_question": "Should the candidate be released?",
        "profile": "STANDARD",
        "as_of": "2026-09-19T12:00:00Z",
        "verdict": "TEST",
        "option": "Run one bounded dogfood cycle before release.",
        "gates": [{"gate_id": "dogfood", "status": "CLEAR_WITH_CONTROLS"}],
        "blockers": ["Human release approval has not been granted."],
        "controls": ["Do not publish from the converter."],
        "evidence_deps": ["pack-17"],
        "snapshot_hash": "sha256:" + "b" * 64,
        "human_approval": "required",
    }
    return _wrap("DecisionEnvelope", payload)


def test_evidence_envelope_renders_a_deterministic_unreviewed_research_draft() -> None:
    mod = _load()
    envelope = _evidence_envelope()

    first = mod.render_draft(envelope, owner="Release team", source_ids=["E-017"])
    second = mod.render_draft(envelope, owner="Release team", source_ids=["E-017"])

    assert first == second
    assert 'title: "Release readiness"' in first
    assert "type: research" in first
    assert "status: draft" in first
    assert 'owner: "Release team"' in first
    assert 'source_ids: ["E-017"]' in first
    assert 'producer_run: "run-2026-09-19"' in first
    assert 'human_reviewed: false' in first
    assert "The deterministic validation suite passes." in first
    assert "Release approval is pending" in first
    assert "S-1" in first


def test_decision_envelope_requires_explicit_ledger_fields_and_stays_draft() -> None:
    mod = _load()
    envelope = _decision_envelope()

    with pytest.raises(ValueError, match="decision_id"):
        mod.render_draft(envelope, owner="Release team", review_by="2026-10-19")
    with pytest.raises(ValueError, match="review_by"):
        mod.render_draft(envelope, owner="Release team", decision_id="D-017")

    rendered = mod.render_draft(
        envelope,
        owner="Release team",
        decision_id="D-017",
        review_by="2026-10-19",
        source_ids=["E-017", "E-018"],
        payload_ref="file:///reviewed/decision-envelope.json",
    )

    assert 'title: "D-017 — Should the candidate be released?"' in rendered
    assert "decision_id: D-017" in rendered
    assert "status: draft" in rendered
    assert "review_by: 2026-10-19" in rendered
    assert 'source_ids: ["E-017", "E-018"]' in rendered
    assert 'human_reviewed: false' in rendered
    assert 'profile: "STANDARD"' in rendered
    assert 'human_approval: "required"' in rendered
    assert 'payload_ref: "file:///reviewed/decision-envelope.json"' in rendered
    assert "Verdict: TEST." in rendered
    assert "Run one bounded dogfood cycle before release." in rendered
    assert "Do not publish from the converter." in rendered
    assert "Human release approval has not been granted." in rendered


def test_converter_rejects_pending_hash_mismatch_and_unsupported_types() -> None:
    mod = _load()

    pending = _evidence_envelope()
    pending["payload_hash"] = "pending"
    with pytest.raises(ValueError, match="pending"):
        mod.render_draft(pending, owner="Release team")

    mismatch = _evidence_envelope()
    mismatch["payload_hash"] = "sha256:" + "0" * 64
    with pytest.raises(ValueError, match="payload_hash mismatch"):
        mod.render_draft(mismatch, owner="Release team")

    unsupported = _evidence_envelope()
    unsupported["type"] = "FindingEnvelope"
    with pytest.raises(ValueError, match="supports only"):
        mod.render_draft(unsupported, owner="Release team")


def test_converter_loads_its_validator_when_another_module_uses_the_same_name(monkeypatch) -> None:
    collision = types.ModuleType("validate_envelope")
    collision.validate_envelope = lambda _data: None
    monkeypatch.setitem(sys.modules, "validate_envelope", collision)

    mod = _load()

    rendered = mod.render_draft(_evidence_envelope(), owner="Release team")
    assert "type: research" in rendered


@pytest.mark.parametrize(
    ("module_name", "envelope_factory", "mutate", "message"),
    [
        (
            "validate_evidence_envelope",
            _evidence_envelope,
            lambda envelope: envelope["payload"]["gaps"].append({"blocking": True}),
            "blocking gaps",
        ),
        (
            "validate_decision_envelope",
            _decision_envelope,
            lambda envelope: envelope["payload"].update(verdict="GO"),
            "GO cannot have blockers",
        ),
    ],
)
def test_converter_ignores_colliding_typed_validator_modules(
    monkeypatch, module_name, envelope_factory, mutate, message
) -> None:
    collision = types.ModuleType(module_name)
    collision.validate = lambda _data: None
    monkeypatch.setitem(sys.modules, module_name, collision)
    envelope = envelope_factory()
    mutate(envelope)
    envelope["payload_hash"] = _hash(envelope["payload"])
    mod = _load()

    with pytest.raises(ValueError, match=message):
        mod.render_draft(
            envelope,
            owner="Release team",
            decision_id="D-017" if envelope["type"] == "DecisionEnvelope" else None,
            review_by="2026-10-19" if envelope["type"] == "DecisionEnvelope" else None,
        )


def test_converter_rejects_invalid_ledger_ids_and_yaml_injection() -> None:
    mod = _load()

    with pytest.raises(ValueError, match="decision_id"):
        mod.render_draft(
            _decision_envelope(),
            owner="Release team",
            decision_id="D-17",
            review_by="2026-10-19",
        )
    with pytest.raises(ValueError, match="source_id"):
        mod.render_draft(_evidence_envelope(), owner="Release team", source_ids=["pack-17"])

    rendered = mod.render_draft(
        _evidence_envelope(),
        owner='Ops"\nsource_ids: ["E-999"]',
    )
    assert 'owner: "Ops\\"\\nsource_ids: [\\"E-999\\"]"' in rendered
    assert '\nsource_ids: ["E-999"]\n' not in rendered


def test_front_matter_escapes_control_characters_and_unicode_line_separators() -> None:
    mod = _load()
    envelope = _evidence_envelope()
    envelope["dependencies"] = ["pack\bcontrol\fform\u2028line\u2029paragraph"]

    rendered = mod.render_draft(envelope, owner="Release team")

    assert "\u2028" not in rendered
    assert "\u2029" not in rendered
    assert "\\u2028" in rendered
    assert "\\u2029" in rendered
    assert "\\b" in rendered
    assert "\\f" in rendered


@pytest.mark.parametrize("kind", ["evidence", "decision"])
def test_producer_text_cannot_forge_markdown_structure(kind: str) -> None:
    mod = _load()
    hostile = "Claim\n\n## Status\n\nApproved by producer\n<script>alert(1)</script>\n- [link](https://example.test)\n```"
    if kind == "evidence":
        envelope = _evidence_envelope()
        envelope["subject"] = hostile
        envelope["payload"]["research_contract"] = hostile
        envelope["payload"]["material_claims"][0]["text"] = hostile
        envelope["payload"]["gaps"][0]["description"] = hostile
        kwargs = {}
    else:
        envelope = _decision_envelope()
        envelope["payload"]["decision_question"] = hostile
        envelope["payload"]["option"] = hostile
        envelope["payload"]["controls"] = [hostile]
        envelope["payload"]["blockers"] = [hostile]
        kwargs = {"decision_id": "D-017", "review_by": "2026-10-19"}
    envelope["payload_hash"] = _hash(envelope["payload"])

    rendered = mod.render_draft(envelope, owner="Release team", **kwargs)

    assert rendered.count("\n## Status\n") <= 1
    assert "Approved by producer\n<script>" not in rendered
    assert "<script>" not in rendered
    assert "[link](https://example.test)" not in rendered
    assert "\n```\n" not in rendered


def test_cli_does_not_create_output_when_validation_fails(tmp_path: Path) -> None:
    source = tmp_path / "pending.json"
    target = tmp_path / "draft.md"
    envelope = _evidence_envelope()
    envelope["payload_hash"] = "pending"
    source.write_text(json.dumps(envelope), encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, str(TOOL), str(source), "--owner", "Release team", "--output", str(target)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 1
    assert "pending" in proc.stderr
    assert not target.exists()


def test_cli_refuses_to_overwrite_an_existing_draft(tmp_path: Path) -> None:
    source = tmp_path / "evidence.json"
    target = tmp_path / "draft.md"
    source.write_text(json.dumps(_evidence_envelope()), encoding="utf-8")
    target.write_text("human work\n", encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, str(TOOL), str(source), "--owner", "Release team", "--output", str(target)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 1
    assert "File exists" in proc.stderr
    assert target.read_text(encoding="utf-8") == "human work\n"


@pytest.mark.parametrize("invalid_kind", ["nan", "duplicate"])
def test_cli_rejects_non_strict_json(tmp_path: Path, invalid_kind: str) -> None:
    source = tmp_path / "invalid.json"
    envelope = _evidence_envelope()
    if invalid_kind == "nan":
        envelope["payload"]["sources"][0]["score"] = float("nan")
        envelope["payload_hash"] = _hash(envelope["payload"])
        raw = json.dumps(envelope)
    else:
        raw = json.dumps(envelope).replace(
            '"id": "run-2026-09-19"',
            '"id": "first", "id": "run-2026-09-19"',
            1,
        )
    source.write_text(raw, encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, str(TOOL), str(source), "--owner", "Release team"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 1
    assert invalid_kind in proc.stderr.lower() or "duplicate" in proc.stderr.lower()


def test_cli_defaults_to_stdout_without_mutating_the_working_directory(tmp_path: Path) -> None:
    source = tmp_path / "evidence.json"
    source.write_text(json.dumps(_evidence_envelope()), encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, str(TOOL), str(source), "--owner", "Release team"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0, proc.stderr
    assert "type: research" in proc.stdout
    assert sorted(path.name for path in tmp_path.iterdir()) == ["evidence.json"]
