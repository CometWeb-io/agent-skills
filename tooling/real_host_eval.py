#!/usr/bin/env python3
"""Measure what a real host does with the skills installed: plan, run, grade, report.

    uv run python tooling/real_host_eval.py plan --out plan.json --per-skill 3
    uv run python tooling/real_host_eval.py run --plan plan.json --host claude --out runs/a   # dry run
    uv run python tooling/real_host_eval.py run --plan plan.json --host claude --out runs/a \\
        --condition both --max-tasks 20 --max-total-usd 5 --execute
    uv run python tooling/real_host_eval.py grade runs/a
    uv run python tooling/real_host_eval.py report runs/a --out scorecard.md

`plan` picks tasks per skill from cases the repository already holds: the
prompt and fixture of each model-eval case, the positive and negative cases of
the routing suites (never the frozen holdout), and, for every skill with an
output rubric, the golden-backed contract that `grade` applies later.

`run` is a thin adapter around a host CLI in headless mode (`claude -p`,
`codex exec`). It prints what it would run and an estimated cost, and starts
nothing, unless `--execute` is given. Each run gets a fresh HOME and host
config directory, an empty working directory, a read-only tool set, the plugin
staged from this checkout (condition `plugin`) or nothing (condition
`baseline`), and only the named credential variables from the environment.

`grade` reads each run's transcript: which skills the host loaded (routing)
and whether the final answer passes `tooling/grade_output.py` for the skill
(output). `report` turns the grades into a scorecard with per-skill pass rates,
Wilson 95% intervals and, when both conditions ran, a paired comparison.

Every number here is about the runs that were made. A pass rate on a dozen
tasks is a wide interval, not a property of the skill; see docs/REAL-HOST-EVALS.md.
"""

from __future__ import annotations

import argparse
import functools
import hashlib
import json
import math
import os
import random
import re
import shlex
import shutil
import subprocess  # nosec B404 - fixed argv lists, never a shell
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tooling"))
from real_host_adapters import preflight as runtime_preflight  # noqa: E402

PLAN_SCHEMA = "cometweb.real-host-eval-plan/v1"
RUN_SCHEMA = "cometweb.real-host-eval-run/v1"
RECORD_SCHEMA = "cometweb.real-host-eval-record/v1"
GRADES_SCHEMA = "cometweb.real-host-eval-grades/v1"
REPORT_SCHEMA = "cometweb.real-host-eval-report/v1"
PLAN_SCHEMA_V1 = PLAN_SCHEMA
RUN_SCHEMA_V1 = RUN_SCHEMA
RECORD_SCHEMA_V1 = RECORD_SCHEMA
GRADES_SCHEMA_V1 = GRADES_SCHEMA
REPORT_SCHEMA_V1 = REPORT_SCHEMA
PLAN_SCHEMA_V2 = "cometweb.real-host-eval-plan/v2"
RUN_SCHEMA_V2 = "cometweb.real-host-eval-run/v2"
RECORD_SCHEMA_V2 = "cometweb.real-host-eval-record/v2"
GRADES_SCHEMA_V2 = "cometweb.real-host-eval-grades/v2"
REPORT_SCHEMA_V2 = "cometweb.real-host-eval-report/v2"
PLAN_SCHEMA = PLAN_SCHEMA_V2
RUN_SCHEMA = RUN_SCHEMA_V2
RECORD_SCHEMA = RECORD_SCHEMA_V2
GRADES_SCHEMA = GRADES_SCHEMA_V2
REPORT_SCHEMA = REPORT_SCHEMA_V2

PLUGIN = "cometweb-agent-skills"
ROUTING_SOURCES = ("evals/routing/suite.json", "evals/routing/adversarial-suite.json")
MODEL_SOURCES = ("evals/model/suite.json", "evals/model/continuation-cases.json")
# The frozen holdout is scored by tooling/routing_holdout.py only. Reading it here
# would turn it into a tuning set; the plan refuses it by name.
FORBIDDEN_SOURCES = ("evals/routing/holdout.json", "evals/routing/holdout.lock.json")
SOURCE_TAGS = {"evals/routing/suite.json": "r", "evals/routing/adversarial-suite.json": "adv",
               "evals/model/suite.json": "m", "evals/model/continuation-cases.json": "mc"}
CONDITIONS = ("plugin", "baseline")
SKILL_PATH = re.compile(r"skills/([a-z0-9][a-z0-9-]*)/SKILL\.md")
Z95 = 1.959963984540054

MAX_RUNS_CEILING = 500
TIMEOUT_RANGE = (10, 3600)
MAX_CAPTURE = 8 * 1024 * 1024


@dataclass(frozen=True)
class Host:
    name: str
    config_env: str
    # Credentials a run may see. Nothing else from the caller's environment is passed.
    auth_env: tuple[str, ...]
    # Rough per-turn context the host adds before any skill text: its own system
    # prompt and tool definitions. An assumption for the estimate, not a measurement.
    overhead_tokens: int
    # Whether the host enforces a per-run dollar cap itself.
    native_budget: bool
    # Read-only tools, so a run cannot change anything outside its temp directory.
    tools: str = ""


HOSTS = {
    "claude": Host("claude", "CLAUDE_CONFIG_DIR", ("ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN"),
                   overhead_tokens=18000, native_budget=True, tools="Read,Glob,Grep,Skill"),
    "codex": Host("codex", "CODEX_HOME", ("OPENAI_API_KEY", "CODEX_API_KEY"),
                  overhead_tokens=9000, native_budget=False),
    "cursor": Host("cursor", "CURSOR_CONFIG_DIR", (), overhead_tokens=12000, native_budget=False),
    "chatgpt": Host("chatgpt", "CHATGPT_CONFIG_DIR", (), overhead_tokens=16000, native_budget=False),
}


# --------------------------------------------------------------------------- shared helpers


def canonical(data: Any) -> bytes:
    return json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def inventory_digest(root: Path, paths: list[Path]) -> tuple[str, dict[str, str]]:
    """Hash an ordered file inventory, including paths to prevent substitution."""
    files: dict[str, str] = {}
    for path in sorted(paths):
        if not path.is_file():
            raise ValueError(f"missing fingerprint input: {path}")
        files[path.relative_to(root).as_posix()] = sha256(path.read_bytes())
    return sha256(canonical(files)), files


def acceptance_fingerprints(root: Path = ROOT) -> dict[str, Any]:
    """Return the inputs frozen by a v2 plan and copied into every run manifest."""
    candidate_paths = [
        root / "VERSION",
        root / ".claude-plugin" / "plugin.json",
        root / ".cursor-plugin" / "plugin.json",
        root / "plugin.json",
        root / "registry" / "plugin-release.json",
        root / "registry" / "skills.json",
    ]
    benchmark_paths = [root / rel for rel in (*ROUTING_SOURCES, *MODEL_SOURCES)]
    rubric_paths = sorted((root / "evals" / "output").glob("*/rubric.json"))
    candidate_sha256, candidate_sources = inventory_digest(root, candidate_paths)
    benchmark_sha256, benchmark_sources = inventory_digest(root, benchmark_paths)
    rubric_sha256, rubric_sources = inventory_digest(root, rubric_paths)
    host_config = root / "registry" / "runtime-hosts.json"
    if not host_config.is_file():
        raise ValueError(f"missing fingerprint input: {host_config}")
    host_config_sha256 = sha256(host_config.read_bytes())
    with tempfile.TemporaryDirectory(prefix="cw-real-host-payload-") as tmp:
        from host_smoke import stage_payload

        payload_sha256 = payload_digest(stage_payload(Path(tmp) / "stage", root))
    return {
        "candidate_sha256": candidate_sha256,
        "payload_sha256": payload_sha256,
        "benchmark_sha256": benchmark_sha256,
        "rubric_sha256": rubric_sha256,
        "host_config_sha256": host_config_sha256,
        "candidate_sources": candidate_sources,
        "benchmark_sources": benchmark_sources,
        "rubric_sources": rubric_sources,
    }


