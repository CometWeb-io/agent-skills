"""Every skill kernel refuses input it cannot use in one documented envelope.

See `tooling/kernel_error_envelope.py` for the rules. The sweep runs over every
library kernel the contracts declare and every behaviour-suite command that
reads a JSON object, so a new skill is covered without being listed here.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_SPEC = importlib.util.spec_from_file_location("kernel_error_envelope", ROOT / "tooling" / "kernel_error_envelope.py")
assert _SPEC and _SPEC.loader
envelope = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(envelope)

KERNELS = envelope.library_kernels()


def test_the_sweep_covers_every_library_kernel() -> None:
    # Eleven skills ship scripts/kernel.py with a JSON payload; a contract edit
    # that drops one from the sweep would otherwise go unnoticed.
    assert len(KERNELS) >= 11, KERNELS


@pytest.mark.parametrize("skill", KERNELS)
def test_library_kernel_keeps_the_error_envelope(skill: str) -> None:
    assert envelope.check_library_kernel(skill) == []


def test_command_scripts_refuse_non_objects_without_a_traceback() -> None:
    assert len(envelope.cli_probes()) >= 150
    assert envelope.check_cli() == []


# A kernel that breaks each rule once, to show the check is not vacuous.
DEMO_KERNEL = """
def validate(x):
    if not isinstance(x, dict):
        return {'status': 'INVALID', 'errors': ['payload:not-object']}
    if x.get('mode') not in {'A', 'B'}:
        return {'status': 'INVALID', 'errors': ['mode:invalid'], 'missing': []}
    return {'status': 'VALID', 'errors': [], 'missing': []}

def evaluate_case(case):
    if not isinstance(case, dict):
        raise TypeError('case is not an object')
    return validate(case.get('input'))
"""


def test_the_check_reports_a_kernel_that_breaks_the_envelope(tmp_path: Path, monkeypatch) -> None:
    package = tmp_path / "skills" / "demo"
    (package / "scripts").mkdir(parents=True)
    (package / "references").mkdir()
    (package / "evals").mkdir()
    (package / "scripts" / "kernel.py").write_text(DEMO_KERNEL, encoding="utf-8")
    (package / "references" / "contract.json").write_text(json.dumps({
        "scripts": {"scripts/kernel.py": {"input": "json", "role": "kernel"}},
        "evals": [{"path": "evals/cases.json", "pass": ["VALID"]}],
    }), encoding="utf-8")
    (package / "evals" / "cases.json").write_text(json.dumps([
        {"id": "ok", "input": {"mode": "A"}},
        {"id": "bad-mode", "input": {"mode": "C"}},
    ]), encoding="utf-8")
    monkeypatch.setattr(envelope, "SKILLS", tmp_path / "skills")

    assert envelope.library_kernels() == ["demo"]
    problems = envelope.check_library_kernel("demo")
    assert any("case null" in p and "raised TypeError" in p for p in problems), problems
    assert any("refusal lacks ['missing']" in p for p in problems), problems
    assert any("wrong type in mode" in p and "unhashable" in p for p in problems), problems
