#!/usr/bin/env python3
"""Deterministic workflow archetype selection for skill-orchestrator."""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class WorkflowStep:
    skill: str
    purpose: str
    envelope_out: str | None = None
    read_skill: bool = True


@dataclass(frozen=True)
class WorkflowPlan:
    archetype: str
    goal_summary: str
    steps: list[WorkflowStep]
    boundaries: list[str] = field(default_factory=list)
    single_skill_alternative: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "archetype": self.archetype,
            "goal_summary": self.goal_summary,
            "steps": [asdict(s) for s in self.steps],
            "boundaries": self.boundaries,
            "single_skill_alternative": self.single_skill_alternative,
        }


def normalize(text: str) -> str:
    return unicodedata.normalize("NFKC", text).casefold()


# (pattern, archetype) — first match wins; order matters (specific before generic).
ARCHETYPE_RULES: list[tuple[str, str]] = [
    (r"evidence.*(then|→|->|potem).*(council|rad[ęe])|(council|rad[ęe]).*after.*evidence", "research_then_council"),
    (r"verify.*claims.*(council|rad[ęe])|research.*(then|→|->|potem).*(go|no-go|decision)", "research_then_council"),
    (r"przepu[śs][ćc]? przez rad[ęe].*po|najpierw.*dowod.*rad", "research_then_council"),
    (r"audit.*(then|→|->|potem).*(release|ship|gate|readiness)", "audit_then_release"),
    (r"web app audit.*release|qa.*(then|→|->).*(release|ship)", "audit_then_release"),
    (r"evidence.*(then|→|->|potem).*(operator|weekly|sprint)", "research_then_operator"),
    (r"competitor.*(then|→|->|potem).*(council|rad[ęe]|decision)", "competitive_then_council"),
    (r"orchestrat|sequence.*skill|multi.?step|full workflow|ca[łl][yąa] workflow", "orchestrated_goal"),
    (r"zr[oó]b wszystko|od researchu do (decyzji|rady)|end.to.end", "orchestrated_goal"),
    (r"which skill|help me pick|not sure what I need|nie wiem kt[oó]ry skill", "disambiguate_only"),
]

SINGLE_SKILL_HINTS: list[tuple[str, str]] = [
    (r"evidence pack only|only research|tylko dowod", "evidence-researcher"),
    (r"only council|tylko rad[ęe]|@ai-council", "ai-council"),
    (r"weekly|this week|co robimy", "product-operator"),
    (r"whole repo|baseline roadmap", "repo-to-roadmap"),
    (r"release candidate|rc[\s.-]?\d|build v?\d", "release-readiness"),
    (r"click.?through|web app audit", "web-app-auditor"),
]

ARCHETYPE_STEPS: dict[str, list[tuple[str, str, str | None]]] = {
    "research_then_council": [
        ("evidence-researcher", "Build Evidence Pack for material claims", "EvidenceEnvelope"),
        ("ai-council", "Deliberate on decision question using accepted evidence", "DecisionHandoff"),
    ],
    "research_then_operator": [
        ("evidence-researcher", "Verify material claims blocking weekly priorities", "EvidenceEnvelope"),
        ("product-operator", "Reconcile state and output NOW/NEXT/LATER", "SpecialistHandoff"),
    ],
    "audit_then_release": [
        ("web-app-auditor", "Produce findings with evidence", "FindingEnvelope"),
        ("release-readiness", "Gate pinned RC/build with audit findings", "DecisionHandoff"),
    ],
    "competitive_then_council": [
        ("competitive-intelligence", "Normalize competitor delta with evidence", "SnapshotMetadata"),
        ("evidence-researcher", "Verify material claims if gaps remain", "EvidenceEnvelope"),
        ("ai-council", "Strategic response decision", "DecisionHandoff"),
    ],
    "orchestrated_goal": [
        ("evidence-researcher", "Verify material factual claims first", "EvidenceEnvelope"),
        ("product-operator", "Reconcile product state if roadmap/ops context applies", None),
        ("ai-council", "Material strategic decision if user goal requires verdict", "DecisionHandoff"),
    ],
    "disambiguate_only": [],
}

BOUNDARIES: dict[str, list[str]] = {
    "research_then_council": [
        "Evidence Researcher stops at Evidence Pack — no GO/NO-GO.",
        "AI Council re-verifies decision-specific evidence; verified_for_research ≠ verified_for_decision.",
        "Load each step's SKILL.md fully before executing that step.",
    ],
    "research_then_operator": [
        "Evidence Researcher does not prioritize or sequence product work.",
        "Product Operator owns NOW/NEXT/LATER after evidence is admitted.",
    ],
    "audit_then_release": [
        "Release Readiness requires pinned RC/build + environment.",
        "Audit findings feed gates; score cannot override hard gates.",
    ],
    "competitive_then_council": [
        "Competitive Intelligence separates observation from implication.",
        "Council only when the user goal includes a material strategic decision.",
    ],
    "orchestrated_goal": [
        "Skip steps that do not apply — kernel plan is a default, not mandatory depth.",
        "Never collapse Evidence Pack into Council verdict in one pass.",
        "Council step runs only when the goal implies a material decision.",
    ],
    "disambiguate_only": [
        "Emit routing recommendation only — do not execute domain skills in this turn unless user confirms.",
    ],
}

