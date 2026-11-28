"""A structurally partial portfolio must not be certified as a complete report."""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'portfolio_kernel.py'
SPEC = importlib.util.spec_from_file_location('portfolio_completeness', SCRIPT)
kernel = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(kernel)


def complete_report():
    return {
        'protocol_version': '1.0', 'as_of': '2026-11-06T10:00:00+01:00',
        'horizon': '14d', 'primary_goal': 'Assess competing commitments',
        'portfolio_scope': ['client', 'product'],
        'capacity': {'source': 'unknown'}, 'coverage': {'calendar': 'unavailable'},
        'readiness': {'status': 'PROVISIONAL', 'reason': 'Capacity not established'},
        'must_do': [], 'now': [],
    }


def test_empty_report_is_not_complete_and_cli_fails(tmp_path):
    assert kernel.validate_report({})
    path = tmp_path / 'empty.json'
    path.write_text('{}')
    result = subprocess.run([sys.executable, str(SCRIPT), 'validate', '--report-json', str(path)],
                            text=True, capture_output=True, check=False)
    assert result.returncode == 1
    assert json.loads(result.stdout)['valid'] is False


@pytest.mark.parametrize('field', ['protocol_version', 'as_of', 'horizon', 'primary_goal',
                                  'portfolio_scope', 'capacity', 'coverage', 'readiness'])
def test_missing_context_is_rejected(field):
    report = complete_report()
    report.pop(field)
    assert kernel.validate_report(report), field


@pytest.mark.parametrize('field,value', [
    ('protocol_version', '42'), ('as_of', '2026-11-06'), ('as_of', 'not-a-date'),
    ('horizon', ' '), ('primary_goal', ''), ('portfolio_scope', ['']),
    ('capacity', []), ('capacity', {'source': ''}), ('coverage', {}),
    ('readiness', {'status': 'READYISH'}), ('readiness', {'status': 'PROVISIONAL'}),
    ('now', [None]), ('now', 'not-a-list'),
])
def test_malformed_context_is_rejected_without_crashing(field, value):
    report = complete_report()
    report[field] = value
    assert kernel.validate_report(report)


def test_explicit_unknown_goal_and_scope_can_be_blocked_without_inventing_values():
    report = complete_report()
    report.update(primary_goal='UNKNOWN', portfolio_scope=[],
                  readiness={'status': 'BLOCKED', 'reason': 'Goal and scope unavailable'})
    assert kernel.validate_report(report) == []
    report['readiness']['status'] = 'READY'
    assert kernel.validate_report(report)


def test_complete_report_keeps_existing_evidence_and_delegation_gates():
    report = complete_report()
    assert kernel.validate_report(report) == []
    report['now'] = [{'id': 'A', 'action': 'Ship 10 items', 'done_when': 'done', 'evidence': []}]
    errors = kernel.validate_report(report)
    assert any('evidence' in message for message in errors)
    assert any('provenance' in message for message in errors)


@pytest.mark.parametrize('field,value', [
    ('done_when', '  '), ('done_when', {'result': 'done'}), ('done_when', True),
    ('evidence', [None]), ('evidence', ['  ']), ('evidence', [{}]),
    ('evidence', [42]), ('evidence', 'not a list'),
])
def test_required_action_fields_reject_empty_or_wrong_type_values(field, value):
    report = complete_report()
    item = {'action': 'Review current work', 'done_when': 'Work reviewed', 'evidence': ['source:one']}
    item[field] = value
    report['now'] = [item]
    assert any(field in error for error in kernel.validate_report(report))


@pytest.mark.parametrize('evidence', [
    ['source:one'], [{'source': 'email', 'locator': 'thread', 'claim': 'request'}],
])
def test_required_action_fields_accept_documented_evidence_forms(evidence):
    report = complete_report()
    report['now'] = [{'action': 'Review current work', 'done_when': 'Work reviewed', 'evidence': evidence}]
    assert kernel.validate_report(report) == []


