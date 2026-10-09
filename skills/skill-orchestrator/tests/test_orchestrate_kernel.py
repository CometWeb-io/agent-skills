"""Tests for orchestrate_kernel."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import orchestrate_kernel
from orchestrate_kernel import plan_workflow


class OrchestrateKernelTests(unittest.TestCase):
    def test_research_then_council_explicit(self) -> None:
        plan = plan_workflow("Verify EU AI Act claims, then run Council on roadmap impact")
        self.assertEqual(plan.archetype, "research_then_council")
        skills = [s.skill for s in plan.steps]
        self.assertEqual(skills, ["evidence-researcher", "ai-council"])

    def test_audit_then_release(self) -> None:
        plan = plan_workflow("Web app audit then release readiness for RC 1.0.2 on staging")
        self.assertEqual(plan.archetype, "audit_then_release")
        self.assertEqual([s.skill for s in plan.steps], ["web-app-auditor", "release-readiness"])

    def test_single_skill_evidence_only(self) -> None:
        plan = plan_workflow("Evidence pack only on vendor pricing claims")
        self.assertEqual(plan.archetype, "single_skill")
        self.assertEqual(plan.steps[0].skill, "evidence-researcher")

    def test_orchestrated_goal_infers_council(self) -> None:
        plan = plan_workflow("Full workflow: verify pricing claims and get a Council GO/NO-GO")
        self.assertIn(plan.archetype, {"orchestrated_goal", "research_then_council"})
        skills = [s.skill for s in plan.steps]
        self.assertIn("evidence-researcher", skills)
        self.assertIn("ai-council", skills)

    def test_disambiguate_only(self) -> None:
        plan = plan_workflow("Which skill should I use for weekly review?")
        self.assertEqual(plan.archetype, "disambiguate_only")
        self.assertEqual(plan.steps, [])

    def test_documented_polish_council_phrase_routes_to_research_then_council(self) -> None:
        plan = plan_workflow("Od researchu do Rady")
        self.assertEqual(plan.archetype, "research_then_council")
        self.assertEqual([step.skill for step in plan.steps], ["evidence-researcher", "ai-council"])

    def test_documented_polish_skill_question_disambiguates(self) -> None:
        plan = plan_workflow("Który skill?")
        self.assertEqual(plan.archetype, "disambiguate_only")
        self.assertEqual(plan.steps, [])

    def test_plan_json_stays_inside_documented_vocabulary(self) -> None:
        # references/contract.json binds ARCHETYPES and ENVELOPE_TYPES to the
        # documented output enums; every plan the kernel emits must stay inside them.
        goals = [
            "Verify EU AI Act claims, then run Council on roadmap impact",
            "Web app audit then release readiness for RC 1.0.2 on staging",
            "Evidence pack only on vendor pricing claims",
            "Full workflow: verify pricing claims and get a Council GO/NO-GO",
            "Which skill should I use for weekly review?",
            "Competitor launch, then Council on our response",
            "Evidence then weekly operator review",
        ]
        for goal in goals:
            payload = plan_workflow(goal).to_dict()
            self.assertEqual(
                set(payload),
                {"archetype", "goal_summary", "steps", "boundaries", "single_skill_alternative"},
            )
            self.assertIn(payload["archetype"], orchestrate_kernel.ARCHETYPES)
            for step in payload["steps"]:
                self.assertEqual(set(step), {"skill", "purpose", "envelope_out", "read_skill"})
                if step["envelope_out"] is not None:
                    self.assertIn(step["envelope_out"], orchestrate_kernel.ENVELOPE_TYPES)


    def test_blank_goal_is_a_usage_error_not_a_traceback(self) -> None:
        for goal in ("   ", "\t\n"):
            proc = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "orchestrate_kernel.py"), goal],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(proc.returncode, 2, proc.stderr)
            self.assertNotIn("Traceback", proc.stderr)
            self.assertIn("goal is required", proc.stderr)


if __name__ == "__main__":
    unittest.main()
