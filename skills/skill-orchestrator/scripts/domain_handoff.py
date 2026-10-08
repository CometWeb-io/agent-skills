"""Pinned research/Council domain admission; constraints are not execution permission."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
GATE = 'research-council-schema-kernel/v1'
SCHEMAS = {'evidence-researcher': 'domain-research', 'ai-council': 'domain-council'}


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def digest(value: Any) -> str:
    return 'sha256:' + hashlib.sha256(canonical(value)).hexdigest()


def _schema(name: str, value: Any) -> None:
    from jsonschema import Draft202012Validator
    schema = json.loads((ROOT / f'skills/skill-orchestrator/references/{name}.schema.json').read_text())
    errors = [str(list(e.path)) + ': ' + e.message for e in Draft202012Validator(schema).iter_errors(value)]
    if errors:
        raise ValueError('domain schema rejected: ' + '; '.join(errors[:12]))


def _council():
    # Fresh package interpreter prevents stale sys.modules policy after a source revision.
    def method(name):
        def invoke(*args, **kwargs):
            code = ("import importlib.util,json,sys; "
                    "spec=importlib.util.spec_from_file_location('isolated_council',sys.argv[1]); "
                    "m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m); "
                    "v=json.load(sys.stdin); print(json.dumps(getattr(m,v['function'])(*v['args'],**v['kwargs']),allow_nan=False))")
            result = subprocess.run([sys.executable, '-c', code, str(ROOT/'skills/ai-council/scripts/council_kernel.py')],
                                    input=canonical({'function':name,'args':args,'kwargs':kwargs}).decode(),
                                    text=True,capture_output=True,timeout=30,check=False)
            if result.returncode:
                raise ValueError('Council kernel rejected the declared decision input')
            return json.loads(result.stdout)
        return invoke
    return SimpleNamespace(**{name:method(name) for name in
                             ('compile_decision_contract','required_confidence','plan_council','gate_verdict')})


def audit_graph(graph: dict) -> dict:
    _schema('domain-evidence-graph', graph)
    with tempfile.TemporaryDirectory(prefix='cw-domain-audit-') as temp:
        path = Path(temp) / 'graph.json'
        path.write_bytes(canonical(graph))
        result = subprocess.run([sys.executable, str(ROOT / 'skills/evidence-researcher/scripts/evidence_kernel.py'),
                                 'audit', '--ledger-json', str(path)], capture_output=True, text=True, timeout=30, check=False)
    try:
        audit = json.loads(result.stdout)
    except ValueError as exc:
        raise ValueError('evidence kernel did not return a report') from exc
    if result.returncode or not audit.get('validation', {}).get('valid'):
        raise ValueError('evidence kernel rejected: ' + json.dumps(audit.get('validation', audit), ensure_ascii=False))
    if graph['research_status'] != audit['research_status']:
        raise ValueError('declared research status differs from evidence kernel: declared=' + graph['research_status'] + '; expected=' + audit['research_status'])
    return audit


def bindings(envelopes: list[dict]) -> list[dict]:
    return [{'step_id': f'step-{index}', 'envelope_id': value['id'], 'envelope_hash': digest(value)}
            for index, value in enumerate(envelopes, 1)]


def research_payload(graph: dict, prior: list[dict]) -> dict:
    audit = audit_graph(graph)
    return {'research_contract': canonical(graph['research_contract']).decode(),
            'material_claims': [{'claim_id': c['claim_id'], 'text': c['claim_text'], 'epistemic_kind': c['epistemic_kind'], 'status': c['status']} for c in graph['claims']],
            'gaps': [g['description'] for g in graph['gaps']],
            'contradictions': [c['explanation'] for c in graph['contradictions']],
            'evidence_pack_hash': audit['pack_hash'], 'evidence_graph': json.loads(canonical(graph)),
            'upstream_bindings': bindings(prior)}


def validate_research(payload: dict) -> dict:
    _schema('domain-research', payload)
    graph = payload['evidence_graph']
    audit = audit_graph(graph)
    expected = research_payload(graph, [])
    for field in ['research_contract', 'material_claims', 'gaps', 'contradictions', 'evidence_pack_hash']:
        if payload[field] != expected[field]:
            raise ValueError('research projection/hash changed: ' + field)
    return audit


def validate_context(context: dict) -> None:
    if not isinstance(context, dict) or set(context) != {'question', 'context', 'mode', 'decision_value', 'max_attempts'}:
        raise ValueError('domain context must declare question/context/mode/decision_value/max_attempts')
    if not isinstance(context['question'], str) or not context['question'].strip() or not isinstance(context['context'], dict):
        raise ValueError('invalid decision input')
    if context['mode'] != 'LIGHT':
        raise ValueError('local adapter qualifies LIGHT only')
    attempts = context['max_attempts']
    if isinstance(attempts, bool) or not isinstance(attempts, int) or not 1 <= attempts <= 3:
        raise ValueError('max_attempts must be an integer from 1 to 3')
    value = context['decision_value']
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError('decision_value must be a finite number from 0 to 1')
    kernel = _council()
    contract = kernel.compile_decision_contract(context['question'], context['context'])
    kernel.required_confidence(contract, 0.0, context['decision_value'])


def council_inputs(bundle: dict, context: dict) -> dict:
    validate_context(context)
    research = bundle['research_envelope']
    if research.get('type') != 'EvidenceEnvelope' or research.get('producer') != 'evidence-researcher':
        raise ValueError('Council research producer/type mismatch')
    audit = validate_research(research['payload'])
    judge = bundle['judge']
    proposal = bundle['proposal']
    _schema('domain-judge', judge)
    _schema('domain-proposal', proposal)
    if len(bundle['blind_memos']) != 2 or {m['role_id'] for m in bundle['blind_memos']} != {'technical', 'product_customer'}:
        raise ValueError('two separately produced LIGHT perspectives are required')
    claims = {v['claim_id'] for v in research['payload']['evidence_graph']['claims']}
    ready = {v['claim_id'] for v in audit['coverage']['claims'] if v['ready']}
    admitted, rejected = set(judge['accepted_claim_ids']), set(judge['rejected_claim_ids'])
    if not admitted <= ready or not rejected <= claims or admitted & rejected:
        raise ValueError('Judge admitted unsupported/unknown claims or conflicting IDs')
    for memo in bundle['blind_memos']:
        _schema('domain-memo', memo)
        if not set(memo['claim_ids']) <= claims:
            raise ValueError('adviser referenced an unknown claim')
    kernel = _council()
    contract = kernel.compile_decision_contract(context['question'], context['context'])
    plan = kernel.plan_council(contract, context['mode'])
    material = {c['claim_id'] for c in research['payload']['evidence_graph']['claims'] if c['materiality'] in {'material', 'critical'}}
    coverage = len(admitted & material) / max(1, len(material))
    required = kernel.required_confidence(contract, coverage, context['decision_value'])
    if proposal['required_confidence'] != required:
        raise ValueError('proposal changed the computed confidence threshold')
    if proposal['freshness_status'] != judge['freshness_status'] or proposal['controls_implemented'] != judge['controls_implemented']:
        raise ValueError('proposal changed Judge gate state')
    kernel_gap = audit['research_status'] != 'READY' or not material <= admitted
    critical = ('Research is not READY for this decision scope' if kernel_gap else
                judge['critical_gaps'][0] if judge['critical_gaps'] else proposal['critical_gap'])
    freshness = 'REFRESH_REQUIRED' if audit['research_status'] == 'REFRESH_REQUIRED' else judge['freshness_status']
    required_gates = sorted(set(plan['roles']['gatekeepers']) | {'technical'})
    verdict = kernel.gate_verdict(proposal['verdict'], proposal['confidence'], required,
                                  proposal['reversible_experiment_available'], critical,
                                  judge['gate_statuses'], judge['controls_implemented'], freshness,
                                  required_gatekeepers=required_gates)
    kernel_verdict = verdict
    # Incomplete research is admissible for discussing gaps, never a positive trial/launch gate.
    if kernel_gap and verdict in {'GO', 'TEST'}:
        verdict = 'DEFER'
    return {'verdict': verdict, 'kernel_verdict': kernel_verdict, 'required_confidence': required, 'evidence_coverage': coverage,
            'required_gates': required_gates, 'freshness_status': freshness, 'critical_gap': critical,
            'controls_implemented': judge['controls_implemented'], 'execution_authorized': False}


def finalize_council(bundle: dict, context: dict, prior: list[dict]) -> dict:
    # Keep the proposal unmodified; the separate deterministic result is authoritative for handoff.
    bundle = json.loads(canonical(bundle))
    result = council_inputs(bundle, context)
    blockers = list(bundle['proposal']['blockers'])
    if result['critical_gap'] and result['critical_gap'] not in blockers:
        blockers.append(result['critical_gap'])
    return {'verdict': result['verdict'], 'blockers': blockers, 'controls': list(bundle['proposal']['controls']),
            'decision_bundle': bundle, 'constraint_result': result, 'upstream_bindings': bindings(prior)}


def validate(payload: dict, producer: str, context: dict, *, expected_report_as_of: str | None = None) -> dict:
    if producer not in SCHEMAS:
        raise ValueError('unsupported domain producer')
    _schema(SCHEMAS[producer], payload)
    if producer == 'evidence-researcher':
        audit = validate_research(payload)
        if expected_report_as_of is not None and payload['evidence_graph']['research_contract']['as_of'] != expected_report_as_of:
            raise ValueError('research_contract.as_of differs from parent report_as_of')
        return {'accepted': True, 'domain_status': audit['research_status'], 'domain_hash': digest(payload)}
    expected = finalize_council(payload['decision_bundle'], context, [])
    for field in ['verdict', 'blockers', 'controls', 'constraint_result']:
        if payload[field] != expected[field]:
            raise ValueError('Council final constraint result changed: ' + field)
    return {'accepted': True, 'domain_status': expected['verdict'], 'domain_hash': digest(payload)}


def check_bindings(envelope: dict, prefix: list[dict], *, research_step_id: str = "step-2") -> None:
    declared = envelope['payload']['upstream_bindings']
    if declared != prefix or envelope.get('dependencies') != [v['envelope_id'] for v in prefix]:
        raise ValueError('domain upstream id/hash/order does not match the completed prefix')
    if envelope['producer'] == 'ai-council':
        prior = envelope['payload']['decision_bundle']['research_envelope']
        research = next((v for v in prefix if v['step_id'] == research_step_id), None)
        if not research or prior['id'] != research['envelope_id'] or digest(prior) != research['envelope_hash']:
            raise ValueError('Council substituted research after checkpoint')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input_json', type=Path)
    parser.add_argument('--producer', required=True, choices=sorted(SCHEMAS))
    parser.add_argument('--context-json', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = validate(json.loads(args.input_json.read_text()), args.producer, json.loads(args.context_json.read_text()))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, TypeError, KeyError, OSError, subprocess.SubprocessError) as exc:
        print(json.dumps({'accepted': False, 'error': str(exc), 'execution_authorized': False}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
