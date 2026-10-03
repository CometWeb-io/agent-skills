#!/usr/bin/env python3
"""Generate host adapters and compatibility docs from registry sources of truth.

Writes:
  - docs/generated-skills-table.md
  - docs/generated-cursor-routing.mdc
  - docs/generated-compatibility-matrix.md
  - the skill catalog block in README.md (with registry/readme-catalog.json)
    and every skill count outside it (README_FACTS; a reworded sentence fails)
  - skills/<id>/agents/openai.yaml interface block, including a one-sentence
    Codex `default_prompt` that invokes the skill as `$skill-id`
  - extras/cursor-routing.mdc (compact Cursor rule; fallback when the full rule is absent)
  - extras/AGENTS.snippet.md (routing block for AGENTS.md hosts such as Codex)
  - the skill list in the `description` of .cursor-plugin/plugin.json and
    .claude-plugin/plugin.json (every other manifest field stays hand-owned;
    a description without the '(N packages): ...' tail fails)
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "skills.json"
HOSTS_FILE = ROOT / "registry" / "hosts.json"
SKILLS = ROOT / "skills"
OUT_DOCS = ROOT / "docs" / "generated-skills-table.md"
OUT_CURSOR = ROOT / "docs" / "generated-cursor-routing.mdc"
OUT_COMPAT = ROOT / "docs" / "generated-compatibility-matrix.md"

DISPLAY_NAMES = {
    "cometweb-context": "CometWeb Context",
    "evidence-researcher": "Evidence Researcher",
    "skill-orchestrator": "Skill Orchestrator",
    "skill-orchestrator-multiagent": "Skill Orchestrator Multiagent",
    "ai-council": "AI Council",
    "repo-to-roadmap": "Repo to Roadmap",
    "product-operator": "Product Operator",
    "release-readiness": "Release Readiness",
    "web-app-auditor": "Web App Auditor",
    "competitive-intelligence": "Competitive Intelligence",
    "product-teardown": "Product Teardown",
    "design-partner-finder": "Design Partner Finder",
    "customer-ops": "Customer Ops",
    "seo-geo-aeo-maxxing": "SEO GEO AEO Maxxing",
    "ai-humanize": "AI Humanize",
    "founder-led-sales-operator": "Founder-led Sales Operator",
    "research-program-operator": "Research Program Operator",
    "portfolio-operator": "Portfolio Operator",
    "longform-publisher": "Longform Publisher",
}

# Codex inserts `interface.default_prompt` when a user picks the skill, and its
# skill-creator reference asks for one short sentence that names the skill
# explicitly as `$skill-id`. Skills with a hand-tuned starting prompt are listed
# here; every other skill gets one built from its README catalog summary.
DEFAULT_PROMPTS = {
    "cometweb-context": (
        "Use $cometweb-context to refresh only the context my goal needs and return a "
        "ContextEnvelope with sources, facts, conflicts and gaps."
    ),
    "evidence-researcher": (
        "Use $evidence-researcher to build an Evidence Pack for my question, with verified "
        "sources, falsifier passes and a readiness verdict."
    ),
    "skill-orchestrator": (
        "Use $skill-orchestrator to plan and run the multi-skill workflow for my goal, "
        "handing results between steps as CW-AIP envelopes."
    ),
    "skill-orchestrator-multiagent": (
        "Use $skill-orchestrator-multiagent to run my multi-skill workflow with one "
        "isolated subagent per specialist step."
    ),
    "ai-council": (
        "Use $ai-council on my decision question with the smallest profile "
        "(LIGHT, STANDARD or DEEP) that protects the decision."
    ),
}
DEFAULT_PROMPT_MAX = 160
# A sentence end followed by more text: "Do X. Then Y." is two sentences.
_SENTENCE_BREAK = re.compile(r"[.!?]\s+\S")


def title_case_skill(skill_id: str) -> str:
    return DISPLAY_NAMES.get(skill_id, skill_id.replace("-", " ").title())


# Codex and ChatGPT list skills by `interface.short_description` and document it
# as 25-64 characters. A longer value is cut off in the skill picker, so the
# generator builds one that fits rather than slicing mid-word.
SHORT_DESCRIPTION_MIN = 25
SHORT_DESCRIPTION_MAX = 64


def _clip_words(text: str, limit: int) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    cut = text[: limit + 1].rsplit(" ", 1)[0].rstrip(" ;,.:")
    return cut if cut else text[:limit]


def short_description(entry: dict) -> str:
    """Whole `owns` items joined while they fit the Codex limit.

    When whole items stay under the minimum (or the first item alone is too
    long), the next item is let in and clipped at a word boundary. Only a skill
    with no usable `owns` falls back to the start of its description.
    """
    owns = list(entry.get("owns") or [])
    parts: list[str] = []
    for item in owns:
        if len("; ".join([*parts, item])) > SHORT_DESCRIPTION_MAX:
            break
        parts.append(item)
    text = "; ".join(parts)
    if len(text) < SHORT_DESCRIPTION_MIN and len(parts) < len(owns):
        # Too short with whole items only: let the next one in, clipped.
        text = _clip_words("; ".join([*parts, owns[len(parts)]]), SHORT_DESCRIPTION_MAX)
    if len(text) < SHORT_DESCRIPTION_MIN:
        text = _clip_words(entry.get("description", ""), SHORT_DESCRIPTION_MAX)
    return text


def _first_sentence(text: str) -> str:
    text = " ".join(text.split())
    match = _SENTENCE_BREAK.search(text)
    return text[: match.start() + 1] if match else text


def _invokes(skill_id: str, prompt: str) -> bool:
    return re.search(r"(?<![\w$-])\$" + re.escape(skill_id) + r"(?![\w-])", prompt) is not None


def default_prompt(entry: dict, summary: str | None = None) -> str:
    """One sentence that invokes the skill as `$skill-id`, at most DEFAULT_PROMPT_MAX chars.

    The catalog summary is a noun phrase ("Claim decomposition, source
    verification ..."), so it reads as "Use $id for <summary>." Without one, the
    first sentence of the description is used after a colon, which reads
    correctly whether it opens with a verb or a noun. Text is clipped at a word
    boundary, never mid-word. A hand-tuned prompt that loses its `$skill-id`,
    grows past the limit or becomes two sentences stops generation.
    """
    skill_id = entry["id"]
    if skill_id in DEFAULT_PROMPTS:
        prompt = " ".join(DEFAULT_PROMPTS[skill_id].split())
    else:
        source, joiner = (summary, " for ") if summary and summary.strip() else (
            _first_sentence(entry.get("description", "")), ": ")
        source = source.strip().rstrip(".!? ")
        # Lower-case an ordinary capitalised first word, but keep acronyms ("SEO").
        if len(source) > 1 and source[0].isupper() and source[1].islower():
            source = source[0].lower() + source[1:]
        lead = f"Use ${skill_id}{joiner}"
        body = _clip_words(source, DEFAULT_PROMPT_MAX - len(lead) - 1) if source else ""
        prompt = (lead + body + ".") if body else f"Use ${skill_id} for my request."
    problems = []
    if not _invokes(skill_id, prompt):
        problems.append(f"does not invoke ${skill_id}")
    if len(prompt) > DEFAULT_PROMPT_MAX:
        problems.append(f"is {len(prompt)} > {DEFAULT_PROMPT_MAX} characters")
    if _SENTENCE_BREAK.search(prompt):
        problems.append("is more than one sentence")
    if problems:
        raise SystemExit(f"{skill_id}: default_prompt " + "; ".join(problems) + f": {prompt!r}")
    return prompt


def render_openai_yaml(
    entry: dict, existing: str | None, skill_dir: Path | None = None, summary: str | None = None
) -> str:
    from adapter_metadata import merge_openai

    skill_id = entry["id"]
    display = title_case_skill(skill_id)
    interface = {
        "display_name": display,
        "short_description": short_description(entry),
        "default_prompt": default_prompt(entry, summary),
    }
    actual_dir = skill_dir or (SKILLS / skill_id)
    if (actual_dir / "assets" / "icon.svg").is_file():
        interface["icon_small"] = "./assets/icon.svg"
        interface["icon_large"] = "./assets/icon.svg"
    return merge_openai(entry, existing, interface)


def build_docs(skills: list[dict]) -> str:
    rows = [
        "# Generated skills table",
        "",
        "<!-- generated by tooling/generate_adapters.py — do not hand-edit -->",
        "",
        "| id | version | tier | lifecycle | release_status | desc_len | explicit_only |",
        "| --- | ---: | --- | --- | --- | ---: | --- |",
    ]
    for skill in skills:
        rows.append(
            f"| `{skill['id']}` | {skill['version']} | {skill.get('tier', '')} | "
            f"{skill.get('lifecycle', '')} | {skill.get('release_status', 'ACTIVE')} | "
            f"{len(skill.get('description', ''))} | {skill.get('explicit_only', False)} |"
        )
    return "\n".join(rows) + "\n"


README_BEGIN = "<!-- BEGIN GENERATED: skill catalog (tooling/generate_adapters.py) -->"
README_END = "<!-- END GENERATED: skill catalog -->"


def build_readme_catalog(skills: list[dict], catalog: dict) -> str:
    """Render the README catalog: grouping and summaries from the catalog file,
    the skill set, versions and status from the registry.

    The two files must name exactly the same skills. A skill added to the
    registry without a summary, or a summary left behind for a removed skill,
    is drift, so it stops generation instead of being skipped.
    """
    by_id = {entry["id"]: entry for entry in skills}
    listed: list[str] = [row["id"] for group in catalog["groups"] for row in group["skills"]]
    duplicates = sorted({sid for sid in listed if listed.count(sid) > 1})
    missing = sorted(set(by_id) - set(listed))
    unknown = sorted(set(listed) - set(by_id))
    if duplicates or missing or unknown:
        raise SystemExit(
            "registry/readme-catalog.json disagrees with registry/skills.json: "
            f"missing={missing} unknown={unknown} duplicated={duplicates}"
        )
    lines = [
        README_BEGIN,
        "<!-- Edit registry/readme-catalog.json or registry/skills.json, then run generate_adapters.py. -->",
        "",
        f"**{len(skills)} skills.** Versions come from each package's `VERSION`; "
        "the [compatibility matrix](docs/generated-compatibility-matrix.md) lists host support.",
    ]
    for group in catalog["groups"]:
        lines += ["", f"### {group['title']}", "", "| Skill | Use it for | Version |", "| --- | --- | ---: |"]
        for row in group["skills"]:
            entry = by_id[row["id"]]
            summary = row["summary"].strip()
            notes = []
            if entry.get("explicit_only"):
                notes.append("runs only when named")
            if entry.get("release_status") == "FROZEN":
                notes.append("frozen")
            if notes:
                summary += f" *({'; '.join(notes)})*"
            lines.append(f"| [`{row['id']}`](skills/{row['id']}/) | {summary} | {entry['version']} |")
    lines += ["", README_END]
    return "\n".join(lines)


def render_readme(current: str, skills: list[dict], catalog: dict) -> str:
    """Replace the marked catalog block in README.md; everything else is untouched."""
    start, end = current.find(README_BEGIN), current.find(README_END)
    if start < 0 or end < start:
        raise SystemExit(f"README.md has no catalog block; expected {README_BEGIN!r} ... {README_END!r}")
    rendered = current[:start] + build_readme_catalog(skills, catalog) + current[end + len(README_END):]
    return render_readme_facts(rendered, len(skills))


# Every place outside the catalog block where README.md states the skill count.
# Each pattern must still match: a reworded sentence would otherwise keep a stale
# number forever, because a substitution that finds nothing changes nothing.
README_FACTS = (
    ("skills badge", re.compile(r"(badge/skills-)\d+(-)")),
    ("opening sentence", re.compile(r"(contains )\d+( reusable skill packages)")),
    ("installer output example", re.compile(r"(`OK: )\d+( Claude Code skills installed in )")),
)


def render_readme_facts(text: str, count: int) -> str:
    missing = [name for name, pattern in README_FACTS if not pattern.search(text)]
    if missing:
        raise SystemExit(
            f"README.md no longer states the skill count in: {', '.join(missing)}. "
            "Restore the wording or update README_FACTS in tooling/generate_adapters.py."
        )
    for _, pattern in README_FACTS:
        text = pattern.sub(rf"\g<1>{count}\g<2>", text)
    return text


HOST_PLUGIN_MANIFESTS = (".claude-plugin/plugin.json", ".cursor-plugin/plugin.json")
PACKAGE_LIST = re.compile(r"\(\d+ packages\): .+\.$")


def host_manifests() -> list[Path]:
    return [ROOT / name for name in HOST_PLUGIN_MANIFESTS if (ROOT / name).is_file()]


def render_host_manifest(current: str, skills: list[dict]) -> str:
    """Keep the '(N packages): A, B, ...' tail of a host plugin description in step.

    A host manifest whose description lost that tail is an error: leaving it
    untouched would let the count and the list go stale without --check noticing.
    """
    data = json.loads(current)
    description = data.get("description")
    match = PACKAGE_LIST.search(description) if isinstance(description, str) else None
    if not match:
        raise SystemExit(
            "host plugin manifest description must end in '(N packages): A, B, ...'; "
            f"got {description!r}"
        )
    names = ", ".join(title_case_skill(entry["id"]) for entry in sorted(skills, key=lambda e: e["id"]))
    data["description"] = description[:match.start()] + f"({len(skills)} packages): {names}."
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def readme_file() -> Path:
    return ROOT / "README.md"


def readme_catalog_file() -> Path:
    return ROOT / "registry" / "readme-catalog.json"


def build_cursor(skills: list[dict]) -> str:
    lines = [
        "---",
        "description: Generated CometWeb Agent Skills routing (from registry/skills.json)",
        "globs:",
        "alwaysApply: true",
        "---",
        "",
        "<!-- generated by tooling/generate_adapters.py — do not hand-edit -->",
        "",
        "# CometWeb Agent Skills routing",
        "",
        "Load skills from the installed skills directory. Prefer **one primary skill**",
        "unless the user wants a multi-step workflow — then use `skill-orchestrator`",
        "(`execution_mode`: auto | single_thread | isolated_subagents).",
        "",
        "## Primary routing",
        "",
        "| Intent | Skill |",
        "| --- | --- |",
    ]
    for skill in skills:
        if skill.get("alias_of"):
            lines.append(f"| Alias for `{skill['alias_of']}` with isolated_subagents | `{skill['id']}` |")
            continue
        owns = ", ".join(skill.get("owns") or []) or skill["id"]
        lines.append(f"| {owns} | `{skill['id']}` |")

    lines.extend(["", "## Collision guardrails", ""])
    for skill in skills:
        if not skill.get("does_not_own"):
            continue
        denied = "; ".join(skill["does_not_own"])
        explicit = " Explicit invocation only." if skill.get("explicit_only") else ""
        lines.append(f"- **{skill['id']}** — does not own: {denied}.{explicit}")

    lines.extend(["", "## Trigger examples (from registry)", ""])
    for skill in skills:
        examples = skill.get("trigger_examples") or []
        negatives = skill.get("negative_trigger_examples") or []
        if not examples and not negatives:
            continue
        lines.append(f"### `{skill['id']}`")
        for example in examples:
            lines.append(f"- trigger: {example}")
        for example in negatives:
            lines.append(f"- do not trigger: {example}")
        lines.append("")
    return "\n".join(lines) + "\n"


GENERATED_MARK = "<!-- generated by tooling/generate_adapters.py from registry/skills.json — do not hand-edit -->"


def _routing_table(skills: list[dict]) -> list[str]:
    """One row per registry skill: short intent and id. Shared by every compact host artefact."""
    rows = ["| Intent | Skill |", "| --- | --- |"]
    for skill in skills:
        if skill.get("alias_of"):
            intent = f"`{skill['alias_of']}` with one subagent per step"
        else:
            intent = short_description(skill)
        notes = []
        if skill.get("explicit_only"):
            notes.append("only when named")
        if skill.get("release_status") == "FROZEN":
            notes.append("frozen")
        if notes:
            intent += f" ({'; '.join(notes)})"
        rows.append(f"| {intent} | `{skill['id']}` |")
    return rows


ROUTING_RULES = [
    "Prefer **one primary skill** per turn. For a multi-step workflow use",
    "`skill-orchestrator` (single thread) or `skill-orchestrator-multiagent` (one",
    "subagent per step), and hand outputs between skills as CW-AIP envelopes",
    "(`protocol/cw-interchange-v1.md` in the agent-skills repository).",
    "",
    "Before acting, read the chosen skill's `SKILL.md` and its \"Do not use\" clauses;",
    "run its deterministic scripts in `scripts/` when it ships them.",
]


def build_cursor_fallback(skills: list[dict]) -> str:
    lines = [
        "---",
        "description: Route CometWeb Agent Skills (compact rule generated from registry/skills.json; "
        "the full catalog with guardrails and trigger examples is docs/generated-cursor-routing.mdc).",
        "alwaysApply: true",
        "---",
        "",
        GENERATED_MARK,
        "",
        "# CometWeb Agent Skills routing",
        "",
        f"{len(skills)} skills, loaded from the installed skills directory.",
        "",
        *ROUTING_RULES,
        "",
        "## Primary routing",
        "",
        *_routing_table(skills),
    ]
    return "\n".join(lines) + "\n"


AGENTS_BEGIN = "<!-- BEGIN cometweb-agent-skills routing -->"
AGENTS_END = "<!-- END cometweb-agent-skills routing -->"


def build_agents_snippet(skills: list[dict]) -> str:
    """Routing block for hosts that read AGENTS.md (Codex) rather than a rule file.

    The installers never write a user's AGENTS.md; this block is pasted between
    its markers, so a later paste can replace exactly what an earlier one added.
    """
    lines = [
        "# AGENTS.md snippet: CometWeb Agent Skills routing",
        "",
        GENERATED_MARK,
        "",
        "Paste everything between the two markers into a project's `AGENTS.md`",
        "(Codex) or `CLAUDE.md`. To update, replace the old block between the same",
        "markers.",
        "",
        AGENTS_BEGIN,
        "## CometWeb Agent Skills",
        "",
        f"{len(skills)} skills are installed from CometWeb-io/agent-skills.",
        "",
        *ROUTING_RULES,
        "",
        *_routing_table(skills),
        AGENTS_END,
    ]
    return "\n".join(lines) + "\n"


# One implementation for the manifest package list; the old name stays importable.
render_plugin_manifest = render_host_manifest


def out_cursor_fallback() -> Path:
    return ROOT / "extras" / "cursor-routing.mdc"


def out_agents_snippet() -> Path:
    return ROOT / "extras" / "AGENTS.snippet.md"


def host_artifacts(skills: list[dict]) -> dict[Path, str]:
    """Compact routing artefacts and host plugin manifests, all from the registry."""
    artifacts = {
        out_cursor_fallback(): build_cursor_fallback(skills),
        out_agents_snippet(): build_agents_snippet(skills),
    }
    # A reduced tree without host manifests has nothing to keep in step.
    for path in host_manifests():
        artifacts[path] = render_host_manifest(path.read_text(encoding="utf-8"), skills)
    return artifacts


def _support(entry: dict, host: dict, *, format_ok: bool) -> str:
    """Declared host-profile support only — never verified runtime acceptance."""
    from compatibility import compute_support

    result = compute_support(entry, host, format_ok=format_ok)
    if result["format"] == "UNSUPPORTED":
        return "UNSUPPORTED"
    return str(result["runtime"])


def _targets(entry: dict) -> set[str]:
    return set(entry.get("host_targets") or entry.get("compatible_hosts") or [])


def build_compatibility_matrix(skills: list[dict], hosts: dict) -> str:
    target_hosts = [
        "chatgpt", "openai-codex", "claude-code", "cursor",
        "qwen-code", "qoder", "lingma", "alibaba-skills-portal",
    ]
    lines = [
        "# Generated compatibility matrix",
        "",
        "<!-- generated by tooling/generate_adapters.py — do not hand-edit -->",
        "",
        "Cells are **declared host-profile support** (`format` + `declared_runtime`), not live host or model proof. "
        "`FULL` = required capabilities present; `DEGRADED` = optional capability missing; "
        "`UNSUPPORTED` = required capability or format contract missing; `—` = not targeted. "
        "`verified_runtime_acceptance` stays `not_assessed` until an explicit host/model eval records otherwise; CI never promotes declared support to verified acceptance.",
        "",
        "| Skill | " + " | ".join(target_hosts) + " |",
        "| --- | " + " | ".join(["---"] * len(target_hosts)) + " |",
    ]
    for entry in skills:
        row = [f"`{entry['id']}`"]
        targets = _targets(entry)
        skill_dir = SKILLS / entry["id"]
        desc = entry.get("description", "")
        for host_name in target_hosts:
            if host_name not in targets:
                row.append("—")
                continue
            host = hosts[host_name]
            max_len = host.get("description_max")
            format_ok = max_len is None or len(desc) <= max_len
            if host.get("agents_file") and not (skill_dir / host["agents_file"]).is_file():
                format_ok = False
            row.append(_support(entry, host, format_ok=format_ok))
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines) + "\n"


def catalog_summaries() -> dict[str, str]:
    """README catalog summaries by skill id; empty for a tree without the catalog."""
    path = readme_catalog_file()
    if not path.is_file():
        return {}
    catalog = json.loads(path.read_text(encoding="utf-8"))
    return {row["id"]: row["summary"] for group in catalog["groups"] for row in group["skills"]}


def write_openai_yamls(skills: list[dict]) -> list[Path]:
    written: list[Path] = []
    summaries = catalog_summaries()
    for entry in skills:
        skill_dir = SKILLS / entry["id"]
        agents = skill_dir / "agents"
        agents.mkdir(parents=True, exist_ok=True)
        path = agents / "openai.yaml"
        existing = path.read_text(encoding="utf-8") if path.is_file() else None
        content = render_openai_yaml(entry, existing, skill_dir=skill_dir, summary=summaries.get(entry["id"]))
        if existing != content:
            path.write_text(content, encoding="utf-8")
            written.append(path)
    return written


def hosts_file() -> Path:
    return ROOT / "registry" / "hosts.json"


def out_compat() -> Path:
    return ROOT / "docs" / "generated-compatibility-matrix.md"


def validate_sources(skills: list[dict]) -> None:
    """Reject an incomplete or redirected source tree before writing anything.

    Generation rewrites files in place across every skill, so a defect found
    halfway through would leave the tree half-updated. Everything is checked
    up front and the run aborts without touching disk.
    """
    seen: set[str] = set()
    for entry in skills:
        skill_id = entry.get("id", "")
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", skill_id or ""):
            raise SystemExit(f"invalid skill id: {skill_id!r}")
        if skill_id in seen:
            raise SystemExit(f"duplicate registry entry: {skill_id}")
        seen.add(skill_id)

        skill_dir = SKILLS / skill_id
        if not skill_dir.is_dir():
            raise SystemExit(f"registry lists {skill_id} but it is not on disk")
        for rel in ("SKILL.md", "VERSION"):
            path = skill_dir / rel
            if not path.is_file():
                raise SystemExit(f"{skill_id}: missing {rel}")
            if path.is_symlink():
                raise SystemExit(f"{skill_id}: {rel} must not be a symlink")
        agents = skill_dir / "agents"
        if agents.is_symlink():
            raise SystemExit(f"{skill_id}: agents/ must not be a symlink")
        on_disk = (skill_dir / "VERSION").read_text(encoding="utf-8").strip()
        if on_disk != entry.get("version"):
            raise SystemExit(
                f"{skill_id}: registry version {entry.get('version')!r} != VERSION {on_disk!r}"
            )


def expected_artifacts(skills: list[dict]) -> dict[Path, str]:
    artifacts = {
        OUT_DOCS: build_docs(skills),
        OUT_CURSOR: build_cursor(skills),
        **host_artifacts(skills),
    }
    # The host matrix needs a host registry. A tree that declares no hosts is a
    # reduced but valid layout, so generate the rest rather than failing.
    hosts_path = hosts_file()
    if hosts_path.is_file():
        hosts = json.loads(hosts_path.read_text(encoding="utf-8"))["hosts"]
        artifacts[out_compat()] = build_compatibility_matrix(skills, hosts)
    # Same reasoning for the README catalog: a reduced tree without the
    # catalog file has nothing to render, which is not an error.
    catalog_path, readme = readme_catalog_file(), readme_file()
    if catalog_path.is_file():
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        current = readme.read_text(encoding="utf-8") if readme.is_file() else ""
        artifacts[readme] = render_readme(current, skills, catalog)
    summaries = catalog_summaries()
    for entry in skills:
        path = SKILLS / entry["id"] / "agents" / "openai.yaml"
        existing = path.read_text(encoding="utf-8") if path.is_file() else None
        artifacts[path] = render_openai_yaml(
            entry, existing, skill_dir=SKILLS / entry["id"], summary=summaries.get(entry["id"])
        )
    return artifacts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="exit 1 if generated files would change")
    parser.add_argument("--skip-openai", action="store_true", help="do not rewrite agents/openai.yaml")
    args = parser.parse_args()
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    skills = data["skills"]
    validate_sources(skills)

    if args.check:
        artifacts = expected_artifacts(skills)
        if args.skip_openai:
            artifacts = {
                path: text for path, text in artifacts.items()
                if path in {OUT_DOCS, OUT_CURSOR, out_compat(), readme_file(), *host_artifacts(skills)}
            }
        changed = []
        for path, expected in artifacts.items():
            if not path.is_file() or path.read_text(encoding="utf-8") != expected:
                changed.append(str(path.relative_to(ROOT)))
        if changed:
            raise SystemExit("generated adapters out of date:\n- " + "\n- ".join(changed))
        print("OK: generate_adapters --check")
        return

    # The compatibility matrix reads whether each agents/openai.yaml exists, so
    # write those first: otherwise a new skill is rendered UNSUPPORTED on the
    # first run and only corrected on a second, and --check fails in between.
    written = [] if args.skip_openai else write_openai_yamls(skills)
    OUT_DOCS.parent.mkdir(parents=True, exist_ok=True)
    OUT_DOCS.write_text(build_docs(skills), encoding="utf-8")
    OUT_CURSOR.write_text(build_cursor(skills), encoding="utf-8")
    written_docs = [OUT_DOCS, OUT_CURSOR]
    for path, text in host_artifacts(skills).items():
        if not path.is_file() or path.read_text(encoding="utf-8") != text:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            written_docs.append(path)
    hosts_path = hosts_file()
    if hosts_path.is_file():
        hosts = json.loads(hosts_path.read_text(encoding="utf-8"))["hosts"]
        compat = out_compat()
        compat.write_text(build_compatibility_matrix(skills, hosts), encoding="utf-8")
        written_docs.append(compat)
    if readme_catalog_file().is_file():
        catalog = json.loads(readme_catalog_file().read_text(encoding="utf-8"))
        readme = readme_file()
        readme.write_text(render_readme(readme.read_text(encoding="utf-8"), skills, catalog), encoding="utf-8")
        written_docs.append(readme)
    msg = "OK: wrote " + ", ".join(str(d.relative_to(ROOT)) for d in written_docs)
    if written:
        msg += f", {len(written)} openai.yaml"
    print(msg)


if __name__ == "__main__":
    main()
