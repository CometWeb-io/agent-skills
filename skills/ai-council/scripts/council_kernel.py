from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from datetime import datetime
from typing import Any

COUNCIL_VERSION = "5.0"
KERNEL_VERSION = "5.0.0"

VERDICTS = {"GO", "NO-GO", "TEST", "DEFER"}
GATE_STATUSES = {"NOT_REQUIRED", "CLEAR", "CLEAR_WITH_CONTROLS", "COUNSEL_REQUIRED", "BLOCK"}
TEMPORAL_STATUSES = {"CURRENT", "NEAR_EXPIRY", "STALE", "SUPERSEDED", "DRAFT", "NOT_YET_EFFECTIVE", "UNKNOWN"}
DECISION_VALIDITY_STATUSES = {"VALID", "WATCH", "STALE", "REOPEN", "SUPERSEDED"}

FRESHNESS_POLICIES: dict[str, dict[str, Any]] = {
    "law_regulation": {"max_age_hours": 24, "requires_live_verification": True, "near_expiry_ratio": 0.50},
    "regulatory_guidance": {"max_age_hours": 24, "requires_live_verification": True, "near_expiry_ratio": 0.50},
    "security_advisory": {"max_age_hours": 6, "requires_live_verification": True, "near_expiry_ratio": 0.50},
    "vendor_policy": {"max_age_hours": 24, "requires_live_verification": True, "near_expiry_ratio": 0.75},
    "competitor_pricing": {"max_age_hours": 24, "requires_live_verification": False, "near_expiry_ratio": 0.75},
    "breaking_market": {"max_age_hours": 6, "requires_live_verification": False, "near_expiry_ratio": 0.67},
    "internal_metric": {"max_age_hours": 4, "requires_system_of_record": True, "near_expiry_ratio": 0.50},
    "official_technical_docs": {"max_age_hours": 168, "requires_live_verification": False, "near_expiry_ratio": 0.75},
    "academic_evidence": {"max_age_hours": 2160, "requires_live_verification": False, "near_expiry_ratio": 0.80},
    "doctrine": {"max_age_hours": None, "versioned_static": True, "near_expiry_ratio": 1.0},
    "general_web": {"max_age_hours": 168, "requires_live_verification": False, "near_expiry_ratio": 0.75},
}

SOURCE_AUTHORITY_REGISTRY: dict[str, dict[str, Any]] = {
    "law_regulation": {
        "preferred_authority": ["official_legislation", "regulator", "court_or_competent_authority", "official_guidance"],
        "secondary_authority": ["qualified_legal_commentary"],
        "freshness_policy": "law_regulation",
    },
    "regulatory_guidance": {
        "preferred_authority": ["regulator", "official_guidance", "official_legislation"],
        "secondary_authority": ["qualified_legal_commentary"],
        "freshness_policy": "regulatory_guidance",
    },
    "security_advisory": {
        "preferred_authority": ["vendor_security_advisory", "cisa_kev", "nvd_or_cve_authority", "maintainer_advisory"],
        "secondary_authority": ["owasp", "reputable_security_research"],
        "freshness_policy": "security_advisory",
    },
    "competitor_pricing": {
        "preferred_authority": ["official_competitor_pricing", "official_terms_or_checkout"],
        "secondary_authority": ["reputable_archive_or_marketplace"],
        "freshness_policy": "competitor_pricing",
    },
    "internal_metric": {
        "preferred_authority": ["internal_system_of_record"],
        "secondary_authority": ["approved_internal_snapshot"],
        "freshness_policy": "internal_metric",
    },
    "official_technical_docs": {
        "preferred_authority": ["official_documentation", "official_release_notes", "maintainer_repository"],
        "secondary_authority": ["reputable_technical_reference"],
        "freshness_policy": "official_technical_docs",
    },
    "academic_evidence": {
        "preferred_authority": ["peer_reviewed_primary_research", "official_research_institution"],
        "secondary_authority": ["systematic_review", "preprint_with_caveat"],
        "freshness_policy": "academic_evidence",
    },
    "breaking_market": {
        "preferred_authority": ["primary_company_or_government_source", "high_quality_wire_or_financial_source"],
        "secondary_authority": ["reputable_press"],
        "freshness_policy": "breaking_market",
    },
    "vendor_policy": {
        "preferred_authority": ["official_vendor_policy", "official_terms", "official_documentation"],
        "secondary_authority": ["reputable_secondary_reference"],
        "freshness_policy": "vendor_policy",
    },
    "doctrine": {
        "preferred_authority": ["versioned_private_synthesis", "primary_book_or_framework"],
        "secondary_authority": [],
        "freshness_policy": "doctrine",
    },
    "general_web": {
        "preferred_authority": ["primary_source", "high_quality_secondary_source"],
        "secondary_authority": ["other_reputable_source"],
        "freshness_policy": "general_web",
    },
}

INTERNAL_CONTEXT_RULES = [
    ("repository_code", ("repo", "github", "kod", "code", "branch", "commit", "pull request", "dependency"), ["GitHub"]),
    ("roadmap_execution", ("roadmap", "task", "issue", "sprint", "milestone", "backlog", "projekt"), ["Linear", "Notion"]),
    ("customer_commercial", ("customer", "klient", "crm", "deal", "pipeline", "renewal", "churn", "sprzeda"), ["HubSpot", "Gmail"]),
    ("capacity_schedule", ("capacity", "dostępno", "dostepno", "calendar", "termin", "meeting", "zespół", "zespol"), ["Google_Calendar", "Linear"]),
    ("docs_contracts", ("contract", "umow", "policy", "polityk", "dokument", "spec", "brief", "notat"), ["Google_Drive", "Notion"]),
    ("decision_history", ("wcześniejsz", "wczesniejsz", "previous decision", "decision memory", "rada", "council"), ["Notion"]),
]

DOMAIN_ORDER = [
    "strategy", "marketing", "sales", "offer_pricing",
    "product_customer", "growth", "operator",
]

DOMAIN_KEYWORDS = {
    "strategy": ["strateg", "rynek", "market", "konkur", "wejsc", "wejść", "moat", "kategoria", "alokac"],
    "marketing": ["marketing", "pozycjon", "brand", "reklam", "kampani", "category", "message"],
    "sales": ["sales", "sprzed", "pipeline", "prospect", "deal", "demo", "outbound"],
    "offer_pricing": ["pricing", "cena", "cen", "pakiet", "offer", "ofert", "monetyz"],
    "product_customer": ["produkt", "product", "customer", "klient", "jtbd", "problem", "user"],
    "growth": ["growth", "wzrost", "acquisition", "retention", "referral", "cac", "viral", "activation"],
    "operator": ["operac", "wdroż", "wdroz", "proces", "execution", "constraint", "zasob", "capacity"],
}

DECISION_KIND = {
    "strategy": "strategy",
    "marketing": "marketing",
    "sales": "sales",
    "offer_pricing": "pricing",
    "product_customer": "product_customer",
    "growth": "growth",
    "operator": "operations",
}

ARCHETYPE_RULES = [
    ("m_and_a", ("m&a", "acquisition", "przeję", "przejec", "przeją", "przejac", "merger", "kupic firme", "kupić firmę")),
    ("pricing", ("pricing", "cena", "podwyż", "podwyz", "pakiet", "plan cen", "monetyz")),
    ("market_entry", ("wejść na rynek", "wejsc na rynek", "market entry", "ekspansj", "international", "zagranic")),
    ("build_vs_buy", ("build vs buy", "budować czy kup", "budowac czy kup", "make or buy")),
    ("resource_allocation", ("alokac", "budżet między", "budzet miedzy", "resource allocation", "podzielić budżet", "podzielic budzet")),
    ("hiring", ("zatrud", "hire", "hiring", "rekrut")),
    ("partnership", ("partner", "reseller", "affiliate", "channel partner")),
    ("launch", ("launch", "wdrożyć produkcyj", "wdrozyc produkcyj", "release", "uruchomić", "uruchomic")),
    ("shutdown", ("zamknąć", "zamknac", "kill product", "wyłączyć", "wylaczyc", "sunset")),
    ("product_investment", ("feature", "funkcj", "produkt", "roadmap", "build")),
]

FRAMEWORKS = [
    dict(id="strategic_choice", domains=("strategy", "operator"), kinds=("strategy", "operations"),
         experts=("strategy", "operator"), triggers=("strategia", "strategy", "alokacja", "resource", "wybor", "wybór")),
    dict(id="competitive_advantage", domains=("strategy", "product_customer"), kinds=("strategy", "product_customer"),
         experts=("strategy", "product_customer"), triggers=("konkurencja", "competitor", "moat", "przewaga", "differentiat")),
    dict(id="positioning_category", domains=("marketing", "sales"), kinds=("marketing", "sales"),
         experts=("marketing", "sales"), triggers=("positioning", "pozycjon", "category", "kategoria", "brand")),
    dict(id="value_equation", domains=("offer_pricing", "sales", "marketing"), kinds=("pricing", "sales", "marketing"),
         experts=("offer_pricing", "sales", "marketing"), triggers=("pricing", "cena", "oferta", "offer", "pakiet", "guarantee")),
    dict(id="customer_job_evidence", domains=("product_customer", "growth"), kinds=("product_customer", "growth"),
         experts=("product_customer", "growth"), triggers=("jtbd", "customer", "klient", "problem", "research", "badanie")),
    dict(id="growth_loop", domains=("growth", "marketing", "product_customer"), kinds=("growth", "marketing", "product_customer"),
         experts=("growth", "marketing", "product_customer"), triggers=("growth", "acquisition", "retention", "referral", "wzrost")),
    dict(id="operating_constraint", domains=("operator", "strategy"), kinds=("operations", "strategy"),
         experts=("operator", "strategy"), triggers=("constraint", "ogranicz", "operac", "proces", "execution", "zasob")),
    dict(id="reversibility_experiment", domains=(), kinds=(), experts=tuple(DOMAIN_ORDER),
         triggers=("test", "experiment", "eksperyment", "pilot", "pilocie", "przetestuj", "validate", "walid")),
]

