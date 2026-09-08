#!/usr/bin/env python3
"""Executable deterministic behavior evals for cometweb-context (CI-gated).

Every assertion string maps to a real handler. No pass-through theatre.
LLM blind comparisons remain operator-run via run_blind_eval_harness.py.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "evals" / "behavior" / "cometweb-context" / "suite.json"
PLANNER = ROOT / "skills" / "cometweb-context" / "scripts" / "context_plan.py"
VALIDATOR = ROOT / "skills" / "cometweb-context" / "scripts" / "validate_context_envelope.py"
SNAPSHOT = ROOT / "skills" / "cometweb-context" / "scripts" / "repo_snapshot.py"
ROUTING = ROOT / "tooling" / "run_routing_evals.py"
SKILL_MD = ROOT / "skills" / "cometweb-context" / "SKILL.md"
SOURCE_REGISTRY = ROOT / "skills" / "cometweb-context" / "references" / "source-registry.json"
SECURITY_MD = ROOT / "skills" / "cometweb-context" / "references" / "security-and-provenance.md"

Handler = Callable[[str, dict, Any, Any, Any], None]


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    raise SystemExit(1)


def base_envelope(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "schema": "cometweb.context/v2",
        "snapshot_id": "ctx-test",
        "generated_at": "2026-08-30T20:00:00Z",
        "goal": "test",
        "mode": "standard",
        "profile": "product",
        "baseline": {"status": "not_requested", "ref": None},
        "sources": [],
        "facts": [],
        "deltas": [],
        "conflicts": [],
        "gaps": [],
        "blocked_public_claims": [],
        "handoff": {"recommended_next_skill": None, "dependencies": [], "constraints": []},
    }
    data.update(overrides)
    return data


def source(
    source_id: str,
    *,
    authority: str = "primary",
    access: str = "connector",
    freshness: str = "fresh",
    sensitivity: str = "internal",
    summary: str = "ok",
) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "source_type": "other",
        "authority": authority,
        "access": access,
        "retrieved_at": "2026-08-30T20:00:00Z",
        "effective_at": None,
        "freshness": freshness,
        "sensitivity": sensitivity,
        "summary": summary,
        "evidence_ref": f"{source_id}:1",
    }


def expect_value_error(validate_mod, data: dict, cid: str, why: str) -> None:
    try:
        validate_mod.validate(data)
    except ValueError:
        return
    fail(f"{cid}: {why}")


def assert_delta_mode(cid: str, case: dict, planner, routing, validate_mod) -> None:
    if planner.pick_mode(case["prompt"], "auto") != "delta":
        fail(f"{cid}: pick_mode is not delta")


def assert_baseline_required(cid: str, case: dict, planner, routing, validate_mod) -> None:
    bad = base_envelope(
        goal=case["prompt"],
        mode="delta",
        baseline={"status": "not_requested", "ref": None},
        deltas=[],
    )
    expect_value_error(validate_mod, bad, cid, "delta with baseline.not_requested should fail")


def assert_no_invented_deltas(cid: str, case: dict, planner, routing, validate_mod) -> None:
    bad = base_envelope(
        goal=case["prompt"],
        mode="delta",
        baseline={"status": "unavailable", "ref": None},
        deltas=[{"delta_id": "d1", "statement": "fake vs previous"}],
    )
    expect_value_error(validate_mod, bad, cid, "invented deltas without baseline accepted")


def assert_baseline_unavailable_ok(cid: str, case: dict, planner, routing, validate_mod) -> None:
    ok = base_envelope(
        goal=case["prompt"],
        mode="delta",
        baseline={"status": "unavailable", "ref": None},
        deltas=[],
    )
    validate_mod.validate(ok)


def assert_deltas_empty_enforced(cid: str, case: dict, planner, routing, validate_mod) -> None:
    assert_no_invented_deltas(cid, case, planner, routing, validate_mod)
    assert_baseline_unavailable_ok(cid, case, planner, routing, validate_mod)


def assert_not_full_gateway(cid: str, case: dict, planner, routing, validate_mod) -> None:
    if routing.classify(case["prompt"]) == "cometweb-context":
        fail(f"{cid}: prompt should not route to cometweb-context")
    if planner.pick_mode(case["prompt"], "auto") == "full":
        fail(f"{cid}: trivial prompt should not pick full mode")


def assert_no_research_verdict(cid: str, case: dict, planner, routing, validate_mod) -> None:
    predicted = routing.classify(case["prompt"])
    if predicted != "evidence-researcher":
        fail(f"{cid}: expected handoff to evidence-researcher, got {predicted!r}")
    skill = SKILL_MD.read_text(encoding="utf-8").casefold()
    if "evidence-researcher" not in skill:
        fail(f"{cid}: SKILL.md must hand off claim truth to evidence-researcher")


def assert_keep_unresolved(cid: str, case: dict, planner, routing, validate_mod) -> None:
    data = base_envelope(
        goal=case["prompt"],
        sources=[
            source("notion", authority="secondary", summary="shipped"),
            source("repo", authority="primary", summary="WIP"),
        ],
        conflicts=[
            {
                "conflict_id": "c1",
                "status": "unresolved",
                "statements": [
                    {"source": "notion", "text": "shipped"},
                    {"source": "repo", "text": "WIP"},
                ],
            }
        ],
    )
    validate_mod.validate(data)


def assert_no_silent_merge(cid: str, case: dict, planner, routing, validate_mod) -> None:
    bad = base_envelope(
        goal=case["prompt"],
        sources=[source("notion"), source("repo")],
        conflicts=[
            {
                "conflict_id": "c1",
                "status": "resolved",
                "statements": [
                    {"source": "notion", "text": "shipped"},
                    {"source": "repo", "text": "WIP"},
                ],
            }
        ],
    )
    expect_value_error(validate_mod, bad, cid, "resolved conflict without basis accepted")


def assert_authority_gap(cid: str, case: dict, planner, routing, validate_mod) -> None:
    ok = base_envelope(
        goal=case["prompt"],
        mode="targeted",
        profile="outreach",
        gaps=[
            {
                "gap_id": "g1",
                "kind": "authority_gap",
                "statement": "CRM unavailable",
                "missing_authority": "crm.system_of_record",
            }
        ],
    )
    validate_mod.validate(ok)
    incomplete = base_envelope(
        goal=case["prompt"],
        gaps=[{"gap_id": "g1", "kind": "authority_gap", "statement": "CRM unavailable"}],
    )
    expect_value_error(validate_mod, incomplete, cid, "authority_gap without missing_authority accepted")


def assert_no_file_fallback_promotion(cid: str, case: dict, planner, routing, validate_mod) -> None:
    crm = json.loads(SOURCE_REGISTRY.read_text(encoding="utf-8"))["domains"]["crm"]
    if crm.get("fallback_policy") != "authority_gap":
        fail(f"{cid}: CRM fallback_policy must be authority_gap, got {crm.get('fallback_policy')!r}")
    bad = base_envelope(
        goal=case["prompt"],
        profile="outreach",
        sources=[
            source(
                "crm-export-csv",
                authority="system_of_record",
                access="fallback",
                summary="exported deals.csv",
            )
        ],
        gaps=[],
    )
    expect_value_error(
        validate_mod,
        bad,
        cid,
        "fallback source promoted to system_of_record without authority_gap",
    )


def assert_authority_over_recency(cid: str, case: dict, planner, routing, validate_mod) -> None:
    levels = json.loads(SOURCE_REGISTRY.read_text(encoding="utf-8"))["authority_levels"]
    if levels.index("canonical") >= levels.index("secondary"):
        fail(f"{cid}: authority_levels must rank canonical above secondary")
    # Stale canonical vs fresh secondary may remain unresolved — never auto-merge on recency.
    data = base_envelope(
        goal=case["prompt"],
        sources=[
            source("canon-doc", authority="canonical", freshness="stale", summary="old decision"),
            source("draft-note", authority="secondary", freshness="fresh", summary="new draft"),
        ],
        conflicts=[
            {
                "conflict_id": "c-auth",
                "status": "unresolved",
                "statements": [
                    {"source": "canon-doc", "text": "old decision"},
                    {"source": "draft-note", "text": "new draft"},
                ],
            }
        ],
    )
    validate_mod.validate(data)
    doc = (ROOT / "skills/cometweb-context/references/source-registry.md").read_text(encoding="utf-8")
    if "freshness" not in doc.casefold() or "authority" not in doc.casefold():
        fail(f"{cid}: source-registry.md must document authority vs freshness")


def assert_blocked_public_claims(cid: str, case: dict, planner, routing, validate_mod) -> None:
    if planner.pick_profile(case["prompt"]) != "claim-verification":
        fail(f"{cid}: expected claim-verification profile")
    ok = base_envelope(
        goal=case["prompt"],
        mode="targeted",
        profile="claim-verification",
        blocked_public_claims=[{"claim": "growth 400%", "reason": "no evidence register hit"}],
    )
    validate_mod.validate(ok)
    bad = dict(ok)
    bad["blocked_public_claims"] = [{"claim": "growth 400%", "reason": ""}]
    expect_value_error(validate_mod, bad, cid, "blocked claim without reason accepted")


def assert_no_raw_confidential(cid: str, case: dict, planner, routing, validate_mod) -> None:
    skill = SKILL_MD.read_text(encoding="utf-8")
    if "Nie wklejaj pełnych prywatnych" not in skill and "nie wklejaj" not in skill.casefold():
        fail(f"{cid}: SKILL.md must forbid pasting full private documents")
    security = SECURITY_MD.read_text(encoding="utf-8").casefold()
    if "confidential" not in security:
        fail(f"{cid}: security-and-provenance.md must define confidential handling")
    # Kernel: confidential facts cannot use multi-KB dump as statement body.
    dump = "X" * 2500
    bad = base_envelope(
        goal=case["prompt"],
        sources=[source("gmail", sensitivity="confidential")],
        facts=[
            {
                "fact_id": "f1",
                "statement": dump,
                "source_ids": ["gmail"],
                "confidence": "medium",
                "sensitivity": "confidential",
            }
        ],
    )
    expect_value_error(validate_mod, bad, cid, "raw confidential dump statement accepted")


def assert_no_full_mailbox(cid: str, case: dict, planner, routing, validate_mod) -> None:
    if planner.pick_profile(case["prompt"]) != "meeting":
        fail(f"{cid}: expected meeting profile")
    groups = planner.load_profiles()["meeting"]
    if "communications" in groups and "crm-or-communications" not in groups:
        fail(f"{cid}: meeting profile must not prefer full communications mailbox")
    if "crm-or-communications" not in groups:
        fail(f"{cid}: meeting profile should use crm-or-communications, not full mailbox")


def assert_not_full_mode(cid: str, case: dict, planner, routing, validate_mod) -> None:
    mode = planner.pick_mode(case["prompt"], "auto")
    if mode == "full":
        fail(f"{cid}: expected non-full mode, got full")
    if case.get("expect_mode") and mode != case["expect_mode"]:
        fail(f"{cid}: mode {mode!r} != expect_mode {case['expect_mode']!r}")


def assert_ambiguity(cid: str, case: dict, planner, routing, validate_mod) -> None:
    result = planner.pick_profiles(case["prompt"])
    if not result.get("ambiguous") or len(result.get("candidates") or []) < 2:
        fail(f"{cid}: expected ambiguous dual profile, got {result}")


def assert_path_redaction(cid: str, case: dict, planner, routing, validate_mod) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        # Init a tiny git repo so snapshot succeeds
        subprocess.run(["git", "init"], cwd=tmp, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", "init"],
            cwd=tmp,
            check=True,
            capture_output=True,
            env={
                **dict(**{k: v for k, v in __import__("os").environ.items()}),
                "GIT_AUTHOR_NAME": "t",
                "GIT_AUTHOR_EMAIL": "t@t",
                "GIT_COMMITTER_NAME": "t",
                "GIT_COMMITTER_EMAIL": "t@t",
            },
        )
        proc = subprocess.run(
            [sys.executable, str(SNAPSHOT), "--root", tmp, "--repo", ".", "--json"],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            fail(f"{cid}: repo_snapshot failed: {proc.stderr}")
        payload = json.loads(proc.stdout)
        if payload.get("root") != "<redacted>":
            fail(f"{cid}: root not redacted: {payload.get('root')!r}")
        blob = json.dumps(payload)
        if tmp in blob:
            fail(f"{cid}: absolute path leaked in snapshot JSON")
        if "observed_at" not in payload or "snapshot_ref" not in payload:
            fail(f"{cid}: snapshot missing observed_at/snapshot_ref")


HANDLERS: dict[str, Handler] = {
    "delta mode": assert_delta_mode,
    "explicit baseline or baseline unavailable": assert_baseline_required,
    "no invented vs-previous": assert_no_invented_deltas,
    "baseline.status unavailable": assert_baseline_unavailable_ok,
    "deltas=[]": assert_deltas_empty_enforced,
    "do not run full context gateway": assert_not_full_gateway,
    "does not own research verdict": assert_no_research_verdict,
    "keep unresolved_conflict": assert_keep_unresolved,
    "do not silently merge": assert_no_silent_merge,
    "authority_gap": assert_authority_gap,
    "do not promote file fallback": assert_no_file_fallback_promotion,
    "authority > recency when registry says so": assert_authority_over_recency,
    "blocked_public_claims when evidence missing": assert_blocked_public_claims,
    "no raw confidential dump": assert_no_raw_confidential,
    "do not read entire mailbox": assert_no_full_mailbox,
    "not full unless explicitly requested": assert_not_full_mode,
    "routing ambiguity noted or dual profile": assert_ambiguity,
    "redact absolute paths by default": assert_path_redaction,
}


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

    assertions = case.get("assertions") or []
    if not assertions and not any(
        k in case for k in ("expect_mode", "expect_profile", "expect_not_skill", "expect_handoff", "expect_ambiguous")
    ):
        fail(f"{cid}: missing assertions or expect_* fields")

    for assertion in assertions:
        handler = HANDLERS.get(assertion)
        if handler is None:
            fail(f"{cid}: unknown assertion {assertion!r}")
        handler(cid, case, planner, routing, validate_mod)


def main() -> None:
    data = json.loads(SUITE.read_text(encoding="utf-8"))
    cases = data.get("cases")
    if not isinstance(cases, list) or len(cases) < 10:
        fail("behavior suite needs >= 10 cases")

    planner = load_module(PLANNER, "context_plan")
    routing = load_module(ROUTING, "run_routing_evals")
    validate_mod = load_module(VALIDATOR, "validate_context_envelope")

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
        run_case(case, planner, routing, validate_mod)

    print(f"OK: behavior evals ({len(cases)} cases, {len(HANDLERS)} assertion handlers)")


if __name__ == "__main__":
    main()
