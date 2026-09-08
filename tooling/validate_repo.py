#!/usr/bin/env python3
"""Repo-level validation: registry ↔ skills ↔ protocol ↔ evals."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "skills.json"
HOSTS = ROOT / "registry" / "hosts.json"
SKILLS = ROOT / "skills"
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    raise SystemExit(1)


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        fail(f"missing YAML frontmatter: {path}")
    block = match.group(1)
    result: dict[str, str] = {}
    key: str | None = None
    buf: list[str] = []
    for line in block.splitlines():
        if line.startswith("  ") and key:
            buf.append(line.strip())
            continue
        if key:
            result[key] = " ".join(buf).strip()
            buf = []
        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip()
            if val in (">", ">-", "|"):
                buf = []
            else:
                result[key] = val.strip('"').strip("'")
                key = None
    if key:
        result[key] = " ".join(buf).strip()
    return result


def load_json(path: Path) -> dict:
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    registry = load_json(REGISTRY)
    hosts = load_json(HOSTS)
    skills = registry.get("skills")
    if not isinstance(skills, list) or not skills:
        fail("registry.skills must be a non-empty list")

    ids = [s.get("id") for s in skills]
    if len(ids) != len(set(ids)):
        fail("duplicate skill ids in registry")

    on_disk = {p.name for p in SKILLS.iterdir() if p.is_dir() and not p.name.startswith(".")}
    reg_ids = set(ids)
    if on_disk != reg_ids:
        missing = sorted(on_disk - reg_ids)
        extra = sorted(reg_ids - on_disk)
        if missing:
            fail(f"skills on disk missing from registry: {missing}")
        if extra:
            fail(f"registry ids missing on disk: {extra}")

    common = hosts["hosts"]["agentskills-common"]
    codex = hosts["hosts"]["openai-codex"]
    name_re = re.compile(common["name_pattern"])

    for entry in skills:
        sid = entry["id"]
        skill_dir = SKILLS / sid
        for rel in ("SKILL.md", "VERSION"):
            if not (skill_dir / rel).is_file():
                fail(f"{sid}: missing {rel}")
        if entry.get("lifecycle") == "active" and not (skill_dir / "LICENSE").is_file():
            # allow missing LICENSE only for internal-only packages if declared
            if entry.get("visibility") not in {"internal_only"}:
                fail(f"{sid}: missing LICENSE")

        fm = parse_frontmatter(skill_dir / "SKILL.md")
        if fm.get("name") != sid:
            fail(f"{sid}: frontmatter name mismatch ({fm.get('name')!r})")
        desc = fm.get("description", "")
        if len(desc) < common["description_min"]:
            fail(f"{sid}: description too short ({len(desc)})")
        if len(desc) > common["description_max"]:
            fail(f"{sid}: description exceeds common max ({len(desc)})")
        if len(desc) > codex["description_max"]:
            fail(f"{sid}: description exceeds openai-codex max {codex['description_max']} ({len(desc)})")
        reg_desc = (entry.get("description") or "").strip()
        if " ".join(desc.split()) != " ".join(reg_desc.split()):
            fail(f"{sid}: SKILL.md description != registry.description")
        if not name_re.match(sid):
            fail(f"{sid}: id fails name_pattern")
        if not entry.get("alias_of"):
            if not entry.get("owns"):
                fail(f"{sid}: registry.owns must be non-empty")
            if not entry.get("does_not_own"):
                fail(f"{sid}: registry.does_not_own must be non-empty")
            if not entry.get("trigger_examples"):
                fail(f"{sid}: registry.trigger_examples must be non-empty")
            if not entry.get("negative_trigger_examples"):
                fail(f"{sid}: registry.negative_trigger_examples must be non-empty")
            if not entry.get("routing_signals"):
                fail(f"{sid}: registry.routing_signals must be non-empty")
        elif entry.get("alias_of") and not entry.get("routing_signals"):
            fail(f"{sid}: alias must still declare routing_signals")

        suite = entry.get("eval_suite")
        if suite:
            suite_path = ROOT / suite / "suite.json"
            if not suite_path.is_file():
                fail(f"{sid}: eval_suite path missing suite.json ({suite})")
        # Foundation context skill must keep executable behavior suite wired
        if sid == "cometweb-context" and suite != "evals/behavior/cometweb-context":
            fail(f"{sid}: eval_suite must be evals/behavior/cometweb-context")

        version_file = (skill_dir / "VERSION").read_text(encoding="utf-8").strip()
        if entry.get("version") != version_file:
            fail(f"{sid}: registry version {entry.get('version')!r} != VERSION {version_file!r}")

        # Broken relative refs inside SKILL.md (best-effort)
        skill_md = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        for ref in re.findall(r"\(([^)]+\.(?:md|json|py|yaml|yml|svg))\)", skill_md):
            if ref.startswith("http") or ref.startswith("../../protocol"):
                continue
            target = (skill_dir / ref).resolve()
            if not str(target).startswith(str(skill_dir.resolve())):
                continue
            if not target.exists():
                fail(f"{sid}: broken relative ref {ref}")

    # Protocol schemas present
    for rel in (
        "protocol/cw-aip-v2/core.schema.json",
        "protocol/cw-aip-v2/context.schema.json",
        "protocol/cw-aip-v2/evidence.schema.json",
        "protocol/cw-aip-v2/decision.schema.json",
        "protocol/cw-aip-v2/finding.schema.json",
        "protocol/cw-aip-v2/roadmap.schema.json",
        "protocol/cw-aip-v2/release.schema.json",
        "protocol/cw-interchange-v1.md",
    ):
        if not (ROOT / rel).is_file():
            fail(f"missing {rel}")

    print(f"OK: validate_repo ({len(skills)} skills)")


if __name__ == "__main__":
    main()
