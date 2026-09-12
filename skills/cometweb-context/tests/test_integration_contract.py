"""The bundle overlay must preserve existing canonical repository guarantees."""
import json
import pytest
from test_context_plan import module as planner
from test_validate_context_envelope import module as validator, valid_envelope


def test_registry_overrides_are_used(tmp_path):
    path = tmp_path / 'registry.json'
    path.write_text(json.dumps({'profiles': {'product': {'preferred_source_groups': ['sentinel']}}}))
    assert planner.load_profiles(path)['product'] == ['sentinel']


def test_invalid_registry_does_not_silently_fallback(tmp_path):
    path = tmp_path / 'registry.json'
    path.write_text('{"profiles":{"product":{"preferred_source_groups":[42]}}}')
    with pytest.raises(ValueError):
        planner.load_profiles(path)


def test_claim_is_not_hidden_by_brand_route():
    result = planner.pick_profiles('LinkedIn post: verify this public claim')
    assert result['primary'] == 'claim-verification'
    assert result['ambiguous'] and 'brand' in result['candidates']


def test_fallback_system_of_record_needs_gap():
    data = valid_envelope()
    data['sources'][0].update(authority='system_of_record', access='fallback')
    with pytest.raises(ValueError, match='authority_gap'):
        validator.validate(data)
    data['gaps'] = [{'kind': 'authority_gap', 'missing_authority': 'live CRM'}]
    validator.validate(data)


def test_confidential_summary_limit_is_preserved():
    data = valid_envelope()
    data['facts'][0].update(sensitivity='confidential', statement='x' * 801)
    with pytest.raises(ValueError, match='summary limit'):
        validator.validate(data)
