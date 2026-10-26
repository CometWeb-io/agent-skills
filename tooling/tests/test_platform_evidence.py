"""Synthetic receipts test rejection rules; they are not native execution proof."""
from __future__ import annotations

import copy
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest

import platform_evidence as pe

SPEC = importlib.util.spec_from_file_location("platform_local_tests", Path(__file__).parents[1] / "validate_local.py")
local = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(local)
CLASS = "tooling.tests.test_windows_portability"
NAME = "test_windows_scanner_checks_handle_containment_and_junctions[repo-roaster]"
CASE_ID = CLASS + "::" + NAME


def xml(inner="", *, name=NAME, cls=CLASS):
    return f'<testsuite><testcase classname="{cls}" name="{name}">{inner}</testcase></testsuite>'.encode()


def state():
    return {"revision": "a" * 40, "dirty": False, "files": {"tooling/example.py": {"sha256": "b" * 64}}}


def manifest(junit):
    try:
        ids = [c.get("classname", "") + "::" + c.get("name", "") for c in pe.ET.fromstring(junit).iter("testcase")]
    except pe.ET.ParseError:
        ids = [CASE_ID]
    return json.dumps({"schema": "cometweb.pytest-collection/v1", "collected": ids, "selected": ids}).encode()


def local_report(output, junit):
    (output / "junit.xml").write_bytes(junit)
    (output / "collection.json").write_bytes(manifest(junit))


def archive(junit=None, change=None, extra=None, collection=None):
    junit = junit if junit is not None else xml()
    collection = collection if collection is not None else manifest(junit)
    receipt = {"schema": pe.SCHEMA, "status": "passed", "revision": state()["revision"],
               "content_fingerprint": pe.content_fingerprint(state()), "junit_sha256": pe.digest(junit),
               "collection_sha256": pe.digest(collection),
               "platform": "win32", "runner_os": "Windows", "python_minor": f"{sys.version_info.major}.{sys.version_info.minor}",
               "repository": pe.REPOSITORY, "run_id": 1, "run_attempt": 1}
    if change:
        receipt.update(change)
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        for name, data in {"receipt.json": json.dumps(receipt), "collection.json": collection, "junit.xml": junit,
                           "test.log": "synthetic pytest output", **(extra or {})}.items():
            z.writestr(name, data)
    return out.getvalue()


def metadata(blob):
    minor = f"{sys.version_info.major}.{sys.version_info.minor}"
    run = {"id": 1, "head_sha": state()["revision"], "run_attempt": 1, "status": "completed",
           "conclusion": "success", "path": ".github/workflows/platform-matrix.yml",
           "repository": {"full_name": pe.REPOSITORY}}
    artifact = {"id": 2, "name": f"native-tests-windows-latest-py{minor}-attempt-1", "size_in_bytes": len(blob),
                "expired": False, "digest": "sha256:" + pe.digest(blob),
                "workflow_run": {"id": 1, "head_sha": state()["revision"]}}
    job = {"id": 3, "name": f"windows-latest / py{minor}", "labels": ["windows-latest"], "conclusion": "success",
           "status": "completed", "run_id": 1, "run_attempt": 1, "head_sha": state()["revision"],
           "runner_group_id": 0, "runner_group_name": "GitHub Actions",
           "steps": [{"name": n, "conclusion": "success"} for n in
                     ["Collect native platform evidence", "Upload native platform evidence"]]}
    return run, artifact, job


def provider(monkeypatch, blob=None, *, mutate_run=None, mutate_artifact=None, mutate_job=None):
    blob = blob or archive()
    run, artifact, job = metadata(blob)
    for change, data in [(mutate_run, run), (mutate_artifact, artifact), (mutate_job, job)]:
        if change:
            change(data)
    def api(path):
        return copy.deepcopy({"actions/runs/1": run,
                              "actions/runs/1/artifacts?per_page=100": {"total_count": 1, "artifacts": [artifact]},
                              "actions/runs/1/jobs?per_page=100": {"total_count": 1, "jobs": [job]}}[path])
    monkeypatch.setattr(pe, "json_api", api)
    monkeypatch.setattr(pe, "gh_api", lambda path: blob if path == "actions/artifacts/2/zip" else pytest.fail(path))
    return artifact


