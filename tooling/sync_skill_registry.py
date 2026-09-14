#!/usr/bin/env python3
"""Synchronize authoritative cross-runtime skill releases into registry/skills.json."""
from __future__ import annotations

import argparse
import json
import re
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "skills.json"
SKILLS = ROOT / "skills"
HOST_TARGETS = [
    "chatgpt",
    "openai-codex",
    "claude-code",
    "cursor",
    "qwen-code",
    "qoder",
    "lingma",
    "alibaba-skills-portal",
]
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)


def parse_description(skill_md: Path) -> str:
    text = skill_md.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError(f"missing frontmatter: {skill_md}")
    block = match.group(1).splitlines()
    for i, line in enumerate(block):
        if not line.startswith("description:"):
            continue
        value = line.split(":", 1)[1].strip()
        if value not in {">", ">-", "|", ""}:
            return value.strip('"').strip("'")
        parts: list[str] = []
        for following in block[i + 1 :]:
            if following.startswith("  "):
                parts.append(following.strip())
            else:
                break
        return " ".join(parts).strip()
    raise ValueError(f"missing description: {skill_md}")


def package_identity(skill_id: str) -> tuple[str, str]:
    skill_dir = SKILLS / skill_id
    return (
        (skill_dir / "VERSION").read_text(encoding="utf-8").strip(),
        parse_description(skill_dir / "SKILL.md"),
    )


OVERRIDES: dict[str, dict] = {
    "founder-led-sales-operator": {
        "release_status": "FROZEN",
        "tier": "domain",
        "owns": ["founder-led commercial next action", "sales-stage reconciliation", "commercial gates and proof progression"],
        "does_not_own": ["broad prospect-list generation", "pricing/packaging strategy", "post-sale customer operations"],
        "trigger_examples": ["What should I do next with these qualified prospects?", "Which founder-led deals should I move, verify, wait, or stop?"],
        "negative_trigger_examples": ["Build me a broad list of 100 prospects", "Design our SaaS pricing tiers"],
        "routing_signals": [[12, "founder-led sales operator|founder led sales"], [10, "qualified prospects?.*(next|move|follow.?up|convert)"], [9, "commercial (next action|gate|proof|stage)"], [8, "pipeline.*(verify|wait|stop|paid conversion)"]],
        "required_capabilities": [],
        "optional_capabilities": ["filesystem", "code_execution", "web", "connectors"],
    },
    "research-program-operator": {
        "release_status": "FROZEN",
        "tier": "domain",
        "owns": ["research-program stage gates", "research/manuscript readiness", "next-study planning"],
        "does_not_own": ["one-off claim verification", "final publication formatting", "cross-domain portfolio allocation"],
        "trigger_examples": ["What should this study do next?", "Reconcile this research project from methodology through manuscript readiness"],
        "negative_trigger_examples": ["Verify this single factual claim", "Format this finished paper as DOCX"],
        "routing_signals": [[12, "research program operator|research-program"], [10, "study.*(what next|readiness|methodology|manuscript)"], [9, "research.*(stage gate|submission readiness|next study)"], [8, "academic project.*(blocker|authorship|governance)"]],
        "required_capabilities": [],
        "optional_capabilities": ["filesystem", "code_execution", "web", "files", "connectors"],
    },
    "portfolio-operator": {
        "release_status": "ACTIVE",
        "tier": "foundation",
        "owns": ["cross-domain allocation", "capacity conflicts", "focus/pause/delegate decisions"],
        "does_not_own": ["deep single-product sequencing", "release GO/NO_GO", "specialist implementation"],
        "trigger_examples": ["What should I focus on for the next 14 days across all my projects?", "Which commitments conflict and what should I pause?"],
        "negative_trigger_examples": ["What should we build next inside this one repo?", "Is this release candidate safe to ship?"],
        "routing_signals": [[12, "portfolio operator|portfolio-wide"], [10, "next (7|14|30) days.*(projects|commitments|focus)"], [9, "capacity conflicts?|what should (i|we) pause|across multiple projects"], [8, "client.*product.*research|cross-domain allocation"]],
        "required_capabilities": [],
        "optional_capabilities": ["filesystem", "code_execution", "connectors"],
    },
    "longform-publisher": {
        "release_status": "FROZEN",
        "tier": "domain",
        "owns": ["canonical long-form manuscript", "publication lifecycle and claim-use reconciliation", "derived-artifact release readiness"],
        "does_not_own": ["primary evidence research", "generic prose humanization", "DOCX/PDF rendering internals"],
        "trigger_examples": ["Refresh this old ebook into a publication-ready 2026 edition", "Build this evidence-backed report through manuscript, DOCX and PDF release readiness"],
        "negative_trigger_examples": ["Humanize this paragraph", "Rotate this PDF page"],
        "routing_signals": [[12, "longform publisher|publication workflow"], [11, "(ebook|white paper|playbook|handbook).*(refresh|publication-ready|release ready)"], [10, "canonical manuscript|publication-report\\.json"], [9, "refresh.*(ebook|report|guide)|derived artifacts?.*(docx|pdf)"]],
        "required_capabilities": [],
        "optional_capabilities": ["filesystem", "code_execution", "web", "files"],
    },
    "product-operator": {
        "release_status": "ACTIVE",
        "tier": "domain",
        "required_capabilities": [],
        "optional_capabilities": ["filesystem", "code_execution", "git", "connectors"],
    },
}


