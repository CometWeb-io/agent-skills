"""Supplied sensitivity and project boundaries cannot become public authority."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _context_fixtures import build_valid_envelope, load_script

validator = load_script("validate_context_envelope")
planner = load_script("context_plan")
snapshot = load_script("repo_snapshot")


@pytest.mark.parametrize("source,fact", [("confidential", "public"), ("restricted", "internal"),
                                        ("internal", "public")])
def test_fact_cannot_downgrade_its_source(source, fact):
    data = build_valid_envelope()
    data["sources"][0]["sensitivity"] = source
    data["facts"][0]["sensitivity"] = fact
    with pytest.raises(ValueError, match="source sensitivity"):
        validator.validate(data)


def test_public_example_rejects_private_source_even_without_facts():
    data = build_valid_envelope()
    data.update(context_scope="public_example", facts=[])
    with pytest.raises(ValueError, match="public_example"):
        validator.validate(data)


@pytest.mark.parametrize("value", [None, [], "invented"])
def test_explicit_invalid_scope_is_not_a_private_default(value):
    data = build_valid_envelope()
    data["context_scope"] = value
    with pytest.raises(ValueError, match="context_scope"):
        validator.validate(data)


def test_project_envelope_requires_matching_declared_source_binding():
    data = build_valid_envelope()
    data.update(context_scope="project_context", project_ref="project-a")
    data["sources"][0]["project_ref"] = "project-b"
    with pytest.raises(ValueError, match="project_ref"):
        validator.validate(data)
    data["sources"][0]["project_ref"] = "project-a"
    validator.validate(data)


def test_public_profiles_do_not_read_malformed_private_overlay(tmp_path):
    path = tmp_path / "source-registry.json"
    path.write_text(json.dumps({"profiles": {"product": {"preferred_source_groups": ["website"]}}}))
    path.with_name("source-registry.local.json").write_text("MALFORMED-PRIVATE-OVERLAY")
    assert planner.load_profiles(path, context_scope="public_example")["product"] == ["website"]
    assert planner.load_profiles(path, context_scope="project_context")["product"] == ["website"]
    with pytest.raises(ValueError):
        planner.load_profiles(path)


def test_public_plan_excludes_private_groups_without_exposing_ids(monkeypatch):
    monkeypatch.setattr(planner, "load_profiles", lambda **kwargs: {"product": ["website", "PRIVATE-GROUP-MARKER"]})
    result = planner.plan("Sprawdz repo", context_scope="public_example")
    assert result["source_groups"] == ["website"]
    assert result["blocked_source_group_count"] == 1
    assert "PRIVATE-GROUP-MARKER" not in json.dumps(result)


def test_legacy_context_is_private_and_sensitivity_can_increase():
    data = build_valid_envelope()
    data["facts"][0]["sensitivity"] = "confidential"
    validator.validate(data)


def test_public_snapshot_does_not_inspect_workspace(tmp_path):
    proc = subprocess.run([sys.executable, snapshot.__file__, "--context-scope", "public_example", "--json"],
                          cwd=tmp_path, capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stderr
    result = json.loads(proc.stdout)
    assert result["execution_status"] == "NOT_RUN" and result["repos"] == []
    assert result["root_available"] is None and result["snapshot_ref"] is None


@pytest.mark.parametrize("repos", [[], ["project-a", "project-b"]])
def test_project_snapshot_refuses_estate_scan(repos, tmp_path):
    argv = [sys.executable, snapshot.__file__, "--context-scope", "project_context", "--root", str(tmp_path), "--json"]
    for repo in repos:
        argv.extend(["--repo", repo])
    proc = subprocess.run(argv, capture_output=True, text=True, check=False)
    assert proc.returncode != 0 and "exactly one --repo" in proc.stderr


def test_fact_uses_strictest_of_multiple_sources():
    data = build_valid_envelope()
    extra = dict(data['sources'][0], source_id='source-restricted', sensitivity='restricted')
    data['sources'].append(extra)
    data['facts'][0].update(source_ids=[data['sources'][0]['source_id'], extra['source_id']],
                            sensitivity='confidential')
    with pytest.raises(ValueError, match='source sensitivity'):
        validator.validate(data)
    data['facts'][0]['sensitivity'] = 'restricted'
    validator.validate(data)


def test_explicit_public_example_accepts_public_records():
    data = build_valid_envelope()
    data['context_scope'] = 'public_example'
    for record in data['sources'] + data['facts']:
        record['sensitivity'] = 'public'
    validator.validate(data)


def test_public_snapshot_returns_before_inspection(monkeypatch, capsys):
    def forbidden(*args, **kwargs):
        pytest.fail('public example attempted workspace inspection')
    for name in ('default_root', 'load_registry', 'snapshot'):
        monkeypatch.setattr(snapshot, name, forbidden)
    monkeypatch.setattr(sys, 'argv', [snapshot.__file__, '--context-scope', 'public_example', '--json'])
    snapshot.main()
    assert json.loads(capsys.readouterr().out)['execution_status'] == 'NOT_RUN'


@pytest.mark.parametrize('options', [['--root', 'private-root'], ['--registry', 'private-registry'],
                                     ['--repo', 'private-repo'], ['--include-paths']])
def test_public_snapshot_refuses_workspace_options(options):
    proc = subprocess.run([sys.executable, snapshot.__file__, '--context-scope', 'public_example', *options],
                          capture_output=True, text=True, check=False)
    assert proc.returncode != 0 and 'does not accept workspace inspection options' in proc.stderr
    assert not proc.stdout
