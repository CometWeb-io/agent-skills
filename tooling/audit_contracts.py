#!/usr/bin/env python3
"""Read-only validation of declared UI/API/auth/storage paths and their evidence.

No repository scanning, code execution, HTTP calls or deployment authorization.
Checks consistency of supplied records; file hashing is not proof of their origin.
"""
from __future__ import annotations

import argparse
from collections import Counter
import datetime as dt
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Any

MAX_JSON = 4 * 1024 * 1024
MAX_FILE = 16 * 1024 * 1024
MAX_TOTAL = 128 * 1024 * 1024
STATES = {"pass", "fail", "unknown", "blocked"}
KINDS = {"ui", "api", "authorization", "service", "database", "queue", "cache", "external"}
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
ID = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_.:-]{0,127}\Z")


class InvalidTrace(ValueError):
    """Invalid records, distinct from a valid audit that finds failures/gaps."""


def require(ok: bool, message: str) -> None:
    if not ok:
        raise InvalidTrace(message)


def pairs(items: list[tuple[str, Any]]) -> dict:
    result = {}
    for key, value in items:
        require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def invalid_constant(_: str) -> None:
    raise InvalidTrace("non-finite JSON number")


def loads(blob: bytes) -> dict:
    require(len(blob) <= MAX_JSON, "JSON input exceeds limit")
    try:
        value = json.loads(blob, object_pairs_hook=pairs, parse_constant=invalid_constant)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise InvalidTrace("malformed JSON") from exc
    require(isinstance(value, dict), "top-level JSON must be an object")
    return value


def obj(value: Any, required: set[str], optional: set[str], where: str) -> dict:
    require(isinstance(value, dict), f"{where}: expected object")
    require(required <= value.keys() and value.keys() <= required | optional,
            f"{where}: missing or unexpected fields")
    return value


def text(value: Any, where: str, max_length: int = 4000) -> str:
    require(isinstance(value, str) and 0 < len(value.strip()) <= max_length,
            f"{where}: expected nonempty bounded text")
    return value


def array(value: Any, where: str, nonempty: bool = False) -> list:
    require(isinstance(value, list) and len(value) <= 5000 and (not nonempty or bool(value)),
            f"{where}: invalid or oversized list")
    return value


def ids(value: Any, where: str, nonempty: bool = False) -> list[str]:
    values = array(value, where, nonempty)
    require(all(isinstance(v, str) and ID.fullmatch(v) for v in values), f"{where}: invalid identifier")
    require(len(values) == len(set(values)), f"{where}: duplicate identifier")
    return values


def index(value: Any, where: str, nonempty: bool = False) -> dict[str, dict]:
    rows = array(value, where, nonempty)
    require(all(isinstance(r, dict) and isinstance(r.get("id"), str) for r in rows),
            f"{where}: rows need identifiers")
    ids([r["id"] for r in rows], where)
    return {r["id"]: r for r in rows}


def instant(value: Any, where: str) -> dt.datetime:
    text(value, where, 64)
    # ISO 8601 timestamp, not a date, implicit local timezone or epoch number.
    require("T" in value, f"{where}: timestamp requires time")
    try:
        date = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise InvalidTrace(f"{where}: invalid timestamp") from exc
    require(date.tzinfo is not None, f"{where}: timezone required")
    return date.astimezone(dt.timezone.utc)


def local_path(value: Any) -> str:
    text(value, "artifact.path", 512)
    path = PurePosixPath(value)
    require(not path.is_absolute() and "\\" not in value and ":" not in value
            and all(p not in {"", ".", ".."} for p in value.split("/"))
            and not any(ord(c) < 32 for c in value), "unsafe artifact path")
    return value


