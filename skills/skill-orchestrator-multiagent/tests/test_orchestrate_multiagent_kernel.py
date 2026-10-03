"""Tests for orchestrate_multiagent_kernel."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from orchestrate_multiagent_kernel import build_multiagent_plan, build_subagent_task
from orchestrate_kernel import plan_workflow


class MultiagentKernelTests(unittest.TestCase):
    def test_builds_task_per_step(self) -> None:
        payload = build_multiagent_plan(
            "Verify claims then run Council on pricing tier GO/NO-GO",
            workspace_root="/tmp/ws",
        )
        # The documented execution_mode token for this package; "multiagent" was
        # a label no orchestrator reference defines.
        self.assertEqual(payload["execution_mode"], "isolated_subagents")
        self.assertEqual(
            set(payload),
            {"execution_mode", "parent_role", "plan", "subagent_tasks", "parent_must_not"},
        )
        self.assertEqual(payload["parent_role"], "orchestrator_only")
        tasks = payload["subagent_tasks"]
        self.assertEqual(len(tasks), 2)
        self.assertEqual(tasks[0]["skill"], "evidence-researcher")
        self.assertEqual(tasks[1]["skill"], "ai-council")
        self.assertIn("isolated subagent", tasks[0]["prompt"].lower())
        self.assertIn("/tmp/ws", tasks[0]["prompt"])
        for task in tasks:
            self.assertEqual(
                set(task),
                {"step_index", "step_total", "skill", "subagent_type", "description",
                 "prompt", "envelope_out", "run_in_background"},
            )
            self.assertFalse(task["run_in_background"])

    def test_subagent_prompt_forbids_council_in_er(self) -> None:
        plan = plan_workflow("Evidence pack only on vendor pricing")
        task = build_subagent_task(
            step=plan.steps[0],
            step_index=1,
            step_total=1,
            goal="Evidence pack only",
            prior_envelopes=[],
        )
        self.assertIn("GO/NO-GO", task.prompt)


if __name__ == "__main__":
    unittest.main()
