"""Freshness evidence, dependency impact and diagnostic boundaries; no live calls."""
import datetime as dt
import json
import sys
from pathlib import Path

import pytest
import yaml

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _tooling_fixtures import root  # noqa: F401
from check_knowledge import audit, main
from doctor import inspect


@pytest.fixture
def data():
    return {"schema": "cometweb.knowledge-rules/v1", "rules": [{
        "id": "limit", "kind": "standard", "state": "active", "statement": "Synthetic limit",
        "scope": "fixture", "verified_at": "2026-10-01", "ttl_days": 30,
        "sources": ["https://example.invalid/spec"], "regression_tests": ["fixture"],
        "dependencies": {"skills": ["*"], "adapters": ["skills/*/agents/openai.yaml"], "tooling": []},
    }]}


@pytest.mark.parametrize("day,status,review", [("2026-10-31", "within_ttl", "current_record"),
                                               ("2026-11-01", "stale", "needs_review")])
def test_ttl_boundary_impacts_current_catalog_without_claiming_contradiction(data, day, status, review):
    before = json.dumps(data)
    result = audit(data, dt.date.fromisoformat(day), [{"id": "new-skill", "version": "2.0.0"}])
    rule = result["results"][0]
    assert rule["status"] == status and rule["review_status"] == review
    assert rule["expires_on"] == "2026-10-31"
    assert rule["claim_truth"] == "not_reverified"
    assert rule["dependencies"]["skills"] == [{"id": "new-skill", "version": "2.0.0"}]
    assert rule["dependencies"]["adapters"] == ["skills/new-skill/agents/openai.yaml"]
    assert result["needs_review"]["skills"] == ({"new-skill": ["limit"]} if review == "needs_review" else {})
    assert result["external_verification"] == "not_run"
    assert json.dumps(data) == before


def test_current_record_can_have_separately_recorded_contradiction(data):
    data["rules"][0]["contradiction"] = {"observed_at": "2026-10-02", "url": "https://example.invalid/change", "note": "Synthetic contrary requirement"}
    result = audit(data, dt.date(2026, 10, 3))["results"][0]
    assert result["status"] == "within_ttl"
    assert result["claim_truth"] == "recorded_contradiction"
    assert result["review_status"] == "needs_review"


@pytest.mark.parametrize("evidence", [[], {"url": 1}, {}, {"observed_at": "2026-10-02", "url": "file:///tmp/secret", "note": "Invalid"},
                                       {"observed_at": "2999-01-01", "url": "https://example.invalid", "note": "Future"}])
def test_contradiction_requires_source_evidence(data, evidence):
    data["rules"][0]["contradiction"] = evidence
    with pytest.raises(ValueError):
        audit(data, dt.date(2026, 10, 3))


@pytest.mark.parametrize("deps", [{"skills": ["missing"]}, {"adapters": ["../private"]},
                                  {"adapters": ["/private/secret"]}, {"skills": ["*", "demo"]},
                                  {"skills": "demo"}, {"unknown": []}])
def test_bad_dependencies_fail_instead_of_silently_losing_impact(data, deps):
    data["rules"][0]["dependencies"] = deps
    with pytest.raises(ValueError):
        audit(data, dt.date(2026, 10, 3), [{"id": "demo", "version": "1.0.0"}])


def test_fixed_adapter_dependency_does_not_require_selected_skills(data):
    data["rules"][0]["dependencies"] = {"adapters": ["tooling/adapter_metadata.py"]}
    result = audit(data, dt.date(2026, 11, 1), [])
    assert result["needs_review"]["adapters"] == {"tooling/adapter_metadata.py": ["limit"]}


@pytest.mark.parametrize("evidence", [[], {"read_at": "2026-10-01", "findings": [1]}, {}, {"read_at": "2026-09-30", "findings": [{"url": "https://example.invalid/spec"}]},
    {"read_at": "2026-10-01", "findings": [{"url": "https://other.invalid", "locator": "section", "note": "Read", "assessment": "supports"}]}])
def test_verification_cannot_be_rebound_to_an_unread_date_or_source(data, evidence):
    data["rules"][0]["verification"] = evidence
    with pytest.raises(ValueError):
        audit(data, dt.date(2026, 10, 3))


def test_cli_advisory_strict_and_bad_input(root, data, capsys):
    path = root / "registry/knowledge-rules.json"
    path.write_text(json.dumps(data))
    before = path.read_bytes()
    assert main([str(path), "--as-of", "2026-11-01"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["needs_review"]["skills"] == {"demo": ["limit"]}
    assert main([str(path), "--as-of", "2026-11-01", "--strict"]) == 1
    capsys.readouterr()
    assert main([str(path), "--as-of", "2026-10-31", "--strict"]) == 0
    assert path.read_bytes() == before
    path.write_text('{bad json')
    assert main([str(path)]) == 2
    assert "FAIL:" in capsys.readouterr().err


def test_doctor_missing_cli_does_not_claim_model_incompetence(root, monkeypatch, data):
    monkeypatch.setattr("doctor.shutil.which", lambda name: None)
    data["rules"][0]["verified_at"] = "2000-01-01"
    (root / "registry/knowledge-rules.json").write_text(json.dumps(data))
    catalog = root / "registry/skills.json"
    entries = json.loads(catalog.read_text())
    entries["skills"].append({"id": "other", "version": "2.0.0"})
    catalog.write_text(json.dumps(entries))
    result = inspect(root, "demo", root / "uninstalled")
    assert not any(result["local_executables"].values())
    assert result["installed"] == "missing"
    assert result["model_competence"] == "unknown"
    assert result["native_execution"] == "not_run"
    assert result["runtime_acceptance"] == "not_assessed"
    assert result["knowledge"]["status"] == "needs_review"
    assert result["knowledge"]["rules"][0]["dependencies"]["skills"] == [{"id": "demo", "version": "1.0.0"}]
    assert result["knowledge"]["rules"][0]["dependencies"]["adapters"] == ["skills/demo/agents/openai.yaml"]
    assert result["issues"] == ["not_installed"]
    assert len(result["baseline"]["registry_sha256"]) == 64
    assert len(result["source_entrypoint_sha256"]) == 64


def test_workflow_only_reports_with_read_permissions():
    path = TOOLS.parent / ".github/workflows/knowledge-freshness.yml"
    workflow = yaml.safe_load(path.read_text())
    # PyYAML reads GitHub's on key as a YAML 1.1 boolean.
    assert set(workflow[True]) == {"schedule", "workflow_dispatch"}
    assert workflow["permissions"] == {"contents": "read"}
    steps = workflow["jobs"]["report"]["steps"]
    commands = [s["run"] for s in steps if "run" in s]
    assert len(commands) == 1 and "check_knowledge.py" in commands[0] and "--strict" not in commands[0]
    assert steps[0]["with"]["persist-credentials"] is False
    assert steps[-1]["uses"].startswith("actions/upload-artifact@")
    assert all("permissions" not in job for job in workflow["jobs"].values())


def test_checked_registry_has_source_bound_reads_and_resolvable_dependencies():
    repository = TOOLS.parent
    data = json.loads((repository / "registry/knowledge-rules.json").read_text())
    skills = json.loads((repository / "registry/skills.json").read_text())["skills"]
    result = audit(data, dt.date(2026, 10, 27), skills)
    assert result["summary"] == {"current_record": 3}
    for rule in result["results"]:
        assert rule["recorded_verification"]["read_at"] == "2026-10-27"
        assert rule["claim_truth"] == "not_reverified"
        for path in rule["dependencies"]["adapters"] + rule["dependencies"]["tooling"]:
            assert (repository / path).is_file()
