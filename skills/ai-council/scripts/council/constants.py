from __future__ import annotations

from typing import Any

COUNCIL_VERSION = "5.0"
KERNEL_VERSION = "5.0.1"

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

_MEMORY_ALLOWLIST_V4 = {
    "decision_key", "domain", "decision_kind", "decision_type", "risk", "risk_level", "reversibility",
    "verdict", "confidence", "outcome", "resolved_vote", "framework_ids", "expert_ids", "outcome_lesson", "updated_at",
    "decision_quality", "execution_quality", "outcome_attribution", "same_decision_again", "snapshot_hash", "snapshot_version",
    "regime_tags", "evidence_coverage", "required_confidence", "consensus_failure", "council_mode", "decision_value_score",
    "double_crux", "evidence_critical_gap", "missing_perspectives", "counterfactual_tested", "council_version", "kernel_version",
    "route_version", "gate_statuses", "adjusted_consensus", "effective_independent_perspectives", "review_dates",
}
