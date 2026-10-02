#!/usr/bin/env python3
"""How much of the skill catalog the routing suite actually exercises.

A routing suite can pass while saying almost nothing about a skill: one positive
case shows the router *can* reach it, not that it resists the prompts next door.
This measures, per active skill, how many hand-written cases expect it to win
and how many forbid it, and rejects suite defects that make a green run hollow:

- duplicate case IDs, or two cases whose prompts normalize to the same text;
- a case that names a skill the registry does not know (a typo in
  `must_not_trigger` silently checks nothing, forever);
- a case that expects a skill and forbids it in the same breath;
- a prompt copied verbatim from a registry trigger/negative example. Those are
  already pinned by tooling/tests/test_registry_self_consistency.py, so a copy
  adds a count without adding evidence.

`evals/routing/known-gaps.json` pins prompts the deterministic router is known
to misroute today. They are not counted as coverage; each must keep reproducing
its recorded misroute, so a fix shows up as a failure asking for promotion into
suite.json instead of disappearing quietly.

Optionally (`--trigger-evals`) it replays skill-local `evals/trigger-evals.json`
files through the same router. That is a deterministic-proxy discovery estimate:
those files were written for model-based triggering. Skills listed in
`TRIGGER_EVAL_FLOORS` are held to it by `--check` anyway, so routing-signal
work that lifted their proxy recall cannot quietly erode.

Read-only, offline, standard library only. Not a model evaluation.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "evals" / "routing" / "suite.json"
GAPS = ROOT / "evals" / "routing" / "known-gaps.json"
REGISTRY = ROOT / "registry" / "skills.json"
POLICY = ROOT / "registry" / "routing-policy.json"

# Floors per active skill. Three positives let a skill be reached from more than
# one phrasing; two negatives mean at least two neighbours are told "not this one".
MIN_POSITIVE = 3
MIN_NEGATIVE = 2
NEAR_DUPLICATE = 0.8
GAPS_SCHEMA = "cometweb.routing-known-gaps/v1"
# Deterministic-proxy floors on skill-local trigger evals, set just under the
# measured result: recall (should-trigger cases routed to the skill), rejected
# (should-not-trigger cases kept away from it) and near_miss (near-miss cases
# routed to the skill they name). Raise them when routing improves.
TRIGGER_EVAL_FLOORS: dict[str, dict[str, int]] = {
    "content-roaster": {"recall": 14, "rejected": 18, "near_miss": 7},
    "repo-roaster": {"recall": 15, "rejected": 18, "near_miss": 7},
    "science-roaster": {"recall": 14, "rejected": 18, "near_miss": 4},
}

sys.path.insert(0, str(ROOT / "tooling"))
from route_skill import normalize, route  # noqa: E402


def prompt_key(text: str) -> str:
    """Case-, accent- and punctuation-insensitive identity of a prompt."""
    return " ".join(re.findall(r"[a-z0-9]+", normalize(text)))


def _tokens(text: str) -> set[str]:
    return set(prompt_key(text).split())


def similarity(a: str, b: str) -> float:
    left, right = _tokens(a), _tokens(b)
    return len(left & right) / len(left | right) if left | right else 1.0


def _active(registry: dict) -> dict[str, dict]:
    return {s["id"]: s for s in registry["skills"] if s.get("lifecycle") == "active"}


def structural_problems(cases: list, registry: dict, *, label: str = "suite") -> list[str]:
    """Defects that make a passing routing run say less than it appears to."""
    if not isinstance(cases, list) or not cases:
        return [f"{label}: cases must be a non-empty list"]
    known = {s["id"] for s in registry["skills"]}
    examples = {prompt_key(e): (s["id"], key)
                for s in registry["skills"]
                for key in ("trigger_examples", "negative_trigger_examples")
                for e in s.get(key, [])}
    problems: list[str] = []
    ids: set[str] = set()
    prompts: dict[str, str] = {}
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            problems.append(f"{label}[{index}]: case must be an object")
            continue
        cid = case.get("id")
        where = f"{label}:{cid}" if isinstance(cid, str) else f"{label}[{index}]"
        if not isinstance(cid, str) or not cid.strip():
            problems.append(f"{where}: id must be a non-empty string")
        elif cid in ids:
            problems.append(f"{where}: duplicate case id")
        else:
            ids.add(cid)
        prompt = case.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            problems.append(f"{where}: prompt must be a non-empty string")
            continue
        key = prompt_key(prompt)
        if key in prompts:
            problems.append(f"{where}: prompt duplicates {prompts[key]} after normalization")
        else:
            prompts[key] = str(cid)
        if key in examples:
            sid, field = examples[key]
            problems.append(f"{where}: prompt copies registry {sid}.{field}; "
                            "registry examples are already tested, paraphrase it")
        expected = case.get("expected_primary_skill")
        if expected is not None and expected not in known:
            problems.append(f"{where}: unknown expected skill {expected!r}")
        for field in ("must_not_trigger", "allowed_secondary_skills"):
            values = case.get(field, [])
            if not isinstance(values, list) or any(not isinstance(v, str) for v in values):
                problems.append(f"{where}: {field} must be a list of skill IDs")
                continue
            if len(values) != len(set(values)):
                problems.append(f"{where}: {field} repeats a skill")
            for sid in values:
                if sid not in known:
                    problems.append(f"{where}: {field} names unknown skill {sid!r}")
        forbidden = case.get("must_not_trigger", [])
        if isinstance(forbidden, list) and expected is not None and expected in forbidden:
            problems.append(f"{where}: expects {expected} and forbids it")
    return problems


def near_duplicates(cases: list[dict], threshold: float = NEAR_DUPLICATE) -> list[tuple[str, str, float]]:
    """Pairs of prompts that differ by a word or two; reported, not failed."""
    rows = []
    for i, left in enumerate(cases):
        for right in cases[i + 1:]:
            score = similarity(left["prompt"], right["prompt"])
            if score >= threshold:
                rows.append((left["id"], right["id"], round(score, 2)))
    return rows


def coverage(cases: list[dict], registry: dict) -> list[dict]:
    rows = []
    for sid, entry in sorted(_active(registry).items()):
        positive = [c["id"] for c in cases if c.get("expected_primary_skill") == sid]
        forbidden = [c for c in cases if sid in c.get("must_not_trigger", [])]
        rows.append({
            "id": sid,
            "positive": len(positive),
            "negative": len(forbidden),
            # A negative whose winner is another skill is a boundary case; one
            # that expects no skill at all is an out-of-scope case.
            "boundary": sum(c.get("expected_primary_skill") is not None for c in forbidden),
            "out_of_scope": sum(c.get("expected_primary_skill") is None for c in forbidden),
            "registry_examples": len(entry.get("trigger_examples", [])),
            "registry_negatives": len(entry.get("negative_trigger_examples", [])),
        })
    return rows


def floor_problems(rows: list[dict], *, min_positive: int = MIN_POSITIVE,
                   min_negative: int = MIN_NEGATIVE) -> list[str]:
    problems = []
    for row in rows:
        if row["positive"] < min_positive:
            problems.append(f"{row['id']}: {row['positive']} positive routing case(s) < {min_positive}")
        if row["negative"] < min_negative:
            problems.append(f"{row['id']}: forbidden in {row['negative']} case(s) < {min_negative}")
    return problems


def gap_problems(gaps: dict, suite_cases: list[dict], registry: dict, policy: dict) -> list[str]:
    """Each known gap must still misroute exactly as recorded."""
    if not isinstance(gaps, dict) or gaps.get("schema") != GAPS_SCHEMA:
        return [f"known-gaps: schema must be {GAPS_SCHEMA}"]
    cases = gaps.get("cases")
    if not isinstance(cases, list):
        return ["known-gaps: cases must be a list"]
    problems = structural_problems(cases, registry, label="known-gaps") if cases else []
    in_suite = {prompt_key(c["prompt"]) for c in suite_cases if isinstance(c.get("prompt"), str)}
    for case in cases:
        if not isinstance(case, dict) or not isinstance(case.get("prompt"), str):
            continue
        cid = case.get("id")
        for field in ("observed_status", "reason"):
            if not isinstance(case.get(field), str) or not case[field].strip():
                problems.append(f"known-gaps:{cid}: {field} is required")
        if "observed_primary_skill" not in case:
            problems.append(f"known-gaps:{cid}: observed_primary_skill is required")
            continue
        if prompt_key(case["prompt"]) in in_suite:
            problems.append(f"known-gaps:{cid}: prompt is also in suite.json; keep it in one place")
        expected, observed = case.get("expected_primary_skill"), case["observed_primary_skill"]
        if expected == observed:
            problems.append(f"known-gaps:{cid}: expected equals observed; this is not a gap")
            continue
        result = route(case["prompt"], registry, policy)
        if result["primary_skill"] == expected and not any(
                sid == result["primary_skill"] or sid in result["candidates"]
                for sid in case.get("must_not_trigger", [])):
            problems.append(f"known-gaps:{cid}: now routes as expected ({expected!r}); "
                            "promote it to suite.json and delete the gap")
        elif (result["primary_skill"], result["status"]) != (observed, case.get("observed_status")):
            problems.append(f"known-gaps:{cid}: misroute changed to {result['primary_skill']!r}/"
                            f"{result['status']} (recorded {observed!r}/{case.get('observed_status')}); "
                            "re-record it")
    return problems


def trigger_eval_proxy(registry: dict, policy: dict) -> list[dict]:
    """Replay skill-local trigger evals through the deterministic router."""
    rows = []
    for path in sorted((ROOT / "skills").glob("*/evals/trigger-evals.json")):
        sid = path.parent.parent.name
        data = json.loads(path.read_text(encoding="utf-8"))
        hit = miss = rejected = leaked = near = near_named = 0
        for row in data if isinstance(data, list) else []:
            if not isinstance(row, dict) or not isinstance(row.get("query"), str):
                continue
            got = route(row["query"], registry, policy)["primary_skill"]
            if row.get("should_trigger") is True:
                hit, miss = hit + (got == sid), miss + (got != sid)
            elif row.get("should_trigger") is False:
                rejected, leaked = rejected + (got != sid), leaked + (got == sid)
                if row.get("near_miss"):
                    near += 1
                    near_named += got == row["near_miss"]
        rows.append({"id": sid, "recall": hit, "should_trigger": hit + miss,
                     "rejected": rejected, "should_not_trigger": rejected + leaked,
                     "false_positive": leaked, "near_miss_routed": near_named, "near_miss": near})
    return rows


def trigger_eval_floor_problems(rows: list[dict],
                                floors: dict[str, dict[str, int]] = TRIGGER_EVAL_FLOORS) -> list[str]:
    by_id = {row["id"]: row for row in rows}
    fields = {"recall": ("recall", "should_trigger"), "rejected": ("rejected", "should_not_trigger"),
              "near_miss": ("near_miss_routed", "near_miss")}
    problems = []
    for sid, floor in sorted(floors.items()):
        row = by_id.get(sid)
        if row is None:
            problems.append(f"trigger-evals {sid}: floor set but no evals/trigger-evals.json found")
            continue
        for name, minimum in sorted(floor.items()):
            got, total = (row[key] for key in fields[name])
            if got < minimum:
                problems.append(f"trigger-evals {sid}: {name} {got}/{total} < floor {minimum}")
    return problems


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def report(*, with_trigger_evals: bool = False) -> dict:
    registry, policy, suite = _load(REGISTRY), _load(POLICY), _load(SUITE)
    cases = suite.get("cases", [])
    gaps = _load(GAPS) if GAPS.is_file() else {"schema": GAPS_SCHEMA, "cases": []}
    rows = coverage(cases, registry)
    proxy = trigger_eval_proxy(registry, policy)
    out = {
        "schema": "cometweb.routing-coverage/v1",
        "mode": "deterministic_proxy",
        "runtime_acceptance": "not_assessed",
        "cases": len(cases),
        "known_gaps": len(gaps.get("cases", [])),
        "floors": {"min_positive": MIN_POSITIVE, "min_negative": MIN_NEGATIVE},
        "skills": rows,
        "near_duplicates": [list(row) for row in near_duplicates(
            [c for c in cases if isinstance(c, dict) and isinstance(c.get("prompt"), str)])],
        "problems": (structural_problems(cases, registry) + floor_problems(rows)
                     + gap_problems(gaps, cases, registry, policy)
                     + trigger_eval_floor_problems(proxy)),
    }
    if with_trigger_evals:
        out["trigger_eval_proxy"] = proxy
    return out


def table(data: dict) -> str:
    out = ["| Skill | Positive | Negative | Boundary | Out of scope |",
           "| --- | ---: | ---: | ---: | ---: |"]
    for row in sorted(data["skills"], key=lambda r: (r["positive"] + r["negative"], r["id"])):
        out.append(f"| `{row['id']}` | {row['positive']} | {row['negative']} | "
                   f"{row['boundary']} | {row['out_of_scope']} |")
    out.append("")
    out.append(f"{data['cases']} suite cases, {data['known_gaps']} known gap(s); "
               f"floors {data['floors']['min_positive']} positive / "
               f"{data['floors']['min_negative']} negative per active skill.")
    for left, right, score in data["near_duplicates"]:
        out.append(f"near-duplicate {score:.2f}: {left} ~ {right}")
    for row in data.get("trigger_eval_proxy", []):
        out.append(f"trigger-evals proxy `{row['id']}`: recall {row['recall']}/{row['should_trigger']}, "
                   f"rejected {row['rejected']}/{row['should_not_trigger']}, "
                   f"near-miss sent to the named skill {row['near_miss_routed']}/{row['near_miss']}")
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="exit 1 on suite defects, floor misses or stale gaps")
    parser.add_argument("--json", action="store_true", help="print the report as JSON")
    parser.add_argument("--trigger-evals", action="store_true",
                        help="also report every skill-local trigger-evals.json replay (floored skills are checked regardless)")
    args = parser.parse_args(argv)
    data = report(with_trigger_evals=args.trigger_evals)
    print(json.dumps(data, indent=2, ensure_ascii=False) if args.json else table(data), end="" if not args.json else "\n")
    if args.check:
        for problem in data["problems"]:
            print(f"FAIL: {problem}", file=sys.stderr)
        if data["problems"]:
            return 1
        print(f"OK: routing coverage ({data['cases']} cases, {len(data['skills'])} skills at floor)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