def default_entry(skill_id: str) -> dict:
    version, description = package_identity(skill_id)
    spec = OVERRIDES[skill_id]
    return {
        "id": skill_id,
        "version": version,
        "lifecycle": "active",
        "visibility": "private_canonical",
        "tier": spec["tier"],
        "alias_of": None,
        "description": description,
        "explicit_only": False,
        "owns": spec["owns"],
        "does_not_own": spec["does_not_own"],
        "trigger_examples": spec["trigger_examples"],
        "negative_trigger_examples": spec["negative_trigger_examples"],
        "inputs": ["user goal"],
        "outputs": ["skill-specific artifact"],
        "dependencies": [],
        "compatible_hosts": list(HOST_TARGETS),
        "host_targets": list(HOST_TARGETS),
        "required_capabilities": list(spec["required_capabilities"]),
        "optional_capabilities": list(spec["optional_capabilities"]),
        "execution_capabilities": ["standard"],
        "eval_suite": None,
        "release_status": spec["release_status"],
        "routing_signals": spec["routing_signals"],
    }


def pending_packages() -> list[str]:
    """Overrides whose package body has not landed on disk yet.

    The metadata for a release is written here before the package itself is
    staged, so an override without a SKILL.md is a package still in flight,
    not a broken repo. Skip it instead of crashing on the missing file.
    """
    return sorted(
        skill_id
        for skill_id in OVERRIDES
        if not (SKILLS / skill_id / "SKILL.md").is_file()
    )


def desired_registry(current: dict) -> dict:
    result = deepcopy(current)
    by_id = {entry["id"]: entry for entry in result["skills"]}
    pending = set(pending_packages())
    for skill_id, spec in OVERRIDES.items():
        if skill_id in pending:
            continue
        version, description = package_identity(skill_id)
        if skill_id not in by_id:
            entry = default_entry(skill_id)
            result["skills"].append(entry)
            by_id[skill_id] = entry
        entry = by_id[skill_id]
        entry["version"] = version
        entry["description"] = description
        entry["release_status"] = spec["release_status"]
        entry["host_targets"] = list(HOST_TARGETS)
        entry["compatible_hosts"] = list(HOST_TARGETS)
        entry["required_capabilities"] = list(spec["required_capabilities"])
        entry["optional_capabilities"] = list(spec["optional_capabilities"])
        if skill_id != "product-operator":
            for key in ("tier", "owns", "does_not_own", "trigger_examples", "negative_trigger_examples", "routing_signals"):
                entry[key] = deepcopy(spec[key])
    result["skills"] = sorted(result["skills"], key=lambda entry: entry["id"])
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    current = json.loads(REGISTRY.read_text(encoding="utf-8"))
    pending = pending_packages()
    if pending:
        print(f"PENDING: package not on disk, skipped: {', '.join(pending)}")
    desired = desired_registry(current)
    rendered = json.dumps(desired, ensure_ascii=False, indent=2) + "\n"
    existing = REGISTRY.read_text(encoding="utf-8")
    if args.check:
        if existing != rendered:
            print("FAIL: registry/skills.json is not synchronized")
            return 1
        print("OK: registry/skills.json synchronized")
        return 0
    REGISTRY.write_text(rendered, encoding="utf-8")
    print(f"OK: synchronized {len(OVERRIDES) - len(pending)} authoritative releases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
