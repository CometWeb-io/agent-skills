"""Validate a source-backed initial competitor profile and CI handoff."""

from __future__ import annotations

from datetime import date, datetime, timezone
import hashlib
import json

STATUSES = ("complete", "partial", "blocked",)
CLAIM_STATES = ("OBSERVED", "INFERRED", "HYPOTHESIS", "UNKNOWN",)
PROFILE_SECTIONS = {"company", "icp", "positioning", "product", "pricing", "proof", "discovery"}
SOURCE_PROFILE_STATUS = ("BOOTSTRAP", "PARTIAL", "READY",)


def timestamp(value: object) -> datetime | None:
    """Accept an ISO date (UTC midnight) or a timezone-aware ISO timestamp."""
    if not isinstance(value, str):
        return None
    try:
        if len(value) == 10:
            return datetime.combine(date.fromisoformat(value), datetime.min.time(), timezone.utc)
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc) if parsed.tzinfo else None
    except ValueError:
        return None


def profile_hash(profile: dict) -> str:
    return "sha256:" + hashlib.sha256(json.dumps(profile, ensure_ascii=False, sort_keys=True,
                                                separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


def validate(result: object) -> list[str]:
    if not isinstance(result, dict):
        return ["result: must be an object"]
    errors: list[str] = []
    summary = result.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        errors.append("summary: required non-empty string")
    if result.get("status") not in STATUSES:
        errors.append("status: must be complete, partial or blocked")
    not_verified = result.get("not_verified")
    if not isinstance(not_verified, list):
        errors.append("not_verified: required list")
    elif result.get("status") == "complete" and not_verified:
        errors.append("status: complete contradicts a non-empty not_verified")
    if isinstance(not_verified, list) and any(not isinstance(v, str) or not v.strip() for v in not_verified):
        errors.append("not_verified: entries must be non-empty strings")
    profile = result.get("profile")
    if not isinstance(profile, dict):
        errors.append("profile: required object")
        return errors
    for field in ("subject", "as_of", "scope"):
        if not isinstance(profile.get(field), str) or not profile[field].strip():
            errors.append(f"profile.{field}: required non-empty string")
    as_of = timestamp(profile.get("as_of"))
    if as_of is None:
        errors.append("profile.as_of: must be ISO date or timezone-aware timestamp")
    sources = profile.get("sources")
    source_ids: set[str] = set()
    if not isinstance(sources, list) or not sources:
        errors.append("profile.sources: required non-empty list")
    else:
        for index, source in enumerate(sources):
            prefix = f"profile.sources[{index}]"
            if not isinstance(source, dict):
                errors.append(f"{prefix}: must be object")
                continue
            source_id = source.get("id")
            if not isinstance(source_id, str) or not source_id.strip():
                errors.append(f"{prefix}.id: required")
            elif source_id in source_ids:
                errors.append(f"{prefix}.id: duplicate")
            else:
                source_ids.add(source_id)
            for field in ("kind", "locator", "observed_at"):
                if not isinstance(source.get(field), str) or not source[field].strip():
                    errors.append(f"{prefix}.{field}: required")
            observed = timestamp(source.get("observed_at"))
            if observed is None:
                errors.append(f"{prefix}.observed_at: must be ISO date or timezone-aware timestamp")
            elif as_of is not None and observed > as_of:
                errors.append(f"{prefix}.observed_at: after profile.as_of")
    claims = profile.get("claims")
    claim_ids: set[str] = set()
    claim_sources: dict[str, list] = {}
    if not isinstance(claims, list) or not claims:
        errors.append("profile.claims: required non-empty list")
    else:
        for index, claim in enumerate(claims):
            prefix = f"profile.claims[{index}]"
            if not isinstance(claim, dict):
                errors.append(f"{prefix}: must be object")
                continue
            claim_id = claim.get("id")
            if not isinstance(claim_id, str) or not claim_id.strip():
                errors.append(f"{prefix}.id: required")
            elif claim_id in claim_ids:
                errors.append(f"{prefix}.id: duplicate")
            else:
                claim_ids.add(claim_id)
            if not isinstance(claim.get("text"), str) or not claim["text"].strip():
                errors.append(f"{prefix}.text: required")
            if claim.get("state") not in CLAIM_STATES:
                errors.append(f"{prefix}.state: invalid")
            evidence = claim.get("source_ids")
            if not isinstance(evidence, list) or not evidence:
                errors.append(f"{prefix}.source_ids: required non-empty list")
            elif any(not isinstance(source_id, str) or source_id not in source_ids for source_id in evidence):
                errors.append(f"{prefix}.source_ids: unknown source")
            if isinstance(claim_id, str) and isinstance(evidence, list):
                claim_sources[claim_id] = evidence
            if result.get("status") == "complete" and claim.get("state") in ("UNKNOWN", "HYPOTHESIS"):
                errors.append(f"{prefix}.state: complete requires supported claims")
    sections = profile.get("sections")
    if not isinstance(sections, dict) or set(sections) != PROFILE_SECTIONS:
        errors.append("profile.sections: must contain exactly company/icp/positioning/product/pricing/proof/discovery")
    if isinstance(sections, dict):
        for section in sorted(PROFILE_SECTIONS & sections.keys()):
            row = sections[section]
            prefix = f"profile.sections.{section}"
            if not isinstance(row, dict):
                errors.append(f"{prefix}: required object with summary and claim_ids")
                continue
            if not isinstance(row.get("summary"), str) or not row["summary"].strip():
                errors.append(f"{prefix}.summary: required non-empty string")
            ids = row.get("claim_ids")
            if not isinstance(ids, list) or not ids or any(not isinstance(v, str) or v not in claim_ids for v in ids):
                errors.append(f"{prefix}.claim_ids: required non-empty references to profile claims")
            support = row.get("section_support")
            if result.get("status") == "complete" or support is not None:
                if not isinstance(support, list) or not support:
                    errors.append(f"{prefix}.section_support: required non-empty evidence mapping")
                else:
                    for item in support:
                        if (not isinstance(item, dict) or not isinstance(item.get("claim_id"), str)
                                or not isinstance(ids, list) or item["claim_id"] not in ids
                                or not isinstance(item.get("source_id"), str)
                                or item["source_id"] not in claim_sources.get(item["claim_id"], [])
                                or not isinstance(item.get("rationale"), str) or not item["rationale"].strip()):
                            errors.append(f"{prefix}.section_support: must bind a section claim to its source with rationale")
    for field in ("contradictions", "gaps"):
        if not isinstance(profile.get(field), list):
            errors.append(f"profile.{field}: required list")
        elif result.get("status") == "complete" and profile[field]:
            errors.append(f"profile.{field}: complete requires no unresolved items")
    handoff = result.get("competitive_intelligence_handoff")
    if not isinstance(handoff, dict):
        errors.append("competitive_intelligence_handoff: required object")
    else:
        for field in ("baseline_id", "source_profile_status"):
            if not isinstance(handoff.get(field), str) or not handoff[field].strip():
                errors.append(f"handoff.{field}: required")
        if handoff.get("source_profile_status") not in SOURCE_PROFILE_STATUS:
            errors.append("handoff.source_profile_status: invalid")
        if handoff.get("source_profile_status") == "READY":
            try:
                expected_hash = profile_hash(profile)
            except (ValueError, TypeError):
                expected_hash = None
            if expected_hash is None or handoff.get("profile_sha256") != expected_hash:
                errors.append("handoff.profile_sha256: READY requires the exact profile fingerprint")
        if handoff.get("source_profile_status") == "READY" and (result.get("status") != "complete" or errors):
            errors.append("handoff.source_profile_status: READY requires a valid complete profile")
    return errors


def assess(result: object) -> dict:
    errors = validate(result)
    return {"status": "INVALID" if errors else result["status"].upper(), "errors": errors,
            "coverage_status": "SUPPORT_MAPPED" if not errors and result["status"] == "complete" else "NOT_ASSESSED",
            "factual_verification": "not_assessed"}