def test_verified_provider_artifact_preserves_receipt_and_exact_case(monkeypatch, tmp_path):
    provider(monkeypatch)
    evidence = pe.fetch_evidence(1, state(), tmp_path)
    assert evidence[0]["cases"] == [CASE_ID]
    assert (tmp_path / "platform-1-2.zip").is_file()
    assert json.loads((tmp_path / "platform-1-2-metadata.json").read_text())["job"]["id"] == 3


@pytest.mark.parametrize("field,value", [("revision", "c" * 40), ("content_fingerprint", "c" * 64),
    ("junit_sha256", "c" * 64), ("status", "verified"), ("schema", "unknown"), ("run_id", 2),
    ("run_attempt", 2), ("run_id", True), ("run_attempt", True), ("python_minor", 3.12),
    ("repository", "elsewhere/repo"), ("platform", "linux"),
    ("platform", []), ("runner_os", "Linux")])
def test_receipt_claims_cannot_override_source_or_platform_binding(field, value):
    blob = archive(change={field: value})
    run, artifact, _ = metadata(blob)
    with pytest.raises(ValueError):
        pe.verify_archive(blob, artifact, run, state())


@pytest.mark.parametrize("change", [lambda a: a.update(expired=True), lambda a: a.update(digest="sha256:" + "0" * 64),
    lambda a: a["workflow_run"].update(head_sha="d" * 40), lambda a: a["workflow_run"].update(id=2)])
def test_bad_expired_or_replayed_archives_are_refused(change):
    blob = archive(); run, artifact, _ = metadata(blob); change(artifact)
    with pytest.raises(ValueError):
        pe.verify_archive(blob, artifact, run, state())


@pytest.mark.parametrize("outcome", ['<failure/>', '<error/>', '<skipped/>', '<skipped type="pytest.xfail"/>'])
def test_native_receipt_requires_execution_pass_not_a_green_summary(outcome):
    blob = archive(xml(outcome)); run, artifact, _ = metadata(blob)
    with pytest.raises(ValueError):
        pe.verify_archive(blob, artifact, run, state())


@pytest.mark.parametrize("junit", [xml(name="unrelated_test"), b'<testsuite/>',
    b'<testsuite><testcase/></testsuite>', xml().replace(b'</testsuite>', xml()[len(b'<testsuite>'):]),
    b'<!DOCTYPE testsuite [<!ENTITY x "test">]><testsuite><testcase name="&x;"/></testsuite>',
    '<!DOCTYPE testsuite><testsuite/>'.encode('utf-16')])
def test_missing_unrelated_duplicate_or_unsafe_xml_is_refused(junit):
    blob = archive(junit); run, artifact, _ = metadata(blob)
    with pytest.raises((ValueError, pe.ET.ParseError)):
        pe.verify_archive(blob, artifact, run, state())


def test_zip_paths_are_never_extracted(tmp_path):
    blob = archive(extra={"../outside": "untrusted"});run, artifact, _ = metadata(blob)
    with pytest.raises(ValueError):
        pe.verify_archive(blob, artifact, run, state())
    assert not (tmp_path.parent / "outside").exists()


@pytest.mark.parametrize("change", [lambda r: r.update(head_sha="e" * 40), lambda r: r.update(conclusion="failure"),
    lambda r: r.update(status="in_progress"), lambda r: r.update(path=".github/workflows/unknown.yml"),
    lambda r: r["repository"].update(full_name="foreign/repo"), lambda r: r.update(run_attempt=2)])
def test_wrong_provider_run_never_qualifies(monkeypatch, tmp_path, change):
    provider(monkeypatch, mutate_run=change)
    with pytest.raises(ValueError):
        pe.fetch_evidence(1, state(), tmp_path)


@pytest.mark.parametrize("change", [lambda j: j.update(labels=["ubuntu-latest"]),
    lambda j: j.update(conclusion="failure"), lambda j: j["steps"][0].update(conclusion="failure"),
    lambda j: j["steps"][1].update(conclusion="skipped")])
