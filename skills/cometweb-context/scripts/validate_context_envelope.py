#!/usr/bin/env python3
"""Minimal validator for cometweb.context/v2 envelopes."""

from __future__ import annotations

import json
import pathlib
import sys

REQUIRED = ["schema", "snapshot_id", "generated_at", "goal", "mode", "profile", "baseline", "sources", "facts", "deltas", "conflicts", "gaps", "blocked_public_claims", "handoff"]
MODES = {"targeted", "standard", "delta", "full"}
FRESHNESS = {"fresh", "aging", "stale", "unknown"}


def fail(message: str) -> None:
    raise ValueError(message)


def validate(data: dict) -> None:
    missing = [key for key in REQUIRED if key not in data]
    if missing:
        fail(f"missing keys: {', '.join(missing)}")
    if data["schema"] != "cometweb.context/v2":
        fail("schema must be cometweb.context/v2")
    if data["mode"] not in MODES:
        fail(f"invalid mode: {data['mode']}")
    if not isinstance(data["sources"], list):
        fail("sources must be a list")
    for index, source in enumerate(data["sources"]):
        for key in ["source_id", "source_type", "authority", "access", "retrieved_at", "freshness", "sensitivity", "summary", "evidence_ref"]:
            if key not in source:
                fail(f"sources[{index}] missing {key}")
        if source["freshness"] not in FRESHNESS:
            fail(f"sources[{index}] invalid freshness")
    baseline_status = data.get("baseline", {}).get("status")
    if data["mode"] == "delta" and baseline_status not in {"available", "unavailable"}:
        fail("delta mode requires baseline.status available or unavailable")


def main() -> None:
    if len(sys.argv) != 2:
        print("usage: validate_context_envelope.py <file.json>", file=sys.stderr)
        raise SystemExit(2)
    path = pathlib.Path(sys.argv[1])
    data = json.loads(path.read_text(encoding="utf-8"))
    validate(data)
    print("OK: cometweb.context/v2")


if __name__ == "__main__":
    main()