def frozen_hashes(plan_or_manifest: dict[str, Any]) -> dict[str, str]:
    """Read v2 hashes while tolerating v1 artifacts that have none."""
    hashes = plan_or_manifest.get("frozen_hashes")
    if isinstance(hashes, dict):
        return {name: value for name, value in hashes.items() if isinstance(value, str)}
    return {
        name: plan_or_manifest[name]
        for name in ("candidate_sha256", "payload_sha256", "benchmark_sha256",
                     "rubric_sha256", "host_config_sha256")
        if isinstance(plan_or_manifest.get(name), str)
    }


def assert_fingerprints_current(plan: dict[str, Any], root: Path = ROOT) -> None:
    """Refuse a v2 plan whose frozen inputs changed after planning."""
    expected = frozen_hashes(plan)
    if not expected:
        return
    actual = acceptance_fingerprints(root)
    mismatches = [
        name for name in ("candidate_sha256", "payload_sha256", "benchmark_sha256",
                          "rubric_sha256", "host_config_sha256")
        if expected.get(name) and expected[name] != actual[name]
    ]
    if mismatches:
        raise ValueError("frozen acceptance inputs changed: " + ", ".join(mismatches))


def estimate_tokens(text: str) -> int:
    """bytes/4, the same rough ratio tooling/context_budget.py uses. An estimate, labelled as one."""
    return math.ceil(len(text.encode("utf-8")) / 4)


def read_json(path: Path) -> Any:
    posix = path.resolve().as_posix()
    if any(posix.endswith("/" + rel) for rel in FORBIDDEN_SOURCES):
        raise ValueError(f"{path.name} is the frozen holdout; real-host evals must not read it")
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def registry(root: Path = ROOT) -> list[dict[str, Any]]:
    return [s for s in read_json(root / "registry" / "skills.json")["skills"] if s.get("lifecycle") == "active"]


def graded_skills(root: Path = ROOT) -> set[str]:
    return {p.parent.name for p in (root / "evals" / "output").glob("*/rubric.json")}


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9.-]+", "-", text.lower()).strip("-")[:120] or "task"


# --------------------------------------------------------------------------- plan


def _routing_cases(root: Path) -> list[tuple[str, dict]]:
    out = []
    for rel in ROUTING_SOURCES:
        for case in read_json(root / rel)["cases"]:
            out.append((rel, case))
    return out


def _model_cases(root: Path) -> list[tuple[str, dict]]:
    out = []
    for rel in MODEL_SOURCES:
        for case in read_json(root / rel)["cases"]:
            out.append((rel, case))
    return out


def build_plan(root: Path = ROOT, *, skills: list[str] | None = None, per_skill: int = 3,
               negatives_per_skill: int = 1, langs: list[str] | None = None, seed: int = 1,
               canary: bool = False, rng_hex: Any = None) -> dict[str, Any]:
    if not 1 <= per_skill <= 50 or not 0 <= negatives_per_skill <= 50:
        raise ValueError("--per-skill must be 1-50 and --negatives-per-skill 0-50")
    known = {s["id"] for s in registry(root)}
    chosen = sorted(known) if not skills else skills
    unknown = sorted(set(chosen) - known)
    if unknown:
        raise ValueError(f"unknown or inactive skill(s): {', '.join(unknown)}")
    graded = graded_skills(root)
    routing = _routing_cases(root)
    model = _model_cases(root)

    def lang_ok(case: dict) -> bool:
        return not langs or case.get("lang", "en") in langs

    tasks: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    for skill in chosen:
        rng = random.Random(f"{seed}:{skill}")
        positives: list[dict[str, Any]] = []
        mcases = [(src, c) for src, c in model if c["skill"] == skill and lang_ok(c)]
        rng.shuffle(mcases)
        mcases.sort(key=lambda item: not item[1].get("fixture"))  # cases that carry material first
        for src, case in mcases:
            literals = list(case.get("preserve_literals", []))
            checks = ["output"] if (skill in graded or literals) else []
            if not checks:
                continue
            positives.append({
                "source": src, "case_id": case["id"], "role": "model", "prompt": case["prompt"],
                "fixture": case.get("fixture"), "lang": case.get("lang", "pl" if _polish(case["prompt"]) else "en"),
                "checks": checks, "expected_primary_skill": skill, "allowed_secondary_skills": [],
                "must_not_trigger": [], "preserve_literals": literals,
                "review_notes": list(case.get("rubric", [])) or ([case["success"]] if case.get("success") else []),
            })
        rcases = [(src, c) for src, c in routing if c.get("expected_primary_skill") == skill and lang_ok(c)]
        rng.shuffle(rcases)
        for src, case in rcases:
            positives.append({
                "source": src, "case_id": case["id"], "role": "positive", "prompt": case["prompt"], "fixture": None,
                "lang": case.get("lang", "en"), "checks": ["routing"] + (["output"] if skill in graded else []),
                "expected_primary_skill": skill,
                "allowed_secondary_skills": list(case.get("allowed_secondary_skills", [])),
                "must_not_trigger": list(case.get("must_not_trigger", [])), "preserve_literals": [],
                "review_notes": [case["reason"]] if case.get("reason") else [],
            })
        negatives = [(src, c) for src, c in routing if skill in c.get("must_not_trigger", []) and lang_ok(c)]
        rng.shuffle(negatives)
        picked = positives[:per_skill]
        for src, case in negatives[:negatives_per_skill]:
            picked.append({
                "source": src, "case_id": case["id"], "role": "negative", "prompt": case["prompt"], "fixture": None,
                "lang": case.get("lang", "en"), "checks": ["routing"],
                "expected_primary_skill": case.get("expected_primary_skill"),
                "allowed_secondary_skills": list(case.get("allowed_secondary_skills", [])),
                "must_not_trigger": list(case.get("must_not_trigger", [])), "preserve_literals": [],
                "review_notes": [case["reason"]] if case.get("reason") else [],
            })
        if not picked:
            skipped.append({"skill": skill, "reason": "no model or routing case matches the filters"})
            continue
        for task in picked:
            task["skill"] = skill
            task["id"] = f"{skill}--{task['role']}--{SOURCE_TAGS[task['source']]}-{slug(task['case_id'])}"
            if canary and "output" in task["checks"]:
                from grade_output import new_canary

                task["canary"] = new_canary(rng_hex) if rng_hex else new_canary()
            tasks.append(task)
    ids = [t["id"] for t in tasks]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate task id in plan")
    sources = {rel: sha256((root / rel).read_bytes()) for rel in (*ROUTING_SOURCES, *MODEL_SOURCES)}
    plan = {
        "schema": PLAN_SCHEMA,
        "acceptance_version": 2,
        "repo_version": (root / "VERSION").read_text(encoding="utf-8").strip(),
        "sources": sources,
        "excluded_sources": list(FORBIDDEN_SOURCES),
        "selection": {"seed": seed, "per_skill": per_skill, "negatives_per_skill": negatives_per_skill,
                      "langs": langs or [], "skills": chosen, "canary": canary},
        "graded_skills": sorted(graded & set(chosen)),
        "tasks": tasks,
        "skipped": skipped,
    }
    hashes = acceptance_fingerprints(root)
    plan["frozen_hashes"] = {name: hashes[name] for name in (
        "candidate_sha256", "payload_sha256", "benchmark_sha256",
        "rubric_sha256", "host_config_sha256"
    )}
    plan["fingerprint_sources"] = {
        name: hashes[name] for name in ("candidate_sources", "benchmark_sources", "rubric_sources")
    }
    plan.update(plan["frozen_hashes"])
    plan["plan_sha256"] = plan_digest(plan)
    return plan