def test_provider_requires_a_successful_native_producer_job(monkeypatch, tmp_path, change):
    provider(monkeypatch, mutate_job=change)
    with pytest.raises(ValueError):
        pe.fetch_evidence(1, state(), tmp_path)


def test_dirty_source_cannot_borrow_a_committed_native_pass():
    blob=archive();run,artifact,_=metadata(blob)
    with pytest.raises(ValueError):
        pe.verify_archive(blob, artifact, run, {**state(), "dirty": True})


def test_skip_policy_does_not_trust_reason_text_or_waive_local_capability():
    known = pe.cases_from_xml(xml('<skipped message="native Windows"/>'))
    assert pe.classify_skips(known, "darwin")[0]["coverage"] == "platform_evidence_required"
    assert pe.classify_skips(known, "win32")[0]["coverage"] == "environment_blocked"
    unknown = pe.cases_from_xml(xml('<skipped message="native Windows"/>', name="unregistered"))
    assert pe.classify_skips(unknown, "darwin")[0]["coverage"] == "environment_blocked"
    xfail = pe.cases_from_xml(xml('<skipped type="pytest.xfail"/>'))
    assert pe.classify_skips(xfail, "darwin")[0]["coverage"] == "environment_blocked"
    suid = pe.cases_from_xml(xml('<skipped/>', cls="tooling.tests.test_snapshot_installer", name="test_cached_snapshot_tamper_fails_even_if_manifest_is_rewritten[special_permission]"))
    assert pe.classify_skips(suid, "darwin")[0]["coverage"] == "environment_blocked"


def test_join_keeps_local_skip_and_records_verified_external_pass(monkeypatch, tmp_path):
    provider(monkeypatch)
    monkeypatch.setattr(local.sys, "platform", "darwin")
    local_report(tmp_path, xml('<skipped/>'))
    result = local.assess_tests(tmp_path, state(), (1,))
    assert result["status"] == "passed_with_platform_evidence"
    assert result["junit"]["skipped"] == 1
    assert result["skipped_tests"][0]["coverage"] == "verified_on_native_platform"


def test_missing_case_cannot_be_replaced_by_another_test(monkeypatch, tmp_path):
    provider(monkeypatch, archive(xml(name=NAME.replace('repo-roaster', 'science-roaster'))))
    monkeypatch.setattr(local.sys, "platform", "darwin")
    local_report(tmp_path, xml('<skipped/>'))
    result = local.assess_tests(tmp_path, state(), (1,))
    assert result["status"] == "platform_evidence_required"


def test_failure_is_not_rescued_by_external_pass(monkeypatch, tmp_path):
    monkeypatch.setattr(pe, "fetch_evidence", lambda *a: pytest.fail("must not mask local failure"))
    local_report(tmp_path, xml('<failure/>'))
    assert local.assess_tests(tmp_path, state(), (1,))["status"] == "failed"


def test_no_authentication_or_network_error_is_a_failure_to_verify(monkeypatch, tmp_path):
    monkeypatch.setattr(pe, "gh_api", lambda *a: (_ for _ in ()).throw(ValueError("GitHub unavailable")))
    monkeypatch.setattr(local.sys, "platform", "darwin")
    local_report(tmp_path, xml('<skipped/>'))
    result = local.assess_tests(tmp_path, state(), (1,))
    assert result["status"] == "invalid_platform_evidence"


def test_proof_for_another_python_version_does_not_close_the_gap(monkeypatch, tmp_path):
    provider(monkeypatch)
    real_fetch = pe.fetch_evidence
    def another_python(*args):
        proof = real_fetch(*args)
        proof[0]["python_minor"] = "3.99"
        return proof
    monkeypatch.setattr(pe, "fetch_evidence", another_python)
    monkeypatch.setattr(local.sys, "platform", "darwin")
    local_report(tmp_path, xml('<skipped/>'))
    assert local.assess_tests(tmp_path, state(), (1,))["status"] == "platform_evidence_required"


