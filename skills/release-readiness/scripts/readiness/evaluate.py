"""Weighted readiness evaluation and verdict assembly."""

from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Any, Dict, Iterable, List, Tuple

from .gates import (
    GATES,
    _normalize_check,
    _normalize_governance_gate,
    _required_gates,
)
from .manifest import (
    DOMAINS,
    ENGINE_VERSION,
    MANIFEST_VERSION,
    MODE_RANK,
    MODES,
    PROFILES,
    RISK_MODE_FLOOR,
    STATUS_CREDIT,
    ManifestError,
    _domain_weights,
    _normalize_scope,
    _parse_dt,
    _release_identity_gaps,
    _thresholds,
    _validate_json,
)


def _contract_check(check: Dict[str, Any]) -> Dict[str, Any]:
    return {k: check.get(k) for k in ("id", "gate", "domain", "title", "severity", "binding", "applicable", "required_evidence", "weight")}


def _contract_hash(profile, scope, checks, domain_weights, thresholds, mode) -> str:
    return _snapshot_hash({"profile": profile, "scope": scope, "mode": mode,
                           "checks": sorted((_contract_check(c) for c in checks), key=lambda c: c["id"]),
                           "domain_weights": domain_weights, "thresholds": thresholds})


def _summarize_domain(checks: Iterable[Dict[str, Any]]) -> Tuple[float, float, int]:
    applicable = [c for c in checks if c["effective_status"] != "na"]
    if not applicable:
        return 0.0, 0.0, 0
    scale = max(c["weight"] for c in applicable)
    weights = [c["weight"] / scale for c in applicable]
    total = math.fsum(weights)
    earned = math.fsum(w * STATUS_CREDIT[c["effective_status"]] for c, w in zip(applicable, weights, strict=True))
    known = math.fsum(w for c, w in zip(applicable, weights, strict=True) if c["effective_status"] != "unknown")
    return (100.0 * (earned / total), 100.0 * (known / total), len(applicable))


def _snapshot_hash(manifest: Dict[str, Any]) -> str:
    canonical = json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _revalidation_triggers(scope: Dict[str, Any]) -> List[str]:
    triggers = [
        "release candidate artifact, commit, tag, or build changes",
        "target environment or material production configuration changes",
        "a binding test, scan, deployment check, or runtime verification becomes invalid or expires",
        "a new blocker/critical/major finding appears in assessed scope",
        "a compensating control or accepted-risk approval expires",
        "a related incident occurs during rollout or immediately after release",
    ]
    if scope["commercial"] == "paid" or scope["risk_flags"].get("billing_change") == "yes":
        triggers.append("billing provider configuration, price/plan mapping, webhook behavior, or entitlement logic changes")
    if scope["risk_flags"].get("schema_or_data_migration") == "yes":
        triggers.append("migration plan, migration artifact, schema, backfill data set, or recovery procedure changes")
    if scope["risk_flags"].get("mobile_store_release") == "yes":
        triggers.append("store submission artifact, signing/provisioning state, or applicable platform policy changes")
    if scope.get("governance_surfaces"):
        triggers.append("material evidence underlying a governance gate changes or is superseded")
    return triggers


def _slim_check(c: Dict[str, Any]) -> Dict[str, Any]:
    evidence = c.get("evidence") or {}
    return {
        "id": c["id"],
        "gate": c.get("gate", ""),
        "domain": c["domain"],
        "title": c.get("title", ""),
        "severity": c["severity"],
        "status": c["status"],
        "effective_status": c["effective_status"],
        "evidence_level": c["evidence_level"],
        "freshness": c["freshness"],
        "evidence": evidence,
        "owner": c.get("owner", ""),
        "mitigation": c.get("mitigation", ""),
        "control_owner": c.get("control_owner", ""),
        "control_due": c.get("control_due", ""),
        "risk_acceptance": c.get("risk_acceptance"),
        "evidence_issues": c.get("evidence_issues", []),
    }


