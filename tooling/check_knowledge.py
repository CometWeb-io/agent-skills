#!/usr/bin/env python3
"""Audit recorded freshness and dependencies; never fetch or infer claim truth from TTL."""
from __future__ import annotations
import argparse
import datetime as dt
import json
import sys
from collections import Counter
from pathlib import Path

KINDS = {"platform_requirement", "standard", "heuristic", "observation", "experiment"}


def dependencies(rule: dict, skills: list[dict] | None) -> dict:
    declared = rule.get("dependencies", {})
    if not isinstance(declared, dict) or set(declared) - {"skills", "adapters", "tooling"}:
        raise ValueError("dependencies must name skills, adapters or tooling")
    for values in declared.values():
        if not isinstance(values, list) or any(not isinstance(v, str) or not v for v in values):
            raise ValueError("dependencies must be lists of non-empty strings")
    selected = declared.get("skills", [])
    if "*" in selected and selected != ["*"]:
        raise ValueError("all-skills selector must stand alone")
    catalog = {s["id"]: s["version"] for s in skills} if skills is not None else None
    if catalog is not None:
        if selected == ["*"]:
            selected = sorted(catalog)
        if set(selected) - catalog.keys():
            raise ValueError("unknown skill dependency")
    adapters = declared.get("adapters", [])
    tooling = declared.get("tooling", [])
    for path in adapters + tooling:
        if Path(path).is_absolute() or ".." in Path(path).parts or "\\" in path:
            raise ValueError("dependency paths must stay repository-relative")
    return {"skills": [{"id": s, "version": catalog[s] if catalog else None} for s in selected],
            "adapters": sorted({expanded for p in adapters for expanded in
                                ([p.replace("*", s) for s in selected] if "*" in p else [p])}) if catalog is not None else adapters,
            "tooling": tooling, "resolution": "registry" if catalog is not None else "declared_only"}


def freshness(verified: str, ttl: int, as_of: dt.date) -> dict:
    if type(ttl) is not int or ttl <= 0:
        raise ValueError("TTL must be a positive integer")
    date = dt.date.fromisoformat(verified)
    age = (as_of - date).days
    status = "future_verification" if age < 0 else "stale" if age > ttl else "within_ttl"
    return {"status": status, "freshness": "expired" if status == "stale" else status,
            "verified_at": verified, "expires_on": (date + dt.timedelta(days=ttl)).isoformat(),
            "days_remaining": ttl - age}


def audit(data: dict, as_of: dt.date, skills: list[dict] | None = None) -> dict:
    if not isinstance(data, dict):
        raise ValueError("knowledge registry must be an object")
    results = []
    # Existing SEO registry remains the source of truth. It is consumed, not duplicated.
    if isinstance(data.get("groups"), list):
        for group in data["groups"]:
            if not group.get("official_sources"):
                raise ValueError("group needs official sources")
            results.append({"id": group["id"],
                            **freshness(group["last_verified"], group.get("ttl_days", data.get("default_ttl_days")), as_of),
                            "claim_truth": "not_reverified", "claims": len(group.get("claims", []))})
    elif data.get("schema") == "cometweb.knowledge-rules/v1":
        if not isinstance(data.get("rules"), list) or any(not isinstance(r, dict) for r in data["rules"]):
            raise ValueError("rules must be a list of objects")
        seen = set()
        for rule in data["rules"]:
            if rule["id"] in seen or rule.get("kind") not in KINDS or not rule.get("statement"):
                raise ValueError("duplicate ID, unknown rule kind or empty claim")
            seen.add(rule["id"])
            result = {"id": rule["id"], "kind": rule["kind"], "claim_truth": "not_reverified",
                      "dependencies": dependencies(rule, skills)}
            if rule.get("state") in {"withdrawn", "unverified"}:
                result["status"] = rule["state"]
            else:
                if rule.get("state") != "active" or not rule.get("sources") or not rule.get("scope") or not rule.get("regression_tests"):
                    raise ValueError("active rule requires source, scope and regression test")
                result.update(freshness(rule["verified_at"], rule["ttl_days"], as_of))
            if "verification" in rule:
                evidence = rule["verification"]
                if (not isinstance(evidence, dict) or evidence.get("read_at") != rule.get("verified_at")
                        or not isinstance(evidence.get("findings"), list) or not evidence["findings"]):
                    raise ValueError("verification must bind findings to verified_at")
                for finding in evidence["findings"]:
                    if (not isinstance(finding, dict) or finding.get("url") not in rule["sources"] or not finding.get("locator")
                            or not finding.get("note") or finding.get("assessment") != "supports"):
                        raise ValueError("verification needs source-bound supporting findings")
                result["recorded_verification"] = evidence
            if "contradiction" in rule:
                evidence = rule["contradiction"]
                if (not isinstance(evidence, dict) or not isinstance(evidence.get("url"), str)
                        or not evidence["url"].startswith("https://") or not evidence.get("note")
                        or not isinstance(evidence.get("observed_at"), str)
                        or dt.date.fromisoformat(evidence["observed_at"]) > as_of):
                    raise ValueError("contradiction requires dated source evidence, not TTL expiry")
                result.update(claim_truth="recorded_contradiction", contradiction=evidence)
            results.append(result)
    else:
        raise ValueError("unsupported knowledge registry")
    if not results:
        raise ValueError("empty knowledge registry")
    impacted = {"skills": {}, "adapters": {}}
    for result in results:
        result["review_status"] = "current_record" if result["status"] == "within_ttl" and result["claim_truth"] != "recorded_contradiction" else "needs_review"
        if result["review_status"] == "needs_review":
            for kind in impacted:
                for dep in result.get("dependencies", {}).get(kind, []):
                    key = dep["id"] if kind == "skills" else dep
                    impacted[kind].setdefault(key, []).append(result["id"])
    return {"as_of": as_of.isoformat(), "results": results, "external_verification": "not_run",
            "summary": dict(Counter(r["review_status"] for r in results)), "needs_review": impacted}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("registry", type=Path)
    parser.add_argument("--as-of", type=dt.date.fromisoformat, default=dt.datetime.now(dt.timezone.utc).date())
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.registry.read_text(encoding="utf-8"))
        catalog = args.registry.parent / "skills.json"
        skills = json.loads(catalog.read_text(encoding="utf-8"))["skills"] if isinstance(data, dict) and data.get("schema") == "cometweb.knowledge-rules/v1" and catalog.is_file() else None
        report = audit(data, args.as_of, skills)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return int(args.strict and bool(report["summary"].get("needs_review")))


if __name__ == "__main__":
    raise SystemExit(main())
