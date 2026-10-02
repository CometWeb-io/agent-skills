import json
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


@pytest.mark.parametrize("change", [
    {"inventory": [{"name": "frontend"}]},
    {"inventory": ["frontend"]},
    {"inventory": [{"id": ["frontend"]}]},
    {"inventory": [{"id": ""}]},
    {"checks": ["frontend"]},
    {"checks": [{"id": ["frontend"], "status": "inspected"}]},
    {"checks": [{"id": "frontend", "status": ["inspected"]}]},
    {"inventory_status": ["complete"]},
    {"claim": ["bounded"]},
], ids=lambda c: next(iter(c)))
def test_malformed_rows_are_reported_not_crashed(change):
    # These used to escape as KeyError/TypeError/AttributeError.
    data=ledger()
    data.update(change)
    with pytest.raises(ValueError):
        validate(data)


@pytest.mark.parametrize("refs", ["fixture-source", [""], ["  "], [None], {}])
def test_evidence_refs_must_name_something(refs):
    # A bare string or blank entries are truthy yet reference no evidence.
    data=ledger()
    data["checks"][0]["evidence_refs"]=refs
    with pytest.raises(ValueError, match="frontend"):
        validate(data)


@pytest.mark.parametrize("execution_ref", ["", "   ", ["fixture-run"]])
def test_execution_ref_must_be_a_nonblank_string(execution_ref):
    data=ledger()
    data["checks"][1]["execution_ref"]=execution_ref
    with pytest.raises(ValueError, match="execution record"):
        validate(data)


def test_errors_name_the_offending_check():
    data=ledger()
    data["checks"][0]["id"]="mobile"
    with pytest.raises(ValueError, match="unknown inventory ID: 'mobile'"):
        validate(data)
    data=ledger()
    data["checks"][0]["status"]="done"
    with pytest.raises(ValueError, match="'frontend' has unknown status: 'done'"):
        validate(data)


def test_cli_exit_codes_and_messages(tmp_path, capsys):
    from validate_coverage import main
    good=tmp_path/"good.json"
    good.write_text(json.dumps(ledger()))
    assert main([str(good)]) == 0
    bad=tmp_path/"bad.json"
    bad.write_text(json.dumps({**ledger(), "inventory": [{}]}))
    assert main([str(bad)]) == 1
    assert main([str(tmp_path/"absent.json")]) == 1
    err=capsys.readouterr().err
    assert "FAIL: every inventory entry" in err and "FAIL: cannot read" in err