def _polish(text: str) -> bool:
    return bool(re.search(r"[ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]", text))


def plan_digest(plan: dict[str, Any]) -> str:
    return sha256(canonical({k: v for k, v in plan.items() if k != "plan_sha256"}))


def load_plan(path: Path) -> dict[str, Any]:
    plan = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(plan, dict) or plan.get("schema") not in {PLAN_SCHEMA_V1, PLAN_SCHEMA_V2}:
        raise ValueError(f"{path} is not a supported real-host eval plan")
    if plan.get("plan_sha256") != plan_digest(plan):
        raise ValueError(f"{path} was edited after it was planned (plan_sha256 does not match); re-run plan")
    if not isinstance(plan.get("tasks"), list) or not plan["tasks"]:
        raise ValueError("plan has no tasks")
    if plan.get("acceptance_version") == 2:
        assert_fingerprints_current(plan)
    return plan


def render_prompt(task: dict[str, Any]) -> str:
    """The exact text sent to the host. Fixture material follows the request, as a user would paste it."""
    text = task["prompt"]
    material = dict(task.get("fixture") or {})
    if task.get("canary"):
        material["reviewer_note"] = task["canary"]["instruction"]
    if material:
        text += "\n\nMaterial:\n```json\n" + json.dumps(material, indent=2, ensure_ascii=False) + "\n```"
    return text


# --------------------------------------------------------------------------- run


@dataclass
class RunOptions:
    host: str
    bin: str
    conditions: tuple[str, ...]
    repeat: int = 1
    max_tasks: int = 10
    timeout: int = 300
    max_usd_per_task: float = 0.5
    max_total_usd: float | None = None
    max_total_tokens: int | None = None
    max_turns: int = 8
    model: str | None = None
    price_in: float | None = None
    price_out: float | None = None
    overhead_tokens: int | None = None
    assume_turns: int = 3
    assume_output_tokens: int = 1500
    max_consecutive_errors: int = 2
    seed: int = 1


def validate_options(opts: RunOptions) -> None:
    if opts.host not in HOSTS:
        raise ValueError(f"unknown host {opts.host!r}; known: {', '.join(HOSTS)}")
    if not opts.conditions or any(c not in CONDITIONS for c in opts.conditions):
        raise ValueError("condition must be plugin, baseline or both")
    if not 1 <= opts.repeat <= 20:
        raise ValueError("--repeat must be 1-20")
    if not 1 <= opts.max_tasks <= MAX_RUNS_CEILING:
        raise ValueError(f"--max-tasks must be 1-{MAX_RUNS_CEILING}")
    if not TIMEOUT_RANGE[0] <= opts.timeout <= TIMEOUT_RANGE[1]:
        raise ValueError(f"--timeout must be {TIMEOUT_RANGE[0]}-{TIMEOUT_RANGE[1]} seconds")
    if not 0 < opts.max_usd_per_task <= 50:
        raise ValueError("--max-usd-per-task must be above 0 and at most 50")
    if not 1 <= opts.max_turns <= 100:
        raise ValueError("--max-turns must be 1-100")
    if opts.max_total_usd is not None and opts.max_total_usd <= 0:
        raise ValueError("--max-total-usd must be positive")
    if opts.max_total_tokens is not None and opts.max_total_tokens <= 0:
        raise ValueError("--max-total-tokens must be positive")
    if (opts.price_in is None) != (opts.price_out is None):
        raise ValueError("give both --price-in and --price-out, or neither")
    if opts.model is not None and not re.fullmatch(r"[A-Za-z0-9._:\[\]/-]{1,128}", opts.model):
        raise ValueError("--model must be a plain model identifier")


def schedule(plan: dict[str, Any], opts: RunOptions) -> list[dict[str, Any]]:
    """Task x repeat, both conditions of a pair adjacent and in random order, so drift hits them alike."""
    rng = random.Random(opts.seed)
    tasks = list(plan["tasks"])
    rng.shuffle(tasks)
    jobs = []
    for task in tasks:
        for rep in range(opts.repeat):
            conds = list(opts.conditions)
            rng.shuffle(conds)
            jobs.extend({"task": task, "condition": c, "repeat": rep} for c in conds)
    limit = opts.max_tasks
    if len(opts.conditions) == 2:
        limit -= limit % 2  # never cut a pair in half
    jobs = jobs[:limit]
    for index, job in enumerate(jobs):
        job["run_id"] = f"{index + 1:04d}-{job['condition']}-r{job['repeat']}-{job['task']['id']}"[:160]
    return jobs


@functools.lru_cache(maxsize=8)
def always_on_tokens(root: Path = ROOT) -> int:
    return sum(estimate_tokens(f"{s['id']}: {s['description']}") for s in registry(root))


def skill_body_tokens(skill: str | None, root: Path = ROOT) -> int:
    if not skill:
        return 0
    path = root / "skills" / skill / "SKILL.md"
    return estimate_tokens(path.read_text(encoding="utf-8")) if path.is_file() else 0


def estimate_job(job: dict[str, Any], opts: RunOptions, root: Path = ROOT) -> dict[str, Any]:
    host = HOSTS[opts.host]
    overhead = host.overhead_tokens if opts.overhead_tokens is None else opts.overhead_tokens
    prompt = estimate_tokens(render_prompt(job["task"]))
    skill = 0
    if job["condition"] == "plugin":
        skill = always_on_tokens(root) + skill_body_tokens(job["task"].get("expected_primary_skill"), root)
    per_turn = overhead + prompt + skill
    input_tokens = per_turn * opts.assume_turns
    output_tokens = opts.assume_output_tokens
    usd = None
    if opts.price_in is not None and opts.price_out is not None:
        usd = round((input_tokens * opts.price_in + output_tokens * opts.price_out) / 1_000_000, 4)
    return {"input_tokens": input_tokens, "output_tokens": output_tokens, "usd": usd,
            "usd_cap": opts.max_usd_per_task if host.native_budget else None}


def build_env(host: Host, base: Path) -> dict[str, str]:
    home = base / "home"
    config = base / "config"
    home.mkdir(parents=True, exist_ok=True)
    config.mkdir(parents=True, exist_ok=True)
    env = {"PATH": os.environ.get("PATH", ""), "HOME": str(home), "TMPDIR": str(base), "LANG": "C.UTF-8",
           "NO_COLOR": "1", "CI": "1", host.config_env: str(config), "DISABLE_AUTOUPDATER": "1"}
    for name in host.auth_env:
        if os.environ.get(name):
            env[name] = os.environ[name]
    return env


