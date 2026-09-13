"""Synthetic regressions for decision admission; no model or external approval is simulated."""
from __future__ import annotations
import importlib.util
import itertools
import json
from pathlib import Path
import subprocess
import sys
import pytest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/council_kernel.py'
spec = importlib.util.spec_from_file_location('council_safety_subject', SCRIPT)
k = importlib.util.module_from_spec(spec)
spec.loader.exec_module(k)
AS_OF = '2026-09-13T10:00:00+00:00'


def row(**changes):
    return {'claim_id': 'c1', 'claim_type': 'general_web', 'material': True,
            'last_verified_at': '2026-09-13T09:00:00+00:00', **changes}


def gate(**changes):
    data = dict(proposed_verdict='GO', confidence=.99, required_confidence_value=.8,
                reversible_experiment_available=False)
    data.update(changes)
    return k.gate_verdict(**data)


@pytest.mark.parametrize('changes', [
    {'freshness_status': 'REFRESH_REQUIRED'},
    {'human_approval_required': True},
    {'freshness_status': 'UNKNOWN', 'human_approval_required': True},
])
def test_binding_block_remains_a_block(changes):
    assert gate(gate_statuses={'security': 'BLOCK'}, **changes) == 'NO-GO'


@pytest.mark.parametrize('verdict', ['GO', 'NO-GO'])
@pytest.mark.parametrize('experiment', [True, False])
def test_confidence_does_not_erase_critical_gap(verdict, experiment):
    assert gate(proposed_verdict=verdict, critical_gap='unverified prerequisite',
                reversible_experiment_available=experiment) == ('TEST' if experiment else 'DEFER')


@pytest.mark.parametrize('verdict', ['GO', 'TEST'])
def test_experiment_does_not_bypass_required_controls(verdict):
    assert gate(proposed_verdict=verdict, gate_statuses={'privacy': 'CLEAR_WITH_CONTROLS'},
                reversible_experiment_available=True) == 'DEFER'


@pytest.mark.parametrize('field', ['confidence', 'required_confidence_value'])
@pytest.mark.parametrize('value', [None, '0.9', True, -1, 1.1, float('nan'), float('inf')])
def test_invalid_gate_numbers_are_not_clamped(field, value):
    with pytest.raises(ValueError):
        gate(**{field: value})


@pytest.mark.parametrize('field', ['controls_implemented', 'human_approved',
                                  'human_approval_required', 'reversible_experiment_available'])
def test_gate_flags_are_real_booleans(field):
    with pytest.raises(ValueError):
        gate(**{field: 'false'})


@pytest.mark.parametrize('status', [None, '', 'UNKNOWN', 'REFRESH_REQUIRED'])
def test_missing_freshness_is_not_clear(status):
    assert gate(freshness_status=status) == 'DEFER'


def test_missing_binding_dimension_cannot_disappear():
    result = k.decompose_confidence({'thesis': .99}, ['security'])
    assert result['overall'] == 0
    assert result['missing_binding_dimensions'] == ['security']


@pytest.mark.parametrize('mode', ['FAST', 'STANDARD', 'DEEP', 'LIGHT'])
def test_all_required_gatekeepers_survive_budget(mode):
    contract = {'question': 'bounded test', 'primary_domain': 'strategy',
                'risk_surfaces': ['legal', 'privacy', 'security', 'financial', 'responsible_ai', 'reputation']}
    result = k.route_roles(contract, mode)
    assert set(result['gatekeepers']) == {'legal', 'privacy', 'security', 'financial_risk', 'responsible_ai', 'reputation'}


def test_light_is_fast_alias():
    assert k.mode_budget('LIGHT') == k.mode_budget('FAST')


def test_unknown_mode_is_rejected():
    with pytest.raises(ValueError):
        k.mode_budget('FAAST')


