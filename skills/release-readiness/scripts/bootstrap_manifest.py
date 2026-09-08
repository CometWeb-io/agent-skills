#!/usr/bin/env python3
"""Create a release-readiness v2 manifest skeleton from release context.

The bootstrapper derives required gate families from profile + scope and creates
binding UNKNOWN checks. It never assumes unknown risk flags are "no" and never
creates passing evidence.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

ENGINE_PATH = Path(__file__).resolve().with_name("readiness_engine.py")
spec = importlib.util.spec_from_file_location("readiness_engine", ENGINE_PATH)
engine = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(engine)

GATE_DEFAULTS = {
    "release_scope_acceptance": ("product", "critical", "verified", "Release scope and critical acceptance are verified"),
    "candidate_verification": ("qa", "critical", "verified", "Critical behavior is verified on the release candidate"),
    "security_release": ("security", "critical", "verified", "No release-blocking security condition remains"),
    "release_delivery": ("ops", "critical", "verified", "Release delivery/publish path is executable"),
    "recovery_strategy": ("ops", "critical", "verified", "Rollback/disable/forward-recovery path is credible"),
    "observability": ("ops", "major", "verified", "Critical release failures are observable and owned"),
    "operator_docs": ("docs", "major", "supported", "Operator documentation matches the candidate"),
    "consumer_docs": ("docs", "major", "supported", "Consumer documentation matches the release"),
    "support_path": ("support", "major", "supported", "Support/escalation path is available"),
    "billing_entitlements": ("billing", "critical", "verified", "Billing-plan entitlement mapping is correct"),
    "billing_state_transitions": ("billing", "critical", "verified", "Critical billing state transitions are verified"),
    "auth_access_control": ("security", "critical", "verified", "Authentication/authorization boundaries are verified"),
    "migration_integrity": ("ops", "critical", "verified", "Migration integrity and recovery are verified"),
    "sensitive_data_handling": ("security", "critical", "verified", "Sensitive-data handling is verified"),
    "api_compatibility": ("qa", "critical", "verified", "Public API compatibility/migration behavior is verified"),
    "infra_resilience": ("ops", "critical", "verified", "Changed infrastructure failure modes are verified"),
    "store_delivery": ("ops", "critical", "verified", "Store/signing/distribution path matches the candidate"),
    "incident_regression": ("qa", "critical", "verified", "Prior incident failure mode is directly regression-tested"),
    "ai_safety_behavior": ("product", "critical", "verified", "Material high-impact AI failure/guardrail behavior is verified"),
}


def build(context: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(context, dict):
        raise engine.ManifestError("context must be a JSON object")
    profile = str(context.get("profile", "generic")).lower().strip()
    if profile not in engine.PROFILES:
        raise engine.ManifestError(f"invalid profile: {profile!r}")
    mode = str(context.get("mode", "standard")).lower().strip()
    if mode not in engine.MODES:
        raise engine.ManifestError(f"invalid mode: {mode!r}")
    release = context.get("release") or {}
    if not isinstance(release, dict):
        raise engine.ManifestError("release must be an object")

    scope, _, _, surfaces = engine._normalize_scope(context.get("scope"), profile)
    required = engine._required_gates(profile, scope)
    checks: List[Dict[str, Any]] = []
    for gate in required:
        domain, severity, required_evidence, title = GATE_DEFAULTS[gate]
        checks.append({
            "id": f"gate.{gate}",
            "gate": gate,
            "domain": domain,
            "title": title,
            "status": "unknown",
            "severity": severity,
            "binding": True,
            "applicable": True,
            "evidence_level": "missing",
            "required_evidence": required_evidence,
            "freshness": "unknown",
            "evidence": {},
            "owner": "",
            "notes": "Bootstrap placeholder: replace UNKNOWN with evidence-backed state.",
        })

    governance = [
        {
            "surface": surface,
            "status": "counsel_required",
            "evidence": {},
            "rationale": "Bootstrap placeholder: resolve with current authoritative evidence or qualified review.",
        }
        for surface in sorted(surfaces)
    ]

    return {
        "manifest_version": engine.MANIFEST_VERSION,
        "profile": profile,
        "mode": mode,
        "release": dict(release),
        "scope": scope,
        "checks": checks,
        "governance_gates": governance,
    }


def _load(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise engine.ManifestError(f"cannot read context: {exc}") from exc


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bootstrap a release-readiness v2 manifest")
    parser.add_argument("--context", required=True, type=Path, help="Release context JSON")
    parser.add_argument("--output", type=Path, help="Optional output path; stdout otherwise")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    args = parser.parse_args(argv)

    try:
        manifest = build(_load(args.context))
    except engine.ManifestError as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2

    text = json.dumps(manifest, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