@pytest.mark.parametrize("native,xfail,name", [(True, False, NAME), (False, True, NAME), (False, False, "unknown")])
def test_remote_pass_cannot_waive_local_or_unregistered_skips(monkeypatch, tmp_path, native, xfail, name):
    provider(monkeypatch)
    monkeypatch.setattr(local.sys, "platform", "win32" if native else "darwin")
    local_report(tmp_path, xml('<skipped type="pytest.xfail"/>' if xfail else '<skipped/>', name=name))
    assert local.assess_tests(tmp_path, state(), (1,))["status"] == "incomplete"


@pytest.mark.parametrize("body,expected", [("assert True", 0), ("import pytest; pytest.skip('capability missing')", 1),
                                         ("assert False", 1)])
def test_real_collector_records_actual_execution_and_never_turns_skip_into_pass(tmp_path, monkeypatch, body, expected):
    root = tmp_path / "source"
    test = root / "tests/test_native.py"
    test.parent.mkdir(parents=True)
    # Exercise Windows CRLF with the same normalization policy as the real repo.
    test.write_bytes(("def test_native():\r\n    " + body + "\r\n").encode())
    (root / ".gitattributes").write_bytes((Path(__file__).parents[2] / ".gitattributes").read_bytes())
    plugin = root / "tooling/pytest_inventory.py"
    plugin.parent.mkdir()
    plugin.write_bytes((Path(__file__).parents[1] / "pytest_inventory.py").read_bytes())
    (root / ".gitignore").write_text("__pycache__/\n.pytest_cache/\n")
    for command in (["init", "-q"], ["add", "."], ["-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                    "-c", "core.hooksPath=/dev/null", "commit", "-qm", "synthetic native collector"]):
        subprocess.run(["git", "-C", str(root), *command], check=True, capture_output=True)
    assert local.source_state(root)["dirty"] is False
    monkeypatch.setattr(pe, "REQUIREMENTS", {"tests/test_native.py::test_native": (sys.platform,)})
    out = tmp_path / "evidence"
    assert pe.collect(root, out) == expected
    receipt = json.loads((out / "receipt.json").read_text())
    assert receipt["status"] == ("passed" if expected == 0 else "failed")
    assert receipt["junit_sha256"] == pe.digest((out / "junit.xml").read_bytes())
    assert receipt["platform"] == sys.platform


def test_repository_workflow_produces_head_bound_evidence_with_pinned_upload():
    import yaml
    workflow = yaml.safe_load((Path(__file__).parents[2] / ".github/workflows/platform-matrix.yml").read_text())
    steps = workflow["jobs"]["portable-tooling"]["steps"]
    checkout = next(s for s in steps if s.get("uses", "").startswith("actions/checkout@"))
    assert checkout["with"]["ref"] == "${{ github.event.pull_request.head.sha || github.sha }}"
    collect = next(s for s in steps if s.get("name") == "Collect native platform evidence")
    assert "--trusted-checkout" in collect["run"]
    assert collect["shell"] == "bash"
    upload = next(s for s in steps if s.get("name") == "Upload native platform evidence")
    assert upload["uses"] == "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a"
    assert "github.run_attempt" in upload["with"]["name"]


@pytest.mark.parametrize("junit", [xml('<failure xmlns="urn:other"/>'), xml('<disabled/>'),
    xml().replace(b'<testcase ', b'<testcase status="notrun" '),
    xml().replace(b'<testcase ', b'<testcase disabled="true" '),
    xml().replace(b'<testsuite>', b'<testsuite failures="1">'),
    xml().replace(b'<testsuite>', b'<testsuite disabled="1">'),
    xml().replace(b'<testsuite>', b'<testsuite errors="1"><error message="runner failed"/>')])
def test_unknown_or_suite_level_outcomes_cannot_be_native_pass(junit):
    blob = archive(junit); run, artifact, _ = metadata(blob)
    with pytest.raises(ValueError):
        pe.verify_archive(blob, artifact, run, state())


@pytest.mark.parametrize("change", [lambda j: j.update(run_id=99), lambda j: j.update(run_attempt=99),
    lambda j: j.update(head_sha="f" * 40), lambda j: j.update(status="in_progress"),
    lambda j: j.update(labels=["windows-latest", "self-hosted"], runner_group_id=1, runner_group_name="Default"),
    lambda j: j["steps"].append({"name": "Run tests", "conclusion": "failure"})])
def test_stale_or_self_hosted_or_partly_failed_job_is_not_native_proof(monkeypatch, tmp_path, change):
    provider(monkeypatch, mutate_job=change)
    with pytest.raises(ValueError):
        pe.fetch_evidence(1, state(), tmp_path)


@pytest.mark.parametrize("collection", [
    {"collected": [CASE_ID, "tests.extra::test_missing"], "selected": [CASE_ID, "tests.extra::test_missing"]},
    {"collected": [CASE_ID, "tests.extra::test_deselected"], "selected": [CASE_ID]},
    {"collected": [CASE_ID, CASE_ID], "selected": [CASE_ID, CASE_ID]},
    {"collected": [], "selected": []}, {"collected": [CASE_ID], "selected": None}])
def test_partial_or_filtered_or_duplicate_collection_is_not_native_pass(collection):
    blob = archive(collection=json.dumps({"schema": "cometweb.pytest-collection/v1", **collection}).encode())
    run, artifact, _ = metadata(blob)
    with pytest.raises(ValueError, match="full unfiltered collection"):
        pe.verify_archive(blob, artifact, run, state())


def test_manifest_hash_cannot_be_replaced_by_matching_case_names():
    blob = archive(change={"collection_sha256": "f" * 64}); run, artifact, _ = metadata(blob)
    with pytest.raises(ValueError, match="binding mismatch"):
        pe.verify_archive(blob, artifact, run, state())


@pytest.mark.parametrize("missing", [True, False])
def test_local_green_partial_report_cannot_bypass_collection(tmp_path, missing):
    local_report(tmp_path, xml())
    if missing:
        (tmp_path / "collection.json").unlink()
    else:
        data = json.loads((tmp_path / "collection.json").read_text())
        data["collected"].append("tests.extra::test_missing")
        data["selected"].append("tests.extra::test_missing")
        (tmp_path / "collection.json").write_text(json.dumps(data))
    with pytest.raises((OSError, ValueError)):
        local.assess_tests(tmp_path, state(), ())


@pytest.mark.parametrize("filtering", ["-k first", "plugin"])
def test_real_collection_records_tests_before_deselection(tmp_path, filtering):
    root = tmp_path / "source"; root.mkdir()
    plugin = root / "tooling/pytest_inventory.py"; plugin.parent.mkdir()
    plugin.write_bytes((Path(__file__).parents[1] / "pytest_inventory.py").read_bytes())
    (root / "test_sample.py").write_text("def test_first(): pass\ndef test_second(): pass\n")
    if filtering == "plugin":
        (root / "conftest.py").write_text("def pytest_collection_modifyitems(items): items.pop()\n")
    result = subprocess.run([sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", "-p", "tooling.pytest_inventory",
        f"--collection-manifest={tmp_path / 'collection.json'}", f"--junitxml={tmp_path / 'junit.xml'}",
        *(filtering.split() if filtering != "plugin" else [])], cwd=root, capture_output=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    cases = pe.cases_from_xml((tmp_path / "junit.xml").read_bytes())
    assert len(cases) == 1
    data = json.loads((tmp_path / "collection.json").read_text())
    assert len(data["collected"]) == 2 and len(data["selected"]) == 1
    with pytest.raises(ValueError, match="full unfiltered collection"):
        pe.verify_collection((tmp_path / "collection.json").read_bytes(), cases)


def test_unknown_skip_type_is_never_eligible_for_external_waiver():
    cases = pe.cases_from_xml(xml('<skipped type="custom.disabled"/>'))
    assert pe.classify_skips(cases, "darwin")[0]["coverage"] == "environment_blocked"


def test_error_counts_remain_distinct_from_assertion_failures(tmp_path):
    local_report(tmp_path, xml('<error message="setup failed"/>'))
    assert local.junit_counts(tmp_path / "junit.xml") == {"tests": 1, "failures": 0, "errors": 1, "skipped": 0}
