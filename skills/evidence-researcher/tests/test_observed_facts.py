"""Controlled local observations; these do not authenticate external facts."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

spec = importlib.util.spec_from_file_location("observation_fixture", Path(__file__).with_name("test_evidence_admission.py"))
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)
kernel, ledger = fixture.kernel, fixture.ledger


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def case(tmp_path):
    graph = ledger()
    claim = graph["claims"][0]
    claim.update(basis="verified_fact", claim_text="The controlled record reports 12 completed checks.",
                 claim_type="dataset_fact", temporal_sensitivity="static", scope={"record": "local-run"})
    graph["evidence"][0]["basis"] = "verified_fact"
    graph["evidence"][0]["locator"] = "/run/completed"
    graph["sources"][0].update(canonical_ref="controlled:local-run", source_class="USER_FILE", provenance_lane="USER_SUPPLIED")
    raw = b'{"run":{"completed":12},"secret":"synthetic-do-not-echo"}'
    (tmp_path / "run.json").write_bytes(raw)
    context = {"question": "Review the controlled run", "decision_type": "option_selection", "purpose": "document_review"}
    check = {"claim_id": claim["claim_id"], "claim_hash": digest(claim),
             "source_id": graph["sources"][0]["source_id"], "source_hash": digest(graph["sources"][0]),
             "evidence_id": graph["evidence"][0]["evidence_id"], "evidence_hash": digest(graph["evidence"][0]),
             "path": "run.json", "sha256": hashlib.sha256(raw).hexdigest(),
             "pointer": "/run/completed", "expected": 12, "observed_scope": "document_content"}
    plan = {"version": "local-fact-check/v1", "research_id": graph["research_id"],
            "as_of": graph["research_contract"]["as_of"], "context_hash": digest(context), "checks": [check]}
    return graph, plan, context


def observe(tmp_path, graph, plan, context):
    return kernel.observe_facts(graph, plan, tmp_path, context)


def test_actual_bytes_checked_without_returning_values(tmp_path):
    graph, plan, context = case(tmp_path)
    result = observe(tmp_path, graph, plan, context)
    assert result["status"] == "CHECKED"
    assert result["claims"][0]["status"] == "MATCH"
    assert result["claims"][0]["observed_scope"] == "document_content"
    assert result["execution_authorized"] is False
    assert "synthetic-do-not-echo" not in json.dumps(result)
    assert "expected" not in result["claims"][0]


@pytest.mark.parametrize("change", ["bytes", "predicate", "claim", "scope", "time", "context", "source", "legacy", "receipt"])
def test_metadata_and_replayed_receipts_do_not_replace_observation(tmp_path, change):
    graph, plan, context = case(tmp_path)
    if change == "bytes":
        (tmp_path / "run.json").write_text('{"run":{"completed":9}}')
    elif change == "predicate":
        plan["checks"][0]["expected"] = 13
    elif change == "claim":
        graph["claims"][0]["claim_text"] = "The controlled record reports 900 completed checks."
    elif change == "scope":
        graph["claims"][0]["scope"] = {"record": "another-run"}
    elif change == "time":
        graph["research_contract"]["as_of"] = "2030-01-01T00:00:00Z"
    elif change == "context":
        context["question"] = "Authorize production launch"
    elif change == "source":
        graph["sources"][0]["canonical_ref"] = "controlled:other"
    elif change == "legacy":
        graph["claims"][0].pop("basis")
        plan["checks"][0]["claim_hash"] = digest(graph["claims"][0])
    else:
        graph["observations"] = {"status": "CHECKED", "claims": [{"status": "MATCH"}]}
        (tmp_path / "run.json").unlink()
    result = observe(tmp_path, graph, plan, context)
    assert result["status"] != "CHECKED"
    assert "synthetic-do-not-echo" not in json.dumps(result)


@pytest.mark.parametrize("basis", ["user_supplied", "assumption", "framework_method"])
def test_observation_does_not_upgrade_nonfact_basis(tmp_path, basis):
    graph, plan, context = case(tmp_path)
    graph["claims"][0]["basis"] = basis
    plan["checks"][0]["claim_hash"] = digest(graph["claims"][0])
    assert observe(tmp_path, graph, plan, context)["status"] != "CHECKED"


@pytest.mark.parametrize("path", ["../run.json", "/run.json", "a/../../run.json", "a\\run.json", "./run.json", "C:run.json", "run.json/"])
def test_plan_cannot_read_outside_capability_root(tmp_path, path):
    graph, plan, context = case(tmp_path)
    plan["checks"][0]["path"] = path
    with pytest.raises(ValueError):
        observe(tmp_path, graph, plan, context)


@pytest.mark.parametrize("kind", ["symlink", "directory", "hardlink", "fifo"])
def test_nonregular_or_aliased_source_is_not_read(tmp_path, kind):
    graph, plan, context = case(tmp_path)
    original = tmp_path / "run.json"
    original.rename(tmp_path / "original.json")
    if kind == "symlink":
        original.symlink_to(tmp_path / "original.json")
    elif kind == "directory":
        original.mkdir()
    elif kind == "hardlink":
        os.link(tmp_path / "original.json", original)
    else:
        if not hasattr(os, "mkfifo"):
            pytest.skip("no FIFO support")
        os.mkfifo(original)
    assert observe(tmp_path, graph, plan, context)["status"] != "CHECKED"


@pytest.mark.parametrize("raw", [b'{"run":{"completed":12,"completed":9}}', b'{"run":{"completed":NaN}}', b'{"run":{"completed":1e999}}', b'\xff', b'x' * (4 * 1024 * 1024 + 1)])
def test_invalid_source_has_no_positive_or_raw_error_echo(tmp_path, raw):
    graph, plan, context = case(tmp_path)
    (tmp_path / "run.json").write_bytes(raw)
    plan["checks"][0]["sha256"] = hashlib.sha256(raw).hexdigest()
    result = observe(tmp_path, graph, plan, context)
    assert result["status"] != "CHECKED"
    assert "completed" not in json.dumps(result)


def test_equality_preserves_json_types(tmp_path):
    graph, plan, context = case(tmp_path)
    plan["checks"][0]["expected"] = True
    assert observe(tmp_path, graph, plan, context)["status"] != "CHECKED"


def test_neighboring_true_field_does_not_check_the_claim_locator(tmp_path):
    graph, plan, context = case(tmp_path)
    plan["checks"][0].update(pointer="/secret", expected="synthetic-do-not-echo")
    assert observe(tmp_path, graph, plan, context)["status"] != "CHECKED"


@pytest.mark.parametrize("mutation", ["duplicate", "unknown_field", "empty", "missing_context", "wrong_version"])
def test_malformed_plan_is_refused(tmp_path, mutation):
    graph, plan, context = case(tmp_path)
    if mutation == "duplicate":
        plan["checks"].append(copy.deepcopy(plan["checks"][0]))
    elif mutation == "unknown_field":
        plan["checks"][0]["verified"] = True
    elif mutation == "empty":
        plan["checks"] = []
    elif mutation == "missing_context":
        del plan["context_hash"]
    else:
        plan["version"] = "unsupported"
    with pytest.raises(ValueError):
        observe(tmp_path, graph, plan, context)


def test_cli_reruns_sources_and_fails_after_change(tmp_path):
    graph, plan, context = case(tmp_path)
    for name, value in (("graph", graph), ("plan", plan), ("context", context)):
        (tmp_path / (name + ".json")).write_text(json.dumps(value))
    script = Path(__file__).resolve().parents[1] / "scripts/evidence_kernel.py"
    args = [sys.executable, str(script), "observe", "--ledger-json", str(tmp_path / "graph.json"),
            "--check-plan-json", str(tmp_path / "plan.json"), "--source-root", str(tmp_path),
            "--consumer-context-json", str(tmp_path / "context.json")]
    first = subprocess.run(args, capture_output=True, text=True, timeout=10)
    assert first.returncode == 0, first.stderr
    assert json.loads(first.stdout)["status"] == "CHECKED"
    (tmp_path / "run.json").write_text('{"run":{"completed":9}}')
    second = subprocess.run(args, capture_output=True, text=True, timeout=10)
    assert second.returncode == 1
    assert json.loads(second.stdout)["status"] != "CHECKED"


@pytest.mark.parametrize("basis", ["user_supplied", "assumption", "framework_method"])
def test_four_basis_classes_are_valid_but_not_interchangeable_with_verified(tmp_path, basis):
    graph, _, _ = case(tmp_path)
    graph["claims"][0].update(basis=basis, status="PARTIAL")
    graph["evidence"][0]["basis"] = basis
    assert kernel.validate_ledger(graph)["valid"] is True
    graph["claims"][0]["status"] = "VERIFIED"
    assert kernel.validate_ledger(graph)["valid"] is False


def test_document_content_fact_keeps_framework_origin(tmp_path):
    graph, plan, context = case(tmp_path)
    graph["sources"][0]["source_class"] = "FRAMEWORK"
    plan["checks"][0]["source_hash"] = digest(graph["sources"][0])
    assert observe(tmp_path, graph, plan, context)["status"] == "CHECKED"
    assert graph["sources"][0]["source_class"] == "FRAMEWORK"


@pytest.mark.parametrize("basis", [None, [], {}, "invented"])
@pytest.mark.parametrize("field", ["claims", "evidence"])
def test_unknown_or_malformed_basis_fails_validation(tmp_path, basis, field):
    graph, _, _ = case(tmp_path)
    graph[field][0]["basis"] = basis
    assert kernel.validate_ledger(graph)["valid"] is False


def test_missing_legacy_basis_is_explicitly_unassessed():
    report = kernel.validate_ledger(ledger())
    assert report["valid"] is True
    assert any("basis is unassessed" in warning for warning in report["warnings"])


def test_source_text_cannot_become_another_filename(tmp_path):
    root = tmp_path / "controlled"
    root.mkdir()
    graph, plan, context = case(root)
    outside = tmp_path / "outside.json"
    outside.write_text('{"run":{"completed":12},"secret":"outside-capability-canary"}')
    raw = str(outside).encode()
    (root / "run.json").write_bytes(raw)
    plan["checks"][0]["sha256"] = hashlib.sha256(raw).hexdigest()
    assert observe(root, graph, plan, context)["status"] != "CHECKED"


def test_source_root_ancestor_alias_is_refused(tmp_path):
    parent = tmp_path / "real"
    root = parent / "controlled"
    root.mkdir(parents=True)
    graph, plan, context = case(root)
    alias = tmp_path / "alias"
    alias.symlink_to(parent, target_is_directory=True)
    assert observe(alias / "controlled", graph, plan, context)["status"] != "CHECKED"


def count_case(tmp_path):
    graph, plan, context = case(tmp_path)
    rows = [{'state': 'ok', 'checked': True}, {'state': 'ok', 'checked': False},
            {'state': 'bad', 'checked': True}, {'state': 'ok', 'checked': True}, {'checked': True}]
    raw = json.dumps({'records': rows, 'private': 'count-canary'}).encode()
    (tmp_path / 'run.json').write_bytes(raw)
    graph['claims'][0]['claim_text'] = 'Exactly two records are ok and checked.'
    graph['evidence'][0]['locator'] = '/records'
    plan['checks'][0].update(claim_hash=digest(graph['claims'][0]), evidence_hash=digest(graph['evidence'][0]),
                            pointer='/records', sha256=hashlib.sha256(raw).hexdigest(), operator='count_matching',
                            where={'state': 'ok', 'checked': True}, expected=2)
    return graph, plan, context


def test_count_predicate_is_computed_from_actual_rows_not_declared_count(tmp_path):
    graph, plan, context = count_case(tmp_path)
    result = observe(tmp_path, graph, plan, context)
    assert result['status'] == 'CHECKED'
    assert 'count-canary' not in json.dumps(result)
    plan['checks'][0]['expected'] = 3
    assert observe(tmp_path, graph, plan, context)['status'] == 'NOT_CHECKED'


@pytest.mark.parametrize('field,value', [('where', {}), ('where', {'state': ['ok']}),
    ('expected', True), ('expected', 2.), ('expected', -1), ('operator', 'execute'), ('reference_result', 2)])
def test_count_plan_rejects_unbounded_or_ambiguous_predicates(tmp_path, field, value):
    graph, plan, context = count_case(tmp_path)
    plan['checks'][0][field] = value
    with pytest.raises(ValueError): observe(tmp_path, graph, plan, context)


def test_count_matching_preserves_json_scalar_types(tmp_path):
    graph, plan, context = count_case(tmp_path)
    plan['checks'][0]['where'] = {'checked': 1}
    plan['checks'][0]['expected'] = 0
    assert observe(tmp_path, graph, plan, context)['status'] == 'CHECKED'


def test_count_refuses_nonobject_rows_without_publishing_source_values(tmp_path):
    graph, plan, context = count_case(tmp_path)
    raw = b'{"records":[{"state":"ok"},"count-canary"]}'
    (tmp_path / 'run.json').write_bytes(raw)
    plan['checks'][0]['sha256'] = hashlib.sha256(raw).hexdigest()
    result = observe(tmp_path, graph, plan, context)
    assert result['status'] == 'NOT_CHECKED'
    assert 'count-canary' not in json.dumps(result)


def test_literal_text_presence_is_document_content_not_entailment(tmp_path):
    graph, plan, context = case(tmp_path)
    raw = b'{"note":"The document does not authorize launch. private-text-canary"}'
    (tmp_path / 'run.json').write_bytes(raw)
    graph['claims'][0]['claim_text'] = 'The pinned document contains the literal word launch.'
    graph['evidence'][0]['locator'] = '/note'
    plan['checks'][0].update(claim_hash=digest(graph['claims'][0]), evidence_hash=digest(graph['evidence'][0]),
                            pointer='/note', sha256=hashlib.sha256(raw).hexdigest(), operator='text_present', expected='launch')
    result = observe(tmp_path, graph, plan, context)
    assert result['status'] == 'CHECKED'
    assert result['execution_authorized'] is False
    assert 'private-text-canary' not in json.dumps(result)
    plan['checks'][0]['expected'] = 'unseen phrase'
    assert observe(tmp_path, graph, plan, context)['status'] == 'NOT_CHECKED'
    plan['checks'][0]['observed_scope'] = 'controlled_state'
    with pytest.raises(ValueError): observe(tmp_path, graph, plan, context)
