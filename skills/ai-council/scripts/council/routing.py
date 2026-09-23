from __future__ import annotations

import json
import re
from typing import Any

from .constants import (
    DOMAIN_ORDER,
    FRAMEWORKS,
    INTERNAL_CONTEXT_RULES,
    LEGAL_DOMAIN_RULES,
    ROLE_REGISTRY,
    SPECIALIST_RULES,
)
from .contract import infer_jurisdictions, infer_risk_surfaces, mode_budget
from .util import _dedupe, _mode_name, _norm

def route_experts(profile: dict[str, Any], max_experts: int | None = None) -> list[str]:
    primary = profile["primary_domain"]
    candidates = [primary] + list(profile.get("secondary_domains") or [])
    complements = {
        "strategy": ["operator", "product_customer", "marketing", "growth", "offer_pricing", "sales"],
        "marketing": ["sales", "strategy", "growth", "product_customer", "offer_pricing", "operator"],
        "sales": ["marketing", "offer_pricing", "strategy", "product_customer", "operator", "growth"],
        "offer_pricing": ["sales", "marketing", "strategy", "product_customer", "growth", "operator"],
        "product_customer": ["strategy", "growth", "marketing", "operator", "sales", "offer_pricing"],
        "growth": ["marketing", "product_customer", "strategy", "operator", "offer_pricing", "sales"],
        "operator": ["strategy", "product_customer", "growth", "sales", "marketing", "offer_pricing"],
    }
    candidates += complements.get(primary, [])
    target = max(1, min(len(DOMAIN_ORDER), int(max_experts or 5)))
    out = []
    for expert in candidates + DOMAIN_ORDER:
        if expert in DOMAIN_ORDER and expert not in out:
            out.append(expert)
        if len(out) >= target:
            break
    return out


def dynamic_specialists(query: str, existing_experts: list[str] | None = None, max_specialists: int = 5) -> list[dict[str, str]]:
    text = _norm(query)
    existing = set(existing_experts or [])
    out = []
    for sid, triggers in SPECIALIST_RULES:
        if sid in existing:
            continue
        hits = [t for t in triggers if t in text]
        if hits:
            out.append({"id": sid, "name": ROLE_REGISTRY[sid]["name"], "reason": hits[0], "role_class": "specialist"})
        if len(out) >= max(0, int(max_specialists)):
            break
    return out