def test_legacy_invariants_mode_is_explicitly_partial(tmp_path):
    assert kernel.validate_invariants({}) == []
    path = tmp_path / 'partial.json'
    path.write_text('{}')
    result = subprocess.run([sys.executable, str(SCRIPT), 'validate-invariants', '--report-json', str(path)],
                            text=True, capture_output=True, check=False)
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output['valid'] is True
    assert output['validation_scope'] == 'invariants_only'
    assert output['complete_report_validated'] is False


@pytest.mark.parametrize('source', ['unknown', 'UNKNOWN', 'relative-only', 'relative_only'])
def test_unknown_or_relative_capacity_cannot_supply_exact_hours(source):
    report = complete_report()
    report['capacity'] = {'source': source, 'hours': 40}
    assert kernel.validate_report(report)


@pytest.mark.parametrize('value', [None, '', [], {}, 4])
def test_coverage_requires_an_explicit_readable_state(value):
    report = complete_report()
    report['coverage'] = {'calendar': value}
    assert kernel.validate_report(report)


@pytest.mark.parametrize('reference', [[None], [{}], [42], ['  ']])
def test_empty_or_nontext_references_do_not_prove_exact_claims(reference):
    report = complete_report()
    report['now'] = [{'id': 'A', 'action': 'Deliver 10 items', 'done_when': 'Done',
                      'evidence': ['source'], 'evidence_ref': reference}]
    assert any('provenance gate' in error for error in kernel.validate_report(report))


@pytest.mark.parametrize('reference', [[None], [{}], [42], ['  ']])
def test_empty_or_nontext_references_do_not_confirm_delegate(reference):
    report = complete_report()
    report['delegate'] = [{'id': 'A', 'delegate_to': 'external person', 'question': 'Question',
                           'return_contract': 'Answer', 'delegate_evidence_ref': reference}]
    assert any('reality gate' in error for error in kernel.validate_report(report))


@pytest.mark.parametrize('field,value', [
    ('delegate_to', {'name': 'external'}), ('delegate_to', '  '),
    ('question', ['question']), ('question', '  '),
    ('return_contract', True), ('return_contract', '  '),
])
def test_delegation_requires_readable_executor_question_and_return_contract(field, value):
    report = complete_report()
    delegate = {'delegate_to': 'external person', 'question': 'Question',
                'return_contract': 'Answer', 'user_defined': True}
    delegate[field] = value
    report['delegate'] = [delegate]
    assert any(field in error for error in kernel.validate_report(report))


@pytest.mark.parametrize('hours', [True, -1, '40', {}, float('nan'), float('inf')])
def test_supplied_capacity_hours_must_be_finite_nonnegative_numbers(hours):
    report = complete_report()
    report['capacity'] = {'source': 'user-provided', 'hours': hours}
    assert kernel.validate_report(report)


def test_zero_capacity_can_be_recorded_when_supplied():
    report = complete_report()
    report['capacity'] = {'source': 'user-provided', 'hours': 0}
    assert kernel.validate_report(report) == []


@pytest.mark.parametrize('value', [True, -1, 6, '5', {}, float('nan'), float('inf')])
def test_rank_rejects_invalid_scoring_values_instead_of_fabricating_rank(value):
    with pytest.raises(ValueError, match='goal_alignment'):
        kernel.rank_items([{'id': 'A', 'commitment_type': 'strategic', 'goal_alignment': value}])


def test_rank_preserves_explicit_zero_and_existing_known_scores():
    result = kernel.rank_items([{'id': 'A', 'commitment_type': 'strategic', 'goal_alignment': 0}])
    assert result[0]['priority_score'] == 11.5


@pytest.mark.parametrize('value', [True, 1.2, '3', {}, float('nan')])
def test_invalid_deadline_distance_is_not_silently_treated_as_no_urgency(value):
    with pytest.raises(ValueError, match='days_to_deadline'):
        kernel.rank_items([{'id': 'A', 'commitment_type': 'strategic', 'days_to_deadline': value}])
