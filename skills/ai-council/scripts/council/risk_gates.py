from __future__ import annotations

import json
from typing import Any

from .constants import ENVELOPE_VERDICTS, EVIDENCE_PURPOSES, GATE_STATUSES, PREMISE_ROLES, VERDICTS
from .contract import check_contract_values
from .util import _aware_time, _boolean, _rows, _strings, _unit_interval


def validate_evidence_use(use: dict | None) -> None:
    """Validate consumer-owned scope; missing legacy policy remains unassessed."""
    if use is None:
        return
    if not isinstance(use, dict) or set(use) != {"purpose", "as_of", "premises"}:
        raise ValueError("evidence_use requires purpose/as_of/premises")
    if not isinstance(use["purpose"], str) or use["purpose"] not in EVIDENCE_PURPOSES:
        raise ValueError("invalid evidence purpose")
    _aware_time(use["as_of"], "evidence_use.as_of")
    rows = _rows(use["premises"], "premises")
    if not 1 <= len(rows) <= 32:
        raise ValueError("evidence_use requires 1 to 32 premises")
    _strings([row.get("claim_id") for row in rows], "required claim ids")
    for row in rows:
        if (set(row) != {"claim_id", "role", "scope"} or not isinstance(row["role"], str)
                or row["role"] not in PREMISE_ROLES or not isinstance(row["scope"], dict) or not row["scope"]):
            raise ValueError("each premise requires a known role and explicit nonempty scope")
        json.dumps(row["scope"], sort_keys=True, allow_nan=False)


