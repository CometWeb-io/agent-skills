#!/usr/bin/env python3
"""How much of a kernel its own eval harness actually pins.

A harness that runs is not the same as a harness that holds. Inverting the
priority-score comparator in portfolio_kernel left all ten golden cases green,
because every ranking case was decided by the gate order before the score was
ever consulted. Counting cases would not have shown that; counting which guards
a case can still be broken past does.

Method: copy the package to a temporary directory, replace one `if` guard at a
time with `if False:`, and run the package's own harness against the copy. A
guard the harness still passes without is a guard nothing is holding. The
working tree is never edited, so an interrupted run cannot leave a broken kernel
behind.

Some guards cannot be observed this way and that is not a coverage gap: a guard
whose removal produces the same value, one masked by an earlier gate, or one
reachable only through the CLI. They are recorded, not explained away.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
HARNESS = "scripts/run_evals.py"
BASELINE = ROOT / "registry" / "eval-strength.json"
POLICY = ROOT / "registry" / "eval-strength-policy.json"
TIMEOUT = 120

# Guards a harness cannot reach by construction, not ones it fails to cover.
SKIP_PREFIXES = ("if __name__", "if args.")


def guard_lines(text: str) -> list[int]:
    rows = []
    for index, line in enumerate(text.splitlines()):
        stripped = line.strip()
        if not (stripped.startswith("if ") and stripped.endswith(":")):
            continue
        if stripped in {"if False:", "if True:"} or stripped.startswith(SKIP_PREFIXES):
            continue
        rows.append(index)
    return rows


# A harness reaches a module by naming it: `from portfolio_kernel import ...` or
# `ROOT / "scripts" / "operator_kernel.py"`. Reading the name out of the harness
# source covers both styles, where inspecting sys.modules afterwards does not --
# product-operator loads its kernel through importlib without registering it.
def kernels(package: Path) -> list[Path]:
    """The package's own modules its harness names, and therefore exercises."""
    text = (package / HARNESS).read_text(encoding="utf-8")
    return sorted(p for p in (package / "scripts").glob("*.py")
                  if p.name != "run_evals.py" and re.search(rf"\b{re.escape(p.stem)}\b", text))


def unexercised(package: Path, loaded: list[Path]) -> list[str]:
    """Scripts the package ships that its harness never loads."""
    names = {p.name for p in loaded} | {"run_evals.py"}
    return sorted(p.name for p in (package / "scripts").glob("*.py") if p.name not in names)


def measure(package: Path) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        # .resolve(): on macOS the temp dir is /var/... while the harness's own
        # Path(__file__).resolve() reports /private/var/..., and the module filter
        # below compares those strings.
        work = Path(tmp).resolve() / package.name
        shutil.copytree(package, work, ignore=shutil.ignore_patterns("__pycache__"))
        harness = work / HARNESS
        if subprocess.run([sys.executable, "-B", str(harness)], cwd=ROOT, capture_output=True,
                          stdin=subprocess.DEVNULL, timeout=TIMEOUT, check=False).returncode != 0:
            raise SystemExit(f"FAIL: {package.name} harness does not pass unmutated")

        loaded = kernels(work)
        held = unheld = 0
        loose: list[str] = []
        for kernel in loaded:
            original = kernel.read_text(encoding="utf-8")
            lines = original.splitlines(keepends=True)
            for index in guard_lines(original):
                indent = len(lines[index]) - len(lines[index].lstrip())
                kernel.write_text(
                    "".join(lines[:index] + [" " * indent + "if False:\n"] + lines[index + 1:]),
                    encoding="utf-8")
                proc = subprocess.run([sys.executable, "-B", str(harness)], cwd=ROOT,
                                      capture_output=True, stdin=subprocess.DEVNULL,
                                      timeout=TIMEOUT, check=False)
                if proc.returncode == 0:
                    unheld += 1
                    loose.append(f"{kernel.name}:{index + 1} {lines[index].strip()[:80]}")
                else:
                    held += 1
                kernel.write_text(original, encoding="utf-8")
        total = held + unheld
        return {"id": package.name, "guards": total, "held": held,
                "strength": round(held / total, 3) if total else 0.0,
                "modules": sorted(p.name for p in loaded),
                "unexercised": unexercised(work, loaded),
                "unheld": sorted(loose)}


def current() -> list[dict]:
    rows = []
    for package in sorted(SKILLS.iterdir()):
        if (package / HARNESS).is_file():
            rows.append(measure(package))
    return rows