@pytest.mark.parametrize('changes', [
    {'last_verified_at': '2027-01-01T00:00:00+00:00'},
    {'published_at': '2027-01-01T00:00:00+00:00'},
    {'last_verified_at': '2026-09-13T09:00:00'},
    {'last_verified_at': '2026-09-13not-a-time'},
    {'expires_at': 'not-a-date'},
    {'expires_at': '2026-09-13T09:30:00+00:00'},
    {'expires_at': AS_OF},
    {'effective_to': AS_OF},
    {'effective_from': '2026-10-01T00:00:00+00:00', 'effective_to': '2026-09-01T00:00:00+00:00'},
    {'verified_for_decision': 'false', 'claim_type': 'law_regulation'},
    {'system_of_record_verified': 'false', 'claim_type': 'internal_metric'},
    {'material': 'false'},
    {'claim_type': 'misspelled-policy'},
    {'last_verified_at': '2026-09-13T08:00:00+00:00', 'verified_at': '2026-09-13T09:00:00+00:00'},
])
def test_temporal_contradictions_never_admit(changes):
    result = k.evaluate_temporal_truth(row(**changes), AS_OF)
    assert result['admissible'] is False


@pytest.mark.parametrize('as_of', ['bad', '2026-09-13', '2026-09-13T10:00:00', None])
def test_as_of_must_be_timezone_aware(as_of):
    with pytest.raises(ValueError):
        k.evaluate_temporal_truth(row(), as_of)


def test_empty_freshness_is_not_decision_ready():
    assert k.freshness_gate([], AS_OF)['decision_ready'] is False


@pytest.mark.parametrize('dependency', [
    {'operator': 'gte', 'current': 'no data', 'threshold': 10},
    {'operator': 'gte', 'current': float('nan'), 'threshold': 10},
    {'operator': 'typo', 'current': 10, 'threshold': 2},
    {'operator': 'changed'},
    {'operator': 'changed', 'previous': None, 'current': None},
    {'operator': 'pct_change_gt', 'previous': 0, 'current': 20, 'threshold': .1},
])
def test_bad_observation_is_unknown_not_unchanged(dependency):
    result = k.evaluate_watch_dependency(dependency)
    assert result['observation_status'] == 'UNKNOWN'
    assert result['triggered'] is None
    overlay = k.decision_validity_overlay({}, [dependency], AS_OF)
    assert overlay['status'] != 'VALID'
    assert overlay['revalidation_required'] is True


def test_stale_decision_keeps_other_watch_findings():
    result = k.decision_validity_overlay({'material_stale_evidence_count': 1},
        [{'id': 'x', 'operator': 'changed', 'previous': 1, 'current': 2, 'materiality': .9}], AS_OF)
    assert result['triggered_dependencies']
    assert result['revalidation_required'] is True


def test_no_watch_coverage_is_not_valid():
    assert k.decision_validity_overlay({}, [], AS_OF)['status'] != 'VALID'


def test_unsearched_critical_opposition_cannot_be_hidden():
    result = k.contradiction_coverage([{'claim_id': 'c1', 'importance': 1,
         'contradiction_tested': False, 'opposing_evidence_count': 1}])
    assert result['decision_ready'] is False
    assert result['critical_unresolved_claim_ids'] == ['c1']


def test_empty_contradiction_coverage_is_not_ready():
    result = k.contradiction_coverage([])
    assert result['decision_ready'] is False
    assert result['contradiction_coverage'] is None


@pytest.mark.parametrize('value', [None, 'missing', -1, 2, float('nan'), float('inf'), True])
def test_invalid_probability_not_counted_as_perfect_zero(value):
    result = k.forecast_score_report([{'probability': value, 'outcome': 0}])
    assert result['n'] == 0
    assert result['brier_score'] is None
    assert result['invalid_count'] == 1


def test_complete_forecast_accounting():
    result = k.forecast_score_report([{'probability': 0, 'outcome': 0},
        {'probability': .5, 'outcome': 'Pending'}, {'outcome': 0}, {'probability': 1, 'outcome': 1}])
    assert (result['n'], result['unresolved_count'], result['invalid_count']) == (2, 1, 1)
    assert result['brier_score'] == 0


