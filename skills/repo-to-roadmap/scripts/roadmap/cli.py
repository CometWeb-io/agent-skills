"""CLI entry for the repo-to-roadmap kernel."""
from __future__ import annotations

import argparse
import json

from .delta import delta_report, snapshot_report
from .evidence import evidence_report
from .graph import graph_report
from .inventory import coverage_report
from .prioritization import priority_report, sensitivity_report
from .util import parse_json_arg
from .validation import validate_roadmap


def main() -> int:
    parser = argparse.ArgumentParser(description="Repo-to-roadmap v2 deterministic kernel")
    sub = parser.add_subparsers(dest="command", required=True)

    p_evidence = sub.add_parser("evidence", help="Validate/score evidence for one claim")
    p_evidence.add_argument("--claim-json", required=True, help="JSON object or @file.json")

    p_priority = sub.add_parser("priority", help="Apply gate/target blocker rules and score one roadmap candidate")
    p_priority.add_argument("--item-json", required=True, help="JSON object or @file.json")

    p_sensitivity = sub.add_parser("sensitivity", help="Perturb heuristic priority inputs and report lane stability")
    p_sensitivity.add_argument("--item-json", required=True, help="JSON object or @file.json")

    p_graph = sub.add_parser("graph", help="Validate hard dependencies and compute waves/leverage")
    p_graph.add_argument("--items-json", required=True, help="JSON array or @file.json")

    p_coverage = sub.add_parser("coverage", help="Validate and score analysis coverage")
    p_coverage.add_argument("--coverage-json", required=True, help="JSON array or @file.json")

    p_validate = sub.add_parser("validate", help="Validate complete roadmap payload")
    p_validate.add_argument("--roadmap-json", required=True, help="JSON object or @file.json")

    p_snapshot = sub.add_parser("snapshot", help="Create canonical immutable snapshot hash")
    p_snapshot.add_argument("--roadmap-json", required=True, help="JSON object or @file.json")

    p_delta = sub.add_parser("delta", help="Compare two roadmap snapshots and compute revalidation set")
    p_delta.add_argument("--before-json", required=True, help="JSON object or @file.json")
    p_delta.add_argument("--after-json", required=True, help="JSON object or @file.json")

    p_validate.add_argument("--require-valid", action="store_true", help="Exit 1 for a processed invalid roadmap")
    p_validate.add_argument("--expected-scope-sha256", help="Independently saved assessment contract fingerprint")
    p_graph.add_argument("--require-valid", action="store_true", help="Exit 1 for a processed invalid dependency graph")
    args = parser.parse_args()
    try:
        if args.command == "evidence":
            result = evidence_report(parse_json_arg(args.claim_json))
        elif args.command == "priority":
            result = priority_report(parse_json_arg(args.item_json))
        elif args.command == "sensitivity":
            result = sensitivity_report(parse_json_arg(args.item_json))
        elif args.command == "graph":
            payload = parse_json_arg(args.items_json)
            if not isinstance(payload, list):
                raise ValueError("items must be a JSON array")
            result = graph_report(payload)
        elif args.command == "coverage":
            payload = parse_json_arg(args.coverage_json)
            if not isinstance(payload, list):
                raise ValueError("coverage must be a JSON array")
            result = coverage_report(payload)
        elif args.command == "validate":
            result = validate_roadmap(parse_json_arg(args.roadmap_json), expected_scope_sha256=args.expected_scope_sha256)
        elif args.command == "snapshot":
            result = snapshot_report(parse_json_arg(args.roadmap_json))
        elif args.command == "delta":
            result = delta_report(parse_json_arg(args.before_json), parse_json_arg(args.after_json))
        else:
            raise ValueError("unknown command")
    except (ValueError, TypeError, OSError, KeyError, AttributeError, RecursionError):
        print(json.dumps({"status": "error", "error": "invalid input or unreadable file"}))
        return 2

    print(json.dumps(result, ensure_ascii=False, sort_keys=True, allow_nan=False))
    if getattr(args, "require_valid", False) and not result.get("valid", False):
        return 1
    return 0

