#!/usr/bin/env python3
import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path


def parse_day(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        raise ValueError(f"Invalid date {value!r}; expected YYYY-MM-DD")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check bundled volatile source groups against their TTL.")
    parser.add_argument("--as-of", help="Date for the check, YYYY-MM-DD; defaults to today")
    parser.add_argument("--groups", help="Comma-separated source-group ids; defaults to all")
    parser.add_argument("--strict", action="store_true", help="Exit 1 if any selected group is stale")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    registry = json.loads((root / "references" / "live-source-registry.json").read_text(encoding="utf-8"))
    as_of = parse_day(args.as_of) if args.as_of else date.today()
    selected = None
    if args.groups:
        selected = {x.strip() for x in args.groups.split(",") if x.strip()}

    known = {g["id"] for g in registry.get("groups", [])}
    if selected is not None:
        unknown = sorted(selected - known)
        if unknown:
            raise ValueError("Unknown source groups: " + ", ".join(unknown))

    rows = []
    stale = False
    has_issue = False
    for group in registry.get("groups", []):
        if selected is not None and group["id"] not in selected:
            continue
        verified = parse_day(group["last_verified"])
        ttl = int(group.get("ttl_days", registry.get("default_ttl_days", 30)))
        raw_age = (as_of - verified).days
        if raw_age < 0:
            age = raw_age
            state = "future"
        else:
            age = raw_age
            state = "fresh" if age <= ttl else "stale"
        stale = stale or state == "stale"
        has_issue = has_issue or state != "fresh"
        rows.append({
            "group": group["id"],
            "platform": group.get("platform"),
            "last_verified": str(verified),
            "age_days": age,
            "ttl_days": ttl,
            "state": state,
            "official_sources": group.get("official_sources", [])
        })

    print(json.dumps({"as_of": str(as_of), "groups": rows, "has_stale": stale, "has_issue": has_issue}, indent=2, ensure_ascii=False))
    return 1 if args.strict and has_issue else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, json.JSONDecodeError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
