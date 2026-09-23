"""CLI entry for the Evidence Researcher kernel."""
from __future__ import annotations

import argparse
import json
import sys

from .audit import audit
from .constants import VERSION
from .coverage_ops import coverage
from .delta import delta
from .identity import canonical_url, fingerprint_source, make_id, pack_hash, source_policy
from .migrate import migrate_v1
from .refresh import refresh_plan
from .stop import stop_decision
from .template import template
from .temporal_eval import temporal_status
from .util import _json_dump, _load_json
from .validators import validate_ledger


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evidence Researcher deterministic kernel v2")
    parser.add_argument("--version", action="version", version=VERSION)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("canonical-url")
    p.add_argument("--url", required=True)

    p = sub.add_parser("make-id")
    p.add_argument("--kind", choices=["research", "claim", "source", "evidence", "contradiction", "search", "gap", "watch"], required=True)
    p.add_argument("--value", required=True)

    p = sub.add_parser("source-policy")
    p.add_argument("--claim-type", required=True)

    p = sub.add_parser("temporal")
    p.add_argument("--source-json", required=True)
    p.add_argument("--as-of", required=True)
    p.add_argument("--claim-type")
    p.add_argument("--research-id")
    p.add_argument("--research-started-at")

    p = sub.add_parser("fingerprint-source")
    p.add_argument("--source-json", required=True)

    p = sub.add_parser("pack-hash")
    p.add_argument("--ledger-json", required=True)

    for name in ("validate", "coverage", "audit", "refresh-plan", "migrate-v1"):
        p = sub.add_parser(name)
        p.add_argument("--ledger-json", required=True)
        if name == "audit":
            p.add_argument("--require-ready", action="store_true", help="exit 1 unless the research gate is READY")

    p = sub.add_parser("delta")
    p.add_argument("--old-ledger-json", required=True)
    p.add_argument("--new-ledger-json", required=True)

    p = sub.add_parser("stop")
    p.add_argument("--ledger-json", required=True)
    p.add_argument("--no-novelty-rounds", type=int, default=0)
    p.add_argument("--expected-information-gain", type=float, default=1.0)
    p.add_argument("--research-cost", type=float, default=0.0)

    p = sub.add_parser("template")
    p.add_argument("--question", required=True)
    p.add_argument("--as-of", required=True)
    p.add_argument("--mode", choices=["QUICK", "STANDARD", "DEEP"], default="STANDARD")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.command == "canonical-url":
            print(canonical_url(args.url))
        elif args.command == "make-id":
            print(make_id(args.kind, args.value))
        elif args.command == "source-policy":
            _json_dump(source_policy(args.claim_type))
        elif args.command == "temporal":
            _json_dump(temporal_status(_load_json(args.source_json), args.as_of, args.claim_type,
                                      research_id=args.research_id, research_started_at=args.research_started_at))
        elif args.command == "fingerprint-source":
            print(fingerprint_source(_load_json(args.source_json)))
        elif args.command == "pack-hash":
            print(pack_hash(_load_json(args.ledger_json)))
        elif args.command == "validate":
            _json_dump(validate_ledger(_load_json(args.ledger_json)))
        elif args.command == "coverage":
            _json_dump(coverage(_load_json(args.ledger_json)))
        elif args.command == "audit":
            result = audit(_load_json(args.ledger_json))
            _json_dump(result)
            if args.require_ready and result["research_status"] != "READY":
                return 1
        elif args.command == "refresh-plan":
            _json_dump(refresh_plan(_load_json(args.ledger_json)))
        elif args.command == "migrate-v1":
            _json_dump(migrate_v1(_load_json(args.ledger_json)))
        elif args.command == "delta":
            _json_dump(delta(_load_json(args.old_ledger_json), _load_json(args.new_ledger_json)))
        elif args.command == "stop":
            _json_dump(stop_decision(_load_json(args.ledger_json), args.no_novelty_rounds, args.expected_information_gain, args.research_cost))
        elif args.command == "template":
            _json_dump(template(args.question, args.as_of, args.mode))
        else:
            parser.error("unsupported command")
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RecursionError):
        print(json.dumps({"error": "invalid input; research was not assessed"}), file=sys.stderr)
        return 2
    return 0