def verify_file(root: Path, item: dict) -> int:
    require(root.is_dir() and not root.is_symlink(), "artifacts root must be a real directory")
    # Reject symlink ancestors too; resolve() alone would silently accept them.
    require(not any(p.is_symlink() for p in [root, *root.parents]), "symlink in artifacts root")
    target = root
    for part in PurePosixPath(item["path"]).parts:
        target = target / part
        require(not target.is_symlink(), "symlink in evidence path")
    require(target.resolve().is_relative_to(root.resolve()), "evidence path escapes root")
    require(target.is_file(), "evidence file missing or not regular")
    size = target.stat().st_size
    require(size <= MAX_FILE, "evidence file exceeds limit")
    with target.open("rb") as handle:
        blob = handle.read(MAX_FILE + 1)
    require(len(blob) <= MAX_FILE and hashlib.sha256(blob).hexdigest() == item["sha256"],
            "evidence hash mismatch or oversized read")
    return len(blob)


def contract_fingerprint(data: dict) -> str:
    """Hash expectations only; results and before/after build identities may change."""
    contract = {
        "schema": data["schema"],
        "environment": data["scope"]["environment"],
        "nodes": sorted(data["nodes"], key=lambda x: x["id"]),
        "edges": sorted([{k: e[k] for k in ("id", "from", "to", "contract")} for e in data["edges"]],
                        key=lambda x: x["id"]),
        "journeys": sorted([{**j, "required_scenarios": sorted(j["required_scenarios"])}
                            for j in data["journeys"]], key=lambda x: x["id"]),
    }
    return hashlib.sha256(json.dumps(contract, sort_keys=True, ensure_ascii=False,
                                   separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _validate(data: dict, *, artifacts_root: Path | None = None,
             now: dt.datetime | None = None, expected_contract_sha256: str | None = None) -> dict:
    obj(data, {"schema", "scope", "nodes", "edges", "evidence", "journeys", "scenarios"},
        {"claim"}, "trace")
    require(data["schema"] == "cometweb.contract-trace/v1", "unknown trace schema")
    scope = obj(data["scope"], {"revision", "environment", "as_of", "inventory_status", "inventory_refs"},
                {"build"}, "scope")
    require(isinstance(scope["revision"], str) and HEX40.fullmatch(scope["revision"]), "revision must be a full Git SHA")
    text(scope["environment"], "environment", 128)
    if "build" in scope:
        text(scope["build"], "build", 256)
    as_of = instant(scope["as_of"], "as_of")
    clock = now or dt.datetime.now(dt.timezone.utc)
    require(clock.tzinfo is not None and as_of <= clock, "as_of is in the future or clock is naive")
    require(scope["inventory_status"] in {"complete", "partial", "unknown"}, "invalid inventory status")
    claim = data.get("claim", "bounded")
    require(claim in {"bounded", "full_source_trace", "full_runtime_trace"}, "unknown trace claim")
    nodes = index(data["nodes"], "nodes", True)
    edges = index(data["edges"], "edges", True)
    evidence = index(data["evidence"], "evidence")
    journeys = index(data["journeys"], "journeys", True)
    scenarios = index(data["scenarios"], "scenarios")
    for node in nodes.values():
        obj(node, {"id", "kind", "locator"}, set(), "node")
        require(node["kind"] in KINDS, "unknown node kind")
        text(node["locator"], "locator")
    used_evidence = set()
    for item in evidence.values():
        obj(item, {"id", "kind", "revision", "environment", "observed_at", "artifact", "covers_edges"},
            {"build", "run_id", "journey_id", "scenario_id", "outcome"}, "evidence")
        require(item["kind"] in {"source", "execution", "inventory"}, "invalid evidence kind")
        require(item["revision"] == scope["revision"] and item["environment"] == scope["environment"],
                "evidence belongs to a different revision/environment")
        require(instant(item["observed_at"], "observed_at") <= as_of, "evidence is newer than the audit")
        artifact = obj(item["artifact"], {"path", "sha256"}, set(), "artifact")
        local_path(artifact["path"])
        require(isinstance(artifact["sha256"], str) and HEX64.fullmatch(artifact["sha256"]), "invalid artifact hash")
        require(set(ids(item["covers_edges"], "covers_edges")) <= edges.keys(), "evidence covers nonexistent edge")
        if item["kind"] == "execution":
            require("build" in scope and item.get("build") == scope["build"], "execution must match the pinned build")
            text(item.get("run_id"), "run_id", 256)
            require(item.get("outcome") in {"pass", "fail"}, "execution needs an actual outcome")
        else:
            require(not {"run_id", "outcome", "journey_id", "scenario_id"} & item.keys(),
                    "source/inventory evidence cannot impersonate an execution")
    # One path cannot represent two different artifacts in a single evidence bundle.
    artifact_hashes = {}
    for item in evidence.values():
        path, sha = item["artifact"]["path"], item["artifact"]["sha256"]
        require(path not in artifact_hashes or artifact_hashes[path] == sha, "conflicting hashes for one artifact")
        artifact_hashes[path] = sha
    inv_refs = ids(scope["inventory_refs"], "inventory_refs")
    require(all(e in evidence and evidence[e]["kind"] == "inventory" for e in inv_refs), "invalid inventory evidence")
    used_evidence.update(inv_refs)
    if scope["inventory_status"] == "complete":
        require(bool(inv_refs), "complete inventory requires its evidence record")
    incident = {n for edge in edges.values() for n in (edge.get("from"), edge.get("to")) if isinstance(n, str)}
    gaps = ["node:" + n for n in sorted(nodes.keys() - incident)]
    failures = []
    edge_levels = Counter()

    def supporting(refs: Any, target_edges: set[str], state: str, kind: str | None = None) -> list[dict]:
        refs = ids(refs, "evidence_refs")
        require(all(ref in evidence for ref in refs), "dangling evidence reference")
        records = [evidence[ref] for ref in refs]
        used_evidence.update(refs)
        if state in {"pass", "fail"}:
            require(bool(records), "assessed result requires evidence")
        for record in records:
            require(target_edges <= set(record["covers_edges"]), "evidence does not cover the claimed path")
            if kind:
                require(record["kind"] == kind, "wrong evidence kind for assessment method")
            if record["kind"] == "execution" and state in {"pass", "fail"}:
                require(record["outcome"] == state, "execution outcome contradicts the recorded result")
        return records

    for edge in edges.values():
        obj(edge, {"id", "from", "to", "contract", "state", "method", "evidence_refs"}, {"reason"}, "edge")
        require(edge["from"] in nodes and edge["to"] in nodes, "dangling graph endpoint")
        text(edge["contract"], "contract")
        require(edge["state"] in STATES and edge["method"] in {"source", "runtime", "none"}, "unknown edge state/method")
        if edge["state"] in {"pass", "fail"}:
            require(edge["method"] != "none", "assessed edge needs an assessment method")
            supporting(edge["evidence_refs"], {edge["id"]}, edge["state"],
                       "execution" if edge["method"] == "runtime" else "source")
            edge_levels[edge["method"]] += 1
            if edge["state"] == "fail":
                failures.append("edge:" + edge["id"])
        else:
            require(edge["method"] == "none", "unassessed edge must use method none")
            text(edge.get("reason"), "unassessed reason")
            supporting(edge["evidence_refs"], {edge["id"]}, edge["state"])
            gaps.append("edge:" + edge["id"])
    required_scenarios = {}
    for journey in journeys.values():
        obj(journey, {"id", "edge_ids", "required_scenarios"}, set(), "journey")
        sequence = ids(journey["edge_ids"], "journey.edge_ids", True)
        require(set(sequence) <= edges.keys(), "journey references nonexistent edge")
        require(all(edges[a]["to"] == edges[b]["from"] for a, b in zip(sequence, sequence[1:])),
                "journey edges do not form one continuous path")
        for scenario_id in ids(journey["required_scenarios"], "required_scenarios", True):
            require(scenario_id not in required_scenarios, "scenario ID reused across journeys")
            required_scenarios[scenario_id] = journey["id"]
    require(scenarios.keys() <= required_scenarios.keys(), "undeclared scenario result")
    scenario_counts = Counter()
    for sid, jid in required_scenarios.items():
        if sid not in scenarios:
            gaps.append("scenario:" + sid)
            scenario_counts["unknown"] += 1
            continue
        scenario = obj(scenarios[sid], {"id", "journey_id", "state", "evidence_refs"}, {"reason"}, "scenario")
        require(scenario["journey_id"] == jid and scenario["state"] in STATES, "scenario scope/state mismatch")
        state = scenario["state"]
        scenario_counts[state] += 1
        records = supporting(scenario["evidence_refs"], set(journeys[jid]["edge_ids"]), state, "execution")
        for record in records:
            require(record.get("journey_id") == jid and record.get("scenario_id") == sid,
                    "execution belongs to a different journey/scenario")
        if state in {"unknown", "blocked"}:
            text(scenario.get("reason"), "unassessed scenario reason")
            gaps.append("scenario:" + sid)
        elif state == "fail":
            failures.append("scenario:" + sid)
    if scope["inventory_status"] != "complete":
        gaps.append("inventory:not_complete")
    if claim == "full_source_trace":
        require(scope["inventory_status"] == "complete" and sum(edge_levels.values()) == len(edges) and nodes.keys() <= incident,
                "full source trace cannot hide unassessed edges or incomplete inventory")
    if claim == "full_runtime_trace":
        require(not gaps and edge_levels["runtime"] == len(edges),
                "full runtime trace requires runtime evidence for all edges and required scenarios")
    fingerprint = contract_fingerprint(data)
    if expected_contract_sha256 is not None:
        require(isinstance(expected_contract_sha256, str) and HEX64.fullmatch(expected_contract_sha256)
                and expected_contract_sha256 == fingerprint, "reviewed audit contract changed")
    checked_bytes = 0
    if artifacts_root is not None:
        for path, sha in artifact_hashes.items():
            checked_bytes += verify_file(artifacts_root, {"path": path, "sha256": sha})
            require(checked_bytes <= MAX_TOTAL, "total evidence byte budget exceeded")
    return {
        "schema": "cometweb.contract-trace-result/v1",
        "validation": "consistent_supplied_records",
        "contract_sha256": fingerprint,
        "contract_pin": "matched" if expected_contract_sha256 is not None else "not_requested",
        "artifact_integrity": "verified_local_bytes" if artifacts_root is not None else "not_checked",
        "evidence_authentication": "not_performed",
        "revision": scope["revision"], "environment": scope["environment"], "claim": claim,
        "coverage": {"nodes": len(nodes), "edges": len(edges), "source_assessed_edges": edge_levels["source"],
                     "runtime_assessed_edges": edge_levels["runtime"], "required_scenarios": len(required_scenarios),
                     "scenarios": dict(sorted(scenario_counts.items()))},
        "gaps": sorted(gaps), "failures": sorted(failures),
        "unused_evidence_ids": sorted(evidence.keys() - used_evidence),
        "result": "failures_present" if failures else "incomplete" if gaps else "no_failures_in_declared_scope",
        "release_authorization": "not_provided",
    }


def validate(data: dict, *, artifacts_root: Path | None = None,
             now: dt.datetime | None = None, expected_contract_sha256: str | None = None) -> dict:
    """Keep malformed JSON-compatible API inputs in one documented error class."""
    try:
        return _validate(data, artifacts_root=artifacts_root, now=now, expected_contract_sha256=expected_contract_sha256)
    except (TypeError, KeyError, AttributeError, RecursionError) as exc:
        raise InvalidTrace("malformed trace field") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("--artifacts-root", type=Path)
    parser.add_argument("--expected-contract-sha256", help="Previously reviewed expectation fingerprint")
    args = parser.parse_args(argv)
    try:
        with args.trace.open("rb") as handle:
            data = loads(handle.read(MAX_JSON + 1))
        result = validate(data, artifacts_root=args.artifacts_root, expected_contract_sha256=args.expected_contract_sha256)
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 0 if result["result"] == "no_failures_in_declared_scope" else 1
    except (OSError, ValueError, TypeError, KeyError, RecursionError):
        # Do not echo user-supplied text or contents of evidence files into logs.
        print(json.dumps({"validation": "invalid", "result": "not_assessed", "release_authorization": "not_provided"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
