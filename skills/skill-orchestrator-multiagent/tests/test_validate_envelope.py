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
            "payload": {"claims": []},
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
    sys.path.insert(0, str(ROOT.parents[1] / "tooling"))
    from package_skill import payload

    entries, _manifest = payload(ROOT.parents[1], "skill-orchestrator-multiagent")
    assert "scripts/validate_envelope.py" in entries
    assert entries["references/envelope.core.schema.json"] == (
        ROOT.parents[1] / "protocol" / "schemas" / "envelope.core.schema.json"
    ).read_bytes()


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
