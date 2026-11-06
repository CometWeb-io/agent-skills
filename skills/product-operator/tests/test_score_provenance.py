"""Unknown judgments must not turn into apparently verified numbers."""
import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("score_brief", ROOT / "scripts/prepare_brief.py")
brief = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(brief)


def example():
    data = json.loads((ROOT / "examples/brief.synthetic.pl.json").read_text())
    data["coverage"]["notion"] = "verified"
    for row in data["candidates"]:
        row.pop("scoring_mode")
        row.update(impact=5, goal_alignment=5, urgency=4, effort=1,
                   confidence=0.9, evidence_strength=0.9)
    return data


def qualitative(row):
    row["scoring_mode"] = "qualitative"
    for field in ("confidence", "evidence_strength", "impact", "goal_alignment", "urgency", "effort"):
        row.pop(field, None)


def test_unscored_actions_roundtrip_without_inventing_zero_or_blocker():
    data = example()
    for row in data["candidates"]:
        qualitative(row)
    result = brief.assemble(data)
    row = result["report"]["verify_now"][0]
    assert row["priority_score"] is None
    assert row["score_breakdown"] is None
    assert row.get("confidence") is None
    assert result["validation"]["status"] == "PASS"
    assert [row["id"] for row in result["report"]["next"]] == ["B"]
    assert "Pewność: —" in brief.render(result)


def test_numeric_inputs_without_basis_cannot_be_reported_as_verified():
    result = brief.assemble(example())
    assert result["validation"]["status"] == "WARN"
    assert any("numeric" in item.lower() and "unverified" in item.lower() for item in result["validation"]["warnings"])


def test_self_declared_basis_does_not_authenticate_numeric_inputs():
    data = example()
    for row in data["candidates"]:
        row["score_basis"] = "source says 0.9"
    result = brief.assemble(data)
    assert result["validation"]["status"] == "WARN"
    assert any("unverified" in item.lower() for item in result["validation"]["warnings"])


def test_qualitative_mode_rejects_inconsistent_numeric_values():
    data = example()
    qualitative(data["candidates"][0])
    data["candidates"][0]["confidence"] = 0.9
    with pytest.raises(brief.kernel.InputError, match="qualitative"):
        brief.assemble(data)


def test_existing_numeric_ranking_and_dependency_gate_are_preserved():
    data = example()
    result = brief.assemble(copy.deepcopy(data))
    assert result["report"]["verify_now"][0]["id"] == "A"
    assert result["report"]["next"][0]["id"] == "B"
    assert result["report"]["verify_now"][0]["priority_score"] > 0


def test_qualitative_blocker_needs_evidence_not_an_invented_score():
    row = {"id": "V", "scoring_mode": "qualitative", "blocker": True,
           "blocks_current_goal": True}
    result = brief.kernel.rank_candidate(row)
    assert result["priority_tier"] == "VERIFY_NOW"
    assert result["priority_score"] is None


def test_forged_qualitative_score_is_invalid_in_sidecar():
    data = example()
    for row in data["candidates"]:
        qualitative(row)
    report = brief.assemble(data)["report"]
    report["verify_now"][0]["priority_score"] = 17
    assert brief.kernel.validate_report(report)["status"] == "FAIL"


def test_numeric_score_in_later_lane_is_not_silently_accepted():
    data = example()
    for row in data["candidates"]:
        qualitative(row)
    report = brief.assemble(data)["report"]
    report["later"] = [{"id": "L", "confidence": 0.9}]
    assert brief.kernel.validate_report(report)["status"] == "WARN"


def test_unknown_scoring_mode_is_rejected():
    data = example()
    data["candidates"][0]["scoring_mode"] = "qualitativ"
    with pytest.raises(brief.kernel.InputError, match="scoring_mode"):
        brief.assemble(data)


def test_mixed_qualitative_and_numeric_rows_do_not_gain_false_score_precedence():
    rows = [
        {"id": "A", "scoring_mode": "qualitative", "verify_first": True},
        {"id": "Z", "verify_first": True, "impact": 5, "confidence": 1, "evidence_strength": 1},
    ]
    result = brief.kernel.sequence_candidates(rows)
    assert [row["id"] for row in result["execution_order"]] == ["A", "Z"]


def test_explicit_null_confidence_renders_as_unknown():
    data = example()
    for row in data["candidates"]:
        qualitative(row)
        row["confidence"] = None
    result = brief.assemble(data)
    assert "Pewność: —" in brief.render(result)
    assert "Pewność: None" not in brief.render(result)


def test_qualitative_future_gate_is_not_promoted_as_verification_now():
    data = example()
    row = data["candidates"][0]
    qualitative(row)
    row.update(future_gate=True, blocks_current_goal=False)
    data["candidates"] = [row]
    result = brief.assemble(data)
    assert not result["report"]["verify_now"]
    assert [item["id"] for item in result["report"]["later"]] == ["A"]


def test_unscored_unproven_blocker_does_not_promote_implementation():
    data = example()
    row = data["candidates"][0]
    qualitative(row)
    row.update(blocker=True, blocks_current_goal=True, action_type="implement", verify_first=False)
    data["candidates"] = [row]
    result = brief.assemble(data)
    assert not result["report"]["now"]
    assert result["plan"]["held_implementation_action_ids"] == ["A"]