ROLE_REGISTRY: dict[str, dict[str, Any]] = {
    "strategy": {"class": "adviser", "name": "Strategy", "domains": ["strategy"]},
    "product_customer": {"class": "adviser", "name": "Product & Customer", "domains": ["product_customer"]},
    "operator": {"class": "adviser", "name": "Operator / Execution", "domains": ["operator"]},
    "marketing": {"class": "adviser", "name": "Marketing & Positioning", "domains": ["marketing"]},
    "sales": {"class": "adviser", "name": "Sales", "domains": ["sales"]},
    "offer_pricing": {"class": "adviser", "name": "Offer & Pricing", "domains": ["offer_pricing"]},
    "growth": {"class": "adviser", "name": "Growth", "domains": ["growth"]},
    "finance": {"class": "specialist", "name": "Finance & Capital Allocation"},
    "m_and_a": {"class": "specialist", "name": "M&A / CorpDev"},
    "localization": {"class": "specialist", "name": "International / Market Entry"},
    "technical": {"class": "specialist", "name": "Technical Architecture"},
    "data": {"class": "specialist", "name": "Data / Measurement / Causal Inference"},
    "people": {"class": "specialist", "name": "People & Organization"},
    "partnerships": {"class": "specialist", "name": "Partnerships & Ecosystem"},
    "change_management": {"class": "specialist", "name": "Change Management"},
    "legal": {"class": "gatekeeper", "name": "Legal & Regulatory Gate"},
    "security": {"class": "gatekeeper", "name": "Security Gate"},
    "privacy": {"class": "gatekeeper", "name": "Privacy & Data Protection Gate"},
    "financial_risk": {"class": "gatekeeper", "name": "Financial Risk Gate"},
    "responsible_ai": {"class": "gatekeeper", "name": "Responsible AI / Ethics Gate"},
    "reputation": {"class": "gatekeeper", "name": "Reputation & Stakeholder Risk"},
    "red_team": {"class": "auditor", "name": "Red Team"},
    "evidence_judge": {"class": "auditor", "name": "Evidence Judge"},
    "minority_sentinel": {"class": "auditor", "name": "Minority Sentinel"},
    "process_auditor": {"class": "auditor", "name": "Process Auditor"},
    "chairman": {"class": "authority", "name": "Chairman"},
}

SPECIALIST_RULES = [
    ("m_and_a", ("przeję", "przejec", "przeją", "przejac", "acquisition", "m&a", "merger", "due diligence")),
    ("finance", ("finans", "budget", "budżet", "budzet", "cash", "roi", "marż", "margin", "runway", "capex", "opex")),
    ("localization", ("niemc", "germany", "franc", "hiszp", "uk", "usa", "lokaliz", "international", "zagranic", "cross-border")),
    ("technical", ("technic", "integrac", "architecture", "architektur", "api", "system", "migrac", "infrastr", "repo", "auth", "token", "sekret", "secret")),
    ("data", ("data", "dane", "analytics", "metryk", "measurement", "attribution", "causal", "statyst")),
    ("people", ("hiring", "zatrud", "team", "zespół", "zespol", "organiz", "talent", "rekrut")),
    ("partnerships", ("partner", "channel", "reseller", "affiliate", "integrator", "ecosystem")),
    ("change_management", ("migration", "migrac", "rollout", "adoption", "change management", "training")),
]

LEGAL_DOMAIN_RULES = [
    ("commercial_contracts", ("contract", "umow", "sla", "liability", "terms", "vendor", "client terms")),
    ("privacy_data_protection", ("gdpr", "rodo", "privacy", "prywatno", "personal data", "dane osobowe", "dpa", "dpia", "cookie", "profil")),
    ("ai_regulation", ("ai act", "artificial intelligence", "sztuczna inteligenc", "automated decision", "model ai", "genai")),
    ("ip_copyright_licensing", ("copyright", "prawo autorsk", "licenc", "license", "trademark", "znak towar", "scrap", "training data")),
    ("consumer_advertising", ("consumer", "konsument", "reklam", "claim", "promotion", "promocj", "dark pattern", "guarantee")),
    ("employment", ("employee", "pracownik", "employment", "zatrud", "monitoring prac", "hr")),
    ("competition_antitrust", ("antitrust", "competition law", "konkurencj", "exclusiv", "wyłączno", "wylaczno")),
    ("corporate_m_and_a", ("m&a", "acquisition", "przeję", "przejec", "shares", "udział", "udzial", "merger")),
    ("international_cross_border", ("cross-border", "international", "zagranic", "transfer danych", "data transfer", "jurisdiction")),
    ("sector_regulatory", ("medical", "medycz", "health", "finance", "finans", "education", "edukac", "insurance", "ubezpiec")),
]

RISK_SURFACE_RULES = {
    "legal": ("legal", "prawo", "regul", "compliance", "contract", "umow", "licenc", "copyright", "m&a", "acquisition", "przeję", "przeją", "przejac"),
    "privacy": ("gdpr", "rodo", "privacy", "prywatno", "dane osobowe", "personal data", "employee monitoring", "monitoring prac"),
    "security": ("security", "bezpiecze", "auth", "secret", "sekret", "token", "credential", "threat", "vulnerab", "attack"),
    "financial": ("budget", "budżet", "budzet", "cash", "runway", "roi", "pricing", "cena", "m&a", "acquisition", "milion", "mln"),
    "responsible_ai": ("ai act", "automated decision", "high-risk ai", "sztuczna inteligenc", "artificial intelligence", "genai"),
    "reputation": ("brand", "pr", "public", "press", "media", "reputation", "reputac", "customer trust", "zaufan"),
    "technical": ("architecture", "architektur", "api", "migration", "migrac", "infra", "system", "repo", "technical"),
    "people": ("employee", "pracownik", "team", "zespół", "zespol", "hiring", "zatrud", "organi"),
}


def _norm(text: str) -> str:
    return str(text or "").casefold()


def _hits(text: str, keywords: list[str] | tuple[str, ...]) -> int:
    t = _norm(text)
    return sum(1 for kw in keywords if kw.casefold() in t)


def _clamp01(value: Any) -> float:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return 0.0
    if math.isnan(value) or math.isinf(value):
        return 0.0
    return max(0.0, min(1.0, value))


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(v for v in values if v))


def _setish(value: Any) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, str):
        return {value} if value else set()
    out = set()
    for item in value:
        if isinstance(item, dict):
            token = item.get("id") or item.get("key") or item.get("claim_id") or item.get("text") or item.get("value")
            if token:
                out.add(str(token))
        elif item:
            out.add(str(item))
    return out


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    union = a | b
    return len(a & b) / len(union) if union else 0.0


