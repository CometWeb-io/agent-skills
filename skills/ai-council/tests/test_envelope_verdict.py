"""The Council verdict on a CW-AIP v2 DecisionEnvelope uses the schema's spelling.

The Council contract writes `NO-GO`; `protocol/cw-aip-v2/decision.schema.json`
accepts `NO_GO`. The kernel maps one onto the other and reports both from `gate`.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parents[1]
ROOT = SKILL.parents[1]
sys.path.insert(0, str(SKILL / "scripts"))

import council  # noqa: E402

SCHEMA = ROOT / "protocol" / "cw-aip-v2" / "decision.schema.json"


def test_every_council_verdict_maps_onto_the_schema_enum() -> None:
    wire = set(json.loads(SCHEMA.read_text(encoding="utf-8"))["properties"]["verdict"]["enum"])
    assert {council.envelope_verdict(v) for v in council.VERDICTS} == wire
    assert council.envelope_verdict("NO-GO") == "NO_GO"
    for unchanged in ("GO", "TEST", "DEFER"):
        assert council.envelope_verdict(unchanged) == unchanged


@pytest.mark.parametrize("value", ["NO_GO", "no-go", "GO_WITH_CONTROLS", "", None])
def test_anything_but_a_council_verdict_is_refused(value) -> None:
    with pytest.raises(ValueError, match="not a Council verdict"):
        council.envelope_verdict(value)


def test_gate_reports_the_envelope_spelling() -> None:
    out = subprocess.run(
        [sys.executable, str(SKILL / "scripts" / "council_kernel.py"), "gate", "--verdict", "GO",
         "--confidence", "0.9", "--required-confidence", "0.8", "--freshness-status", "CLEAR",
         "--required-gates-json", '["security"]', "--gate-statuses-json", '{"security": "BLOCK"}'],
        capture_output=True, text=True, timeout=60, check=True,
    )
    assert json.loads(out.stdout) == {"verdict": "NO-GO", "envelope_verdict": "NO_GO"}
