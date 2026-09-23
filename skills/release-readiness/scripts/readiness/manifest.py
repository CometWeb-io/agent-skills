"""Manifest schema constants, validation helpers, and scope/threshold normalization."""

from __future__ import annotations

import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

MANIFEST_VERSION = 2
ENGINE_VERSION = "2.1.0"

DOMAINS = ("product", "qa", "security", "ops", "docs", "billing", "support")
PROFILES = ("saas_web", "api_service", "mobile_app", "desktop_app", "internal_tool", "oss_library", "generic")
MODES = ("fast", "standard", "deep")
STATUSES = ("pass", "pass_with_controls", "accepted_risk", "fail", "unknown", "na")
SEVERITIES = ("blocker", "critical", "major", "minor")
EVIDENCE_LEVELS = ("missing", "claimed", "supported", "verified")
FRESHNESS = ("current", "stale", "mismatched", "unknown")
TRI = ("yes", "no", "unknown")
AUDIENCES = ("external", "internal", "library_consumers", "unknown")
COMMERCIAL = ("paid", "free", "not_applicable", "unknown")

GOVERNANCE_SURFACES = ("legal", "privacy", "financial_risk", "responsible_ai", "reputation", "platform_policy")
GOVERNANCE_STATUSES = ("not_required", "clear", "clear_with_controls", "counsel_required", "block")

SCOPE_FLAG_KEYS = (
    "first_production_release",
    "auth_change",
    "billing_change",
    "schema_or_data_migration",
    "sensitive_data_change",
    "public_api_breaking_change",
    "major_infra_change",
    "mobile_store_release",
    "incident_recovery_release",
    "high_impact_ai_change",
    "legal_or_regulatory_change",
)

HIGH_RISK_FLAGS = {
    "first_production_release",
    "auth_change",
    "billing_change",
    "schema_or_data_migration",
    "sensitive_data_change",
    "high_impact_ai_change",
    "legal_or_regulatory_change",
}
ELEVATED_RISK_FLAGS = {
    "public_api_breaking_change",
    "major_infra_change",
    "mobile_store_release",
    "incident_recovery_release",
}

FLAG_GOVERNANCE_SURFACES = {
    "sensitive_data_change": {"privacy"},
    "mobile_store_release": {"platform_policy"},
    "high_impact_ai_change": {"responsible_ai"},
    "legal_or_regulatory_change": {"legal"},
}

DEFAULT_DOMAIN_WEIGHTS = {
    "product": 15.0,
    "qa": 20.0,
    "security": 20.0,
    "ops": 20.0,
    "docs": 10.0,
    "billing": 8.0,
    "support": 7.0,
}
DEFAULT_CHECK_WEIGHTS = {"blocker": 8.0, "critical": 5.0, "major": 3.0, "minor": 1.0}
STATUS_CREDIT = {"pass": 1.0, "pass_with_controls": 0.75, "accepted_risk": 0.50, "fail": 0.0, "unknown": 0.0}
EVIDENCE_RANK = {name: idx for idx, name in enumerate(EVIDENCE_LEVELS)}
MODE_RANK = {"fast": 1, "standard": 2, "deep": 3}
RISK_MODE_FLOOR = {"R1": "fast", "R2": "standard", "R3": "deep"}
RISK_THRESHOLD_FLOORS = {
    "R1": {"go_score": 88.0, "conditional_score": 78.0, "min_coverage": 90.0},
    "R2": {"go_score": 92.0, "conditional_score": 84.0, "min_coverage": 95.0},
    "R3": {"go_score": 95.0, "conditional_score": 90.0, "min_coverage": 98.0},
}


class ManifestError(ValueError):
    pass


IMMUTABLE_KEYS = ("commit_sha", "artifact_id", "image_digest", "build_number")
MAX_INPUT_BYTES = 4 * 1024 * 1024


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _identity_value(key: str, value: Any) -> str:
    if key == "build_number" and type(value) is int and value >= 0:
        return str(value)
    value = _text(value)
    if not value or len(value) > 512 or value.casefold() in {"none", "null", "unknown", "n/a"}:
        return ""
    if key == "commit_sha" and not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", value):
        return ""
    if key == "image_digest" and not re.fullmatch(r"(?:sha256:[0-9a-f]{64}|sha512:[0-9a-f]{128})", value):
        return ""
    return value