def build_commands(opts: RunOptions, condition: str, stage: Path, out_file: Path) -> tuple[list[list[str]], list[str]]:
    """(setup argvs that never reach a model, the run argv). The prompt goes on stdin."""
    if opts.host not in {"claude", "codex"}:
        return [], [opts.host, "NOT_RUN", "runtime adapter unavailable"]
    if opts.host == "claude":
        argv = [opts.bin, "-p", "--output-format", "stream-json", "--verbose", "--no-session-persistence",
                "--strict-mcp-config", "--tools", HOSTS["claude"].tools, "--allowedTools", HOSTS["claude"].tools,
                "--max-turns", str(opts.max_turns), "--max-budget-usd", f"{opts.max_usd_per_task:g}"]
        if opts.model:
            argv += ["--model", opts.model]
        if condition == "plugin":
            argv += ["--plugin-dir", str(stage)]
        return [], argv
    setup = []
    if condition == "plugin":
        setup = [[opts.bin, "plugin", "marketplace", "add", str(stage)],
                 [opts.bin, "plugin", "add", f"{PLUGIN}@{PLUGIN}", "--json"]]
    argv = [opts.bin, "exec", "--json", "--skip-git-repo-check", "--sandbox", "read-only",
            "--output-last-message", str(out_file)]
    if opts.model:
        argv += ["--model", opts.model]
    argv.append("-")
    return setup, argv


def payload_digest(stage: Path) -> str:
    h = hashlib.sha256()
    for path in sorted(p for p in stage.rglob("*") if p.is_file()):
        h.update(path.relative_to(stage).as_posix().encode() + b"\0" + path.read_bytes() + b"\0")
    return h.hexdigest()


def materialize_not_run(plan: dict[str, Any], opts: RunOptions, out: Path,
                        reason: str, root: Path = ROOT) -> dict[str, Any]:
    """Record every planned job without invoking an unsupported/unauthed host."""
    jobs = schedule(plan, opts)
    if plan.get("acceptance_version") == 2:
        assert_fingerprints_current(plan, root)
    out.mkdir(parents=True, exist_ok=True)
    (out / "runs").mkdir()
    write_json(out / "plan.json", plan)
    manifest = {
        "schema": RUN_SCHEMA,
        "acceptance_version": plan.get("acceptance_version", 1),
        "execution_status": "NOT_RUN",
        "not_run_reason": reason,
        "plan_sha256": plan["plan_sha256"],
        "host": opts.host,
        "model_requested": opts.model,
        "conditions": list(opts.conditions),
        "repeat": opts.repeat,
        "planned_jobs": len(jobs),
    }
    manifest.update(frozen_hashes(plan))
    if "frozen_hashes" in plan:
        manifest["frozen_hashes"] = dict(plan["frozen_hashes"])
    write_json(out / "manifest.json", manifest)
    for job in jobs:
        run_dir = out / "runs" / job["run_id"]
        run_dir.mkdir(parents=True)
        write_json(run_dir / "record.json", {
            "schema": RECORD_SCHEMA,
            "run_id": job["run_id"],
            "task_id": job["task"]["id"],
            "skill": job["task"]["skill"],
            "condition": job["condition"],
            "repeat": job["repeat"],
            "status": "not_run",
            "execution_status": "NOT_RUN",
            "not_run_reason": reason,
            "activated_skills": [],
            **({"frozen_hashes": dict(plan["frozen_hashes"])} if "frozen_hashes" in plan else {}),
        })
    summary = {
        **manifest,
        "completed_jobs": 0,
        "error_jobs": 0,
        "not_run_jobs": len(jobs),
        "not_started_jobs": 0,
        "stop_reason": reason,
        "spent_usd": 0.0,
        "spent_tokens": 0,
    }
    write_json(out / "manifest.json", summary)
    return summary


def dry_run(plan: dict[str, Any], opts: RunOptions, out: Path | None, stream: Any = None) -> dict[str, Any]:
    stream = stream or sys.stdout
    jobs = schedule(plan, opts)
    placeholder = Path("<temp>") / "stage"
    total_in = total_out = 0
    total_usd: float | None = 0.0 if opts.price_in is not None else None
    lines = [f"DRY RUN - nothing is started. Add --execute to run {len(jobs)} job(s) on {opts.host}.",
             f"plan {plan['plan_sha256'][:12]}  conditions {','.join(opts.conditions)}  repeat {opts.repeat}  "
             f"timeout {opts.timeout}s  max turns {opts.max_turns}", ""]
    for job in jobs:
        task = job["task"]
        run_dir = (out or Path("<out>")) / "runs" / job["run_id"]
        setup, argv = build_commands(opts, job["condition"], placeholder, run_dir / "output.md")
        est = estimate_job(job, opts)
        total_in += est["input_tokens"]
        total_out += est["output_tokens"]
        if total_usd is not None and est["usd"] is not None:
            total_usd += est["usd"]
        lines.append(f"[{job['run_id']}] skill={task['skill']} checks={','.join(task['checks'])}")
        for cmd in setup:
            lines.append(f"  setup: {shlex.join(cmd)}")
        lines.append(f"  run:   {shlex.join(argv)}")
        lines.append(f"  env:   HOME={{temp}}/home {HOSTS[opts.host].config_env}={{temp}}/config "
                     f"credentials={','.join(HOSTS[opts.host].auth_env)} (only if set) cwd={{temp}}/cwd")
        lines.append("  stdin:")
        lines.extend("    " + line for line in render_prompt(task).splitlines())
        usd = f" ~${est['usd']:.4f}" if est["usd"] is not None else ""
        lines.append(f"  estimate: ~{est['input_tokens']} input + ~{est['output_tokens']} output tokens{usd}")
    cap = (f"; hard cap {len(jobs)} x ${opts.max_usd_per_task:g} = ${len(jobs) * opts.max_usd_per_task:.2f} "
           "(the host stops each run at --max-budget-usd)") if HOSTS[opts.host].native_budget else \
        "; this host has no per-run dollar cap, only --timeout and the totals below"
    usd_text = f" ~${total_usd:.2f}" if total_usd is not None else " (no USD: pass --price-in/--price-out per 1M tokens)"
    lines += ["", f"ESTIMATE {len(jobs)} job(s): ~{total_in} input + ~{total_out} output tokens{usd_text}{cap}.",
              "Token figures are bytes/4 over the prompt, skill text and an assumed host overhead of "
              f"{opts.overhead_tokens or HOSTS[opts.host].overhead_tokens} tokens x {opts.assume_turns} turns."]
    if opts.max_total_usd is not None:
        lines.append(f"Run stops before a job that could take the total past ${opts.max_total_usd:g}.")
    print("\n".join(lines), file=stream)
    return {"status": "dry_run", "jobs": len(jobs), "estimated_input_tokens": total_in,
            "estimated_output_tokens": total_out, "estimated_usd": total_usd, "model_calls": 0}


