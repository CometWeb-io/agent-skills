#!/usr/bin/env python3
"""Validate bounded UI-to-durable-state contract traces."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SCHEMA = "cometweb.contract-trace/v1"
SCENARIO_KINDS = {"happy", "null_partial", "retry_duplicate", "wrong_tenant", "rollback"}
SCENARIO_STATUSES = {"pass", "fail", "unknown", "blocked"}
EDGE_STATES = {"pass", "fail", "unknown", "blocked"}
EVIDENCE_CHANNELS = {"browser", "backend", "joined"}


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _strings(value: Any) -> bool:
    return isinstance(value, list) and all(_text(item) for item in value)


def validate(payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return ["payload:not-object"]
    errors: list[str] = []
    if payload.get("schema") != SCHEMA:
        errors.append("schema:invalid")
    for field in ("revision", "build", "environment", "journey_id", "claim"):
        if not _text(payload.get(field)):
            errors.append(f"{field}:required")
    if payload.get("claim") not in {"bounded", "incomplete"}:
        errors.append("claim:must-be-bounded-or-incomplete")

    nodes = payload.get("nodes")
    node_ids: set[str] = set()
    if not isinstance(nodes, list) or not nodes:
        errors.append("nodes:required-non-empty-list")
        nodes = []
    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            errors.append(f"nodes[{index}]:not-object")
            continue
        node_id = node.get("id")
        if not _text(node_id):
            errors.append(f"nodes[{index}].id:required")
        elif node_id in node_ids:
            errors.append(f"nodes[{index}].id:duplicate")
        else:
            node_ids.add(node_id)
        if not _text(node.get("kind")):
            errors.append(f"nodes[{index}].kind:required")

    evidence = payload.get("evidence")
    evidence_ids: set[str] = set()
    evidence_channels: dict[str, str] = {}
    if not isinstance(evidence, list):
        errors.append("evidence:required-list")
        evidence = []
    for index, row in enumerate(evidence):
        if not isinstance(row, dict):
            errors.append(f"evidence[{index}]:not-object")
            continue
        evidence_id = row.get("id")
        channel = row.get("channel")
        if not _text(evidence_id):
            errors.append(f"evidence[{index}].id:required")
        elif evidence_id in evidence_ids:
            errors.append(f"evidence[{index}].id:duplicate")
        else:
            evidence_ids.add(evidence_id)
            evidence_channels[evidence_id] = channel
        if channel not in EVIDENCE_CHANNELS:
            errors.append(f"evidence[{index}].channel:invalid")
        if not _text(row.get("locator")):
            errors.append(f"evidence[{index}].locator:required")

    edges = payload.get("edges")
    edge_ids: set[str] = set()
    if not isinstance(edges, list) or not edges:
        errors.append("edges:required-non-empty-list")
        edges = []
    for index, edge in enumerate(edges):
        prefix = f"edges[{index}]"
        if not isinstance(edge, dict):
            errors.append(f"{prefix}:not-object")
            continue
        edge_id = edge.get("id")
        if not _text(edge_id):
            errors.append(f"{prefix}.id:required")
        elif edge_id in edge_ids:
            errors.append(f"{prefix}.id:duplicate")
        else:
            edge_ids.add(edge_id)
        if edge.get("from") not in node_ids:
            errors.append(f"{prefix}.from:unknown-node")
        if edge.get("to") not in node_ids:
            errors.append(f"{prefix}.to:unknown-node")
        if edge.get("state") not in EDGE_STATES:
            errors.append(f"{prefix}.state:invalid")
        refs = edge.get("evidence_ids")
        if not _strings(refs):
            errors.append(f"{prefix}.evidence_ids:required-list")
        else:
            for ref in refs:
                if ref not in evidence_ids:
                    errors.append(f"{prefix}.evidence_ids:unknown-{ref}")
                elif evidence_channels.get(ref) == "browser" and edge.get("kind") in {"auth", "db", "job", "durable"}:
                    errors.append(f"{prefix}.browser-evidence-cannot-prove-backend")

    scenarios = payload.get("scenarios")
    seen_kinds: set[str] = set()
    if not isinstance(scenarios, list):
        errors.append("scenarios:required-list")
        scenarios = []
    for index, scenario in enumerate(scenarios):
        prefix = f"scenarios[{index}]"
        if not isinstance(scenario, dict):
            errors.append(f"{prefix}:not-object")
            continue
        kind = scenario.get("kind")
        if kind not in SCENARIO_KINDS:
            errors.append(f"{prefix}.kind:invalid")
        else:
            seen_kinds.add(kind)
        if scenario.get("status") not in SCENARIO_STATUSES:
            errors.append(f"{prefix}.status:invalid")
        if not _strings(scenario.get("evidence_ids")):
            errors.append(f"{prefix}.evidence_ids:required-list")
        else:
            errors.extend(
                f"{prefix}.evidence_ids:unknown-{ref}"
                for ref in scenario["evidence_ids"] if ref not in evidence_ids
            )
    missing = sorted(SCENARIO_KINDS - seen_kinds)
    if missing:
        errors.append(f"scenarios:missing-{','.join(missing)}")
    if payload.get("claim") == "bounded" and any(
        isinstance(s, dict) and s.get("status") in {"unknown", "blocked"} for s in scenarios
    ):
        errors.append("claim:bounded-with-unresolved-scenario")
    return errors


def result(payload: Any) -> dict[str, Any]:
    errors = validate(payload)
    return {
        "schema": "cometweb.contract-trace-result/v1",
        "status": "INVALID" if errors else "VALID",
        "result": "incomplete" if errors else (
            "incomplete" if payload.get("claim") == "incomplete" else "complete"
        ),
        "errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    args = parser.parse_args(argv)
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "INVALID", "errors": [f"input:{exc}"]}))
        return 2
    output = result(payload)
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if output["status"] == "VALID" else 1


if __name__ == "__main__":
    raise SystemExit(main())
