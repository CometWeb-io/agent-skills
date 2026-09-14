"""Real local Git fixtures; no connector writes, network, production or model calls."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import integration_preview as mod


def git(root, *args):
    env = dict(os.environ, GIT_AUTHOR_NAME='Fixture', GIT_AUTHOR_EMAIL='fixture@example.invalid',
               GIT_COMMITTER_NAME='Fixture', GIT_COMMITTER_EMAIL='fixture@example.invalid')
    return subprocess.run(['git', '-C', str(root), *args], env=env, check=True, capture_output=True).stdout.decode().strip()


def put(root, name, text):
    p=root/name;p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(text if isinstance(text, bytes) else text.encode());return p


@pytest.fixture
def setup(tmp_path):
    root=tmp_path/'checkout'; root.mkdir(); git(root,'init','-q')
    git(root,'config','core.filemode','true')
    put(root,'README.md','one\ntwo\nthree\nfour\nfive\nsix\nseven\neight\nnine\n')
    put(root,'.github/workflows/validate.yml','name: original\n')
    put(root,'LICENSE','Original license\n')
    put(root,'scripts/executable.py','#!/usr/bin/env python3\nprint("not executed")\n').chmod(0o755)
    git(root,'add','.');git(root,'commit','-qm','baseline')
    base=git(root,'rev-parse','HEAD')
    overlay=tmp_path/'overlay';overlay.mkdir()
    manifest=tmp_path/'manifest.json'
    def configure(files):
        for p in list(overlay.rglob('*')):
            if p.is_file():p.unlink()
        for n,v in files.items():put(overlay,n,v)
        data={'schema':'cometweb.overlay/v1','canonical_base':base,
              'files':{n:mod.digest((v if isinstance(v,bytes) else v.encode())) for n,v in files.items()}}
        manifest.write_bytes(mod.canonical(data));return data
    configure({'README.md':'ONE\ntwo\nthree\nfour\nfive\nsix\nseven\neight\nnine\n',
               'tooling/new.py':'print("not executed")\n'})
    return root, overlay, manifest, tmp_path/'preview', configure


def snap(root):
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file() and not p.is_symlink()}


def test_exact_base_preserves_git_and_all_unrelated_files(setup):
    root,over,manifest,out,_=setup;before=snap(root)
    report=mod.preview(root,over,manifest,out)
    assert report['status']=='prepared'
    assert snap(root)==before
    assert (out/'candidate/LICENSE').read_bytes()==(root/'LICENSE').read_bytes()
    assert os.access(out/'candidate/scripts/executable.py',os.X_OK)
    assert not (out/'candidate/.git').exists()
    assert report['full_repository_tests']=='not_run'
    assert report['remote_write_attempted'] is False


def test_newer_unrelated_edit_three_way_merged(setup):
    root,over,manifest,out,_=setup
    p=root/'README.md';p.write_text(p.read_text().replace('nine','NINE'))
    put(root,'upstream-only.txt','keep this')
    git(root,'add','.');git(root,'commit','-qm','newer changes')
    before=snap(root)
    report=mod.preview(root,over,manifest,out)
    assert report['status']=='prepared'
    text=(out/'candidate/README.md').read_text()
    assert text.startswith('ONE') and 'NINE' in text
    assert (out/'candidate/upstream-only.txt').read_text()=='keep this'
    assert snap(root)==before


def test_conflict_does_not_emit_installable_candidate(setup):
    root,over,manifest,out,_=setup
    p=root/'README.md';p.write_text(p.read_text().replace('one','OTHER'))
    git(root,'add','.');git(root,'commit','-qm','conflicting change')
    before=snap(root);report=mod.preview(root,over,manifest,out)
    assert report['status']=='conflicts' and report['conflicts']==['README.md']
    assert not (out/'candidate').exists()
    assert snap(root)==before


@pytest.mark.parametrize('include',[True,False])
def test_workflows_are_separately_opt_in(setup,include):
    root,over,manifest,out,configure=setup
    configure({'.github/workflows/validate.yml':'name: revised\n'})
    report=mod.preview(root,over,manifest,out,include_workflows=include)
    assert (out/'candidate/.github/workflows/validate.yml').read_text()==('name: revised\n' if include else 'name: original\n')
    assert bool(report['excluded_workflows']) is not include


def test_added_on_both_sides_cannot_overwrite_newer_file(setup):
    root,over,manifest,out,_=setup
    put(root,'tooling/new.py','newer independent code')
    git(root,'add','.');git(root,'commit','-qm','new file')
    report=mod.preview(root,over,manifest,out)
    assert report['status']=='conflicts' and report['conflicts']==['tooling/new.py']


def test_upstream_deletion_requires_reconciliation(setup):
    root,over,manifest,out,_=setup
    (root/'README.md').unlink();git(root,'add','.');git(root,'commit','-qm','delete')
    assert mod.preview(root,over,manifest,out)['status']=='conflicts'


def test_unchanged_overlay_does_not_resurrect_deleted_upstream(setup):
    root,over,manifest,out,configure=setup
    configure({'README.md':(root/'README.md').read_bytes()})
    (root/'README.md').unlink();git(root,'add','.');git(root,'commit','-qm','delete')
    assert mod.preview(root,over,manifest,out)['status']=='prepared'
    assert not (out/'candidate/README.md').exists()


@pytest.mark.parametrize('kind',['content','deleted','mode'])
def test_tracked_working_tree_changes_are_not_ignored(setup,kind):
    root,over,manifest,out,_=setup
    if kind=='content':(root/'LICENSE').write_text('working change')
    elif kind=='mode':(root/'LICENSE').chmod(0o755)
    else:(root/'LICENSE').unlink()
    before=snap(root)
    with pytest.raises(ValueError):mod.preview(root,over,manifest,out)
    assert not out.exists() and snap(root)==before


def test_untracked_files_not_exported(setup):
    root,over,manifest,out,_=setup
    put(root,'untracked-private.txt','local-only sentinel')
    report=mod.preview(root,over,manifest,out)
    assert report['untracked_files_not_exported']==1
    assert not (out/'candidate/untracked-private.txt').exists()


def test_modified_overlay_not_accepted(setup):
    root,over,manifest,out,_=setup;put(over,'README.md','tampered')
    with pytest.raises(ValueError):mod.preview(root,over,manifest,out)
    assert not out.exists()


def test_expected_manifest_pin(setup):
    root,over,manifest,out,_=setup
    with pytest.raises(ValueError):mod.preview(root,over,manifest,out,expected_manifest_sha256='0'*64)
    report=mod.preview(root,over,manifest,out,expected_manifest_sha256=mod.digest(manifest.read_bytes()))
    assert report['manifest_pin']=='matched'


@pytest.mark.parametrize('name',['../escape','/absolute','.git/config','x/.GiT/config','x\\y','a:b','a//b','x/./y','evil\npath','name.','dir /file'])
def test_unsafe_manifest_paths_rejected(setup,name):
    root,over,manifest,out,_=setup
    data=json.loads(manifest.read_text());data['files']={name:'a'*64};manifest.write_text(json.dumps(data))
    with pytest.raises(ValueError):mod.preview(root,over,manifest,out)
    assert not out.exists()


def test_output_must_be_new(setup):
    root,over,manifest,out,_=setup;out.mkdir();put(out,'keep.txt','keep')
    with pytest.raises(ValueError):mod.preview(root,over,manifest,out)
    assert (out/'keep.txt').read_text()=='keep'


@pytest.mark.parametrize('parent',['checkout','overlay'])
def test_output_cannot_overlap_sources(setup,parent):
    root,over,manifest,out,_=setup
    with pytest.raises(ValueError):mod.preview(root,over,manifest,(root if parent=='checkout' else over)/'out')


def test_overlay_symlink_rejected(setup):
    root,over,manifest,out,_=setup
    (over/'README.md').unlink();(over/'README.md').symlink_to(root/'README.md')
    with pytest.raises(ValueError):mod.preview(root,over,manifest,out)


def test_tracked_symlink_rejected(setup):
    root,over,manifest,out,_=setup
    (root/'linked').symlink_to('LICENSE');git(root,'add','.');git(root,'commit','-qm','symlink')
    with pytest.raises(ValueError):mod.preview(root,over,manifest,out)
    assert not out.exists()


def test_no_local_filter_execution_or_checkout_hook(setup):
    root,over,manifest,out,_=setup
    marker=root.parent/'hook-executed'
    # Local config intentionally dangerous; no filter/hook may run during preview.
    put(root,'.gitattributes','README.md filter=fixture\n')
    git(root,'add','.gitattributes');git(root,'commit','-qm','filter config')
    git(root,'config','filter.fixture.clean',f'touch {marker}')
    assert not marker.exists()
    put(root,'.git/hooks/post-checkout',f'#!/bin/sh\ntouch {marker}\n').chmod(0o755)
    mod.preview(root,over,manifest,out)
    assert not marker.exists()


def test_retired_skill_not_resurrected(setup):
    root,over,manifest,out,configure=setup
    configure({'skills/ai-antipattern-writing/SKILL.md':'retired content'})
    with pytest.raises(ValueError):mod.preview(root,over,manifest,out)
    assert not out.exists()


def test_binary_conflict_is_not_text_merged():
    status,value=mod.merge_file(b'new\0',b'base\0',b'other\0')
    assert status=='conflict_binary' and value is None


def test_duplicate_json_keys_rejected(setup):
    root,over,manifest,out,_=setup
    text=manifest.read_text().replace('"schema":','"schema": "duplicate", "schema":',1)
    manifest.write_text(text)
    with pytest.raises(ValueError):mod.preview(root,over,manifest,out)


def test_file_directory_collision_rejected(setup):
    root,over,manifest,out,configure=setup
    configure({'LICENSE/child.txt':'cannot be a directory'})
    with pytest.raises(ValueError):mod.preview(root,over,manifest,out)


def test_changed_head_stops_export(setup,monkeypatch):
    root,over,manifest,out,_=setup
    real_git=mod.git;reads=0
    def changing(path,*args):
        nonlocal reads
        if args==('rev-parse','HEAD'):
            reads+=1
            if reads==2:return b'a'*40+b'\n'
        return real_git(path,*args)
    monkeypatch.setattr(mod,'git',changing)
    with pytest.raises(ValueError):mod.preview(root,over,manifest,out)
    assert not out.exists()


def test_dotdot_output_cannot_hide_overlap_with_checkout(setup):
    root,over,manifest,out,_=setup
    other=root.parent/'other';other.mkdir()
    deceptive=other/'..'/'checkout'/'out'
    with pytest.raises(ValueError):mod.preview(root,over,manifest,deceptive)
    assert not (root/'out').exists()


def test_casefold_file_directory_collision_rejected(setup):
    root,over,manifest,out,configure=setup
    configure({'license/child.txt':'collides on case-insensitive filesystems'})
    with pytest.raises(ValueError):mod.preview(root,over,manifest,out)
    assert not out.exists()