def _validate_json(value: Any, depth: int = 0, budget: List[int] | None = None) -> None:
    if budget is None:
        budget = [100000]
    budget[0] -= 1
    if depth > 64 or budget[0] < 0:
        raise ManifestError("manifest complexity exceeds limit")
    if value is None or type(value) in (str, bool):
        return
    if type(value) is int:
        if value.bit_length() > 8192:
            raise ManifestError("integer exceeds rendering budget")
        return
    if type(value) is float and math.isfinite(value):
        return
    if isinstance(value, dict):
        if any(not isinstance(k, str) for k in value):
            raise ManifestError("JSON keys must be strings")
        for item in value.values():
            _validate_json(item, depth + 1, budget)
        return
    if isinstance(value, list):
        for item in value:
            _validate_json(item, depth + 1, budget)
        return
    raise ManifestError("manifest contains a non-JSON or non-finite value")


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ManifestError("duplicate JSON key")
        result[key] = value
    return result


def _invalid_constant(value):
    raise ManifestError("non-finite JSON constant")


def _num(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ManifestError(f"{name} must be numeric")
    try:
        number = float(value)
    except OverflowError as exc:
        raise ManifestError(f"{name} exceeds numeric range") from exc
    if not math.isfinite(number):
        raise ManifestError(f"{name} must be finite")
    return number


def _pct(value: Any, name: str) -> float:
    number = _num(value, name)
    if number < 0 or number > 100:
        raise ManifestError(f"{name} must be between 0 and 100")
    return number


def _parse_dt(value: Any) -> datetime | None:
    value = _text(value)
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})", value):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except (ValueError, OverflowError):
        return None


def _release_identity_gaps(release: Dict[str, Any]) -> List[str]:
    gaps = [k for k in ("id", "environment", "as_of") if not _identity_value(k, release.get(k))]
    if _parse_dt(release.get("as_of")) is None:
        gaps.append("as_of_invalid")
    elif _parse_dt(release["as_of"]) > datetime.now(timezone.utc):
        gaps.append("as_of_in_future")
    if not any(_identity_value(k, release.get(k)) for k in IMMUTABLE_KEYS):
        gaps.append("artifact_identity")
    for k in IMMUTABLE_KEYS:
        if k in release and not _identity_value(k, release[k]):
            gaps.append(k + "_invalid")
    if "config_digest" in release and not _identity_value("config_digest", release["config_digest"]):
        gaps.append("config_digest_invalid")
    return sorted(set(gaps))


def _release_ids(release: Dict[str, Any]) -> set[str]:
    keys = (*IMMUTABLE_KEYS, "id", "tag", "deployment_id")
    return {v for k in keys if (v := _identity_value(k, release.get(k)))}


def _evidence_obj(raw: Any) -> Dict[str, Any]:
    if isinstance(raw, dict):
        return dict(raw)
    if isinstance(raw, str) and raw.strip():
        return {"summary": raw.strip()}
    return {}


