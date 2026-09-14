import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from validate_coverage import validate


def ledger():
    return {"schema":"cometweb.audit-coverage/v1","inventory_status":"complete","source_revision":"a"*40,"inventory_evidence_ref":"fixture-inventory","inventory":[{"id":"frontend"},{"id":"api"}],"checks":[{"id":"frontend","status":"inspected","evidence_refs":["fixture-source"]},{"id":"api","status":"tested","evidence_refs":["fixture-source"],"execution_ref":"fixture-run"}],"claim":"bounded"}


def test_source_inspection_is_not_execution():
    result=validate(ledger())
    assert result["counts"]["inspected"] == result["counts"]["tested"] == 1
    assert result["evidence_authentication"] == "not_performed"


@pytest.mark.parametrize("status", ["sampled","policy_blocked","environment_blocked","unreachable","not_assessed"])
def test_partial_or_blocked_entries_cannot_support_full_claim(status):
    data=ledger()
    data["claim"]="full_source_review"
    data["checks"][0]["status"]=status
    with pytest.raises(ValueError):
        validate(data)


def test_missing_entries_remain_visible():
    data=ledger()
    data["checks"].pop()
    assert validate(data)["missing"] == ["api"]
    data["claim"]="full_source_review"
    with pytest.raises(ValueError):
        validate(data)


def test_complete_source_review_cannot_claim_full_execution():
    data=ledger()
    data["claim"]="full_source_review"
    validate(data)
    data["claim"]="full_execution"
    with pytest.raises(ValueError):
        validate(data)


def test_execution_needs_execution_record():
    data=ledger()
    del data["checks"][1]["execution_ref"]
    with pytest.raises(ValueError):
        validate(data)


def test_unknown_inventory_cannot_claim_full_coverage():
    data=ledger()
    data.update(inventory_status="unknown",claim="full_source_review")
    with pytest.raises(ValueError):
        validate(data)


def test_duplicate_checks_are_not_double_counted():
    data=ledger()
    data["checks"].append(data["checks"][0])
    with pytest.raises(ValueError):
        validate(data)
