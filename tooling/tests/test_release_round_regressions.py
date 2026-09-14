"""Deterministic regressions; no remote provider calls or live skill execution."""
import copy
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from test_distribution_hardening import root, add
from test_review_packet_bridge import packet_source
from test_model_evals import response, case
import package_skill as package
import build_review_packets as bridge
import run_model_evals as runner


def test_canonical_evaluation_directory_is_packaged(root):
    add(root, 'evaluation/redteam-protocol.md', b'# Local evaluation\n')
    (root/'skills/demo/SKILL.md').write_text('---\nname: demo\ndescription: Regression fixture.\n---\n[Evaluation](evaluation/redteam-protocol.md)\n')
    entries, manifest = package.payload(root, 'demo')
    assert 'evaluation/redteam-protocol.md' in entries


@pytest.mark.parametrize('markdown', [
    '[Evidence][source]\n\n[source]: references/missing.md\n',
    '[Evidence](references/missing.md "Evidence title")\n',
    '[Evidence](<references/missing note.md>)\n',
])
def test_nontrivial_missing_markdown_resources_are_rejected(markdown):
    with pytest.raises(ValueError):
        package.check_resources({'SKILL.md': markdown.encode()})


@pytest.mark.parametrize('usage', [
    {'input_tokens': 10, 'output_tokens': 20, 'total_tokens': 999},
    {'input_tokens': 10, 'output_tokens': 20, 'total_tokens': 1},
])
def test_inconsistent_total_usage_rejected(usage):
    with pytest.raises(ValueError):
        runner.validate_response(response(usage=usage), allow_mock=True)


@pytest.mark.parametrize('value', [None, [], 'not-an-object'])
def test_response_nonobject_has_documented_validation_error(value):
    with pytest.raises(ValueError):
        runner.validate_response(value)


@pytest.mark.parametrize('change', [
    {'skill': '../outside'}, {'resources': 'references/file.md'},
    {'resources': ['../outside.md']}, {'capabilities': {'tools': 'false'}},
    {'rubric': [None]}, {'rubric': ['']}, {'fixture': 'not-an-object'},
])
def test_suite_contract_rejects_unsafe_or_ambiguous_shapes(change):
    c = case(); c.update(change)
    with pytest.raises(ValueError):
        runner.validate_suite({'schema': 'cometweb.model-evals/v1', 'cases': [c]})


def test_bridge_revalidates_usage_not_only_top_level_labels(packet_source):
    suite, requests, records, _ = packet_source
    records[0]['response']['usage'] = {'input_tokens': -1, 'output_tokens': 100}
    with pytest.raises(ValueError):
        bridge.build_packets(suite, requests, records)


@pytest.mark.parametrize('elapsed', [True, -0.01, float('nan'), float('inf')])
def test_bridge_rejects_bad_elapsed_records(packet_source, elapsed):
    suite, requests, records, _ = packet_source
    records[0]['elapsed_seconds'] = elapsed
    with pytest.raises(ValueError):
        bridge.build_packets(suite, requests, records)
