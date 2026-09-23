from __future__ import annotations

import re
from typing import Any

from .constants import (
    ARCHETYPE_RULES,
    COUNCIL_VERSION,
    DECISION_KIND,
    DOMAIN_KEYWORDS,
    DOMAIN_ORDER,
    KERNEL_VERSION,
    RISK_SURFACE_RULES,
)
from .util import _clamp01, _dedupe, _hits, _mode_name, _norm

def infer_decision_archetype(query: str, options: Any = None) -> str:
    text = _norm(query)
    for archetype, triggers in ARCHETYPE_RULES:
        if any(t in text for t in triggers):
            return archetype
    if re.search(r"\b(a|b|c)\s+(czy|vs|versus|albo)\b", text):
        return "option_selection"
    # Three or more named options is not a binary decision, whatever the prose
    # looks like. The caller already told us the shape; prefer that over
    # guessing from wording.
    if isinstance(options, (list, tuple)) and len(options) >= 3:
        return "option_selection"
    return "binary"


def infer_risk_surfaces(query: str) -> list[str]:
    text = _norm(query)
    out = [surface for surface, triggers in RISK_SURFACE_RULES.items() if any(t in text for t in triggers)]
    if "ai" in text and any(t in text for t in ("health", "medycz", "employee", "pracownik", "education", "edukac", "finance", "finans")):
        out.extend(["legal", "responsible_ai"])
    return _dedupe(out)


def infer_jurisdictions(query: str, context: dict[str, Any] | None = None) -> list[str]:
    context = context or {}
    explicit = context.get("jurisdictions") or context.get("jurisdiction")
    if explicit:
        return _dedupe([str(x) for x in (explicit if isinstance(explicit, list) else [explicit])])
    text = _norm(query)
    out = []
    if any(t in text for t in ("polska", "poland", "rodo")):
        out.append("PL")
    if any(t in text for t in ("eu", "european union", "gdpr", "ai act", "unia europejska")):
        out.append("EU")
    if any(t in text for t in ("usa", "united states", " u.s.", " us ")):
        out.append("US")
    if any(t in text for t in ("uk", "united kingdom", "wielka brytania")):
        out.append("UK")
    return _dedupe(out) or ["unspecified"]


def profile_problem(query: str) -> dict[str, Any]:
    scores = {d: _hits(query, kws) for d, kws in DOMAIN_KEYWORDS.items()}
    primary = max(DOMAIN_ORDER, key=lambda d: (scores[d], -DOMAIN_ORDER.index(d)))
    if scores[primary] == 0:
        primary = "strategy"
    secondary = [d for d in DOMAIN_ORDER if d != primary and scores[d] > 0]
    secondary.sort(key=lambda d: (-scores[d], DOMAIN_ORDER.index(d)))
    text = _norm(query)
    hard = any(x in text for x in (
        "trudnym odwrotem", "trudny odwrot", "trudna do odwrócenia", "trudna do odwrocenia", "hard to reverse", "nieodwracal",
        "duza inwestycja", "duża inwestycja", "dużą inwestycj", "duza inwestycj", "acquisition", "przeję",
    ))
    high = hard or any(x in text for x in ("wysokie ryzyko", "high risk", "milion", "mln", "regulatory approval"))
    low = any(x in text for x in ("mały test", "maly test", "pilot", "eksperyment", "reversible")) and not high
    return {
        "primary_domain": primary,
        "secondary_domains": secondary[:3],
        "decision_kind": DECISION_KIND[primary],
        "decision_archetype": infer_decision_archetype(query),
        "reversibility": "hard_to_reverse" if hard else "reversible",
        "risk_level": "high" if high else ("low" if low else "medium"),
        "risk_surfaces": infer_risk_surfaces(query),
    }


