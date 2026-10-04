"""Validate a source-backed initial competitor profile and CI handoff."""

from __future__ import annotations

STATUSES = {"complete", "partial", "blocked"}
CLAIM_STATES = {"OBSERVED", "INFERRED", "HYPOTHESIS", "UNKNOWN"}
PROFILE_SECTIONS = {"company", "icp", "positioning", "product", "pricing", "proof", "discovery"}
SOURCE_PROFILE_STATUS = {"BOOTSTRAP", "PARTIAL", "READY"}


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
    profile = result.get("profile")
    if not isinstance(profile, dict):
        errors.append("profile: required object")
        return errors
    for field in ("subject", "as_of", "scope"):
        if not isinstance(profile.get(field), str) or not profile[field].strip():
            errors.append(f"profile.{field}: required non-empty string")
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
    claims = profile.get("claims")
    claim_ids: set[str] = set()
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
            elif any(source_id not in source_ids for source_id in evidence):
                errors.append(f"{prefix}.source_ids: unknown source")
    sections = profile.get("sections")
    if not isinstance(sections, dict) or set(sections) != PROFILE_SECTIONS:
        errors.append("profile.sections: must contain exactly company/icp/positioning/product/pricing/proof/discovery")
    for field in ("contradictions", "gaps"):
        if not isinstance(profile.get(field), list):
            errors.append(f"profile.{field}: required list")
    handoff = result.get("competitive_intelligence_handoff")
    if not isinstance(handoff, dict):
        errors.append("competitive_intelligence_handoff: required object")
    else:
        for field in ("baseline_id", "source_profile_status"):
            if not isinstance(handoff.get(field), str) or not handoff[field].strip():
                errors.append(f"handoff.{field}: required")
        if handoff.get("source_profile_status") not in SOURCE_PROFILE_STATUS:
            errors.append("handoff.source_profile_status: invalid")
    return errors
