"""The release gate holds the red-team manifest to the scorer's own case contract.

`release_check.py` used to check only that six keys were present, so a manifest
with an unsupported language or an unknown key passed the release gate and then
made `redteam_score.py` stop with exit 2 before any output was scored.
"""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def _load(name):
    spec = importlib.util.spec_from_file_location(f"contract_{name}", ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RELEASE = _load("release_check")
SCORER = _load("redteam_score")


def _case(index, **overrides):
    case = {
        "id": f"case-{index:02d}",
        "language": "en",
        "request": "Rewrite faithfully.",
        "mode_expectation": "light",
        "source": "The beta does not support SSO.",
        "manual_checks": ["Keep negation."],
    }
    case.update(overrides)
    return case


class ReleaseManifestContractTests(unittest.TestCase):
    def check(self, cases):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "redteam-cases.json"
            path.write_text(json.dumps(cases), encoding="utf-8")
            RELEASE.check_redteam_manifest(path)

    def test_bundled_manifest_passes(self):
        RELEASE.check_redteam_manifest()

    def test_conforming_manifest_passes(self):
        self.check([_case(i) for i in range(12)])

    def test_unsupported_language_fails_the_release_gate(self):
        cases = [_case(i) for i in range(12)]
        cases[3]["language"] = "de"
        with self.assertRaisesRegex(AssertionError, "red-team manifest"):
            self.check(cases)

    def test_unknown_case_key_fails_the_release_gate(self):
        cases = [_case(i) for i in range(12)]
        cases[0]["expected_mode"] = "light"
        with self.assertRaisesRegex(AssertionError, "red-team manifest"):
            self.check(cases)

    def test_too_few_cases_still_fails(self):
        with self.assertRaisesRegex(AssertionError, "at least 12"):
            self.check([_case(i) for i in range(3)])

    def test_language_vocabulary_is_a_named_constant(self):
        self.assertEqual(SCORER.LANGUAGES, {"en", "pl"})


if __name__ == "__main__":
    unittest.main()
