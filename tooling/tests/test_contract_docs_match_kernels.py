"""Every skill's scripts, docs and eval cases agree with one declared contract.

An agent loading a skill cold builds its payload from the reference, not from
the kernel source. When the two drift, the agent writes a field the kernel never
reads and nothing complains: repair-operator documented `dependencies[]` while
its kernel read `depends_on`, so every dependency was silently ignored, and
benchmark-curator documented none of the enums its kernel rejects payloads for.

Each skill that ships a script declares its contract once, in
`references/contract.json`; `tooling/skill_contracts.py` holds the kernel, the
docs and the eval cases to it. The tests below run that check for every such
skill, then prove each rule of the checker fails on a package that breaks it.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tooling"))
import skill_contracts  # noqa: E402


def load(skill: str, relative: str):
    path = ROOT / "skills" / skill / relative
    spec = importlib.util.spec_from_file_location(f"{skill.replace('-', '_')}_contract_kernel", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_every_skill_with_scripts_is_covered() -> None:
    skills = skill_contracts.unique_skills()
    assert len(skills) >= 30, skills
    missing = [s for s in skills if not (ROOT / "skills" / s / skill_contracts.CONTRACT).is_file()]
    assert not missing, f"skills with scripts but no {skill_contracts.CONTRACT}: {missing}"


@pytest.mark.parametrize("skill", skill_contracts.unique_skills())
def test_skill_contract_holds(skill: str) -> None:
    errors = skill_contracts.check(skill)
    assert not errors, "\n".join(errors)


def test_checker_cli_passes_on_the_tree() -> None:
    proc = subprocess.run([sys.executable, str(ROOT / "tooling" / "skill_contracts.py"), "--check"],
                          capture_output=True, text=True, timeout=300, check=False)
    assert proc.returncode == 0, proc.stdout + proc.stderr


# --- the checker itself: each rule fails on a package that breaks it ----------------------------

KERNEL = '''
MODES = {"A", "B"}
def validate(payload):
    errors = []
    if payload.get("mode") not in MODES:
        errors.append("mode")
    for item in payload.get("items") or []:
        if not item.get("item_id"):
            errors.append("item_id")
    return {"status": "INVALID" if errors else "VALID", "errors": errors}
'''
DOC = """# Contract

```text
mode: A|B
items[]:
  item_id
```

