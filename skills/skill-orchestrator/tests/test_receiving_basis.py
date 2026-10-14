"""Receiving checks use caller capabilities, never serialized observation receipts."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

spec = importlib.util.spec_from_file_location('receiving_fixtures', Path(__file__).with_name('test_domain_handoff.py'))
D = importlib.util.module_from_spec(spec)
spec.loader.exec_module(D)
domain = D.domain


def sha(value):
    return hashlib.sha256(domain.canonical(value)).hexdigest()


def case(tmp_path):
    graph = json.loads((Path(__file__).parent / 'fixtures/domain-ready-graph.json').read_text())
    claim = graph['claims'][0]
    claim.update(basis='verified_fact', scope={'run': 'bounded-receiver'}, temporal_sensitivity='static',
                 claim_type='dataset_fact', claim_text='The controlled run has 18 successful checks.')
    source = graph['sources'][0]
    source.update(source_class='USER_FILE', canonical_ref='controlled:bounded-receiver', provenance_lane='USER_SUPPLIED')
    edge = graph['evidence'][0]
    edge.update(basis='verified_fact', locator='/checks/success')
    context = copy.deepcopy(D.CONTEXT)
    context['evidence_use'] = {'purpose': 'action', 'as_of': graph['research_contract']['as_of'],
                               'premises': [{'claim_id': claim['claim_id'], 'role': 'controlled_fact', 'scope': claim['scope']}]}
    raw = b'{"checks":{"success":18},"private":"receiver-canary"}'
    (tmp_path / 'controlled.json').write_bytes(raw)
    check = dict(claim_id=claim['claim_id'], claim_hash=sha(claim), source_id=source['source_id'], source_hash=sha(source),
                 evidence_id=edge['evidence_id'], evidence_hash=sha(edge), path='controlled.json',
                 sha256=hashlib.sha256(raw).hexdigest(), pointer=edge['locator'], expected=18, observed_scope='controlled_state')
    plan = dict(version='local-fact-check/v1', research_id=graph['research_id'], as_of=context['evidence_use']['as_of'],
                context_hash=sha(context), checks=[check])
    return graph, context, plan


def positive_bundle(graph, context, coverage=1.):
    research = D.wrap(domain.research_payload(graph, [D.prd()]), 'evidence-researcher', 'observed-research', [D.prd()])
    bundle = D.bundle(research)
    bundle['judge'].update(accepted_claim_ids=[c['claim_id'] for c in graph['claims']], rejected_claim_ids=[],
                           critical_gaps=[], freshness_status='CLEAR', gate_statuses={'technical': 'CLEAR'}, controls_implemented=True)
    kernel = domain._council()
    threshold = kernel.required_confidence(kernel.compile_decision_contract(context['question'], context['context']), coverage, context['decision_value'])
    bundle['proposal'].update(verdict='GO', confidence=1., required_confidence=threshold, critical_gap=None,
                             freshness_status='CLEAR', controls_implemented=True, reversible_experiment_available=True)
    return bundle


def test_actual_receiver_reads_and_rechecks_source(tmp_path):
    graph, context, plan = case(tmp_path)
    bundle = positive_bundle(graph, context)
    output = domain.finalize_council(bundle, context, [], check_plan=plan, source_root=tmp_path)
    assert output['verdict'] == 'GO'
    assert output['constraint_result']['basis_assessment']['observed_fact_ids'] == ['clm_policy']
    assert output['constraint_result']['execution_authorized'] is False
    assert 'receiver-canary' not in json.dumps(output)
    assert domain.validate(output, 'ai-council', context, check_plan=plan, source_root=tmp_path)['accepted']
    (tmp_path / 'controlled.json').write_text('{"checks":{"success":3}}')
    with pytest.raises(ValueError):
        domain.validate(output, 'ai-council', context, check_plan=plan, source_root=tmp_path)


def test_cached_positive_without_capabilities_is_refused(tmp_path):
    graph, context, plan = case(tmp_path)
    output = domain.finalize_council(positive_bundle(graph, context), context, [], check_plan=plan, source_root=tmp_path)
    with pytest.raises(ValueError):
        domain.validate(output, 'ai-council', context)


def test_legacy_verified_metadata_does_not_clear_receiver():
    graph = json.loads((Path(__file__).parent / 'fixtures/domain-ready-graph.json').read_text())
    with pytest.raises(ValueError, match='Judge admitted unsupported'):
        domain.finalize_council(positive_bundle(graph, D.CONTEXT), D.CONTEXT, [])


def test_explicit_method_choice_keeps_nonfact_without_fact_credit(tmp_path):
    graph, context, _ = case(tmp_path)
    claim = graph['claims'][0]
    claim.update(basis='framework_method', status='PARTIAL', epistemic_kind='INFERENCE', contradiction_tested=False)
    graph['evidence'][0].update(basis='framework_method', admission='CONTEXT_ONLY')
    graph['research_status'] = 'PARTIAL'
    context['evidence_use']['purpose'] = 'method_choice'
    context['evidence_use']['premises'][0]['role'] = 'method'
    output = domain.finalize_council(positive_bundle(graph, context, 0), context, [])
    assert output['verdict'] == 'GO'
    assert output['constraint_result']['evidence_coverage'] == 0
    assert output['decision_bundle']['research_envelope']['payload']['evidence_graph']['research_status'] == 'PARTIAL'
    assert output['constraint_result']['basis_assessment']['caveats']


@pytest.mark.parametrize('change', ['bytes', 'predicate', 'context', 'scope', 'scope-class', 'supporting-required', 'producer-plan'])
def test_receiving_scope_cannot_be_laundered(tmp_path, change):
    graph, context, plan = case(tmp_path)
    if change == 'bytes':
        (tmp_path / 'controlled.json').write_text('{"checks":{"success":1}}')
    elif change == 'predicate':
        plan['checks'][0]['expected'] = 19
    elif change == 'context':
        context['question'] = 'Approve a different operation'
    elif change == 'scope':
        context['evidence_use']['premises'][0]['scope'] = {'run': 'another-run'}
    elif change == 'scope-class':
        plan['checks'][0]['observed_scope'] = 'document_content'
    elif change == 'supporting-required':
        graph['claims'][0]['materiality'] = 'supporting'
        plan['checks'][0]['claim_hash'] = sha(graph['claims'][0])
        (tmp_path / 'controlled.json').unlink()
    else:
        graph['check_plan'] = plan
    with pytest.raises(ValueError):
        domain.finalize_council(positive_bundle(graph, context), context, [], check_plan=plan, source_root=tmp_path)


def test_unknown_hypothesis_trial_requires_separately_observed_safeguard(tmp_path):
    graph, context, plan = case(tmp_path)
    context['evidence_use']['purpose'] = 'trial'
    context['evidence_use']['premises'][0]['role'] = 'safeguard'
    hypothesis = {**graph['claims'][0], 'claim_id': 'trial-effect', 'basis': 'assumption',
                  'epistemic_kind': 'INFERENCE', 'materiality': 'material', 'status': 'UNKNOWN',
                  'contradiction_tested': False, 'confidence': 'low'}
    graph['claims'].append(hypothesis)
    graph['research_status'] = 'PARTIAL'
    context['evidence_use']['premises'].append({'claim_id': hypothesis['claim_id'], 'role': 'hypothesis', 'scope': hypothesis['scope']})
    plan['context_hash'] = sha(context)
    output = domain.finalize_council(positive_bundle(graph, context), context, [], check_plan=plan, source_root=tmp_path)
    assert output['verdict'] == 'TEST'
    assert output['constraint_result']['evidence_coverage'] == 1
    assert output['constraint_result']['basis_assessment']['observed_fact_ids'] == ['clm_policy']
    assert output['decision_bundle']['proposal']['verdict'] == 'GO'
    assert hypothesis['status'] == 'UNKNOWN'
    (tmp_path / 'controlled.json').unlink()
    with pytest.raises(ValueError):
        domain.validate(output, 'ai-council', context, check_plan=plan, source_root=tmp_path)


def test_method_on_high_risk_topic_does_not_clear_actual_action_gates(tmp_path):
    graph, context, plan = case(tmp_path)
    context['context'].update(risk_level='high', reversibility='hard_to_reverse', risk_surfaces=['technical', 'financial', 'legal'])
    plan['context_hash'] = sha(context)
    output = domain.finalize_council(positive_bundle(graph, context), context, [], check_plan=plan, source_root=tmp_path)
    assert output['verdict'] == 'DEFER'
    assert set(output['constraint_result']['required_gates']) - {'technical'}
    claim = graph['claims'][0]
    claim.update(basis='framework_method', status='PARTIAL', epistemic_kind='INFERENCE', contradiction_tested=False)
    graph['evidence'][0].update(basis='framework_method', admission='CONTEXT_ONLY')
    graph['research_status'] = 'PARTIAL'
    context['evidence_use']['purpose'] = 'method_choice'
    context['evidence_use']['premises'][0]['role'] = 'method'
    output = domain.finalize_council(positive_bundle(graph, context, 0), context, [])
    assert output['verdict'] == 'GO'
    assert output['constraint_result']['required_gates'] == ['technical']
    assert output['constraint_result']['basis_assessment']['scope'] == 'method_choice'


def test_actual_cli_rechecks_and_requires_paired_capabilities(tmp_path):
    graph, context, plan = case(tmp_path)
    output = domain.finalize_council(positive_bundle(graph, context), context, [], check_plan=plan, source_root=tmp_path)
    for name, value in [('output', output), ('context', context), ('plan', plan)]:
        (tmp_path / (name + '.json')).write_bytes(domain.canonical(value))
    command = [sys.executable, str(domain.ROOT / 'skills/skill-orchestrator/scripts/domain_handoff.py'),
               str(tmp_path / 'output.json'), '--producer', 'ai-council', '--context-json', str(tmp_path / 'context.json'),
               '--check-plan-json', str(tmp_path / 'plan.json'), '--source-root', str(tmp_path)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['accepted'] is True
    assert subprocess.run(command[:-2], capture_output=True, timeout=30).returncode == 1
    (tmp_path / 'controlled.json').unlink()
    result = subprocess.run(command, capture_output=True, text=True, timeout=30)
    assert result.returncode == 1
    assert 'receiver-canary' not in result.stdout + result.stderr


@pytest.mark.parametrize('raw', ['{"x":1,"x":2}', '{"x":1e999}', '{"x":NaN}'])
def test_actual_receiving_reader_rejects_ambiguous_json(tmp_path, raw):
    path = tmp_path / 'input.json'
    path.write_text(raw)
    with pytest.raises(ValueError, match='bounded JSON'):
        domain.load_input(path)


def test_actual_compiler_and_checkpoint_thread_process_capabilities(tmp_path, monkeypatch):
    graph, context, plan = case(tmp_path)
    workflow = D.gate.attach(D.planner.plan_workflow('evidence then council').to_dict(), with_domain_gates=True, domain_context=context)
    run = D.ledger.create_run(tmp_path / 'runs', 'observed', workflow)
    prd = D.prd()
    D.checkpoint(run, 'step-1', prd, workflow)
    bundle = positive_bundle(graph, context)
    research = bundle['research_envelope']
    D.checkpoint(run, 'step-2', research, workflow)
    output = domain.finalize_council(bundle, context, [prd, research], check_plan=plan, source_root=tmp_path)
    envelope = D.wrap(output, 'ai-council', 'observed-decision', [prd, research])
    task = D.ledger.claim_next(run, workflow)
    spec = importlib.util.spec_from_file_location('receiving_worker', domain.ROOT / 'skills/skill-orchestrator/scripts/worker_compiler.py')
    worker = importlib.util.module_from_spec(spec); spec.loader.exec_module(worker)
    role_task = {'skill': 'ai-council', 'compiled_worker_version': 'v2', 'domain_context': context}
    role = worker.compile_council_role(role_task, 'chair', domain.ROOT, research=research, prior=[prd, research],
                                     memos=bundle['blind_memos'], judge=bundle['judge'], check_plan=plan, source_root=tmp_path)
    assert 'observed_fact_ids' in role['prompt']
    assert 'receiver-canary' not in role['prompt']
    assert '"expected"' not in role['prompt'].split('INPUTS\n')[-1].split('\nOUTPUT SCHEMA')[0]
    before = (run / 'events.jsonl').read_bytes()
    with pytest.raises(ValueError):
        D.ledger.complete_step(run, 'step-3', envelope['id'], domain.digest(envelope), task['data']['attempt_id'], envelope=envelope)
    assert before == (run / 'events.jsonl').read_bytes()
    D.ledger.complete_step(run, 'step-3', envelope['id'], domain.digest(envelope), task['data']['attempt_id'],
                           envelope=envelope, check_plan=plan, source_root=tmp_path)
    assert D.ledger.replay(run)['status'] == 'COMPLETED'
    builder_path = domain.ROOT / 'skills/skill-orchestrator-multiagent/scripts/orchestrate_multiagent_kernel.py'
    monkeypatch.syspath_prepend(str(builder_path.parent))
    builder = D.module('receiving_resume_builder', str(builder_path.relative_to(domain.ROOT)))
    prefix = [prd, research, envelope]
    before = (run / 'events.jsonl').read_bytes()
    with pytest.raises(ValueError):
        builder.build_next_task(run, workflow, prefix)
    with pytest.raises(ValueError, match='together'):
        builder.build_next_task(run, workflow, prefix, check_plan=plan)
    resumed = builder.build_next_task(run, workflow, prefix, check_plan=plan, source_root=tmp_path)
    assert resumed['dispatch_status'] == 'COMPLETED' and resumed['subagent_tasks'] == []
    paths = [tmp_path / name for name in ('workflow.json', 'prefix.json', 'checks.json')]
    for path, value in zip(paths, (workflow, prefix, plan), strict=True):
        path.write_bytes(domain.canonical(value))
    command = [sys.executable, str(builder_path), '--json', '--run-dir', str(run),
               '--plan-json', str(paths[0]), '--prior-envelopes-json', str(paths[1])]
    refused = subprocess.run(command, capture_output=True, text=True)
    assert refused.returncode == 1 and not refused.stdout
    command += ['--check-plan-json', str(paths[2]), '--source-root', str(tmp_path)]
    accepted = subprocess.run(command, capture_output=True, text=True)
    assert accepted.returncode == 0, accepted.stderr
    assert json.loads(accepted.stdout)['dispatch_status'] == 'COMPLETED'
    assert 'receiver-canary' not in accepted.stdout
    assert before == (run / 'events.jsonl').read_bytes()
    (tmp_path / 'controlled.json').unlink()
    with pytest.raises(ValueError):
        builder.build_next_task(run, workflow, prefix, check_plan=plan, source_root=tmp_path)
    refused = subprocess.run(command, capture_output=True, text=True)
    assert refused.returncode == 1 and not refused.stdout
    assert before == (run / 'events.jsonl').read_bytes()
    with pytest.raises(ValueError):
        D.ledger.complete_step(run, 'step-3', envelope['id'], domain.digest(envelope), None,
                               envelope=envelope, check_plan=plan, source_root=tmp_path)


@pytest.mark.parametrize('proposal', ['TEST', 'GO-below-threshold'])
def test_action_cannot_silently_become_unqualified_trial(tmp_path, proposal):
    graph, context, plan = case(tmp_path)
    bundle = positive_bundle(graph, context)
    bundle['proposal']['verdict'] = 'TEST' if proposal == 'TEST' else 'GO'
    if proposal == 'GO-below-threshold':
        bundle['proposal']['confidence'] = 0
    output = domain.finalize_council(bundle, context, [], check_plan=plan, source_root=tmp_path)
    assert output['verdict'] == 'DEFER'


def test_binding_block_survives_unassessed_evidence_scope():
    research = D.research([D.prd()])
    bundle = D.bundle(research)
    bundle['judge']['gate_statuses']['technical'] = 'BLOCK'
    assert domain.finalize_council(bundle, D.CONTEXT, [])['verdict'] == 'NO-GO'


def test_receiving_path_reader_never_interprets_a_filename_as_inline_json(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    path = Path('{"inline":1}')
    path.write_text('{"actual_file":18}')
    assert domain.load_input(path) == {'actual_file': 18}


def test_uncertain_estimate_informs_action_without_increasing_fact_coverage(tmp_path):
    graph, context, plan = case(tmp_path)
    estimate = {**graph['claims'][0], 'claim_id': 'future-cost', 'basis': 'assumption',
                'status': 'PARTIAL', 'epistemic_kind': 'INFERENCE', 'materiality': 'material',
                'contradiction_tested': False, 'confidence': 'low'}
    graph['claims'].append(estimate)
    graph['research_status'] = 'PARTIAL'
    context['evidence_use']['premises'].append({'claim_id': estimate['claim_id'], 'role': 'estimate', 'scope': estimate['scope']})
    plan['context_hash'] = sha(context)
    output = domain.finalize_council(positive_bundle(graph, context), context, [], check_plan=plan, source_root=tmp_path)
    assert output['verdict'] == 'GO'
    report = output['constraint_result']
    assert report['evidence_coverage'] == 1
    assert report['basis_assessment']['required_fact_ids'] == report['basis_assessment']['observed_fact_ids'] == ['clm_policy']
    assert report['basis_assessment']['caveats']
    assert output['decision_bundle']['research_envelope']['payload']['evidence_graph']['claims'][1]['status'] == 'PARTIAL'


@pytest.mark.parametrize('basis,role,purpose', [('user_supplied', 'intent', 'planning'), ('framework_method', 'method', 'method_choice')])
def test_nonfact_fact_encoding_does_not_inherit_global_world_freshness(tmp_path, basis, role, purpose):
    graph, context, _ = case(tmp_path)
    claim = graph['claims'][0]
    claim.update(basis=basis, status='PARTIAL', epistemic_kind='FACT', contradiction_tested=False, temporal_sensitivity='high', claim_type='current_fact')
    graph.update(evidence=[], searches=[], sources=[], research_status='REFRESH_REQUIRED')
    context['evidence_use']['purpose'] = purpose
    context['evidence_use']['premises'][0]['role'] = role
    output = domain.finalize_council(positive_bundle(graph, context, 0), context, [])
    assert output['verdict'] == 'GO'
    assert output['constraint_result']['freshness_status'] == 'CLEAR'
    assert output['constraint_result']['evidence_coverage'] == 0
    assert output['decision_bundle']['research_envelope']['payload']['evidence_graph']['research_status'] == 'REFRESH_REQUIRED'
    assert claim['epistemic_kind'] == 'FACT' and claim['status'] == 'PARTIAL'