def basis_admission(graph: dict, coverage: dict, observations: dict | None,
                    contract: dict, use: dict | None) -> dict:
    """Compute scope policy for supplied records; the receiving caller owns actual reruns.

    This pure helper cannot authenticate observation dictionaries. The domain
    receiving gate reruns the Evidence owner with its own plan/root/context.
    """
    check_contract_values(contract)
    validate_evidence_use(use)
    result = {"policy_version": "decision-basis/v1", "scope": use["purpose"] if use else "unassessed",
              "eligible": False, "positive_verdict": "DEFER", "eligible_premise_ids": [],
              "required_fact_ids": [], "observed_fact_ids": [], "missing_premise_ids": [],
              "blockers": [], "caveats": [], "execution_authorized": False,
              "limit": "policy is not authentication; consumer must rerun applicable controlled local observations"}
    if use is None:
        result["blockers"].append("Consumer evidence scope is unassessed")
        return result
    claims = _rows(graph.get("claims"), "claims")
    _strings([claim.get("claim_id") for claim in claims], "claim ids")
    by_id = {claim["claim_id"]: claim for claim in claims}
    roles = {row["claim_id"]: row for row in use["premises"]}
    material = {claim["claim_id"] for claim in claims if claim.get("materiality") in ("material", "critical")}
    uncovered = material - roles.keys()
    if uncovered:
        result["blockers"].append("Material premises lack a consumer-defined role")
        result["missing_premise_ids"].extend(sorted(uncovered))
    if use["as_of"] != graph.get("research_contract", {}).get("as_of"):
        result["blockers"].append("Consumer and research as_of differ")
    metadata_rows = _rows(coverage.get("all_claims", []), "metadata coverage")
    _strings([row.get("claim_id") for row in metadata_rows], "metadata claim ids")
    metadata = {row["claim_id"]: row for row in metadata_rows}
    observed_rows = _rows((observations or {}).get("claims", []), "observations")
    _strings([row.get("claim_id") for row in observed_rows], "observed claim ids")
    observed = {row["claim_id"]: row for row in observed_rows}
    eligible = set()
    inference_ids = set()
    for cid, premise in roles.items():
        claim = by_id.get(cid)
        role = premise["role"]
        if role in ("controlled_fact", "document_fact", "safeguard"):
            result["required_fact_ids"].append(cid)
        if not claim or json.dumps(claim.get("scope", {}), sort_keys=True, allow_nan=False) != json.dumps(premise["scope"], sort_keys=True, allow_nan=False):
            continue
        basis, status = claim.get("basis"), claim.get("status")
        if role in ("controlled_fact", "document_fact", "safeguard"):
            expected_scope = "document_content" if role == "document_fact" else "controlled_state"
            proof = observed.get(cid, {})
            meta = metadata.get(cid, {})
            if (basis == "verified_fact" and claim.get("epistemic_kind") == "FACT" and status == "VERIFIED"
                    and claim.get("contradiction_tested") is True and meta.get("metadata_ready") is True
                    and meta.get("falsifier_search_completed") is True and proof.get("status") == "MATCH"
                    and proof.get("observed_scope") == expected_scope):
                eligible.add(cid)
                result["observed_fact_ids"].append(cid)
        elif role == "inference":
            if (basis == "verified_fact" and claim.get("epistemic_kind") == "INFERENCE" and status == "SUPPORTED_INFERENCE"
                    and claim.get("contradiction_tested") is True
                    and metadata.get(cid, {}).get("metadata_ready") is True
                    and metadata.get(cid, {}).get("falsifier_search_completed") is True):
                inference_ids.add(cid)
        elif ((role == "method" and basis == "framework_method" and status in ("PARTIAL", "SUPPORTED_INFERENCE"))
              or (role == "intent" and basis == "user_supplied" and status in ("PARTIAL", "UNKNOWN"))
              or (role in ("estimate", "hypothesis") and basis == "assumption" and status in ("PARTIAL", "UNKNOWN", "SUPPORTED_INFERENCE"))):
            eligible.add(cid)
            result["caveats"].append(cid + ": " + basis + " remains a nonfact premise")
    # An inference retains its kind and cannot launder an unobserved dependency.
    while inference_ids:
        admitted = {cid for cid in inference_ids if by_id[cid].get("depends_on_claim_ids")
                    and set(by_id[cid]["depends_on_claim_ids"]) <= eligible
                    and all(roles[dep]["role"] in ("controlled_fact", "document_fact", "safeguard", "inference")
                            for dep in by_id[cid]["depends_on_claim_ids"])}
        if not admitted:
            break
        eligible.update(admitted)
        inference_ids.difference_update(admitted)
        result["caveats"].extend(cid + ": supported inference, not a VERIFIED observation" for cid in sorted(admitted))
    for row in _rows(graph.get("gaps", []), "gaps"):
        allowed_hypothesis_gap = (row.get("severity") == "material" and row.get("claim_id") in roles
                                  and roles[row["claim_id"]]["role"] in ("estimate", "hypothesis")
                                  and use["purpose"] != "method_choice")
        if row.get("severity") in ("critical", "material") and not allowed_hypothesis_gap:
            result["blockers"].append("A required factual or critical evidence gap remains")
    for row in _rows(graph.get("contradictions", []), "contradictions"):
        if row.get("resolution") == "UNRESOLVED" and (row.get("claim_id") in roles or row.get("severity") in ("critical", "material")):
            result["blockers"].append("An applicable contradiction remains unresolved")
    missing = set(roles) - eligible
    result["missing_premise_ids"] = sorted(set(result["missing_premise_ids"]) | missing)
    result["eligible_premise_ids"] = sorted(eligible)
    for key in ("observed_fact_ids", "required_fact_ids"):
        result[key].sort()
    purpose = use["purpose"]
    has_hypothesis = any(p["role"] == "hypothesis" for p in roles.values())
    has_safeguard = any(p["role"] == "safeguard" for p in roles.values())
    low_reversible = contract.get("risk_level") == "low" and contract.get("reversibility") == "reversible"
    if purpose == "method_choice" and any(p["role"] == "hypothesis" for p in roles.values()):
        result["blockers"].append("Method choice cannot substitute a world hypothesis")
    if purpose in ("action", "trial") and not any(p["role"] in ("controlled_fact", "safeguard") for p in roles.values()):
        result["blockers"].append("Actual action requires observed controlled factual prerequisites")
    if purpose == "action" and has_hypothesis:
        result["blockers"].append("A tested hypothesis requires an explicit consumer trial scope")
    if purpose == "trial":
        if not low_reversible or not has_safeguard or not has_hypothesis:
            result["blockers"].append("Hypothesis testing needs a low-risk reversible scope and observed safeguards")
        if any(by_id.get(cid, {}).get("materiality") == "critical" and row["role"] == "hypothesis" for cid, row in roles.items()):
            result["blockers"].append("A critical unobserved hypothesis cannot clear this bounded trial")
    result["eligible"] = not result["blockers"] and not result["missing_premise_ids"]
    if result["eligible"]:
        result["positive_verdict"] = "TEST" if purpose == "trial" else "GO"
    return result

