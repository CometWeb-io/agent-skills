"""Coverage domain scoring and file-accounting inventory."""
from __future__ import annotations

import importlib.util
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from .constants import COVERAGE_FACTORS
from .util import clamp, normalized, normalized_upper


def coverage_report(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not isinstance(rows, list):
        raise ValueError("coverage must be a list")
    numerator = 0.0
    denominator = 0.0
    incomplete_mandatory: List[str] = []
    sampled: List[str] = []
    unavailable: List[str] = []
    errors: List[str] = []
    names: List[str] = []

    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"coverage[{index}] must be an object")
        name = normalized(row.get("name", f"domain-{index}"))
        names.append(name)
        status = normalized_upper(row.get("status", "UNAVAILABLE"))
        if status not in COVERAGE_FACTORS:
            raise ValueError(f"invalid coverage status for {name}: {status}")
        factor = COVERAGE_FACTORS[status]
        if status == "NOT_APPLICABLE":
            if not normalized(row.get("not_applicable_reason", "")):
                errors.append(f"{name}: NOT_APPLICABLE requires not_applicable_reason")
            continue
        try:
            weight = clamp(float(row.get("weight", 1.0)), 0.0, 10.0)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"coverage weight for {name} must be numeric") from exc
        denominator += weight
        numerator += weight * float(factor)
        if row.get("mandatory") and status != "COMPLETE":
            incomplete_mandatory.append(name)
        if status == "SAMPLED":
            sampled.append(name)
        if status == "UNAVAILABLE":
            unavailable.append(name)

    duplicate_names = sorted({name for name in names if names.count(name) > 1})
    if duplicate_names:
        errors.append(f"duplicate coverage domains: {duplicate_names}")

    score = numerator / denominator if denominator else 0.0
    if score >= 0.90:
        grade = "A"
    elif score >= 0.80:
        grade = "B"
    elif score >= 0.65:
        grade = "C"
    elif score >= 0.50:
        grade = "D"
    else:
        grade = "E"

    if errors:
        scope_claim = "COVERAGE_INVALID"
    elif score >= 0.88 and not incomplete_mandatory:
        scope_claim = "WHOLE_PROJECT_SCOPE_DEFENSIBLE"
    elif score >= 0.65:
        scope_claim = "WHOLE_PROJECT_SCOPE_QUALIFIED"
    else:
        scope_claim = "WHOLE_PROJECT_SCOPE_NOT_DEFENSIBLE"

    return {
        "coverage_score": round(score, 3),
        "coverage_grade": grade,
        "scope_claim": scope_claim,
        "incomplete_mandatory_domains": sorted(set(incomplete_mandatory)),
        "sampled_domains": sorted(set(sampled)),
        "unavailable_domains": sorted(set(unavailable)),
        "errors": errors,
        "note": "Coverage grade is a disclosure aid. Whole-project scope never implies every source file was read unless exhaustive file accounting proves it.",
    }


