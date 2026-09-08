"""Tests for orchestrate_kernel."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

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


if __name__ == "__main__":
    unittest.main()
