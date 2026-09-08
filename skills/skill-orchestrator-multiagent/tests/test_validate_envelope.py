"""Tests for validate_envelope."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

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