def file_coverage_report(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Recompute file evidence through the existing inventory auditor.

    No paths or modules supplied by the payload are opened. Commit/tree anchors
    are supplied assessment records; hashing does not authenticate their origin.
    """
    assessment = payload.get("assessment")
    if not isinstance(assessment, dict):
        return {"status": "INVALID", "errors": ["assessment must be an object"], "repositories": []}
    required = normalized_upper(assessment.get("mode", "")) == "EXHAUSTIVE"
    result = {"status": "NOT_REQUESTED", "errors": [], "repositories": [],
              "review_authentication": "not_performed", "runtime_verification": "not_performed"}
    if "file_coverage" not in payload and not required:
        return result
    result["status"] = "EXHAUSTIVE_NOT_PROVEN"
    if "file_coverage" not in payload:
        result["errors"].append("file accounting is required for EXHAUSTIVE mode")
        return result
    # Load only the trusted sibling shipped with this skill, not a package named
    # by the input or one resolved from the caller's current working directory.
    try:
        path = Path(__file__).resolve().parents[1] / "coverage_inventory.py"
        spec = importlib.util.spec_from_file_location("roadmap_pinned_file_accounting", path)
        if spec is None or spec.loader is None:
            raise ValueError("file accounting module is unavailable")
        inventory = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(inventory)
        require = inventory.require
        block = payload["file_coverage"]
        inventory.fields(block, {"schema", "bundles"})
        require(block["schema"] == "cometweb.roadmap-file-coverage/v1", "unsupported file coverage schema")
        bundles = block["bundles"]
        require(isinstance(bundles, list) and 0 < len(bundles) <= 64, "file coverage requires 1-64 bundles")
        repos = assessment.get("repos")
        require(isinstance(repos, list) and 0 < len(repos) <= 64, "file coverage requires pinned repository scopes")
        policy = assessment.get("file_review_policy", "all_inspected")
        require(isinstance(policy, str) and policy in {"all_inspected", "allow_documented_exclusions"},
                "unknown file review policy")
        as_of = inventory.timestamp(assessment.get("as_of"))
        require(as_of <= datetime.now(timezone.utc), "assessment as_of is in the future")
        anchors = {}
        for pin in repos:
            require(isinstance(pin, dict), "invalid repository pin")
            name = inventory.repo_id(pin.get("name"))
            require(name not in anchors, "duplicate repository scope")
            require(isinstance(pin.get("ref"), str) and isinstance(pin.get("tree_sha"), str), "full ref and tree SHA required")
            require(isinstance(pin.get("inventory_sha256"), str), "inventory fingerprint required")
            anchors[name] = pin
        seen, statuses, total_entries = set(), [], 0
        for bundle in bundles:
            inventory.fields(bundle, {"inventory", "ledger"})
            inv, ledger = bundle["inventory"], bundle["ledger"]
            require(isinstance(inv, dict), "invalid inventory object")
            name = inventory.repo_id(inv.get("repository"))
            require(name in anchors and name not in seen, "unknown or duplicate repository bundle")
            pin = anchors[name]
            require(pin["ref"] == inv.get("commit_sha") and pin["tree_sha"] == inv.get("tree_sha"),
                    "inventory differs from the assessment commit/tree pin")
            require(isinstance(inv.get("entries"), list), "inventory entries must be a list")
            total_entries += len(inv["entries"])
            require(total_entries <= inventory.MAX_ENTRIES, "aggregate inventory budget exceeded")
            report = inventory.audit(inv, ledger, expected=pin["inventory_sha256"])
            require(inventory.timestamp(inv["observed_at"]) <= as_of, "inventory is newer than assessment as_of")
            for row in ledger["rows"]:
                if "reviewed_at" in row:
                    require(inventory.timestamp(row["reviewed_at"]) <= as_of, "review is newer than assessment as_of")
            seen.add(name)
            statuses.append(report["result"])
            result["repositories"].append(report)
        require(seen == set(anchors), "one or more assessed repositories lack file accounting")
        acceptable = {"INSPECTION_RECORDS_COMPLETE"}
        if policy == "allow_documented_exclusions":
            acceptable.add("ACCOUNTED_WITH_EXCLUSIONS")
        if not all(status in acceptable for status in statuses):
            result["errors"].append("file accounting has gaps, empty scope, unexpanded submodules or disallowed exclusions")
        else:
            result["status"] = ("ACCOUNTED_WITH_EXCLUSIONS" if "ACCOUNTED_WITH_EXCLUSIONS" in statuses
                                else "INSPECTION_RECORDS_COMPLETE")
        result["policy"] = policy
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RecursionError, ImportError):
        result["status"] = "INVALID"
        # Never reflect source contents, review notes or arbitrary imported data.
        result["errors"].append("file accounting is missing, malformed or inconsistent with assessment pins")
    return result

