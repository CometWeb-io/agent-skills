"""Adversarial package paths and receipt binding; synthetic bytes are not attestations."""
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _tooling_fixtures import root, add  # noqa: F401
import installation_acceptance as acceptance
import package_skill as package


def rehashed(entries, manifest):
    manifest["files"] = {name: package.digest(data) for name, data in entries.items()}
    manifest["payload_sha256"] = package.digest(package.canonical({
        "files": manifest["files"], "policy_sha256": manifest["policy_sha256"]}))
    return package.archive(entries, manifest)


@pytest.mark.parametrize("name", [
    "scripts/run_evals.py.", "scripts/run_evals.py ",
    "scripts/run_evals?.py", "scripts/run_evals*.py", "scripts/run_evals|.py",
    'scripts/run_evals".py', "scripts/run_evals<.py", "scripts/run_evals>.py",
    "scripts/CON", "scripts/aux.txt", "references/NUL.json", "references/com1.txt",
    "references/LPT9.md", "references/CON .txt",
])
def test_zip_names_that_windows_changes_or_treats_as_devices_are_refused(root, name):
    entries, manifest = package.payload(root, "demo")
    entries["scripts/run_evals.py"] = b"raise SystemExit(0)\n"
    entries[name] = b"raise SystemExit(7)\n"
    with pytest.raises(ValueError, match="nonportable|unsafe"):
        package.inspect_archive(rehashed(entries, manifest))


@pytest.mark.skipif(os.name == "nt", reason="Windows normalizes the filename before packaging can inspect it")
def test_source_payload_also_refuses_windows_extraction_aliases(root):
    add(root, "scripts/run_evals.py.", b"raise SystemExit(7)\n")
    with pytest.raises(ValueError, match="nonportable|unsafe"):
        package.payload(root, "demo")


@pytest.mark.parametrize("parent", ["references", "References"])
def test_archive_cannot_use_a_file_as_another_members_directory(root, parent):
    entries, manifest = package.payload(root, "demo")
    entries[parent] = b"This is a file, not a directory.\n"
    entries["references/child.txt"] = b"Cannot be extracted below a file.\n"
    with pytest.raises(ValueError, match="path|inventory"):
        package.inspect_archive(rehashed(entries, manifest))


@pytest.mark.parametrize("alias", [b"../outside\n", b"/outside\n", b"demo\n", b"", b"other\nsecond\n",
                                 b" canonical-skill\n", b"canonical-skill \n"])
def test_archive_rejects_malformed_or_self_referential_alias_edges(root, alias):
    entries, manifest = package.payload(root, "demo")
    entries["ALIAS_OF"] = alias
    with pytest.raises(ValueError, match="alias|identifier"):
        package.inspect_archive(rehashed(entries, manifest))


def test_valid_alias_declaration_is_structural_not_dependency_installation(root):
    entries, manifest = package.payload(root, "demo")
    entries["ALIAS_OF"] = b"canonical-skill\n"
    actual = package.inspect_archive(rehashed(entries, manifest))
    assert actual["runtime_acceptance"] == "not_assessed"
    assert actual["files"]["ALIAS_OF"] == package.digest(entries["ALIAS_OF"])


def test_source_payload_also_refuses_self_referential_alias(root):
    add(root, "ALIAS_OF", b"demo\n")
    with pytest.raises(ValueError, match="alias"):
        package.payload(root, "demo")


@pytest.mark.parametrize("tamper", ["payload", "archive", "version", "identity", "path", "symlink", "content", "source-policy"])
def test_install_acceptance_binds_receipt_to_the_actual_archive_before_extraction(root, monkeypatch, tamper):
    entries, manifest = package.payload(root, "demo")
    if tamper == "identity":
        entries["SKILL.md"] = entries["SKILL.md"].replace(b"name: demo", b"name: other")
        entries["MATURITY.json"] = entries["MATURITY.json"].replace(b'"demo"', b'"other"')
        manifest["skill"] = "other"
    elif tamper == "content":
        entries["scripts/extra.py"] = b"raise SystemExit(7)\n"
    elif tamper == "source-policy":
        manifest["policy_sha256"] = "0" * 64
    blob = rehashed(entries, manifest)
    archive = root / "dist/demo/1.0.0/skill.zip"
    archive.parent.mkdir(parents=True)
    archive.write_bytes(blob)
    report = {"status": "packaged", "skill": "demo", "version": "1.0.0",
              "payload_sha256": manifest["payload_sha256"], "archive_sha256": package.digest(blob),
              "path": archive.relative_to(root).as_posix()}
    if tamper in {"payload", "archive"}:
        report[tamper + "_sha256"] = "0" * 64
    elif tamper == "version":
        report["version"] = "9.9.9"
    elif tamper in {"path", "symlink"}:
        outside = root.parent / "outside.zip"
        outside.write_bytes(blob)
        if tamper == "path":
            report["path"] = "../outside.zip"
        else:
            archive.unlink()
            archive.symlink_to(outside)
    monkeypatch.setattr(acceptance.subprocess, "run", lambda *a, **kw: SimpleNamespace(
        returncode=0, stdout=json.dumps(report), stderr=""))
    work = root / "acceptance-work"
    with pytest.raises(ValueError):
        acceptance.accept_staged(root, root, "demo", work)
    assert not (work / "install/demo").exists()


