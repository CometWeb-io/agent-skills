"""Regression coverage for structural and fail-closed verdict validation."""
import copy
import importlib.util
import json
from pathlib import Path
import pytest
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("audit_validation_quality", ROOT / "scripts/validate_report.py")
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)

def report():
    return json.loads((ROOT / "tests/report-valid.json").read_text())

def clean_report():
    d = report()
    d.update(findings=[], evidence=[], verdict="ship")
    d["counts"] = {k: 0 for k in d["counts"]}
    d["coverage"] = dict(totalInScope=5, tested=5, sampled=0, policyBlocked=0, environmentBlocked=0, unreachable=0)
    return d

def test_valid_fixture():
    assert not v.validate(report()).errors

@pytest.mark.parametrize("field,bad", [(field,bad) for field in ["findings", "evidence", "counts", "coverage", "capabilities", "environment", "scope", "mode", "verdict"] for bad in [None,"invalid",17,[]] if not (bad == [] and field in {"findings","evidence"})])
def test_malformed_structure_is_rejected_without_crash(field, bad):
    d = clean_report()
    d[field] = bad
    assert v.validate(d).errors

@pytest.mark.parametrize("field", ["environmentBlocked", "unreachable"])
@pytest.mark.parametrize("verdict", ["ship", "ship_with_fixes"])
def test_blocked_coverage_cannot_certify_release(field, verdict):
    d = report() if verdict == "ship_with_fixes" else clean_report()
    d["verdict"] = verdict
    d["coverage"] = dict(totalInScope=5, tested=0, sampled=0, policyBlocked=0, environmentBlocked=0, unreachable=0)
    d["coverage"][field] = 5
    assert v.validate(d).errors

def test_zero_scope_cannot_ship():
    d = clean_report()
    d["coverage"]["totalInScope"] = d["coverage"]["tested"] = 0
    assert v.validate(d).errors

def test_incomplete_is_honest_with_missing_coverage():
    d = clean_report()
    d["verdict"] = "incomplete"
    d["coverage"]["tested"] = 0
    d["coverage"]["environmentBlocked"] = 5
    assert not v.validate(d).errors

def test_confirmed_blocker_can_stop_release_despite_incomplete_coverage():
    d = report()
    d["verdict"] = "do_not_ship"
    d["findings"][0]["severity"] = "blocker"
    d["counts"].update(blocker=1, major=0)
    d["coverage"]["tested"] -= 1
    d["coverage"]["environmentBlocked"] += 1
    assert not v.validate(d).errors

def test_evidence_requires_declared_capability():
    d = report()
    d["capabilities"]["screenshots"] = False
    assert v.validate(d).errors

@pytest.mark.parametrize("field", ["tested", "sampled", "totalInScope"])
@pytest.mark.parametrize("value", [True, -1, "5", []])
def test_bad_coverage_types(field, value):
    d = clean_report()
    d["coverage"][field] = value
    assert v.validate(d).errors

def test_reverse_evidence_link_must_agree():
    d = report()
    d["evidence"][0]["supports"] = []
    assert v.validate(d).errors

@pytest.mark.parametrize("data", [None, [], "report", 3, True])
def test_invalid_root(data):
    assert v.validate(data).errors