def test_missing_required_gate_cannot_pass():
    assert gate(required_gatekeepers=['security']) == 'DEFER'
    assert gate(required_gatekeepers=['security'], gate_statuses={'security': 'NOT_REQUIRED'}) == 'DEFER'
    assert gate(required_gatekeepers=['security'], gate_statuses={'security': 'CLEAR'}) == 'GO'


@pytest.mark.parametrize('raw', ['{"security":"BLOCK","security":"CLEAR"}', '{"security":NaN}'])
def test_cli_rejects_invalid_json(raw):
    proc = subprocess.run([sys.executable, str(SCRIPT), 'gate', '--verdict', 'GO', '--confidence', '.99',
        '--required-confidence', '.8', '--freshness-status', 'CLEAR', '--gate-statuses-json', raw],
        capture_output=True, text=True, timeout=10)
    assert proc.returncode == 2
    assert 'Traceback' not in proc.stderr


def test_cli_requires_explicit_freshness_for_go():
    proc = subprocess.run([sys.executable, str(SCRIPT), 'gate', '--verdict', 'GO', '--confidence', '.99',
        '--required-confidence', '.8'], capture_output=True, text=True, timeout=10)
    assert json.loads(proc.stdout)['verdict'] == 'DEFER'


def test_valid_cases_still_work():
    assert gate() == 'GO'
    assert k.evaluate_temporal_truth(row(), AS_OF)['status'] == 'CURRENT'
    result = k.evaluate_watch_dependency({'operator': 'gte', 'current': 10, 'threshold': 10})
    assert result['triggered'] is True
    assert k.forecast_score_report([{'probability': .8, 'outcome': 1}])['brier_score'] == .04


def test_every_combination_preserves_explicit_block():
    for statuses in itertools.product(sorted(k.GATE_STATUSES), repeat=3):
        if 'BLOCK' in statuses:
            assert gate(gate_statuses=dict(zip(['a','b','c'], statuses)),
                        freshness_status='UNKNOWN', human_approval_required=True) == 'NO-GO'


@pytest.mark.parametrize('extra, code, verdict', [
    ([], 1, 'DEFER'),
    (['--freshness-status', 'CLEAR'], 0, 'GO'),
    (['--freshness-status', 'CLEAR', '--required-gates-json', '["security"]'], 1, 'DEFER'),
    (['--freshness-status', 'CLEAR', '--required-gates-json', '["security"]',
      '--gate-statuses-json', '{"security":"CLEAR"}'], 0, 'GO'),
    (['--gate-statuses-json', '{"security":"BLOCK"}'], 1, 'NO-GO'),
])
def test_cli_admission_exit_policy(extra, code, verdict):
    proc = subprocess.run([sys.executable, '-S', str(SCRIPT), 'gate', '--verdict', 'GO',
        '--confidence', '.99', '--required-confidence', '.8', '--require-go', *extra],
        capture_output=True, text=True, timeout=10)
    assert proc.returncode == code, proc.stderr
    assert json.loads(proc.stdout)['verdict'] == verdict


def test_watch_valid_stable_observation_remains_valid():
    observation = {'id': 'x', 'operator': 'changed', 'previous': 'build1', 'current': 'build1'}
    assert k.decision_validity_overlay({}, [observation], AS_OF)['status'] == 'VALID'


def test_expiry_is_exclusive_but_future_expiry_allows_current():
    assert k.evaluate_temporal_truth(row(expires_at='2026-09-13T10:00:01+00:00'), AS_OF)['admissible'] is True
    assert k.evaluate_temporal_truth(row(expires_at=AS_OF), AS_OF)['admissible'] is False


def test_equivalent_zoned_verification_aliases_are_accepted():
    result = k.evaluate_temporal_truth(row(verified_at='2026-09-13T11:00:00+02:00'), AS_OF)
    assert result['status'] == 'CURRENT'
