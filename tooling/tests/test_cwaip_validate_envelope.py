"""Tests for universal CW-AIP v2 envelope validator."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
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


def test_rejects_generated_at_without_an_rfc3339_timezone():
    payload = _evidence_payload()
    envelope = {
        "id": "ev-1",
        "type": "EvidenceEnvelope",
        "producer": "evidence-researcher",
        "producer_version": "1.0.2",
        "protocol_version": "2.0",
        "subject": "pricing",
        "generated_at": "2026-09-08T12:00:00",
        "as_of": "2026-09-08T12:00:00Z",
        "sensitivity": "internal",
        "dependencies": [],
        "payload": payload,
        "payload_hash": mod.payload_hash(payload),
    }

    with pytest.raises(ValueError, match="generated_at"):
        mod.validate_envelope(envelope)


@pytest.mark.parametrize(
    "generated_at",
    [
        "20260908T120000Z",
        "2026-W37-2T12:00:00Z",
        "2026-09-08T12:00:00+01:02:03",
        "2026-09-08T12:00:00+01:60",
        "2026-09-08T12:00:00-00:60",
    ],
)
def test_rejects_iso8601_dates_outside_rfc3339(generated_at):
    payload = _evidence_payload()
    envelope = {
        "id": "ev-1",
        "type": "EvidenceEnvelope",
        "producer": "evidence-researcher",
        "producer_version": "1.0.2",
        "protocol_version": "2.0",
        "subject": "pricing",
        "generated_at": generated_at,
        "as_of": "2026-09-08T12:00:00Z",
        "sensitivity": "internal",
        "dependencies": [],
        "payload": payload,
        "payload_hash": mod.payload_hash(payload),
    }

    with pytest.raises(ValueError, match="RFC 3339"):
        mod.validate_envelope(envelope)


def test_rejects_hash_mismatch():
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
        "payload_hash": "sha256:" + ("ab" * 32),
    }
    with pytest.raises(ValueError, match="payload_hash mismatch"):
        mod.validate_envelope(envelope, final=True)


def test_fixture_file_validates():
    path = Path(__file__).resolve().parents[2] / "fixtures" / "cwaip-v2" / "evidence-final.json"
    mod.validate_envelope(json.loads(path.read_text()), final=True)


@pytest.mark.parametrize("location", ["core", "payload"])
def test_standard_library_fallback_rejects_schema_forbidden_properties(tmp_path, location):
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
        "payload_hash": mod.payload_hash(payload),
    }
    envelope["unexpected"] = True
    if location == "payload":
        envelope.pop("unexpected")
        payload["unexpected"] = True
        envelope["payload_hash"] = mod.payload_hash(payload)
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(envelope), encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, "-S", str(ROOT / "validate_envelope.py"), str(path), "--final"],
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 1
    assert "unexpected" in proc.stderr


def _envelope_text(payload_json: str, digest: str) -> str:
    return (
        '{"id": "ev-1", "type": "EvidenceEnvelope", "producer": "evidence-researcher",'
        ' "producer_version": "1.0.2", "protocol_version": "2.0", "subject": "pricing",'
        ' "generated_at": "2026-09-08T12:00:00Z", "as_of": "2026-09-08T12:00:00Z",'
        ' "sensitivity": "internal", "dependencies": [],'
        f' "payload": {payload_json}, "payload_hash": "{digest}"}}'
    )


def _run_cli(path: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(ROOT / "validate_envelope.py"), str(path), *extra],
        capture_output=True,
        text=True,
    )


def test_cli_rejects_duplicate_keys_that_other_parsers_resolve_differently(tmp_path):
    # Python keeps the last "mode", so the hash matches here; a first-wins
    # parser would read a different payload under the same verified hash.
    payload = _evidence_payload()
    digest = mod.payload_hash(payload)
    body = json.dumps(payload)
    duplicated = body.replace('"mode": "QUICK"', '"mode": "DEEP", "mode": "QUICK"', 1)
    assert duplicated != body
    path = tmp_path / "dup.json"
    path.write_text(_envelope_text(duplicated, digest), encoding="utf-8")

    proc = _run_cli(path, "--final")

    assert proc.returncode == 1
    assert "duplicate JSON key: 'mode'" in proc.stderr
    assert "Traceback" not in proc.stderr


def test_cli_rejects_non_finite_numbers(tmp_path):
    payload = _evidence_payload()
    payload["gaps"] = [{"weight": 0}]
    body = json.dumps(payload).replace('"weight": 0', '"weight": NaN')
    path = tmp_path / "nan.json"
    path.write_text(_envelope_text(body, "pending"), encoding="utf-8")

    proc = _run_cli(path)

    assert proc.returncode == 1
    assert "non-finite JSON number: NaN" in proc.stderr


def test_cli_reports_missing_file_without_traceback(tmp_path):
    proc = _run_cli(tmp_path / "absent.json")

    assert proc.returncode == 1
    assert proc.stderr.startswith("FAIL: cannot read")
    assert "Traceback" not in proc.stderr


def test_print_hash_rejects_non_object_document(tmp_path):
    path = tmp_path / "list.json"
    path.write_text("[]", encoding="utf-8")

    proc = _run_cli(path, "--print-hash")

    assert proc.returncode == 1
    assert "envelope must be an object" in proc.stderr
