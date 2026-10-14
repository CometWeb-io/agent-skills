"""Fixture and instruction-loading checks, not model-behavior evaluations."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tooling"))
from run_model_evals import prepare, validate_suite  # noqa: E402

SUITE = ROOT / "evals/model/source-screening.json"
GOLD = ROOT / "evals/model/source-screening-gold.json"
CASES = validate_suite(json.loads(SUITE.read_text()))
EXPECTATIONS = json.loads(GOLD.read_text())["cases"]


def test_every_claim_has_separate_nonempty_review_expectations():
    assert {c["id"] for c in CASES} == {g["case_id"] for g in EXPECTATIONS}
    assert len(EXPECTATIONS) == len(CASES)
    by_id = {g["case_id"]: g for g in EXPECTATIONS}
    lanes = set()
    for case in CASES:
        fixture = case["fixture"]
        assert fixture["synthetic"] is True
        assert fixture["source"]["excerpt"].strip()
        lanes.add(fixture["privacy_lane"])
        claims = fixture["claims"]
        assert claims and len({c["claim_id"] for c in claims}) == len(claims)
        expected = by_id[case["id"]]["expectations"]
        assert len(expected) == len(claims)
        assert {e["claim_id"] for e in expected} == {c["claim_id"] for c in claims}
        for row in expected:
            assert row["screening"] and set(row["screening"]) <= {
                "REGISTER", "LIMITED", "DISCOVERY_ONLY"
            }
            assert row["admission"] and set(row["admission"]) <= {
                "ACCEPTED", "CONTEXT_ONLY", "REJECTED"
            }
            assert row["direction"] and set(row["direction"]) <= {
                "SUPPORT", "CONTRADICT", "CONTEXT"
            }
    assert lanes == {"PUBLIC", "PRIVATE", "USER_SUPPLIED"}


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
def test_eval_request_loads_the_policy_but_withholds_the_grading_oracle(case):
    current = prepare(case, "current", ROOT, ROOT, 2048)
    candidate = prepare(case, "candidate", ROOT, ROOT, 2048)
    baseline = prepare(case, "no_skill", ROOT, ROOT, 2048)
    assert current["instructions"] == candidate["instructions"]
    assert baseline["instructions"] == {}
    assert set(candidate["instructions"]) == {"SKILL.md", *case["resources"]}
    assert "references/source-routing.md" in candidate["instructions"]
    for name, contents in candidate["instructions"].items():
        assert contents == (ROOT / "skills/evidence-researcher" / name).read_text()
    for request in (current, candidate, baseline):
        assert request["fixture"] == case["fixture"]
        assert request["prompt"] == case["prompt"]
        assert request["capabilities"] == {"tools": False}
        assert "rubric" not in request
        assert "expectations" not in request
        assert "review_notes" not in request
        assert set(request["fixture"]) == {
            "synthetic", "privacy_lane", "capture_date", "source", "claims"
        }


def test_source_screening_plan_makes_no_model_call():
    result = subprocess.run(
        [sys.executable, str(ROOT / "tooling/run_model_evals.py"), "--suite", str(SUITE)],
        capture_output=True, text=True, check=True,
    )
    report = json.loads(result.stdout)
    assert report["case_count"] == len(CASES)
    assert report["status"] == "not_run"
    assert report["model_calls"] == 0
    assert report["runtime_acceptance"] == "not_assessed"
