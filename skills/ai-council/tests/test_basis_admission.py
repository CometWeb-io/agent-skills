"""Decision policy unit controls; supplied observation dictionaries are not authentication."""
import copy
import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("basis_council", Path(__file__).parents[1] / "scripts/council_kernel.py")
kernel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kernel)


def case(purpose="action", role="controlled_fact", basis="verified_fact"):
    claim = {"claim_id": "release", "claim_text": "Controlled local candidate is ready.", "basis": basis,
             "epistemic_kind": "FACT", "status": "VERIFIED" if basis == "verified_fact" else "PARTIAL",
             "materiality": "material", "scope": {"candidate": "synthetic-A"}, "depends_on_claim_ids": [],
             "contradiction_tested": True}
    graph = {"research_contract": {"as_of": "2026-10-11T10:00:00Z"}, "claims": [claim],
             "gaps": [], "contradictions": []}
    coverage = {"all_claims": [{"claim_id": "release", "metadata_ready": basis == "verified_fact",
                               "falsifier_search_completed": True}]}
    observations = {"claims": [{"claim_id": "release", "status": "MATCH", "observed_scope": "controlled_state"}]}
    contract = kernel.compile_decision_contract("Review a reversible local technical candidate",
                {"decision_type": "binary", "risk_level": "low", "reversibility": "reversible", "risk_surfaces": ["technical"]})
    use = {"purpose": purpose, "as_of": graph["research_contract"]["as_of"],
           "premises": [{"claim_id": "release", "role": role, "scope": copy.deepcopy(claim["scope"])}]}
    return [graph, coverage, observations, contract, use]


def assess(values):
    return kernel.basis_admission(*values)


def test_controlled_fact_needs_both_metadata_and_applicable_observation():
    values = case()
    result = assess(values)
    assert result["eligible"] is True
    assert result["observed_fact_ids"] == ["release"]
    assert result["positive_verdict"] == "GO"
    assert result["execution_authorized"] is False
    values[2]["claims"][0]["status"] = "MISMATCH"
    assert assess(values)["eligible"] is False


@pytest.mark.parametrize("change", ["legacy", "document", "scope", "time", "metadata", "unknown", "missing", "critical-gap", "contradiction", "supporting-falsifier"])
def test_context_or_record_changes_cannot_clear_required_facts(change):
    values = case(); graph, coverage, observations, _, use = values
    if change == "legacy":
        graph["claims"][0].pop("basis")
    elif change == "document":
        observations["claims"][0]["observed_scope"] = "document_content"
    elif change == "scope":
        graph["claims"][0]["scope"] = {"candidate": "other"}
    elif change == "time":
        graph["research_contract"]["as_of"] = "2030-01-01T00:00:00Z"
    elif change == "metadata":
        coverage["all_claims"][0]["metadata_ready"] = False
    elif change == "unknown":
        graph["claims"].append({**graph["claims"][0], "claim_id": "hidden-material"})
    elif change == "missing":
        graph["claims"] = []
    elif change == "critical-gap":
        graph["gaps"] = [{"claim_id": "release", "severity": "critical"}]
    elif change == "contradiction":
        graph["contradictions"] = [{"claim_id": "release", "severity": "material", "resolution": "UNRESOLVED"}]
    else:
        graph["claims"][0]["materiality"] = "supporting"
        coverage["all_claims"][0]["falsifier_search_completed"] = False
    assert assess(values)["eligible"] is False


@pytest.mark.parametrize("basis", ["user_supplied", "assumption", "framework_method"])
def test_nonfacts_cannot_replace_world_prerequisites(basis):
    assert assess(case(basis=basis))["eligible"] is False


def test_method_choice_does_not_require_world_factual_ready():
    values = case("method_choice", "method", "framework_method")
    values[3] = kernel.compile_decision_contract("Choose an analytical framework for M&A",
                    {"decision_type": "m_and_a", "risk_level": "high", "reversibility": "hard_to_reverse"})
    result = assess(values)
    assert result["eligible"] is True
    assert result["observed_fact_ids"] == []
    assert result["scope"] == "method_choice"
    assert result["caveats"]


@pytest.mark.parametrize("role,basis", [("method", "framework_method"), ("intent", "user_supplied"), ("hypothesis", "assumption")])
def test_planning_preserves_caveated_nonfact_inputs(role, basis):
    result = assess(case("planning", role, basis))
    assert result["eligible"] is True
    assert result["observed_fact_ids"] == []
    assert result["caveats"]


def test_document_fact_cannot_be_reused_as_action_world_fact():
    values = case("planning", "document_fact")
    values[2]["claims"][0]["observed_scope"] = "document_content"
    assert assess(values)["eligible"] is True
    values[4]["purpose"] = "action"
    assert assess(values)["eligible"] is False


