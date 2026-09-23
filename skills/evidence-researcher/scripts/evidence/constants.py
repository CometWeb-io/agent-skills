"""Shared constants for the Evidence Researcher kernel."""
from __future__ import annotations

VERSION = "2.0.1"
SCHEMA_VERSION = "2.0"
POLICY_VERSION = "evidence-policy-v2.1"

TRACKING_KEYS = {
    "fbclid", "gclid", "dclid", "msclkid", "mc_cid", "mc_eid", "ref", "ref_src",
}

CLAIM_TYPES = {
    "law_regulation", "regulatory_guidance", "security_advisory", "vendor_policy",
    "competitor_pricing", "official_technical_docs", "repository_behavior",
    "internal_metric", "internal_process_state", "company_announcement", "market_metric",
    "academic_evidence", "historical_fact", "current_fact", "product_behavior",
    "qualitative_experience", "doctrine_framework", "service_status", "dataset_fact",
}

LIVE_VERIFICATION_TYPES = {
    "law_regulation", "regulatory_guidance", "security_advisory", "vendor_policy",
    "competitor_pricing", "internal_metric", "internal_process_state", "service_status",
}

DEFAULT_TTL_DAYS = {
    "law_regulation": 0,
    "regulatory_guidance": 0,
    "security_advisory": 0,
    "vendor_policy": 7,
    "competitor_pricing": 3,
    "internal_metric": 1,
    "internal_process_state": 1,
    "service_status": 0,
    "official_technical_docs": 30,
    "repository_behavior": 30,
    "company_announcement": 30,
    "market_metric": 30,
    "current_fact": 7,
    "product_behavior": 30,
    "qualitative_experience": 90,
    "academic_evidence": 365,
    "dataset_fact": 365,
    "historical_fact": 3650,
    "doctrine_framework": 3650,
}

MATERIALITIES = {"critical", "material", "supporting"}
TEMPORAL_SENSITIVITIES = {"high", "medium", "low", "static"}
EPISTEMIC_KINDS = {"FACT", "INFERENCE"}
CLAIM_STATUSES = {
    "VERIFIED", "SUPPORTED_INFERENCE", "PARTIAL", "UNSUPPORTED", "CONTRADICTED", "UNKNOWN"
}
CONFIDENCE_LEVELS = {"high", "medium", "low"}
SOURCE_CLASSES = {
    "LIVE_WEB", "PRIVATE_KNOWLEDGE", "USER_FILE", "REPOSITORY", "DATABASE_SYSTEM_OF_RECORD",
    "ACADEMIC_SOURCE", "HUMAN_EXPERT_EVIDENCE", "DECISION_MEMORY", "FRAMEWORK",
}
SOURCE_ROLES = {"SYSTEM_OF_RECORD", "PRIMARY", "OFFICIAL", "SECONDARY", "AGGREGATOR", "EXPERT", "DOCTRINE"}
PROVENANCE_LANES = {"PUBLIC", "PRIVATE", "USER_SUPPLIED"}
ADMISSION_STATUSES = {"ACCEPTED", "CONTEXT_ONLY", "REJECTED"}
DIRECTIONS = {"SUPPORT", "CONTRADICT", "CONTEXT"}
FIT_LEVELS = {"high", "medium", "low", "unknown"}
MEASUREMENT_LEVELS = {"high", "medium", "low", "unknown", "not_applicable"}
TEMPORAL_STATUSES = {"CURRENT", "NEAR_EXPIRY", "STALE", "SUPERSEDED", "DRAFT", "NOT_YET_EFFECTIVE", "UNKNOWN"}
RESEARCH_STATUSES = {"READY", "PARTIAL", "REFRESH_REQUIRED", "BLOCKED_BY_CONTRADICTION"}
SEARCH_PURPOSES = {"SUPPORT", "FALSIFIER", "RETRACTION", "VERSION", "NEGATIVE_CASE", "ABSENCE_TEST", "LINEAGE"}
FALSIFIER_PURPOSES = {"FALSIFIER", "RETRACTION", "VERSION", "NEGATIVE_CASE", "ABSENCE_TEST"}
SEARCH_LANES = {"PUBLIC", "PRIVATE", "USER_SUPPLIED", "REPOSITORY", "DATABASE", "HUMAN"}
CONTRADICTION_RESOLUTIONS = {
    "RESOLVED_SCOPE", "RESOLVED_TIME", "RESOLVED_DEFINITION", "RESOLVED_METHOD",
    "RESOLVED_SUPERSEDED", "RESOLVED_AUTHORITY", "UNRESOLVED",
}
PRIMARY_ROLES = {"PRIMARY", "OFFICIAL", "SYSTEM_OF_RECORD"}