def compile_decision_contract(question: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    context = dict(context or {})
    profile = profile_problem(question)
    options = context.get("options") or []
    if isinstance(options, str):
        options = [options]
    if (
        not context.get("decision_type")
        and len(options) >= 3
        and profile["decision_archetype"] == "binary"
    ):
        # Three or more named options is not a binary decision, whatever the
        # prose looks like. Only upgrade the generic fallback: a domain
        # archetype such as pricing or m_and_a drives specialist routing and
        # must not be replaced by the shape of the option list.
        profile = {**profile, "decision_archetype": "option_selection"}
    contract = {
        "question": str(question).strip(),
        "decision_type": context.get("decision_type") or profile["decision_archetype"],
        "objective": context.get("objective") or "maximize decision quality under current constraints",
        "options": [str(x)[:300] for x in options][:12],
        "status_quo": str(context.get("status_quo") or "")[:500],
        "constraints": [str(x)[:300] for x in (context.get("constraints") or [])][:12],
        "time_horizon": str(context.get("time_horizon") or "unspecified")[:120],
        "success_metric": str(context.get("success_metric") or "")[:300],
        "financial_impact": _clamp01(context.get("financial_impact", 0.5)),
        "strategic_impact": _clamp01(context.get("strategic_impact", 0.5)),
        "uncertainty": _clamp01(context.get("uncertainty", 0.5)),
        "reversibility": context.get("reversibility") or profile["reversibility"],
        "risk_level": context.get("risk_level") or profile["risk_level"],
        "cost_of_delay": _clamp01(context.get("cost_of_delay", 0.3)),
        "cost_of_false_positive": _clamp01(context.get("cost_of_false_positive", 0.5)),
        "cost_of_false_negative": _clamp01(context.get("cost_of_false_negative", 0.5)),
        "known_facts": [str(x)[:500] for x in (context.get("known_facts") or [])][:20],
        "known_unknowns": [str(x)[:500] for x in (context.get("known_unknowns") or [])][:20],
        "stakeholders": [str(x)[:200] for x in (context.get("stakeholders") or [])][:15],
        "execution_dependencies": [str(x)[:300] for x in (context.get("execution_dependencies") or [])][:15],
        "jurisdictions": infer_jurisdictions(question, context),
        "risk_surfaces": _dedupe(list(profile.get("risk_surfaces") or []) + [str(x) for x in (context.get("risk_surfaces") or [])]),
        "primary_domain": profile["primary_domain"],
        "secondary_domains": profile["secondary_domains"],
        "decision_kind": profile["decision_kind"],
    }
    if contract["decision_type"] in {"m_and_a", "market_entry", "hiring"} and "legal" not in contract["risk_surfaces"]:
        contract["risk_surfaces"].append("legal")
    return contract


def decision_value_score(profile_or_contract: dict[str, Any], financial_impact: float = 0.5,
                         uncertainty: float = 0.5, strategic_impact: float | None = None) -> float:
    risk = {"low": 0.2, "medium": 0.5, "high": 0.8}.get(profile_or_contract.get("risk_level"), 0.5)
    irreversible = 1.0 if profile_or_contract.get("reversibility") == "hard_to_reverse" else 0.0
    fin = _clamp01(profile_or_contract.get("financial_impact", financial_impact))
    unc = _clamp01(profile_or_contract.get("uncertainty", uncertainty))
    strat_source = profile_or_contract.get("strategic_impact")
    strat = _clamp01(strat_source if strat_source is not None else (risk if strategic_impact is None else strategic_impact))
    cost_error = max(_clamp01(profile_or_contract.get("cost_of_false_positive", 0.5)),
                     _clamp01(profile_or_contract.get("cost_of_false_negative", 0.5)))
    score = 0.24 * fin + 0.22 * unc + 0.22 * strat + 0.17 * irreversible + 0.15 * cost_error
    return round(_clamp01(score), 6)


def choose_council_mode(profile_or_contract: dict[str, Any], financial_impact: float = 0.5,
                        uncertainty: float = 0.5, strategic_impact: float | None = None) -> str:
    score = decision_value_score(profile_or_contract, financial_impact, uncertainty, strategic_impact)
    if score < 0.30 and profile_or_contract.get("risk_level") == "low" and profile_or_contract.get("reversibility") == "reversible":
        return "FAST"
    if score >= 0.72 or (profile_or_contract.get("risk_level") == "high" and profile_or_contract.get("reversibility") == "hard_to_reverse"):
        return "DEEP"
    return "STANDARD"


def mode_budget(mode: str) -> dict[str, Any]:
    mode = _mode_name(mode)
    budgets = {
        "FAST": {
            "adviser_count": 3, "expert_count": 3, "max_specialists": 1, "max_gatekeepers": 2,
            "max_frameworks": 1, "max_web_queries": 1, "max_analogies": 1,
            "counterfactual": False, "premortem": False, "minority_sentinel": False,
        },
        "STANDARD": {
            "adviser_count": 5, "expert_count": 5, "max_specialists": 3, "max_gatekeepers": 4,
            "max_frameworks": 3, "max_web_queries": 2, "max_analogies": 3,
            "counterfactual": False, "premortem": True, "minority_sentinel": True,
        },
        "DEEP": {
            "adviser_count": 7, "expert_count": 7, "max_specialists": 5, "max_gatekeepers": 6,
            "max_frameworks": 3, "max_web_queries": 5, "max_analogies": 3,
            "counterfactual": True, "premortem": True, "minority_sentinel": True,
        },
    }
    return dict(budgets.get(mode, budgets["STANDARD"]))

def critical_evidence_areas(contract: dict[str, Any]) -> list[str]:
    archetype = contract.get("decision_type")
    areas = ["customer", "operations"]
    if archetype in {"pricing", "market_entry", "m_and_a", "resource_allocation", "partnership"}:
        areas.extend(["finance", "market_demand"])
    if archetype in {"pricing", "launch", "product_investment"}:
        areas.extend(["willingness_to_pay", "product"])
    if archetype in {"market_entry", "m_and_a", "partnership"}:
        areas.append("competition")
    surfaces = set(contract.get("risk_surfaces") or [])
    if surfaces & {"legal", "privacy", "responsible_ai"}:
        areas.append("legal_regulatory")
    if "security" in surfaces:
        areas.append("security")
    if "people" in surfaces:
        areas.append("people")
    if "reputation" in surfaces:
        areas.append("reputation")
    return _dedupe(areas)[:10]


def required_confidence(profile_or_contract: dict[str, Any], evidence_coverage: float,
                        decision_value: float = 0.5) -> float:
    risk_bonus = {"low": 0.0, "medium": 0.06, "high": 0.12}.get(profile_or_contract.get("risk_level"), 0.06)
    reverse_bonus = 0.10 if profile_or_contract.get("reversibility") == "hard_to_reverse" else 0.0
    coverage_penalty = 0.15 * (1.0 - _clamp01(evidence_coverage))
    value_bonus = 0.12 * _clamp01(decision_value)
    error_cost = max(_clamp01(profile_or_contract.get("cost_of_false_positive", 0.5)),
                     _clamp01(profile_or_contract.get("cost_of_false_negative", 0.5)))
    error_bonus = 0.06 * error_cost
    return round(max(0.55, min(0.95, 0.52 + risk_bonus + reverse_bonus + coverage_penalty + value_bonus + error_bonus)), 6)


def plan_council(contract: dict[str, Any], mode: str | None = None) -> dict[str, Any]:
    from .routing import route_legal_risk, route_roles, select_frameworks
    selected_mode = _mode_name(mode or choose_council_mode(contract))
    budget = mode_budget(selected_mode)
    roles = route_roles(contract, selected_mode)
    fw_profile = {
        "primary_domain": contract.get("primary_domain", "strategy"),
        "secondary_domains": contract.get("secondary_domains", []),
        "decision_kind": contract.get("decision_kind", "strategy"),
        "reversibility": contract.get("reversibility", "reversible"),
        "risk_level": contract.get("risk_level", "medium"),
    }
    frameworks = select_frameworks(contract.get("question", ""), fw_profile, roles["advisers"], budget["max_frameworks"])
    value = decision_value_score(contract)
    legal = route_legal_risk(contract.get("question", ""), contract)
    stages = [
        "context_source_routing", "blind_round", "assumption_ledger", "decision_memory_post_blind", "base_rate_outside_view",
        "rebuttal_double_crux", "live_evidence", "temporal_truth", "freshness_gate", "evidence_coverage",
        "contradiction_coverage", "red_team", "evidence_judge", "chairman", "constraint_engine",
        "decision_validity_overlay", "snapshot", "writeback",
    ]
    if budget["premortem"]:
        stages.insert(6, "premortem")
    if budget["counterfactual"]:
        stages.insert(-4, "counterfactual")
    if budget["minority_sentinel"]:
        stages.insert(-5, "minority_sentinel")
    return {
        "council_version": COUNCIL_VERSION,
        "kernel_version": KERNEL_VERSION,
        "mode": selected_mode,
        "decision_value_score": value,
        "budget": budget,
        "roles": roles,
        "frameworks": frameworks,
        "critical_evidence_areas": critical_evidence_areas(contract),
        "legal_route": legal,
        "temporal_requirements": {
            "as_of_required": True,
            "freshness_gate_required": True,
            "current_claims_require_last_verified_at": True,
            "material_time_sensitive_claims_require_admissible_temporal_status": True,
        },
        "required_stages": stages,
    }