def _normalize_scope(raw: Any, profile: str) -> Tuple[Dict[str, Any], List[str], str, set[str]]:
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise ManifestError("scope must be an object")
    audience = str(raw.get("audience", "unknown")).lower().strip()
    if audience not in AUDIENCES:
        raise ManifestError(f"scope.audience invalid: {audience!r}")
    commercial = str(raw.get("commercial", "unknown")).lower().strip()
    if commercial not in COMMERCIAL:
        raise ManifestError(f"scope.commercial invalid: {commercial!r}")

    raw_flags = raw.get("risk_flags", {})
    if not isinstance(raw_flags, dict):
        raise ManifestError("scope.risk_flags must be an object")
    if set(raw_flags) - set(SCOPE_FLAG_KEYS):
        raise ManifestError("unknown risk flag; check spelling")
    flags: Dict[str, str] = {}
    gaps: List[str] = []
    for key in SCOPE_FLAG_KEYS:
        value = str(raw_flags.get(key, "unknown")).lower().strip()
        if value not in TRI:
            raise ManifestError(f"scope.risk_flags.{key} invalid: {value!r}")
        flags[key] = value
        if value == "unknown":
            gaps.append(f"risk_flag:{key}")

    if audience == "unknown":
        gaps.append("audience")
    if commercial == "unknown":
        gaps.append("commercial")
    if raw.get("risk_assessment_complete") is not True:
        gaps.append("risk_assessment_complete")

    explicit_surfaces = raw.get("governance_surfaces", [])
    if not isinstance(explicit_surfaces, list):
        raise ManifestError("scope.governance_surfaces must be an array")
    surfaces: set[str] = set()
    for surface in explicit_surfaces:
        s = str(surface).lower().strip()
        if s not in GOVERNANCE_SURFACES:
            raise ManifestError(f"invalid governance surface: {s!r}")
        surfaces.add(s)
    for flag, derived in FLAG_GOVERNANCE_SURFACES.items():
        if flags.get(flag) == "yes":
            surfaces |= set(derived)

    yes_flags = {k for k, v in flags.items() if v == "yes"}
    if yes_flags & HIGH_RISK_FLAGS:
        risk_tier = "R3"
    elif yes_flags & ELEVATED_RISK_FLAGS:
        risk_tier = "R2"
    else:
        risk_tier = "R1"

    normalized = {
        "audience": audience,
        "commercial": commercial,
        "risk_flags": flags,
        "governance_surfaces": sorted(surfaces),
        "risk_assessment_complete": raw.get("risk_assessment_complete") is True,
        "notes": str(raw.get("notes", ""))[:1000],
    }
    return normalized, gaps, risk_tier, surfaces


def _domain_weights(raw: Any) -> Dict[str, float]:
    weights = dict(DEFAULT_DOMAIN_WEIGHTS)
    if raw is None:
        return weights
    if not isinstance(raw, dict):
        raise ManifestError("domain_weights must be an object")
    for domain, value in raw.items():
        if domain not in DOMAINS:
            raise ManifestError(f"invalid domain weight key: {domain}")
        number = _num(value, f"domain_weights.{domain}")
        if number < 0:
            raise ManifestError(f"domain_weights.{domain} must be >= 0")
        weights[domain] = number
    if not any(v > 0 for v in weights.values()):
        raise ManifestError("domain_weights must contain positive total weight")
    return weights


def _thresholds(raw: Any, risk_tier: str) -> Dict[str, float]:
    raw = {} if raw is None else raw
    if not isinstance(raw, dict):
        raise ManifestError("thresholds must be an object")
    floor = RISK_THRESHOLD_FLOORS[risk_tier]
    supplied_go = _pct(raw.get("go_score", floor["go_score"]), "thresholds.go_score")
    supplied_cond = _pct(raw.get("conditional_score", floor["conditional_score"]), "thresholds.conditional_score")
    supplied_cov = _pct(raw.get("min_coverage", floor["min_coverage"]), "thresholds.min_coverage")
    result = {
        "go_score": max(floor["go_score"], supplied_go),
        "conditional_score": max(floor["conditional_score"], supplied_cond),
        "min_coverage": max(floor["min_coverage"], supplied_cov),
    }
    if result["conditional_score"] > result["go_score"]:
        raise ManifestError("conditional_score cannot exceed go_score")
    return result


def _load(path: Path) -> Dict[str, Any]:
    try:
        with path.open("rb") as handle:
            blob = handle.read(MAX_INPUT_BYTES + 1)
        if len(blob) > MAX_INPUT_BYTES:
            raise ManifestError("input exceeds size limit")
        data = json.loads(blob, object_pairs_hook=_unique_pairs, parse_constant=_invalid_constant)
        _validate_json(data)
        if not isinstance(data, dict):
            raise ManifestError("input must be a JSON object")
        return data
    except (OSError, UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise ManifestError("cannot read valid input JSON") from exc
