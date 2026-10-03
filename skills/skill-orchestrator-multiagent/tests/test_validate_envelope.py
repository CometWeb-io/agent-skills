"""Tests for validate_envelope."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_envelope import validate_envelope



class ValidateEnvelopeTests(unittest.TestCase):
    def test_minimal_evidence_envelope(self) -> None:
        data = {
            "id": "evidence-researcher:EvidenceEnvelope:smoke",
            "type": "EvidenceEnvelope",
            "producer": "evidence-researcher",
            "protocol_version": "1.0",
            "subject": "cometweb.io/pricing claims",
            "as_of": "2026-08-26T00:00:00+02:00",
            "payload": {
                "research_contract": "Is the listed plan price current?",
                "material_claims": [],
                "evidence_pack_hash": "sha256:" + "0" * 64,
            },
        }
        errors = validate_envelope(data, expected_type="EvidenceEnvelope")
        self.assertEqual(errors, [])

    def test_type_mismatch(self) -> None:
        data = {
            "id": "x",
            "type": "DecisionHandoff",
            "producer": "ai-council",
            "protocol_version": "1.0",
            "subject": "s",
            "as_of": "2026-08-26T00:00:00+02:00",
            "payload": {},
        }
        errors = validate_envelope(data, expected_type="EvidenceEnvelope")
        self.assertTrue(any("type" in e for e in errors))


if __name__ == "__main__":
    unittest.main()


@pytest.mark.parametrize("remove_schema", [False, True])
def test_relocated_package_rejects_invalid_envelope(tmp_path: Path, remove_schema: bool) -> None:
    package = tmp_path / "skill-orchestrator-multiagent"
    script = package / "scripts" / "validate_envelope.py"
    script.parent.mkdir(parents=True)
    script.write_bytes((ROOT / "scripts" / "validate_envelope.py").read_bytes())
    schema = package / "references" / "envelope.core.schema.json"
    if (ROOT / "references" / "envelope.core.schema.json").is_file():
        schema.parent.mkdir(parents=True)
        schema.write_bytes((ROOT / "references" / "envelope.core.schema.json").read_bytes())
    if remove_schema:
        schema.unlink(missing_ok=True)
    envelope = tmp_path / "invalid.json"
    envelope.write_text(json.dumps({
        "id": 17, "type": "EvidenceEnvelope", "producer": "demo",
        "protocol_version": "1.0", "subject": "demo", "as_of": "2026-09-25", "payload": {},
    }), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(package / "scripts" / "validate_envelope.py"), str(envelope)],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode != 0
    assert "FAIL:" in result.stderr


def test_multiagent_package_contains_usable_validator() -> None:
    # Packaging is repository tooling, not this skill's runtime: the isolated
    # runtime-matrix venv installs only RUNTIME.json dependencies.
    pytest.importorskip("yaml", reason="repository packaging tooling needs PyYAML")
    sys.path.insert(0, str(ROOT.parents[1] / "tooling"))
    from package_skill import payload

    entries, _manifest = payload(ROOT.parents[1], "skill-orchestrator-multiagent")
    assert "scripts/validate_envelope.py" in entries
    for name in ("envelope.core.schema.json", "evidence-envelope.schema.json", "decision-handoff.schema.json"):
        assert entries[f"references/{name}"] == (ROOT.parents[1] / "protocol" / "schemas" / name).read_bytes()


V1_DECISION = {
    "id": "release-readiness:DecisionHandoff:demo", "type": "DecisionHandoff", "producer": "release-readiness",
    "protocol_version": "1.0", "subject": "demo", "as_of": "2026-09-25T00:00:00Z",
    "payload": {"verdict": "GO", "blockers": [], "controls": []},
}


def test_v1_kind_schema_applies_payload_rules() -> None:
    assert validate_envelope(V1_DECISION, expected_type="DecisionHandoff") == []
    missing_verdict = {**V1_DECISION, "payload": {"blockers": []}}
    assert any("verdict" in e for e in validate_envelope(missing_verdict))
    evidence = {**V1_DECISION, "type": "EvidenceEnvelope", "payload": {"claims": []}}
    assert any("research_contract" in e for e in validate_envelope(evidence))


@pytest.mark.parametrize("verdict,ok", [("GO", False), ("GO_WITH_CONTROLS", False), ("NO_GO", True), ("DEFER", True)])
def test_v1_authorizing_verdict_rejects_blockers(verdict: str, ok: bool) -> None:
    data = {**V1_DECISION, "payload": {"verdict": verdict, "blockers": ["checkout returns 500"]}}
    errors = validate_envelope(data)
    assert (errors == []) is ok, errors
    if not ok:
        assert any("blockers" in e for e in errors)


def test_relocated_package_fails_closed_without_kind_schema(tmp_path: Path) -> None:
    """A missing kind schema must not silently downgrade the check to the core."""
    package = tmp_path / "skill-orchestrator-multiagent"
    (package / "scripts").mkdir(parents=True)
    (package / "references").mkdir()
    (package / "scripts" / "validate_envelope.py").write_bytes((ROOT / "scripts" / "validate_envelope.py").read_bytes())
    (package / "references" / "envelope.core.schema.json").write_bytes(
        (ROOT / "references" / "envelope.core.schema.json").read_bytes()
    )
    envelope = tmp_path / "decision.json"
    envelope.write_text(json.dumps(V1_DECISION), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(package / "scripts" / "validate_envelope.py"), str(envelope)],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 1
    assert "bundled kind schema is missing: decision-handoff.schema.json" in result.stderr


def test_envelope_validation_fails_closed_without_jsonschema(tmp_path: Path) -> None:
    envelope = tmp_path / "valid.json"
    envelope.write_text(json.dumps({
        "id": "e1", "type": "EvidenceEnvelope", "producer": "demo",
        "protocol_version": "1.0", "subject": "demo", "as_of": "2026-09-25", "payload": {},
    }), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-S", str(ROOT / "scripts" / "validate_envelope.py"), str(envelope)],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode != 0
    assert "jsonschema dependency is required" in result.stderr


def _documented_required(block_title: str, list_key: str) -> list[str]:
    """Fields kernel-contract.md marks required for one list under a kind payload."""
    text = (ROOT / "references" / "kernel-contract.md").read_text(encoding="utf-8")
    block = text.split(block_title, 1)[1]
    lines = block.split(f"{list_key}[]", 1)[1].splitlines()[1:]
    required: list[str] = []
    for line in lines:
        if not line.startswith("    "):
            break
        names, _, rule = line.strip().partition(":")
        if rule.strip() == "required":
            required += [name.strip() for name in names.split(",")]
    return sorted(required)


def test_kernel_contract_lists_every_required_evidence_claim_field() -> None:
    # The gate validates against the bundled kind schema; a field the schema
    # requires but the reference leaves optional is refused with no warning.
    schema = json.loads((ROOT / "references" / "evidence-envelope.schema.json").read_text(encoding="utf-8"))
    kind = next(part for part in schema["allOf"] if "payload" in part.get("properties", {}))
    claim = kind["properties"]["payload"]["properties"]["material_claims"]["items"]
    assert _documented_required("EvidenceEnvelope (v1) payload:", "material_claims") == sorted(claim["required"])


def test_evidence_claim_without_epistemic_kind_is_refused() -> None:
    data = {
        "id": "evidence-researcher:EvidenceEnvelope:claims",
        "type": "EvidenceEnvelope",
        "producer": "evidence-researcher",
        "protocol_version": "1.0",
        "subject": "example.com/pricing claims",
        "as_of": "2026-08-26T00:00:00+02:00",
        "payload": {
            "research_contract": "Is the listed plan price current?",
            "material_claims": [{"claim_id": "c1", "text": "Pro costs 39 USD.", "status": "VERIFIED"}],
            "evidence_pack_hash": "sha256:" + "0" * 64,
        },
    }
    errors = validate_envelope(data, expected_type="EvidenceEnvelope")
    assert any("epistemic_kind" in e for e in errors), errors
