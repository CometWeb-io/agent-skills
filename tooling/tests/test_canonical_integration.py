"""Canonical layout regressions; synthetic package contents, no host or model runs."""
from pathlib import Path
import json
import sys
import pytest

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import generate_adapters as adapters
import package_skill as package
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _tooling_fixtures import root, add  # noqa: F401


@pytest.mark.parametrize('name', ['INSTALL.md', 'examples/strong-pl.md'])
def test_canonical_humanize_layout_is_admitted(root, name):
    add(root, name, b'# Synthetic package-layout fixture\n')
    entries, manifest = package.payload(root, 'demo')
    assert name in entries and name in manifest['files']
    assert manifest['runtime_acceptance'] == 'not_assessed'


def wire(root, monkeypatch):
    for key, path in {'ROOT':root, 'SKILLS':root/'skills', 'REGISTRY':root/'registry/skills.json',
                      'OUT_DOCS':root/'docs/table.md', 'OUT_CURSOR':root/'docs/cursor.mdc'}.items():
        monkeypatch.setattr(adapters, key, path)
    monkeypatch.setattr(sys, 'argv', ['generate_adapters.py'])


@pytest.mark.parametrize('defect', ['missing_skill', 'missing_version', 'version_drift', 'duplicate', 'bad_id', 'source_symlink', 'metadata_symlink'])
def test_generator_requires_complete_sources_before_writing(root, monkeypatch, defect):
    wire(root, monkeypatch)
    registry_path=root/'registry/skills.json'
    registry=json.loads(registry_path.read_text())
    if defect == 'missing_skill':
        registry['skills'].append({'id':'absent','version':'1.0.0'})
    elif defect == 'missing_version':
        (root/'skills/demo/VERSION').unlink()
    elif defect == 'version_drift':
        (root/'skills/demo/VERSION').write_text('1.1.0\n')
    elif defect == 'duplicate':
        registry['skills'].append(dict(registry['skills'][0]))
    elif defect == 'bad_id':
        registry['skills'][0]['id']='../escaped'
    elif defect == 'source_symlink':
        (root/'skills/demo/SKILL.md').rename(root/'original.md')
        (root/'skills/demo/SKILL.md').symlink_to(root/'original.md')
    elif defect == 'metadata_symlink':
        (root/'outside').mkdir()
        (root/'skills/demo/agents').symlink_to(root/'outside',target_is_directory=True)
    registry_path.write_text(json.dumps(registry))
    before={p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}
    with pytest.raises(SystemExit):
        adapters.main()
    after={p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}
    assert before == after
    assert not (root/'skills/absent').exists()
    assert not (root/'docs').exists()


def test_complete_sources_allow_generation_and_clean_check(root, monkeypatch):
    wire(root, monkeypatch)
    adapters.main()
    assert (root/'skills/demo/agents/openai.yaml').is_file()
    before={p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}
    monkeypatch.setattr(sys,'argv',['generate_adapters.py','--check'])
    adapters.main()
    assert before=={p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}


def test_candidate_registry_version_and_generated_table_are_consistent():
    registry=json.loads((TOOLS.parent/'registry/skills.json').read_text())
    humanize=next(s for s in registry['skills'] if s['id']=='ai-humanize')
    # The point is that registry and package agree, not which release it is; a
    # hard-coded version turns every legitimate bump into a failing test.
    assert humanize['version']==(TOOLS.parent/'skills/ai-humanize/VERSION').read_text().strip()
    assert (TOOLS.parent/'docs/generated-skills-table.md').read_text()==adapters.build_docs(registry['skills'])
