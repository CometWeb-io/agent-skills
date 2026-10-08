#!/usr/bin/env python3
"""Executable deterministic behavior evals for every skill that ships a script (CI-gated).

Two suite shapes live under evals/behavior/<skill>/suite.json:

- cometweb-context keeps its assertion suite: every assertion string maps to a
  real handler below. No pass-through theatre.
- Every other skill has an offline command suite (schema
  `cometweb.behavior-suite/v1`): each case runs one of the skill's own scripts
  the way its references tell a user to, and pins what comes back -- the exit
  code plus exact JSON values or output text. A script the references document
  as a library (`kernel.review(payload)`) is driven the same way through
  `"call"`: the named function gets `"args"` and its return value is printed
  as JSON. A case states the behaviour it
  holds in one sentence and is tagged `accept`, `refuse` or `boundary`; a suite
  needs at least three cases and both an accepted and a refused input.

A case whose script imports a package its skill declares in RUNTIME.json is
skipped, with the reason printed, when the interpreter cannot import that
package (a bare `python3` rather than `uv run`); `--require-runtime`, which
check_all passes under `--ci`, fails it instead.

A skill that ships a script under scripts/ without a suite fails the gate, so
coverage cannot quietly shrink. `--coverage` prints the count per skill and
`--skill ID` runs one command suite. LLM blind comparisons remain operator-run
via run_blind_eval_harness.py.
"""
from __future__ import annotations

