#!/usr/bin/env python3
"""Measure discovery metadata, activated instructions and the optional reference pool.

Token counts are static estimates at four UTF-8 bytes/token. Host transcripts
are required for actual prompt tokens, cache accounting and runtime cost.
Legacy front_door fields mean activated SKILL.md size, never discovery cost.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path
from typing import Any

from compatibility import parse_frontmatter

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "registry" / "context-baseline.json"
HOST_BUDGET = ROOT / "registry" / "context-host-budget.json"
BYTES_PER_TOKEN = 4


def _text_bytes(path: Path) -> int:
    return len(path.read_bytes())


def measure_skill(directory: Path) -> dict[str, Any]:
    skill_md = directory / "SKILL.md"
    front_door = _text_bytes(skill_md) if skill_md.is_file() else 0
    references = sorted(p for p in (directory / "references").rglob("*") if p.is_file() and p.suffix in {".md", ".json", ".yaml", ".yml", ".txt", ".csv"}) if (directory / "references").is_dir() else []
    depth = sum(_text_bytes(p) for p in references)
    metadata = parse_frontmatter(skill_md) if skill_md.is_file() else {}
    discovery = len((metadata.get("name", "") + "\n" + metadata.get("description", "")).encode("utf-8"))
    return {
        "id": directory.name,
        "discovery_metadata_bytes": discovery,
        "discovery_metadata_tokens_estimated": discovery // BYTES_PER_TOKEN,
        "activation_instruction_tokens_estimated": front_door // BYTES_PER_TOKEN,
        "reference_pool_tokens_estimated": depth // BYTES_PER_TOKEN,
        "front_door_bytes": front_door,
        "front_door_tokens_estimated": front_door // BYTES_PER_TOKEN,
        "depth_bytes": depth,
        "depth_tokens_estimated": depth // BYTES_PER_TOKEN,
        "reference_files": len(references),
        # Share stored in optional references rather than activated instructions.
        "deferred_ratio": round(depth / (front_door + depth), 4) if (front_door + depth) else 0.0,
    }


def measure(root: Path = ROOT) -> dict[str, Any]:
    skills = sorted(p for p in (root / "skills").iterdir() if p.is_dir() and (p / "SKILL.md").is_file())
    rows = [measure_skill(p) for p in skills]
    front = [r["front_door_tokens_estimated"] for r in rows]
    return {
        "schema": "cometweb.context-budget/v1",
        "unit": "bytes; token counts are estimates at %d bytes/token" % BYTES_PER_TOKEN,
        "skill_count": len(rows),
        "total_discovery_metadata_tokens_estimated": sum(r["discovery_metadata_tokens_estimated"] for r in rows),
        "observed_prompt_tokens": None,
        "actual_reference_tokens": None,
        "cache_read_tokens": None,
        "runtime_cost": None,
        "total_front_door_tokens_estimated": sum(front),
        "median_front_door_tokens_estimated": int(statistics.median(front)) if front else 0,
        "max_front_door_tokens_estimated": max(front) if front else 0,
        "skills": rows,
    }


def load_baseline() -> dict[str, Any] | None:
    if not BASELINE.is_file():
        return None
    return json.loads(BASELINE.read_text(encoding="utf-8"))


def compare(current: dict[str, Any], baseline: dict[str, Any], tolerance: float) -> list[str]:
    """Report unexplained growth against the recorded baseline.

    Growth is always a decision someone made. Absolute host ceilings are checked
    separately via enforce_host_budgets().
    """
    was = {r["id"]: r for r in baseline.get("skills", [])}
    problems: list[str] = []
    for row in current["skills"]:
        previous = was.get(row["id"])
        if previous is None:
            problems.append(f"{row['id']}: new skill, not in the baseline; run --update to record it")
            continue
        before = previous["front_door_bytes"]
        after = row["front_door_bytes"]
        if before and after > before * (1 + tolerance):
            grew = (after / before - 1) * 100
            problems.append(
                f"{row['id']}: front door grew {grew:.1f}% "
                f"({before} -> {after} bytes, ~{previous['front_door_tokens_estimated']} -> "
                f"~{row['front_door_tokens_estimated']} tokens). Move detail into references/ "
                f"or run --update to accept the new cost."
            )
    for missing in sorted(set(was) - {r["id"] for r in current["skills"]}):
        problems.append(f"{missing}: in the baseline but no longer on disk; run --update")
    return problems


def load_host_budgets() -> dict[str, Any] | None:
    if not HOST_BUDGET.is_file():
        return None
    data = json.loads(HOST_BUDGET.read_text(encoding="utf-8"))
    if data.get("schema") != "cometweb.context-host-budget/v1":
        raise ValueError("unsupported context-host-budget schema")
    return data


def enforce_host_budgets(report: dict[str, Any], policy: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    hosts = policy.get("hosts") or {}
    for host_name, host in hosts.items():
        limit = host.get("frontdoor_budget_bytes")
        if limit is None:
            continue
        if type(limit) is not int or limit < 1:
            problems.append(f"{host_name}: invalid frontdoor_budget_bytes")
            continue
        for row in report["skills"]:
            if row["front_door_bytes"] > limit:
                problems.append(
                    f"{row['id']}@{host_name}: front door "
                    f"{row['front_door_bytes']} > host limit {limit}"
                )
    return problems


def render_table(report: dict[str, Any]) -> str:
    lines = [
        "# Generated context budget",
        "",
        "<!-- generated by tooling/context_budget.py — do not hand-edit -->",
        "",
        "Discovery loads name + description; activation loads the selected SKILL.md;",
        "references load on demand. `Front door` is the legacy activation-size field.",
        "The reference pool includes nested text resources, not actual loaded context.",
        "Observed prompt/reference tokens, cache reads and runtime cost are not assessed.",
        "",
        "Token counts are estimates at %d bytes/token, not a tokenizer result." % BYTES_PER_TOKEN,
        "",
        "| Skill | Front door | ~tokens | Depth | ~tokens | Refs | Deferred |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in sorted(report["skills"], key=lambda r: -r["front_door_bytes"]):
        lines.append(
            f"| `{row['id']}` | {row['front_door_bytes']:,} B | {row['front_door_tokens_estimated']:,} "
            f"| {row['depth_bytes']:,} B | {row['depth_tokens_estimated']:,} | {row['reference_files']} "
            f"| {row['deferred_ratio']:.2f} |"
        )
    lines += [
        "",
        f"**{report['skill_count']} skills.** Discovery metadata totals roughly "
        f"{report['total_discovery_metadata_tokens_estimated']:,} tokens. Activating all skills "
        f"would load ~{report['total_front_door_tokens_estimated']:,} instruction tokens; "
        f"the median activation is ~{report['median_front_door_tokens_estimated']:,}, "
        f"and the largest ~{report['max_front_door_tokens_estimated']:,}.",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="fail if a front door grew beyond tolerance")
    parser.add_argument("--update", action="store_true", help="record the current measurement as the baseline")
    parser.add_argument("--table", type=Path, help="write the generated markdown table to this path")
    parser.add_argument("--verify-table", type=Path, metavar="PATH",
                        help="with --check: also fail when the table at PATH is not what --table would write")
    parser.add_argument("--tolerance", type=float, default=0.10,
                        help="growth allowed before --check fails (default 0.10 = 10%%)")
    parser.add_argument("--json", action="store_true", help="print the raw measurement")
    args = parser.parse_args(argv)

    report = measure()

    if args.table:
        args.table.parent.mkdir(parents=True, exist_ok=True)
        args.table.write_text(render_table(report), encoding="utf-8")

    if args.update:
        BASELINE.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"OK: context baseline recorded for {report['skill_count']} skills "
              f"(~{report['total_front_door_tokens_estimated']:,} front-door tokens)")
        return 0

    if args.check:
        baseline = load_baseline()
        if baseline is None:
            print("FAIL: no context baseline; run tooling/context_budget.py --update", file=sys.stderr)
            return 1
        problems = compare(report, baseline, args.tolerance)
        try:
            host_policy = load_host_budgets()
        except ValueError as exc:
            print(f"FAIL: {exc}", file=sys.stderr)
            return 1
        if host_policy:
            problems.extend(enforce_host_budgets(report, host_policy))
        if args.verify_table is not None:
            on_disk = args.verify_table.read_text(encoding="utf-8") if args.verify_table.is_file() else None
            if on_disk != render_table(report):
                problems.append(f"{args.verify_table} is stale; regenerate it with "
                                "`uv run python tooling/check_all.py --fix --fast`")
        if problems:
            for problem in problems:
                print(f"FAIL: {problem}", file=sys.stderr)
            return 1
        print(f"OK: context budget ({report['skill_count']} skills, "
              f"~{report['total_front_door_tokens_estimated']:,} front-door tokens)")
        return 0

    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else render_table(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
