#!/usr/bin/env python3
"""Scaffold and register a skill package that passes every gate on the day it is created.

Adding a skill used to mean copying an existing one and discovering the contract
by watching checks fail: the registry entry, the shared package surface, the
icon the adapter needs, the LICENSE every other skill carries, the routing
signals and cases that make the skill reachable, coverage that actually runs,
and the recorded baselines.

This writes the package, then registers it: a registry entry, a README catalog
row, placeholder routing cases, and baseline rows for this skill alone (other
skills' baselines are never re-recorded here, so their regressions cannot be
accepted by accident). Generated files are then rebuilt by the repository's own
generators. `uv run python tooling/check_all.py --fast` passes straight after.

Everything it writes is a placeholder that is honest about being one: the
routing cases say so in their `reason`, and the eval harness pins a small
output-contract validator rather than nothing. Replace both with the real thing.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
HOSTS = ["cursor", "claude-code", "openai-codex", "chatgpt"]

SKILL_MD = '''---
name: {skill_id}
description: >-
  {description}
---

# {title}

State what this skill owns in one paragraph, then what it does not own and which
skill takes those cases instead. Both halves are load-bearing: the second is what
keeps routing honest.

## When to use this

Describe the request shapes that belong here. Be concrete enough that a reader
can tell a match from a near-miss.

## When not to use this

Name the neighbouring skills and the cases that belong to them.

## Workflow

1. Establish what is actually known before deciding anything.
2. Do the work the skill owns.
3. Return the result in the shape `references/output-contract.md` defines.

## Boundaries

- Operate read-only unless the user asked for a side effect.
- Do not claim a check proves more than it tested.
- Report what was not verified as not verified.

## References

Keep this file small. Depth belongs in `references/`, which a host reads only
when the skill opens it — see `docs/generated-context-budget.md`.

| File | Purpose |
| --- | --- |
| `references/output-contract.md` | What this skill returns, and in what shape |
'''

OUTPUT_CONTRACT = '''# Output contract

A result is an object with these fields. `scripts/output_contract.py` enforces
them, and `evals/cases.json` pins each rule; change all three together.

| Field | Type | Meaning |
| --- | --- | --- |
| `summary` | non-empty string | What was done, in one or two sentences |
| `status` | `complete`, `partial` or `blocked` | How far the work got |
| `not_verified` | list of strings | What was not checked; empty only when nothing was left |

A `complete` result with a non-empty `not_verified` is contradictory and is
rejected.

The output does **not** assert anything beyond what was checked. A consumer that
mistakes a heuristic for a verdict is the failure mode worth preventing here.
'''

CHANGELOG = '''# Changelog

All notable changes to this skill.

Format follows [Keep a Changelog](https://keepachangelog.com/).

## [0.1.0] - {today}

### Added

- Initial scaffold.
'''

KERNEL = '''"""Check a {skill_id} result against references/output-contract.md.

Replace these rules with the skill's real contract. Every rule is pinned by a
case in evals/cases.json: tooling/eval_strength.py disables one `if` at a time
and expects scripts/run_evals.py to fail, so a rule nothing pins is reported.
"""

from __future__ import annotations

STATUSES = ("complete", "partial", "blocked")


def validate(result: object) -> list[str]:
    if not isinstance(result, dict):
        return ["result: must be an object"]
    errors = []
    summary = result.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        errors.append("summary: required non-empty string")
    if result.get("status") not in STATUSES:
        errors.append("status: must be complete, partial or blocked")
    not_verified = result.get("not_verified")
    if not isinstance(not_verified, list):
        errors.append("not_verified: required list")
    elif result.get("status") == "complete" and not_verified:
        errors.append("status: complete contradicts a non-empty not_verified")
    return errors
'''

RUN_EVALS = '''#!/usr/bin/env python3
"""Deterministic eval cases for {skill_id}.

Each case in evals/cases.json gives an input and the exact errors the
output-contract validator must return. Pin the exact list, not just "invalid":
a case that only asserts failure holds no single rule.

The rules live in scripts/output_contract.py, not here: eval_strength.py
measures a harness by disabling each `if` guard in the modules it imports, and
logic written inside this file is never measured.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from output_contract import validate  # noqa: E402


