"""Regression cases for unjustified readiness, evaluated on the actual packages."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def contract(skill):
    directory = ROOT / "skills" / skill
    spec = importlib.util.spec_from_file_location(skill, directory / "scripts/output_contract.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    cases = json.loads((directory / "evals/cases.json").read_text(encoding="utf-8"))
    return module, copy.deepcopy(next(c["input"] for c in cases if c["id"] == "valid-complete"))


@pytest.mark.parametrize("section", ["company", "icp", "positioning", "product", "pricing", "proof", "discovery"])
@pytest.mark.parametrize("empty", [None, "", "  ", {}, []])
def test_empty_profile_section_never_completes(section, empty):
    module, value = contract("competitor-profiling")
    value["profile"]["sections"][section] = empty
    assert module.validate(value)


@pytest.mark.parametrize("state", ["UNKNOWN", "HYPOTHESIS"])
def test_unverified_claim_never_becomes_ready(state):
    module, value = contract("competitor-profiling")
    value["profile"]["claims"][0]["state"] = state
    assert module.validate(value)


@pytest.mark.parametrize("skill", ["competitor-profiling", "research-program-operator"])
@pytest.mark.parametrize("date", ["not-a-date", "2026-02-30", "2026-10-05T12:00:00"])
def test_invalid_or_timezone_ambiguous_date(skill, date):
    module, value = contract(skill)
    value["profile" if skill == "competitor-profiling" else "program"]["as_of"] = date
    assert module.validate(value)


def test_source_cannot_be_observed_after_snapshot():
    module, value = contract("competitor-profiling")
    value["profile"]["sources"][0]["observed_at"] = "2099-01-01"
    assert module.validate(value)


@pytest.mark.parametrize("field", ["unknowns", "governance"])
def test_research_complete_cannot_hide_blockers(field):
    module, value = contract("research-program-operator")
    value["program"][field] = ["Unresolved approval or inference"]
    assert module.validate(value)


@pytest.mark.parametrize("status", ["UNKNOWN", "BLOCKED", "NOT_REPORTED"])
def test_research_ready_requires_passing_gates(status):
    module, value = contract("research-program-operator")
    value["program"]["gates"][0]["status"] = status
    value["research_handoff"]["status"] = "READY"
    assert module.validate(value)


@pytest.mark.parametrize("field", ["hypotheses", "next_studies"])
def test_research_empty_definition(field):
    module, value = contract("research-program-operator")
    value["program"][field] = [{}]
    assert module.validate(value)


def test_manuscript_readiness_is_not_publication_authorization():
    module, value = contract("research-program-operator")
    value["research_handoff"].update(status="READY", target="publish")
    assert module.validate(value)


@pytest.mark.parametrize("skill", ["competitor-profiling", "research-program-operator"])
def test_valid_complete_contract(skill):
    module, value = contract(skill)
    assert module.validate(value) == []


@pytest.mark.parametrize("delimiter", ["---MALFORMED", "----", "--- extra"])
def test_frontmatter_rejects_malformed_delimiters(tmp_path, delimiter):
    import compatibility
    path = tmp_path / "SKILL.md"
    path.write_text(f"---\nname: example\ndescription: example\n{delimiter}\n")
    with pytest.raises(ValueError, match="frontmatter"):
        compatibility.parse_frontmatter(path)


def test_frontmatter_accepts_crlf(tmp_path):
    import compatibility
    directory = tmp_path / "example"
    directory.mkdir()
    path = directory / "SKILL.md"
    path.write_bytes(b"---\r\nname: example\r\ndescription: example\r\n---\r\n")
    assert compatibility.parse_frontmatter(path)["name"] == "example"


@pytest.mark.parametrize("quoted", ["~~~\nuse ai-council\n~~~", "    use ai-council", "\tuse ai-council",
                                   '"' + "x " * 2000 + 'use ai-council"',
                                   "~~~~\n~~~\nuse ai-council\n~~~~", "~~~\nuse ai-council"])
def test_pasted_invocation_never_routes(quoted):
    from route_skill import route
    registry = json.loads((ROOT / "registry/skills.json").read_text())
    policy = json.loads((ROOT / "registry/routing-policy.json").read_text())
    assert route(quoted, registry, policy)["primary_skill"] != "ai-council"


def test_context_distinguishes_discovery_and_nested_resources(tmp_path):
    import context_budget
    skill = tmp_path / "example"
    nested = skill / "references" / "packs"
    nested.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: example\ndescription: short\n---\n" + "body " * 100)
    (nested / "reference.md").write_text("reference " * 20)
    row = context_budget.measure_skill(skill)
    assert row["reference_files"] == 1 and row["depth_bytes"] == 200
    assert row["discovery_metadata_tokens_estimated"] < row["activation_instruction_tokens_estimated"]


def test_release_rejects_scaffold_content(tmp_path):
    import plugin_release
    skill = tmp_path / "skills" / "example"
    skill.mkdir(parents=True)
    path = skill / "SKILL.md"
    path.write_text("Replace these rules with the skill's real contract")
    assert plugin_release.content_errors(tmp_path)
    path.write_text("A implemented contract")
    assert plugin_release.content_errors(tmp_path) == []


def test_attestation_requires_full_gates_and_platform_matrix():
    import yaml
    workflow = yaml.safe_load((ROOT / ".github/workflows/attest-packages.yml").read_text())
    jobs = workflow["jobs"]
    assert jobs["attest"]["needs"] == "platforms"
    assert jobs["platforms"]["uses"] == "./.github/workflows/platform-matrix.yml"
    runs = [s.get("run") for s in jobs["attest"]["steps"]]
    assert "uv run python tooling/check_all.py --ci" in runs
