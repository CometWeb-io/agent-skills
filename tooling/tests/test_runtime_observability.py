"""Synthetic receipt plumbing only; no model/host task evidence is produced."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import runtime_observability as obs

ROOT = Path(__file__).resolve().parents[2]
SECRET = 'sk-secret-never-export'
PRIVATE = '/private/operator/workspace/private-project'


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def make_receipts(root, *, condition='plugin', schema=2):
    hashes = {name: hashlib.sha256(name.encode()).hexdigest() for name in obs.HASH_FIELDS if name not in {'plan_sha256', 'run_config_sha256'}}
    task = {'id': 'task-1', 'case_id': 'case-1', 'source': 'fixture.json', 'prompt': SECRET + PRIVATE,
            'fixture': {'private': PRIVATE}, 'skill': 'release-readiness', 'checks': ['output']}
    plan = {'schema': f'cometweb.real-host-eval-plan/v{schema}', 'tasks': [task],
            'sources': {'fixture.json': 'f' * 64}, 'frozen_hashes': hashes}
    plan['plan_sha256'] = obs._sha(plan)
    manifest = {'schema': 'cometweb.real-host-eval-run/v2', 'plan_sha256': plan['plan_sha256'],
                'host': 'codex', 'host_version': 'synthetic-v0 ' + PRIVATE + SECRET, 'model_requested': SECRET,
                'planned_jobs': 1, 'run_config_sha256': 'c' * 64, 'frozen_hashes': hashes,
                'evidence_class': 'synthetic_fixture', 'argv': [PRIVATE], 'prompt': SECRET,
                'prices_per_mtok': {'input': None, 'output': None}, 'estimated_tokens': 999999}
    record = {'schema': 'cometweb.real-host-eval-record/v2', 'run_id': 'run-1', 'task_id': 'task-1',
              'condition': condition, 'repeat': 0, 'status': 'executed', 'execution_status': 'EXECUTED',
              'model': 'synthetic-model ' + SECRET + PRIVATE, 'input_tokens': 100, 'output_tokens': 20,
              'cost_usd': None, 'num_turns': 2, 'elapsed_seconds': 1.5,
              'argv': [SECRET, PRIVATE], 'env': {'API_KEY': SECRET}, 'output': SECRET,
              'task_outcome_status': 'pass', 'task_outcome_observation': {'PASS': SECRET}}
    if schema == 3:
        manifest['experiment'] = {'harness_sha256': 'd' * 64, 'bundled_tools_sha256': 'e' * 64,
                                  'condition_payload_sha256': {condition: 'a' * 64}}
        record.update(plan_sha256=plan['plan_sha256'], run_config_sha256='c' * 64,
                      frozen_hashes=hashes, condition_payload_sha256='a' * 64,
                      resources={key: record.get(key) for key in obs.METRICS})
        record['resources'].pop('num_turns')
        record['resources']['cost_source'] = None
        record['metadata_status'] = {'model': 'host_reported', 'hardware': 'unavailable'}
    grade = {'schema': 'cometweb.real-host-eval-grades/v2', 'plan_sha256': plan['plan_sha256'],
             'results': [{'run_id': 'run-1', 'task_id': 'task-1', 'condition': condition, 'repeat': 0,
                          'run_status': 'executed', 'checks': {'output': {'status': 'pass', 'reason': SECRET},
                                                            'task_success': {'status': 'pass'}}}]}
    write(root / 'manifest.json', manifest)
    write(root / 'plan.json', plan)
    write(root / 'runs/job/record.json', record)
    write(root / 'grades.json', grade)
    # The exporter must not read these files even if they contain secrets or fail UTF-8 decoding.
    (root / 'runs/job/output.md').write_bytes(b'\xff' + SECRET.encode())
    (root / 'runs/job/events.jsonl').write_bytes(b'\xff' + PRIVATE.encode())
    return manifest, plan, record, grade


@pytest.fixture
def receipts(tmp_path):
    root = tmp_path / 'receipts'
    values = make_receipts(root)
    return root, values


def rewrite(root, values):
    manifest, plan, record, grade = values
    write(root / 'manifest.json', manifest)
    write(root / 'plan.json', plan)
    write(root / 'runs/job/record.json', record)
    write(root / 'grades.json', grade)


def decode_any(value):
    if not value:
        return None
    if 'kvlistValue' in value:
        return {item['key']: decode_any(item['value']) for item in value['kvlistValue']['values']}
    if 'arrayValue' in value:
        return [decode_any(item) for item in value['arrayValue']['values']]
    if 'intValue' in value:
        assert isinstance(value['intValue'], str)
        return int(value['intValue'])
    return next(iter(value.values()))


@pytest.mark.parametrize('format', ['json', 'otlp'])
def test_allowlist_export_does_not_leak_any_raw_freeform_identity_or_material(receipts, format):
    root, _ = receipts
    result = obs.read_receipts(root) if format == 'json' else obs.export_otlp(root)
    text = json.dumps(result)
    for forbidden in (SECRET, PRIVATE, 'synthetic-model', 'synthetic-v0', 'task-1', 'run-1', 'case-1', 'output.md', 'argv', 'API_KEY'):
        assert forbidden not in text
    assert 'synthetic_fixture' in text


def test_structural_pass_never_establishes_task_success(receipts):
    row = obs.read_receipts(receipts[0])['rows'][0]
    assert row['output_contract'] == 'pass'
    assert row['task_success'] is None
    assert row['metrics']['input_tokens'] == 100
    assert row['metrics']['cost_usd'] is None
    assert row['metrics']['tool_calls'] is None
    assert row['metrics']['retries'] is None


@pytest.mark.parametrize('source', [None, 'estimated_from_prices', 'unknown'])
def test_unreported_cost_is_null_even_with_pricing_or_an_estimate(receipts, source):
    root, values = receipts
    values[0]['prices_per_mtok'] = {'input': 100, 'output': 100}
    values[2].update(cost_usd=99.0, cost_source=source)
    rewrite(root, values)
    assert obs.read_receipts(root)['rows'][0]['metrics']['cost_usd'] is None


def test_reported_cost_is_retained_without_a_price_table(receipts):
    root, values = receipts
    values[2].update(cost_usd=0.02, cost_source='host_reported')
    rewrite(root, values)
    assert obs.read_receipts(root)['rows'][0]['metrics']['cost_usd'] == 0.02


def test_no_usage_never_becomes_bytes_div_four_or_manifest_estimate(receipts):
    root, values = receipts
    values[2].pop('input_tokens')
    values[2].pop('output_tokens')
    values[2].update(estimated_input_tokens=500, estimated_output_tokens=30, prompt_bytes=2000)
    rewrite(root, values)
    metrics = obs.read_receipts(root)['rows'][0]['metrics']
    assert metrics['input_tokens'] is None and metrics['output_tokens'] is None


def test_otlp_is_export_logs_request_with_typed_values_and_observation_timestamp(receipts):
    snapshot = obs.read_receipts(receipts[0])
    payload = obs.export_otlp(receipts[0])
    assert set(payload) == {'resourceLogs'}
    scope = payload['resourceLogs'][0]['scopeLogs'][0]
    assert scope['scope']['name'] == 'tooling.runtime_observability'
    log = scope['logRecords'][0]
    assert set(log) == {'observedTimeUnixNano', 'body'}
    assert isinstance(log['observedTimeUnixNano'], str) and int(log['observedTimeUnixNano']) > 0
    body = decode_any(log['body'])
    assert body['identity'] == snapshot['identity']
    assert body['metrics'] == snapshot['rows'][0]['metrics']
    assert body['task_success'] is None
    assert 'timeUnixNano' not in log  # Original event timestamp was not observed.


def test_v3_resources_and_condition_payload_are_supported_without_runner_import(tmp_path):
    root = tmp_path / 'v3'
    make_receipts(root, condition='skill', schema=3)
    result = obs.read_receipts(root)
    assert result['rows'][0]['condition_payload_sha256'] == 'a' * 64
    assert result['rows'][0]['metrics']['input_tokens'] == 100
    assert result['identity']['harness_sha256'] == 'd' * 64


@pytest.mark.parametrize('field', ['candidate_sha256', 'rubric_sha256', 'benchmark_sha256', 'host_config_sha256',
                                   'run_config_sha256', 'payload_sha256'])
def test_drift_blocks_every_frozen_identity_mismatch(tmp_path, field):
    left, right = tmp_path / 'before', tmp_path / 'after'
    make_receipts(left)
    values = make_receipts(right)
    if field == 'run_config_sha256':
        values[0][field] = '1' * 64
    else:
        values[0]['frozen_hashes'][field] = '1' * 64
        values[1]['frozen_hashes'][field] = '1' * 64
        values[1]['plan_sha256'] = obs._sha({k: v for k, v in values[1].items() if k != 'plan_sha256'})
        values[0]['plan_sha256'] = values[3]['plan_sha256'] = values[1]['plan_sha256']
    rewrite(right, values)
    result = obs.compare_receipts(left, right, {'input_tokens': {'max_increase': 10}})
    assert result['comparison_status'] == 'blocked'
    assert 'identity_mismatch:' + field in result['blockers']
    assert all(axis['status'] == 'not_assessed' for axis in result['axes'].values())


def test_drift_requires_exact_case_and_task_identity(tmp_path):
    left, right = tmp_path / 'before', tmp_path / 'after'
    make_receipts(left)
    values = make_receipts(right)
    values[1]['tasks'][0]['case_id'] = 'different-case'
    values[1]['plan_sha256'] = obs._sha({k: v for k, v in values[1].items() if k != 'plan_sha256'})
    values[0]['plan_sha256'] = values[3]['plan_sha256'] = values[1]['plan_sha256']
    rewrite(right, values)
    result = obs.compare_receipts(left, right, {'input_tokens': {'max_increase': 10}})
    assert result['comparison_status'] == 'blocked'
    assert 'identity_mismatch:case_sha256' in result['blockers']
    assert 'identity_mismatch:task_sha256' in result['blockers']


def test_drift_is_per_metric_and_uses_explicit_thresholds(tmp_path):
    left, right = tmp_path / 'before', tmp_path / 'after'
    make_receipts(left)
    values = make_receipts(right)
    values[2]['input_tokens'] = 112
    values[2]['elapsed_seconds'] = 2.0
    rewrite(right, values)
    result = obs.compare_receipts(left, right, {'input_tokens': {'max_increase': 10}, 'elapsed_seconds': {'max_increase': 0.5}})
    assert result['comparison_status'] == 'compared'
    assert result['axes']['plugin:input_tokens']['status'] == 'threshold_exceeded'
    assert result['axes']['plugin:elapsed_seconds']['status'] == 'within_threshold'
    assert result['model_qualification'] == 'not_provided'
    assert result['task_quality'] == 'not_assessed'
    assert 'score' not in result


@pytest.mark.parametrize('mutation,blocker', [('model', 'missing_identity:model_sha256'),
                                            ('source', 'missing_identity:case_sha256'),
                                            ('inventory', 'incomplete_inventory'),
                                            ('cost', 'missing_measurement:cost_usd')])
def test_missing_metadata_or_measurement_blocks_drift(tmp_path, mutation, blocker):
    left, right = tmp_path / 'before', tmp_path / 'after'
    make_receipts(left)
    values = make_receipts(right)
    field = 'input_tokens'
    if mutation == 'model':
        values[2]['model'] = None
    elif mutation == 'source':
        values[1]['sources'] = {}
        values[1]['plan_sha256'] = obs._sha({k: v for k, v in values[1].items() if k != 'plan_sha256'})
        values[0]['plan_sha256'] = values[3]['plan_sha256'] = values[1]['plan_sha256']
    elif mutation == 'inventory':
        values[0]['planned_jobs'] = 2
    else:
        field = 'cost_usd'
    rewrite(right, values)
    result = obs.compare_receipts(left, right, {field: {'max_increase': 10}})
    assert result['comparison_status'] == 'blocked'
    assert blocker in result['blockers']


@pytest.mark.parametrize('status,execution', [('not_run', 'NOT_RUN'), ('error', 'ERROR'), ('timeout', 'ERROR')])
def test_missing_execution_cannot_produce_drift_pass(tmp_path, status, execution):
    left, right = tmp_path / 'before', tmp_path / 'after'
    make_receipts(left)
    values = make_receipts(right)
    values[2].update(status=status, execution_status=execution)
    values[3]['results'][0]['run_status'] = status
    if status == 'not_run':
        for key in obs.METRICS:
            values[2].pop(key, None)
    rewrite(right, values)
    result = obs.compare_receipts(left, right, {'input_tokens': {'max_increase': 10}})
    assert result['comparison_status'] == 'blocked'
    assert 'missing_completed_execution' in result['blockers']
    row = obs.read_receipts(right)['rows'][0]
    assert row['output_contract'] is None
    assert row['task_success'] is None


@pytest.mark.parametrize('thresholds', [{}, {'made_up_score': {'max_increase': 1}}, {'input_tokens': {}},
                                       {'input_tokens': {'max_increase': -1}}, {'input_tokens': {'max_increase': True}}])
def test_thresholds_are_explicit_closed_and_nonnegative(receipts, thresholds):
    with pytest.raises(ValueError):
        obs.compare_receipts(receipts[0], receipts[0], thresholds)


@pytest.mark.parametrize('mutation', ['record-id', 'grade-cell', 'grade-plan', 'plan-edit', 'invalid-usage', 'conflicting-status'])
def test_mutated_receipts_are_rejected(receipts, mutation):
    root, values = receipts
    if mutation == 'record-id':
        values[2]['task_id'] = 'not-in-plan'
    elif mutation == 'grade-cell':
        values[3]['results'][0]['condition'] = 'baseline'
    elif mutation == 'grade-plan':
        values[3]['plan_sha256'] = '0' * 64
    elif mutation == 'plan-edit':
        values[1]['tasks'][0]['prompt'] = 'changed after freeze'
    elif mutation == 'invalid-usage':
        values[2]['input_tokens'] = True
    else:
        values[2]['execution_status'] = 'NOT_RUN'
    rewrite(root, values)
    with pytest.raises(ValueError):
        obs.read_receipts(root)


def test_no_grades_is_unknown_but_valid_snapshot(receipts):
    root, _ = receipts
    (root / 'grades.json').unlink()
    row = obs.read_receipts(root)['rows'][0]
    assert row['output_contract'] is None and row['routing'] is None


def test_symlink_receipts_are_refused_without_reading_their_target(receipts, tmp_path):
    root, _ = receipts
    target = tmp_path / 'secret.json'
    target.write_text(SECRET)
    record = root / 'runs/job/record.json'
    record.unlink()
    record.symlink_to(target)
    with pytest.raises((OSError, ValueError)):
        obs.read_receipts(root)


def test_cli_output_and_invalid_diagnostics_never_echo_private_paths(receipts):
    root, values = receipts
    command = [sys.executable, str(ROOT / 'tooling/runtime_observability.py'), 'export', str(root)]
    proc = subprocess.run(command, capture_output=True, text=True)
    assert proc.returncode == 0
    assert SECRET not in proc.stdout + proc.stderr and PRIVATE not in proc.stdout + proc.stderr
    values[2]['schema'] = SECRET + PRIVATE
    rewrite(root, values)
    proc = subprocess.run(command, capture_output=True, text=True)
    assert proc.returncode == 2
    assert SECRET not in proc.stdout + proc.stderr and PRIVATE not in proc.stdout + proc.stderr
    assert json.loads(proc.stdout)['validation'] == 'invalid'


def test_v3_missing_harness_identity_blocks_drift(tmp_path):
    before, after = tmp_path / 'before', tmp_path / 'after'
    make_receipts(before, condition='skill', schema=3)
    values = make_receipts(after, condition='skill', schema=3)
    values[0]['experiment'].pop('harness_sha256')
    rewrite(after, values)
    result = obs.compare_receipts(before, after, {'input_tokens': {'max_increase': 10}})
    assert result['comparison_status'] == 'blocked'
    assert 'missing_identity:harness_sha256' in result['blockers']


def test_different_conditions_never_cancel_each_others_resource_drift(tmp_path):
    before, after = tmp_path / 'before', tmp_path / 'after'
    make_receipts(before)
    make_receipts(after)
    for root, plugin_tokens, baseline_tokens in ((before, 100, 100), (after, 150, 50)):
        manifest = obs._read(root / 'manifest.json')
        manifest['planned_jobs'] = 2
        write(root / 'manifest.json', manifest)
        record = obs._read(root / 'runs/job/record.json')
        record['input_tokens'] = plugin_tokens
        write(root / 'runs/job/record.json', record)
        baseline = copy.deepcopy(record)
        baseline.update(run_id='run-2', condition='baseline', input_tokens=baseline_tokens)
        write(root / 'runs/other/record.json', baseline)
    result = obs.compare_receipts(before, after, {'input_tokens': {'max_increase': 10}})
    assert result['comparison_status'] == 'compared'
    assert result['axes']['plugin:input_tokens']['status'] == 'threshold_exceeded'
    assert result['axes']['baseline:input_tokens']['status'] == 'within_threshold'
    assert result['evidence_classes'] == ['synthetic_fixture']


def test_decimal_threshold_does_not_create_false_cost_regression(tmp_path):
    before, after = tmp_path / 'before', tmp_path / 'after'
    for root, cost in ((before, 0.1), (after, 0.4)):
        values = make_receipts(root)
        values[2].update(cost_usd=cost, cost_source='host_reported')
        rewrite(root, values)
    result = obs.compare_receipts(before, after, {'cost_usd': {'max_increase': 0.3}})
    assert result['axes']['plugin:cost_usd']['status'] == 'within_threshold'
    assert result['axes']['plugin:cost_usd']['absolute_delta'] == 0.3


def test_large_observed_integer_delta_does_not_disappear_in_float_mean(tmp_path):
    before, after = tmp_path / 'before', tmp_path / 'after'
    for root, tokens in ((before, 2**60), (after, 2**60 + 1)):
        values = make_receipts(root)
        values[2]['input_tokens'] = tokens
        rewrite(root, values)
    result = obs.compare_receipts(before, after, {'input_tokens': {'max_increase': 0}})
    assert result['axes']['plugin:input_tokens']['status'] == 'threshold_exceeded'
    assert result['axes']['plugin:input_tokens']['absolute_delta'] == 1


@pytest.mark.parametrize('field', ['model', 'host_version'])
def test_different_observed_model_or_host_version_blocks_drift(tmp_path, field):
    before, after = tmp_path / 'before', tmp_path / 'after'
    make_receipts(before)
    values = make_receipts(after)
    if field == 'model':
        values[2]['model'] = 'different-observed-model'
    else:
        values[0]['host_version'] = 'different-observed-version'
    rewrite(after, values)
    result = obs.compare_receipts(before, after, {'input_tokens': {'max_increase': 10}})
    assert result['comparison_status'] == 'blocked'
    assert 'identity_mismatch:' + ('model_sha256' if field == 'model' else 'host_version_sha256') in result['blockers']
    assert result['axes']['plugin:input_tokens']['reference_mean'] is None


def test_duplicate_run_cells_and_inconsistent_resource_sources_are_rejected(receipts):
    root, values = receipts
    duplicate = copy.deepcopy(values[2])
    duplicate['run_id'] = 'different-run-same-cell'
    write(root / 'runs/duplicate/record.json', duplicate)
    with pytest.raises(ValueError):
        obs.read_receipts(root)
    (root / 'runs/duplicate/record.json').unlink()
    (root / 'runs/duplicate').rmdir()
    values[2]['cost_source'] = 'host_reported'
    values[2]['resources'] = {'cost_source': 'estimated_from_prices'}
    rewrite(root, values)
    with pytest.raises(ValueError):
        obs.read_receipts(root)


def test_cli_drift_exit_reflects_comparison_gate_and_exceeded_axis(receipts, tmp_path):
    root, _ = receipts
    limits = tmp_path / 'thresholds.json'
    write(limits, {'input_tokens': {'max_increase': 0}})
    command = [sys.executable, str(ROOT / 'tooling/runtime_observability.py'), 'drift', str(root), str(root),
               '--thresholds', str(limits)]
    proc = subprocess.run(command, capture_output=True, text=True)
    assert proc.returncode == 0
    assert json.loads(proc.stdout)['comparison_status'] == 'compared'
    write(limits, {SECRET + PRIVATE: {'max_increase': 0}})
    proc = subprocess.run(command, capture_output=True, text=True)
    assert proc.returncode == 2
    assert SECRET not in proc.stdout + proc.stderr and PRIVATE not in proc.stdout + proc.stderr