def table(rows: list[dict]) -> str:
    out = ["# Generated eval strength", "",
           "<!-- generated by tooling/eval_strength.py — do not hand-edit -->", "",
           "How much of each kernel its own harness holds. `guards` counts the `if`",
           "branches a harness can reach; `held` is how many of them the harness fails",
           "when the branch is removed. A guard nothing holds can be deleted without a",
           "single case going red.", "",
           "This is not a coverage percentage. A guard can be unheld because it is",
           "genuinely unobservable — the same value either way, or masked by an earlier",
           "gate — and those are listed rather than hidden.", "",
           "| Skill | Guards | Held | Strength |", "| --- | ---: | ---: | ---: |"]
    for row in sorted(rows, key=lambda r: -r["strength"]):
        out.append(f"| `{row['id']}` | {row['guards']} | {row['held']} | {row['strength']:.2f} |")
    idle = {row["id"]: row["unexercised"] for row in rows if row["unexercised"]}
    if idle:
        out += ["", "Scripts a package ships that its harness never loads, so nothing above "
                    "measures them:", ""]
        out += [f"- `{name}`: {', '.join(scripts)}" for name, scripts in sorted(idle.items())]
    total = sum(r["guards"] for r in rows)
    held = sum(r["held"] for r in rows)
    out += ["", f"**{len(rows)} harnesses.** {held} of {total} reachable guards are held "
                f"({held / total:.0%} if every skill counted equally, which they do not)."]
    return "\n".join(out) + "\n"


def compare(rows: list[dict], baseline: dict, policy: dict | None = None) -> list[str]:
    before = {row["id"]: row for row in baseline.get("skills", [])}
    policy = policy or {}
    default_floor = float(policy.get("default_min_strength", 0.0))
    critical = policy.get("critical_skills") or {}
    allow_unexercised = policy.get("allow_unexercised_scripts") or {}
    problems = []
    for row in rows:
        old = before.get(row["id"])
        if old is None:
            problems.append(f"{row['id']}: not in the baseline; run --update to record it")
            continue
        if row["held"] < old["held"]:
            problems.append(
                f"{row['id']}: held guards fell {old['held']} -> {row['held']} of {row['guards']}. "
                f"A rule the harness used to pin is now removable without a red case.")
        minimum = float(critical.get(row["id"], default_floor))
        strength = row.get("strength")
        if strength is None and row.get("guards"):
            strength = round(row["held"] / row["guards"], 3)
        if strength is not None and strength < minimum:
            problems.append(
                f"{row['id']}: strength {strength:.2f} < absolute floor {minimum:.2f}")
        allowed = set(allow_unexercised.get(row["id"], []))
        unexpected = [name for name in row.get("unexercised", []) if name not in allowed]
        if unexpected:
            problems.append(
                f"{row['id']}: unexercised scripts without waiver: " + ", ".join(unexpected))
        for name in sorted(allowed - set(row.get("unexercised", []))):
            problems.append(
                f"{row['id']}: waiver lists {name} but the harness now loads it; remove the waiver")
    missing = sorted(set(before) - {row["id"] for row in rows})
    for name in missing:
        problems.append(f"{name}: baseline has it but it ships no {HARNESS} any more")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="fail if any skill holds fewer guards than the baseline")
    parser.add_argument("--update", action="store_true", help="record the current measurement as the baseline")
    parser.add_argument("--table", type=Path, help="write the Markdown table to this path")
    parser.add_argument("--json", action="store_true", help="print the measurement as JSON")
    args = parser.parse_args(argv)

    rows = current()
    if args.json:
        print(json.dumps({"skills": rows}, indent=2, sort_keys=True))
    if args.table:
        target = args.table if args.table.is_absolute() else ROOT / args.table
        target.write_text(table(rows), encoding="utf-8")
        print(f"OK: wrote {target.relative_to(ROOT)}")
    if args.update:
        BASELINE.write_text(json.dumps(
            {"note": "Recorded by tooling/eval_strength.py --update. Held counts may rise freely; "
                     "a fall means a rule stopped being pinned.",
             "skills": [{k: v for k, v in row.items() if k not in {"unheld", "modules"}}
                        for row in rows]},
            indent=2, sort_keys=True) + "\n", encoding="utf-8")
        total = sum(r["held"] for r in rows)
        print(f"OK: eval strength baseline recorded for {len(rows)} skills ({total} held guards)")
    if args.check:
        if not BASELINE.is_file():
            print(f"FAIL: no baseline at {BASELINE.relative_to(ROOT)}; run --update", file=sys.stderr)
            return 1
        policy = {}
        if POLICY.is_file():
            policy = json.loads(POLICY.read_text(encoding="utf-8"))
            if policy.get("schema") != "cometweb.eval-strength-policy/v1":
                print(f"FAIL: unsupported policy schema in {POLICY.relative_to(ROOT)}", file=sys.stderr)
                return 1
        problems = compare(rows, json.loads(BASELINE.read_text(encoding="utf-8")), policy)
        for problem in problems:
            print(f"FAIL: {problem}", file=sys.stderr)
        if problems:
            return 1
        print(f"OK: eval strength ({sum(r['held'] for r in rows)} guards held across {len(rows)} skills)")
    if not (args.check or args.update or args.table or args.json):
        print(table(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
