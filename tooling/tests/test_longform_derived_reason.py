"""check-derived must name a reason whenever the derived formats hold the stage.

`infer_stage` stops at MASTER_LOCKED when `_derived_ready` is false, and
`check_derived` is the command an operator runs to learn why. An optional HTML
QA that ran and failed used to stop the stage with `check_derived` returning
nothing. This sweeps every format and QA combination so a new branch in one of
the two functions cannot drift from the other unnoticed.
"""
from __future__ import annotations

import importlib.util
import itertools
from copy import deepcopy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills" / "longform-publisher" / "scripts"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(f"longform_{name}", SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


kernel = _load("publication_kernel")
harness = _load("run_evals")

FORMATS = ("HTML", "DOCX", "PDF", "EPUB")
QA_REQUIRED = (True, False, None)
QA_STATUS = ("PASS", "NOT_REQUIRED", "FAIL", "MISSING", None)


def _report(fmt: str, required, status) -> dict:
    report = deepcopy(harness.base_report())
    artifact = report["derived_artifacts"][0]
    artifact["format"] = fmt
    artifact["qa_required"] = required
    artifact["qa_status"] = status
    return report


@pytest.mark.parametrize("fmt,required,status", list(itertools.product(FORMATS, QA_REQUIRED, QA_STATUS)))
def test_held_stage_always_has_a_derived_reason(fmt, required, status):
    report = _report(fmt, required, status)
    ready = kernel._derived_ready(report)
    reasons = kernel.check_derived(report)
    assert ready == (reasons == []), (ready, reasons)


def test_optional_qa_that_failed_is_named():
    report = _report("HTML", False, "FAIL")
    assert kernel.infer_stage(report) == "MASTER_LOCKED"
    assert kernel.check_derived(report) == ["DERIVED_QA_FAILED"]


@pytest.mark.parametrize("status", ["PASS", "NOT_REQUIRED"])
def test_optional_qa_that_passed_or_was_skipped_is_not_flagged(status):
    report = _report("HTML", False, status)
    assert kernel.check_derived(report) == []
    assert kernel.infer_stage(report) == "RELEASE_READY"
