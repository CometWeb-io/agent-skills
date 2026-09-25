"""Plans must never promote work whose prerequisites cannot be executed."""
import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location(
    "product_plan_kernel", Path(__file__).resolve().parents[1] / "scripts/operator_kernel.py"
)
kernel = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(kernel)


def candidate(identifier, **fields):
    return {"id": identifier, "impact": 5, "goal_alignment": 5,
            "confidence": 1, "evidence_strength": 1, **fields}


def plan(rows, **fields):
    return kernel.build_plan({
        "target": "fixture/product", "goal": "Verify prerequisite ordering",
        "horizon": "one week", "as_of": "2026-09-25T00:00:00Z",
        "coverage": {"github": "verified", "notion": "verified", "product_context": "verified"},
        "candidates": rows, **fields,
    })


class PlanTests(unittest.TestCase):
    def test_missing_dependency_holds_entire_chain_but_not_independent_work(self):
        result = plan([
            candidate("A", depends_on=["missing"]),
            candidate("B", depends_on=["A"]), candidate("C"),
        ])
        self.assertEqual([row["id"] for row in result["immediate_actions"]], ["C"])
        self.assertEqual(result["next_actions"], [])
        self.assertEqual(result["sequence"]["missing_dependencies"], [
            {"action_id": "A", "missing_dependency": "missing"},
        ])

    def test_present_dependency_is_first_and_dependent_is_next(self):
        result = plan([candidate("A"), candidate("B", depends_on=["A"])])
        self.assertEqual([row["id"] for row in result["immediate_actions"]], ["A"])
        self.assertEqual([row["id"] for row in result["next_actions"]], ["B"])

    def test_cycles_hold_dependents(self):
        result = plan([
            candidate("A", depends_on=["B"]), candidate("B", depends_on=["A"]),
            candidate("C", depends_on=["B"]),
        ])
        self.assertFalse(result["sequence"]["is_acyclic"])
        self.assertEqual(result["immediate_actions"], [])
        self.assertEqual(result["next_actions"], [])

    def test_incomplete_coverage_allows_verification_not_implementation(self):
        result = plan([candidate("A"), candidate("V", verify_first=True)], coverage={})
        self.assertEqual([row["id"] for row in result["immediate_actions"]], ["V"])
        self.assertEqual(result["held_by_readiness_action_ids"], ["A"])

    def test_stop_and_future_gate_never_promoted(self):
        result = plan([candidate("S", stop=True), candidate("F", future_gate=True)])
        self.assertEqual(result["immediate_actions"], [])
        self.assertEqual(result["next_actions"], [])

    def test_plan_limits_are_enforced(self):
        result = plan([candidate(str(i)) for i in range(12)])
        self.assertEqual(len(result["immediate_actions"]), 3)
        self.assertEqual(len(result["next_actions"]), 5)


if __name__ == "__main__":
    unittest.main()
