#!/usr/bin/env python3
"""Scaffold a skill package that passes every gate on the day it is created.

Adding skill nineteen currently means copying an existing one and discovering
the contract by watching checks fail: the registry entry, the shared package
surface, the icon the adapter needs, the LICENSE every other skill carries, the
routing signals that make the skill reachable, coverage that actually runs.

This writes that skeleton instead, then tells the operator the two commands that
turn it into a registered skill. It deliberately does not touch the registry
itself — `sync_skill_registry.py` and `generate_adapters.py` own that, and a
second writer would be a second source of truth.
"""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")

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
3. Hand off in a typed envelope rather than prose.

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

Describe the structure this skill returns: the fields, what each one means, and
which of them a consumer may rely on.

State explicitly what the output does **not** assert. A consumer that mistakes a
heuristic for a verdict is the failure mode worth preventing here.
'''

CHANGELOG = '''# Changelog

All notable changes to this skill.

Format follows [Keep a Changelog](https://keepachangelog.com/).

## [0.1.0] - {today}

### Added

- Initial scaffold.
'''

RUN_EVALS = '''#!/usr/bin/env python3
"""Deterministic eval cases for {skill_id}.

Coverage lives here rather than in tests/ for skills whose behaviour is easier to
state as cases than as unit tests. Either is fine; shipping neither is not, and
tooling/tests/test_package_layout_consistency.py enforces that.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def cases() -> list[dict]:
    path = ROOT / "evals" / "cases.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else []


def run_case(case: dict) -> tuple[bool, str]:
    # Replace with the real assertion. Returning True unconditionally would make
    # this harness a decoration, so it fails until something is asserted.
    return False, "no assertion implemented yet"


def main() -> int:
    if len(sys.argv) > 1:
        print("usage: run_evals.py\\n  Takes no arguments.", file=sys.stderr)
        return 2
    rows = cases()
    if not rows:
        print("FAIL: no eval cases in evals/cases.json")
        return 1
    failures = [c.get("id") for c in rows if not run_case(c)[0]]
    print(json.dumps({{"total": len(rows), "passed": len(rows) - len(failures),
                      "failures": failures,
                      "status": "PASS" if not failures else "FAIL"}}, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
'''

CASES = '''[
  {
    "id": "first-case",
    "prompt": "A request this skill should handle",
    "expect": "Describe the observable property the case asserts"
  }
]
'''


def title_from(skill_id: str) -> str:
    special = {"ai": "AI", "seo": "SEO", "geo": "GEO", "aeo": "AEO", "qa": "QA"}
    return " ".join(special.get(w, w.capitalize()) for w in skill_id.split("-"))


def create(skill_id: str, description: str, force: bool) -> Path:
    if not SKILL_ID.fullmatch(skill_id):
        raise SystemExit(f"invalid skill id {skill_id!r}: use lowercase words joined by hyphens")
    if len(description.strip()) < 80:
        raise SystemExit(
            "description must be at least 80 characters: it is what routes the skill, "
            "and validate_skill.py rejects anything shorter"
        )
    if len(description.strip()) > 1024:
        raise SystemExit("description exceeds the 1024-character Codex limit")

    target = ROOT / "skills" / skill_id
    if target.exists() and not force:
        raise SystemExit(f"{target.relative_to(ROOT)} already exists; pass --force to overwrite")
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
    (target / "evals" / "cases.json").write_text(CASES, encoding="utf-8")
    harness = target / "scripts" / "run_evals.py"
    harness.write_text(RUN_EVALS.format(skill_id=skill_id), encoding="utf-8")
    harness.chmod(0o755)

    # Every other skill carries these two; copying beats generating a licence.
    shutil.copy2(ROOT / "skills" / "ai-council" / "LICENSE", target / "LICENSE")
    shutil.copy2(ROOT / "skills" / "ai-council" / "assets" / "icon.svg", target / "assets" / "icon.svg")
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("skill_id", help="lowercase-with-hyphens")
    parser.add_argument("--description", required=True,
                        help="80-1024 characters; this is what routes the skill")
    parser.add_argument("--force", action="store_true", help="overwrite an existing directory")
    args = parser.parse_args(argv)

    target = create(args.skill_id, args.description, args.force)
    print(f"OK: scaffolded {target.relative_to(ROOT)}")
    print()
    print("It is not a registered skill yet. Next:")
    print(f"  1. Write the real SKILL.md, then add routing signals for {args.skill_id!r}")
    print("     to registry/skills.json (owns, does_not_own, trigger_examples,")
    print("     negative_trigger_examples, routing_signals).")
    print("  2. python3 tooling/generate_adapters.py")
    print("  3. python3 tooling/context_budget.py --update")
    print("  4. python3 tooling/validate_local.py --output .validation --timeout 900")
    print()
    print("The eval harness fails until you implement run_case(); that is deliberate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
