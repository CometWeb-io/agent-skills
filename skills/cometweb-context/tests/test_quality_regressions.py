import importlib.util
import json
import subprocess
from pathlib import Path
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _context_fixtures import load_script, build_valid_envelope as valid_envelope

planner = load_script("context_plan")
validator = load_script("validate_context_envelope")
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("snapshot_quality", ROOT / "scripts/repo_snapshot.py")
snap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(snap)

@pytest.mark.parametrize("value", ["2026-09-07", "2026-09-07T00:00:00", "nonsense", 123])
def test_timestamps_need_explicit_timezone(value):
    d = valid_envelope()
    d["generated_at"] = value
    with pytest.raises(ValueError): validator.validate(d)

@pytest.mark.parametrize("field", ["summary", "evidence_ref"])
def test_empty_provenance_rejected(field):
    d = valid_envelope()
    d["sources"][0][field] = " "
    with pytest.raises(ValueError): validator.validate(d)

def test_empty_statement_rejected():
    d = valid_envelope(); d["facts"][0]["statement"] = ""
    with pytest.raises(ValueError): validator.validate(d)

def test_future_retrieval_rejected():
    d = valid_envelope(); d["sources"][0]["retrieved_at"] = "2026-09-08T00:00:00Z"
    with pytest.raises(ValueError): validator.validate(d)

def test_available_baseline_requires_reference():
    d = valid_envelope(); d["baseline"] = {"status": "available", "ref": None}
    with pytest.raises(ValueError): validator.validate(d)

def test_nonempty_deltas_need_baseline():
    d = valid_envelope(); d["deltas"] = [{"claim": "changed"}]
    with pytest.raises(ValueError): validator.validate(d)

@pytest.mark.parametrize("field", ["mode", "profile"])
def test_bad_enum_is_validation_error(field):
    d = valid_envelope(); d[field] = []
    with pytest.raises(ValueError): validator.validate(d)

@pytest.mark.parametrize("refs", [[[]], [None], ["src-1", "src-1"]])
def test_bad_fact_references(refs):
    d = valid_envelope(); d["facts"][0]["source_ids"] = refs
    with pytest.raises(ValueError): validator.validate(d)

@pytest.mark.parametrize("rel", ["../outside", "/tmp/private", "a/../../outside"])
def test_snapshot_refuses_path_escape(tmp_path, rel):
    assert snap.snapshot(tmp_path, rel)["status"] == "invalid_path"

def test_snapshot_refuses_symlink_escape(tmp_path):
    root = tmp_path / "root"; root.mkdir()
    outside = tmp_path / "outside"; outside.mkdir()
    (root / "linked").symlink_to(outside, target_is_directory=True)
    assert snap.snapshot(root, "linked")["status"] == "invalid_path"

def test_snapshot_cannot_mistake_parent_git_repo(tmp_path):
    repo = tmp_path / "project"; repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    (repo / "nested").mkdir()
    assert snap.snapshot(tmp_path, "project/nested")["status"] == "not_repo_root"

def test_error_does_not_leak_private_path(tmp_path):
    (tmp_path / "empty").mkdir()
    value = snap.snapshot(tmp_path, "empty")
    assert str(tmp_path) not in json.dumps(value)

def test_snapshot_does_not_execute_repo_fsmonitor_hook(tmp_path):
    repo=tmp_path/"repo";repo.mkdir()
    def git(*args):
        subprocess.run(["git","-C",str(repo),*args],check=True,capture_output=True,text=True)
    git("init","-q")
    (repo/"file").write_text("example")
    git("add","file")
    git("-c","user.name=Test","-c","user.email=test@example.invalid","commit","-qm","fixture")
    marker=tmp_path/"hook-was-executed"
    hook=tmp_path/"fsmonitor.sh"
    hook.write_text(f"#!/bin/sh\ntouch '{marker}'\n")
    hook.chmod(0o755)
    git("config","core.fsmonitor",str(hook))
    result=snap.snapshot(tmp_path,"repo")
    assert result["status"]=="ok"
    assert not marker.exists()
