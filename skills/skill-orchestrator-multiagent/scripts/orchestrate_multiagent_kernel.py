#!/usr/bin/env python3
"""Build isolated subagent task payloads for skill-orchestrator-multiagent."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import json
import sys
from dataclasses import dataclass
from typing import Any

from orchestrate_kernel import WorkflowStep, plan_workflow

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
        return {
            "step_index": self.step_index,
            "step_total": self.step_total,
            "skill": self.skill,
            "subagent_type": self.subagent_type,
            "description": self.description,
            "prompt": self.prompt,
            "envelope_out": self.envelope_out,
            "run_in_background": self.run_in_background,
        }


def _skill_paths(skill: str, pinned_root: Path | None = None) -> str:
    if pinned_root is not None:
        return f"- `{pinned_root / 'skills' / skill / 'SKILL.md'}` (pinned local pilot; do not load an installed copy)"
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
    pinned_root: Path | None = None,
    handoff_step: dict | None = None,
) -> SubagentTask:
    subagent_type = SUBAGENT_TYPE_BY_SKILL.get(step.skill, "generalPurpose")
    envelope_line = (
        f"Required CW-AIP output: `{step.envelope_out}`."
        if step.envelope_out
        else "Emit the skill's standard output contract."
    )
    prior_block = json.dumps(prior_envelopes, indent=2, ensure_ascii=False) if prior_envelopes else "[]"
    ws = workspace_root or "<host workspace root>"

    gate_rules = ""
    if handoff_step:
        gate_rules = "\n- Parent must validate and checkpoint this full envelope before dispatching the next step."
        if handoff_step.get("artifact_profile") == "PRD":
            gate_rules += "\n- Emit canonical PRD payload using brief-architect/references/prd-output.schema.json; preserve unknowns. READY is required for execution; do not force readiness."
    prompt = f"""You are an **isolated subagent** for CometWeb skill `{step.skill}` only.

## Hard rules
- Execute **only** `{step.skill}`. Do not run other skills or their workflows.
- {_forbidden_outputs(step.skill)}
- Read and follow the full skill entrypoint before acting.
- {envelope_line}{gate_rules}

## Skill locations (read SKILL.md from the first path that exists)
{_skill_paths(step.skill, pinned_root)}

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


ROOT = Path(__file__).resolve().parents[3]


