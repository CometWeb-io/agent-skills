"""Known generated scaffolds cannot enter either versioned distribution path."""
from pathlib import Path
import shutil
import json

import pytest

import new_skill
import package_skill
import plugin_release

ROOT = Path(__file__).resolve().parents[2]
DESCRIPTION = 'Synthetic fixture for observing package admission, with no model execution or empirical skill qualification.'
CONCRETE = f'---\nname: scaffold-probe\ndescription: {DESCRIPTION}\n---\n# Text checksum\n\nReturn the supplied text and its supplied checksum, or state that the checksum is missing.\n'
OLD_MARKERS = ("Replace these rules with the skill's real contract",
               'Scaffold placeholder from tooling/new_skill.py; replace with a real case')


@pytest.fixture
def generated(tmp_path):
    new_skill.create('scaffold-probe', DESCRIPTION, False, tmp_path)
    # These tests isolate template detection after a declared development transition.
    path = tmp_path / 'skills/scaffold-probe/MATURITY.json'
    maturity = json.loads(path.read_text())
    maturity['stage'] = 'DEVELOPMENT'
    path.write_text(json.dumps(maturity))
    (tmp_path / 'registry').mkdir()
    shutil.copyfile(ROOT / 'registry/package-policy.json', tmp_path / 'registry/package-policy.json')
    return tmp_path


def mask_old_markers(root):
    for path in (root / 'skills/scaffold-probe').rglob('*'):
        if path.is_file() and path.suffix in {'.md', '.py', '.json'}:
            text = path.read_text()
            for marker in OLD_MARKERS:
                text = text.replace(marker, 'Synthetic offline structural contract, not empirical qualification')
            path.write_text(text)


def test_release_gate_refuses_generated_front_door_after_marker_removal(generated):
    mask_old_markers(generated)
    errors = plugin_release.content_errors(generated)
    assert any(error.startswith('skills/scaffold-probe/SKILL.md:') for error in errors)


@pytest.mark.parametrize('instruction', [
    'State what this skill owns in one paragraph',
    'Describe the request shapes that belong here.',
    'Name the neighbouring skills and the cases that belong to them.',
])
@pytest.mark.parametrize('whitespace', [' ', '\r\n'])
def test_remaining_author_prompts_are_rejected_even_when_wrapped(generated, instruction, whitespace):
    mask_old_markers(generated)
    (generated / 'skills/scaffold-probe/SKILL.md').write_text(CONCRETE + whitespace.join(instruction.split()))
    assert plugin_release.content_errors(generated)


@pytest.mark.parametrize('existing_archive', [False, True])
def test_versioned_package_refuses_masked_scaffold_without_writes(generated, monkeypatch, existing_archive):
    mask_old_markers(generated)
    archive = generated / 'dist/scaffold-probe/0.1.0/skill.zip'
    if existing_archive:
        entries, manifest = package_skill.payload(generated, 'scaffold-probe')
        manifest.update(source_revision='a' * 40, source_tree='clean')
        archive.parent.mkdir(parents=True)
        archive.write_bytes(package_skill.archive(entries, manifest))
    before = {str(p.relative_to(generated)): p.read_bytes() for p in generated.rglob('*') if p.is_file()}
    monkeypatch.setattr(package_skill, 'source_revision', lambda root: 'a' * 40)
    with pytest.raises(ValueError, match='unreplaced scaffold content'):
        package_skill.build(generated, 'scaffold-probe')
    after = {str(p.relative_to(generated)): p.read_bytes() for p in generated.rglob('*') if p.is_file()}
    assert after == before


def test_versioned_package_refuses_script_placeholder_with_concrete_front_door(generated, monkeypatch):
    (generated / 'skills/scaffold-probe/SKILL.md').write_text(CONCRETE)
    monkeypatch.setattr(package_skill, 'source_revision', lambda root: 'a' * 40)
    with pytest.raises(ValueError, match='unreplaced scaffold content'):
        package_skill.build(generated, 'scaffold-probe')
    assert not (generated / 'dist').exists()


def test_development_package_remains_explicitly_unassessed(generated):
    result = package_skill.build_dev(generated, 'scaffold-probe')
    assert result['status'] == 'packaged-dev'
    assert result['runtime_acceptance'] == 'not_assessed'
    assert not (generated / 'dist/scaffold-probe/0.1.0').exists()


def test_concrete_minimal_front_door_is_not_a_model_qualification(generated, monkeypatch):
    mask_old_markers(generated)
    (generated / 'skills/scaffold-probe/SKILL.md').write_text(CONCRETE)
    assert plugin_release.content_errors(generated) == []
    monkeypatch.setattr(package_skill, 'source_revision', lambda root: 'a' * 40)
    result = package_skill.build(generated, 'scaffold-probe')
    assert result['runtime_acceptance'] == 'not_assessed'


@pytest.mark.parametrize('example', [
    '```text\nState what this skill owns in one paragraph\n```',
    '> State what this skill owns in one paragraph',
    'Avoid the template prompt `State what this skill owns in one paragraph`.',
])
def test_quoted_counterexample_is_not_an_unfinished_front_door(generated, monkeypatch, example):
    mask_old_markers(generated)
    (generated / 'skills/scaffold-probe/SKILL.md').write_text(CONCRETE + '\nBad template example:\n' + example + '\n')
    assert plugin_release.content_errors(generated) == []
    monkeypatch.setattr(package_skill, 'source_revision', lambda root: 'a' * 40)
    assert package_skill.build(generated, 'scaffold-probe')['runtime_acceptance'] == 'not_assessed'