The kernel prints `{status: VALID|INVALID, errors[]}`.
"""


def contract() -> dict:
    return {
        "schema": skill_contracts.SCHEMA,
        "docs": ["references/contract.md"],
        "scripts": {"scripts/kernel.py": {"input": "json", "enums": {"MODES": "mode"}}},
        "fields": {"mode": {"enum": ["A", "B"]}, "items": {}, "item_id": {}},
        "outputs": {"status": {"enum": ["VALID", "INVALID"]}, "errors": {}},
        "internal": [],
        "doc_terms": [],
        "evals": [{"path": "evals/cases.json", "cases": "", "input": "input",
                   "status": "expect.status", "pass": ["VALID"]}],
    }


CASES = [
    {"id": "ok", "input": {"mode": "A", "items": [{"item_id": "x"}]}, "expect": {"status": "VALID"}},
    {"id": "bad", "input": {"mode": "C", "items": []}, "expect": {"status": "INVALID"}},
]


@pytest.fixture
def package(tmp_path, monkeypatch):
    def build(contract_data=None, kernel=KERNEL, doc=DOC, cases=None):
        base = tmp_path / "skills" / "demo"
        for sub in ("scripts", "references", "evals"):
            (base / sub).mkdir(parents=True, exist_ok=True)
        (base / "SKILL.md").write_text("# Demo\n", encoding="utf-8")
        (base / "scripts" / "kernel.py").write_text(kernel, encoding="utf-8")
        (base / "references" / "contract.md").write_text(doc, encoding="utf-8")
        (base / "evals" / "cases.json").write_text(json.dumps(CASES if cases is None else cases), encoding="utf-8")
        (base / "references" / "contract.json").write_text(json.dumps(contract_data or contract()), encoding="utf-8")
        monkeypatch.setattr(skill_contracts, "SKILLS", tmp_path / "skills")
        return skill_contracts.check("demo")
    return build


def test_a_conforming_package_passes(package) -> None:
    assert package() == []


def test_a_package_without_a_contract_fails(package, tmp_path) -> None:
    package()
    (tmp_path / "skills" / "demo" / "references" / "contract.json").unlink()
    assert skill_contracts.check("demo") == ["demo: ships scripts but has no references/contract.json"]


def test_an_undeclared_script_fails(package, tmp_path) -> None:
    package()
    (tmp_path / "skills" / "demo" / "scripts" / "extra.py").write_text("x = 1\n", encoding="utf-8")
    assert any("script not declared" in e for e in skill_contracts.check("demo"))


def test_a_field_the_kernel_reads_but_the_contract_omits_fails(package) -> None:
    errors = package(kernel=KERNEL + "\ndef more(p):\n    return p.get('undeclared_key')\n")
    assert any("undeclared_key" in e and "does not declare" in e for e in errors)


def test_a_declared_field_no_script_knows_fails(package) -> None:
    data = contract()
    data["fields"]["ghost_field"] = {}
    errors = package(data, doc=DOC + "\n`ghost_field` is documented.\n")
    assert any("no script or schema knows" in e and "ghost_field" in e for e in errors)


def test_an_unread_field_is_allowed_only_when_marked(package) -> None:
    data = contract()
    data["fields"]["ghost_field"] = {"unread": True}
    assert package(data, doc=DOC + "\n`ghost_field` is for the reader.\n") == []


def test_a_kernel_enum_that_drifts_from_the_contract_fails(package) -> None:
    errors = package(kernel=KERNEL.replace('MODES = {"A", "B"}', 'MODES = {"A", "B", "C"}'))
    assert any("MODES accepts" in e for e in errors)


def test_an_enum_no_constant_enforces_fails_unless_declared_unenforced(package) -> None:
    data = contract()
    data["scripts"]["scripts/kernel.py"]["enums"] = {}
    assert any("no script constant enforces" in e for e in package(data))
    data["fields"]["mode"]["enforced"] = False
    assert package(data) == []


def test_a_field_missing_from_the_docs_fails(package) -> None:
    errors = package(doc=DOC.replace("  item_id\n", ""))
    assert any("fields not documented" in e and "item_id" in e for e in errors)


def test_an_enum_value_documented_in_prose_only_fails(package) -> None:
    """The web-app-auditor defect: docs said "do not ship", the validator wants do_not_ship."""
    data = contract()
    data["fields"]["mode"]["enum"] = ["A", "do_not_ship"]
    kernel = KERNEL.replace('MODES = {"A", "B"}', 'MODES = {"A", "do_not_ship"}')
    errors = package(data, kernel=kernel, doc=DOC.replace("mode: A|B", "mode: A|do not ship"),
                     cases=[CASES[0]])
    assert any("enum values not documented verbatim" in e and "mode=do_not_ship" in e for e in errors)


def test_a_documented_field_the_contract_omits_fails(package) -> None:
    errors = package(doc=DOC.replace("  item_id\n", "  item_id\n  dependencies[]\n"))
    assert any("docs name fields" in e and "dependencies" in e for e in errors)


def test_a_passing_eval_case_that_breaks_the_contract_fails(package) -> None:
    cases = [*CASES, {"id": "sneaky", "input": {"mode": "A", "items": [{"item_id": "x", "extra": 1}]},
                      "expect": {"status": "VALID"}}]
    errors = package(cases=cases)
    assert any("sneaky" in e and "unknown field 'extra'" in e for e in errors)


def test_an_off_contract_case_that_expects_rejection_passes(package) -> None:
    assert package(cases=[*CASES, {"id": "x", "input": {"mode": "Z", "junk": 1},
                                   "expect": {"status": "INVALID"}}]) == []


def test_conform_always_checks_cases_that_expect_rejection(package) -> None:
    data = contract()
    data["evals"][0]["conform"] = "always"
    errors = package(data, cases=[*CASES, {"id": "pinned", "input": {"mode": "A", "junk": 1},
                                           "expect": {"status": "INVALID"}}])
    assert any("pinned" in e and "conform: always" in e for e in errors)
    assert any("#bad" in e for e in errors)
    data["evals"][0]["exempt"] = {"bad": "off-enum mode is the point", "pinned": "unknown key is the point"}
    assert package(data, cases=[*CASES, {"id": "pinned", "input": {"mode": "A", "junk": 1},
                                         "expect": {"status": "INVALID"}}]) == []


def test_conform_rejects_an_unknown_mode(package) -> None:
    data = contract()
    data["evals"][0]["conform"] = "sometimes"
    assert any("conform must be" in e for e in package(data))


def test_an_exempt_case_must_actually_break_the_contract(package) -> None:
    data = contract()
    data["evals"][0]["exempt"] = {"ok": "no reason"}
    assert any("drop the exemption" in e for e in package(data))


def test_an_undeclared_expected_status_fails(package) -> None:
    errors = package(cases=[*CASES, {"id": "odd", "input": {"mode": "A"}, "expect": {"status": "MAYBE"}}])
    assert any("'MAYBE' is not a declared output status" in e for e in errors)


def test_a_qualified_field_scopes_its_enum_to_its_parent(package) -> None:
    data = contract()
    data["fields"]["items.state"] = {"enum": ["OPEN"], "enforced": False}
    doc = DOC.replace("  item_id\n", "  item_id\n  state: OPEN\n")
    kernel = KERNEL + "\ndef st(i):\n    return i.get('state')\n"
    ok = [*CASES, {"id": "s", "input": {"mode": "A", "items": [{"item_id": "x", "state": "OPEN"}]},
                   "expect": {"status": "VALID"}}]
    assert package(data, kernel=kernel, doc=doc, cases=ok) == []
    bad = [*CASES, {"id": "s", "input": {"mode": "A", "items": [{"item_id": "x", "state": "SHUT"}]},
                    "expect": {"status": "VALID"}}]
    assert any("items.state='SHUT'" in e for e in package(data, kernel=kernel, doc=doc, cases=bad))


def test_draft_lists_every_script_and_read(package, tmp_path) -> None:
    package()
    draft = skill_contracts.draft("demo")
    assert set(draft["scripts"]) == {"scripts/kernel.py"}
    assert {"mode", "items", "item_id"} <= set(draft["fields"]) | set(draft["internal"])


# --- defects this contract was introduced to catch -----------------------------------------------

def test_the_documented_repair_field_is_the_one_the_kernel_reads() -> None:
    """The original defect: a dependency written as documented must be enforced."""
    kernel = load("repair-operator", "scripts/kernel.py")
    ledger = {"items": [
        {"repair_id": "R1", "finding_ids": ["F1"], "repair_class": "PATCH",
         "status": "PLANNED", "depends_on": ["R9"]},
    ]}
    assert "0:depends-on-missing:R9" in kernel.validate(ledger)["errors"]


def test_an_unknown_repair_mode_is_not_silently_standard() -> None:
    """`mode: deep` used to fall back to standard closure without a word."""
    kernel = load("repair-operator", "scripts/kernel.py")
    out = kernel.validate({"mode": "deep", "items": []})
    assert out["errors"] == ["mode:invalid"] and out["status"] == "INVALID"
    assert kernel.validate({"mode": ["DEEP"], "items": []})["errors"] == ["mode:invalid"]


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


@pytest.mark.parametrize("skill", ["repair-operator", "benchmark-curator"])
def test_kernel_rejects_a_payload_that_is_not_json(skill: str) -> None:
    kernel = ROOT / "skills" / skill / "scripts" / "kernel.py"
    proc = subprocess.run([sys.executable, str(kernel)], input="not json",
                          capture_output=True, text=True, timeout=60, check=False)
    assert proc.returncode == 2 and "not JSON" in proc.stderr