def route_legal_risk(query: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    context = context or {}
    text = _norm(query + " " + json.dumps(context, ensure_ascii=False, default=str))
    domains = []
    triggers = {}
    for domain, rules in LEGAL_DOMAIN_RULES:
        hits = [r for r in rules if r in text]
        if hits:
            domains.append(domain)
            triggers[domain] = hits[:3]
    if re.search(r"\bai\b", text) and "ai_regulation" not in domains:
        domains.append("ai_regulation")
        triggers["ai_regulation"] = ["ai"]
    jurisdictions = infer_jurisdictions(query, context)
    high_impact_ai = ("ai_regulation" in domains or "responsible_ai" in infer_risk_surfaces(text)) and any(
        t in text for t in ("health", "medycz", "employee", "pracownik", "education", "edukac", "finance", "finans")
    )
    required = bool(domains or context.get("force_legal_gate") or high_impact_ai)
    counsel_required = bool(context.get("material_legal_uncertainty") or context.get("counsel_required"))
    return {
        "required": required,
        "jurisdictions": jurisdictions,
        "legal_domains": domains,
        "trigger_map": triggers,
        "high_impact_ai": bool(high_impact_ai),
        "default_gate_status": "COUNSEL_REQUIRED" if counsel_required else ("CLEAR_WITH_CONTROLS" if required else "NOT_REQUIRED"),
        "note": "Determine current law from primary jurisdiction-specific sources; do not encode stale legal conclusions in the router.",
    }


def detect_missing_perspectives(query: str, existing_experts: list[str] | None = None) -> list[str]:
    existing = set(existing_experts or [])
    missing = [x["id"] for x in dynamic_specialists(query, existing_experts, max_specialists=10)]
    surfaces = infer_risk_surfaces(query)
    mapping = {
        "legal": "legal", "privacy": "privacy", "security": "security", "financial": "finance",
        "responsible_ai": "responsible_ai", "reputation": "reputation", "technical": "technical", "people": "people",
    }
    for surface in surfaces:
        role = mapping.get(surface)
        if role and role not in existing and role not in missing:
            missing.append(role)
    text = _norm(query)
    if any(token in text for token in ("mln", "milion", "duża inwestycj", "duza inwestycj")) and "finance" not in existing and "finance" not in missing:
        missing.insert(0, "finance")
    return _dedupe(missing)


def route_roles(contract: dict[str, Any], mode: str) -> dict[str, Any]:
    mode = _mode_name(mode)
    budget = mode_budget(mode)
    profile = {
        "primary_domain": contract.get("primary_domain", "strategy"),
        "secondary_domains": contract.get("secondary_domains", []),
    }
    advisers = route_experts(profile, budget["adviser_count"])
    question = contract.get("question", "")
    specialists = [x["id"] for x in dynamic_specialists(question, advisers, budget["max_specialists"])]

    archetype = contract.get("decision_type")
    if archetype == "m_and_a":
        specialists = _dedupe(["m_and_a", "finance"] + specialists)
    elif archetype == "market_entry":
        specialists = _dedupe(["localization", "finance"] + specialists)
    elif archetype == "resource_allocation":
        specialists = _dedupe(["finance", "data"] + specialists)
    elif archetype == "hiring":
        specialists = _dedupe(["people", "finance"] + specialists)
    specialists = specialists[: budget["max_specialists"]]

    surfaces = set(contract.get("risk_surfaces") or [])
    gatekeepers = []
    if "legal" in surfaces or archetype in {"m_and_a", "market_entry", "hiring", "partnership"}:
        gatekeepers.append("legal")
    if "privacy" in surfaces:
        gatekeepers.append("privacy")
    if "security" in surfaces:
        gatekeepers.append("security")
    if "financial" in surfaces or contract.get("financial_impact", 0) >= 0.7 or archetype in {"m_and_a", "resource_allocation"}:
        gatekeepers.append("financial_risk")
    if "responsible_ai" in surfaces:
        gatekeepers.append("responsible_ai")
    if "reputation" in surfaces:
        gatekeepers.append("reputation")
    # Cost budgets may limit advisers, never the required risk gates.
    gatekeepers = _dedupe(gatekeepers)

    auditors = ["red_team", "evidence_judge"]
    if budget.get("minority_sentinel"):
        auditors.append("minority_sentinel")
    if mode == "DEEP":
        auditors.append("process_auditor")

    return {
        "advisers": advisers,
        "specialists": specialists,
        "gatekeepers": gatekeepers,
        "gatekeeper_budget_exceeded": len(gatekeepers) > budget["max_gatekeepers"],
        "auditors": auditors,
        "authority": ["chairman"],
        "role_classes": {rid: ROLE_REGISTRY[rid]["class"] for rid in _dedupe(advisers + specialists + gatekeepers + auditors + ["chairman"])},
    }


def select_frameworks(query: str, profile: dict[str, Any], routed_experts: list[str], max_frameworks: int = 3) -> dict[str, Any]:
    matches = []
    secondary = set(profile.get("secondary_domains") or [])
    for order, fw in enumerate(FRAMEWORKS):
        score = 0
        reasons = []
        if profile.get("primary_domain") in fw["domains"]:
            score += 4
            reasons.append(f"primary_domain:{profile['primary_domain']}")
        sec_matches = [d for d in secondary if d in fw["domains"]]
        if sec_matches:
            score += min(4, 2 * len(sec_matches))
            reasons.extend(f"secondary_domain:{d}" for d in sorted(sec_matches))
        if profile.get("decision_kind") in fw["kinds"]:
            score += 3
            reasons.append(f"decision_kind:{profile['decision_kind']}")
        expert_matches = [e for e in routed_experts if e in fw["experts"]]
        if expert_matches:
            score += min(2, len(expert_matches))
            reasons.extend(f"routed_expert:{e}" for e in expert_matches[:2])
        trigger_hits = [kw for kw in fw["triggers"] if kw.casefold() in _norm(query)]
        if trigger_hits:
            score += min(3, len(trigger_hits))
            reasons.extend(f"keyword:{kw}" for kw in trigger_hits[:3])
        if fw["id"] == "reversibility_experiment" and profile.get("reversibility") == "reversible" and trigger_hits:
            score += 2
            reasons.append("reversibility_bonus")
        if fw["id"] == "strategic_choice" and (profile.get("reversibility") == "hard_to_reverse" or profile.get("risk_level") == "high"):
            score += 2
            reasons.append("high_risk_strategy_bonus")
        if score >= 5:
            matches.append({
                "framework_id": fw["id"], "score": score, "reason_labels": reasons,
                "assigned_expert_ids": expert_matches, "_order": order,
            })
    matches.sort(key=lambda x: (-x["score"], x["_order"], x["framework_id"]))
    matches = matches[:max(0, int(max_frameworks))]
    by_expert = {e: [] for e in routed_experts}
    for match in matches:
        for expert in match["assigned_expert_ids"]:
            if expert in by_expert and len(by_expert[expert]) < 2:
                by_expert[expert].append(match["framework_id"])
        match.pop("_order", None)
    return {
        "status": "ok" if matches else "empty",
        "policy_version": "framework-selector-v4",
        "matches": matches,
        "by_expert": by_expert,
        "error_labels": [],
    }

def route_internal_context(query: str) -> dict[str, Any]:
    text = _norm(query)
    routes = []
    for claim_family, triggers, systems in INTERNAL_CONTEXT_RULES:
        hits = sum(1 for trigger in triggers if trigger in text)
        if hits:
            routes.append({"claim_family": claim_family, "systems": systems, "hits": hits})
    routes.sort(key=lambda r: (-r["hits"], r["claim_family"]))
    if not routes:
        routes = [{"claim_family": "general_private_context", "systems": ["Notion", "Google_Drive"], "hits": 0}]
    return {"routes": routes, "primary": routes[0], "rule": "use the system-of-record for the claim; do not treat all private context as Drive"}