def infer_decision_archetype(query: str) -> str:
    text = _norm(query)
    for archetype, triggers in ARCHETYPE_RULES:
        if any(t in text for t in triggers):
            return archetype
    if re.search(r"\b(a|b|c)\s+(czy|vs|versus|albo)\b", text):
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
    mode = str(mode or "STANDARD").upper()
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
    gatekeepers = _dedupe(gatekeepers)[: budget["max_gatekeepers"]]

    auditors = ["red_team", "evidence_judge"]
    if budget.get("minority_sentinel"):
        auditors.append("minority_sentinel")
    if mode == "DEEP":
        auditors.append("process_auditor")

    return {
        "advisers": advisers,
        "specialists": specialists,
        "gatekeepers": gatekeepers,
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
    selected_mode = str(mode or choose_council_mode(contract)).upper()
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


def evidence_coverage_report(rows: list[dict[str, Any]], critical_areas: list[str]) -> dict[str, Any]:
    areas = _dedupe([str(x) for x in critical_areas if x]) or ["other"]
    per_area: dict[str, float] = {}
    per_area_unknown: dict[str, int] = {}
    all_groups: set[str] = set()
    for area in areas:
        best_by_group: dict[str, float] = {}
        unknown_count = 0
        for row in rows:
            if not row.get("accepted") or row.get("critical_area") != area:
                continue
            raw_group = str(row.get("independence_group") or "").strip()
            quality = _clamp01(row.get("source_quality", 0.5))
            directness = _clamp01(row.get("directness", 0.5))
            independence_confidence = _clamp01(row.get("independence_confidence", 1.0 if raw_group else 0.35))
            weight = quality * directness * (0.5 + 0.5 * independence_confidence)
            if raw_group:
                group = raw_group[:120]
            else:
                group = f"unknown_independence:{area}"
                unknown_count += 1
                weight *= 0.60
            best_by_group[group] = max(best_by_group.get(group, 0.0), weight)
            all_groups.add(group)
        remaining = 1.0
        for weight in best_by_group.values():
            remaining *= 1.0 - min(0.85, weight)
        score = 1.0 - remaining if best_by_group else 0.0
        if unknown_count and not any(not g.startswith("unknown_independence:") for g in best_by_group):
            score = min(score, 0.55)
        per_area[area] = round(score, 6)
        per_area_unknown[area] = unknown_count
    critical_gap = min(areas, key=lambda a: (per_area[a], areas.index(a)))
    overall = sum(per_area.values()) / len(per_area)
    return {
        "overall": round(overall, 6),
        "per_area": per_area,
        "critical_gap": critical_gap,
        "independent_source_count": len([g for g in all_groups if not g.startswith("unknown_independence:")]),
        "unknown_independence_sources": sum(per_area_unknown.values()),
        "unknown_independence_by_area": per_area_unknown,
    }


def find_double_crux(memos: list[dict[str, Any]]) -> dict[str, Any]:
    by_key: dict[str, list[dict[str, Any]]] = {}
    for memo in memos:
        for assumption in memo.get("assumptions") or []:
            key = str(assumption.get("key") or assumption.get("assumption_key") or "").strip()
            if not key:
                continue
            by_key.setdefault(key, []).append({
                "expert_id": str(memo.get("expert_id") or memo.get("role_id") or ""),
                "vote": memo.get("vote"),
                "value": str(assumption.get("value") or assumption.get("position") or "")[:200],
                "importance": _clamp01(assumption.get("importance", 0.5)),
                "uncertainty": _clamp01(assumption.get("uncertainty", 0.5)),
            })
    candidates = []
    for key, entries in by_key.items():
        values = {e["value"] for e in entries}
        votes = {e["vote"] for e in entries}
        if len(entries) < 2 or len(values) < 2 or len(votes) < 2:
            continue
        importance = sum(e["importance"] for e in entries) / len(entries)
        uncertainty = sum(e["uncertainty"] for e in entries) / len(entries)
        score = importance * (0.5 + 0.5 * uncertainty)
        candidates.append((score, importance, key, entries))
    if not candidates:
        return {"assumption_key": None, "experts": [], "positions": [], "importance": 0.0, "crux_score": 0.0}
    candidates.sort(key=lambda x: (-x[0], x[2]))
    score, importance, key, entries = candidates[0]
    return {
        "assumption_key": key,
        "experts": sorted({e["expert_id"] for e in entries if e["expert_id"]}),
        "positions": [{"expert_id": e["expert_id"], "value": e["value"], "vote": e["vote"]} for e in entries],
        "importance": round(importance, 6),
        "crux_score": round(score, 6),
    }


def consensus_share(votes: list[str]) -> float:
    usable = [str(v) for v in votes if v]
    if not usable:
        return 0.0
    counts = {v: usable.count(v) for v in set(usable)}
    return max(counts.values()) / len(usable)


def consensus_report(memos: list[dict[str, Any]], same_model_baseline: float = 0.25) -> dict[str, Any]:
    usable = [m for m in memos if m.get("vote")]
    n = len(usable)
    if not n:
        return {
            "raw_consensus": 0.0, "adjusted_consensus": 0.0, "majority_vote": None,
            "average_pairwise_correlation": 0.0, "effective_independent_perspectives": 0.0,
        }
    votes = [str(m["vote"]) for m in usable]
    counts = {v: votes.count(v) for v in set(votes)}
    majority = sorted(counts.items(), key=lambda x: (-x[1], x[0]))[0][0]
    raw = counts[majority] / n
    correlations = []
    baseline = _clamp01(same_model_baseline)
    for i in range(n):
        for j in range(i + 1, n):
            a, b = usable[i], usable[j]
            fw = _jaccard(_setish(a.get("frameworks") or a.get("framework_ids")), _setish(b.get("frameworks") or b.get("framework_ids")))
            src = _jaccard(_setish(a.get("independence_groups")), _setish(b.get("independence_groups")))
            claims = _jaccard(_setish(a.get("claim_ids") or a.get("unique_claim_ids")), _setish(b.get("claim_ids") or b.get("unique_claim_ids")))
            overlap = 0.30 * fw + 0.45 * src + 0.25 * claims
            correlations.append(max(baseline, overlap))
    avg_corr = sum(correlations) / len(correlations) if correlations else baseline
    effective_n = n / (1.0 + max(0, n - 1) * avg_corr)
    independence_ratio = min(1.0, effective_n / n)
    adjusted = 0.5 + (raw - 0.5) * independence_ratio
    return {
        "raw_consensus": round(raw, 6),
        "adjusted_consensus": round(_clamp01(adjusted), 6),
        "majority_vote": majority,
        "average_pairwise_correlation": round(avg_corr, 6),
        "effective_independent_perspectives": round(effective_n, 6),
        "perspective_count": n,
    }


def minority_sentinel(memos: list[dict[str, Any]]) -> dict[str, Any]:
    report = consensus_report(memos)
    majority = report.get("majority_vote")
    protected = []
    for memo in memos:
        if not memo.get("vote") or memo.get("vote") == majority:
            continue
        peers = [m for m in memos if m is not memo]
        peer_sources = set().union(*[_setish(m.get("independence_groups")) for m in peers]) if peers else set()
        own_sources = _setish(memo.get("independence_groups"))
        unique_sources = own_sources - peer_sources
        peer_assumptions = set()
        for peer in peers:
            peer_assumptions |= {str(a.get("key") or a.get("assumption_key")) for a in (peer.get("assumptions") or []) if a.get("key") or a.get("assumption_key")}
        own_assumptions = [a for a in (memo.get("assumptions") or []) if a.get("key") or a.get("assumption_key")]
        unique_high_risk = 0
        for assumption in own_assumptions:
            key = str(assumption.get("key") or assumption.get("assumption_key"))
            risk = _clamp01(assumption.get("importance", 0.5)) * _clamp01(assumption.get("uncertainty", 0.5))
            if key not in peer_assumptions and risk >= 0.35:
                unique_high_risk += 1
        role_id = str(memo.get("expert_id") or memo.get("role_id") or "")
        role_class = memo.get("role_class") or ROLE_REGISTRY.get(role_id, {}).get("class")
        gate_bonus = 0.35 if role_class == "gatekeeper" else 0.0
        score = min(1.0, 0.25 * min(2, len(unique_sources)) + 0.25 * min(2, unique_high_risk) + gate_bonus + 0.15 * _clamp01(memo.get("decision_impact", 0.5)))
        if score >= 0.35:
            protected.append({
                "expert_id": role_id,
                "vote": memo.get("vote"),
                "protection_score": round(score, 6),
                "unique_evidence_groups": sorted(unique_sources)[:5],
                "unique_high_risk_assumptions": unique_high_risk,
                "role_class": role_class or "unknown",
            })
    protected.sort(key=lambda x: (-x["protection_score"], x["expert_id"]))
    return {"majority_vote": majority, "protected_minority": protected, "must_surface": bool(protected)}


def detect_consensus_failure(votes: list[str], decision_quality: str | None,
                             outcome: str | None, outcome_attribution: list[str] | None = None) -> bool:
    if consensus_share(votes) <= 0.80:
        return False
    attrs = set(outcome_attribution or [])
    thesis_failure = decision_quality == "Bad" or "thesis_wrong" in attrs
    return bool(thesis_failure and outcome in {"Failure", "Mixed"})


def assumption_risk(importance: float, uncertainty: float) -> float:
    return round(_clamp01(importance) * _clamp01(uncertainty), 6)


def decompose_confidence(dimensions: dict[str, Any], binding_dimensions: list[str] | None = None) -> dict[str, Any]:
    clean = {str(k): _clamp01(v) for k, v in dimensions.items()}
    if not clean:
        return {"dimensions": {}, "overall": 0.0, "binding_dimensions": [], "weakest_dimension": None}
    default_weights = {
        "thesis": 0.28, "evidence": 0.22, "execution": 0.18, "financial": 0.10,
        "legal": 0.08, "security": 0.06, "privacy": 0.04, "timing": 0.04,
    }
    weights = {k: default_weights.get(k, 0.05) for k in clean}
    total = sum(weights.values()) or 1.0
    weighted = sum(clean[k] * weights[k] for k in clean) / total
    binding = [b for b in (binding_dimensions or []) if b in clean]
    if binding:
        binding_floor = min(clean[b] for b in binding)
        weighted = min(weighted, binding_floor + 0.10)
    weakest = min(clean, key=lambda k: (clean[k], k))
    return {
        "dimensions": {k: round(v, 6) for k, v in clean.items()},
        "overall": round(_clamp01(weighted), 6),
        "binding_dimensions": binding,
        "weakest_dimension": weakest,
    }


def value_of_information(probability_decision_changes: float, value_difference: float,
                         information_cost: float, delay_cost: float = 0.0) -> dict[str, Any]:
    p = _clamp01(probability_decision_changes)
    value = max(0.0, float(value_difference or 0.0))
    cost = max(0.0, float(information_cost or 0.0))
    delay = max(0.0, float(delay_cost or 0.0))
    gross = p * value
    net = gross - cost - delay
    return {
        "probability_decision_changes": round(p, 6),
        "gross_value_of_information": round(gross, 6),
        "information_cost": round(cost, 6),
        "delay_cost": round(delay, 6),
        "net_value_of_information": round(net, 6),
        "recommendation": "GATHER_EVIDENCE" if net > 0 else "DECIDE_NOW",
    }


def deliberation_stop(expected_information_gain: float, deliberation_cost: float,
                      no_novelty_rounds: int = 0, unresolved_mandatory_gate: bool = False,
                      critical_gap_open: bool = False) -> dict[str, Any]:
    gain = max(0.0, float(expected_information_gain or 0.0))
    cost = max(0.0, float(deliberation_cost or 0.0))
    if unresolved_mandatory_gate:
        stop = False
        reason = "mandatory_gate_unresolved"
    elif critical_gap_open and gain > 0:
        stop = gain <= cost and int(no_novelty_rounds) >= 2
        reason = "critical_gap_but_low_marginal_value" if stop else "critical_gap_still_worth_investigating"
    elif int(no_novelty_rounds) >= 2:
        stop = True
        reason = "information_saturation"
    else:
        stop = gain <= cost
        reason = "marginal_gain_below_cost" if stop else "continue_positive_information_value"
    return {
        "stop": bool(stop),
        "reason": reason,
        "expected_information_gain": round(gain, 6),
        "deliberation_cost": round(cost, 6),
        "no_novelty_rounds": int(no_novelty_rounds),
    }


def gate_verdict(proposed_verdict: str, confidence: float, required_confidence_value: float,
                 reversible_experiment_available: bool, critical_gap: str | None = None,
                 gate_statuses: dict[str, str] | None = None, controls_implemented: bool = False,
                 freshness_status: str = "CLEAR", human_approval_required: bool = False,
                 human_approved: bool = False) -> str:
    verdict = str(proposed_verdict or "DEFER").upper()
    if verdict not in VERDICTS:
        verdict = "DEFER"
    if str(freshness_status or "CLEAR").upper() != "CLEAR":
        return "DEFER"
    if human_approval_required and not human_approved:
        return "DEFER"
    statuses = {str(k): str(v).upper() for k, v in (gate_statuses or {}).items()}
    if any(status == "BLOCK" for status in statuses.values()):
        return "NO-GO"
    if any(status == "COUNSEL_REQUIRED" for status in statuses.values()):
        return "DEFER"
    if any(status not in GATE_STATUSES for status in statuses.values()):
        return "DEFER"
    if any(status == "CLEAR_WITH_CONTROLS" for status in statuses.values()) and not controls_implemented and verdict == "GO":
        return "TEST" if reversible_experiment_available else "DEFER"
    conf = _clamp01(confidence)
    required = _clamp01(required_confidence_value)
    if verdict in {"GO", "NO-GO"} and conf < required:
        return "TEST" if reversible_experiment_available else "DEFER"
    if critical_gap and verdict in {"GO", "NO-GO"} and conf < min(0.95, required + 0.03):
        return "TEST" if reversible_experiment_available else "DEFER"
    return verdict


def build_experiment_spec(hypothesis: str, metric: str, baseline: str, pass_threshold: str,
                          fail_threshold: str, duration: str, budget: str, sample: str,
                          guardrails: list[str] | None = None, minimum_detectable_effect: str = "",
                          kill_criteria: list[str] | None = None, evidence_gap_addressed: str = "",
                          assumption_key: str = "", owner: str = "", review_date: str = "") -> dict[str, Any]:
    return {
        "hypothesis": str(hypothesis)[:500],
        "primary_metric": str(metric)[:200],
        "metric": str(metric)[:200],
        "baseline": str(baseline)[:200],
        "target": str(pass_threshold)[:200],
        "pass_threshold": str(pass_threshold)[:200],
        "fail_threshold": str(fail_threshold)[:200],
        "minimum_detectable_effect": str(minimum_detectable_effect)[:200],
        "duration": str(duration)[:120],
        "budget": str(budget)[:120],
        "sample": str(sample)[:200],
        "guardrails": [str(x)[:200] for x in (guardrails or [])[:8]],
        "kill_criteria": [str(x)[:200] for x in (kill_criteria or [])[:8]],
        "decision_rule": {"GO": str(pass_threshold)[:200], "NO-GO": str(fail_threshold)[:200], "otherwise": "DEFER"},
        "evidence_gap_addressed": str(evidence_gap_addressed)[:300],
        "assumption_key": str(assumption_key)[:120],
        "owner": str(owner)[:120],
        "review_date": str(review_date)[:40],
    }


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    raw = str(value).strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        try:
            return datetime.strptime(raw[:10], "%Y-%m-%d")
        except ValueError:
            return None


def _recency_factor(updated_at: str | None, as_of: str | None) -> float:
    updated = _parse_date(updated_at)
    now = _parse_date(as_of) or datetime.utcnow()
    if not updated:
        return 0.0
    if updated.tzinfo is not None and now.tzinfo is None:
        now = now.replace(tzinfo=updated.tzinfo)
    if updated.tzinfo is None and now.tzinfo is not None:
        updated = updated.replace(tzinfo=now.tzinfo)
    age_days = max(0, (now - updated).days)
    return math.exp(-age_days / 730.0)


def rank_analogies(current: dict[str, Any], history: list[dict[str, Any]], limit: int = 3) -> list[dict[str, Any]]:
    scored = []
    current_fw = set(current.get("framework_ids") or [])
    current_experts = set(current.get("expert_ids") or [])
    current_regimes = set(current.get("regime_tags") or [])
    for row in history:
        if row.get("memory_status") != "Complete" or row.get("outcome") in (None, "Pending"):
            continue
        quality_factor = 0.65 if row.get("decision_quality") in {"Pending", "Unclear", None} else 1.0
        score = 0.0
        if row.get("domain") == current.get("primary_domain"):
            score += 5
        if row.get("decision_kind") == current.get("decision_kind"):
            score += 4
        if row.get("decision_type") == current.get("decision_type"):
            score += 4
        if row.get("risk") == current.get("risk_level"):
            score += 2
        if row.get("reversibility") == current.get("reversibility"):
            score += 2
        score += min(3, len(current_fw & set(row.get("framework_ids") or [])))
        score += min(2, len(current_experts & set(row.get("expert_ids") or [])))
        regime_overlap = len(current_regimes & set(row.get("regime_tags") or []))
        score += min(4, 2 * regime_overlap)
        recency = _recency_factor(row.get("updated_at"), current.get("as_of"))
        score = score * quality_factor + 2.0 * recency
        scored.append({
            "decision_key": row.get("decision_key", ""), "score": round(score, 6),
            "outcome": row.get("outcome"), "resolved_vote": row.get("resolved_vote"),
            "domain": row.get("domain"), "decision_kind": row.get("decision_kind"),
            "decision_type": row.get("decision_type"), "decision_quality": row.get("decision_quality"),
            "outcome_lesson": str(row.get("outcome_lesson") or "")[:500],
            "updated_at": row.get("updated_at") or "", "regime_overlap": regime_overlap,
            "recency_factor": round(recency, 6),
        })
    scored.sort(key=lambda x: (-x["score"], x["decision_key"]))
    return scored[:max(0, min(3, int(limit)))]


def _is_non_thesis_row(row: dict[str, Any]) -> bool:
    attrs = set(row.get("outcome_attribution") or [])
    if "thesis_wrong" in attrs or "thesis_correct" in attrs:
        return False
    return bool(attrs & {"execution_failure", "external_shock", "wrong_timing"})


def _sample_strength(n: int) -> str:
    return "none" if n < 5 else ("weak" if n < 15 else "normal")


def calibration_report(rows: list[dict[str, Any]], expert_id: str, domain: str | None = None,
                       decision_kind: str | None = None, regime_tags: list[str] | None = None) -> dict[str, Any]:
    candidates = [
        row for row in rows
        if row.get("memory_status") == "Complete"
        and row.get("outcome") not in (None, "Pending")
        and (row.get("expert") == expert_id or row.get("expert_id") == expert_id)
        and (domain is None or row.get("domain") == domain)
        and (decision_kind is None or row.get("decision_kind") == decision_kind)
        and row.get("resolved_vote")
    ]
    excluded_non_thesis = sum(1 for row in candidates if _is_non_thesis_row(row))
    usable = [row for row in candidates if not _is_non_thesis_row(row)]
    if regime_tags:
        wanted = set(regime_tags)
        regime_matches = [row for row in usable if wanted & set(row.get("regime_tags") or [])]
        if len(regime_matches) >= 5:
            usable = regime_matches
    n = len(usable)
    if n == 0:
        return {
            "expert_id": expert_id, "sample_size": 0, "sample_strength": "none", "hit_rate": 0.0,
            "mean_confidence": 0.0, "brier_like_error": 0.0, "flags": [], "excluded_non_thesis": excluded_non_thesis,
        }
    correct = [1.0 if row.get("blind_vote") == row.get("resolved_vote") else 0.0 for row in usable]
    confidence = [_clamp01(row.get("blind_confidence") or 0) for row in usable]
    hit = sum(correct) / n
    mean_conf = sum(confidence) / n
    brier = sum((c - y) ** 2 for c, y in zip(confidence, correct)) / n
    flags = []
    if mean_conf - hit >= 0.15:
        flags.append("overconfidence")
    if hit - mean_conf >= 0.15:
        flags.append("underconfidence")
    go_share = sum(1 for row in usable if row.get("blind_vote") == "GO") / n
    test_share = sum(1 for row in usable if row.get("blind_vote") == "TEST") / n
    if go_share >= 0.7:
        flags.append("go_bias")
    if test_share >= 0.7:
        flags.append("test_bias")
    return {
        "expert_id": expert_id, "sample_size": n, "sample_strength": _sample_strength(n),
        "hit_rate": round(hit, 6), "mean_confidence": round(mean_conf, 6),
        "brier_like_error": round(brier, 6), "flags": flags,
        "excluded_non_thesis": excluded_non_thesis,
    }


def information_gain_score(expert_vote: str, peer_votes: list[str], novel_claims: int = 0, shared_claims: int = 0,
                           independence: float | None = None, decision_impact: float = 0.5,
                           later_validation: float | None = None) -> float:
    peers = [str(v) for v in peer_votes if v]
    surprise = 1.0 - peers.count(str(expert_vote)) / len(peers) if peers else 0.5
    novel = max(0, int(novel_claims))
    shared = max(0, int(shared_claims))
    novelty = novel / (novel + shared) if (novel + shared) else 0.0
    independence_score = _clamp01(independence if independence is not None else surprise)
    validation = _clamp01(later_validation if later_validation is not None else 0.5)
    impact = _clamp01(decision_impact)
    return round(_clamp01(0.30 * novelty + 0.30 * independence_score + 0.25 * impact + 0.15 * validation), 6)


def framework_usefulness(exposed_assumption: bool, changed_vote: bool, identified_test: bool,
                         exposed_risk: bool, rejected: bool) -> dict[str, Any]:
    if rejected:
        score = 0.0
    else:
        score = 0.25 * sum(bool(x) for x in (exposed_assumption, changed_vote, identified_test, exposed_risk))
    return {"utility_score": round(score, 6), "rejected": bool(rejected)}


def framework_usefulness_report(rows: list[dict[str, Any]], framework_id: str) -> dict[str, Any]:
    usable = [row for row in rows if row.get("memory_status") == "Complete" and row.get("framework") == framework_id]
    n = len(usable)
    mean_utility = sum(_clamp01(row.get("utility_score", 0)) for row in usable) / n if n else 0.0
    return {"framework_id": framework_id, "sample_size": n, "sample_strength": _sample_strength(n), "mean_utility": round(mean_utility, 6)}


def information_gain_report(rows: list[dict[str, Any]], expert_id: str) -> dict[str, Any]:
    usable = [row for row in rows if row.get("memory_status") == "Complete" and (row.get("expert") == expert_id or row.get("expert_id") == expert_id)]
    n = len(usable)
    mean_gain = sum(_clamp01(row.get("information_gain", 0)) for row in usable) / n if n else 0.0
    if n < 5:
        signal = "insufficient"
    elif mean_gain < 0.20:
        signal = "redundant"
    elif mean_gain >= 0.55:
        signal = "high_value"
    else:
        signal = "useful"
    return {"expert_id": expert_id, "sample_size": n, "sample_strength": _sample_strength(n), "mean_information_gain": round(mean_gain, 6), "signal": signal}


def should_run_counterfactual(mode: str, confidence: float, required_confidence_value: float,
                              consensus_value: float) -> bool:
    if str(mode).upper() == "DEEP":
        return True
    if str(mode).upper() == "STANDARD" and (
        _clamp01(confidence) < _clamp01(required_confidence_value) or _clamp01(consensus_value) > 0.80
    ):
        return True
    return False


def infer_regime_tags(context: dict[str, Any]) -> list[str]:
    mappings = [
        ("company_stage", {"early": "early_stage", "early_stage": "early_stage", "growth": "growth_stage", "growth_stage": "growth_stage", "mature": "mature_stage", "mature_stage": "mature_stage"}),
        ("market_volatility", {"stable": "stable_market", "stable_market": "stable_market", "volatile": "volatile_market", "volatile_market": "volatile_market"}),
        ("geography", {"local": "local", "international": "international"}),
        ("business_model", {"b2b": "b2b", "b2c": "b2c"}),
        ("motion", {"self_serve": "self_serve", "sales_led": "sales_led"}),
    ]
    out = []
    for key, mapping in mappings:
        value = str(context.get(key) or "").strip().casefold()
        if value in mapping:
            out.append(mapping[value])
    return out


def source_provenance_summary(rows: list[dict[str, Any]]) -> dict[str, str]:
    classes = ["CURRENT_FACT", "PRIVATE_KNOWLEDGE", "DECISION_MEMORY", "FRAMEWORK", "LIVE_WEB", "EXPERT_JUDGMENT"]
    result = {}
    for source_class in classes:
        weights = [_clamp01(row.get("evidence_weight", 0)) for row in rows if row.get("accepted") and row.get("source_class") == source_class]
        strength = max(weights) if weights else 0.0
        if strength >= 0.8:
            label = "HIGH"
        elif strength >= 0.4:
            label = "MEDIUM"
        elif strength > 0:
            label = "LOW"
        else:
            label = "NONE"
        result[source_class] = label
    return result


def consensus_failure_patterns(rows: list[dict[str, Any]]) -> dict[str, Any]:
    failures = [row for row in rows if row.get("memory_status") == "Complete" and row.get("consensus_failure")]
    framework_counts: dict[str, int] = {}
    expert_counts: dict[str, int] = {}
    for row in failures:
        for framework in row.get("framework_ids") or []:
            framework_counts[str(framework)] = framework_counts.get(str(framework), 0) + 1
        for expert in row.get("expert_ids") or []:
            expert_counts[str(expert)] = expert_counts.get(str(expert), 0) + 1
    return {
        "failure_count": len(failures),
        "top_frameworks": sorted(framework_counts.items(), key=lambda x: (-x[1], x[0]))[:5],
        "top_experts": sorted(expert_counts.items(), key=lambda x: (-x[1], x[0]))[:10],
    }


def learning_weight(decision_quality: str | None, outcome_attribution: list[str] | None = None) -> float:
    attrs = set(outcome_attribution or [])
    if attrs & {"execution_failure", "external_shock", "wrong_timing"} and not attrs & {"thesis_wrong", "thesis_correct"}:
        return 0.0
    if decision_quality in {"Good", "Bad"}:
        return 1.0
    if decision_quality == "Unclear":
        return 0.25
    return 0.0


def due_reviews(rows: list[dict[str, Any]], today: str) -> list[dict[str, Any]]:
    now = _parse_date(today)
    if not now:
        return []
    due = []
    for row in rows:
        if row.get("memory_status") != "Complete" or row.get("outcome") != "Pending":
            continue
        dates = row.get("review_dates") or [row.get("review_date")]
        parsed = [_parse_date(d) for d in dates if d]
        if any(d and d.date() <= now.date() for d in parsed):
            due.append(row)
    due.sort(key=lambda row: (str(row.get("review_date") or ""), str(row.get("decision_key") or "")))
    return due


def council_health(decisions: list[dict[str, Any]], votes: list[dict[str, Any]], experiments: list[dict[str, Any]],
                   process_rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    complete = [d for d in decisions if d.get("memory_status") == "Complete"]
    resolved = [d for d in complete if d.get("outcome") not in (None, "Pending")]
    verdict_counts = {v: sum(1 for d in complete if d.get("verdict") == v) for v in ("GO", "NO-GO", "TEST", "DEFER")}
    process_rows = process_rows or []
    return {
        "council_version": COUNCIL_VERSION,
        "total_decisions": len(complete),
        "resolved_decisions": len(resolved),
        "good_decisions": sum(1 for d in resolved if d.get("decision_quality") == "Good"),
        "bad_decisions": sum(1 for d in resolved if d.get("decision_quality") == "Bad"),
        "failed_outcomes": sum(1 for d in resolved if d.get("outcome") == "Failure"),
        "consensus_failures": sum(1 for d in resolved if bool(d.get("consensus_failure"))),
        "verdict_counts": verdict_counts,
        "pending_experiments": sum(1 for e in experiments if e.get("memory_status") == "Complete" and e.get("outcome") == "Pending"),
        "resolved_votes": sum(1 for v in votes if v.get("memory_status") == "Complete" and v.get("outcome") not in (None, "Pending")),
        "process_events": len([r for r in process_rows if r.get("memory_status") == "Complete"]),
        "router_misses": sum(1 for r in process_rows if r.get("memory_status") == "Complete" and r.get("event_type") == "router_miss"),
        "minority_vindications": sum(1 for r in process_rows if r.get("memory_status") == "Complete" and r.get("event_type") == "minority_vindicated"),
    }


_MEMORY_ALLOWLIST_V4 = {
    "decision_key", "domain", "decision_kind", "decision_type", "risk", "risk_level", "reversibility",
    "verdict", "confidence", "outcome", "resolved_vote", "framework_ids", "expert_ids", "outcome_lesson", "updated_at",
    "decision_quality", "execution_quality", "outcome_attribution", "same_decision_again", "snapshot_hash", "snapshot_version",
    "regime_tags", "evidence_coverage", "required_confidence", "consensus_failure", "council_mode", "decision_value_score",
    "double_crux", "evidence_critical_gap", "missing_perspectives", "counterfactual_tested", "council_version", "kernel_version",
    "route_version", "gate_statuses", "adjusted_consensus", "effective_independent_perspectives", "review_dates",
}


def sanitize_memory_record(raw: dict[str, Any]) -> dict[str, Any]:
    clean = {k: raw[k] for k in _MEMORY_ALLOWLIST_V4 if k in raw}
    clean["outcome_lesson"] = str(clean.get("outcome_lesson") or "")[:500]
    clean["framework_ids"] = [str(x) for x in clean.get("framework_ids") or []][:6]
    clean["expert_ids"] = [str(x) for x in clean.get("expert_ids") or []][:20]
    clean["regime_tags"] = [str(x) for x in clean.get("regime_tags") or []][:12]
    clean["outcome_attribution"] = [str(x) for x in clean.get("outcome_attribution") or []][:6]
    clean["missing_perspectives"] = [str(x) for x in clean.get("missing_perspectives") or []][:20]
    clean["review_dates"] = [str(x) for x in clean.get("review_dates") or []][:8]
    clean["snapshot_hash"] = str(clean.get("snapshot_hash") or "")[:80]
    clean["double_crux"] = str(clean.get("double_crux") or "")[:300]
    clean["evidence_critical_gap"] = str(clean.get("evidence_critical_gap") or "")[:120]
    clean["gate_statuses"] = {str(k)[:80]: str(v)[:40] for k, v in dict(clean.get("gate_statuses") or {}).items()}
    for key in ("confidence", "evidence_coverage", "required_confidence", "decision_value_score", "adjusted_consensus", "effective_independent_perspectives"):
        if key in clean:
            clean[key] = _clamp01(clean[key]) if key != "effective_independent_perspectives" else max(0.0, float(clean[key] or 0))
    return clean


def make_decision_key(question: str, date_key: str, context: dict[str, Any] | None = None) -> str:
    stable_context = {
        "decision_type": (context or {}).get("decision_type"),
        "options": (context or {}).get("options"),
        "objective": (context or {}).get("objective"),
        "jurisdictions": (context or {}).get("jurisdictions"),
    }
    payload = json.dumps({
        "date": date_key.strip(), "question": _norm(question).strip(), "context": stable_context,
    }, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "dc-" + hashlib.sha256(payload).hexdigest()[:16]


def snapshot_hash(snapshot: dict[str, Any], version: int = 3) -> str:
    payload = {"snapshot_version": int(version), "snapshot": snapshot}
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return "snap-" + hashlib.sha256(canonical).hexdigest()


def champion_challenger(champion: dict[str, Any], challenger: dict[str, Any]) -> dict[str, Any]:
    benefit_keys = [
        "critical_assumptions_found", "material_risks_found", "evidence_gaps_found", "minority_preservation",
        "legal_constraints_found", "test_quality", "calibration_score",
    ]
    cost_keys = ["latency", "token_cost", "tool_calls"]

    def score(row: dict[str, Any]) -> float:
        benefit = sum(_clamp01(row.get(k, 0)) for k in benefit_keys) / len(benefit_keys)
        cost = sum(_clamp01(row.get(k, 0)) for k in cost_keys) / len(cost_keys)
        return 0.8 * benefit - 0.2 * cost

    c_score = score(champion)
    h_score = score(challenger)
    delta = h_score - c_score
    return {
        "champion_score": round(c_score, 6),
        "challenger_score": round(h_score, 6),
        "delta": round(delta, 6),
        "winner": "challenger" if delta > 0.03 else ("champion" if delta < -0.03 else "tie"),
        "promotion_recommended": bool(delta > 0.03),
    }



def source_authority_for_claim(claim_type: str) -> dict[str, Any]:
    key = str(claim_type or "general_web").strip().lower()
    if key not in SOURCE_AUTHORITY_REGISTRY:
        key = "general_web"
    row = dict(SOURCE_AUTHORITY_REGISTRY[key])
    row["claim_type"] = key
    row["policy"] = dict(FRESHNESS_POLICIES[row["freshness_policy"]])
    return row


def _hours_between(older: datetime, newer: datetime) -> float:
    if older.tzinfo is not None and newer.tzinfo is None:
        newer = newer.replace(tzinfo=older.tzinfo)
    if older.tzinfo is None and newer.tzinfo is not None:
        older = older.replace(tzinfo=newer.tzinfo)
    return max(0.0, (newer - older).total_seconds() / 3600.0)


def evaluate_temporal_truth(row: dict[str, Any], as_of: str) -> dict[str, Any]:
    now = _parse_date(as_of)
    if now is None:
        raise ValueError("as_of must be ISO-8601")
    claim_type = str(row.get("claim_type") or row.get("freshness_policy") or "general_web").lower()
    if claim_type not in FRESHNESS_POLICIES:
        claim_type = "general_web"
    policy = FRESHNESS_POLICIES[claim_type]
    material = bool(row.get("material", True))
    published = _parse_date(row.get("published_at"))
    effective_from = _parse_date(row.get("effective_from"))
    effective_to = _parse_date(row.get("effective_to"))
    last_verified = _parse_date(row.get("last_verified_at") or row.get("verified_at") or row.get("observed_at"))
    superseded_by = row.get("superseded_by")
    draft = bool(row.get("draft", False))

    status = "CURRENT"
    reason = "within freshness policy"
    if draft:
        status, reason = "DRAFT", "source or rule is marked draft"
    elif superseded_by:
        status, reason = "SUPERSEDED", "a superseding source/version is known"
    elif effective_from is not None:
        left, right = effective_from, now
        if left.tzinfo is not None and right.tzinfo is None:
            right = right.replace(tzinfo=left.tzinfo)
        if left.tzinfo is None and right.tzinfo is not None:
            left = left.replace(tzinfo=right.tzinfo)
        if right < left:
            status, reason = "NOT_YET_EFFECTIVE", "effective_from is in the future"
    if status == "CURRENT" and effective_to is not None:
        left, right = effective_to, now
        if left.tzinfo is not None and right.tzinfo is None:
            right = right.replace(tzinfo=left.tzinfo)
        if left.tzinfo is None and right.tzinfo is not None:
            left = left.replace(tzinfo=right.tzinfo)
        if right > left:
            status, reason = "SUPERSEDED", "effective_to has passed"

    age_hours = None
    if status == "CURRENT":
        if policy.get("versioned_static"):
            if not row.get("source_version"):
                status, reason = "UNKNOWN", "versioned static source has no source_version"
        elif last_verified is None:
            status, reason = "UNKNOWN", "no last_verified_at/observed_at"
        else:
            age_hours = _hours_between(last_verified, now)
            if policy.get("requires_system_of_record") and material and not bool(row.get("system_of_record_verified", False)):
                status, reason = "STALE", "material internal metric is not verified against system of record"
            elif policy.get("requires_live_verification") and material and not bool(row.get("verified_for_decision", False)):
                status, reason = "STALE", "material claim requires live verification for this decision"
            else:
                max_age = policy.get("max_age_hours")
                if max_age is not None and age_hours > float(max_age):
                    status, reason = "STALE", f"age {age_hours:.2f}h exceeds {max_age}h policy"
                elif max_age is not None and age_hours > float(max_age) * float(policy.get("near_expiry_ratio", 0.75)):
                    status, reason = "NEAR_EXPIRY", f"age {age_hours:.2f}h is near freshness limit"

    if status not in TEMPORAL_STATUSES:
        status = "UNKNOWN"
    admissible = status in {"CURRENT", "NEAR_EXPIRY"}
    if material and status in {"DRAFT", "NOT_YET_EFFECTIVE", "STALE", "SUPERSEDED", "UNKNOWN"}:
        admissible = False
    return {
        "claim_id": row.get("claim_id") or row.get("evidence_id") or row.get("id"),
        "claim_type": claim_type,
        "status": status,
        "admissible": bool(admissible),
        "material": material,
        "reason": reason,
        "published_at": row.get("published_at"),
        "effective_from": row.get("effective_from"),
        "effective_to": row.get("effective_to"),
        "last_verified_at": row.get("last_verified_at") or row.get("verified_at") or row.get("observed_at"),
        "age_hours": round(age_hours, 3) if age_hours is not None else None,
        "max_age_hours": policy.get("max_age_hours"),
        "requires_live_verification": bool(policy.get("requires_live_verification", False)),
        "requires_system_of_record": bool(policy.get("requires_system_of_record", False)),
        "superseded_by": superseded_by,
    }


def freshness_gate(rows: list[dict[str, Any]], as_of: str) -> dict[str, Any]:
    evaluated = [evaluate_temporal_truth(row, as_of) for row in rows]
    blockers = [r for r in evaluated if r["material"] and not r["admissible"]]
    warnings = [r for r in evaluated if r["status"] == "NEAR_EXPIRY"]
    material_ages = [r["age_hours"] for r in evaluated if r["material"] and r["age_hours"] is not None]
    counts = {status: sum(1 for r in evaluated if r["status"] == status) for status in sorted(TEMPORAL_STATUSES)}
    return {
        "as_of": as_of,
        "status": "REFRESH_REQUIRED" if blockers else "CLEAR",
        "decision_ready": not blockers,
        "material_blocker_count": len(blockers),
        "near_expiry_count": len(warnings),
        "oldest_material_evidence_hours": round(max(material_ages), 3) if material_ages else None,
        "counts": counts,
        "blockers": blockers,
        "warnings": warnings,
        "evaluated": evaluated,
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


def evaluate_watch_dependency(dependency: dict[str, Any]) -> dict[str, Any]:
    op = str(dependency.get("operator") or "changed").lower()
    previous = dependency.get("previous")
    current = dependency.get("current")
    threshold = dependency.get("threshold")
    triggered = bool(dependency.get("triggered", False))
    if op == "changed":
        triggered = current != previous
    elif op in {"gt", "gte", "lt", "lte"}:
        try:
            c, t = float(current), float(threshold)
            triggered = {"gt": c > t, "gte": c >= t, "lt": c < t, "lte": c <= t}[op]
        except (TypeError, ValueError):
            triggered = False
    elif op == "pct_change_gt":
        try:
            p, c, t = float(previous), float(current), abs(float(threshold))
            triggered = p != 0 and abs((c - p) / p) > t
        except (TypeError, ValueError):
            triggered = False
    return {
        "dependency_id": dependency.get("dependency_id") or dependency.get("id"),
        "type": dependency.get("type") or "generic",
        "operator": op,
        "triggered": bool(triggered),
        "materiality": _clamp01(dependency.get("materiality", 0.5)),
        "assumption_keys": list(dependency.get("assumption_keys") or []),
        "previous": previous,
        "current": current,
        "threshold": threshold,
        "reason": dependency.get("reason") or "",
    }


def decision_validity_overlay(decision: dict[str, Any], dependencies: list[dict[str, Any]], as_of: str) -> dict[str, Any]:
    if decision.get("superseded_by"):
        return {"status": "SUPERSEDED", "as_of": as_of, "reason": "decision explicitly superseded", "triggered_dependencies": []}
    if int(decision.get("material_stale_evidence_count") or 0) > 0:
        return {"status": "STALE", "as_of": as_of, "reason": "material evidence is stale", "triggered_dependencies": []}
    evaluated = [evaluate_watch_dependency(dep) for dep in dependencies]
    triggered = [d for d in evaluated if d["triggered"]]
    high = [d for d in triggered if d["materiality"] >= 0.7]
    status = "REOPEN" if high else ("WATCH" if triggered else "VALID")
    reasons = []
    if high:
        reasons.append("high-materiality watch dependency changed")
    elif triggered:
        reasons.append("watch dependency changed")
    next_revalidation = _parse_date(decision.get("next_revalidation_at"))
    now = _parse_date(as_of)
    if next_revalidation and now:
        left, right = next_revalidation, now
        if left.tzinfo is not None and right.tzinfo is None:
            right = right.replace(tzinfo=left.tzinfo)
        if left.tzinfo is None and right.tzinfo is not None:
            left = left.replace(tzinfo=right.tzinfo)
        if right >= left and status == "VALID":
            status = "WATCH"
            reasons.append("scheduled revalidation is due")
    affected = sorted({key for d in triggered for key in d.get("assumption_keys", [])})
    return {
        "status": status if status in DECISION_VALIDITY_STATUSES else "WATCH",
        "as_of": as_of,
        "reason": "; ".join(reasons) or "no material change detected",
        "triggered_dependencies": triggered,
        "affected_assumptions": affected,
        "revalidation_required": status in {"WATCH", "REOPEN"},
    }


def contradiction_coverage(claims: list[dict[str, Any]]) -> dict[str, Any]:
    material = [c for c in claims if bool(c.get("material", True))]
    tested = [c for c in material if bool(c.get("contradiction_tested", False))]
    unresolved = []
    for c in tested:
        opposing = int(c.get("opposing_evidence_count") or 0)
        if bool(c.get("unresolved_contradiction", False)) or (opposing > 0 and not bool(c.get("contradiction_resolved", False))):
            unresolved.append(c)
    coverage = len(tested) / len(material) if material else 1.0
    critical_unresolved = [c for c in unresolved if _clamp01(c.get("importance", 0.5)) >= 0.8]
    return {
        "material_claims": len(material),
        "contradiction_tested": len(tested),
        "contradiction_coverage": round(coverage, 6),
        "unresolved_contradictions": len(unresolved),
        "critical_unresolved_claim_ids": [c.get("claim_id") or c.get("id") for c in critical_unresolved],
        "decision_ready": not critical_unresolved,
    }


def independence_grade(memo: dict[str, Any], peers: list[dict[str, Any]]) -> str:
    if bool(memo.get("human_external", False)) or str(memo.get("actor_type") or "").lower() == "human":
        return "I4"
    model = str(memo.get("model_family") or memo.get("model") or "unknown")
    provider = str(memo.get("provider") or "unknown")
    others = [p for p in peers if p is not memo and (p.get("expert_id") or p.get("id")) != (memo.get("expert_id") or memo.get("id"))]
    if others and any(str(p.get("provider") or "unknown") != provider or str(p.get("model_family") or p.get("model") or "unknown") != model for p in others):
        return "I3"
    groups = _setish(memo.get("independence_groups"))
    peer_groups = set().union(*[_setish(p.get("independence_groups")) for p in others]) if others else set()
    if groups and peer_groups and not (groups & peer_groups):
        return "I2"
    if str(memo.get("expert_id") or memo.get("role") or "") and others:
        return "I1"
    return "I0"


def independence_grade_report(memos: list[dict[str, Any]]) -> dict[str, Any]:
    grades = []
    for memo in memos:
        grades.append({"expert_id": memo.get("expert_id") or memo.get("id"), "grade": independence_grade(memo, memos)})
    counts = {grade: sum(1 for r in grades if r["grade"] == grade) for grade in ("I0", "I1", "I2", "I3", "I4")}
    numeric = {"I0": 0.0, "I1": 0.25, "I2": 0.5, "I3": 0.75, "I4": 1.0}
    mean = sum(numeric[r["grade"]] for r in grades) / len(grades) if grades else 0.0
    return {"grades": grades, "counts": counts, "mean_independence_grade": round(mean, 6)}


def forecast_score_report(forecasts: list[dict[str, Any]]) -> dict[str, Any]:
    resolved = []
    for row in forecasts:
        try:
            p = _clamp01(row.get("probability"))
            outcome = row.get("outcome")
            if isinstance(outcome, str):
                outcome = 1 if outcome.lower() in {"1", "true", "yes", "success", "occurred"} else 0 if outcome.lower() in {"0", "false", "no", "failure", "did_not_occur"} else None
            if outcome not in (0, 1, False, True):
                continue
            resolved.append((p, int(bool(outcome))))
        except Exception:
            continue
    if not resolved:
        return {"n": 0, "sample_strength": "none", "brier_score": None, "calibration_error": None}
    brier = sum((p - y) ** 2 for p, y in resolved) / len(resolved)
    bins: dict[int, list[tuple[float, int]]] = {}
    for p, y in resolved:
        bucket = min(4, int(p * 5))
        bins.setdefault(bucket, []).append((p, y))
    cal = 0.0
    for vals in bins.values():
        avg_p = sum(p for p, _ in vals) / len(vals)
        avg_y = sum(y for _, y in vals) / len(vals)
        cal += abs(avg_p - avg_y) * (len(vals) / len(resolved))
    return {
        "n": len(resolved),
        "sample_strength": _sample_strength(len(resolved)),
        "brier_score": round(brier, 6),
        "calibration_error": round(cal, 6),
        "mean_forecast": round(sum(p for p, _ in resolved) / len(resolved), 6),
        "base_rate": round(sum(y for _, y in resolved) / len(resolved), 6),
    }


def base_rate_report(rows: list[dict[str, Any]], decision_type: str, regime_tags: list[str] | None = None) -> dict[str, Any]:
    target_regimes = set(regime_tags or [])
    eligible = []
    for row in rows:
        if row.get("memory_status") != "Complete":
            continue
        if str(row.get("decision_type") or row.get("decision_kind") or "") != str(decision_type):
            continue
        if target_regimes:
            row_regimes = _setish(row.get("regime_tags"))
            if not (target_regimes & row_regimes):
                continue
        outcome = str(row.get("outcome") or "")
        if outcome not in {"Success", "Failure"}:
            continue
        eligible.append(1 if outcome == "Success" else 0)
    n = len(eligible)
    return {
        "decision_type": decision_type,
        "n": n,
        "sample_strength": _sample_strength(n),
        "success_base_rate": round(sum(eligible) / n, 6) if n else None,
        "usable_as_prior": n >= 5,
        "warning": None if n >= 5 else "insufficient resolved analogues; do not overfit the outside view",
    }


def portfolio_report(decisions: list[dict[str, Any]], capacities: dict[str, Any] | None = None) -> dict[str, Any]:
    capacities = dict(capacities or {})
    totals: dict[str, float] = {}
    ids = {str(d.get("decision_id") or d.get("decision_key") or d.get("id")) for d in decisions}
    missing_dependencies = []
    ranked = []
    for d in decisions:
        did = str(d.get("decision_id") or d.get("decision_key") or d.get("id"))
        claims = d.get("resource_claims") or {}
        total_claim = 0.0
        for resource, amount in claims.items():
            try:
                value = max(0.0, float(amount))
            except (TypeError, ValueError):
                value = 0.0
            totals[resource] = totals.get(resource, 0.0) + value
            total_claim += value
        for dep in d.get("depends_on") or []:
            if str(dep) not in ids:
                missing_dependencies.append({"decision_id": did, "missing_dependency": str(dep)})
        ev = float(d.get("expected_value") or 0.0)
        ranked.append({"decision_id": did, "expected_value": ev, "resource_claim_total": total_claim, "value_density": round(ev / (1.0 + total_claim), 6)})
    conflicts = []
    for resource, used in totals.items():
        if resource in capacities:
            try:
                cap = float(capacities[resource])
            except (TypeError, ValueError):
                continue
            if used > cap:
                conflicts.append({"resource": resource, "used": round(used, 6), "capacity": round(cap, 6), "over_by": round(used - cap, 6)})
    ranked.sort(key=lambda r: (-r["value_density"], -r["expected_value"], r["decision_id"]))
    return {"resource_totals": totals, "capacity_conflicts": conflicts, "missing_dependencies": missing_dependencies, "value_density_ranking": ranked}


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

def main() -> None:
    parser = argparse.ArgumentParser(description="Deterministic AI Council v5 temporal decision intelligence kernel")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("profile")
    p.add_argument("--query", required=True)

    p = sub.add_parser("contract")
    p.add_argument("--query", required=True)
    p.add_argument("--context-json", default="{}")

    p = sub.add_parser("plan")
    p.add_argument("--contract-json", required=True)
    p.add_argument("--mode")

    p = sub.add_parser("route")
    p.add_argument("--contract-json", required=True)
    p.add_argument("--mode", default="STANDARD")

    p = sub.add_parser("legal")
    p.add_argument("--query", required=True)
    p.add_argument("--context-json", default="{}")

    p = sub.add_parser("select")
    p.add_argument("--query", required=True)
    p.add_argument("--profile-json", required=True)
    p.add_argument("--experts-json", required=True)
    p.add_argument("--max-frameworks", type=int, default=3)

    p = sub.add_parser("rank")
    p.add_argument("--current-json", required=True)
    p.add_argument("--history-json", required=True)

    p = sub.add_parser("calibrate")
    p.add_argument("--rows-json", required=True)
    p.add_argument("--expert", required=True)
    p.add_argument("--domain")
    p.add_argument("--decision-kind")
    p.add_argument("--regime-tags-json")

    p = sub.add_parser("sanitize")
    p.add_argument("--record-json", required=True)

    p = sub.add_parser("key")
    p.add_argument("--query", required=True)
    p.add_argument("--date", required=True)
    p.add_argument("--context-json", default="{}")

    p = sub.add_parser("mode")
    p.add_argument("--profile-json", required=True)
    p.add_argument("--financial-impact", type=float, default=0.5)
    p.add_argument("--uncertainty", type=float, default=0.5)
    p.add_argument("--strategic-impact", type=float)

    p = sub.add_parser("budget")
    p.add_argument("--mode", required=True)

    p = sub.add_parser("threshold")
    p.add_argument("--profile-json", required=True)
    p.add_argument("--evidence-coverage", type=float, required=True)
    p.add_argument("--decision-value", type=float, default=0.5)

    p = sub.add_parser("coverage")
    p.add_argument("--rows-json", required=True)
    p.add_argument("--areas-json", required=True)

    p = sub.add_parser("crux")
    p.add_argument("--memos-json", required=True)

    p = sub.add_parser("consensus")
    p.add_argument("--memos-json", required=True)
    p.add_argument("--same-model-baseline", type=float, default=0.25)

    p = sub.add_parser("minority")
    p.add_argument("--memos-json", required=True)

    p = sub.add_parser("confidence")
    p.add_argument("--dimensions-json", required=True)
    p.add_argument("--binding-json", default="[]")

    p = sub.add_parser("voi")
    p.add_argument("--probability-change", type=float, required=True)
    p.add_argument("--value-difference", type=float, required=True)
    p.add_argument("--information-cost", type=float, required=True)
    p.add_argument("--delay-cost", type=float, default=0.0)

    p = sub.add_parser("stop")
    p.add_argument("--expected-information-gain", type=float, required=True)
    p.add_argument("--deliberation-cost", type=float, required=True)
    p.add_argument("--no-novelty-rounds", type=int, default=0)
    p.add_argument("--unresolved-mandatory-gate", action="store_true")
    p.add_argument("--critical-gap-open", action="store_true")

    p = sub.add_parser("specialists")
    p.add_argument("--query", required=True)
    p.add_argument("--experts-json", default="[]")
    p.add_argument("--max-specialists", type=int, default=5)

    p = sub.add_parser("missing")
    p.add_argument("--query", required=True)
    p.add_argument("--experts-json", default="[]")

    p = sub.add_parser("experiment")
    p.add_argument("--spec-json", required=True)

    p = sub.add_parser("snapshot")
    p.add_argument("--snapshot-json", required=True)
    p.add_argument("--version", type=int, default=3)

    p = sub.add_parser("gate")
    p.add_argument("--verdict", required=True)
    p.add_argument("--confidence", type=float, required=True)
    p.add_argument("--required-confidence", type=float, required=True)
    p.add_argument("--reversible-experiment", action="store_true")
    p.add_argument("--critical-gap")
    p.add_argument("--gate-statuses-json", default="{}")
    p.add_argument("--controls-implemented", action="store_true")
    p.add_argument("--freshness-status", default="CLEAR")
    p.add_argument("--human-approval-required", action="store_true")
    p.add_argument("--human-approved", action="store_true")

    p = sub.add_parser("regime")
    p.add_argument("--context-json", required=True)

    p = sub.add_parser("due-reviews")
    p.add_argument("--rows-json", required=True)
    p.add_argument("--today", required=True)

    p = sub.add_parser("info-gain")
    p.add_argument("--expert-vote", required=True)
    p.add_argument("--peer-votes-json", required=True)
    p.add_argument("--novel-claims", type=int, default=0)
    p.add_argument("--shared-claims", type=int, default=0)
    p.add_argument("--independence", type=float)
    p.add_argument("--decision-impact", type=float, default=0.5)
    p.add_argument("--later-validation", type=float)

    p = sub.add_parser("framework-utility")
    p.add_argument("--exposed-assumption", action="store_true")
    p.add_argument("--changed-vote", action="store_true")
    p.add_argument("--identified-test", action="store_true")
    p.add_argument("--exposed-risk", action="store_true")
    p.add_argument("--rejected", action="store_true")

    p = sub.add_parser("health")
    p.add_argument("--decisions-json", required=True)
    p.add_argument("--votes-json", required=True)
    p.add_argument("--experiments-json", required=True)
    p.add_argument("--process-json", default="[]")

    p = sub.add_parser("provenance")
    p.add_argument("--rows-json", required=True)

    p = sub.add_parser("consensus-patterns")
    p.add_argument("--rows-json", required=True)

    p = sub.add_parser("eval-compare")
    p.add_argument("--champion-json", required=True)
    p.add_argument("--challenger-json", required=True)

    p = sub.add_parser("source-authority")
    p.add_argument("--claim-type", required=True)

    p = sub.add_parser("temporal")
    p.add_argument("--row-json", required=True)
    p.add_argument("--as-of", required=True)

    p = sub.add_parser("freshness")
    p.add_argument("--rows-json", required=True)
    p.add_argument("--as-of", required=True)

    p = sub.add_parser("context-route")
    p.add_argument("--query", required=True)

    p = sub.add_parser("watch")
    p.add_argument("--dependency-json", required=True)

    p = sub.add_parser("validity")
    p.add_argument("--decision-json", required=True)
    p.add_argument("--dependencies-json", default="[]")
    p.add_argument("--as-of", required=True)

    p = sub.add_parser("contradiction")
    p.add_argument("--claims-json", required=True)

    p = sub.add_parser("independence-grade")
    p.add_argument("--memos-json", required=True)

    p = sub.add_parser("forecast-score")
    p.add_argument("--forecasts-json", required=True)

    p = sub.add_parser("base-rate")
    p.add_argument("--rows-json", required=True)
    p.add_argument("--decision-type", required=True)
    p.add_argument("--regime-tags-json", default="[]")

    p = sub.add_parser("portfolio")
    p.add_argument("--decisions-json", required=True)
    p.add_argument("--capacities-json", default="{}")

    p = sub.add_parser("handoff")
    p.add_argument("--kind", required=True)
    p.add_argument("--decision-json", required=True)
    p.add_argument("--issue-json", required=True)

    p = sub.add_parser("tool-authority")
    p.add_argument("--action-json", required=True)

    args = parser.parse_args()

    if args.command == "profile":
        result = profile_problem(args.query)
    elif args.command == "contract":
        result = compile_decision_contract(args.query, json.loads(args.context_json))
    elif args.command == "plan":
        result = plan_council(json.loads(args.contract_json), args.mode)
    elif args.command == "route":
        result = route_roles(json.loads(args.contract_json), args.mode.upper())
    elif args.command == "legal":
        result = route_legal_risk(args.query, json.loads(args.context_json))
    elif args.command == "select":
        result = select_frameworks(args.query, json.loads(args.profile_json), json.loads(args.experts_json), args.max_frameworks)
    elif args.command == "rank":
        result = rank_analogies(json.loads(args.current_json), json.loads(args.history_json))
    elif args.command == "calibrate":
        regimes = json.loads(args.regime_tags_json) if args.regime_tags_json else None
        result = calibration_report(json.loads(args.rows_json), args.expert, args.domain, args.decision_kind, regimes)
    elif args.command == "sanitize":
        result = sanitize_memory_record(json.loads(args.record_json))
    elif args.command == "key":
        result = {"decision_key": make_decision_key(args.query, args.date, json.loads(args.context_json))}
    elif args.command == "mode":
        profile = json.loads(args.profile_json)
        score = decision_value_score(profile, args.financial_impact, args.uncertainty, args.strategic_impact)
        result = {"mode": choose_council_mode(profile, args.financial_impact, args.uncertainty, args.strategic_impact), "decision_value_score": score}
    elif args.command == "budget":
        result = mode_budget(args.mode)
    elif args.command == "threshold":
        result = {"required_confidence": required_confidence(json.loads(args.profile_json), args.evidence_coverage, args.decision_value)}
    elif args.command == "coverage":
        result = evidence_coverage_report(json.loads(args.rows_json), json.loads(args.areas_json))
    elif args.command == "crux":
        result = find_double_crux(json.loads(args.memos_json))
    elif args.command == "consensus":
        result = consensus_report(json.loads(args.memos_json), args.same_model_baseline)
    elif args.command == "minority":
        result = minority_sentinel(json.loads(args.memos_json))
    elif args.command == "confidence":
        result = decompose_confidence(json.loads(args.dimensions_json), json.loads(args.binding_json))
    elif args.command == "voi":
        result = value_of_information(args.probability_change, args.value_difference, args.information_cost, args.delay_cost)
    elif args.command == "stop":
        result = deliberation_stop(args.expected_information_gain, args.deliberation_cost, args.no_novelty_rounds, args.unresolved_mandatory_gate, args.critical_gap_open)
    elif args.command == "specialists":
        result = dynamic_specialists(args.query, json.loads(args.experts_json), args.max_specialists)
    elif args.command == "missing":
        result = {"missing_perspectives": detect_missing_perspectives(args.query, json.loads(args.experts_json))}
    elif args.command == "experiment":
        spec = json.loads(args.spec_json)
        result = build_experiment_spec(
            spec.get("hypothesis", ""), spec.get("metric") or spec.get("primary_metric", ""), spec.get("baseline", ""),
            spec.get("pass_threshold") or spec.get("target", ""), spec.get("fail_threshold", ""), spec.get("duration", ""),
            spec.get("budget", ""), spec.get("sample", ""), spec.get("guardrails"), spec.get("minimum_detectable_effect", ""),
            spec.get("kill_criteria"), spec.get("evidence_gap_addressed", ""), spec.get("assumption_key", ""),
            spec.get("owner", ""), spec.get("review_date", ""),
        )
    elif args.command == "snapshot":
        result = {"snapshot_hash": snapshot_hash(json.loads(args.snapshot_json), args.version), "snapshot_version": args.version}
    elif args.command == "gate":
        result = {"verdict": gate_verdict(
            args.verdict, args.confidence, args.required_confidence, args.reversible_experiment,
            args.critical_gap, json.loads(args.gate_statuses_json), args.controls_implemented,
            args.freshness_status, args.human_approval_required, args.human_approved,
        )}
    elif args.command == "regime":
        result = {"regime_tags": infer_regime_tags(json.loads(args.context_json))}
    elif args.command == "due-reviews":
        result = due_reviews(json.loads(args.rows_json), args.today)
    elif args.command == "info-gain":
        result = {"information_gain": information_gain_score(
            args.expert_vote, json.loads(args.peer_votes_json), args.novel_claims, args.shared_claims,
            args.independence, args.decision_impact, args.later_validation,
        )}
    elif args.command == "framework-utility":
        result = framework_usefulness(args.exposed_assumption, args.changed_vote, args.identified_test, args.exposed_risk, args.rejected)
    elif args.command == "health":
        result = council_health(json.loads(args.decisions_json), json.loads(args.votes_json), json.loads(args.experiments_json), json.loads(args.process_json))
    elif args.command == "provenance":
        result = source_provenance_summary(json.loads(args.rows_json))
    elif args.command == "consensus-patterns":
        result = consensus_failure_patterns(json.loads(args.rows_json))
    elif args.command == "eval-compare":
        result = champion_challenger(json.loads(args.champion_json), json.loads(args.challenger_json))
    elif args.command == "source-authority":
        result = source_authority_for_claim(args.claim_type)
    elif args.command == "temporal":
        result = evaluate_temporal_truth(json.loads(args.row_json), args.as_of)
    elif args.command == "freshness":
        result = freshness_gate(json.loads(args.rows_json), args.as_of)
    elif args.command == "context-route":
        result = route_internal_context(args.query)
    elif args.command == "watch":
        result = evaluate_watch_dependency(json.loads(args.dependency_json))
    elif args.command == "validity":
        result = decision_validity_overlay(json.loads(args.decision_json), json.loads(args.dependencies_json), args.as_of)
    elif args.command == "contradiction":
        result = contradiction_coverage(json.loads(args.claims_json))
    elif args.command == "independence-grade":
        result = independence_grade_report(json.loads(args.memos_json))
    elif args.command == "forecast-score":
        result = forecast_score_report(json.loads(args.forecasts_json))
    elif args.command == "base-rate":
        result = base_rate_report(json.loads(args.rows_json), args.decision_type, json.loads(args.regime_tags_json))
    elif args.command == "portfolio":
        result = portfolio_report(json.loads(args.decisions_json), json.loads(args.capacities_json))
    elif args.command == "handoff":
        result = build_human_handoff_packet(args.kind, json.loads(args.decision_json), json.loads(args.issue_json))
    else:
        result = tool_authority_assessment(json.loads(args.action_json))

    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
