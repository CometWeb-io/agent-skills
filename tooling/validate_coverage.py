#!/usr/bin/env python3
"""Validate audit coverage accounting; source inspection is never promoted to executed testing."""
import argparse
import json
import re
from pathlib import Path

STATUSES = {"inspected", "tested", "sampled", "policy_blocked", "environment_blocked", "unreachable", "not_assessed"}


def validate(data: dict) -> dict:
    if data.get("schema") != "cometweb.audit-coverage/v1" or data.get("inventory_status") not in {"complete","partial","unknown"}:
        raise ValueError("unknown coverage contract or inventory status")
    inventory, checks = data.get("inventory"), data.get("checks")
    if not isinstance(inventory,list) or not inventory or not isinstance(checks,list):
        raise ValueError("a nonempty inventory and checks list are required")
    ids = [item["id"] for item in inventory]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate inventory ID")
    by_id = {}
    for check in checks:
        cid = check.get("id")
        if cid not in ids or cid in by_id or check.get("status") not in STATUSES:
            raise ValueError("unknown/duplicate check ID or status")
        if check["status"] in {"inspected","tested","sampled"} and not check.get("evidence_refs"):
            raise ValueError("inspected/tested/sample status requires evidence references")
        if check["status"] == "tested" and not check.get("execution_ref"):
            raise ValueError("tested status requires an execution record, not only source evidence")
        by_id[cid] = check
    missing = sorted(set(ids) - by_id.keys())
    counts = {status:sum(c["status"] == status for c in checks) for status in sorted(STATUSES)}
    complete = data["inventory_status"] == "complete" and not missing
    claim = data.get("claim", "bounded")
    if claim not in {"bounded","full_source_review","full_execution"}:
        raise ValueError("unknown coverage claim")
    if claim != "bounded":
        if not complete or not re.fullmatch(r"[a-f0-9]{40}", str(data.get("source_revision", ""))) or not data.get("inventory_evidence_ref"):
            raise ValueError("full coverage requires pinned revision and evidenced complete inventory")
        allowed = {"tested"} if claim == "full_execution" else {"inspected","tested"}
        if any(c["status"] not in allowed for c in checks):
            raise ValueError("sampling or blocked/unassessed entries cannot support a full-coverage claim")
    return {"validation":"structural_only", "evidence_authentication":"not_performed", "inventory_status":data["inventory_status"],
            "inventory_count":len(inventory), "accounted_count":len(checks), "missing":missing, "counts":counts, "claim":claim}


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ledger",type=Path)
    args=parser.parse_args()
    print(json.dumps(validate(json.loads(args.ledger.read_text())),indent=2))


if __name__ == "__main__":
    main()
