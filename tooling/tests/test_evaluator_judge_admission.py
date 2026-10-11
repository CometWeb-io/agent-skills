"""Invalid judge metadata and bounds cannot promote a declared experiment."""
import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('judge_admission', ROOT / 'skills/skill-evaluator/scripts/kernel.py')
kernel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kernel)
CASES = json.loads((ROOT / 'skills/skill-evaluator/evals/cases.json').read_text())


def report(real=False):
    case_id = 'deep-llm-judge-calibrated' if real else 'improved'
    data = copy.deepcopy(next(c['input'] for c in CASES if c['id'] == case_id))
    data['mode'] = 'STANDARD'
    return data


@pytest.mark.parametrize('flag', ['uses_llm_judge', 'runtime_executed'])
@pytest.mark.parametrize('value', [None, 0, 1, 'true', [], {}])
def test_execution_flags_require_booleans(flag, value):
    data = report()
    data[flag] = value
    result = kernel.validate(data)
    assert result['status'] == 'INVALID'
    assert f'{flag}:boolean' in result['errors']
    assert result['promotion_eligible'] is False


@pytest.mark.parametrize('mode', ['STANDARD', 'DEEP'])
@pytest.mark.parametrize('status', ['NEEDS_REVIEW', 'INSUFFICIENT_DATA', 'NOT_USED'])
def test_executed_model_judge_requires_calibration(mode, status):
    data = report(real=True)
    data.update(mode=mode, judge_agreement={'status': status})
    result = kernel.validate(data)
    assert result['status'] == 'INVALID' and result['promotion_eligible'] is False
    assert any(error.startswith('judge_agreement:') for error in result['errors'])


def test_model_judge_is_not_scripted_execution():
    data = report()
    data.update(uses_llm_judge=True, judge_agreement={'status': 'CALIBRATED'})
    result = kernel.validate(data)
    assert result['status'] == 'INVALID'
    assert 'local-deterministic:llm-judge' in result['errors']


@pytest.mark.parametrize('mode', ['STANDARD', 'DEEP'])
def test_unexecuted_model_judge_plan_never_claims_empirical_results(mode):
    data = report(real=True)
    data.update(mode=mode, execution_mode='SPEC_ONLY', runtime_executed=False,
                judge_agreement={'status': 'NOT_USED'})
    result = kernel.validate(data)
    assert result['status'] == 'DESIGN_READY'
    assert result['promotion_eligible'] is False and result['empirical_claim_allowed'] is False


@pytest.mark.parametrize('key', ['min_pass_rate_delta', 'trigger_precision_floor', 'trigger_recall_floor',
                                  'max_token_ratio', 'max_duration_ratio'])
@pytest.mark.parametrize('value', [float('nan'), float('inf'), 10**1000], ids=['nan', 'infinity', 'huge-integer'])
def test_policy_bounds_are_finite_without_conversion_errors(key, value):
    data = report()
    data['promotion_policy'][key] = value
    result = kernel.validate(data)
    assert result['status'] == 'INVALID'
    assert f'promotion_policy:{key}' in result['errors']


def test_equal_success_rates_are_not_improvement_with_zero_threshold():
    data = report()
    data['candidate']['passed'] = data['baseline']['passed']
    data['promotion_policy']['min_pass_rate_delta'] = 0
    result = kernel.validate(data)
    assert result['status'] == 'NO_MATERIAL_CHANGE' and result['promotion_eligible'] is False


@pytest.mark.parametrize('key', ['declared_case_ids', 'executed_case_ids'])
def test_positive_metrics_need_nonempty_case_identity(key):
    data = report()
    data[key] = []
    result = kernel.validate(data)
    assert result['status'] == 'INVALID' and key in result['errors']


def test_calibrated_and_scripted_reports_remain_eligible():
    assert kernel.validate(report(real=True))['promotion_eligible'] is True
    assert kernel.validate(report())['promotion_eligible'] is True


@pytest.mark.parametrize('policy', [[], 'policy', {'max_token_ratio': float('nan')},
                                   {'trigger_precision_floor': True}])
def test_unexecuted_plan_needs_valid_policy(policy):
    data = report()
    data.update(execution_mode='SPEC_ONLY', runtime_executed=False, promotion_policy=policy)
    result = kernel.validate(data)
    assert result['status'] == 'INVALID' and result['promotion_eligible'] is False
    assert any(error.startswith('promotion_policy:') for error in result['errors'])


@pytest.mark.parametrize('change', ['uncalibrated', 'invalid-flag'])
def test_markdown_grader_rejects_invalid_promotion_payload(change):
    import re
    import grade_output as go

    text = (ROOT / 'evals/output/skill-evaluator/good-improved.md').read_text()
    match = re.search(r'```json\n(.*?)\n```', text, re.S)
    data = json.loads(match.group(1))
    if change == 'uncalibrated':
        data['judge_agreement'] = {'status': 'NEEDS_REVIEW'}
    else:
        data['uses_llm_judge'] = 'true'
    text = text[:match.start(1)] + json.dumps(data) + text[match.end(1):]
    issues = go.grade('skill-evaluator', text)
    assert 'SIDECAR_INVALID:experiment-kernel' in {issue.key() for issue in issues}
