"""A kernel's input contract and the reference that documents it must agree.

An agent loading a skill cold builds its payload from the reference, not from
the kernel source. When the two drift, the agent writes a field the kernel never
reads and nothing complains: repair-operator documented `dependencies[]` while
its kernel read `depends_on`, so every dependency was silently ignored, and
benchmark-curator documented none of the enums its kernel rejects payloads for.

Each case here names a kernel and the one reference that is its contract, then
checks two things: every literal field the kernel reads appears in that
reference, and every enum the kernel accepts is spelled out there exactly.
"""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

# skill -> (kernel, contract reference, kernel constants that are enums)
CONTRACTS = {
    "repair-operator": (
        "scripts/kernel.py", "references/output-contract.md",
        ("VALID_STATUS", "VALID_CLASS", "PATCH_RISK", "EFFORT", "BLAST", "REVERSIBILITY"),
    ),
    "benchmark-curator": (
        "scripts/kernel.py", "references/benchmark-model.md",
        ("LEAK", "MODES", "CLASSES", "DIFF", "SPLITS", "CONTAM", "LANES"),
    ),
}

FIELD_READ = re.compile(r"""\.get\(\s*['"]([A-Za-z_][\w-]*)['"]""")
# The harness hands the kernel {"input": ...}; that wrapper is not a contract field.
HARNESS_ONLY = {"input"}


def load(skill: str, relative: str):
    path = ROOT / "skills" / skill / relative
    spec = importlib.util.spec_from_file_location(f"{skill.replace('-', '_')}_contract_kernel", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def documented_enums(text: str) -> list[set[str]]:
    """Every `A|B|C` run in the reference, as a set of its alternatives."""
    return [set(run.split("|")) for run in re.findall(r"[\w-]+(?:\|[\w-]+)+", text)]


@pytest.mark.parametrize("skill", sorted(CONTRACTS))
def test_every_field_the_kernel_reads_is_documented(skill: str) -> None:
    kernel, reference, _ = CONTRACTS[skill]
    source = (ROOT / "skills" / skill / kernel).read_text(encoding="utf-8")
    doc = (ROOT / "skills" / skill / reference).read_text(encoding="utf-8")
    fields = set(FIELD_READ.findall(source)) - HARNESS_ONLY
    assert fields, f"{skill}: found no field reads; the pattern no longer matches the kernel"
    missing = sorted(f for f in fields if not re.search(rf"(?<![\w-]){re.escape(f)}(?![\w-])", doc))
    assert not missing, f"{skill}: {reference} does not document fields {kernel} reads: {missing}"


@pytest.mark.parametrize("skill", sorted(CONTRACTS))
def test_every_enum_the_kernel_accepts_is_spelled_out(skill: str) -> None:
    kernel, reference, constants = CONTRACTS[skill]
    module = load(skill, kernel)
    enums = documented_enums((ROOT / "skills" / skill / reference).read_text(encoding="utf-8"))
    for name in constants:
        accepted = set(getattr(module, name))
        assert accepted in enums, (
            f"{skill}: {reference} never lists {name} exactly as {kernel} accepts it: "
            f"{'|'.join(sorted(accepted))}"
        )


def test_the_documented_repair_field_is_the_one_the_kernel_reads() -> None:
    """The original defect: a dependency written as documented must be enforced."""
    kernel = load("repair-operator", "scripts/kernel.py")
    ledger = {"items": [
        {"repair_id": "R1", "finding_ids": ["F1"], "repair_class": "PATCH",
         "status": "PLANNED", "depends_on": ["R9"]},
    ]}
    assert "0:depends-on-missing:R9" in kernel.validate(ledger)["errors"]


@pytest.mark.parametrize("skill,payload,code,status", [
    ("repair-operator", {"items": []}, 0, "VALID"),
    ("repair-operator", {"items": "not-a-list"}, 1, "INVALID"),
    ("benchmark-curator", {"cases": []}, 1, "INVALID"),
])
def test_kernel_runs_as_the_command_the_reference_shows(skill, payload, code, status, tmp_path) -> None:
    """The references tell an agent to run `python3 scripts/kernel.py file.json`."""
    kernel = ROOT / "skills" / skill / "scripts" / "kernel.py"
    path = tmp_path / "payload.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    for args, stdin in (([str(path)], None), ([], json.dumps(payload))):
        proc = subprocess.run([sys.executable, str(kernel), *args], input=stdin,
                              capture_output=True, text=True, timeout=60, check=False)
        assert proc.returncode == code, proc.stderr
        assert json.loads(proc.stdout)["status"] == status


@pytest.mark.parametrize("skill", sorted(CONTRACTS))
def test_kernel_rejects_a_payload_that_is_not_json(skill: str) -> None:
    kernel = ROOT / "skills" / skill / "scripts" / "kernel.py"
    proc = subprocess.run([sys.executable, str(kernel)], input="not json",
                          capture_output=True, text=True, timeout=60, check=False)
    assert proc.returncode == 2 and "not JSON" in proc.stderr
