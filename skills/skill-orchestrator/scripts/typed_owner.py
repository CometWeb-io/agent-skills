"""Typed SOURCE_BOUND local reports with exhaustive native source bindings.

This contract is opt-in and read-only, not a full replacement for each owner's
live-host schema. Native validators still check cross-field rules independently.
"""
import copy
import json
import re
from datetime import datetime
from pathlib import Path

VERSION = 'cometweb.typed-local-owner/v2'
OWNERS = {'brief-architect', 'content-writer', 'product-operator', 'web-app-auditor'}


def schema(owner: str, root: Path) -> dict:
    if owner not in OWNERS:
        raise ValueError('unsupported typed owner')
    return json.loads((root / f'skills/skill-orchestrator/references/native-reports/{owner}.schema.json').read_text())


def validate_timestamp(value):
    if not isinstance(value,str):raise ValueError('parent report_as_of must be text')
    try:stamp=datetime.fromisoformat(value.replace('Z','+00:00'))
    except ValueError:raise ValueError('parent report_as_of must be ISO-8601') from None
    if stamp.tzinfo is None or 'T' not in value:raise ValueError('parent report_as_of requires timestamp and timezone')
    pattern = r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?(?:Z|[+-][0-9]{2}:[0-9]{2})'
    if not re.fullmatch(pattern, value):
        raise ValueError('parent report_as_of requires full seconds and a canonical Z or HH:MM timezone')
    return value


def response_schema(base, owner, root, context, report_as_of=None):
    result = copy.deepcopy(base)
    native = schema(owner, root)
    def inline(value):
        if isinstance(value, dict):
            if '$ref' in value:
                name = value['$ref'].removeprefix('#/$defs/')
                if name not in native.get('$defs', {}):
                    raise ValueError('unsupported native schema reference')
                return inline(native['$defs'][name])
            return {k: inline(v) for k, v in value.items() if k not in {'$defs', '$schema', '$id'}}
        if isinstance(value, list):
            return [inline(v) for v in value]
        return value
    result['properties']['owner_output'] = inline(native)
    if owner=='product-operator' and report_as_of is not None:
        result['properties']['owner_output']['properties']['as_of']={'type':'string','enum':[validate_timestamp(report_as_of)]}
    ids = [row['id'] for row in context['sources']]
    result['properties']['native_source_bindings'] = {'type': 'array', 'minItems': 1, 'maxItems': 64,
        'items': {'type': 'object', 'additionalProperties': False,
                  'properties': {'pointer': {'type': 'string', 'pattern': {'brief-architect':r'^/owner_output/inputs/[0-9]+$', 'web-app-auditor':r'^/owner_output/evidence/[0-9]+/location$', 'content-writer':r'^/owner_output/claims/[0-9]+/evidence/[0-9]+/source$', 'product-operator':r'^/owner_output/(?:blockers|verify_now|decision_now|now|next|later|watch|stop)/[0-9]+/evidence/[0-9]+/source$'}[owner]},
                                 'source_id': {'type': 'string', 'enum': ids}},
                  'required': ['pointer', 'source_id']}}
    result['required'] += ['owner_output', 'native_source_bindings']
    return result


def source_slots(value, owner):
    """Enumerate every source-bearing native field; unknown pointers are rejected."""
    slots = {}
    if owner == 'brief-architect':
        slots = {f'/inputs/{i}': {'reference': v} for i, v in enumerate(value['inputs'])}
    elif owner == 'web-app-auditor':
        slots = {f'/evidence/{i}/location': {'reference': v['location']} for i, v in enumerate(value['evidence'])}
    elif owner == 'content-writer':
        for i, claim in enumerate(value['claims']):
            for j, ev in enumerate(claim['evidence']):
                slots[f'/claims/{i}/evidence/{j}/source'] = {'id': ev['source'], 'reference': ev['locator'], 'kind': ev['authority']}
    elif owner == 'product-operator':
        for group in ('blockers', 'verify_now', 'decision_now', 'now', 'next', 'later', 'watch', 'stop'):
            for i, item in enumerate(value[group]):
                for j, ev in enumerate(item['evidence']):
                    slots[f'/{group}/{i}/evidence/{j}/source'] = {'id': ev['source'], 'reference': ev['locator'], 'kind': ev['claim_type']}
    return {'/owner_output' + pointer: slot for pointer, slot in slots.items()}


def check(response, owner, root, context):
    from jsonschema import Draft202012Validator
    report = response['owner_output']
    errors = [f'native schema {list(e.path)}: {e.message}' for e in Draft202012Validator(schema(owner, root)).iter_errors(report)]
    if errors:
        return errors
    rows = response['native_source_bindings']
    by_id = {row['id']: row for row in context['sources']}
    pointers = [row['pointer'] for row in rows]
    slots = source_slots(report, owner)
    if len(set(pointers)) != len(pointers) or set(pointers) != set(slots):
        errors.append('native bindings must cover every source slot exactly once')
    for row in rows:
        original = by_id.get(row['source_id'])
        slot = slots.get(row['pointer'])
        if original is None or slot is None:
            errors.append('native binding references an unknown source or pointer')
            continue
        for key, expected in slot.items():
            if original[key] != expected:
                errors.append('native source identity/reference/kind changed: ' + row['pointer'])
    if owner == 'content-writer' and (len(report['approved_sources']) != len(by_id) or set(report['approved_sources']) != set(by_id)):
        errors.append('native approved_sources must match parent source IDs exactly')
    return errors
