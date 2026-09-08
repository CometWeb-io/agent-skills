#!/usr/bin/env python3
"""Validate a web-app-auditor v1.1 JSON report using only the stdlib.

This intentionally checks cross-field protocol invariants that JSON Schema alone
cannot express cleanly. It is not a general JSON Schema validator.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

FINDING_ID = re.compile(r"^F-[0-9]{3}$")
EVIDENCE_ID = re.compile(r"^E-[0-9]{3}$")

MODES = {"page", "area", "crawl", "flow", "data", "visual", "regression", "a11y"}
DEPTHS = {"recon", "standard", "forensic"}
PROFILES = {"hybrid", "browser", "screenshot", "source", "fetch-only"}
ENVIRONMENTS = {"production", "staging", "test", "local", "unknown"}
MUTATION_POLICIES = {"read-only", "safe-test-only"}
VERDICTS = {"do_not_ship", "ship_with_fixes", "ship", "incomplete"}
CONFIDENCE = {"high", "medium", "low"}
KINDS = {"defect", "usability-risk", "recommendation", "needs-repro"}
DEFECT_SEVERITIES = {"blocker", "major", "minor", "nit"}
SEVERITIES = DEFECT_SEVERITIES | {"n/a"}
EXPECTED_BASES = {
    "product-requirement",
    "user-instruction",
    "arithmetic",
    "observed-consistency",
    "API-contract",
    "accessibility-standard",
    "platform-convention",
    "heuristic",
}
EVIDENCE_TYPES = {"screenshot", "dom", "text", "arithmetic", "console", "network", "source"}
INTERACTION_HEAVY_MODES = {"page", "area", "crawl", "flow"}


class Result:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)


def _obj(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _require_keys(result: Result, obj: dict[str, Any], keys: set[str], prefix: str) -> None:
    for key in sorted(keys):
        if key not in obj:
            result.error(f"{prefix}: missing required key '{key}'")


def validate(report: dict[str, Any]) -> Result:
    r = Result()

    required_top = {
        "schemaVersion", "target", "mode", "depth", "confidence", "verdict",
        "capabilities", "environment", "scope", "counts", "findings", "evidence", "coverage",
    }
    _require_keys(r, report, required_top, "report")

    if report.get("schemaVersion") != "1.1":
        r.error("report.schemaVersion must be '1.1'")
    if report.get("mode") not in MODES:
        r.error(f"report.mode must be one of {sorted(MODES)}")
    if report.get("depth") not in DEPTHS:
        r.error(f"report.depth must be one of {sorted(DEPTHS)}")
    if report.get("confidence") not in CONFIDENCE:
        r.error(f"report.confidence must be one of {sorted(CONFIDENCE)}")
    if report.get("verdict") not in VERDICTS:
        r.error(f"report.verdict must be one of {sorted(VERDICTS)}")
    if not isinstance(report.get("target"), str) or not report.get("target", "").strip():
        r.error("report.target must be a non-empty string")

    caps = _obj(report.get("capabilities"))
    _require_keys(r, caps, {"profile", "browser", "source", "screenshots", "console", "network", "filesystem", "codeExecution"}, "capabilities")
    profile = caps.get("profile")
    if profile not in PROFILES:
        r.error(f"capabilities.profile must be one of {sorted(PROFILES)}")
    for key in ("browser", "source", "screenshots", "console", "network", "filesystem", "codeExecution"):
        if key in caps and not isinstance(caps[key], bool):
            r.error(f"capabilities.{key} must be boolean")

    if profile == "hybrid" and not (caps.get("browser") and caps.get("source")):
        r.error("profile 'hybrid' requires browser=true and source=true")
    if profile == "browser" and not caps.get("browser"):
        r.error("profile 'browser' requires browser=true")
    if profile == "screenshot" and (caps.get("browser") or not caps.get("screenshots")):
        r.error("profile 'screenshot' requires browser=false and screenshots=true")
    if profile == "source" and (caps.get("browser") or not caps.get("source")):
        r.error("profile 'source' requires browser=false and source=true")
    if profile == "fetch-only" and (caps.get("browser") or caps.get("source")):
        r.error("profile 'fetch-only' requires browser=false and source=false")
    if caps.get("browser") and caps.get("source") and profile != "hybrid":
        r.warn("browser=true and source=true normally implies profile 'hybrid'")

    env = _obj(report.get("environment"))
    _require_keys(r, env, {"kind", "mutationPolicy"}, "environment")
    env_kind = env.get("kind")
    mutation_policy = env.get("mutationPolicy")
    if env_kind not in ENVIRONMENTS:
        r.error(f"environment.kind must be one of {sorted(ENVIRONMENTS)}")
    if mutation_policy not in MUTATION_POLICIES:
        r.error(f"environment.mutationPolicy must be one of {sorted(MUTATION_POLICIES)}")
    if env_kind in {"production", "unknown"} and mutation_policy != "read-only":
        r.error("production/unknown environment must use mutationPolicy='read-only'")

    scope = _obj(report.get("scope"))
    _require_keys(r, scope, {"in", "out", "viewports", "persona", "covered", "skipped"}, "scope")
    for key in ("in", "out", "viewports", "covered", "skipped"):
        if key in scope and not isinstance(scope[key], list):
            r.error(f"scope.{key} must be an array")
    if "persona" in scope and not isinstance(scope["persona"], str):
        r.error("scope.persona must be a string")

    evidence = _list(report.get("evidence"))
    evidence_ids: set[str] = set()
    evidence_supports: dict[str, set[str]] = {}
    for index, item in enumerate(evidence):
        e = _obj(item)
        prefix = f"evidence[{index}]"
        _require_keys(r, e, {"id", "type", "location", "supports", "redacted"}, prefix)
        eid = e.get("id")
        if not isinstance(eid, str) or not EVIDENCE_ID.match(eid):
            r.error(f"{prefix}.id must match E-###")
        elif eid in evidence_ids:
            r.error(f"duplicate evidence id {eid}")
        else:
            evidence_ids.add(eid)
        if e.get("type") not in EVIDENCE_TYPES:
            r.error(f"{prefix}.type is invalid")
        if e.get("redacted") not in {"yes", "no", "n/a"}:
            r.error(f"{prefix}.redacted must be yes/no/n/a")
        supports = _list(e.get("supports"))
        if not isinstance(e.get("supports"), list):
            r.error(f"{prefix}.supports must be an array")
        evidence_supports[str(eid)] = {str(x) for x in supports}

    findings = _list(report.get("findings"))
    finding_ids: set[str] = set()
    computed = Counter({"blocker": 0, "major": 0, "minor": 0, "nit": 0, "needsRepro": 0, "recommendations": 0})

    for index, item in enumerate(findings):
        f = _obj(item)
        prefix = f"findings[{index}]"
        _require_keys(
            r,
            f,
            {"id", "kind", "severity", "confidence", "title", "where", "repro", "expected", "expectedBasis", "actual", "evidence", "impact", "rootCause"},
            prefix,
        )
        fid = f.get("id")
        if not isinstance(fid, str) or not FINDING_ID.match(fid):
            r.error(f"{prefix}.id must match F-###")
        elif fid in finding_ids:
            r.error(f"duplicate finding id {fid}")
        else:
            finding_ids.add(fid)

        kind = f.get("kind")
        severity = f.get("severity")
        confidence = f.get("confidence")
        if kind not in KINDS:
            r.error(f"{prefix}.kind is invalid")
        if severity not in SEVERITIES:
            r.error(f"{prefix}.severity is invalid")
        if confidence not in CONFIDENCE:
            r.error(f"{prefix}.confidence is invalid")

        if kind in {"defect", "usability-risk"}:
            if severity not in DEFECT_SEVERITIES:
                r.error(f"{prefix}: confirmed {kind} must use blocker/major/minor/nit severity")
            else:
                computed[severity] += 1
            if confidence == "low":
                r.error(f"{prefix}: low-confidence item must be needs-repro, not confirmed {kind}")
        elif kind == "needs-repro":
            computed["needsRepro"] += 1
            if severity != "n/a":
                r.error(f"{prefix}: needs-repro must use severity 'n/a'")
        elif kind == "recommendation":
            computed["recommendations"] += 1
            if severity != "n/a":
                r.error(f"{prefix}: recommendation must use severity 'n/a'")

        title = f.get("title")
        if not isinstance(title, str) or not (8 <= len(title.strip()) <= 160):
            r.error(f"{prefix}.title must be 8..160 characters")
        if not isinstance(f.get("repro"), list) or not f.get("repro"):
            r.error(f"{prefix}.repro must contain at least one step")

        bases = f.get("expectedBasis")
        if not isinstance(bases, list) or not bases:
            r.error(f"{prefix}.expectedBasis must be a non-empty array")
            bases_set: set[str] = set()
        else:
            bases_set = {str(x) for x in bases}
            unknown = bases_set - EXPECTED_BASES
            if unknown:
                r.error(f"{prefix}.expectedBasis has unknown values: {sorted(unknown)}")
        if severity in {"blocker", "major"} and bases_set == {"heuristic"}:
            r.error(f"{prefix}: heuristic-only expectation cannot justify {severity}")

        refs = f.get("evidence")
        if not isinstance(refs, list):
            r.error(f"{prefix}.evidence must be an array of E-### ids")
            refs = []
        if kind in {"defect", "usability-risk"} and not refs:
            r.error(f"{prefix}: confirmed finding requires at least one evidence id")
        for eid in refs:
            if eid not in evidence_ids:
                r.error(f"{prefix}: references missing evidence id {eid}")
            elif fid and fid not in evidence_supports.get(eid, set()):
                r.warn(f"{prefix}: {eid} does not list {fid} in evidence.supports")

        for key in ("expected", "actual", "impact", "rootCause"):
            if not isinstance(f.get(key), str) or not f.get(key, "").strip():
                r.error(f"{prefix}.{key} must be a non-empty string")

    # Evidence -> finding referential integrity.
    for eid, supports in evidence_supports.items():
        for fid in supports:
            if fid not in finding_ids:
                r.error(f"evidence {eid} supports unknown finding {fid}")

    counts = _obj(report.get("counts"))
    required_counts = {"blocker", "major", "minor", "nit", "needsRepro", "recommendations"}
    _require_keys(r, counts, required_counts, "counts")
    for key in sorted(required_counts):
        value = counts.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            r.error(f"counts.{key} must be a non-negative integer")
        elif value != computed[key]:
            r.error(f"counts.{key}={value} but findings compute to {computed[key]}")

    coverage = _obj(report.get("coverage"))
    required_cov = {"totalInScope", "tested", "sampled", "policyBlocked", "environmentBlocked", "unreachable"}
    _require_keys(r, coverage, required_cov, "coverage")
    cov_values: dict[str, int] = {}
    for key in sorted(required_cov):
        value = coverage.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            r.error(f"coverage.{key} must be a non-negative integer")
        else:
            cov_values[key] = value
    if required_cov.issubset(cov_values):
        accounted = sum(cov_values[k] for k in ("tested", "sampled", "policyBlocked", "environmentBlocked", "unreachable"))
        if accounted != cov_values["totalInScope"]:
            r.error(f"coverage arithmetic mismatch: accounted={accounted}, totalInScope={cov_values['totalInScope']}")
    if report.get("depth") == "forensic" and coverage.get("sampled") not in {0, None}:
        r.error("forensic depth cannot use sampled coverage")
    if coverage.get("sampled", 0) > 0 and not str(coverage.get("samplingRule", "")).strip():
        r.error("sampled coverage requires coverage.samplingRule")

    verdict = report.get("verdict")
    blockers = computed["blocker"]
    majors = computed["major"]
    if blockers > 0 and verdict != "do_not_ship":
        r.error("confirmed blocker requires verdict 'do_not_ship'")
    if blockers == 0 and verdict == "do_not_ship":
        r.error("verdict 'do_not_ship' requires at least one confirmed blocker")
    if blockers == 0 and majors > 0 and verdict not in {"ship_with_fixes", "incomplete"}:
        r.error("confirmed major(s) require 'ship_with_fixes' unless the audit is incomplete")
    if blockers == 0 and majors == 0 and verdict == "ship_with_fixes":
        r.error("verdict 'ship_with_fixes' requires at least one confirmed major")
    if verdict == "ship" and (blockers > 0 or majors > 0):
        r.error("verdict 'ship' cannot coexist with blocker/major findings")

    if (
        report.get("mode") in INTERACTION_HEAVY_MODES
        and report.get("depth") in {"standard", "forensic"}
        and not caps.get("browser")
        and verdict != "incomplete"
    ):
        r.error("interaction-heavy standard/forensic audit without browser must use verdict 'incomplete'")

    if verdict == "ship" and coverage.get("unreachable", 0) > 0:
        r.warn("verdict 'ship' with unreachable in-scope controls requires justification")
    if verdict == "ship" and coverage.get("policyBlocked", 0) > 0:
        r.warn("verdict 'ship' with policy-blocked controls is valid only if terminal proof was not required")
    if len(_list(report.get("outOfScope"))) > 3:
        r.error("outOfScope may contain at most 3 observations")

    return r


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate web-app-auditor v1.1 audit-report.json")
    parser.add_argument("report", type=Path)
    parser.add_argument("--json", action="store_true", help="emit machine-readable validation result")
    args = parser.parse_args()

    try:
        report = json.loads(args.report.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"ERROR: report not found: {args.report}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"ERROR: invalid JSON: {exc}", file=sys.stderr)
        return 2

    if not isinstance(report, dict):
        print("ERROR: top-level JSON value must be an object", file=sys.stderr)
        return 2

    result = validate(report)
    if args.json:
        print(json.dumps({"ok": not result.errors, "errors": result.errors, "warnings": result.warnings}, indent=2))
    else:
        for message in result.errors:
            print(f"ERROR: {message}")
        for message in result.warnings:
            print(f"WARNING: {message}")
        if not result.errors:
            suffix = f" ({len(result.warnings)} warning(s))" if result.warnings else ""
            print(f"VALID: web-app-auditor report v1.1{suffix}")

    return 1 if result.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