DEFAULT_ORCHESTRATED_BOUNDARIES = BOUNDARIES["orchestrated_goal"]


def _match_first(text: str, rules: list[tuple[str, str]]) -> str | None:
    for pattern, label in rules:
        if re.search(pattern, text, re.IGNORECASE):
            return label
    return None


def _goal_implies_council(text: str) -> bool:
    return bool(
        re.search(
            r"council|rad[ęe]|go.?no.?go|decision|decyzj|strategic|material options|pricing decision",
            text,
            re.IGNORECASE,
        )
    )


def _goal_implies_release(text: str) -> bool:
    return bool(re.search(r"release|ship|rc[\s.-]?\d|build v?\d|gate|readiness", text, re.IGNORECASE))


def _goal_implies_audit(text: str) -> bool:
    return bool(re.search(r"audit|qa|click.?through|web app", text, re.IGNORECASE))


def _goal_implies_operator(text: str) -> bool:
    return bool(re.search(r"weekly|this week|roadmap|notion|github|priority|operator", text, re.IGNORECASE))


def plan_workflow(goal: str) -> WorkflowPlan:
    norm = normalize(goal.strip())
    if not norm:
        raise ValueError("goal must not be empty")

    single = _match_first(norm, SINGLE_SKILL_HINTS)
    archetype = _match_first(norm, ARCHETYPE_RULES)

    if single and not archetype:
        return WorkflowPlan(
            archetype="single_skill",
            goal_summary=goal.strip(),
            steps=[WorkflowStep(skill=single, purpose="User requested a single specialist skill", envelope_out=None)],
            boundaries=[
                "Single-skill mode — load only the target SKILL.md.",
                "Re-run orchestrator when the user wants a multi-step workflow.",
            ],
            single_skill_alternative=single,
        )

    if not archetype:
        if _goal_implies_audit(goal) and _goal_implies_release(goal):
            archetype = "audit_then_release"
        elif _goal_implies_council(goal):
            archetype = "research_then_council"
        elif _goal_implies_operator(goal):
            archetype = "research_then_operator"
        else:
            archetype = "orchestrated_goal"

    raw_steps = ARCHETYPE_STEPS.get(archetype, [])
    steps: list[WorkflowStep] = [
        WorkflowStep(skill=skill, purpose=purpose, envelope_out=envelope)
        for skill, purpose, envelope in raw_steps
    ]

    if archetype == "orchestrated_goal":
        filtered: list[WorkflowStep] = [steps[0]] if steps else []
        if _goal_implies_operator(goal) and len(steps) > 1:
            filtered.append(steps[1])
        if _goal_implies_council(goal) and len(steps) > 2:
            filtered.append(steps[2])
        elif _goal_implies_council(goal):
            filtered.append(
                WorkflowStep(
                    skill="ai-council",
                    purpose="Deliberate when goal implies material decision",
                    envelope_out="DecisionHandoff",
                )
            )
        if _goal_implies_audit(goal) and _goal_implies_release(goal):
            filtered = [
                WorkflowStep("web-app-auditor", "Produce findings with evidence", "FindingEnvelope"),
                WorkflowStep("release-readiness", "Gate pinned RC with findings", "DecisionHandoff"),
            ]
            archetype = "audit_then_release"
        steps = filtered or steps

    if archetype == "research_then_council" and not _goal_implies_council(goal):
        steps = [s for s in steps if s.skill != "ai-council"]

    boundaries = BOUNDARIES.get(archetype, DEFAULT_ORCHESTRATED_BOUNDARIES)

    return WorkflowPlan(
        archetype=archetype,
        goal_summary=goal.strip(),
        steps=steps,
        boundaries=boundaries,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Plan a CometWeb multi-skill workflow")
    parser.add_argument("goal", nargs="?", help="User goal in plain language")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()

    if not args.goal:
        parser.error("goal is required")

    plan = plan_workflow(args.goal)
    payload = plan.to_dict()

    if args.json:
        json.dump(payload, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
        return

    print(f"archetype: {plan.archetype}")
    for i, step in enumerate(plan.steps, 1):
        out = f" → {step.envelope_out}" if step.envelope_out else ""
        print(f"  {i}. {step.skill}: {step.purpose}{out}")
    for line in plan.boundaries:
        print(f"boundary: {line}")


if __name__ == "__main__":
    main()