def gate_verdict(proposed_verdict: str, confidence: float, required_confidence_value: float,
                 reversible_experiment_available: bool, critical_gap: str | None = None,
                 gate_statuses: dict[str, str] | None = None, controls_implemented: bool = False,
                 freshness_status: str = "CLEAR", human_approval_required: bool = False,
                 human_approved: bool = False, required_gatekeepers: list[str] | None = None) -> str:
    """Apply declared constraints, not factual verification or execution authorization.

    A supplied BLOCK remains NO-GO even when other evidence needs refresh. That
    preserves the constraint; it does not authenticate its basis. Unknown inputs
    never become confidence zero, approval, implemented controls, or a clear gate.
    """
    conf = _unit_interval(confidence, "confidence")
    required = _unit_interval(required_confidence_value, "required_confidence")
    experiment = _boolean(reversible_experiment_available, "reversible_experiment_available")
    _boolean(controls_implemented, "controls_implemented")
    _boolean(human_approval_required, "human_approval_required")
    _boolean(human_approved, "human_approved")
    if critical_gap is not None and (not isinstance(critical_gap, str) or not critical_gap.strip()):
        raise ValueError("critical_gap must be null or nonempty text")
    if gate_statuses is not None and not isinstance(gate_statuses, dict):
        raise ValueError("gate_statuses must be an object")
    statuses = {}
    for name, status in (gate_statuses or {}).items():
        if not isinstance(name, str) or not name.strip() or not isinstance(status, str):
            raise ValueError("invalid gate name or status")
        statuses[name] = status.strip().upper()
    needed = _strings(required_gatekeepers if required_gatekeepers is not None else [], "required_gatekeepers")
    verdict = proposed_verdict.strip().upper() if isinstance(proposed_verdict, str) else "DEFER"
    if "BLOCK" in statuses.values():
        return "NO-GO"
    if verdict not in VERDICTS or any(v not in GATE_STATUSES for v in statuses.values()):
        return "DEFER"
    if any(name not in statuses or statuses[name] == "NOT_REQUIRED" for name in needed):
        return "DEFER"
    if "COUNSEL_REQUIRED" in statuses.values():
        return "DEFER"
    if not isinstance(freshness_status, str) or freshness_status.strip().upper() != "CLEAR":
        return "DEFER"
    if human_approval_required and not human_approved:
        return "DEFER"
    # A trial is not permission to skip safeguards required for the assessed scope.
    if "CLEAR_WITH_CONTROLS" in statuses.values() and not controls_implemented:
        return "DEFER"
    if verdict in {"GO", "NO-GO"} and (critical_gap or conf < required):
        return "TEST" if experiment else "DEFER"
    return verdict

def envelope_verdict(verdict: str) -> str:
    """Return the CW-AIP v2 DecisionEnvelope spelling of a Council verdict.

    The Council writes `NO-GO`; the v2 decision schema accepts `NO_GO`. `GO`,
    `TEST` and `DEFER` are unchanged. Anything else is refused rather than guessed.
    """
    if not isinstance(verdict, str) or verdict not in ENVELOPE_VERDICTS:
        raise ValueError(f"{verdict!r} is not a Council verdict (expected one of {sorted(VERDICTS)})")
    return ENVELOPE_VERDICTS[verdict]

def build_human_handoff_packet(kind: str, decision: dict[str, Any], issue: dict[str, Any]) -> dict[str, Any]:
    kind = str(kind or "expert").lower()
    packet_type = {"legal": "COUNSEL_PACKET", "security": "SECURITY_REVIEW_PACKET", "finance": "FINANCE_APPROVAL_PACKET", "medical": "DOMAIN_EXPERT_PACKET"}.get(kind, "DOMAIN_EXPERT_PACKET")
    return {
        "packet_type": packet_type,
        "decision": decision.get("question") or decision.get("decision") or "",
        "decision_key": decision.get("decision_key"),
        "jurisdictions": decision.get("jurisdictions") or [],
        "known_facts": decision.get("known_facts") or [],
        "exact_question": issue.get("question") or issue.get("exact_question") or "",
        "material_uncertainty": issue.get("material_uncertainty") or issue.get("uncertainty") or "",
        "primary_sources": issue.get("primary_sources") or [],
        "alternative_interpretations": issue.get("alternative_interpretations") or [],
        "business_consequence": issue.get("business_consequence") or "",
        "deadline": issue.get("deadline") or "",
        "decision_change_condition": issue.get("decision_change_condition") or "",
        "return_evidence_class": "HUMAN_EXPERT_EVIDENCE",
        "scope_is_bounded": True,
    }


def tool_authority_assessment(action: dict[str, Any]) -> dict[str, Any]:
    flags = {
        "write": bool(action.get("write", False)),
        "external_side_effect": bool(action.get("external_side_effect", False)),
        "financial": bool(action.get("financial", False)),
        "public": bool(action.get("public", False)),
        "destructive": bool(action.get("destructive", False)),
        "credential_sensitive": bool(action.get("credential_sensitive", False)),
        "sensitive_data": bool(action.get("sensitive_data", False)),
        "irreversible": bool(action.get("irreversible", False)),
    }
    score = 0
    if flags["write"]:
        score = max(score, 1)
    if flags["external_side_effect"] or flags["public"]:
        score = max(score, 2)
    if flags["financial"] or flags["destructive"] or flags["credential_sensitive"] or flags["sensitive_data"]:
        score = max(score, 3)
    if flags["irreversible"] and (flags["financial"] or flags["destructive"] or flags["public"] or flags["sensitive_data"]):
        score = 4
    klass = f"T{score}"
    return {
        "authority_class": klass,
        "approval_required": score >= 2,
        "explicit_human_approval_required": score >= 3,
        "execute_automatically": score <= 1,
        "flags": flags,
        "rule": "higher tool authority requires stronger approval; evidence gathering must not silently escalate into side effects",
    }
