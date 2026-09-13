"""Synthetic end-to-end coverage admission; records are not actual source reviews."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value

k = module('integration_kernel', ROOT / 'scripts/roadmap_kernel.py')
c = module('integration_inventory', ROOT / 'scripts/coverage_inventory.py')
fixtures = module('integration_fixtures', ROOT / 'tests/test_roadmap_kernel.py')
AS_OF = '2026-08-25T22:00:00+02:00'
OBSERVED = '2026-08-25T18:00:00Z'

def git_hash(kind, data):
    return hashlib.sha1(kind.encode() + b' ' + str(len(data)).encode() + b'\0' + data).hexdigest()

def bundle(name='example/repo', commit='a' * 40):
    sha = git_hash('blob', b'synthetic example\n')
    rows = [{'path': 'app.py', 'type': 'blob', 'mode': '100644', 'sha': sha}]
    tree = git_hash('tree', b'100644 app.py\0' + bytes.fromhex(sha))
    inv = c.make_inventory(rows, repository=name, commit=commit, tree=tree, observed_at=OBSERVED)
    ledger = c.review_template(inv)
    ledger['rows'][0] = {'path': 'app.py', 'sha': sha, 'status': 'INSPECTED',
        'reviewer': 'synthetic-fixture', 'evidence_ref': 'fixture:review',
        'reviewed_at': OBSERVED, 'summary': 'Synthetic record only; not a real review.'}
    pin = {'name': name, 'ref': commit, 'tree_sha': tree, 'inventory_sha256': inv['inventory_sha256']}
    return pin, {'inventory': inv, 'ledger': ledger}

def payload():
    p = fixtures.valid_payload()
    pin, proof = bundle()
    p['assessment'].update(mode='EXHAUSTIVE', as_of=AS_OF, repos=[pin])
    p['file_coverage'] = {'schema': 'cometweb.roadmap-file-coverage/v1', 'bundles': [proof]}
    return p

def invalid(p):
    r = k.validate_roadmap(p)
    assert not r['valid'], r
    return r

def test_missing_accounting_rejected():
    p = payload(); del p['file_coverage']; invalid(p)

def test_complete_payload_control():
    r = k.validate_roadmap(payload())
    assert r['valid'], r['errors']
    assert r['file_coverage']['status'] == 'INSPECTION_RECORDS_COMPLETE'
    assert r['file_coverage']['runtime_verification'] == 'not_performed'

def test_empty_template_is_not_success():
    p = payload(); b = p['file_coverage']['bundles'][0]
    b['ledger'] = c.review_template(b['inventory'])
    invalid(p)

def test_deleted_review_row_rejected():
    p = payload(); p['file_coverage']['bundles'][0]['ledger']['rows'] = []; invalid(p)

def test_second_repository_missing_rejected():
    p = payload(); pin, _ = bundle('example/backend', 'b'*40)
    p['assessment']['repos'].append(pin); invalid(p)

def test_two_complete_repository_scopes_pass():
    p = payload(); pin, proof = bundle('example/backend', 'b'*40)
    p['assessment']['repos'].append(pin); p['file_coverage']['bundles'].append(proof)
    r = k.validate_roadmap(p); assert r['valid'], r['errors']
    assert len(r['file_coverage']['repositories']) == 2

@pytest.mark.parametrize('field,value', [('ref', 'b'*40), ('ref', 'aaaaaaa'),
    ('tree_sha', 'b'*40), ('inventory_sha256', 'b'*64), ('name', 'other/repo')])
def test_wrong_assessment_pin_rejected(field, value):
    p = payload(); p['assessment']['repos'][0][field] = value; invalid(p)

@pytest.mark.parametrize('field', ['tree_sha', 'inventory_sha256', 'ref', 'name'])
def test_missing_pin_rejected(field):
    p = payload(); del p['assessment']['repos'][0][field]; invalid(p)

def test_duplicate_bundle_rejected():
    p = payload(); p['file_coverage']['bundles'] *= 2; invalid(p)

def test_duplicate_repo_rejected():
    p = payload(); p['assessment']['repos'] *= 2; invalid(p)

def test_unrequested_bundle_rejected():
    p = payload(); _, proof = bundle('other/repo')
    p['file_coverage']['bundles'].append(proof); invalid(p)

def test_forged_summary_cannot_replace_raw_records():
    p = payload(); p['file_coverage'] = {'status': 'INSPECTION_RECORDS_COMPLETE', 'file_count': 100}; invalid(p)

def test_modified_tree_rejected_even_with_new_inventory_digest():
    p = payload(); b = p['file_coverage']['bundles'][0]; inv = b['inventory']
    inv['entries'] = []; inv['inventory_sha256'] = c.digest({n:v for n,v in inv.items() if n != 'inventory_sha256'})
    p['assessment']['repos'][0]['inventory_sha256'] = inv['inventory_sha256']
    b['ledger']['inventory_sha256'] = inv['inventory_sha256']; invalid(p)

def test_future_to_assessment_review_rejected():
    p = payload(); p['file_coverage']['bundles'][0]['ledger']['rows'][0]['reviewed_at'] = '2026-08-26T00:00:00Z'; invalid(p)

def test_future_to_assessment_inventory_rejected():
    p = payload(); p['assessment']['as_of'] = '2026-08-24T00:00:00Z'; invalid(p)

@pytest.mark.parametrize('value', ['2026-08-25', '2026-08-25T20:00:00', 'invalid', None])
def test_as_of_must_be_pinned_timestamp(value):
    p = payload(); p['assessment']['as_of'] = value; invalid(p)

def test_exclusion_requires_explicit_policy():
    p = payload(); row = p['file_coverage']['bundles'][0]['ledger']['rows'][0]
    row.update(status='EXCLUDED_GENERATED', reason='fixture exclusion', scope_basis='fixture policy')
    invalid(p)
    p['assessment']['file_review_policy'] = 'allow_documented_exclusions'
    r = k.validate_roadmap(p); assert r['valid'], r['errors']
    assert r['file_coverage']['status'] == 'ACCOUNTED_WITH_EXCLUSIONS'
    assert r['warnings']

def test_unknown_review_policy_rejected():
    p = payload(); p['assessment']['file_review_policy'] = 'skip'; invalid(p)

def test_standard_mode_without_accounting_stays_supported():
    r = k.validate_roadmap(fixtures.valid_payload()); assert r['valid'], r['errors']
    assert r['file_coverage']['status'] == 'NOT_REQUESTED'

def test_standard_mode_does_not_ignore_supplied_invalid_proof():
    p = payload(); p['assessment']['mode'] = 'STANDARD'; p['file_coverage']['bundles'] = []; invalid(p)

def test_inventory_change_enters_delta():
    before = payload(); after = copy.deepcopy(before)
    after['file_coverage']['bundles'][0]['ledger']['rows'][0]['summary'] = 'Changed supplied review'
    r = k.delta_report(before, after)
    assert r['file_coverage_changed']
    assert r['roadmap_validity'] == 'REVALIDATE'
    assert 'R-1' in r['revalidate_item_ids']

def test_pinned_scope_cannot_be_narrowed():
    p = payload(); pin, proof = bundle('other/repo', 'b'*40)
    p['assessment']['repos'].append(pin); p['file_coverage']['bundles'].append(proof)
    saved = k.validate_roadmap(p)['assessment_contract_sha256']
    p['assessment']['repos'].pop(); p['file_coverage']['bundles'].pop()
    assert not k.validate_roadmap(p, expected_scope_sha256=saved)['valid']

def test_scope_pin_prevents_mode_downgrade():
    p = payload(); saved = k.validate_roadmap(p)['assessment_contract_sha256']
    p['assessment']['mode'] = 'STANDARD'; del p['file_coverage']
    assert not k.validate_roadmap(p, expected_scope_sha256=saved)['valid']

def test_scope_pin_prevents_exclusion_policy_change():
    p = payload(); saved = k.validate_roadmap(p)['assessment_contract_sha256']
    p['assessment']['file_review_policy'] = 'allow_documented_exclusions'
    assert not k.validate_roadmap(p, expected_scope_sha256=saved)['valid']

def test_matching_scope_pin_passes():
    p = payload(); saved = k.validate_roadmap(p)['assessment_contract_sha256']
    assert k.validate_roadmap(p, expected_scope_sha256=saved)['valid']

def test_invalid_graph_never_emits_execution_waves():
    r = k.graph_report([{'id':'A', 'depends_on':['ghost']}, {'id':'B','depends_on':['A']}])
    assert not r['valid']
    assert r['waves'] == r['topological_order'] == r['critical_chain_by_hard_dependency_count'] == []

def test_duplicate_graph_never_emits_order():
    r = k.graph_report([{'id':'A'}, {'id':'A'}])
    assert not r['valid']
    assert r['topological_order'] == []

def test_supplied_snapshot_mismatch_rejected():
    p = payload(); p.update(k.snapshot_report(p)); p['items'][0]['title'] = 'Modified'
    invalid(p)
    with pytest.raises(ValueError): k.delta_report(p, payload())

@pytest.mark.parametrize('raw', ['{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}', '{"x":-Infinity}'])
def test_strict_json(raw):
    with pytest.raises(ValueError): k.parse_json_arg(raw)

def test_cli_require_valid_rejects_incomplete(tmp_path):
    p = payload(); del p['file_coverage']
    src = tmp_path/'input.json'; src.write_text(json.dumps(p))
    result = subprocess.run([sys.executable,'-S',str(ROOT/'scripts/roadmap_kernel.py'),
        'validate','--roadmap-json','@'+str(src),'--require-valid'],capture_output=True,text=True)
    assert result.returncode == 1
    assert not json.loads(result.stdout)['valid']

def test_cli_complete_passes_with_exact_scope(tmp_path):
    p = payload(); saved=k.validate_roadmap(p)['assessment_contract_sha256']
    src = tmp_path/'input.json'; src.write_text(json.dumps(p))
    result = subprocess.run([sys.executable,'-S',str(ROOT/'scripts/roadmap_kernel.py'),
        'validate','--roadmap-json','@'+str(src),'--require-valid','--expected-scope-sha256',saved],capture_output=True,text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)['valid']

def test_no_input_mutation():
    p = payload(); old=copy.deepcopy(p); k.validate_roadmap(p); assert p == old

@pytest.mark.parametrize('mode', ['exhaustive', ' ExHaUsTiVe '])
def test_exhaustive_mode_normalization_cannot_bypass_proof(mode):
    p = payload(); p['assessment']['mode'] = mode; del p['file_coverage']; invalid(p)

@pytest.mark.parametrize('mode', ['EXHAUSTIV', [], {}, 17])
def test_invalid_mode_rejected(mode):
    p = fixtures.valid_payload(); p['assessment']['mode'] = mode; invalid(p)

def test_future_assessment_rejected():
    p = payload(); p['assessment']['as_of'] = '2999-01-01T00:00:00Z'; invalid(p)

def test_scope_change_alone_enters_delta():
    a = payload(); b = copy.deepcopy(a)
    b['assessment']['file_review_policy'] = 'allow_documented_exclusions'
    r = k.delta_report(a,b)
    assert r['assessment_contract_changed']
    assert r['roadmap_validity'] == 'REVALIDATE'
    assert r['revalidate_item_ids'] == ['R-1']

def test_identical_incomplete_file_scope_is_not_valid_delta():
    p = payload(); del p['file_coverage']
    r=k.delta_report(p,copy.deepcopy(p))
    assert r['roadmap_validity'] == 'REVALIDATE'
    assert r['file_coverage_issues']

def test_identical_complete_file_scope_is_valid_delta():
    p = payload(); r = k.delta_report(p,copy.deepcopy(p))
    assert r['roadmap_validity'] == 'VALID'
    assert not r['file_coverage_changed']

def test_valid_stored_snapshot_accepted():
    p = payload(); p['snapshot_hash'] = k.snapshot_report(p)['snapshot_hash']
    assert k.validate_roadmap(p)['valid']

def test_supplied_proof_changes_snapshot():
    p = payload(); old = k.snapshot_report(p)['snapshot_hash']
    p['file_coverage']['bundles'][0]['ledger']['rows'][0]['summary'] += ' Changed scope'
    assert k.snapshot_report(p)['snapshot_hash'] != old

@pytest.mark.parametrize('row', [{}, {'id':None}, {'id':17}, {'id':''}, {'id':'  '},
    {'id':'A','depends_on':None}, {'id':'A','depends_on':'B'}, {'id':'A','depends_on':[None]},
    {'id':'A','depends_on':['B','B']}])
def test_malformed_graph_rows_rejected(row):
    with pytest.raises(ValueError): k.graph_report([row])

@pytest.mark.parametrize('value', [[], None, 'text', 17])
def test_bad_target_does_not_crash_validator(value):
    p = fixtures.valid_payload(); p['target_contract'] = value; invalid(p)

def test_invalid_capability_refs_are_validation_error_not_crash():
    p=fixtures.valid_payload(); p['capabilities'][0].update(state='MISSING',claim_refs=3)
    invalid(p)

def test_cli_invalid_graph_processed_exit_one(tmp_path):
    rows = tmp_path/'graph.json'; rows.write_text('[{"id":"A","depends_on":["missing"]}]')
    r = subprocess.run([sys.executable,'-S',str(ROOT/'scripts/roadmap_kernel.py'),
        'graph','--items-json','@'+str(rows),'--require-valid'],capture_output=True,text=True)
    assert r.returncode == 1
    assert not json.loads(r.stdout)['valid']

def test_cli_bad_json_does_not_echo_payload():
    r = subprocess.run([sys.executable,'-S',str(ROOT/'scripts/roadmap_kernel.py'),
        'validate','--roadmap-json','{"PRIVATE_MARKER":NaN}','--require-valid'],capture_output=True,text=True)
    assert r.returncode == 2
    assert 'PRIVATE_MARKER' not in r.stdout + r.stderr

def test_cli_legacy_report_only_exit_zero(tmp_path):
    p = payload(); del p['file_coverage']
    src=tmp_path/'input.json'; src.write_text(json.dumps(p))
    r=subprocess.run([sys.executable,'-S',str(ROOT/'scripts/roadmap_kernel.py'),'validate',
        '--roadmap-json','@'+str(src)],capture_output=True,text=True)
    assert r.returncode == 0
    assert not json.loads(r.stdout)['valid']

def test_parser_rejects_overflow_and_byte_budget(monkeypatch):
    with pytest.raises(ValueError): k.parse_json_arg('{"value":1e99999}')
    monkeypatch.setattr(k,'MAX_JSON_BYTES',20)
    with pytest.raises(ValueError): k.parse_json_arg('"'+'x'*21+'"')

def test_scope_can_be_frozen_before_review_completion():
    p=payload(); b=p['file_coverage']['bundles'][0]; b['ledger']=c.review_template(b['inventory'])
    r=k.validate_roadmap(p); assert not r['valid']
    pin=r['assessment_contract_sha256']
    finished=payload()
    assert k.validate_roadmap(finished,expected_scope_sha256=pin)['valid']

def test_scope_pin_detects_target_change():
    p=payload(); saved=k.validate_roadmap(p)['assessment_contract_sha256']
    p['target_contract']['target_profile']='PROTOTYPE'
    assert not k.validate_roadmap(p,expected_scope_sha256=saved)['valid']