def evaluate(manifest: Dict[str, Any], *, expected_contract_hash: str | None = None) -> Dict[str, Any]:
    if not isinstance(manifest, dict):
        raise ManifestError("manifest must be a JSON object")
    _validate_json(manifest)
    if expected_contract_hash is not None and not re.fullmatch(r"[0-9a-f]{64}", expected_contract_hash):
        raise ManifestError("expected_contract_hash must be a SHA-256")
    if type(manifest.get("manifest_version")) is not int or manifest.get("manifest_version") != MANIFEST_VERSION:
        raise ManifestError(f"manifest_version must be {MANIFEST_VERSION}")

    profile = str(manifest.get("profile", "generic")).lower().strip()
    if profile not in PROFILES:
        raise ManifestError(f"invalid profile: {profile!r}")
    mode = str(manifest.get("mode", "standard")).lower().strip()
    if mode not in MODES:
        raise ManifestError(f"invalid mode: {mode!r}")

    release = manifest.get("release", {})
    if not isinstance(release, dict):
        raise ManifestError("release must be an object")
    identity_gaps = _release_identity_gaps(release)
    scope, scope_gaps, risk_tier, governance_surfaces = _normalize_scope(manifest.get("scope"), profile)
    mode_floor = RISK_MODE_FLOOR[risk_tier]
    mode_gap = MODE_RANK[mode] < MODE_RANK[mode_floor]

    raw_checks = manifest.get("checks")
    if not isinstance(raw_checks, list) or not raw_checks:
        raise ManifestError("checks must be a non-empty array")
    seen: set[str] = set()
    checks = [_normalize_check(raw, seen, release) for raw in raw_checks]

    required_gates = _required_gates(profile, scope)
    gate_members: Dict[str, List[Dict[str, Any]]] = {g: [] for g in GATES}
    for check in checks:
        if check.get("gate"):
            gate_members[check["gate"]].append(check)
    missing_required_gates: List[str] = []
    for gate in required_gates:
        members = [c for c in gate_members.get(gate, []) if c["effective_status"] != "na"]
        if not members or not any(c["binding"] for c in members):
            missing_required_gates.append(gate)

    as_of = _parse_dt(release.get("as_of"))
    raw_governance = manifest.get("governance_gates", [])
    if not isinstance(raw_governance, list):
        raise ManifestError("governance_gates must be an array")
    governance = [_normalize_governance_gate(row, as_of, release) for row in raw_governance]
    seen_surfaces: set[str] = set()
    for gate in governance:
        if gate["surface"] in seen_surfaces:
            raise ManifestError(f"duplicate governance gate: {gate['surface']}")
        seen_surfaces.add(gate["surface"])
    governance_by_surface = {g["surface"]: g for g in governance}
    missing_governance_gates = sorted(governance_surfaces - set(governance_by_surface))
    # Any explicitly recorded BLOCK/COUNSEL_REQUIRED/controlled gate is material by construction.
    # Required surfaces additionally reject NOT_REQUIRED as an invalid way to satisfy a routed gate.
    governance_blocks = [g for g in governance if g["effective_status"] == "block"]
    governance_unknowns = [
        g for g in governance
        if g["effective_status"] == "counsel_required"
        or (g["surface"] in governance_surfaces and g["effective_status"] == "not_required")
    ]
    governance_controls = [g for g in governance if g["effective_status"] == "clear_with_controls"]

    domain_weights = _domain_weights(manifest.get("domain_weights"))
    thresholds = _thresholds(manifest.get("thresholds"), risk_tier)
    by_domain: Dict[str, List[Dict[str, Any]]] = {domain: [] for domain in DOMAINS}
    for check in checks:
        by_domain[check["domain"]].append(check)

    contract_hash = _contract_hash(profile, scope, checks, domain_weights, thresholds, mode)
    contract_mismatch = expected_contract_hash is not None and expected_contract_hash != contract_hash
    domain_results: Dict[str, Dict[str, Any]] = {}
    unrounded_domains = {}
    active_domains: List[str] = []
    for domain in DOMAINS:
        score, coverage, count = _summarize_domain(by_domain[domain])
        if count:
            unrounded_domains[domain] = (score, coverage)
            active_domains.append(domain)
            domain_results[domain] = {"score": round(score, 1), "coverage": round(coverage, 1), "applicable_checks": count}
        else:
            domain_results[domain] = {"score": None, "coverage": None, "applicable_checks": 0}

    scale = max((domain_weights[d] for d in active_domains), default=0)
    if scale <= 0:
        raise ManifestError("applicable domains have zero total domain weight")
    weights = {d: domain_weights[d] / scale for d in active_domains}
    total = math.fsum(weights.values())
    overall_score = math.fsum(unrounded_domains[d][0] * weights[d] for d in active_domains) / total
    overall_coverage = math.fsum(unrounded_domains[d][1] * weights[d] for d in active_domains) / total

    binding_failures = [c for c in checks if c["binding"] and c["effective_status"] == "fail"]
    binding_unknowns = [c for c in checks if c["binding"] and c["effective_status"] == "unknown"]
    blocking_failures = [
        c for c in checks
        if c["effective_status"] == "fail" and (c["binding"] or c["severity"] in ("blocker", "critical", "major"))
    ]
    minor_failures = [c for c in checks if c["effective_status"] == "fail" and c["severity"] == "minor"]
    controlled = [c for c in checks if c["effective_status"] == "pass_with_controls"]
    accepted_risks = [c for c in checks if c["effective_status"] == "accepted_risk"]
    downgraded_unknowns = [
        c for c in checks if c["effective_status"] == "unknown" and c["status"] in ("pass", "pass_with_controls", "accepted_risk", "fail")
    ]

    material_unknowns = [c for c in checks if c["effective_status"] == "unknown" and c["severity"] in ("blocker", "critical", "major")]
    score = round(overall_score, 1)
    coverage = round(overall_coverage, 1)
    reasons: List[str] = []

    if blocking_failures or governance_blocks:
        verdict = "NO_GO"
        if blocking_failures:
            reasons.append("unresolved blocking failure")
        if governance_blocks:
            reasons.append("governance gate blocks release")
    elif contract_mismatch:
        verdict = "DEFER"
        reasons.append("assessment requirements differ from the independently pinned contract")
    elif identity_gaps:
        verdict = "DEFER"
        reasons.append("release identity incomplete")
    elif scope_gaps:
        verdict = "DEFER"
        reasons.append("release scope/risk assessment incomplete")
    elif mode_gap:
        verdict = "DEFER"
        reasons.append(f"{risk_tier} release requires at least {mode_floor} mode")
    elif missing_required_gates:
        verdict = "DEFER"
        reasons.append("required gate set is incomplete")
    elif binding_unknowns:
        verdict = "DEFER"
        reasons.append("binding gate lacks admissible evidence")
    elif missing_governance_gates or governance_unknowns:
        verdict = "DEFER"
        reasons.append("required governance gate unresolved")
    elif material_unknowns:
        verdict = "DEFER"
        reasons.append("material finding remains unverified")
    elif overall_coverage < thresholds["min_coverage"]:
        verdict = "DEFER"
        reasons.append("evidence coverage below risk-tier threshold")
    elif overall_score < thresholds["conditional_score"]:
        verdict = "NO_GO"
        reasons.append("readiness score below conditional threshold")
    elif controlled or accepted_risks or governance_controls or minor_failures or overall_score < thresholds["go_score"]:
        verdict = "GO_WITH_CONTROLS"
        reasons.append("non-blocking residual risk or readiness debt remains")
    else:
        verdict = "GO"
        reasons.append("scope, required gates, governance gates, evidence and thresholds satisfied")

    result = {
        "engine_version": ENGINE_VERSION,
        "contract_hash": contract_hash,
        "contract_mismatch": contract_mismatch,
        "assessment_basis": "declared_manifest",
        "evidence_authentication": "not_performed",
        "deployment_authorization": "not_provided",
        "gating_metrics": {"readiness_score": overall_score, "evidence_coverage": overall_coverage},
        "material_unknowns": [_slim_check(c) for c in material_unknowns],
        "check_states": {c["id"]: c["effective_status"] for c in checks},
        "manifest_version": MANIFEST_VERSION,
        "verdict": verdict,
        "reason": "; ".join(reasons),
        "profile": profile,
        "mode": mode,
        "risk_tier": risk_tier,
        "required_mode_floor": mode_floor,
        "release": release,
        "scope": scope,
        "readiness_score": score,
        "evidence_coverage": coverage,
        "thresholds": thresholds,
        "release_identity_gaps": identity_gaps,
        "scope_gaps": scope_gaps,
        "required_gates": required_gates,
        "missing_required_gates": missing_required_gates,
        "required_governance_surfaces": sorted(governance_surfaces),
        "missing_governance_gates": missing_governance_gates,
        "governance_gates": governance,
        "governance_blocks": governance_blocks,
        "governance_unknowns": governance_unknowns,
        "governance_controls": governance_controls,
        "domain_results": domain_results,
        "binding_failures": [_slim_check(c) for c in binding_failures],
        "binding_unknowns": [_slim_check(c) for c in binding_unknowns],
        "blocking_failures": [_slim_check(c) for c in blocking_failures],
        "minor_failures": [_slim_check(c) for c in minor_failures],
        "controlled_risks": [_slim_check(c) for c in controlled],
        "accepted_risks": [_slim_check(c) for c in accepted_risks],
        "evidence_downgrades": [_slim_check(c) for c in downgraded_unknowns],
        "checks_evaluated": len(checks),
        "snapshot_hash": _snapshot_hash(manifest),
        "revalidation_triggers": _revalidation_triggers(scope),
    }
    result["decision_validity"] = "VALID" if verdict == "GO" else ("WATCH" if verdict == "GO_WITH_CONTROLS" else "NOT_VALID_TO_SHIP")
    return result
