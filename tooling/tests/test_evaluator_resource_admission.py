"""Resource evidence must never default missing/bad observations to ratio 1."""
import copy
import importlib.util
import json
from pathlib import Path
import re
import pytest
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("resource_evaluator", ROOT / "skills/skill-evaluator/scripts/kernel.py")
kernel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kernel)

def report():
    text = (ROOT / "evals/output/skill-evaluator/good-improved.md").read_text()
    return json.loads(re.findall(r"```json\s*(.*?)```", text, re.S)[-1])

@pytest.mark.parametrize("arm", ["candidate", "baseline"])
@pytest.mark.parametrize("metric", ["tokens", "duration_s"])
@pytest.mark.parametrize("value", [None, True, -1, "10", float("nan"), float("inf"), 10**1000])
def test_bad_measurement_never_promotes(arm, metric, value):
    data = report(); data[arm][metric] = value
    result = kernel.validate(data)
    assert result["status"] == "INSUFFICIENT_EVIDENCE"
    assert result["promotion_eligible"] is False

def test_missing_and_zero_baseline_are_not_unit_ratios():
    for metric in ("tokens", "duration_s"):
        for missing in (True, False):
            data = report()
            if missing: data["baseline"].pop(metric)
            else: data["baseline"][metric] = 0
            assert kernel.validate(data)["status"] == "INSUFFICIENT_EVIDENCE"

def test_zero_candidate_is_a_valid_observation():
    data = report(); data["candidate"].update(tokens=0, duration_s=0)
    result = kernel.validate(data)
    assert result["token_ratio"] == result["duration_ratio"] == 0
    assert result["status"] == "IMPROVED"