def trial():
    values = case("trial", "safeguard")
    graph, coverage, _, _, use = values
    hypothesis = {**graph["claims"][0], "claim_id": "effect", "basis": "assumption", "status": "UNKNOWN"}
    graph["claims"].append(hypothesis)
    coverage["all_claims"].append({"claim_id": "effect", "metadata_ready": False, "falsifier_search_completed": False})
    use["premises"].append({"claim_id": "effect", "role": "hypothesis", "scope": hypothesis["scope"]})
    graph["gaps"].append({"claim_id": "effect", "severity": "material"})
    return values


def test_trial_can_test_an_unknown_hypothesis_with_observed_safeguards():
    values = trial(); result = assess(values)
    assert result["eligible"] is True
    assert result["positive_verdict"] == "TEST"
    assert result["observed_fact_ids"] == ["release"]
    assert values[0]["claims"][1]["status"] == "UNKNOWN"


@pytest.mark.parametrize("change", ["no-safeguard", "unobserved", "documentary", "high-risk", "irreversible", "critical-hypothesis"])
def test_trial_does_not_bypass_controls_or_raise_hypothesis_to_fact(change):
    values = trial()
    if change == "no-safeguard":
        values[4]["premises"][0]["role"] = "controlled_fact"
    elif change == "unobserved":
        values[2]["claims"] = []
    elif change == "documentary":
        values[2]["claims"][0]["observed_scope"] = "document_content"
    elif change == "high-risk":
        values[3]["risk_level"] = "high"
    elif change == "irreversible":
        values[3]["reversibility"] = "hard_to_reverse"
    else:
        values[0]["gaps"][0]["severity"] = "critical"
    assert assess(values)["eligible"] is False


def test_required_fact_cannot_disappear_by_downcasting_materiality():
    values = case(); values[0]["claims"][0]["materiality"] = "supporting"
    values[2]["claims"] = []
    assert assess(values)["eligible"] is False


def test_missing_consumer_policy_has_no_inferred_method_or_fact_admission():
    values = list(case()); values[4] = None
    result = assess(values)
    assert result["eligible"] is False
    assert result["eligible_premise_ids"] == []


def test_caveated_estimate_can_inform_fact_qualified_action_without_becoming_fact():
    values = case(); graph, coverage, _, contract, use = values
    estimate = {**graph["claims"][0], "claim_id": "future-cost", "basis": "assumption", "status": "PARTIAL"}
    graph["claims"].append(estimate)
    coverage["all_claims"].append({"claim_id": "future-cost", "metadata_ready": False, "falsifier_search_completed": False})
    use["premises"].append({"claim_id": "future-cost", "role": "estimate", "scope": estimate["scope"]})
    contract.update(risk_level="high", reversibility="hard_to_reverse")
    result = assess(values)
    assert result["eligible"] is True
    assert result["positive_verdict"] == "GO"
    assert result["required_fact_ids"] == result["observed_fact_ids"] == ["release"]
    assert graph["claims"][1]["status"] == "PARTIAL"
    assert result["caveats"]


def test_inference_requires_observed_dependency_closure_and_retains_kind():
    values = case(); graph, coverage, _, _, use = values
    inference = {**graph["claims"][0], "claim_id": "conclusion", "epistemic_kind": "INFERENCE",
                 "status": "SUPPORTED_INFERENCE", "depends_on_claim_ids": ["release"]}
    graph["claims"].append(inference)
    coverage["all_claims"].append({"claim_id": "conclusion", "metadata_ready": True, "falsifier_search_completed": True})
    use["premises"].append({"claim_id": "conclusion", "role": "inference", "scope": inference["scope"]})
    assert assess(values)["eligible"] is True
    assert assess(values)["observed_fact_ids"] == ["release"]
    assert inference["status"] == "SUPPORTED_INFERENCE"
    values[2]["claims"] = []
    assert assess(values)["eligible"] is False


def test_inference_with_unchecked_contradictions_is_ineligible():
    values = case(); graph, coverage, _, _, use = values
    inference = {**graph["claims"][0], "claim_id": "unchecked-conclusion", "epistemic_kind": "INFERENCE",
                 "status": "SUPPORTED_INFERENCE", "contradiction_tested": False, "depends_on_claim_ids": ["release"]}
    graph["claims"].append(inference)
    coverage["all_claims"].append({"claim_id": inference["claim_id"], "metadata_ready": True, "falsifier_search_completed": True})
    use["premises"].append({"claim_id": inference["claim_id"], "role": "inference", "scope": inference["scope"]})
    assert assess(values)["eligible"] is False