def _canonical_module(name: str):
    path = ROOT / "skills/skill-orchestrator/scripts" / (name + ".py")
    spec = importlib.util.spec_from_file_location("dispatch_" + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _task(plan: dict, index: int, prior_envelopes: list, workspace_root: str | None, *, gated: bool) -> dict:
    raw = plan["steps"][index]
    step = WorkflowStep(skill=raw["skill"], purpose=raw["purpose"], envelope_out=raw.get("envelope_out"), read_skill=raw.get("read_skill",True))
    result = build_subagent_task(step=step, step_index=index+1, step_total=len(plan["steps"]), goal=plan["goal_summary"],
                                prior_envelopes=prior_envelopes, workspace_root=workspace_root,
                                pinned_root=ROOT if gated or plan.get("specialist_profile") else None, handoff_step=raw if gated else None).to_dict()
    if raw.get("profile_lock"):
        result = _canonical_module("specialist_profiles").attach_task(result, {"specialist_profile":raw["profile_lock"], "steps":[raw]}, ROOT)
    if raw["skill"] == "ai-council" and plan.get("capability_packs"):
        result["capability_packs"] = plan["capability_packs"]
        result["prompt"] += "\nLocked role-scoped capability packs (FRAMEWORK only, never factual evidence):\n" + json.dumps(plan["capability_packs"], ensure_ascii=False, indent=2)
    if gated:
        result["step_id"] = raw.get("step_id") or raw.get("id") or f"step-{index+1}"
        result["handoff_gate"] = raw["handoff_gate"]
        result["gate_lock"] = raw["gate_lock"]
        if raw.get("artifact_profile"): result["artifact_profile"] = raw["artifact_profile"]
        if raw.get("domain_context"): result["domain_context"] = raw["domain_context"]
        if raw["handoff_gate"] == _canonical_module("prd_handoff").DOMAIN_GATE:
            result["prompt"] += "\nDomain handoff: include full graph/bundle and pinned upstream_bindings; run domain_handoff.py. Keep proposal separate from deterministic constraint_result. Partial research permits only gap discussion, never GO/TEST. No execution authorization.\n"
        result["prior_envelope_ids"] = [v["id"] for v in prior_envelopes]
    if plan.get("compiled_dispatch"):
        result = _canonical_module("worker_compiler").compile_task(result, plan, raw, prior_envelopes, ROOT)
    return result


def build_multiagent_plan(goal: str, workspace_root: str | None = None, *, with_prd_handoff: bool = False,
                          with_capability_packs: bool = False, specialist_profile: str | None = None, with_domain_gates: bool = False, domain_context: dict | None = None, trusted_context: dict | None = None, instruction_arm: str = "candidate", typed_native_reports: bool = False, report_as_of: str | None = None) -> dict[str, Any]:
    if with_domain_gates and not with_prd_handoff: raise ValueError("domain gates require --with-prd-handoff")
    if domain_context is not None and not with_domain_gates: raise ValueError("domain context requires domain gates")
    combined = specialist_profile and with_prd_handoff
    if combined and (trusted_context is None or not with_domain_gates):
        raise ValueError("combined profiles require trusted context and domain gates")
    if specialist_profile and with_capability_packs:
        raise ValueError("combined capability pack dispatch is not qualified")
    if instruction_arm not in {"candidate", "baseline"}:
        raise ValueError("invalid instruction arm")
    plan = (_canonical_module("specialist_profiles").plan_for_profile(goal, specialist_profile, ROOT, trusted_context=trusted_context)
            if specialist_profile else plan_workflow(goal).to_dict())
    if with_capability_packs:
        plan["capability_packs"] = _canonical_module("capability_packs").select(ROOT,goal)
    if combined:
        tail = {"archetype":"research_council", "goal_summary":goal, "boundaries":[], "steps":[
            {"skill":"evidence-researcher", "purpose":"Build auditable evidence for bounded PRD", "envelope_out":"EvidenceEnvelope", "read_skill":True},
            {"skill":"ai-council", "purpose":"Review bounded design with independent blind roles", "envelope_out":"DecisionHandoff", "read_skill":True}]}
        tail = _canonical_module("prd_handoff").attach(tail, with_domain_gates=True, domain_context=domain_context)
        plan["steps"] += tail["steps"]
        plan["archetype"] = "profile_prd_research_council"
    elif with_prd_handoff:
        plan = _canonical_module("prd_handoff").attach(plan, with_domain_gates=with_domain_gates, domain_context=domain_context)
    if trusted_context is not None:
        _canonical_module("trusted_profile_context").validate(trusted_context)
        if trusted_context["original_brief"] != goal.strip():
            raise ValueError("context must match exact original goal")
        plan.update(trusted_context=trusted_context, compiled_dispatch=True, instruction_arm=instruction_arm)
    if typed_native_reports:
        if trusted_context is None or not specialist_profile:
            raise ValueError("typed native reports require trusted profile context")
        plan["steps"][0]["native_report_contract"] = _canonical_module("typed_owner").VERSION
        if report_as_of is not None:
            _canonical_module("typed_owner").validate_timestamp(report_as_of)
            plan["report_as_of"] = report_as_of
            for step in plan["steps"]:
                step["report_as_of"] = report_as_of
        elif plan["steps"][0]["skill"] == "product-operator":
            raise ValueError("typed operator dispatch requires parent --report-as-of")
    elif report_as_of is not None:
        raise ValueError("report-as-of requires typed native reports")
    # Gated mode exposes only the briefing preview. Real dispatch is ledger-backed.
    indices = range(1 if with_prd_handoff else len(plan["steps"]))
    tasks = [_task(plan,i,[],workspace_root,gated=with_prd_handoff) for i in indices]
    result = {
        "execution_mode": "isolated_subagents", "parent_role": "orchestrator_only", "plan":plan, "subagent_tasks":tasks,
        "parent_must_not": ["Execute domain skill workflows in the parent thread.",
                            "Collapse multiple steps into one model pass.",
                            "Issue Council or Release verdicts without a dedicated ai-council/release-readiness subagent run."],
    }
    if specialist_profile: result["dispatch_status"] = "PLAN_ONLY"
    if with_prd_handoff:
        result["dispatch_status"] = "PLAN_ONLY"
        result["deferred_step_ids"] = [f"step-{i+1}" for i in range(1,len(plan["steps"]))]
    return result


def build_next_task(run_dir: Path, plan: dict, prior_envelopes: list, workspace_root: str | None = None, *, previous_error: str | None = None) -> dict:
    """Validate exact upstream prefix, then claim one isolated attempt. No domain execution."""
    ledger = _canonical_module("workflow_ledger")
    gate = _canonical_module("prd_handoff")
    state = ledger.replay(run_dir)
    if plan.get("compiled_dispatch"):
        context = plan.get("trusted_context")
        _canonical_module("trusted_profile_context").validate(context)
        if context["original_brief"] != plan.get("goal_summary") or (plan.get("specialist_profile") and context != plan["steps"][0].get("trusted_context")):
            raise ValueError("compiled plan input commitments diverged")
    if ledger.plan_hash(plan) != state["plan_hash"]:
        changed = ledger.claim_next(run_dir,plan)
        return {"dispatch_status":changed["status"],"subagent_tasks":[],"plan":plan}
    if not plan.get("steps") or (plan["steps"][0].get("artifact_profile") != "PRD" and not plan.get("specialist_profile")):
        raise ValueError("ledger-backed dispatch requires a gated PRD workflow")
    if "capability_packs" in plan:
        current = _canonical_module("capability_packs").select(ROOT,plan["goal_summary"])
        if current != plan["capability_packs"]: raise ValueError("capability pack pointers changed since plan")
    definitions = ledger._normalise_steps(plan)
    completed = []
    for definition in definitions:
        if state["steps"].get(definition["step_id"],{}).get("status") != "COMPLETED": break
        completed.append(definition)
    if not isinstance(prior_envelopes,list) or len(prior_envelopes) != len(completed):
        raise ValueError("prior envelopes must exactly match the completed prefix")
    prior_envelopes = json.loads(gate.canonical(prior_envelopes))
    for definition, envelope in zip(completed,prior_envelopes,strict=True):
        if definition["handoff_gate"] == gate.PROFILE_GATE:
            result=_canonical_module("specialist_profiles").validate_envelope(envelope,definition,ROOT)
        else:
            result = gate.validate(envelope,definition["gate_lock"],expected_type=definition["envelope_out"],
                                   expected_producer=definition["skill"],prd_required=definition["handoff_gate"]==gate.GATE, domain_required=definition["handoff_gate"]==gate.DOMAIN_GATE, domain_context=definition.get("domain_context"))
        checkpoint = state["steps"][definition["step_id"]]
        if not result["accepted"] or result["envelope_id"] != checkpoint["envelope_id"] or result["envelope_hash"] != checkpoint["envelope_hash"]:
            raise ValueError("prior envelope invalid or changed since checkpoint")
    claim = ledger.claim_next(run_dir,plan)
    if claim.get("event_type") != "step_claimed":
        return {"dispatch_status":claim["status"],"subagent_tasks":[],"plan":plan}
    task = _task(plan,len(completed),prior_envelopes,workspace_root,gated=True)
    task["attempt_id"] = claim["data"]["attempt_id"]
    if plan.get("compiled_dispatch"):
        task = _canonical_module("worker_compiler").compile_task(task, plan, plan["steps"][len(completed)], prior_envelopes, ROOT, previous_error=previous_error)
    return {"dispatch_status":"CLAIMED","subagent_tasks":[task],"plan":plan}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build multiagent workflow task payloads")
    parser.add_argument("goal", nargs="?", help="User goal in plain language")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    parser.add_argument("--workspace-root", default="", help="Host workspace root path")
    parser.add_argument("--with-prd-handoff", action="store_true")
    parser.add_argument("--with-domain-gates", action="store_true")
    parser.add_argument("--domain-context-json", type=Path)
    parser.add_argument("--with-capability-packs", action="store_true")
    parser.add_argument("--specialist-profile", choices=("conversion-audit", "experiment-design", "activation-onboarding", "sop-documentation"))
    parser.add_argument("--report-as-of")
    parser.add_argument("--typed-native-reports", action="store_true")
    parser.add_argument("--trusted-context-json", type=Path)
    parser.add_argument("--instruction-arm", choices=("candidate", "baseline"), default="candidate")
    parser.add_argument("--previous-error", default=None)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--plan-json", type=Path)
    parser.add_argument("--prior-envelopes-json", type=Path)
    args = parser.parse_args()

    try:
        if args.run_dir:
            if args.report_as_of: parser.error("resume uses the parent timestamp in the pinned plan")
            if args.typed_native_reports: parser.error("resume uses the typed contract in the pinned plan")
            if args.specialist_profile: parser.error("resume uses the profile in the pinned plan, not an override")
            if not args.plan_json: parser.error("--run-dir requires --plan-json")
            payload = build_next_task(args.run_dir,json.loads(args.plan_json.read_text()),
                                      json.loads(args.prior_envelopes_json.read_text()) if args.prior_envelopes_json else [],
                                      args.workspace_root or None, previous_error=args.previous_error)
        else:
            if not args.goal: parser.error("goal is required")
            if args.plan_json or args.prior_envelopes_json: parser.error("execution inputs require --run-dir")
            payload = build_multiagent_plan(args.goal,args.workspace_root or None,with_prd_handoff=args.with_prd_handoff,
                                           with_capability_packs=args.with_capability_packs, specialist_profile=args.specialist_profile, with_domain_gates=args.with_domain_gates,
                                           domain_context=json.loads(args.domain_context_json.read_text()) if args.domain_context_json else None,
                                           trusted_context=json.loads(args.trusted_context_json.read_text()) if args.trusted_context_json else None, instruction_arm=args.instruction_arm, typed_native_reports=args.typed_native_reports, report_as_of=args.report_as_of)
    except (OSError,ValueError) as exc:
        print("FAIL: "+str(exc),file=sys.stderr)
        raise SystemExit(1) from exc

    if args.json:
        json.dump(payload, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
        return

    print(f"mode: {payload.get('execution_mode', 'isolated_subagents')}")
    if "dispatch_status" in payload: print(f"dispatch: {payload['dispatch_status']}")
    print(f"archetype: {payload['plan']['archetype']}")
    for task in payload["subagent_tasks"]:
        print(f"  {task['step_index']}. Task({task['subagent_type']}) -> {task['skill']}")


if __name__ == "__main__":
    main()
