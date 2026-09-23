"""Shared constants for the repo-to-roadmap kernel."""
from __future__ import annotations

SCHEMA_VERSION = "2.0"
KERNEL_VERSION = "2.0.1"
MAX_JSON_BYTES = 32 * 1024 * 1024

SOURCE_BASE = {
    "inventory": 0.94,
    "test": 0.95,
    "ci": 0.94,
    "runtime": 0.96,
    "analytics": 0.94,
    "incident": 0.92,
    "code": 0.90,
    "config": 0.88,
    "migration": 0.88,
    "deployment": 0.94,
    "release": 0.94,
    "external_primary": 0.95,
    "vendor_official": 0.94,
    "approved_decision": 0.94,
    "user_requirement": 0.92,
    "product_context": 0.86,
    "customer_research": 0.86,
    "support": 0.80,
    "experiment": 0.88,
    "pr": 0.74,
    "commit": 0.70,
    "issue": 0.66,
    "documentation": 0.60,
    "external_secondary": 0.60,
    "inference": 0.22,
}

LANE_MULTIPLIERS = {
    "implementation": {
        "inventory": 1.00,
        "test": 1.00,
        "ci": 0.98,
        "runtime": 1.00,
        "code": 1.00,
        "config": 1.00,
        "migration": 1.00,
        "deployment": 0.95,
        "release": 0.90,
        "pr": 0.82,
        "commit": 0.80,
        "issue": 0.62,
        "documentation": 0.62,
        "user_requirement": 0.38,
        "product_context": 0.40,
        "analytics": 0.55,
        "incident": 0.65,
        "inference": 0.45,
    },
    "intent": {
        "user_requirement": 1.00,
        "approved_decision": 1.00,
        "product_context": 1.00,
        "documentation": 0.90,
        "issue": 0.76,
        "pr": 0.62,
        "code": 0.40,
        "analytics": 0.40,
        "inference": 0.45,
    },
    "outcome": {
        "analytics": 1.00,
        "runtime": 0.92,
        "customer_research": 1.00,
        "support": 0.92,
        "incident": 0.95,
        "experiment": 1.00,
        "issue": 0.62,
        "code": 0.30,
        "test": 0.38,
        "documentation": 0.48,
        "inference": 0.42,
    },
    "operational": {
        "ci": 1.00,
        "runtime": 1.00,
        "incident": 1.00,
        "deployment": 1.00,
        "release": 0.95,
        "config": 0.92,
        "test": 0.78,
        "code": 0.78,
        "issue": 0.64,
        "documentation": 0.58,
        "inference": 0.40,
    },
    "external": {
        "external_primary": 1.00,
        "vendor_official": 1.00,
        "external_secondary": 0.78,
        "documentation": 0.55,
        "inference": 0.35,
    },
}

DIRECTNESS = {"direct": 1.00, "supporting": 0.76, "inferred": 0.42}
FRESHNESS = {
    "CURRENT": 1.00,
    "NEAR_EXPIRY": 0.90,
    "NOT_TIME_SENSITIVE": 1.00,
    "STALE": 0.30,
    "SUPERSEDED": 0.00,
    "UNKNOWN": 0.45,
}
CURRENT_ADMISSIBLE = {"CURRENT", "NEAR_EXPIRY"}
SCOPE_MATCH = {"exact": 1.00, "partial": 0.72, "weak": 0.42}
DIRECTIONS = {"support", "contradict"}
CLAIM_LANES = set(LANE_MULTIPLIERS)
CLAIM_TYPES = {
    "presence",
    "behavior",
    "release",
    "outcome",
    "intent",
    "operational",
    "external_current",
    "absence",
}
MATERIALITIES = {"low", "medium", "high", "critical"}

VERIFICATION_SOURCES = {
    "presence": {"inventory", "code", "config", "migration", "test", "ci", "runtime"},
    "behavior": {"test", "ci", "runtime", "experiment"},
    "release": {"deployment", "release", "runtime", "ci"},
    "outcome": {"analytics", "runtime", "customer_research", "support", "incident", "experiment"},
    "intent": {"user_requirement", "approved_decision", "product_context", "documentation"},
    "operational": {"ci", "runtime", "incident", "deployment", "release"},
    "external_current": {"external_primary", "vendor_official"},
    "absence": {"inventory", "code", "config"},
}

COVERAGE_FACTORS = {
    "COMPLETE": 1.00,
    "PARTIAL": 0.72,
    "SAMPLED": 0.42,
    "UNAVAILABLE": 0.00,
    "NOT_APPLICABLE": None,
}

EFFORT_FACTORS = {"XS": 1.00, "S": 1.35, "M": 1.90, "L": 2.70, "XL": 3.80}
EFFORT_ORDER = ["XS", "S", "M", "L", "XL"]
VALID_LANES = {"BLOCKER", "VERIFY_NOW", "NOW", "NEXT", "LATER", "PARK", "VALIDATE"}
LANE_ORDER = {"BLOCKER": 0, "VERIFY_NOW": 1, "NOW": 2, "VALIDATE": 3, "NEXT": 4, "LATER": 5, "PARK": 6}
ITEM_KINDS = {"BUILD", "FIX", "HARDEN", "VERIFY", "VALIDATE", "INSTRUMENT", "MIGRATE", "RETIRE", "DOCUMENT", "DECIDE"}
GATE_TYPES = {"release", "security", "privacy", "data_integrity", "legal", "core_flow"}
GATE_STATUSES = {"NOT_REQUIRED", "UNVERIFIED", "CLEAR", "CLEAR_WITH_CONTROLS", "BLOCK"}
CAPABILITY_STATES = {
    "VERIFIED_WORKING",
    "IMPLEMENTED_UNVERIFIED",
    "PARTIAL",
    "STUBBED",
    "BROKEN",
    "MISSING",
    "UNKNOWN",
    "NOT_APPLICABLE",
}
TARGET_PROFILES = {"PROTOTYPE", "INTERNAL_BETA", "PUBLIC_BETA", "CLIENT_READY", "PAID_PRODUCTION", "SCALE_READY", "CUSTOM"}
TARGET_APPLICABILITY = {"APPLIES", "NOT_APPLICABLE", "UNKNOWN"}