import argparse
import ast
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path, PurePath
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
# Suites run side by side; each case is its own subprocess in its own temp dir.
JOBS = min(8, os.cpu_count() or 2)
BEHAVIOR = ROOT / "evals" / "behavior"
COMMAND_SCHEMA = "cometweb.behavior-suite/v1"
ASSERTION_SUITE_SKILL = "cometweb-context"
MIN_COMMAND_CASES = 3
CASE_KINDS = {"accept", "refuse", "boundary"}
EXPECT_KEYS = {"exit_code", "json", "json_len", "stdout_contains", "stdout_absent", "stderr_contains"}
CASE_KEYS = {"id", "kind", "behavior", "run", "call", "args", "input", "stdin", "files", "env", "expect"}
# Imports a script as a module, calls one function with JSON arguments from
# stdin and prints the return value; an exception exits 1 with its traceback.
CALL_WRAPPER = """
import importlib.util, json, sys
from pathlib import Path
path, name = Path(sys.argv[1]), sys.argv[2]
sys.path.insert(0, str(path.parent))
spec = importlib.util.spec_from_file_location("behavior_subject", path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
print(json.dumps(getattr(module, name)(*json.load(sys.stdin)), ensure_ascii=False, sort_keys=True))
"""
CASE_TIMEOUT = 60
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
                "status": "unresolved_conflict",
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
                "status": "unresolved_conflict",
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
        # Init a tiny git repo so snapshot succeeds. The contributor's own git
        # config (commit signing, hooks, templates) must not decide whether an
        # offline eval passes, so global and system config are shut out.
        git_env = {
            **os.environ,
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@example.com",
            "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@example.com",
        }
        subprocess.run(["git", "init", "-q"], cwd=tmp, check=True, capture_output=True, env=git_env)
        subprocess.run(
            ["git", "-c", "commit.gpgsign=false", "commit", "--allow-empty", "-q", "-m", "init"],
            cwd=tmp,
            check=True,
            capture_output=True,
            env=git_env,
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


def run_assertion_suite() -> int:
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
    return len(cases)


# --- offline command suites ------------------------------------------------------------------

_MISSING = object()


def skills_with_scripts() -> list[str]:
    """Skills that ship at least one Python script, which a behavior suite must exercise."""
    return sorted({p.parent.parent.name for p in SKILLS.glob("*/scripts/*.py")}
                  | {p.parent.parent.parent.name for p in SKILLS.glob("*/scripts/*/*.py")})


def suite_path(skill: str) -> Path:
    return BEHAVIOR / skill / "suite.json"


def json_at(document: Any, path: str) -> Any:
    """Value at a dotted path (`errors.0`, `result.status`); `$` is the whole document."""
    if path == "$":
        return document
    current = document
    for part in path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        elif isinstance(current, list) and part.lstrip("-").isdigit() and -len(current) <= int(part) < len(current):
            current = current[int(part)]
        else:
            return _MISSING
    return current


def suite_problems(skill: str, data: Any) -> list[str]:
    """Shape problems in a command suite, before anything runs."""
    if not isinstance(data, dict) or data.get("schema") != COMMAND_SCHEMA:
        return [f"{skill}: suite schema must be {COMMAND_SCHEMA}"]
    problems = []
    if data.get("skill") != skill:
        problems.append(f"{skill}: suite names skill {data.get('skill')!r}")
    cases = data.get("cases")
    if not isinstance(cases, list) or len(cases) < MIN_COMMAND_CASES:
        return problems + [f"{skill}: needs at least {MIN_COMMAND_CASES} cases"]
    seen: set[str] = set()
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            problems.append(f"{skill}: case {index} is not an object")
            continue
        cid = case.get("id")
        label = f"{skill}#{cid or index}"
        if not isinstance(cid, str) or not cid or cid in seen:
            problems.append(f"{label}: id must be unique and non-empty")
        seen.add(str(cid))
        if set(case) - CASE_KEYS:
            problems.append(f"{label}: unknown keys {sorted(set(case) - CASE_KEYS)}")
        if case.get("kind") not in CASE_KINDS:
            problems.append(f"{label}: kind must be one of {sorted(CASE_KINDS)}")
        if not isinstance(case.get("behavior"), str) or not case["behavior"].strip():
            problems.append(f"{label}: state the behavior the case holds")
        run = case.get("run")
        if not isinstance(run, list) or not run or not all(isinstance(a, str) for a in run):
            problems.append(f"{label}: run must be a list of strings, script first")
        elif not run[0].startswith("scripts/") or not (SKILLS / skill / run[0]).is_file():
            problems.append(f"{label}: {run[0]!r} is not a script under scripts/")
        if "call" in case:
            if not isinstance(case["call"], str) or not case["call"].isidentifier():
                problems.append(f"{label}: call must name a function")
            if not isinstance(case.get("args"), list):
                problems.append(f"{label}: call needs args, a list of the function's arguments")
            if isinstance(run, list) and len(run) != 1 or {"stdin", "input"} & set(case):
                problems.append(f"{label}: a call takes its arguments from args only")
        elif "args" in case:
            problems.append(f"{label}: args belongs to a call")
        expect = case.get("expect")
        if not isinstance(expect, dict) or not isinstance(expect.get("exit_code"), int):
            problems.append(f"{label}: expect.exit_code is required")
            continue
        if set(expect) - EXPECT_KEYS:
            problems.append(f"{label}: unknown expect keys {sorted(set(expect) - EXPECT_KEYS)}")
        if not set(expect) & (EXPECT_KEYS - {"exit_code"}):
            problems.append(f"{label}: an exit code alone pins nothing; add json or output text")
    kinds = {c.get("kind") for c in cases if isinstance(c, dict)}
    for needed in ("accept", "refuse"):
        if needed not in kinds:
            problems.append(f"{skill}: no {needed} case")
    return problems


def _fill(value: str, slots: dict[str, str]) -> str:
    for key, replacement in slots.items():
        value = value.replace("{" + key + "}", replacement)
    return value


def normalize_scratch_paths(text: str, work: PurePath, expect: dict) -> str:
    """Render only known scratch paths portably, keeping wrong paths distinct.

    A CLI can print native paths, POSIX paths or repr/JSON-escaped paths. Match
    the expected scratch filenames before replacing the root; never rewrite
    arbitrary backslashes, filename differences or paths outside this case.
    """
    def strings(value):
        if isinstance(value, str):
            yield value
        elif isinstance(value, dict):
            for child in value.values():
                yield from strings(child)
        elif isinstance(value, list):
            for child in value:
                yield from strings(child)

    suffixes = {""}
    for value in strings(expect):
        suffixes.update(re.findall(r"\{tmp\}((?:/[\w.-]+)*)", value))
    replacements = {}
    for suffix in suffixes:
        path = work.joinpath(*suffix.lstrip("/").split("/")) if suffix else work
        for spelling in {str(path), path.as_posix(), str(work) + suffix}:
            for variant in {spelling, repr(spelling)[1:-1],
                            json.dumps(spelling, ensure_ascii=False)[1:-1],
                            json.dumps(spelling, ensure_ascii=True)[1:-1]}:
                replacements[variant] = "{tmp}" + suffix
    for spelling in sorted(replacements, key=len, reverse=True):
        pattern = re.escape(spelling) + r"(?=$|[\\/\s'\"<>),;:])"
        text = re.sub(pattern, lambda _, value=replacements[spelling]: value, text)
    return text


def run_command_case(skill: str, case: dict) -> list[str]:
    """Run one case in a scratch directory and compare what came back."""
    label = f"{skill}#{case['id']}"
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp).resolve()
        slots = {"tmp": str(work), "skill": str((SKILLS / skill).resolve()), "input": str(work / "input.json")}
        if "input" in case:
            (work / "input.json").write_text(json.dumps(case["input"], ensure_ascii=False), encoding="utf-8")
        for name, content in (case.get("files") or {}).items():
            target = work / name
            if work not in target.resolve().parents:
                return [f"{label}: file {name!r} escapes the scratch directory"]
            target.parent.mkdir(parents=True, exist_ok=True)
            text = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False)
            target.write_text(text, encoding="utf-8")
        stdin = case.get("stdin")
        if stdin is not None and not isinstance(stdin, str):
            stdin = json.dumps(stdin, ensure_ascii=False)
        script, *args = case["run"]
        prefix = [sys.executable, "-B"]
        if "call" in case:
            prefix += ["-c", CALL_WRAPPER]
            args = [case["call"]]
            stdin = json.dumps(case["args"], ensure_ascii=False)
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"}
        env.update({k: _fill(str(v), slots) for k, v in (case.get("env") or {}).items()})
        try:
            proc = subprocess.run([*prefix, str(SKILLS / skill / script), *(_fill(a, slots) for a in args)],
                                  input=stdin, capture_output=True, encoding="utf-8", cwd=work, env=env,
                                  timeout=CASE_TIMEOUT, check=False)
        except subprocess.TimeoutExpired:
            return [f"{label}: timed out after {CASE_TIMEOUT} s"]
        stdout = normalize_scratch_paths(proc.stdout, work, case["expect"])
        stderr = normalize_scratch_paths(proc.stderr, work, case["expect"])
    expect = case["expect"]
    problems = []
    if proc.returncode != expect["exit_code"]:
        problems.append(f"{label}: exit code {proc.returncode}, expected {expect['exit_code']}; "
                        f"stderr: {stderr.strip()[-300:]}")
    if "json" in expect or "json_len" in expect:
        try:
            document = json.loads(stdout)
        except json.JSONDecodeError:
            return problems + [f"{label}: stdout is not JSON: {stdout.strip()[:200]!r}"]
        for path, value in (expect.get("json") or {}).items():
            got = json_at(document, path)
            if got is _MISSING:
                problems.append(f"{label}: {path} is missing")
            elif got != value:
                problems.append(f"{label}: {path} is {got!r}, expected {value!r}")
        for path, length in (expect.get("json_len") or {}).items():
            got = json_at(document, path)
            if not isinstance(got, (list, dict, str)) or len(got) != length:
                problems.append(f"{label}: {path} has length "
                                f"{len(got) if isinstance(got, (list, dict, str)) else 'n/a'}, expected {length}")
    for text in expect.get("stdout_contains") or []:
        if text not in stdout:
            problems.append(f"{label}: stdout lacks {text!r}")
    for text in expect.get("stdout_absent") or []:
        if text in stdout:
            problems.append(f"{label}: stdout contains {text!r}")
    for text in expect.get("stderr_contains") or []:
        if text not in stderr:
            problems.append(f"{label}: stderr lacks {text!r}")
    return problems