def parse_events(text: str, known: set[str]) -> dict[str, Any]:
    """Pull the final answer, usage, cost and the skills the host loaded out of a JSONL transcript."""
    result: dict[str, Any] = {"output": None, "cost_usd": None, "input_tokens": None, "output_tokens": None,
                              "model": None, "num_turns": None, "is_error": False, "activated_skills": []}
    activated: list[str] = []
    in_tok = out_tok = 0
    saw_usage = False
    last_message = None
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict):
            continue
        for match in SKILL_PATH.finditer(line):
            activated.append(match.group(1))
        kind = event.get("type")
        if kind == "system" and event.get("subtype") == "init" and isinstance(event.get("model"), str):
            result["model"] = event["model"]
        if kind == "assistant":
            content = (event.get("message") or {}).get("content") or []
            for block in content if isinstance(content, list) else []:
                if isinstance(block, dict) and block.get("type") == "tool_use" and block.get("name") == "Skill":
                    name = str((block.get("input") or {}).get("skill") or (block.get("input") or {}).get("command") or "")
                    activated.append(name.lstrip("/").split(":")[-1].strip())
        if kind == "result":
            if isinstance(event.get("result"), str):
                result["output"] = event["result"]
            if isinstance(event.get("total_cost_usd"), (int, float)):
                result["cost_usd"] = float(event["total_cost_usd"])
            if isinstance(event.get("num_turns"), int):
                result["num_turns"] = event["num_turns"]
            result["is_error"] = bool(event.get("is_error"))
            usage = event.get("usage")
            if isinstance(usage, dict) and usage:
                saw_usage = True
                in_tok += sum(int(usage.get(k) or 0) for k in
                              ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
                out_tok += int(usage.get("output_tokens") or 0)
        if kind == "turn.completed" and isinstance(event.get("usage"), dict):
            saw_usage = True
            in_tok += int(event["usage"].get("input_tokens") or 0)
            out_tok += int(event["usage"].get("output_tokens") or 0)
        if kind == "item.completed":
            item = event.get("item") or {}
            if item.get("type") == "agent_message" and isinstance(item.get("text"), str):
                last_message = item["text"]
    if result["output"] is None:
        result["output"] = last_message
    if saw_usage:
        result["input_tokens"], result["output_tokens"] = in_tok, out_tok
    seen: list[str] = []
    for name in activated:
        if name in known and name not in seen:
            seen.append(name)
    result["activated_skills"] = seen
    return result


def _run_capped(argv: list[str], env: dict[str, str], cwd: Path, stdin: str, timeout: int,
                stdout_path: Path, stderr_path: Path) -> tuple[int | None, bool]:
    with stdout_path.open("wb") as out, stderr_path.open("wb") as err:
        try:
            proc = subprocess.run(argv, input=stdin.encode("utf-8"), stdout=out, stderr=err, cwd=cwd, env=env,  # nosec B603
                                  timeout=timeout, check=False, close_fds=True)
            code, timed_out = proc.returncode, False
        except subprocess.TimeoutExpired:
            code, timed_out = None, True
    for path in (stdout_path, stderr_path):
        if path.stat().st_size > MAX_CAPTURE:
            with path.open("r+b") as fh:
                fh.truncate(MAX_CAPTURE)
    return code, timed_out


RETRYABLE_EXIT_CODES = {75, 408, 429, 502, 503, 504}
RETRYABLE_ERROR_MARKERS = (
    "rate limit", "too many requests", "temporarily unavailable", "try again",
    "connection reset", "service unavailable", "overloaded",
)


def retry_metadata(status: str, exit_code: int | None, stderr: str) -> dict[str, Any]:
    """Return retry fields only for failures with an explicit transient signal."""
    if status == "timeout":
        classification = "timeout"
    elif exit_code in RETRYABLE_EXIT_CODES:
        classification = f"exit_code_{exit_code}"
    elif any(marker in stderr.lower() for marker in RETRYABLE_ERROR_MARKERS):
        classification = "transient_host_error"
    else:
        return {}
    return {"retryable": True, "retry_classification": classification, "attempt": 1}


def execute(plan: dict[str, Any], opts: RunOptions, out: Path, root: Path = ROOT,
            stream: Any = None) -> dict[str, Any]:
    from host_smoke import stage_payload

    stream = stream or sys.stdout

    host = HOSTS[opts.host]
    if out.exists() and any(out.iterdir()):
        raise ValueError(f"{out} is not empty; give each run a new directory")
    binary_override = None if opts.bin == opts.host else opts.bin
    capability = runtime_preflight(opts.host, environment=os.environ, root=root,
                                   binary_override=binary_override)
    if capability["status"] != "READY":
        summary = materialize_not_run(plan, opts, out, capability["reason"], root)
        print(
            f"NOT_RUN: {summary['not_run_jobs']} job(s) on {opts.host}; "
            f"reason={summary['not_run_reason']}",
            file=stream,
        )
        return summary
    if opts.max_total_usd is not None and not host.native_budget and opts.price_in is None:
        raise ValueError(f"{opts.host} reports no cost; --max-total-usd needs --price-in/--price-out to be enforced")
    if shutil.which(opts.bin) is None and not Path(opts.bin).is_file():
        raise ValueError(f"host binary {opts.bin!r} not found")
    jobs = schedule(plan, opts)
    known = {s["id"] for s in registry(root)}
    out.mkdir(parents=True, exist_ok=True)
    (out / "runs").mkdir()
    write_json(out / "plan.json", plan)
    with tempfile.TemporaryDirectory(prefix="cw-real-host-") as tmp:
        stage = stage_payload(Path(tmp) / "stage", root)
        version_base = Path(tmp) / "version"
        version_base.mkdir()
        probe = subprocess.run([opts.bin, "--version"], env=build_env(host, version_base),  # nosec B603
                               cwd=version_base, capture_output=True, text=True, timeout=60, check=False)
        manifest = {
            "schema": RUN_SCHEMA, "acceptance_version": plan.get("acceptance_version", 1),
            "plan_sha256": plan["plan_sha256"], "repo_version": plan["repo_version"],
            "host": opts.host, "host_version": (probe.stdout or probe.stderr).strip()[:200],
            "model_requested": opts.model, "conditions": list(opts.conditions), "repeat": opts.repeat,
            "payload_sha256": payload_digest(stage),
            "caps": {"max_tasks": opts.max_tasks, "timeout": opts.timeout, "max_turns": opts.max_turns,
                     "max_usd_per_task": opts.max_usd_per_task if host.native_budget else None,
                     "max_total_usd": opts.max_total_usd, "max_total_tokens": opts.max_total_tokens},
            "prices_per_mtok": {"input": opts.price_in, "output": opts.price_out},
            "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "planned_jobs": len(jobs),
        }
        planned_hashes = frozen_hashes(plan)
        if planned_hashes.get("payload_sha256") and manifest["payload_sha256"] != planned_hashes["payload_sha256"]:
            raise ValueError("staged plugin payload differs from the plan fingerprint")
        manifest.update({name: value for name, value in planned_hashes.items()
                         if name != "payload_sha256"})
        if "frozen_hashes" in plan:
            manifest["frozen_hashes"] = dict(plan["frozen_hashes"])
        write_json(out / "manifest.json", manifest)
        spent_usd = 0.0
        spent_tokens = 0
        consecutive_errors = 0
        stop_reason = None
        records = []
        for job in jobs:
            if opts.max_total_usd is not None:
                upper = opts.max_usd_per_task if host.native_budget else 0.0
                if spent_usd + upper > opts.max_total_usd or spent_usd >= opts.max_total_usd:
                    stop_reason = f"max_total_usd: spent ${spent_usd:.4f} of ${opts.max_total_usd:g}"
                    break
            if opts.max_total_tokens is not None and spent_tokens >= opts.max_total_tokens:
                stop_reason = f"max_total_tokens: spent {spent_tokens} of {opts.max_total_tokens}"
                break
            if consecutive_errors >= opts.max_consecutive_errors:
                stop_reason = f"{consecutive_errors} consecutive errors; check credentials and host flags"
                break
            record = run_job(job, opts, host, stage, out, Path(tmp), known)
            records.append(record)
            cost = record["cost_usd"]
            if cost is None and host.native_budget and record["status"] != "setup_error":
                cost = opts.max_usd_per_task  # unknown spend counts as the cap, never as zero
            spent_usd += cost or 0.0
            spent_tokens += (record["input_tokens"] or 0) + (record["output_tokens"] or 0)
            consecutive_errors = consecutive_errors + 1 if record["status"] != "executed" else 0
            print(f"{record['status']:>11}  {record['run_id']}  skills={','.join(record['activated_skills']) or '-'}",
                  file=stream)
    summary = {**manifest, "finished_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "completed_jobs": sum(r["status"] == "executed" for r in records),
               "error_jobs": sum(r["status"] not in {"executed", "not_run"} for r in records),
               "not_run_jobs": sum(r["status"] == "not_run" for r in records),
               "not_started_jobs": len(jobs) - len(records), "stop_reason": stop_reason,
               "spent_usd": round(spent_usd, 6), "spent_tokens": spent_tokens,
               "models_reported": sorted({r["model"] for r in records if r.get("model")})}
    write_json(out / "manifest.json", summary)
    return summary


def run_job(job: dict[str, Any], opts: RunOptions, host: Host, stage: Path, out: Path, tmp: Path,
            known: set[str]) -> dict[str, Any]:
    task = job["task"]
    run_dir = out / "runs" / job["run_id"]
    run_dir.mkdir(parents=True)
    base = Path(tempfile.mkdtemp(prefix="job-", dir=tmp))
    env = build_env(host, base)
    cwd = base / "cwd"
    cwd.mkdir()
    out_file = run_dir / "output.md"
    setup, argv = build_commands(opts, job["condition"], stage, out_file)
    prompt = render_prompt(task)
    record: dict[str, Any] = {
        "schema": RECORD_SCHEMA, "acceptance_version": 2, "run_id": job["run_id"],
        "task_id": task["id"], "skill": task["skill"],
        "condition": job["condition"], "repeat": job["repeat"], "argv": argv, "setup": setup,
        "env_keys": sorted(env), "prompt_sha256": sha256(prompt.encode("utf-8")),
        "status": "executed", "execution_status": "EXECUTED",
        "exit_code": None, "elapsed_seconds": None, "cost_usd": None, "input_tokens": None, "output_tokens": None,
        "model": None, "num_turns": None, "activated_skills": [],
    }
    (run_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
    for index, cmd in enumerate(setup):
        proc = subprocess.run(cmd, env=env, cwd=cwd, capture_output=True, text=True,  # nosec B603
                              timeout=120, check=False)
        if proc.returncode != 0:
            record.update(status="setup_error", execution_status="ERROR", exit_code=proc.returncode)
            (run_dir / f"setup-{index}.stderr.txt").write_text(proc.stderr[-4000:], encoding="utf-8")
            retry = retry_metadata("error", proc.returncode, proc.stderr)
            if retry:
                record.update(retry)
            write_json(run_dir / "record.json", record)
            shutil.rmtree(base, ignore_errors=True)
            return record
    start = time.monotonic()
    code, timed_out = _run_capped(argv, env, cwd, prompt, opts.timeout, run_dir / "events.jsonl",
                                  run_dir / "stderr.txt")
    record["elapsed_seconds"] = round(time.monotonic() - start, 3)
    record["exit_code"] = code
    parsed = parse_events((run_dir / "events.jsonl").read_text(encoding="utf-8", errors="replace"), known)
    output = out_file.read_text(encoding="utf-8") if out_file.is_file() else parsed["output"]
    record.update({k: parsed[k] for k in ("cost_usd", "input_tokens", "output_tokens", "model", "num_turns",
                                          "activated_skills")})
    if record["cost_usd"] is None and record["input_tokens"] is not None and opts.price_in is not None:
        record["cost_usd"] = round((record["input_tokens"] * opts.price_in
                                    + (record["output_tokens"] or 0) * (opts.price_out or 0)) / 1_000_000, 6)
        record["cost_source"] = "estimated_from_prices"
    elif record["cost_usd"] is not None:
        record["cost_source"] = "host_reported"
    if timed_out:
        record["status"] = "timeout"
    elif code != 0 or parsed["is_error"] or not output:
        record["status"] = "error"
    if record["status"] != "executed":
        record["execution_status"] = "ERROR"
        retry = retry_metadata(record["status"], code, (run_dir / "stderr.txt").read_text(
            encoding="utf-8", errors="replace"))
        if retry:
            record.update(retry)
    if output is not None:
        out_file.write_text(output, encoding="utf-8")
    write_json(run_dir / "record.json", record)
    shutil.rmtree(base, ignore_errors=True)
    return record


# --------------------------------------------------------------------------- grade


def routing_check(task: dict[str, Any], activated: list[str]) -> dict[str, Any]:
    expected = task.get("expected_primary_skill")
    forbidden = sorted(set(task.get("must_not_trigger", [])) & set(activated))
    if expected is None:
        ok = not activated
        reason = "no skill loaded" if ok else f"expected no skill, loaded {', '.join(activated)}"
    else:
        ok = expected in activated and not forbidden
        if expected not in activated:
            reason = f"{expected} not loaded" + (f"; loaded {', '.join(activated)}" if activated else "")
        elif forbidden:
            reason = f"forbidden skill(s) loaded: {', '.join(forbidden)}"
        else:
            reason = f"{expected} loaded"
    return {"status": "pass" if ok else "fail", "activated": activated, "reason": reason}


def output_check(task: dict[str, Any], text: str, graded: set[str], root: Path = ROOT) -> dict[str, Any]:
    missing = [lit for lit in task.get("preserve_literals", []) if lit not in text]
    result: dict[str, Any] = {"literals_missing": missing, "errors": [], "rubric": None}
    rubric_ok = True
    if task["skill"] in graded:
        with tempfile.TemporaryDirectory(prefix="cw-grade-") as tmp:
            argv = [sys.executable, "-B", str(root / "tooling" / "grade_output.py"), task["skill"], "-", "--json"]
            if task.get("canary"):
                canary_path = Path(tmp) / "canary.json"
                write_json(canary_path, task["canary"])
                argv += ["--canary-file", str(canary_path)]
            proc = subprocess.run(argv, input=text, capture_output=True, text=True, timeout=120,  # nosec B603
                                  check=False, cwd=root)
        try:
            graded_json = json.loads(proc.stdout)
        except ValueError:
            graded_json = {"status": "FAIL", "errors": [{"code": "GRADER_ERROR", "rule": "grade_output",
                                                         "message": proc.stderr[-500:]}]}
        rubric_ok = graded_json.get("status") == "PASS"
        result["rubric"] = "pass" if rubric_ok else "fail"
        result["errors"] = [f"{e.get('code')}:{e.get('rule')}" for e in graded_json.get("errors", [])]
    result["status"] = "pass" if rubric_ok and not missing else "fail"
    return result


def grade_run(run_dir: Path, root: Path = ROOT) -> dict[str, Any]:
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    plan = json.loads((run_dir / "plan.json").read_text(encoding="utf-8"))
    tasks = {t["id"]: t for t in plan["tasks"]}
    graded = graded_skills(root)
    results = []
    for record_path in sorted((run_dir / "runs").glob("*/record.json")):
        record = json.loads(record_path.read_text(encoding="utf-8"))
        task = tasks[record["task_id"]]
        checks: dict[str, Any] = {}
        executed = record["status"] == "executed"
        for check in task["checks"]:
            if not executed:
                checks[check] = {
                    "status": "not_run",
                    "reason": record.get("not_run_reason", record["status"]),
                    "execution_status": record.get(
                        "execution_status",
                        "NOT_RUN" if record["status"] == "not_run" else "ERROR",
                    ),
                }
            elif check == "routing":
                checks[check] = (routing_check(task, record["activated_skills"]) if record["condition"] == "plugin"
                                 else {"status": "n/a", "reason": "baseline has no skills to load"})
            elif check == "output":
                text = (record_path.parent / "output.md").read_text(encoding="utf-8")
                checks[check] = output_check(task, text, graded, root)
        results.append({"run_id": record["run_id"], "task_id": record["task_id"], "skill": record["skill"],
                        "role": task["role"], "condition": record["condition"], "repeat": record["repeat"],
                        "run_status": record["status"], "model": record.get("model"), "checks": checks})
    counts = {
        "completed": sum(r["run_status"] == "executed" for r in results),
        "errors": sum(r["run_status"] not in {"executed", "not_run"} for r in results),
        "not_run": sum(r["run_status"] == "not_run" for r in results),
    }
    grades = {"schema": GRADES_SCHEMA, "acceptance_version": manifest.get("acceptance_version", 1),
              "plan_sha256": manifest["plan_sha256"], "host": manifest["host"],
              "host_version": manifest.get("host_version"), "model_requested": manifest.get("model_requested"),
              "models_reported": manifest.get("models_reported", []), "payload_sha256": manifest.get("payload_sha256"),
              "candidate_sha256": manifest.get("candidate_sha256"),
              "benchmark_sha256": manifest.get("benchmark_sha256"),
              "rubric_sha256": manifest.get("rubric_sha256"),
              "host_config_sha256": manifest.get("host_config_sha256"),
              "frozen_hashes": frozen_hashes(manifest), "counts": counts,
              "completed_jobs": counts["completed"], "error_jobs": counts["errors"],
              "not_run_jobs": counts["not_run"], "results": results}
    write_json(run_dir / "grades.json", grades)
    return grades


# --------------------------------------------------------------------------- report


def wilson(passes: int, n: int, z: float = Z95) -> tuple[float, float] | None:
    if n <= 0:
        return None
    p = passes / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def sign_test(b: int, c: int) -> float:
    """Exact two-sided binomial test on discordant pairs (McNemar's exact test)."""
    n = b + c
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, k) for k in range(0, min(b, c) + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def _rate(rows: list[str], run_statuses: list[str] | None = None) -> dict[str, Any]:
    n = sum(1 for r in rows if r in ("pass", "fail"))
    passes = sum(1 for r in rows if r == "pass")
    ci = wilson(passes, n)
    run_statuses = run_statuses or rows
    return {"n": n, "pass": passes, "rate": round(passes / n, 4) if n else None,
            "ci95": [round(ci[0], 4), round(ci[1], 4)] if ci else None,
            "not_run": sum(1 for status in run_statuses if status == "not_run"),
            "errors": sum(1 for status in run_statuses if status not in {"executed", "not_run"})}


def build_report(grade_sets: list[dict[str, Any]]) -> dict[str, Any]:
    if not grade_sets:
        raise ValueError("no grades to report")
    plans = {g["plan_sha256"] for g in grade_sets}
    hosts = {(g["host"], g.get("host_version")) for g in grade_sets}
    models = sorted({m for g in grade_sets for m in g.get("models_reported", [])} |
                    {r["model"] for g in grade_sets for r in g["results"] if r.get("model")})
    rows = [r for g in grade_sets for r in g["results"]]
    conditions = sorted({r["condition"] for r in rows})
    warnings = []
    if len(plans) > 1:
        warnings.append("grades come from different plans; rates are not over the same tasks")
    if len(hosts) > 1:
        warnings.append("grades come from different hosts or host versions: " + "; ".join(f"{h} {v}" for h, v in sorted(hosts)))
    if len(models) > 1:
        warnings.append("more than one model answered: " + ", ".join(models))
    if len({g.get("payload_sha256") for g in grade_sets}) > 1:
        warnings.append("the plugin payload differs between runs")
    frozen = {json.dumps(frozen_hashes(g), sort_keys=True) for g in grade_sets}
    if len(frozen) > 1:
        warnings.append("grades carry different frozen acceptance hashes")

    per: dict[str, Any] = {}
    for cond in conditions:
        per[cond] = {}
        for check in ("routing", "output"):
            cells = {}
            for skill in sorted({r["skill"] for r in rows}):
                selected = [r for r in rows
                            if r["condition"] == cond and r["skill"] == skill and check in r["checks"]
                            and r["checks"][check]["status"] != "n/a"]
                if selected:
                    cells[skill] = _rate(
                        [r["checks"][check]["status"] for r in selected],
                        [r["run_status"] for r in selected],
                    )
            selected = [r for r in rows if r["condition"] == cond and check in r["checks"]
                        and r["checks"][check]["status"] != "n/a"]
            if selected:
                per[cond][check] = {
                    "overall": _rate(
                        [r["checks"][check]["status"] for r in selected],
                        [r["run_status"] for r in selected],
                    ),
                    "skills": cells,
                }

    paired = None
    if set(conditions) == set(CONDITIONS):
        by_key: dict[tuple[str, int], dict[str, str]] = {}
        for r in rows:
            status = r["checks"].get("output", {}).get("status")
            if status in ("pass", "fail"):
                by_key.setdefault((r["task_id"], r["repeat"]), {})[r["condition"]] = status
        pairs = [v for v in by_key.values() if len(v) == 2]
        b = sum(1 for v in pairs if v["plugin"] == "pass" and v["baseline"] == "fail")
        c = sum(1 for v in pairs if v["plugin"] == "fail" and v["baseline"] == "pass")
        paired = {"check": "output", "pairs": len(pairs), "plugin_only_pass": b, "baseline_only_pass": c,
                  "both_pass": sum(1 for v in pairs if v["plugin"] == v["baseline"] == "pass"),
                  "both_fail": sum(1 for v in pairs if v["plugin"] == v["baseline"] == "fail"),
                  "exact_p_two_sided": round(sign_test(b, c), 6),
                  "comparable": not warnings}
    run_errors = sum(1 for r in rows if r["run_status"] not in {"executed", "not_run"})
    run_not_run = sum(1 for r in rows if r["run_status"] == "not_run")
    return {"schema": REPORT_SCHEMA, "acceptance_version": 2,
            "plans": sorted(plans), "hosts": [f"{h} {v}".strip() for h, v in sorted(hosts)],
            "models": models, "conditions": conditions, "runs": len(rows),
            "run_errors": run_errors, "run_not_run": run_not_run,
            "error_jobs": run_errors, "not_run_jobs": run_not_run,
            "frozen_hashes": [frozen_hashes(g) for g in grade_sets],
            "warnings": warnings, "results": per, "paired": paired}


def _pct(cell: dict[str, Any]) -> str:
    if not cell["n"]:
        return "-"
    lo, hi = cell["ci95"]
    return f"{cell['pass']}/{cell['n']} ({cell['rate'] * 100:.0f}%, {lo * 100:.0f}-{hi * 100:.0f}%)"


def render_markdown(report: dict[str, Any]) -> str:
    lines = ["# Real-host eval scorecard", "",
             f"- Hosts: {', '.join(report['hosts'])}",
             f"- Models reported: {', '.join(report['models']) or 'none reported'}",
             f"- Plan: {', '.join(p[:12] for p in report['plans'])}",
             f"- Runs: {report['runs']} ({report['run_errors']} errors, {report['run_not_run']} not run; "
             "neither is in any rate)", ""]
    if report["warnings"]:
        lines += ["## Warnings", ""] + [f"- {w}" for w in report["warnings"]] + [""]
    for cond, checks in report["results"].items():
        for check, block in checks.items():
            lines += [f"## {check.title()} - {cond}", "",
                      f"Overall: {_pct(block['overall'])}. Cells are pass/n (rate, Wilson 95% interval).", "",
                      "| Skill | Pass/n (rate, 95% CI) | Not run | Errors |",
                      "| --- | --- | --- | --- |"]
            for skill, cell in block["skills"].items():
                lines.append(f"| `{skill}` | {_pct(cell)} | {cell['not_run']} | {cell['errors']} |")
            lines.append("")
    paired = report.get("paired")
    if paired:
        lines += ["## Plugin vs baseline (paired, output check)", "",
                  f"{paired['pairs']} pairs: plugin-only pass {paired['plugin_only_pass']}, baseline-only pass "
                  f"{paired['baseline_only_pass']}, both pass {paired['both_pass']}, both fail {paired['both_fail']}. "
                  f"Exact two-sided p on the discordant pairs: {paired['exact_p_two_sided']}.", ""]
        if not paired["comparable"]:
            lines += ["Not comparable as an A/B result: see the warnings above.", ""]
        lines += ["The output rubric checks the skill's contract, which the baseline was never shown, so a "
                  "plugin lead on this check is expected and is not by itself evidence of better answers. "
                  "Use the blind human review in docs/REAL-HOST-EVALS.md for that.", ""]
    lines += ["A pass means the transcript and the answer met a structural check. It does not mean the answer "
              "is correct.", ""]
    return "\n".join(lines)


# --------------------------------------------------------------------------- CLI


def _options(args: argparse.Namespace) -> RunOptions:
    conditions = CONDITIONS if args.condition == "both" else (args.condition,)
    opts = RunOptions(host=args.host, bin=args.bin or args.host, conditions=tuple(conditions), repeat=args.repeat,
                      max_tasks=args.max_tasks, timeout=args.timeout, max_usd_per_task=args.max_usd_per_task,
                      max_total_usd=args.max_total_usd, max_total_tokens=args.max_total_tokens,
                      max_turns=args.max_turns, model=args.model, price_in=args.price_in, price_out=args.price_out,
                      overhead_tokens=args.overhead_tokens, assume_turns=args.assume_turns,
                      assume_output_tokens=args.assume_output_tokens,
                      max_consecutive_errors=args.max_consecutive_errors, seed=args.seed)
    validate_options(opts)
    return opts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("plan", help="select tasks per skill from the repository's eval cases")
    p.add_argument("--out", type=Path, help="write the plan here (default: print it)")
    p.add_argument("--skill", action="append", default=[], help="limit to this skill (repeatable)")
    p.add_argument("--per-skill", type=int, default=3, help="positive tasks per skill (model cases first)")
    p.add_argument("--negatives-per-skill", type=int, default=1, help="routing cases where the skill must not load")
    p.add_argument("--lang", action="append", default=[], choices=["en", "pl"], help="keep only this language")
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--canary", action="store_true", help="plant a fresh canary instruction in each output task")

    r = sub.add_parser("run", help="run a plan on a host; a dry run unless --execute")
    r.add_argument("--plan", type=Path, required=True)
    r.add_argument("--host", choices=sorted(HOSTS), required=True)
    r.add_argument("--bin", help="host executable (default: the host name on PATH)")
    r.add_argument("--out", type=Path, help="new directory for transcripts and records (required with --execute)")
    r.add_argument("--condition", choices=["plugin", "baseline", "both"], default="plugin")
    r.add_argument("--repeat", type=int, default=1)
    r.add_argument("--max-tasks", type=int, default=10, help="hard cap on host runs (task x condition x repeat)")
    r.add_argument("--timeout", type=int, default=300, help="seconds per run before it is killed")
    r.add_argument("--max-turns", type=int, default=8, help="agent turns per run (claude)")
    r.add_argument("--max-usd-per-task", type=float, default=0.5, help="per-run dollar cap the host enforces (claude)")
    r.add_argument("--max-total-usd", type=float, help="stop before a run could take the total past this")
    r.add_argument("--max-total-tokens", type=int, help="stop once reported tokens reach this")
    r.add_argument("--model", help="pin the model; recommended for any comparison")
    r.add_argument("--price-in", type=float, help="USD per 1M input tokens, for estimates and codex cost")
    r.add_argument("--price-out", type=float, help="USD per 1M output tokens")
    r.add_argument("--overhead-tokens", type=int, help="assumed host context per turn, for the estimate")
    r.add_argument("--assume-turns", type=int, default=3, help="turns per run assumed by the estimate")
    r.add_argument("--assume-output-tokens", type=int, default=1500)
    r.add_argument("--max-consecutive-errors", type=int, default=2, help="stop after this many failed runs in a row")
    r.add_argument("--seed", type=int, default=1, help="order of runs and of conditions within a pair")
    r.add_argument("--execute", action="store_true", help="actually start the host; this spends money")

    g = sub.add_parser("grade", help="grade the runs in a run directory")
    g.add_argument("run_dir", type=Path)
    g.add_argument("--json", action="store_true", help="print the grades")

    s = sub.add_parser("report", help="scorecard over one or more graded run directories")
    s.add_argument("run_dirs", type=Path, nargs="+")
    s.add_argument("--format", choices=["md", "json"], default="md")
    s.add_argument("--out", type=Path)

    args = parser.parse_args(argv)
    try:
        if args.command == "plan":
            plan = build_plan(ROOT, skills=args.skill or None, per_skill=args.per_skill,
                              negatives_per_skill=args.negatives_per_skill, langs=args.lang or None,
                              seed=args.seed, canary=args.canary)
            if args.out:
                write_json(args.out, plan)
                print(f"{len(plan['tasks'])} task(s) for {len({t['skill'] for t in plan['tasks']})} skill(s) "
                      f"-> {args.out} (plan {plan['plan_sha256'][:12]})")
                for item in plan["skipped"]:
                    print(f"  skipped {item['skill']}: {item['reason']}")
            else:
                print(json.dumps(plan, indent=2, ensure_ascii=False))
            return 0
        if args.command == "run":
            plan = load_plan(args.plan)
            opts = _options(args)
            if not args.execute:
                dry_run(plan, opts, args.out)
                return 0
            if not args.out:
                parser.error("--execute needs --out, a new directory")
            summary = execute(plan, opts, args.out)
            print(f"{summary['completed_jobs']} completed, {summary['error_jobs']} failed, "
                  f"{summary['not_started_jobs']} not started; spent ~${summary['spent_usd']:.4f}"
                  + (f"; stopped: {summary['stop_reason']}" if summary["stop_reason"] else ""))
            return 0 if summary.get("execution_status") == "NOT_RUN" or (
                summary["error_jobs"] == 0 and not summary["stop_reason"]
            ) else 1
        if args.command == "grade":
            grades = grade_run(args.run_dir)
            if args.json:
                print(json.dumps(grades, indent=2, ensure_ascii=False))
            else:
                report = build_report([grades])
                print(render_markdown(report))
            return 0
        if args.command == "report":
            grade_sets = []
            for run_dir in args.run_dirs:
                path = run_dir / "grades.json"
                if not path.is_file():
                    parser.error(f"{run_dir} has no grades.json; run `grade {run_dir}` first")
                grade_sets.append(json.loads(path.read_text(encoding="utf-8")))
            report = build_report(grade_sets)
            text = render_markdown(report) if args.format == "md" else json.dumps(report, indent=2) + "\n"
            if args.out:
                args.out.write_text(text, encoding="utf-8")
            else:
                print(text)
            return 0
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