def cases() -> list[dict]:
    path = ROOT / "evals" / "cases.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else []


def run_case(case: dict) -> tuple[bool, str]:
    actual = validate(case["input"])
    expected = case["expected_errors"]
    return actual == expected, f"expected {{expected}}, got {{actual}}"


def main() -> int:
    args = sys.argv[1:]
    usage = "usage: run_evals.py [-h]\\n  Runs evals/cases.json; takes no other arguments."
    if args in (["-h"], ["--help"]):
        print(usage)
        return 0
    if args:
        print(f"{{usage}}\\nrun_evals.py: error: unrecognized arguments: {{' '.join(args)}}",
              file=sys.stderr)
        return 2
    rows = cases()
    if not rows:
        print("FAIL: no eval cases in evals/cases.json")
        return 1
    failures = []
    for case in rows:
        ok, detail = run_case(case)
        if not ok:
            failures.append({{"id": case.get("id"), "detail": detail}})
    print(json.dumps({{"total": len(rows), "passed": len(rows) - len(failures),
                      "failures": failures,
                      "status": "PASS" if not failures else "FAIL"}}, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
'''

CASES = [
    {"id": "valid-complete", "input": {"summary": "Checked the request.", "status": "complete",
                                       "not_verified": []},
     "expected_errors": []},
    {"id": "not-an-object", "input": ["summary"], "expected_errors": ["result: must be an object"]},
    {"id": "missing-summary", "input": {"status": "partial", "not_verified": ["live data"]},
     "expected_errors": ["summary: required non-empty string"]},
    {"id": "unknown-status", "input": {"summary": "Done.", "status": "done", "not_verified": []},
     "expected_errors": ["status: must be complete, partial or blocked"]},
    {"id": "missing-not-verified", "input": {"summary": "Done.", "status": "partial"},
     "expected_errors": ["not_verified: required list"]},
    {"id": "complete-but-unverified", "input": {"summary": "Done.", "status": "complete",
                                                "not_verified": ["pricing page"]},
     "expected_errors": ["status: complete contradicts a non-empty not_verified"]},
]

# The one machine-readable statement of the contract above, checked against the
# validator, references/output-contract.md and evals/cases.json by
# tooling/skill_contracts.py.
CONTRACT = {
    "schema": "cometweb.skill-contract/v1",
    "docs": ["references/output-contract.md"],
    "scripts": {
        "scripts/output_contract.py": {"input": "json", "role": "validator", "enums": {"STATUSES": "status"}},
        "scripts/run_evals.py": {"input": "none", "role": "eval-harness"},
    },
    "fields": {"summary": {}, "status": {"enum": ["complete", "partial", "blocked"]}, "not_verified": {}},
    "outputs": {},
    "internal": [],
    "doc_terms": [],
    "evals": [{"path": "evals/cases.json", "cases": "", "input": "input",
               "errors": "expected_errors", "pass": ["pass"]}],
}

PLACEHOLDER = "Scaffold placeholder from tooling/new_skill.py; replace with a real case"

# Package files whose content is a working placeholder. next_steps() names each
# one, and tooling/tests/test_new_skill_scaffold.py keeps this list, the files
# create() writes and the README walkthrough in step.
PLACEHOLDER_FILES = (
    ("SKILL.md", "the real front door; keep it short, depth goes in references/"),
    ("references/output-contract.md", "what the skill returns, and in what shape"),
    ("scripts/output_contract.py", "the deterministic rules; eval_strength.py mutates this module"),
    ("evals/cases.json", "one case per rule, pinning the exact `expected_errors` list"),
    ("references/contract.json", "every payload field and enum, bound to the validator's constants"),
)


def next_steps(skill_id: str, registered: bool = True) -> str:
    """What is still placeholder, in the order to replace it."""
    head = ("Every fast gate passes now; the content is still placeholder. Replace, in order:"
            if registered else "Not registered (--no-register): registry, routing cases and baselines "
            "are unchanged. Replace, in order:")
    lines = [head]
    for index, (relative, what) in enumerate(PLACEHOLDER_FILES, 1):
        lines.append(f"  {index}. skills/{skill_id}/{relative}: {what}")
    step = len(PLACEHOLDER_FILES) + 1
    lines += [
        f"  {step}. The '{skill_id}-scaffold-*' cases in evals/routing/suite.json and the",
        "     routing_signals, owns and trigger examples in registry/skills.json",
        "     (a changed description goes into the registry entry too).",
        f"  {step + 1}. Bump the plugin version (VERSION, pyproject.toml, the three plugin.json),",
        "     then: uv run python tooling/plugin_release.py --record",
        f"  {step + 2}. uv run python tooling/check_all.py --fix --fast   # regenerate and check",
        "     uv run python tooling/check_all.py                # every gate, as CI runs them",
    ]
    return "\n".join(lines)


def title_from(skill_id: str) -> str:
    special = {"ai": "AI", "seo": "SEO", "geo": "GEO", "aeo": "AEO", "qa": "QA"}
    return " ".join(special.get(w, w.capitalize()) for w in skill_id.split("-"))


def validate_input(skill_id: str, description: str) -> None:
    if not SKILL_ID.fullmatch(skill_id):
        raise SystemExit(f"invalid skill id {skill_id!r}: use lowercase words joined by hyphens")
    if len(description.strip()) < 80:
        raise SystemExit(
            "description must be at least 80 characters: it is what routes the skill, "
            "and validate_skill.py rejects anything shorter"
        )
    if len(description.strip()) > 1024:
        raise SystemExit("description exceeds the 1024-character Codex limit")


def create(skill_id: str, description: str, force: bool, root: Path = ROOT) -> Path:
    """Write the package only. register() makes it part of the catalog."""
    validate_input(skill_id, description)
    target = root / "skills" / skill_id
    if target.exists() and not force:
        raise SystemExit(f"{target.relative_to(root)} already exists; pass --force to overwrite")
    import datetime as dt
    today = dt.datetime.now(dt.timezone.utc).date().isoformat()

    for sub in ("references", "scripts", "evals", "assets"):
        (target / sub).mkdir(parents=True, exist_ok=True)

    (target / "SKILL.md").write_text(
        SKILL_MD.format(skill_id=skill_id, description=description.strip(), title=title_from(skill_id)),
        encoding="utf-8")
    (target / "VERSION").write_text("0.1.0\n", encoding="utf-8")
    (target / "CHANGELOG.md").write_text(CHANGELOG.format(today=today), encoding="utf-8")
    (target / "references" / "output-contract.md").write_text(OUTPUT_CONTRACT, encoding="utf-8")
    (target / "evals" / "cases.json").write_text(json.dumps(CASES, indent=2) + "\n", encoding="utf-8")
    (target / "references" / "contract.json").write_text(json.dumps(CONTRACT, indent=2) + "\n", encoding="utf-8")
    (target / "scripts" / "output_contract.py").write_text(KERNEL.format(skill_id=skill_id), encoding="utf-8")
    harness = target / "scripts" / "run_evals.py"
    harness.write_text(RUN_EVALS.format(skill_id=skill_id), encoding="utf-8")
    harness.chmod(0o755)

    # Every other skill carries these two; copying beats generating a licence.
    # They come from this checkout even when the skill is written elsewhere.
    shutil.copy2(ROOT / "skills" / "ai-council" / "LICENSE", target / "LICENSE")
    shutil.copy2(ROOT / "skills" / "ai-council" / "assets" / "icon.svg", target / "assets" / "icon.svg")
    return target


def routing(skill_id: str) -> dict:
    """Placeholder routing: reachable when invoked by name, and only then."""
    title = title_from(skill_id)
    name = r"[- ]".join(re.escape(word) for word in skill_id.split("-"))
    # Polish imperatives too: the routing suite floors Polish coverage per skill.
    signal = rf"\b(?:use|run|invoke|uzyj|uruchom|odpal) (?:the )?{name}\b"
    positives = [
        f"Use {skill_id} on the attached notes.",
        f"Run the {title} workflow for this request.",
        f"Please invoke {skill_id} and list what it could not check.",
    ]
    negatives = [
        f"Rename the {skill_id} folder on my desktop.",
        f"What does the name {title} mean?",
    ]
    pl_positives = [
        f"Użyj {skill_id} do tych notatek.",
        f"Uruchom {skill_id} dla tego zgłoszenia.",
        f"Odpal {skill_id} i wypisz, czego nie dało się sprawdzić.",
    ]
    # A Polish boundary case: another skill wins and this one must not trigger.
    pl_boundary = (f"Zroastuj to repozytorium bez litości, łącznie z katalogiem {skill_id}.", "repo-roaster")
    # The registry examples are routed by their own test and may not repeat a
    # suite prompt, so they get their own phrasing.
    return {"signal": signal, "positives": positives, "negatives": negatives,
            "pl_positives": pl_positives, "pl_boundary": pl_boundary,
            "trigger_example": f"Use the {title} skill for this.",
            "negative_trigger_example": f"Delete the {skill_id} branch."}


def registry_entry(skill_id: str, description: str, plan: dict) -> dict:
    return {
        "id": skill_id,
        "version": "0.1.0",
        "lifecycle": "active",
        "visibility": "public_canonical",
        "tier": "domain",
        "alias_of": None,
        "description": " ".join(description.split()),
        "explicit_only": False,
        "owns": [f"{title_from(skill_id)} requests"],
        "does_not_own": ["work a neighbouring skill already owns"],
        "trigger_examples": [plan["trigger_example"]],
        "negative_trigger_examples": [plan["negative_trigger_example"]],
        "inputs": ["user goal"],
        "outputs": ["skill-specific artifact"],
        "dependencies": [],
        "compatible_hosts": list(HOSTS),
        "execution_capabilities": ["standard"],
        "eval_suite": None,
        "routing_signals": [[10, plan["signal"]]],
    }


def write_json(path: Path, data: object, **options) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, **options) + "\n", encoding="utf-8")


def load_tool(root: Path, name: str):
    """The target checkout's own tool, so its ROOT is that checkout."""
    spec = importlib.util.spec_from_file_location(f"new_skill_{name}", root / "tooling" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def record_baselines(skill_id: str, root: Path) -> None:
    """Add this skill's rows to the context and eval-strength baselines, nothing else."""
    budget = load_tool(root, "context_budget")
    baseline = json.loads(budget.BASELINE.read_text(encoding="utf-8"))
    rows = [r for r in baseline["skills"] if r["id"] != skill_id]
    rows.append(budget.measure_skill(root / "skills" / skill_id))
    rows.sort(key=lambda r: r["id"])
    front = [r["front_door_tokens_estimated"] for r in rows]
    import statistics
    baseline.update(skills=rows, skill_count=len(rows), total_front_door_tokens_estimated=sum(front),
                    median_front_door_tokens_estimated=int(statistics.median(front)),
                    max_front_door_tokens_estimated=max(front))
    write_json(budget.BASELINE, baseline)
    table = root / "docs" / "generated-context-budget.md"
    table.write_text(budget.render_table(budget.measure()), encoding="utf-8")

    strength = load_tool(root, "eval_strength")
    if not (root / "skills" / skill_id / strength.HARNESS).is_file():
        return
    measured = strength.measure(root / "skills" / skill_id)
    recorded = json.loads(strength.BASELINE.read_text(encoding="utf-8"))
    rows = [r for r in recorded["skills"] if r["id"] != skill_id]
    rows.append({k: v for k, v in measured.items() if k not in {"unheld", "modules"}})
    rows.sort(key=lambda r: r["id"])
    recorded["skills"] = rows
    strength.BASELINE.write_text(json.dumps(recorded, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (root / "docs" / "generated-eval-strength.md").write_text(strength.table(rows), encoding="utf-8")


def register(skill_id: str, description: str, group: str | None, summary: str, root: Path = ROOT) -> None:
    registry_path = root / "registry" / "skills.json"
    catalog_path = root / "registry" / "readme-catalog.json"
    suite_path = root / "evals" / "routing" / "suite.json"
    for path in (registry_path, catalog_path, suite_path):
        if not path.is_file():
            raise SystemExit(f"cannot register: {path.relative_to(root)} is missing (use --no-register)")
    plan = routing(skill_id)

    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    skills = [s for s in registry["skills"] if s["id"] != skill_id]
    skills.append(registry_entry(skill_id, description, plan))
    registry["skills"] = sorted(skills, key=lambda s: s["id"])
    write_json(registry_path, registry)

    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    titles = [g["title"] for g in catalog["groups"]]
    chosen = group or titles[-1]
    if chosen not in titles:
        raise SystemExit(f"unknown README group {chosen!r}; choose one of: {', '.join(titles)}")
    for entry in catalog["groups"]:
        entry["skills"] = [row for row in entry["skills"] if row["id"] != skill_id]
        if entry["title"] == chosen:
            entry["skills"].append({"id": skill_id, "summary": summary})
    write_json(catalog_path, catalog)

    suite = json.loads(suite_path.read_text(encoding="utf-8"))
    prefix = f"{skill_id}-scaffold-"
    cases = [c for c in suite["cases"] if not c["id"].startswith(prefix)]
    for index, prompt in enumerate(plan["positives"], 1):
        cases.append({"id": f"{prefix}positive-{index}", "prompt": prompt, "expected_primary_skill": skill_id,
                      "allowed_secondary_skills": [], "must_not_trigger": [], "reason": PLACEHOLDER})
    for index, prompt in enumerate(plan["negatives"], 1):
        cases.append({"id": f"{prefix}negative-{index}", "prompt": prompt, "expected_primary_skill": None,
                      "allowed_secondary_skills": [], "must_not_trigger": [skill_id],
                      "reason": f"{PLACEHOLDER}: naming the skill is not invoking it"})
    for index, prompt in enumerate(plan["pl_positives"], 1):
        cases.append({"id": f"{prefix}pl-positive-{index}", "prompt": prompt, "lang": "pl",
                      "expected_primary_skill": skill_id, "allowed_secondary_skills": [],
                      "must_not_trigger": [], "reason": PLACEHOLDER})
    prompt, winner = plan["pl_boundary"]
    if any(s["id"] == winner for s in registry["skills"]):
        cases.append({"id": f"{prefix}pl-boundary-1", "prompt": prompt, "lang": "pl",
                      "expected_primary_skill": winner, "allowed_secondary_skills": [],
                      "must_not_trigger": [skill_id],
                      "reason": f"{PLACEHOLDER}: naming the skill is not invoking it"})
    suite["cases"] = cases
    write_json(suite_path, suite)

    generator = root / "tooling" / "generate_adapters.py"
    proc = subprocess.run([sys.executable, "-B", str(generator)], cwd=root, capture_output=True, text=True,
                          check=False, timeout=300)
    if proc.returncode != 0:
        raise SystemExit(f"generate_adapters.py failed:\n{proc.stdout}{proc.stderr}")
    record_baselines(skill_id, root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("skill_id", help="lowercase-with-hyphens")
    parser.add_argument("--description", required=True,
                        help="80-1024 characters; this is what routes the skill")
    parser.add_argument("--summary", help="one line for the README catalog (default: the skill title)")
    parser.add_argument("--group", help="README catalog group (default: the last one)")
    parser.add_argument("--no-register", action="store_true",
                        help="write the package only; leave registry, routing and baselines alone")
    parser.add_argument("--force", action="store_true", help="overwrite an existing directory")
    parser.add_argument("--root", type=Path, default=ROOT,
                        help="repository root to write skills/<id> into (default: this checkout)")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    target = create(args.skill_id, args.description, args.force, root)
    print(f"OK: scaffolded {target.relative_to(root)}")
    for path in sorted(p for p in target.rglob("*") if p.is_file()):
        print(f"  {path.relative_to(root).as_posix()}")
    if not args.no_register:
        register(args.skill_id, args.description, args.group,
                 args.summary or f"{title_from(args.skill_id)}.", root)
        print(f"OK: registered {args.skill_id} (registry, README catalog, routing suite, baselines, adapters)")
    print()
    print(next_steps(args.skill_id, registered=not args.no_register))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
