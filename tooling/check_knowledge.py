#!/usr/bin/env python3
"""Audit freshness without fetching sources or pretending a timestamp proves a claim."""
from __future__ import annotations
import argparse
import datetime as dt
import json
from pathlib import Path

KINDS = {"platform_requirement", "standard", "heuristic", "observation", "experiment"}


def audit(data: dict, as_of: dt.date) -> dict:
    results = []
    # Existing SEO registry remains the source of truth. It is consumed, not duplicated.
    if isinstance(data.get("groups"), list):
        for group in data["groups"]:
            date = dt.date.fromisoformat(group["last_verified"])
            ttl = group.get("ttl_days", data.get("default_ttl_days"))
            if type(ttl) is not int or ttl <= 0 or not group.get("official_sources"):
                raise ValueError("group needs positive TTL and official sources")
            age = (as_of - date).days
            results.append({"id":group["id"], "status":"future_verification" if age < 0 else "stale" if age > ttl else "within_ttl",
                            "claim_truth":"not_reverified", "claims":len(group.get("claims", [])), "days_remaining":ttl-age})
    elif data.get("schema") == "cometweb.knowledge-rules/v1":
        seen = set()
        for rule in data["rules"]:
            if rule["id"] in seen or rule.get("kind") not in KINDS or not rule.get("statement"):
                raise ValueError("duplicate ID, unknown rule kind or empty claim")
            seen.add(rule["id"])
            if rule.get("state") in {"withdrawn", "unverified"}:
                results.append({"id":rule["id"], "status":rule["state"], "claim_truth":"not_reverified"})
                continue
            if rule.get("state") != "active" or not rule.get("sources") or not rule.get("scope") or not rule.get("regression_tests"):
                raise ValueError("active rule requires source, scope and regression test")
            verified = dt.date.fromisoformat(rule["verified_at"])
            ttl = rule["ttl_days"]
            if type(ttl) is not int or ttl <= 0:
                raise ValueError("TTL must be a positive integer")
            age = (as_of - verified).days
            results.append({"id":rule["id"], "status":"future_verification" if age < 0 else "stale" if age > ttl else "within_ttl", "claim_truth":"not_reverified", "kind":rule["kind"]})
    else:
        raise ValueError("unsupported knowledge registry")
    if not results:
        raise ValueError("empty knowledge registry")
    return {"as_of":as_of.isoformat(), "results":results, "external_verification":"not_run"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("registry", type=Path)
    parser.add_argument("--as-of", type=dt.date.fromisoformat, default=dt.datetime.now(dt.timezone.utc).date())
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    report = audit(json.loads(args.registry.read_text()), args.as_of)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return int(args.strict and any(r["status"] != "within_ttl" for r in report["results"]))


if __name__ == "__main__":
    raise SystemExit(main())
