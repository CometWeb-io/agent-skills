"""Default planners keep experimental profiles out; registries cannot self-promote."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'skills/skill-orchestrator/scripts'


@pytest.mark.parametrize('goal', ['Audit conversion and pricing', 'Design an A/B experiment',
                                 'Plan activation onboarding', 'Write an operating procedure'])
@pytest.mark.parametrize('script', ['skill-orchestrator/scripts/orchestrate_kernel.py',
                                   'skill-orchestrator-multiagent/scripts/orchestrate_multiagent_kernel.py'])
def test_matching_goal_without_opt_in_never_attaches_profile_or_pack(goal, script):
    result = subprocess.run([sys.executable, str(ROOT / 'skills' / script), goal, '--json'],
                            capture_output=True, text=True, check=True)
    payload = json.loads(result.stdout)
    plan = payload.get('plan', payload)
    assert 'specialist_profile' not in plan and 'capability_packs' not in plan
    assert all('profile_lock' not in step and 'artifact_profile' not in step for step in plan['steps'])


@pytest.mark.parametrize('module,registry,folder', [
    ('specialist_profiles', 'specialist-profiles.json', 'specialist-profiles'),
    ('capability_packs', 'capability-packs.json', 'capability-packs'),
])
@pytest.mark.parametrize('status', ['QUALIFIED', None])
def test_unqualified_registry_cannot_claim_promotion(tmp_path, module, registry, folder, status):
    spec = importlib.util.spec_from_file_location('opt_in_' + module, SCRIPTS / (module + '.py'))
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    shutil.copytree(ROOT / folder, tmp_path / folder)
    (tmp_path / 'registry').mkdir()
    value = json.loads((ROOT / 'registry' / registry).read_text())
    value['status'] = status
    (tmp_path / 'registry' / registry).write_text(json.dumps(value))
    with pytest.raises(ValueError, match='experimental registry status'):
        helper.load_registry(tmp_path)
