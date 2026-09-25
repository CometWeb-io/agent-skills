"""Check the plan-to-report boundary, not merely ranking in isolation."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("product_brief", ROOT / "scripts/prepare_brief.py")
brief = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(brief)


def source():
    return json.loads((ROOT / "examples/brief.synthetic.pl.json").read_text())


def decision_source():
    data = source()
    row = data["candidates"][0]
    row.update(action_type="decision", decision_required=True, verify_first=False,
               question="Which implementation should be evaluated?", decision_domain="product",
               options=["Evaluate A", "Evaluate B"], delegated_to="product owner")
    data["candidates"] = [row]
    return data


class BriefTests(unittest.TestCase):
    def test_inferred_action_type_survives_bridge(self):
        data = source()
        for row in data["candidates"]:
            row.pop("action_type")
        result = brief.assemble(data)
        self.assertEqual([row["id"] for row in result["report"]["verify_now"]], ["A"])
        self.assertEqual([row["id"] for row in result["report"]["later"]], ["B"])

    def test_decision_survives_report_snapshot_and_bilingual_rendering(self):
        result = brief.assemble(decision_source())
        self.assertEqual([row["id"] for row in result["report"].get("decision_now", [])], ["A"])
        self.assertEqual(result["snapshot"]["report"]["decision_now"], result["report"]["decision_now"])
        self.assertNotEqual(result["validation"]["status"], "FAIL")
        for language, label in (("en", "Decisions now"), ("pl", "Decyzje do podjęcia")):
            with self.subTest(language=language):
                rendered = brief.render(result, language)
                self.assertIn(label, rendered)
                self.assertIn("Evaluate A", rendered)
                self.assertIn("Evaluate B", rendered)
                self.assertIn("product owner", rendered)

    def test_preselected_decision_is_rejected_not_silently_dropped(self):
        data = decision_source()
        data["candidates"][0]["selected_option"] = "Evaluate A"
        with self.assertRaisesRegex(brief.kernel.InputError, "must not select"):
            brief.assemble(data)


if __name__ == "__main__":
    unittest.main()
