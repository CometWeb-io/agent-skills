#!/usr/bin/env python3
"""Frozen blind routing holdout: integrity check and aggregate-only measurement.

    uv run python tooling/routing_holdout.py --check     # integrity (CI gate)
    uv run python tooling/routing_holdout.py             # aggregate accuracy
    uv run python tooling/routing_holdout.py --json

`evals/routing/holdout.json` was written before its author read the routing
signals, and nobody tunes routing on it. Every other routing set in this
repository has been looked at while signals were edited, so its pass rate is an
optimistic number; this one is the honest estimate.

The rules (see evals/routing/README.md, "Frozen holdout"):

- The file is pinned by sha256 in `evals/routing/holdout.lock.json`. Any edit,
  including a typo fix, fails `--check` until `holdout_version` is bumped and
  the lock is re-recorded with `--record`. `--record` refuses to give an
  already-recorded version a different hash, so a silent edit cannot hide
  behind the old version number.
- Measurement prints aggregates only (overall, per kind, per language), never
  which prompts failed. A tool that lists the misses is a tuning loop.
- No holdout prompt may also appear (after normalization) in a routing set
  that is used for tuning: suite.json, known-gaps.json, the canonical, policy
  and adversarial suites, or a registry trigger example. Once a holdout prompt
  is tuned on it stops being a holdout: retire it in a new version.

A case passes when the router's primary skill equals `expected_primary_skill`
(None for "no skill") and no `must_not_trigger` skill is the primary or a
candidate, which is the rule tooling/run_routing_evals.py applies to suite.json.

Read-only apart from `--record`; offline; standard library only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTING = ROOT / "evals" / "routing"
HOLDOUT = ROUTING / "holdout.json"
LOCK = ROUTING / "holdout.lock.json"
REGISTRY = ROOT / "registry" / "skills.json"
POLICY = ROOT / "registry" / "routing-policy.json"
SCHEMA = "cometweb.routing-holdout/v1"
LOCK_SCHEMA = "cometweb.routing-holdout-lock/v1"
KINDS = ("positive", "near_miss", "no_skill")
# Routing sets whose prompts are read while signals are tuned.
TUNED_SETS = ("suite.json", "known-gaps.json", "canonical-suite.json", "policy-suite.json",
              "adversarial-suite.json")
VERSION = re.compile(r"^\d+\.\d+\.\d+$")

sys.path.insert(0, str(ROOT / "tooling"))
from route_skill import route  # noqa: E402
from routing_coverage import NEAR_DUPLICATE, prompt_key, similarity, structural_problems  # noqa: E402


def digest(path: Path = HOLDOUT) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _tuned_prompts(root: Path, registry: dict) -> dict[str, str]:
    """Normalized prompt -> where it lives, for every prompt routing is tuned on."""
    seen: dict[str, str] = {}
    for name in TUNED_SETS:
        path = root / "evals" / "routing" / name
        if not path.exists():
            continue
        for case in _load(path).get("cases", []):
            if isinstance(case, dict) and isinstance(case.get("prompt"), str):
                seen.setdefault(prompt_key(case["prompt"]), f"{name}:{case.get('id')}")
    for skill in registry["skills"]:
        for field in ("trigger_examples", "negative_trigger_examples"):
            for example in skill.get(field, []):
                seen.setdefault(prompt_key(example), f"registry {skill['id']}.{field}")
    return seen


def problems(holdout_path: Path = HOLDOUT, lock_path: Path = LOCK, root: Path = ROOT) -> list[str]:
    """Integrity defects: hash drift, schema errors, overlap with tuned sets."""
    out: list[str] = []
    data, lock = _load(holdout_path), _load(lock_path)
    registry = _load(root / "registry" / "skills.json")
    if data.get("schema") != SCHEMA:
        out.append(f"holdout: schema must be {SCHEMA}")
    if lock.get("schema") != LOCK_SCHEMA:
        out.append(f"lock: schema must be {LOCK_SCHEMA}")
    version = data.get("holdout_version")
    versions = {entry.get("holdout_version"): entry.get("sha256") for entry in lock.get("versions", [])}
    actual = digest(holdout_path)
    if not isinstance(version, str) or not VERSION.match(version):
        out.append("holdout: holdout_version must be MAJOR.MINOR.PATCH")
    elif version not in versions:
        out.append(f"holdout: version {version} is not recorded in the lock; "
                   "record it with tooling/routing_holdout.py --record")
    elif versions[version] != actual:
        out.append(f"holdout: file changed without a version bump (sha256 {actual[:12]}…, "
                   f"lock has {str(versions[version])[:12]}… for {version}). The holdout is frozen: "
                   "bump holdout_version deliberately, then --record")
    if lock.get("current") != version:
        out.append(f"lock: current is {lock.get('current')!r}, holdout says {version!r}")
    cases = data.get("cases")
    out += structural_problems(cases, registry, label="holdout")
    if not isinstance(cases, list):
        return out
    kinds = Counter(c.get("kind") for c in cases if isinstance(c, dict))
    for case in cases:
        if isinstance(case, dict) and case.get("kind") not in KINDS:
            out.append(f"holdout:{case.get('id')}: kind must be one of {', '.join(KINDS)}")
        if isinstance(case, dict) and case.get("kind") == "no_skill" and case.get("expected_primary_skill"):
            out.append(f"holdout:{case.get('id')}: a no_skill case cannot expect a skill")
    if kinds["near_miss"] < 10 or kinds["no_skill"] < 10:
        out.append("holdout: needs at least 10 near_miss and 10 no_skill cases")
    tuned = _tuned_prompts(root, registry)
    for case in cases:
        if isinstance(case, dict) and isinstance(case.get("prompt"), str):
            hit = tuned.get(prompt_key(case["prompt"]))
            if hit:
                out.append(f"holdout:{case.get('id')}: prompt also appears in {hit}; a tuned-on "
                           "prompt is no longer held out")
    # A paraphrase leaks as surely as a copy. The count of holdout prompts within
    # NEAR_DUPLICATE of a tuned prompt may not grow past what the lock recorded.
    near = len(near_duplicates(cases, list(tuned)))
    ceiling = lock.get("max_near_duplicates", 0)
    if near > ceiling:
        out.append(f"holdout: {near} prompt(s) are near-duplicates (token overlap >= {NEAR_DUPLICATE}) of "
                   f"tuned routing prompts; the lock allows {ceiling}. Rephrase the new tuned prompt, "
                   "or retire the leaked holdout prompt in a new holdout_version")
    return out


def near_duplicates(cases: list, tuned_keys: list[str]) -> list[str]:
    """IDs of holdout prompts that nearly repeat a prompt routing was tuned on."""
    return [str(case.get("id")) for case in cases
            if isinstance(case, dict) and isinstance(case.get("prompt"), str)
            and any(similarity(case["prompt"], key) >= NEAR_DUPLICATE for key in tuned_keys)]


def uncovered_skills(holdout_path: Path = HOLDOUT, root: Path = ROOT) -> list[str]:
    """Active skills the frozen holdout has no positive case for (added after the freeze)."""
    registry = _load(root / "registry" / "skills.json")
    active = {s["id"] for s in registry["skills"] if s.get("lifecycle", "active") == "active"}
    covered = {c.get("expected_primary_skill") for c in _load(holdout_path)["cases"] if c.get("kind") == "positive"}
    return sorted(active - covered)


def passed(case: dict, result: dict) -> bool:
    primary = result["primary_skill"]
    if primary != case["expected_primary_skill"]:
        return False
    return not any(b == primary or b in result["candidates"] for b in case["must_not_trigger"])


def measure(holdout_path: Path = HOLDOUT, root: Path = ROOT) -> dict:
    """Aggregate pass counts. Deliberately carries no per-case detail."""
    registry, policy = _load(root / "registry" / "skills.json"), _load(root / "registry" / "routing-policy.json")
    cases = _load(holdout_path)["cases"]
    totals: dict[str, Counter] = {"all": Counter(), "kind": Counter(), "lang": Counter()}
    for case in cases:
        ok = passed(case, route(case["prompt"], registry, policy))
        lang = case.get("lang", "en")
        for bucket, key in (("all", "all"), ("kind", case["kind"]), ("lang", lang)):
            totals[bucket][(key, "n")] += 1
            totals[bucket][(key, "ok")] += ok

    def table(bucket: str) -> dict[str, list[int]]:
        keys = sorted({k for k, _ in totals[bucket]})
        return {k: [totals[bucket][(k, "ok")], totals[bucket][(k, "n")]] for k in keys}

    return {"holdout_version": _load(holdout_path)["holdout_version"], "sha256": digest(holdout_path),
            "overall": table("all")["all"], "by_kind": table("kind"), "by_lang": table("lang")}


def record(holdout_path: Path = HOLDOUT, lock_path: Path = LOCK) -> str:
    data = _load(holdout_path)
    lock = _load(lock_path) if lock_path.exists() else {"schema": LOCK_SCHEMA, "versions": []}
    version, sha = data["holdout_version"], digest(holdout_path)
    for entry in lock["versions"]:
        if entry["holdout_version"] == version and entry["sha256"] != sha:
            raise SystemExit(f"version {version} is already recorded with another hash; bump holdout_version")
    if not any(e["holdout_version"] == version for e in lock["versions"]):
        lock["versions"].append({"holdout_version": version, "sha256": sha, "cases": len(data["cases"])})
    lock["current"] = version
    lock_path.write_text(json.dumps(lock, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return sha


def log_measurement(label: str, result: dict, lock_path: Path = LOCK) -> None:
    """Append-only: each entry says when the holdout was read and what it scored."""
    lock = _load(lock_path)
    lock.setdefault("measurements", []).append(
        {"label": label, "holdout_version": result["holdout_version"], "overall": result["overall"],
         "by_kind": result["by_kind"], "by_lang": result["by_lang"]})
    lock_path.write_text(json.dumps(lock, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="integrity only; exit 1 on a defect")
    parser.add_argument("--json", action="store_true", help="print the aggregate measurement as JSON")
    parser.add_argument("--record", action="store_true", help="pin a deliberately bumped holdout version")
    parser.add_argument("--log", metavar="LABEL",
                        help="append this aggregate measurement to the lock's measurement log")
    args = parser.parse_args(argv)
    if args.record:
        print(f"recorded {_load(HOLDOUT)['holdout_version']} sha256 {record()}")
        return 0
    found = problems()
    if args.check:
        for line in found:
            print(f"FAIL: {line}", file=sys.stderr)
        if not found:
            print(f"OK: holdout {_load(HOLDOUT)['holdout_version']} intact ({digest()[:12]}…)")
        return 1 if found else 0
    if missing := uncovered_skills():
        # Skills added after the freeze are not measured here; the next version should add them.
        print(f"note: no holdout positive for {', '.join(missing)}", file=sys.stderr)
    if found:
        print("holdout integrity problems; numbers below are not comparable:", file=sys.stderr)
        for line in found:
            print(f"  {line}", file=sys.stderr)
    result = measure()
    if args.log:
        if found:
            raise SystemExit("refusing to log a measurement of a holdout that fails --check")
        log_measurement(args.log, result)
    if args.json:
        print(json.dumps(result, indent=2))
        return 0
    ok, n = result["overall"]
    print(f"holdout {result['holdout_version']}: {ok}/{n} ({100 * ok / n:.1f}%)")
    for bucket in ("by_kind", "by_lang"):
        for key, (k_ok, k_n) in result[bucket].items():
            print(f"  {key:<10} {k_ok}/{k_n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
