"""Regression fixtures are synthetic, not proof of real-world research quality."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("evidence_admission_kernel", ROOT / "scripts/evidence_kernel.py")
kernel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kernel)
base_spec = importlib.util.spec_from_file_location("original_evidence_cases", ROOT / "tests/test_evidence_kernel.py")
base = importlib.util.module_from_spec(base_spec)
base_spec.loader.exec_module(base)


def ledger():
    return base.EvidenceKernelV2Tests().base_ledger()


def inference(data, cid="clm_inference", dependency="clm_policy"):
    claim = copy.deepcopy(data["claims"][0])
    claim.update(claim_id=cid, materiality="material", epistemic_kind="INFERENCE", status="SUPPORTED_INFERENCE", depends_on_claim_ids=[dependency])
    data["claims"].append(claim)
    search = copy.deepcopy(data["searches"][0])
    search.update(search_id="srch_" + cid, claim_id=cid)
    data["searches"].append(search)
    return claim


def test_empty_pack_is_not_ready():
    data = kernel.template("Synthetic", "2026-09-13T00:00:00Z", "STANDARD")
    assert kernel.audit(data)["research_status"] == "PARTIAL"
    assert kernel.stop_decision(data, 10, 0, 1)["stop"] is False


def test_only_supporting_claims_do_not_establish_material_scope():
    data = ledger()
    data["claims"][0]["materiality"] = "supporting"
    assert kernel.audit(data)["research_status"] == "PARTIAL"


def test_material_gap_blocks_ready():
    data = ledger()
    data["gaps"] = [{"gap_id": "gap_scope", "claim_id": "clm_policy", "severity": "material", "what_closes_it": "Inspect appendix"}]
    assert kernel.audit(data)["research_status"] == "PARTIAL"


@pytest.mark.parametrize("claim_type", ["vendor_policy", "competitor_pricing", "internal_metric", "internal_process_state"])
def test_live_verification_does_not_ignore_ttl(claim_type):
    source = ledger()["sources"][0]
    source["last_verified_at"] = "2020-01-01T00:00:00Z"
    assert kernel.temporal_status(source, "2026-09-13T00:00:00Z", claim_type)["temporal_status"] == "STALE"


@pytest.mark.parametrize("field", ["verified_for_research", "requires_live_verification"])
@pytest.mark.parametrize("value", ["false", "true", 0, 1, [], {}])
def test_live_flags_require_actual_booleans(field, value):
    data = ledger()
    source = data["sources"][0]
    source[field] = value
    result = kernel.temporal_status(source, data["research_contract"]["as_of"], "vendor_policy")
    assert result["temporal_status"] == "UNKNOWN"


@pytest.mark.parametrize("value", [True, -1, "7", float("nan"), float("inf"), 1e300])
@pytest.mark.parametrize("claim_type", ["vendor_policy", "current_fact"])
def test_bad_ttl_cannot_pass_or_crash(value, claim_type):
    data = ledger()
    source = data["sources"][0]
    source["freshness_ttl_days"] = value
    assert kernel.temporal_status(source, data["research_contract"]["as_of"], claim_type)["temporal_status"] == "UNKNOWN"


def test_future_verification_is_not_clock_skew_pass():
    source = ledger()["sources"][0]
    source["last_verified_at"] = "2026-09-13T00:01:00Z"
    assert kernel.temporal_status(source, "2026-09-13T00:00:00Z", "vendor_policy")["temporal_status"] == "UNKNOWN"


@pytest.mark.parametrize("claim_type", ["service_status", "law_regulation", "regulatory_guidance", "security_advisory"])
def test_zero_cache_requires_current_run_binding(claim_type):
    data = ledger()
    assert kernel.temporal_status(data["sources"][0], data["research_contract"]["as_of"], claim_type)["temporal_status"] == "UNKNOWN"


def test_zero_cache_with_explicit_current_run_is_admissible():
    data = ledger()
    data["claims"][0]["claim_type"] = "service_status"
    data["research_contract"]["started_at"] = "2026-08-25T21:00:00+02:00"
    data["sources"][0]["verified_research_id"] = data["research_id"]
    assert kernel.audit(data)["research_status"] == "READY"


@pytest.mark.parametrize("mutate", ["wrong_run", "old_verification", "missing_start"])
def test_zero_cache_run_constraints(mutate):
    data = ledger()
    data["claims"][0]["claim_type"] = "service_status"
    data["research_contract"]["started_at"] = "2026-08-25T21:00:00+02:00"
    data["sources"][0]["verified_research_id"] = data["research_id"]
    if mutate == "wrong_run":
        data["sources"][0]["verified_research_id"] = "other-run"
    elif mutate == "old_verification":
        data["sources"][0]["last_verified_at"] = "2026-08-25T20:00:00+02:00"
    else:
        del data["research_contract"]["started_at"]
    assert kernel.audit(data)["research_status"] != "READY"


def test_stricter_ttl_is_applied_to_live_source():
    data = ledger()
    data["sources"][0]["freshness_ttl_days"] = 0.001
    assert kernel.audit(data)["research_status"] == "REFRESH_REQUIRED"


def test_ttl_override_cannot_lengthen_policy():
    data = ledger()
    data["sources"][0].update(last_verified_at="2026-07-01T00:00:00Z", freshness_ttl_days=365)
    assert kernel.audit(data)["research_status"] == "REFRESH_REQUIRED"


@pytest.mark.parametrize("field", ["scope_fit", "directness", "measurement_quality"])
@pytest.mark.parametrize("value", ["low", "unknown"])
def test_inadequate_evidence_cannot_prove_claim(field, value):
    data = ledger()
    data["evidence"][0][field] = value
    assert kernel.audit(data)["research_status"] != "READY"


def test_quality_and_freshness_must_be_on_same_edge():
    data = ledger()
    source = copy.deepcopy(data["sources"][0])
    source.update(source_id="src_stale", canonical_ref="https://example.com/stale", last_verified_at="2020-01-01T00:00:00Z")
    data["sources"].append(source)
    edge = copy.deepcopy(data["evidence"][0])
    edge.update(evidence_id="ev_stale", source_id="src_stale")
    data["evidence"].append(edge)
    data["evidence"][0]["directness"] = "low"
    assert kernel.audit(data)["research_status"] != "READY"


@pytest.mark.parametrize("condition", ["no_evidence", "stale", "contradiction", "gap"])
def test_inference_needs_admissible_supporting_dependency(condition):
    data = ledger()
    data["claims"][0]["materiality"] = "supporting"
    inference(data)
    if condition == "no_evidence":
        data["evidence"] = []
    elif condition == "stale":
        data["sources"][0]["last_verified_at"] = "2020-01-01T00:00:00Z"
    elif condition == "contradiction":
        data["contradictions"] = [{"contradiction_id": "ctr_a", "claim_id": "clm_policy", "resolution": "UNRESOLVED", "severity": "material", "evidence_ids": []}]
    else:
        data["gaps"] = [{"gap_id": "gap_a", "claim_id": "clm_policy", "severity": "material", "what_closes_it": "Inspect"}]
    result = kernel.audit(data)
    assert result["research_status"] != "READY"
    row = next(r for r in result["coverage"]["claims"] if r["claim_id"] == "clm_inference")
    assert row["dependencies_ready"] is False


def test_inference_chain_order_independent():
    data = ledger()
    inference(data)
    inference(data, "clm_second", "clm_inference")
    data["claims"].reverse()
    assert kernel.audit(data)["research_status"] == "READY"
    data["sources"][0]["last_verified_at"] = "2020-01-01T00:00:00Z"
    assert not any(r["ready"] for r in kernel.coverage(data)["claims"])


@pytest.mark.parametrize("condition", ["missing_time", "future_time", "missing_query"])
def test_falsifier_needs_auditable_execution_record(condition):
    data = ledger()
    if condition == "missing_time":
        data["searches"][0].pop("completed_at")
    elif condition == "future_time":
        data["searches"][0]["completed_at"] = "2030-01-01T00:00:00Z"
    else:
        data["searches"][0]["query_summary"] = ""
    assert kernel.audit(data)["research_status"] != "READY"


def test_migration_does_not_fabricate_a_completed_search():
    old = {"research_question": "Historic", "as_of": "2026-08-25T21:44:00+02:00", "mode": "QUICK",
           "claims": [{"claim_id": "clm_h", "claim_text": "H", "claim_type": "historical_fact", "materiality": "material", "temporal_sensitivity": "static", "contradiction_tested": True, "status": "VERIFIED", "confidence": "high"}],
           "evidence": [{"evidence_id": "ev_h", "title": "Archive", "canonical_url": "https://example.com/history", "source_role": "PRIMARY", "authority_fit": "high", "directness": "high", "scope_fit": "high", "measurement_quality": "not_applicable", "admission": "ACCEPTED", "supports_claim_ids": ["clm_h"]}]}
    result = kernel.migrate_v1(old)
    assert not result["claims"][0]["contradiction_tested"]
    assert not any(s["completed"] for s in result["searches"])
    assert kernel.audit(result)["research_status"] != "READY"
    assert kernel.validate_ledger(result)["valid"]


def test_derived_sources_do_not_multiply_independence():
    data = ledger()
    for i in range(2):
        source = copy.deepcopy(data["sources"][0])
        source.update(source_id=f"src_copy{i}", canonical_ref=f"https://example.net/copy{i}", independence_group=f"copy-{i}", derived_from_source_ids=["src_policy"])
        data["sources"].append(source)
        edge = copy.deepcopy(data["evidence"][0])
        edge.update(evidence_id=f"ev_copy{i}", source_id=source["source_id"])
        data["evidence"].append(edge)
    assert kernel.coverage(data)["accepted_independence_group_count"] == 1
    assert kernel.coverage(data)["claims"][0]["independence_group_count"] == 1


def test_duplicate_artifact_with_different_group_does_not_count_twice():
    data = ledger()
    source = copy.deepcopy(data["sources"][0])
    source.update(source_id="src_dup", independence_group="different")
    data["sources"].append(source)
    edge = copy.deepcopy(data["evidence"][0])
    edge.update(evidence_id="ev_dup", source_id="src_dup")
    data["evidence"].append(edge)
    assert kernel.coverage(data)["accepted_independence_group_count"] == 1


@pytest.mark.parametrize("raw", ['{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}'])
def test_strict_json_input(raw):
    with pytest.raises(ValueError):
        kernel._load_json(raw)


def test_inline_long_json_does_not_become_filename():
    raw = json.dumps({"data": "x" * 5000})
    assert kernel._load_json(raw)["data"] == "x" * 5000


def test_refresh_explains_affected_inference():
    data = ledger()
    inference(data)
    data["sources"][0]["last_verified_at"] = "2020-01-01T00:00:00Z"
    report = kernel.refresh_plan(data)
    assert "clm_inference" in report["dependent_claim_ids"]


def test_audit_cli_can_enforce_readiness(tmp_path):
    path = tmp_path / "empty.json"
    path.write_text(json.dumps(kernel.template("Synthetic", "2026-09-13T00:00:00Z", "STANDARD")))
    result = subprocess.run([sys.executable, str(ROOT / "scripts/evidence_kernel.py"), "audit", "--ledger-json", str(path), "--require-ready"], capture_output=True, text=True, timeout=10)
    assert result.returncode == 1
    assert json.loads(result.stdout)["research_status"] == "PARTIAL"


def test_static_label_cannot_disable_live_policy():
    data = ledger()
    data["claims"][0]["temporal_sensitivity"] = "static"
    data["sources"][0]["last_verified_at"] = "2020-01-01T00:00:00Z"
    assert kernel.audit(data)["research_status"] == "REFRESH_REQUIRED"


def test_temporal_cli_supports_zero_cache_run_context(tmp_path):
    source = ledger()["sources"][0]
    source["verified_research_id"] = "res_test"
    path = tmp_path / "source.json"
    path.write_text(json.dumps(source))
    result = subprocess.run([sys.executable, str(ROOT / "scripts/evidence_kernel.py"), "temporal", "--source-json", str(path), "--claim-type", "service_status", "--as-of", "2026-08-25T21:44:00+02:00", "--research-id", "res_test", "--research-started-at", "2026-08-25T21:00:00+02:00"], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["temporal_status"] == "CURRENT"


def test_zero_cache_refresh_receives_run_identity():
    data = ledger()
    data["claims"][0]["claim_type"] = "service_status"
    data["research_contract"]["started_at"] = "2026-08-25T21:00:00+02:00"
    data["sources"][0]["verified_research_id"] = data["research_id"]
    assert kernel.refresh_plan(data)["refresh_required"] is False
    data["sources"][0]["verified_research_id"] = "different"
    assert kernel.refresh_plan(data)["refresh_required"] is True


def test_nonfinite_exponent_is_rejected():
    with pytest.raises(ValueError):
        kernel._load_json('{"value":1e999}')



# --- Degradation is reported, not hidden ----------------------------------
# `ready` is deliberately narrower than "well supported": a claim can be ready
# while its only support is a blog, or while independence is unknown. That is
# defensible only because separate rates carry those facts. If `ready` ever
# absorbed them, or a rate went constant, a consumer reading the coverage report
# would lose the distinction without anything failing.


def _coverage(mutate=None):
    led = copy.deepcopy(ledger())
    if mutate:
        mutate(led)
    return kernel.coverage(led)


def test_baseline_is_fully_supported():
    cov = _coverage()
    assert cov["claims"][0]["ready"] is True
    assert cov["primary_or_system_of_record_rate"] == 1.0
    assert cov["unknown_independence_support_count"] == 0


def test_non_primary_source_drops_the_primary_rate():
    assert _coverage(lambda l: l["sources"][0].__setitem__("source_role", "BLOG"))[
        "primary_or_system_of_record_rate"] == 0.0


def test_missing_independence_group_is_counted_as_unknown():
    cov = _coverage(lambda l: l["sources"][0].pop("independence_group", None))
    assert cov["unknown_independence_support_count"] == 1
    assert cov["accepted_independence_group_count"] == 0


@pytest.mark.parametrize("admission", ["REJECTED", None])
def test_readiness_still_requires_accepted_support(admission):
    def mutate(led):
        if admission is None:
            led["evidence"][0].pop("admission")
        else:
            led["evidence"][0]["admission"] = admission
    assert _coverage(mutate)["claims"][0]["ready"] is False
