"""Experimental publication is explicit; structural checks cannot grant qualification."""
import copy
import json
import shutil
from pathlib import Path
import sys
import zipfile

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import package_skill
import plugin_release
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _tooling_fixtures import root, add  # noqa: F401


def metadata(**changes):
    value = {"schema": "cometweb.skill-maturity/v1", "skill": "demo", "version": "1.0.0",
             "stage": "DEVELOPMENT", "publication": "EXPERIMENTAL",
             "task_qualification": "not_established"}
    value.update(changes)
    return value


@pytest.mark.parametrize("stage", ["SCAFFOLD", "DEVELOPMENT", "CANDIDATE"])
def test_declared_stage_remains_experimental_and_unassessed(stage):
    value = metadata(stage=stage)
    assert plugin_release.validate_maturity(json.dumps(value).encode(), "demo", "1.0.0") == value


@pytest.mark.parametrize("changes", [
    {"stage": "QUALIFIED"}, {"stage": "READY"}, {"stage": True}, {"stage": []},
    {"publication": "STABLE"}, {"task_qualification": "passed"},
    {"skill": "other"}, {"version": "2.0.0"}, {"schema": "other"},
    {"all_hosts_verified": True},
])
def test_supplied_labels_cannot_grant_task_qualification(changes):
    with pytest.raises(ValueError):
        plugin_release.validate_maturity(json.dumps(metadata(**changes)).encode(), "demo", "1.0.0")


def test_duplicate_stage_cannot_hide_qualified_claim():
    raw = json.dumps(metadata()).replace('"stage": "DEVELOPMENT"', '"stage": "QUALIFIED", "stage": "DEVELOPMENT"')
    with pytest.raises(ValueError):
        plugin_release.validate_maturity(raw.encode(), "demo", "1.0.0")


@pytest.mark.parametrize("blob", [b"\xff", b"{", b" " * 4097, b"[]", b"null"])
def test_invalid_or_oversized_metadata_is_refused(blob):
    with pytest.raises(ValueError):
        plugin_release.validate_maturity(blob, "demo", "1.0.0")


@pytest.mark.parametrize("changes", [None, {"stage": "QUALIFIED"}, {"stage": "SCAFFOLD"},
                                        {"publication": "STABLE"}, {"skill": "other"}])
@pytest.mark.parametrize("existing", [False, True])
def test_versioned_build_refuses_unadmitted_maturity_without_writes(root, changes, existing):
    if existing:
        package_skill.build(root, "demo")
    path = root / "skills/demo/MATURITY.json"
    if changes is None:
        path.unlink(missing_ok=True)
    else:
        path.write_text(json.dumps(metadata(**changes)))
    before = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}
    with pytest.raises(ValueError, match="maturity|MATURITY|SCAFFOLD|QUALIFIED|EXPERIMENTAL"):
        package_skill.build(root, "demo")
    assert before == {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}


def test_full_plugin_gate_and_archive_use_same_maturity_contract(root):
    assert plugin_release.content_errors(root) == []
    entries, manifest = package_skill.payload(root, "demo")
    assert json.loads(entries["MATURITY.json"]) == metadata()
    assert set(manifest) == {"schema", "skill", "version", "policy_sha256", "files", "runtime_acceptance", "payload_sha256"}
    inspected = package_skill.inspect_archive(package_skill.archive(entries, manifest))
    assert "maturity" not in inspected
    assert inspected["files"]["MATURITY.json"] == package_skill.digest(entries["MATURITY.json"])
    entries = copy.deepcopy(entries)
    entries["MATURITY.json"] = json.dumps(metadata(stage="QUALIFIED")).encode()
    manifest["files"] = {n: package_skill.digest(b) for n, b in entries.items()}
    manifest["payload_sha256"] = package_skill.digest(package_skill.canonical({"files": manifest["files"], "policy_sha256": manifest["policy_sha256"]}))
    with pytest.raises(ValueError):
        package_skill.inspect_archive(package_skill.archive(entries, manifest))
    add(root, "MATURITY.json", entries["MATURITY.json"])
    assert plugin_release.content_errors(root)


def test_dev_scaffold_carries_explicit_unassessed_status(root):
    add(root, "MATURITY.json", json.dumps(metadata(stage="SCAFFOLD")).encode())
    result = package_skill.build_dev(root, "demo")
    manifest = package_skill.inspect_archive((root / result["path"]).read_bytes())
    assert "maturity" not in manifest
    with zipfile.ZipFile(root / result["path"]) as bundle:
        assert json.loads(bundle.read("MATURITY.json")) == metadata(stage="SCAFFOLD")
    assert result["runtime_acceptance"] == "not_assessed"
    assert result["maturity"] == metadata(stage="SCAFFOLD")


def test_legacy_archive_is_inspectable_but_cannot_be_reused_as_classified_release(root):
    entries, manifest = package_skill.payload(root, "demo")
    entries.pop("MATURITY.json", None)
    manifest.pop("maturity", None)
    manifest.update(source_revision="a" * 40, source_tree="clean")
    manifest["files"] = {n: package_skill.digest(b) for n, b in entries.items()}
    manifest["payload_sha256"] = package_skill.digest(package_skill.canonical({"files": manifest["files"], "policy_sha256": manifest["policy_sha256"]}))
    legacy = package_skill.archive(entries, manifest)
    assert "maturity" not in package_skill.inspect_archive(legacy)
    archive = root / "dist/demo/1.0.0/skill.zip"
    archive.parent.mkdir(parents=True)
    archive.write_bytes(legacy)
    with pytest.raises(ValueError, match="immutable version conflict"):
        package_skill.build(root, "demo")
    assert archive.read_bytes() == legacy


@pytest.mark.parametrize("variant", ["dev_archive", "dirty_checkout", "missing_git"])
def test_release_cache_requires_current_clean_source_and_archive_provenance(root, variant):
    if variant == "dev_archive":
        dev = package_skill.build_dev(root, "demo")
        target = root / "dist/demo/1.0.0/skill.zip"
        target.parent.mkdir(parents=True)
        shutil.copyfile(root / dev["path"], target)
    else:
        package_skill.build(root, "demo")
        if variant == "dirty_checkout":
            (root / ".gitignore").write_text("dist/\n# dirty checkout control\n")
        else:
            shutil.rmtree(root / ".git")
    before = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}
    with pytest.raises(ValueError):
        package_skill.build(root, "demo")
    assert before == {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}


def test_concurrent_cached_dev_archive_cannot_gain_versioned_provenance(root, monkeypatch):
    dev = package_skill.build_dev(root, "demo")
    unclassified = (root / dev["path"]).read_bytes()
    def planted_winner(path, data, *, immutable):
        assert immutable
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(unclassified)
        raise FileExistsError("synthetic concurrent winner")
    monkeypatch.setattr(package_skill, "write_atomic", planted_winner)
    with pytest.raises(ValueError, match="source provenance"):
        package_skill.build(root, "demo")
    assert (root / "dist/demo/1.0.0/skill.zip").read_bytes() == unclassified
    assert not (root / "dist/demo/skill.zip").exists()
    assert not (root / "dist/demo/1.0.0/skill.zip.sha256").exists()
