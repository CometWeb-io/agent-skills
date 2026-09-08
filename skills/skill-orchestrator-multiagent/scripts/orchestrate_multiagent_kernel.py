#!/usr/bin/env python3
"""Build isolated subagent task payloads for skill-orchestrator-multiagent."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from orchestrate_kernel import WorkflowPlan, WorkflowStep, plan_workflow

SKILL_ROOT_HINTS = (
    "~/.cursor/skills/{skill}",
    "~/.claude/skills/{skill}",
    "platforms/agent-skills/skills/{skill}",
)

SUBAGENT_TYPE_BY_SKILL: dict[str, str] = {
    "evidence-researcher": "generalPurpose",
    "ai-council": "generalPurpose",
    "product-operator": "generalPurpose",
    "web-app-auditor": "generalPurpose",
    "release-readiness": "generalPurpose",
    "repo-to-roadmap": "explore",
    "competitive-intelligence": "generalPurpose",
    "product-teardown": "generalPurpose",
    "design-partner-finder": "generalPurpose",
    "customer-ops": "generalPurpose",
    "seo-geo-aeo-maxxing": "generalPurpose",
    "ai-humanize": "generalPurpose",
}


@dataclass(frozen=True)
class SubagentTask:
    step_index: int
    step_total: int
    skill: str
    subagent_type: str
    description: str
    prompt: str
    envelope_out: str | None
    run_in_background: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _skill_paths(skill: str) -> str:
    return "\n".join(f"- `{p.format(skill=skill)}`" for p in SKILL_ROOT_HINTS)


def _forbidden_outputs(skill: str) -> str:
    rules = {
        "evidence-researcher": "Do NOT issue GO/NO-GO, product priorities, or Council verdicts.",
        "ai-council": "Do NOT skip decision-specific re-verification. Do NOT run Evidence Researcher work inline.",
        "web-app-auditor": "Do NOT issue ship/release verdicts — findings only.",
        "release-readiness": "Do NOT run without pinned RC/build + environment in the prompt context.",
        "product-operator": "Do NOT replace Release Readiness for pinned RC gates.",
    }
    return rules.get(skill, "Stay inside this skill's boundary only.")


def build_subagent_task(
    *,
    step: WorkflowStep,
    step_index: int,
    step_total: int,
    goal: str,
    prior_envelopes: list[dict[str, Any]],
    workspace_root: str | None = None,
) -> SubagentTask:
    subagent_type = SUBAGENT_TYPE_BY_SKILL.get(step.skill, "generalPurpose")
    envelope_line = (
        f"Required CW-AIP output: `{step.envelope_out}`."
        if step.envelope_out
        else "Emit the skill's standard output contract."
    )
    prior_block = json.dumps(prior_envelopes, indent=2, ensure_ascii=False) if prior_envelopes else "[]"
    ws = workspace_root or "<host workspace root>"

    prompt = f"""You are an **isolated subagent** for CometWeb skill `{step.skill}` only.

## Hard rules
- Execute **only** `{step.skill}`. Do not run other skills or their workflows.
- {_forbidden_outputs(step.skill)}
- Read and follow the full skill entrypoint before acting.
- {envelope_line}

## Skill locations (read SKILL.md from the first path that exists)
{_skill_paths(step.skill)}

## Workflow context
- Workspace root: {ws}
- Overall user goal: {goal}
- Step {step_index}/{step_total}: {step.purpose}
- Prior CW-AIP envelopes (inputs): {prior_block}

## Return format (mandatory)
1. **Step status** — completed | blocked | partial
2. **CW-AIP envelope** — valid JSON for `{step.envelope_out or "ArtifactEnvelope"}`
3. **Gaps/blockers** — bullet list
4. **Do not** include downstream skill work or verdicts outside this skill's remit
"""

    description = f"CW step {step_index}/{step_total}: {step.skill}"
    return SubagentTask(
        step_index=step_index,
        step_total=step_total,
        skill=step.skill,
        subagent_type=subagent_type,
        description=description,
        prompt=prompt,
        envelope_out=step.envelope_out,
        run_in_background=False,
    )


def build_multiagent_plan(goal: str, workspace_root: str | None = None) -> dict[str, Any]:
    plan = plan_workflow(goal)
    tasks = [
        build_subagent_task(
            step=step,
            step_index=i,
            step_total=len(plan.steps),
            goal=goal,
            prior_envelopes=[],
            workspace_root=workspace_root,
        ).to_dict()
        for i, step in enumerate(plan.steps, start=1)
    ]
    return {
        "execution_mode": "multiagent",
        "parent_role": "orchestrator_only",
        "plan": plan.to_dict(),
        "subagent_tasks": tasks,
        "parent_must_not": [
            "Execute domain skill workflows in the parent thread.",
            "Collapse multiple steps into one model pass.",
            "Issue Council or Release verdicts without a dedicated ai-council/release-readiness subagent run.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build multiagent workflow task payloads")
    parser.add_argument("goal", help="User goal in plain language")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    parser.add_argument("--workspace-root", default="", help="Host workspace root path")
    args = parser.parse_args()

    payload = build_multiagent_plan(
        args.goal,
        workspace_root=args.workspace_root or None,
    )

    if args.json:
        json.dump(payload, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
        return

    print(f"mode: {payload['execution_mode']}")
    print(f"archetype: {payload['plan']['archetype']}")
    for task in payload["subagent_tasks"]:
        print(f"  {task['step_index']}. Task({task['subagent_type']}) -> {task['skill']}")


if __name__ == "__main__":
    main()
