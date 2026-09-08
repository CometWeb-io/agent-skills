#!/usr/bin/env python3
"""Release checks for the ai-humanize skill bundle."""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "SKILL.md"


def fail(message: str) -> None:
    raise AssertionError(message)


def load_guard():
    path = ROOT / "scripts" / "rewrite_guard.py"
    spec = importlib.util.spec_from_file_location("rewrite_guard", path)
    if spec is None or spec.loader is None:
        fail("cannot import rewrite_guard.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def check_frontmatter(text: str) -> None:
    match = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
    if not match:
        fail("SKILL.md must start with YAML frontmatter")
    keys = []
    for line in match.group(1).splitlines():
        if not line.strip() or line.startswith(" "):
            continue
        if ":" in line:
            keys.append(line.split(":", 1)[0].strip())
    if keys != ["name", "description"]:
        fail(f"frontmatter keys must be exactly name, description; got {keys}")


def check_local_references(text: str) -> None:
    refs = set(re.findall(r"`((?:references|evaluation|scripts)/[^`\s]+)`", text))
    missing = [ref for ref in sorted(refs) if not (ROOT / ref).exists()]
    if missing:
        fail(f"missing referenced files: {missing}")


def extract_example_parts(text: str, name: str) -> tuple[str, str]:
    before_match = re.search(r"(?m)^## (?:Before|Przed)\s*$", text)
    after_match = re.search(r"(?m)^## (?:After|Po) \((?:deep|strong|light)\)\s*$", text)
    if not before_match or not after_match or after_match.start() <= before_match.end():
        fail(f"{name}: cannot locate Before/After sections")
    before = text[before_match.end():after_match.start()].strip()
    tail = text[after_match.end():]
    after = re.split(r"(?m)^## ", tail, maxsplit=1)[0].strip()
    return before, after


def check_examples() -> None:
    guard = load_guard()
    patterns = [
        re.compile(r"\bIt's not about\b", re.I),
        re.compile(r"\bThis isn't\b", re.I),
        re.compile(r"\bIn today's rapidly\b", re.I),
        re.compile(r"\bW dzisiejszym dynamicznie\b", re.I),
    ]
    unsupported = re.compile(
        r"\b(?:undetectable|detector defeated|human-written|watermark removed|"
        r"niewykrywaln\w*|napisan\w+ przez człowieka|watermark usunięt\w*)\b",
        re.I,
    )

    examples = sorted((ROOT / "examples").glob("*.md"))
    if not examples:
        fail("no examples found")
    for path in examples:
        text = path.read_text(encoding="utf-8")
        if not re.search(r"(?m)^## (?:Before|Przed)\s*$", text):
            continue
        before, after = extract_example_parts(text, path.name)
        if unsupported.search(after):
            fail(f"{path.name}: output contains unsupported provenance/detection claim")
        for pattern in patterns:
            if pattern.search(after):
                fail(f"{path.name}: output reintroduces prohibited signature pattern {pattern.pattern}")
        result = guard.compare(before, after, strict=True)
        if not result["passed"]:
            fail(
                f"{path.name}: hard invariant drift: missing={result['missing_invariants']} "
                f"added={result['added_invariants']}"
            )


def check_redteam_manifest() -> None:
    path = ROOT / "evaluation" / "redteam-cases.json"
    cases = json.loads(path.read_text(encoding="utf-8"))
    if len(cases) < 12:
        fail("red-team manifest should contain at least 12 cases")
    ids = [case.get("id") for case in cases]
    if len(ids) != len(set(ids)):
        fail("red-team case IDs must be unique")
    required = {"id", "language", "request", "mode_expectation", "source", "manual_checks"}
    for case in cases:
        missing = required - set(case)
        if missing:
            fail(f"red-team case {case.get('id')} missing fields: {sorted(missing)}")


def run_tests() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=ROOT,
        text=True,
    )
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)


def main() -> int:
    text = SKILL.read_text(encoding="utf-8")
    check_frontmatter(text)
    check_local_references(text)
    check_examples()
    check_redteam_manifest()
    run_tests()
    print("release_check: PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"release_check: FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
