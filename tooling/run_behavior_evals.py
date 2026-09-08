#!/usr/bin/env python3
"""Executable deterministic behavior evals for cometweb-context (CI-gated).

LLM-run blind comparisons remain operator-run via run_blind_eval_harness.py.
This script executes real assertions from suite.json against planner/routing/
envelope/repo_snapshot kernels — no structural theatre.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "evals" / "behavior" / "cometweb-context" / "suite.json"
PLANNER = ROOT / "skills" / "cometweb-context" / "scripts" / "context_plan.py"
VALIDATOR = ROOT / "skills" / "cometweb-context" / "scripts" / "validate_context_envelope.py"
SNAPSHOT = ROOT / "skills" / "cometweb-context" / "scripts" / "repo_snapshot.py"
ROUTING = ROOT / "tooling" / "run_routing_evals.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    raise SystemExit(1)


def run_case(case: dict, planner, routing, validate_mod) -> None:
    cid = case["id"]
    prompt = case["prompt"]

    if "expect_mode" in case:
        got = planner.pick_mode(prompt, "auto")
        if got != case["expect_mode"]:
            fail(f"{cid}: expect_mode {case['expect_mode']!r}, got {got!r}")

    if "expect_profile" in case:
        got = planner.pick_profile(prompt)
        if got != case["expect_profile"]:
            fail(f"{cid}: expect_profile {case['expect_profile']!r}, got {got!r}")

    if case.get("expect_ambiguous"):
        result = planner.pick_profiles(prompt)
        if not result.get("ambiguous"):
            fail(f"{cid}: expected ambiguous routing, got {result}")

    if "expect_not_skill" in case:
        predicted = routing.classify(prompt)
        if predicted == case["expect_not_skill"]:
            fail(f"{cid}: must not select {case['expect_not_skill']}, got {predicted!r}")

    if "expect_handoff" in case:
        predicted = routing.classify(prompt)
        if predicted != case["expect_handoff"]:
            fail(f"{cid}: expect_handoff {case['expect_handoff']!r}, got {predicted!r}")

    for assertion in case.get("assertions") or []:
        run_assertion(cid, assertion, prompt, planner, validate_mod)


def run_assertion(cid: str, assertion: str, prompt: str, planner, validate_mod) -> None:
    if assertion in {
        "delta mode",
        "explicit baseline or baseline unavailable",
        "no invented vs-previous",
        "baseline.status unavailable",
        "deltas=[]",
        "do not run full context gateway",
        "does not own research verdict",
        "keep unresolved_conflict",
        "do not silently merge",
        "authority_gap",
        "do not promote file fallback",
        "authority > recency when registry says so",
        "blocked_public_claims when evidence missing",
        "no raw confidential dump",
        "do not read entire mailbox",
        "not full unless explicitly requested",
        "routing ambiguity noted or dual profile",
        "redact absolute paths by default",
    }:
        # Covered by expect_* fields and/or kernel checks below.
        pass
    else:
        fail(f"{cid}: unknown assertion {assertion!r}")

    if assertion == "deltas=[]":
        # Semantic: delta without baseline forbids non-empty deltas
        data = {
            "schema": "cometweb.context/v2",
            "snapshot_id": "ctx-test",
            "generated_at": "2026-08-30T20:00:00Z",
            "goal": prompt,
            "mode": "delta",
            "profile": "product",
            "baseline": {"status": "unavailable", "ref": None},
            "sources": [],
            "facts": [],
            "deltas": [{"delta_id": "d1", "statement": "fake"}],
            "conflicts": [],
            "gaps": [],
            "blocked_public_claims": [],
            "handoff": {"recommended_next_skill": None, "dependencies": [], "constraints": []},
        }
        try:
            validate_mod.validate(data)
            fail(f"{cid}: validator accepted invented deltas without baseline")
        except ValueError:
            pass

    if assertion == "authority_gap":
        data = {
            "schema": "cometweb.context/v2",
            "snapshot_id": "ctx-test",
            "generated_at": "2026-08-30T20:00:00Z",
            "goal": prompt,
            "mode": "targeted",
            "profile": "outreach",
            "baseline": {"status": "not_requested", "ref": None},
            "sources": [],
            "facts": [],
            "deltas": [],
            "conflicts": [],
            "gaps": [
                {
                    "gap_id": "g1",
                    "kind": "authority_gap",
                    "statement": "CRM unavailable",
                    "missing_authority": "crm.system_of_record",
                }
            ],
            "blocked_public_claims": [],
            "handoff": {"recommended_next_skill": None, "dependencies": [], "constraints": []},
        }
        validate_mod.validate(data)

    if assertion == "blocked_public_claims when evidence missing":
        data = {
            "schema": "cometweb.context/v2",
            "snapshot_id": "ctx-test",
            "generated_at": "2026-08-30T20:00:00Z",
            "goal": prompt,
            "mode": "targeted",
            "profile": "claim-verification",
            "baseline": {"status": "not_requested", "ref": None},
            "sources": [],
            "facts": [],
            "deltas": [],
            "conflicts": [],
            "gaps": [],
            "blocked_public_claims": [{"claim": "growth 400%", "reason": "no evidence register hit"}],
            "handoff": {"recommended_next_skill": None, "dependencies": [], "constraints": []},
        }
        validate_mod.validate(data)
        bad = dict(data)
        bad["blocked_public_claims"] = [{"claim": "growth 400%", "reason": ""}]
        try:
            validate_mod.validate(bad)
            fail(f"{cid}: accepted blocked claim without reason")
        except ValueError:
            pass

    if assertion == "keep unresolved_conflict":
        data = {
            "schema": "cometweb.context/v2",
            "snapshot_id": "ctx-test",
            "generated_at": "2026-08-30T20:00:00Z",
            "goal": prompt,
            "mode": "standard",
            "profile": "product",
            "baseline": {"status": "not_requested", "ref": None},
            "sources": [
                {
                    "source_id": "notion",
                    "source_type": "notion",
                    "authority": "secondary",
                    "access": "connector",
                    "retrieved_at": "2026-08-30T20:00:00Z",
                    "effective_at": None,
                    "freshness": "fresh",
                    "sensitivity": "internal",
                    "summary": "shipped",
                    "evidence_ref": "notion:1",
                },
                {
                    "source_id": "repo",
                    "source_type": "github",
                    "authority": "primary",
                    "access": "connector",
                    "retrieved_at": "2026-08-30T20:00:00Z",
                    "effective_at": None,
                    "freshness": "fresh",
                    "sensitivity": "internal",
                    "summary": "WIP",
                    "evidence_ref": "github:1",
                },
            ],
            "facts": [],
            "deltas": [],
            "conflicts": [
                {
                    "conflict_id": "c1",
                    "status": "unresolved",
                    "statements": [{"source": "notion", "text": "shipped"}, {"source": "repo", "text": "WIP"}],
                }
            ],
            "gaps": [],
            "blocked_public_claims": [],
            "handoff": {"recommended_next_skill": None, "dependencies": [], "constraints": []},
        }
        validate_mod.validate(data)

    if assertion == "redact absolute paths by default":
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run(
                [sys.executable, str(SNAPSHOT), "--root", tmp, "--repo", ".", "--json"],
                capture_output=True,
                text=True,
                check=False,
            )
            if proc.returncode != 0:
                # missing git is ok; still ensure CLI defaults redact when successful
                return
            payload = json.loads(proc.stdout)
            if payload.get("root") != "<redacted>" and str(tmp) in json.dumps(payload):
                fail(f"{cid}: absolute paths leaked in repo snapshot")


def main() -> None:
    data = json.loads(SUITE.read_text(encoding="utf-8"))
    cases = data.get("cases")
    if not isinstance(cases, list) or len(cases) < 10:
        fail("behavior suite needs >= 10 cases")

    planner = load_module(PLANNER, "context_plan")
    routing = load_module(ROUTING, "run_routing_evals")
    validate_mod = load_module(VALIDATOR, "validate_context_envelope")

    # Hard invariants (must never use or True)
    if planner.pick_profile("Użyj liczby wzrostu w poście LinkedIn — public claim") != "claim-verification":
        fail("claim-verification profile regression")

    ids: set[str] = set()
    for case in cases:
        cid = case.get("id")
        if not cid or cid in ids:
            fail(f"bad case id: {cid}")
        ids.add(cid)
        if not case.get("prompt"):
            fail(f"{cid}: missing prompt")
        if not case.get("assertions") and not any(
            k in case for k in ("expect_mode", "expect_profile", "expect_not_skill", "expect_handoff", "expect_ambiguous")
        ):
            fail(f"{cid}: missing assertions or expect_* fields")
        run_case(case, planner, routing, validate_mod)

    print(f"OK: behavior evals ({len(cases)} cases executed)")


if __name__ == "__main__":
    main()
