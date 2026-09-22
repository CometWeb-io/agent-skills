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
        "routing_signals": [[12, "longform publisher|publication workflow"], [11, "(ebook|white paper|playbook|handbook|report).*(refresh|publication-ready|release ready)"], [10, "canonical manuscript|publication-report\\.json"], [10, "through manuscript|manuscript.*(docx|pdf)"], [9, "refresh.*(ebook|report|guide)|derived artifacts?.*(docx|pdf)"]],
        "required_capabilities": [],
        "optional_capabilities": ["filesystem", "code_execution", "web", "files"],
    },
    "product-operator": {
        "release_status": "ACTIVE",
        "tier": "domain",
        "required_capabilities": [],
        "optional_capabilities": ["filesystem", "code_execution", "git", "connectors"],
    },
    "artifact-acceptance": {
        "release_status": "ACTIVE",
        "tier": "domain",
        "owns": ["knowledge-artifact acceptance gates", "evidence-backed artifact verdicts", "candidate and contract traceability"],
        "does_not_own": ["software release verdicts", "initial editorial review", "consequential strategic decisions"],
        "trigger_examples": ["Is this report ready to publish against its brief?", "Run the final acceptance gate on this knowledge artifact"],
        "negative_trigger_examples": ["Is this software release ready?", "Review this article for the first time"],
        "routing_signals": [[12, "artifact acceptance|acceptance gate.*(artifact|report|content)"], [10, "ready.*(publish|deliver).*brief"], [9, "final (artifact|knowledge) gate"], [8, "artifact.*(READY_WITH_CONTROLS|NOT_READY|DEFER)"], [7, "acceptance contract.*evidence"]],
        "required_capabilities": [],
        "optional_capabilities": ["filesystem", "code_execution", "files"],
    },
    "benchmark-curator": {
        "release_status": "ACTIVE",
        "tier": "foundation",
        "owns": ["benchmark and eval corpus design", "holdout and contamination controls", "benchmark revision hashes"],
        "does_not_own": ["model experiment execution", "rubric design", "skill editing"],
        "trigger_examples": ["Curate a clean holdout benchmark for this skill", "Design the discovery and regression corpus"],
        "negative_trigger_examples": ["Run the model experiment and claim lift", "Design the grading rubric"],
        "routing_signals": [[20, "curate.*(clean )?holdout benchmark"], [12, "benchmark curator|benchmark.*corpus"], [10, "golden set|regression corpus|challenge set"], [9, "holdout.*(contamination|leakage|clean)"], [8, "eval dataset.*(taxonomy|provenance|duplicate)"], [7, "freeze.*benchmark.*hash"]],
        "required_capabilities": [],
        "optional_capabilities": ["filesystem", "code_execution"],
    },
    "brief-architect": {
        "release_status": "ACTIVE",
        "tier": "domain",
        "owns": ["artifact brief and execution contract", "observable acceptance criteria", "evidence policy and handoff fields"],
        "does_not_own": ["final artifact production", "broad product discovery", "consequential strategic decisions"],
        "trigger_examples": ["Turn this vague request into an executable brief", "Define acceptance criteria before we write the report"],
        "negative_trigger_examples": ["Write the final article", "Choose the product strategy"],
        "routing_signals": [[20, "vague request.*executable brief|acceptance criteria before"], [12, "brief architect|artifact brief"], [10, "turn this vague request into a brief"], [9, "acceptance criteria before (writing|research|production)"], [8, "evidence policy.*handoff"], [7, "underspecified.*(artifact|report|guide)"]],
        "required_capabilities": [],
        "optional_capabilities": ["filesystem", "code_execution", "files"],
    },
    "content-reviewer": {
        "release_status": "ACTIVE",
        "tier": "domain",
        "owns": ["constructive content review", "evidence-backed editorial findings", "review coverage and repair direction"],
        "does_not_own": ["adversarial roasting", "full content rewrites", "final publication acceptance"],
        "trigger_examples": ["Review this draft against its brief", "Give me actionable editorial QA before publication"],
        "negative_trigger_examples": ["Brutally roast this landing page", "Rewrite the whole article"],
        "routing_signals": [[12, "content reviewer|editorial (review|qa)"], [10, "review this (draft|article|report).*brief"], [9, "pre.publication review|actionable editorial findings"], [8, "content.*(clarity|specificity|internal consistency).*review"], [7, "constructive review.*content"]],
        "required_capabilities": [],
        "optional_capabilities": ["filesystem", "code_execution", "web", "files"],
    },
    "content-roaster": {
        "release_status": "ACTIVE",
        "tier": "domain",
        "owns": ["adversarial content review", "proof-debt and claim-pressure diagnosis", "repair verification contracts"],
        "does_not_own": ["scientific peer review", "repository/code critique", "rewrite-only editing"],
        "trigger_examples": ["Roast this landing page with evidence", "Red-team the claims and objections in this offer"],
        "negative_trigger_examples": ["Peer-review this scientific manuscript", "Audit the repository code"],
        "routing_signals": [[14, "content roaster|content roast|roast.*(landing page|offer|article|copy)"], [12, "red.team.*(content|copy|offer)"], [10, "adversarial.*(content|marketing|sales) review"], [9, "proof debt|claim.*counterevidence.*repair"], [8, "brutal.*critique.*(copy|content|page)"]],
        "required_capabilities": [],
        "optional_capabilities": ["filesystem", "code_execution", "web", "files"],
    },
    "content-writer": {
        "release_status": "ACTIVE",
        "tier": "domain",
        "owns": ["evidence-aware content production", "claim-discipline ledger", "reader-facing informational artifacts"],
        "does_not_own": ["persuasion-first campaign copy", "primary evidence research", "publication release orchestration"],
        "trigger_examples": ["Write the evidence-backed guide from this brief", "Create the reader-facing report without inventing claims"],
        "negative_trigger_examples": ["Humanize this paragraph only", "Run the primary research first"],
        "routing_signals": [[12, "content writer|write.*(evidence.backed|informational) (guide|report|article)"], [10, "create.*reader.facing (artifact|report|guide)"], [9, "write.*from this brief.*(article|report|documentation)"], [8, "claim.discipline.*(draft|content)"], [7, "evidence.aware.*(prose|content)"]],
        "required_capabilities": [],
        "optional_capabilities": ["filesystem", "code_execution", "web", "files"],
    },
    "feedback-integrator": {
        "release_status": "ACTIVE",
        "tier": "foundation",
        "owns": ["recurrent failure pattern synthesis", "evidence-backed improvement proposals", "regression test proposals"],
        "does_not_own": ["silent self-modification", "single-signal generalization", "product or research analytics"],
        "trigger_examples": ["Turn repeated skill failures into a regression plan", "Run a retrospective across these quality incidents"],
        "negative_trigger_examples": ["Patch the skill silently from one correction", "Analyze product retention"],
        "routing_signals": [[20, "retrospective.*quality incidents"], [12, "feedback integrator|integrate.*feedback"], [10, "repeated.*(skill failure|quality failure|user correction)"], [9, "retrospective.*(skill|quality workflow)"], [8, "failure pattern.*regression test"], [7, "improve reliability.*repeated incidents"]],
        "required_capabilities": [],
        "optional_capabilities": ["filesystem", "code_execution", "git"],
    },
    "quality-loop-operator": {
        "release_status": "ACTIVE",
        "tier": "foundation",
        "owns": ["quality workflow state and sequencing", "specialist handoffs and revalidation", "quality rollout lifecycle"],
        "does_not_own": ["general multi-skill orchestration", "consequential strategy decisions", "software production-readiness verdicts"],
        "trigger_examples": ["Run the full content quality loop", "Resume this quality workflow from the last accepted stage"],
        "negative_trigger_examples": ["Orchestrate an unrelated product workflow", "Give a software release GO/NO_GO"],
        "routing_signals": [[20, "full content quality loop"], [14, "quality loop operator|quality workflow"], [12, "full quality loop|resume.*quality workflow"], [10, "brief.*review.*roast.*repair.*acceptance"], [9, "quality.*(revalidation|rollout|rollback)"], [8, "coordinate quality specialists"]],
        "required_capabilities": [],
        "optional_capabilities": ["filesystem", "code_execution", "git", "web", "files"],
    },
    "repair-operator": {
        "release_status": "ACTIVE",
        "tier": "domain",
        "owns": ["finding-to-repair planning", "authorized bounded repairs", "fresh repair verification"],
        "does_not_own": ["initial broad audit", "inventing new requirements", "production release verdicts"],
        "trigger_examples": ["Turn these review findings into the smallest repair set", "Apply the authorized fixes and verify they close the root cause"],
        "negative_trigger_examples": ["Audit the whole repo from scratch", "Decide whether the release is ready"],
        "routing_signals": [[20, "authorized fixes.*verify.*root cause"], [12, "repair operator|repair set"], [10, "fix these findings.*(root cause|verify)"], [9, "convert.*findings.*(repair|patch)"], [8, "authorized.*(repair|fix).*fresh verification"], [7, "close.*finding.*without regressions"]],
        "required_capabilities": [],
        "optional_capabilities": ["filesystem", "code_execution", "git"],
    },
    "repo-roaster": {
        "release_status": "ACTIVE",
        "tier": "domain",
        "owns": ["adversarial repository review", "critical-invariant and reachability analysis", "executable engineering repair contracts"],
        "does_not_own": ["whole-project roadmapping", "runtime web QA", "final production release verdicts"],
        "trigger_examples": ["Roast this repository with file and test evidence", "Red-team the critical invariants and failure paths in this codebase"],
        "negative_trigger_examples": ["Create the whole-project roadmap", "Decide whether the release can ship"],
        "routing_signals": [[14, "repo roaster|repository roast|roast.*(repo|codebase)"], [12, "red.team.*(repository|codebase|software)"], [10, "adversarial.*(repository|codebase) review"], [9, "critical invariant.*(repo|code)"], [8, "file.*symbol.*reachability.*blast radius"]],
        "required_capabilities": [],
        "optional_capabilities": ["filesystem", "code_execution", "git"],
    },
    "rubric-designer": {
        "release_status": "ACTIVE",
        "tier": "foundation",
        "owns": ["evaluation rubric design", "observable pass/fail evidence floors", "rubric revision hashes"],
        "does_not_own": ["judging the candidate", "writing the artifact", "running empirical skill benchmarks"],
        "trigger_examples": ["Design and freeze a review rubric before evaluation", "Define blocker rules and evidence floors for this benchmark"],
        "negative_trigger_examples": ["Score the candidate using the rubric", "Run the A/B experiment"],
        "routing_signals": [[20, "define blocker rules.*evidence floors"], [12, "rubric designer|design.*(evaluation|review) rubric"], [10, "freeze.*rubric|rubric hash"], [9, "pass/fail.*(criteria|semantics)"], [8, "evidence floor.*(rubric|scorecard)"], [7, "blocker rules.*evaluation"]],
        "required_capabilities": [],
        "optional_capabilities": ["filesystem", "code_execution"],
    },
    "science-roaster": {
        "release_status": "ACTIVE",
        "tier": "domain",
        "owns": ["adversarial scientific peer review", "claim/evidence and validity analysis", "methodological repair verification"],
        "does_not_own": ["generic content critique", "repository/code review", "research-program planning"],
        "trigger_examples": ["Reviewer-2 roast this manuscript", "Red-team the methods, estimand, and validity of this study"],
        "negative_trigger_examples": ["Critique this marketing article", "Audit the software repository"],
        "routing_signals": [[14, "science roaster|scientific peer review|reviewer.?2"], [12, "roast.*(manuscript|paper|study|protocol)"], [10, "red.team.*(scientific|study|method)"], [9, "estimand.*validity.*(review|critique)"], [8, "methodological.*(repair|counterevidence)"]],
        "required_capabilities": [],
        "optional_capabilities": ["filesystem", "code_execution", "web", "files"],
    },
    "skill-auditor": {
        "release_status": "ACTIVE",
        "tier": "foundation",
        "owns": ["skill package audits", "routing, portability, and contract review", "package and supply-chain hygiene"],
        "does_not_own": ["editing the audited skill", "empirical behavioral benchmarking", "production release verdicts"],
        "trigger_examples": ["Audit this Agent Skill package for routing and portability risks", "Quality-check the skill library before publication"],
        "negative_trigger_examples": ["Edit the skill instructions", "Benchmark model behavior with and without the skill"],
        "routing_signals": [[20, "quality.check.*skill library"], [12, "skill auditor|audit.*(agent skill|skill package|skill library)"], [10, "skill.*(routing|portability|package hygiene).*audit"], [9, "audit.*skill.*(trigger|reference|eval)"], [8, "supply.chain.*skill|public.*skill.*hardening"], [7, "skill registry.*drift.*audit"]],
        "required_capabilities": [],
        "optional_capabilities": ["filesystem", "code_execution", "git"],
    },
    "skill-evaluator": {
        "release_status": "ACTIVE",
        "tier": "foundation",
        "owns": ["skill experiment design", "behavioral lift and resource measurement", "host and model comparisons"],
        "does_not_own": ["static package audits", "editing the skill", "universal superiority claims"],
        "trigger_examples": ["Measure whether this skill improves behavior over the baseline", "Design a fair A/B eval for the new skill version"],
        "negative_trigger_examples": ["Static-audit the package", "Claim this skill is universally best from one run"],
        "routing_signals": [[20, "measure whether this skill improves behavior over the baseline"], [12, "skill evaluator|evaluate.*skill"], [10, "benchmark.*(skill|model behavior)|A/B.*skill"], [9, "measure.*(behavioral lift|trigger precision|recall)"], [8, "compare.*(no.skill|baseline).*skill"], [7, "host/model.*(comparison|experiment)"]],
        "required_capabilities": [],
        "optional_capabilities": ["filesystem", "code_execution", "git"],
    },
}


def default_entry(skill_id: str) -> dict:
    version, description = package_identity(skill_id)
    spec = OVERRIDES[skill_id]
    return {
        "id": skill_id,
        "version": version,
        "lifecycle": "active",
        "visibility": "public_canonical",
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