def test_matching_synthetic_receipt_never_claims_host_acceptance_or_signed_provenance(root, monkeypatch):
    entries, manifest = package.payload(root, "demo")
    blob = package.archive(entries, manifest)
    archive = root / "dist/demo/1.0.0/skill.zip"
    archive.parent.mkdir(parents=True)
    archive.write_bytes(blob)
    report = {"status": "packaged", "skill": "demo", "version": manifest["version"],
              "payload_sha256": manifest["payload_sha256"], "archive_sha256": package.digest(blob),
              "path": archive.relative_to(root).as_posix()}
    monkeypatch.setattr(acceptance.subprocess, "run", lambda *a, **kw: SimpleNamespace(
        returncode=0, stdout=json.dumps(report), stderr=""))
    result = acceptance.accept_staged(root, root, "demo", root / "acceptance-work")
    assert result["status"] == "passed"
    assert result["payload_sha256"] == manifest["payload_sha256"]
    assert result["archive_sha256"] == package.digest(blob)
    assert result["verified_runtime_acceptance"] == result["host_acceptance"] == "not_assessed"
    assert result["dependency_acceptance"]["status"] == "not_required"
    assert result["dependency_acceptance"]["packages"] == []


@pytest.fixture(scope="module")
def staged_alias_repository(tmp_path_factory):
    return acceptance.stage_fixture(acceptance.ROOT, tmp_path_factory.mktemp("real-alias-packages"))


@pytest.mark.parametrize("alias,canonical", [
    ("content-roaster", "content-reviewer"),
    ("skill-orchestrator-multiagent", "skill-orchestrator"),
])
def test_real_alias_acceptance_requires_the_adjacent_canonical_package(staged_alias_repository, tmp_path, alias, canonical):
    result = acceptance.accept_staged(acceptance.ROOT, staged_alias_repository, alias, tmp_path, run_helpers=True)
    assert result["status"] == result["installation_acceptance"] == "passed", result
    assert (tmp_path / "install" / canonical / "SKILL.md").is_file()
    assert (tmp_path / "install" / alias / "ALIAS_OF").read_text().strip() == canonical
    assert result["installation_scope"] == "package_and_alias_dependency_extraction"
    dependencies = result["dependency_acceptance"]
    assert dependencies["status"] == "passed"
    assert dependencies["required_skills"] == [canonical]
    assert [row["skill"] for row in dependencies["packages"]] == [canonical]
    assert all(row["status"] == "passed" and row["archive_sha256"] for row in dependencies["packages"])
    assert result["verified_runtime_acceptance"] == result["host_acceptance"] == "not_assessed"


@pytest.mark.parametrize("failure", ["missing", "cycle"])
def test_invalid_dependency_closure_fails_before_building_or_extracting(root, monkeypatch, failure):
    add(root, "ALIAS_OF", b"missing\n" if failure == "missing" else b"second\n")
    if failure == "cycle":
        second = root / "skills/second"
        second.mkdir()
        (second / "SKILL.md").write_text("synthetic source dependency")
        (second / "ALIAS_OF").write_text("demo\n")
    monkeypatch.setattr(acceptance.subprocess, "run", lambda *a, **kw: pytest.fail("must preflight the closure"))
    work = root / "acceptance-work"
    result = acceptance.accept_staged(root, root, "demo", work)
    assert result["status"] == "dependency_failed", result
    assert result["installation_acceptance"] == "failed"
    assert result["dependency_acceptance"]["status"] == "failed"
    assert failure in result["dependency_acceptance"]["detail"]
    assert not (work / "install").exists()


def test_alias_cannot_pass_if_the_extracted_canonical_is_missing(staged_alias_repository, tmp_path, monkeypatch):
    original = acceptance._accept_package

    def remove_canonical(*args, **kwargs):
        result = original(*args, **kwargs)
        if args[2] == "content-roaster":
            (tmp_path / "install/content-reviewer/SKILL.md").unlink()
        return result

    monkeypatch.setattr(acceptance, "_accept_package", remove_canonical)
    result = acceptance.accept_staged(acceptance.ROOT, staged_alias_repository, "content-roaster", tmp_path)
    assert result["status"] == "dependency_failed"
    assert result["installation_acceptance"] == "failed"
    assert "missing" in result["dependency_acceptance"]["detail"]


def test_failed_canonical_package_does_not_build_the_alias(root, monkeypatch):
    add(root, "ALIAS_OF", b"canonical\n")
    canonical = root / "skills/canonical"
    canonical.mkdir()
    (canonical / "SKILL.md").write_text("synthetic source dependency")
    called = []

    def fail_canonical(root, package_root, skill, work, **kwargs):
        called.append(skill)
        return {"skill": skill, "status": "package_failed", "detail": "synthetic builder refusal"}

    monkeypatch.setattr(acceptance, "_accept_package", fail_canonical)
    result = acceptance.accept_staged(root, root, "demo", root / "acceptance-work")
    assert result["status"] == "dependency_failed"
    assert result["installation_acceptance"] == "failed"
    assert called == ["canonical"]
