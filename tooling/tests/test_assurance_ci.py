"""Synthetic Git/review records; these tests perform no model or GitHub calls."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest
import yaml

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _tooling_fixtures import root  # noqa: F401
import assurance_ci as mod
from review_skill_evals import CONDITIONS, EMPTY_INSTRUCTIONS


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()


def commit(root):
    git(root, 'add', '-A')
    git(root, 'commit', '-m', 'synthetic-test-candidate')
    return git(root, 'rev-parse', 'HEAD')


@pytest.fixture
def candidate(root):
    base = git(root, 'rev-parse', 'HEAD')
    (root / 'skills/demo/SKILL.md').write_text('Synthetic candidate instructions, not a model call.\n')
    head = commit(root)
    return root, base, head


def evidence(candidate, skill="demo"):
    root, base, head = candidate
    identity = mod.assess(root, base, head)['candidate']
    caps = {'tools': False}
    case = {'id': 'case-1', 'skill': skill, 'prompt': 'Synthetic task', 'fixture': {'text': 'fixture'},
            'rubric': ['Assess correctness'], 'resources': [], 'capabilities': caps}
    suite = {'schema': 'cometweb.model-evals/v1', 'cases': [case]}
    fixture = mod.experiment_fingerprint({'prompt': case['prompt'], 'fixture': case['fixture'], 'capabilities': caps, 'max_output_tokens': 128})
    hashes = {'no_skill': EMPTY_INSTRUCTIONS}
    for condition, revision in [('current', base), ('candidate', head)]:
        inventory = mod.tree(root, revision)
        hashes[condition] = mod.experiment_fingerprint(mod.instructions(root, inventory, mod.catalog(root, inventory), skill, []))
    exp = {'id': 'synthetic-experiment', 'suite_sha256': hashlib.sha256((json.dumps(suite, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()).hexdigest(),
           'instruction_sha256': hashes, 'host': 'synthetic-host', 'model': 'synthetic-label-not-a-call',
           'capabilities': caps, 'dimensions': ['correctness'], 'cases': [{'id': 'case-1', 'fixture_sha256': fixture}], 'repetitions': 1}
    runs, reviews = [], []
    for i, condition in enumerate(CONDITIONS):
        output = f'Synthetic test output {i}; no model was executed.'
        output_sha = hashlib.sha256(output.encode()).hexdigest()
        runs.append({'id': f'run-{i}', 'case_id': 'case-1', 'repetition': 0, 'condition': condition,
                     'execution_kind': 'model', 'host': exp['host'], 'model': exp['model'], 'capabilities': caps,
                     'response_id': f'synthetic-response-{i}', 'fixture_sha256': fixture, 'instructions_sha256': hashes[condition],
                     'output': output, 'output_sha256': output_sha, 'tokens': None, 'duration_ms': None})
        reviews.append({'run_id': f'run-{i}', 'output_sha256': output_sha, 'reviewer': 'synthetic-reviewer',
                        'review_kind': 'model_assisted', 'scores': {'correctness': i + 1},
                        'evidence': {'correctness': 'Synthetic annotation, not a verified fact.'}, 'flags': []})
    packet = {'skill': skill, 'suite': suite, 'max_output_tokens': 128, 'experiment_sha256': mod.experiment_fingerprint(exp),
              'bundle': {'schema': 'cometweb.skill-comparison/v1', 'experiment': exp, 'runs': runs, 'reviews': reviews}}
    return {'schema': mod.EVIDENCE_SCHEMA, 'candidate': identity, 'comparisons': [packet]}


def test_git_only_structural_report_is_never_behavioral_pass(candidate):
    root, base, head = candidate
    (root / 'skills/demo/SKILL.md').write_text('Uncommitted bytes must not replace the identified candidate.')
    report = mod.assess(root, base, head)
    assert report['candidate']['base_commit'] == base and report['candidate']['head_commit'] == head
    assert report['packages'] == [{'skill': 'demo', 'base_version': '1.0.0', 'head_version': '1.0.0', 'status': 'PASS', 'issues': []}]
    assert report['structural_checks']['repository_gates'] == 'NOT_RUN'
    assert report['comparison_evidence']['status'] == 'NOT_RUN'
    assert report['task_outcome'] == 'NOT_ASSESSED' and report['native_integration'] == 'NOT_RUN'
    assert report['policy']['satisfied'] is True
    assert mod.assess(root, base, head, require_evidence=True)['policy']['satisfied'] is False


def test_reviewed_records_are_not_task_outcome_or_native_evidence(candidate):
    data = evidence(candidate)
    result = mod.assess(*candidate, data, True)
    assert result['policy']['satisfied'] is True
    assert result['comparison_evidence']['status'] == 'REVIEWED_SUPPLIED_RECORDS'
    assert result['task_outcome'] == 'NOT_ASSESSED'
    assert result['native_integration'] == 'NOT_RUN'
    assert result['comparison_evidence']['results'][0]['comparison']['quality_verdict'] == 'human_decision_required'


@pytest.mark.parametrize('missing', ['reviews', 'runs', 'comparisons'])
def test_require_evidence_cannot_pass_missing_cells_or_reviews(candidate, missing):
    data = evidence(candidate)
    if missing == 'comparisons':
        data['comparisons'] = []
    else:
        packet = data['comparisons'][0]['bundle']
        packet[missing].pop()
        if missing == 'runs':
            packet['reviews'].pop()
    result = mod.assess(*candidate, data, True)
    assert result['policy']['satisfied'] is False
    assert result['comparison_evidence']['missing_skills'] == ['demo']
    assert result['task_outcome'] == 'NOT_ASSESSED'


@pytest.mark.parametrize('mutation', ['candidate', 'experiment_pin', 'suite', 'fixture', 'instructions', 'output',
                                      'missing_output', 'response_id', 'run_id', 'host', 'model', 'mock', 'case', 'budget',
                                      'top_verified', 'run_verified', 'experiment_verified', 'suite_verified', 'command'])
def test_tampered_or_falsely_verified_records_fail_closed(candidate, mutation):
    data = evidence(candidate)
    packet = data['comparisons'][0]
    bundle, exp = packet['bundle'], packet['bundle']['experiment']
    run = bundle['runs'][-1]
    if mutation == 'candidate':
        data['candidate']['head_commit'] = '0' * 40
    elif mutation == 'experiment_pin':
        packet['experiment_sha256'] = 'a' * 64
    elif mutation == 'suite':
        packet['suite']['cases'][0]['prompt'] = 'Changed stimulus'
    elif mutation == 'fixture':
        exp['cases'][0]['fixture_sha256'] = 'b' * 64
        for r in bundle['runs']:
            r['fixture_sha256'] = 'b' * 64
        packet['experiment_sha256'] = mod.experiment_fingerprint(exp)
    elif mutation == 'instructions':
        exp['instruction_sha256']['candidate'] = 'b' * 64
        run['instructions_sha256'] = 'b' * 64
        packet['experiment_sha256'] = mod.experiment_fingerprint(exp)
    elif mutation == 'output':
        run['output'] += ' Altered'
    elif mutation == 'missing_output':
        del run['output']
    elif mutation in {'response_id', 'run_id'}:
        field = 'id' if mutation == 'run_id' else mutation
        run[field] = bundle['runs'][0][field]
    elif mutation in {'host', 'model'}:
        run[mutation] = 'wrong-identity'
    elif mutation == 'mock':
        run['execution_kind'] = 'mock'
    elif mutation == 'case':
        run['case_id'] = 'absent-case'
    elif mutation == 'budget':
        packet['max_output_tokens'] = 256
    elif mutation == 'top_verified':
        data['verified_runtime_acceptance'] = True
    elif mutation == 'run_verified':
        run['verified'] = True
    elif mutation == 'experiment_verified':
        exp['verified_runtime_acceptance'] = True
        packet['experiment_sha256'] = mod.experiment_fingerprint(exp)
    elif mutation == 'suite_verified':
        packet['suite']['verified'] = True
    elif mutation == 'command':
        packet['command'] = ['sh', '-c', 'touch should-never-exist']
    with pytest.raises(ValueError):
        mod.assess(*candidate, data, True)
    assert not (candidate[0] / 'should-never-exist').exists()


def test_registry_change_and_alias_dependency_are_in_scope(root):
    registry = root / 'registry/skills.json'
    data = json.loads(registry.read_text())
    data['skills'].append({'id': 'alias', 'version': '1.0.0', 'alias_of': 'demo'})
    alias = root / 'skills/alias'
    alias.mkdir()
    for name in ('SKILL.md', 'VERSION', 'LICENSE'):
        (alias / name).write_text('1.0.0' if name == 'VERSION' else 'Synthetic alias')
    registry.write_text(json.dumps(data))
    base = commit(root)
    data['skills'][0]['description'] = 'Changed registry metadata'
    registry.write_text(json.dumps(data))
    head = commit(root)
    assert [p['skill'] for p in mod.assess(root, base, head)['packages']] == ['alias', 'demo']


def test_diverged_target_uses_merge_base_for_diff_and_exact_base_for_review(candidate):
    root, ancestor, head = candidate
    git(root, 'checkout', ancestor)
    (root / 'target-only.txt').write_text('Changes on the target branch must not appear as PR changes.')
    base = commit(root)
    result = mod.assess(root, base, head)
    assert result['candidate']['diff_base_commit'] == ancestor
    assert result['candidate']['base_commit'] == base
    assert result['changed_paths'] == ['skills/demo/SKILL.md']
    assert mod.assess(root, base, head, evidence((root, base, head)), True)['policy']['satisfied']


def test_deleted_package_is_reported_and_inconsistent_deletion_fails(root):
    base = git(root, 'rev-parse', 'HEAD')
    (root / 'skills/demo/SKILL.md').unlink()
    broken = commit(root)
    assert mod.assess(root, base, broken)['structural_checks']['status'] == 'FAIL'
    import shutil
    shutil.rmtree(root / 'skills/demo')
    path = root / 'registry/skills.json'
    data = json.loads(path.read_text())
    data['skills'] = []
    path.write_text(json.dumps(data))
    head = commit(root)
    result = mod.assess(root, base, head)
    assert result['packages'][0]['head_version'] is None
    assert result['structural_checks']['status'] == 'PASS'
    assert result['comparison_evidence']['missing_skills'] == ['demo']


def test_candidate_scripts_and_symlinks_are_never_executed(candidate):
    root, base, _ = candidate
    marker = root / 'executed'
    (root / 'skills/demo/conftest.py').write_text(f'from pathlib import Path\nPath({str(marker)!r}).touch()\n')
    head = commit(root)
    assert mod.assess(root, base, head)['structural_checks']['status'] == 'PASS'
    assert not marker.exists()
    (root / 'skills/demo/SKILL.md').unlink()
    (root / 'skills/demo/SKILL.md').symlink_to(root / 'registry/skills.json')
    head = commit(root)
    assert mod.assess(root, base, head)['structural_checks']['status'] == 'FAIL'
    assert not marker.exists()


@pytest.mark.parametrize('base', ['main', '--help', '$(touch injection)', '0' * 40])
def test_missing_or_unpinned_revisions_never_fall_back(candidate, base, capsys):
    root, _, head = candidate
    assert mod.main(['--repo', str(root), f'--base={base}', '--head', head]) == 2
    result = json.loads(capsys.readouterr().out)
    assert result['status'] == 'INVALID' and result['task_outcome'] == 'NOT_ASSESSED'
    assert not (root / 'injection').exists()


def test_cli_exit_codes_and_duplicate_json(candidate, capsys):
    root, base, head = candidate
    args = ['--repo', str(root), '--base', base, '--head', head]
    assert mod.main(args) == 0
    assert mod.main([*args, '--require-evidence']) == 1
    path = root / 'evidence.json'
    path.write_text('{"schema":"x","schema":"y"}')
    assert mod.main([*args, '--evidence', str(path)]) == 2
    path.write_text(json.dumps(evidence(candidate)))
    assert mod.main([*args, '--evidence', str(path), '--require-evidence']) == 0
    capsys.readouterr()


def test_workflow_trust_boundary_and_permissions():
    workflow = yaml.safe_load((TOOLS.parent / '.github/workflows/assurance-ci.yml').read_text())
    assert set(workflow[True]) == {'pull_request', 'workflow_dispatch'}
    assert workflow['permissions'] == {'contents': 'read'}
    job = workflow['jobs']['report']
    assert 'permissions' not in job
    steps = job['steps']
    assert steps[0]['with']['path'] == 'trusted'
    assert steps[0]['with']['ref'] == '${{ github.event.pull_request.base.sha || github.sha }}'
    assert steps[1]['with']['path'] == 'candidate'
    for step in steps[:2]:
        assert step['with']['persist-credentials'] is False and step['with']['fetch-depth'] == 0
    scripts = [step['run'] for step in steps if 'run' in step]
    assert len(scripts) == 1 and 'trusted/tooling/assurance_ci.py' in scripts[0]
    assert '${{' not in scripts[0] and '--repo candidate' in scripts[0]
    assert 'secrets.' not in json.dumps(workflow) and 'write' not in json.dumps(workflow)


@pytest.mark.parametrize('collision', ['id', 'response_id'])
def test_run_identities_cannot_be_reused_across_skill_packets(candidate, collision):
    root, base, _ = candidate
    path = root / 'registry/skills.json'
    catalog = json.loads(path.read_text())
    catalog['skills'].append({'id': 'alias', 'version': '1.0.0', 'alias_of': 'demo'})
    path.write_text(json.dumps(catalog))
    alias = root / 'skills/alias'
    alias.mkdir()
    for name in ('SKILL.md', 'VERSION', 'LICENSE'):
        (alias / name).write_text('1.0.0' if name == 'VERSION' else 'Synthetic alias')
    head = commit(root)
    data = evidence((root, base, head))
    other = evidence((root, base, head), 'alias')['comparisons'][0]
    for row in other['bundle']['runs']:
        if collision != 'id':
            old = row['id']
            row['id'] = 'alias-' + old
            for review in other['bundle']['reviews']:
                if review['run_id'] == old:
                    review['run_id'] = row['id']
        if collision != 'response_id':
            row['response_id'] = 'alias-' + row['response_id']
    data['comparisons'].append(other)
    with pytest.raises(ValueError, match='reused across packets'):
        mod.assess(root, base, head, data, True)


def test_tree_object_and_ambiguous_merge_base_are_not_acceptable(candidate, monkeypatch):
    root, base, head = candidate
    with pytest.raises(ValueError, match='name commits'):
        mod.assess(root, git(root, 'rev-parse', f'{base}^{{tree}}'), head)
    original = mod.git
    monkeypatch.setattr(mod, 'git', lambda repo, *args: (f'{base}\n{head}\n'.encode() if args[:2] == ('merge-base', '--all') else original(repo, *args)))
    with pytest.raises(ValueError, match='ambiguous merge base'):
        mod.assess(root, base, head)


def test_omitted_suite_case_is_not_complete_evidence(candidate):
    data = evidence(candidate)
    packet = data['comparisons'][0]
    extra = dict(packet['suite']['cases'][0], id='case-omitted')
    packet['suite']['cases'].append(extra)
    packet['bundle']['experiment']['suite_sha256'] = hashlib.sha256((json.dumps(packet['suite'], ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()).hexdigest()
    packet['experiment_sha256'] = mod.experiment_fingerprint(packet['bundle']['experiment'])
    with pytest.raises(ValueError, match='omits suite cases'):
        mod.assess(*candidate, data, True)
