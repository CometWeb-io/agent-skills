"""Admission checks use the full canonical registry, not the earlier toy catalog."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tooling'))
from route_skill import route, matches
from run_policy_evals import evaluate

REGISTRY = json.loads((ROOT/'registry/skills.json').read_text())
POLICY = json.loads((ROOT/'registry/routing-policy.json').read_text())
CONTRACT = json.loads((ROOT/'evals/routing/canonical-suite.json').read_text())


@pytest.mark.parametrize('case', CONTRACT['cases'], ids=lambda c:c['id'])
def test_canonical_contract(case):
    result = route(case['prompt'], REGISTRY, POLICY)
    if 'expected_primary_skill' in case:
        assert result['primary_skill'] == case['expected_primary_skill'], result
    if 'expected_status' in case:
        assert result['status'] == case['expected_status'], result
    for sid in case.get('must_not_trigger', []):
        assert sid != result['primary_skill'] and sid not in result['candidates'], result


@pytest.mark.parametrize('pattern,text,expected', [
    (r'\S+', 'x', True), (r'^\D+$', '12', False), (r'^\D+$', 'text', True),
    (r'^\W+$', '!?', True), (r'^\W+$', 'abc', False), (r'\Bcat', 'cat', False),
    (r'\Bcat', 'bobcat', True), (r'ŻÓŁĆ', 'zolc', True),
])
def test_regex_escape_semantics_survive_normalization(pattern, text, expected):
    assert matches(pattern,text) is expected


@pytest.mark.parametrize('sid', ['ai-humanize','evidence-researcher','web-app-auditor','skill-orchestrator'])
def test_generic_explicit_denial(sid):
    result=route(f"Don't use @{sid}.",REGISTRY,POLICY)
    assert sid not in result['candidates'] and sid != result['primary_skill']
    assert result['blocked'][sid]=='explicitly_excluded'


def test_denied_coordinator_not_reintroduced_by_multiple_specialists():
    result=route('Without @skill-orchestrator, use @ai-humanize and @evidence-researcher.',REGISTRY,POLICY)
    assert result['primary_skill'] is None
    assert result['blocked']['skill-orchestrator']=='explicitly_excluded'


def test_denied_canonical_cannot_reenter_as_alias():
    result=route('Without @skill-orchestrator use @skill-orchestrator-multiagent.',REGISTRY,POLICY)
    assert result['primary_skill'] is None


@pytest.mark.parametrize('mutation', [
    lambda r:r['skills'].append(deepcopy(r['skills'][0])),
    lambda r:r['skills'][0].update(explicit_only='false'),
    lambda r:r['skills'][0].update(routing_signals=[[True,'x']]),
    lambda r:r['skills'][0].update(routing_signals=[[10,'(']]),
    lambda r:r['skills'][0].update(alias_of='missing'),
    lambda r:r['skills'][0].update(alias_of='ai-council'),
])
def test_invalid_catalog_fails_before_decision(mutation):
    registry=deepcopy(REGISTRY);mutation(registry)
    with pytest.raises(ValueError):route('hello',registry,POLICY)


def test_forbidden_only_case_is_executed_not_silently_ignored():
    report=evaluate(REGISTRY,POLICY,{'cases':[dict(id='negative',prompt='fix typos',must_not_trigger=['ai-humanize'])]})
    assert report['passed']==1


def test_empty_expectation_does_not_count_as_a_test():
    with pytest.raises(ValueError):
        evaluate(REGISTRY,POLICY,{'cases':[dict(id='empty',prompt='hello')]})
