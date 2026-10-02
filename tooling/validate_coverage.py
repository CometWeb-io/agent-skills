#!/usr/bin/env python3
"""Validate audit coverage accounting; source inspection is never promoted to executed testing."""
import argparse
import json
import re
import sys
from pathlib import Path

STATUSES = {"inspected", "tested", "sampled", "policy_blocked", "environment_blocked", "unreachable", "not_assessed"}


def validate(data: dict) -> dict:
    if not isinstance(data, dict):
        raise ValueError("coverage ledger must be a JSON object")
    if data.get("schema") != "cometweb.audit-coverage/v1" or data.get("inventory_status") not in ("complete","partial","unknown"):
        raise ValueError("unknown coverage contract or inventory status")
    inventory, checks = data.get("inventory"), data.get("checks")
    if not isinstance(inventory,list) or not inventory or not isinstance(checks,list):
        raise ValueError("a nonempty inventory and checks list are required")
    # Malformed rows must be reported, not crash the validator with a KeyError.
    if not all(isinstance(item, dict) and isinstance(item.get("id"), str) and item["id"] for item in inventory):
        raise ValueError("every inventory entry must be an object with a nonempty string id")
    if not all(isinstance(check, dict) for check in checks):
        raise ValueError("every check must be an object")
    ids = [item["id"] for item in inventory]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate inventory ID")
    by_id = {}
    for check in checks:
        cid = check.get("id")
        status = check.get("status")
        if not isinstance(cid, str) or cid not in ids:
            raise ValueError(f"check references unknown inventory ID: {cid!r}")
        if cid in by_id:
            raise ValueError(f"duplicate check for inventory ID: {cid!r}")
        if not isinstance(status, str) or status not in STATUSES:
            raise ValueError(f"check {cid!r} has unknown status: {status!r}")
        refs = check.get("evidence_refs")
        if status in {"inspected","tested","sampled"} and not (
            isinstance(refs, list) and refs and all(isinstance(r, str) and r.strip() for r in refs)
        ):
            # A bare string or a list of blanks is truthy but references nothing.
            raise ValueError(f"check {cid!r}: inspected/tested/sampled status requires a list of evidence references")
        execution_ref = check.get("execution_ref")
        if status == "tested" and not (isinstance(execution_ref, str) and execution_ref.strip()):
            raise ValueError("tested status requires an execution record, not only source evidence")
        by_id[cid] = check
    missing = sorted(set(ids) - by_id.keys())
    counts = {status:sum(c["status"] == status for c in checks) for status in sorted(STATUSES)}
    complete = data["inventory_status"] == "complete" and not missing
    claim = data.get("claim", "bounded")
    if claim not in ("bounded","full_source_review","full_execution"):
        raise ValueError("unknown coverage claim")
    if claim != "bounded":
        if not complete or not re.fullmatch(r"[a-f0-9]{40}", str(data.get("source_revision", ""))) or not data.get("inventory_evidence_ref"):
            raise ValueError("full coverage requires pinned revision and evidenced complete inventory")
        allowed = {"tested"} if claim == "full_execution" else {"inspected","tested"}
        if any(c["status"] not in allowed for c in checks):
            raise ValueError("sampling or blocked/unassessed entries cannot support a full-coverage claim")
    return {"validation":"structural_only", "evidence_authentication":"not_performed", "inventory_status":data["inventory_status"],
            "inventory_count":len(inventory), "accounted_count":len(checks), "missing":missing, "counts":counts, "claim":claim}


def main(argv: list[str] | None = None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ledger",type=Path)
    args=parser.parse_args(argv)
    try:
        result = validate(json.loads(args.ledger.read_text(encoding="utf-8")))
    except OSError as exc:
        print(f"FAIL: cannot read {args.ledger}: {exc.strerror or exc}", file=sys.stderr)
        return 1
    except ValueError as exc:  # includes JSONDecodeError and UnicodeDecodeError
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result,indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