def _requirement_name(requirement: str) -> str:
    return re.split(r"[<>=!~;\[ ]", requirement, maxsplit=1)[0].strip()


def absent_runtime_dependencies(skill: str) -> set[str]:
    """Packages the skill declares in RUNTIME.json that this interpreter cannot import."""
    path = SKILLS / skill / "RUNTIME.json"
    try:
        runtime = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    except json.JSONDecodeError:
        return set()
    groups = runtime.get("dependencies") if isinstance(runtime, dict) else None
    names = {_requirement_name(r) for group in (groups or {}).values() if isinstance(group, list)
             for r in group if isinstance(r, str)}
    return {name for name in names if name and importlib.util.find_spec(name.replace("-", "_")) is None}


def _script_imports(path: Path) -> set[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return set()
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.split(".")[0])
    return names


def run_command_suite(skill: str, skipped: list[str] | None = None,
                      require_runtime: bool = False) -> tuple[int, list[str]]:
    """Run one suite; return the number of cases run and the problems found.

    A case whose script imports a package the skill declares in RUNTIME.json,
    and which this interpreter cannot import, is not run: a bare interpreter
    would fail it for the missing package, not for the behaviour it pins. Its
    reason goes to `skipped`; with `require_runtime` it is a problem instead.
    """
    path = suite_path(skill)
    if not path.is_file():
        return 0, [f"{skill}: ships scripts but has no {path.relative_to(ROOT).as_posix()}"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return 0, [f"{skill}: suite is not JSON: {exc}"]
    problems = suite_problems(skill, data)
    if problems:
        return 0, problems
    absent = absent_runtime_dependencies(skill)
    count = 0
    for case in data["cases"]:
        needs = sorted(absent & _script_imports(SKILLS / skill / case["run"][0])) if absent else []
        if needs:
            reason = (f"{skill}#{case['id']}: needs {', '.join(needs)}, declared in RUNTIME.json "
                      f"and not installed in this interpreter")
            (problems if require_runtime else skipped if skipped is not None else []).append(reason)
            continue
        count += 1
        problems += run_command_case(skill, case)
    return count, problems


def coverage() -> list[tuple[str, int]]:
    rows = []
    for skill in skills_with_scripts():
        path = suite_path(skill)
        try:
            cases = json.loads(path.read_text(encoding="utf-8")).get("cases") if path.is_file() else []
        except (json.JSONDecodeError, AttributeError):
            cases = []
        rows.append((skill, len(cases) if isinstance(cases, list) else 0))
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--skill", help="run only this skill's command suite")
    parser.add_argument("--coverage", action="store_true", help="print behavior cases per skill and exit")
    parser.add_argument("--require-runtime", action="store_true",
                        help="fail a case whose script needs a RUNTIME.json package this interpreter lacks, "
                             "instead of skipping it (check_all passes this under --ci)")
    args = parser.parse_args(argv)
    skipped: list[str] = []
    if args.coverage:
        rows = coverage()
        for skill, count in rows:
            print(f"{skill:32} {count}")
        missing = [skill for skill, count in rows if count == 0]
        print(f"{len(rows) - len(missing)} of {len(rows)} skills with scripts have behavior cases")
        return 1 if missing else 0
    if args.skill:
        count, problems = run_command_suite(args.skill, skipped, args.require_runtime)
        for line in skipped:
            print(f"SKIP: {line}")
        for problem in problems:
            print(f"FAIL: {problem}", file=sys.stderr)
        if not problems:
            print(f"OK: {args.skill} behavior suite ({count} cases{f', {len(skipped)} skipped' if skipped else ''})")
        return 1 if problems else 0

    skills = [s for s in skills_with_scripts() if s != ASSERTION_SUITE_SKILL]
    # Every case runs its script in its own temporary directory, so suites are
    # independent; they run side by side and report in skill order.
    with ThreadPoolExecutor(max_workers=JOBS) as pool:
        assertion = pool.submit(run_assertion_suite)
        # Each suite collects its own skips so the report keeps skill order.
        per_skill: list[list[str]] = [[] for _ in skills]
        suites = list(pool.map(lambda pair: run_command_suite(pair[0], pair[1], args.require_runtime),
                               zip(skills, per_skill, strict=True)))
        assertion_cases = assertion.result()
    for found_skips in per_skill:
        skipped += found_skips
    problems: list[str] = []
    total = 0
    for count, found in suites:
        total += count
        problems += found
    for line in skipped:
        print(f"SKIP: {line}")
    for problem in problems:
        print(f"FAIL: {problem}", file=sys.stderr)
    if problems:
        return 1
    print(f"OK: behavior evals ({assertion_cases} {ASSERTION_SUITE_SKILL} cases, {len(HANDLERS)} assertion "
          f"handlers; {total} command cases across {len(skills)} skills"
          f"{f', {len(skipped)} skipped for a missing RUNTIME.json package' if skipped else ''})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
