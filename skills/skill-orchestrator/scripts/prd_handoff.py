"""Opt-in local PRD handoff: final CW-AIP wrapper, producer schema and readiness kernel."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
GATE = 'prd-schema-kernel/v1'
WRAPPER_GATE = 'cw-aip-final/v1'
PROFILE_GATE = 'specialist-profile-owner/v2'
PROFILE_PATH = 'skills/skill-orchestrator/scripts/specialist_profiles.py'
DOMAIN_GATE = 'research-council-schema-kernel/v1'
DOMAIN_PATH = 'skills/skill-orchestrator/scripts/domain_handoff.py'
SCHEMA_PATH = 'skills/brief-architect/references/prd-output.schema.json'
KERNEL_PATH = 'skills/brief-architect/scripts/kernel.py'
WRAPPER_PATH = 'skills/skill-orchestrator-multiagent/scripts/validate_envelope.py'
LOCK_FILES = (SCHEMA_PATH, KERNEL_PATH, WRAPPER_PATH,
              'skills/skill-orchestrator-multiagent/references/envelope.core.schema.json',
              'skills/skill-orchestrator-multiagent/references/evidence-envelope.schema.json',
              'skills/skill-orchestrator-multiagent/references/decision-handoff.schema.json',
              'skills/skill-orchestrator-multiagent/references/cw-aip-v2.core.schema.json',
              'skills/skill-orchestrator/scripts/prd_handoff.py')
LOCK_FILES += (DOMAIN_PATH,) + tuple(str(p.relative_to(ROOT)) for folder in ('skills/evidence-researcher/scripts','skills/ai-council/scripts') for p in sorted((ROOT/folder).rglob('*.py')))
LOCK_FILES += tuple(str(p.relative_to(ROOT)) for p in sorted((ROOT/'skills/skill-orchestrator/references').glob('domain-*.schema.json')))



def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(data: bytes) -> str:
    return 'sha256:' + hashlib.sha256(data).hexdigest()


def gate_lock() -> dict:
    try:
        files = _module("skills/skill-orchestrator/scripts/runtime_sources.py", "prd_sources").closure(ROOT)
    except (OSError, ValueError) as exc:
        raise ValueError("PRD gate identity changed or missing; complete pinned source required") from exc
    return {'schema': 'cometweb.prd-handoff-lock/v1', 'files': files}



def protected(step: dict) -> bool:
    return any(key in step for key in ('artifact_profile', 'handoff_gate', 'gate_lock'))


def validate_step(step: dict) -> None:
    if not protected(step): return
    if step.get("handoff_gate") == PROFILE_GATE:
        _module(PROFILE_PATH,"profile_step_gate").validate_profile_step(step,ROOT)
        return
    if step.get('handoff_gate') == GATE:
        if (step.get('skill') != 'brief-architect' or step.get('envelope_out') != 'ArtifactEnvelope'
                or step.get('artifact_profile') != 'PRD'):
            raise ValueError('invalid PRD handoff step')
    elif step.get('handoff_gate') == DOMAIN_GATE:
        if (step.get('skill'), step.get('envelope_out')) not in {('evidence-researcher','EvidenceEnvelope'),('ai-council','DecisionHandoff')}:
            raise ValueError('invalid domain handoff step')
        _module(DOMAIN_PATH, 'plan_domain_gate').validate_context(step.get('domain_context'))
    elif step.get('handoff_gate') == WRAPPER_GATE:
        if 'artifact_profile' in step or not isinstance(step.get('skill'),str) or not step['skill'] or not isinstance(step.get('envelope_out'),str) or not step['envelope_out']:
            raise ValueError('invalid final-envelope handoff step')
    else:
        raise ValueError('unsupported handoff gate')
    if 'domain_context' in step:
        _module(DOMAIN_PATH, 'step_domain_context').validate_context(step['domain_context'])
    if step.get('gate_lock') != gate_lock():
        raise ValueError('PRD gate identity changed or missing; regenerate plan and create a new run')


def attach(plan: dict, *, with_domain_gates: bool = False, domain_context: dict | None = None) -> dict:
    """Prepend one explicitly requested briefing gate; preserve default planner output."""
    result = json.loads(canonical(plan))
    if not result.get('steps'):
        raise ValueError('PRD handoff requires a downstream workflow step')
    if any(protected(step) or step.get('skill') == 'brief-architect' for step in result['steps']):
        raise ValueError('plan already contains a briefing or handoff gate')
    lock = gate_lock()
    for step in result['steps']:
        if not step.get('envelope_out'):
            raise ValueError('gated workflow requires typed downstream envelopes')
        step['handoff_gate'] = WRAPPER_GATE
        step['gate_lock'] = lock
    result['steps'].insert(0, {'skill':'brief-architect', 'purpose':'Produce a READY PRD before downstream execution',
                             'envelope_out':'ArtifactEnvelope', 'read_skill':True, 'artifact_profile':'PRD',
                             'handoff_gate':GATE, 'gate_lock':lock})
    if with_domain_gates:
        if [step['skill'] for step in result['steps']] != ['brief-architect','evidence-researcher','ai-council']:
            raise ValueError('domain adapter requires exactly PRD -> research -> Council')
        context = domain_context or {'question':result['goal_summary'],'context':{},'mode':'LIGHT','decision_value':0.5,'max_attempts':2}
        _module(DOMAIN_PATH, 'attach_domain_gate').validate_context(context)
        for index, step in enumerate(result['steps']):
            step['domain_context'] = json.loads(canonical(context))
            if index: step['handoff_gate'] = DOMAIN_GATE
    result['single_skill_alternative'] = None
    result['boundaries'].append('PRD handoff requires final CW-AIP, producer schema and kernel READY; unresolved decisions stop execution.')
    return result


def _module(relative: str, name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def validate(envelope: Any, lock: dict | None = None, *, expected_type: str = 'ArtifactEnvelope', expected_producer: str = 'brief-architect', prd_required: bool = True, domain_required: bool = False, domain_context: dict | None = None, expected_report_as_of: str | None = None) -> dict:
    """No coercion or ledger writes. Reports remain separate from executable handoffs."""
    try:
        import jsonschema
    except ImportError as exc:
        raise ValueError('jsonschema is required for PRD handoff; validation was not performed') from exc
    before = gate_lock()
    if lock is not None and lock != before:
        raise ValueError('PRD gate identity changed; new plan/run required')
    # Own an immutable JSON snapshot before checking it; reject noncanonical JSON.
    envelope = json.loads(canonical(envelope))
    wrapper_errors = []
    if not isinstance(envelope, dict):
        wrapper_errors.append('envelope must be an object')
        brief = None
    else:
        wrapper = _module(WRAPPER_PATH, 'prd_wrapper')
        try:
            wrapper_errors.extend(wrapper.validate_envelope(envelope, expected_type=expected_type, final=True))
        except (TypeError, ValueError) as exc:
            wrapper_errors.append('invalid wrapper: ' + str(exc))
        if envelope.get('producer') != expected_producer: wrapper_errors.append('producer does not match planned skill')
        brief = envelope.get('payload')
    schema_errors = []
    kernel = None
    status_matches = None
    accepted = not wrapper_errors
    if prd_required:
        schema = json.loads((ROOT / SCHEMA_PATH).read_text())
        jsonschema.Draft202012Validator.check_schema(schema)
        schema_errors = [{'path':list(e.absolute_path), 'keyword':e.validator, 'message':e.message}
                         for e in jsonschema.Draft202012Validator(schema).iter_errors(brief)]
        kernel = _module(KERNEL_PATH, 'prd_brief_kernel').readiness(brief)
        status_matches = isinstance(brief, dict) and brief.get('status') == kernel['status']
        accepted = accepted and not schema_errors and status_matches and kernel['status'] == 'READY'
    domain = None
    if domain_required:
        try:
            domain = _module(DOMAIN_PATH, 'validate_domain_gate').validate(brief, expected_producer, domain_context, expected_report_as_of=expected_report_as_of)
        except (ValueError, TypeError, KeyError, OSError) as exc:
            domain = {'accepted':False,'error':str(exc)}
        accepted = accepted and domain['accepted']
    if gate_lock() != before: raise ValueError('PRD gate changed during validation')
    return {'accepted':accepted, 'domain_validation':domain, 'wrapper_errors':wrapper_errors, 'schema_errors':schema_errors,
            'kernel':kernel, 'status_matches':status_matches, 'gate_lock_hash':digest(canonical(before)),
            'envelope_id':envelope.get('id') if isinstance(envelope, dict) else None,
            'envelope_hash':digest(canonical(envelope)), 'brief_hash':digest(canonical(brief)), 'payload_hash':digest(canonical(brief)),
            'expected_type':expected_type, 'producer':envelope.get('producer') if isinstance(envelope,dict) else None}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('envelope_json', type=Path)
    args = parser.parse_args()
    try:
        result = validate(json.loads(args.envelope_json.read_text()))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result['accepted'] else 1
    except (OSError, ValueError, TypeError) as exc:
        print('FAIL: '+str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__': raise SystemExit(main())
