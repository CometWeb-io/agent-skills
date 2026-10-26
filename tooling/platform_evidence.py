"""Native test receipts and verified, read-only GitHub Actions evidence.

The trust root is the reviewed source commit and GitHub's artifact/run metadata,
not an uploaded JSON claim. Unknown skips never become platform exemptions.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import subprocess  # nosec B404 - fixed argument vectors, no shell
import sys
import xml.etree.ElementTree as ET
import zipfile

REPOSITORY = "CometWeb-io/agent-skills"
SCHEMA = "cometweb.native-platform-tests/v1"
MAX_BYTES = 32 * 1024 * 1024
POSIX = ("darwin", "linux")
# Selectors are reviewable source policy, never inferred from a skip's message.
REQUIREMENTS = {
    "tooling/tests/test_windows_portability.py::test_windows_scanner_checks_handle_containment_and_junctions": ("win32",),
    "tooling/tests/test_snapshot_installer.py": POSIX,
    "tooling/tests/test_ledger_concurrency.py::test_existing_root_permissions_never_change": POSIX,
    "tooling/tests/test_roaster_shared.py::test_sync_preserves_canonical_mode_and_repairs_mode_only_drift": POSIX,
    "tooling/tests/test_host_migration.py::test_payload_hashes_refuse_following_links_or_reading_special_files[fifo]": POSIX,
    "skills/evidence-researcher/tests/test_observed_facts.py::test_nonregular_or_aliased_source_is_not_read[fifo]": POSIX,
    **{f"tooling/tests/test_real_host_eval.py::{name}": POSIX for name in (
        "test_capture_limit_is_enforced_while_host_is_running", "test_timeout_kills_inherited_process_group",
        "test_not_run_outputs_are_private_under_permissive_umask",
        "test_output_symlinks_and_hardlinks_cannot_overwrite_external_files",
        "test_symlink_output_directory_is_refused", "test_large_prompt_does_not_deadlock_against_full_output_pipes",
        "test_private_output_refuses_fifo_without_blocking",
    )},
}
RUNNER = {"win32": "windows-latest", "linux": "ubuntu-latest", "darwin": "macos-latest"}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def content_fingerprint(state: dict) -> str:
    # Git tree retains committed modes; content hashes remain comparable on Windows.
    return digest(json.dumps({k: v["sha256"] for k, v in state["files"].items()}, sort_keys=True).encode())


def unique_pairs(pairs: list) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key in platform evidence")
        result[key] = value
    return result


def cases_from_xml(blob: bytes) -> list[dict]:
    if len(blob) > MAX_BYTES or b"\0" in blob or b"<!DOCTYPE" in blob.upper() or b"<!ENTITY" in blob.upper():
        raise ValueError("unsupported or oversized JUnit")
    root = ET.fromstring(blob)  # nosec B314 - DTD/entities refused above
    if root.tag not in {"testsuite", "testsuites"}:
        raise ValueError("invalid JUnit root")
    rows, seen = [], set()
    for case in root.iter("testcase"):
        cls, name = case.get("classname", ""), case.get("name", "")
        key = cls + "::" + name
        if cls and name and key in seen:
            raise ValueError("duplicate JUnit test identity")
        seen.add(key)
        skip = case.find("skipped")
        rows.append({"id": key, "classname": cls, "name": name,
                     "status": "failed" if case.find("failure") is not None or case.find("error") is not None
                     else "skipped" if skip is not None else "passed",
                     "reason": skip.get("message", "") if skip is not None else "",
                     "skip_type": skip.get("type", "") if skip is not None else ""})
    if not rows:
        raise ValueError("JUnit contains no executed test cases")
    return rows


def required_platforms(case: dict) -> tuple[str, ...]:
    for selector, platforms in REQUIREMENTS.items():
        path, _, test = selector.partition("::")
        if case["classname"] != path[:-3].replace("/", "."):
            continue
        if not test or case["name"] == test or ("[" not in test and case["name"].split("[")[0] == test):
            return platforms
    return ()


def classify_skips(cases: list[dict], current: str) -> list[dict]:
    rows = []
    for case in cases:
        if case["status"] != "skipped":
            continue
        platforms = required_platforms(case)
        foreign = platforms and current not in platforms and "xfail" not in case["skip_type"].lower()
        rows.append({**case, "required_platforms": list(platforms),
                     "coverage": "platform_evidence_required" if foreign else "environment_blocked"})
    return rows


def gh_api(path: str) -> bytes:
    result = subprocess.run(  # nosec B603 B607 - GET only, fixed host/repository, numeric IDs
        ["gh", "api", "--hostname", "github.com", "--method", "GET", f"repos/{REPOSITORY}/{path}"],
        capture_output=True, stdin=subprocess.DEVNULL, timeout=120, check=False,
        env={**os.environ, "GH_PROMPT_DISABLED": "1", "GH_PAGER": "cat"},
    )
    if result.returncode or len(result.stdout) > MAX_BYTES:
        raise ValueError("GitHub platform evidence could not be retrieved")
    return result.stdout


def json_api(path: str) -> dict:
    data = json.loads(gh_api(path), object_pairs_hook=unique_pairs)
    if not isinstance(data, dict):
        raise ValueError("invalid GitHub evidence metadata")
    return data


def verify_archive(blob: bytes, artifact: dict, run: dict, state: dict) -> tuple[dict, list[dict]]:
    if artifact.get("expired") is not False or artifact.get("digest") != "sha256:" + digest(blob):
        raise ValueError("expired platform artifact or archive hash mismatch")
    origin = artifact.get("workflow_run", {})
    if not isinstance(origin, dict):
        raise ValueError("invalid platform artifact origin")
    if type(origin.get("id")) is not int or origin["id"] != run["id"] or origin.get("head_sha") != state["revision"]:
        raise ValueError("platform artifact belongs to another run or SHA")
    try:
        archive = zipfile.ZipFile(io.BytesIO(blob))
    except zipfile.BadZipFile as exc:
        raise ValueError("invalid platform ZIP") from exc
    with archive:
        names = archive.namelist()
        if sorted(names) != ["junit.xml", "receipt.json", "test.log"]:
            raise ValueError("unexpected or duplicate platform artifact files")
        if any(info.file_size > MAX_BYTES for info in archive.infolist()):
            raise ValueError("oversized platform artifact member")
        try:
            receipt = json.loads(archive.read("receipt.json"), object_pairs_hook=unique_pairs)
            junit = archive.read("junit.xml")
        except (zipfile.BadZipFile, RuntimeError, NotImplementedError) as exc:
            raise ValueError("unreadable platform artifact members") from exc
    if not isinstance(receipt, dict):
        raise ValueError("invalid platform receipt")
    native = receipt.get("platform")
    expected = {"schema": SCHEMA, "status": "passed", "revision": state["revision"],
                "content_fingerprint": content_fingerprint(state), "junit_sha256": digest(junit),
                "repository": REPOSITORY, "run_id": run["id"], "run_attempt": run["run_attempt"]}
    if state["dirty"] or any(type(receipt.get(k)) is not type(v) or receipt.get(k) != v for k, v in expected.items()):
        raise ValueError("platform receipt/source binding mismatch")
    if not isinstance(native, str) or native not in RUNNER or receipt.get("runner_os") != {"win32": "Windows", "linux": "Linux", "darwin": "macOS"}[native]:
        raise ValueError("platform receipt has no matching native runner")
    if not isinstance(receipt.get("python_minor"), str):
        raise ValueError("invalid native Python version")
    expected_name = f"native-tests-{RUNNER[native]}-py{receipt.get('python_minor')}-attempt-{run['run_attempt']}"
    if artifact.get("name") != expected_name:
        raise ValueError("platform artifact name/platform mismatch")
    cases = cases_from_xml(junit)
    if any(c["status"] != "passed" or not c["classname"] or not c["name"] or native not in required_platforms(c) for c in cases):
        raise ValueError("native evidence contains failed, skipped or unrelated cases")
    return receipt, cases


def fetch_evidence(run_id: int, state: dict, output: Path) -> list[dict]:
    if type(run_id) is not int or run_id < 1:
        raise ValueError("platform run ID must be a positive integer")
    run = json_api(f"actions/runs/{run_id}")
    if (type(run.get("id")) is not int or run["id"] != run_id or run.get("head_sha") != state["revision"] or run.get("conclusion") != "success"
            or run.get("status") != "completed" or not isinstance(run.get("repository"), dict)
            or run["repository"].get("full_name") != REPOSITORY
            or type(run.get("run_attempt")) is not int or run["run_attempt"] < 1
            or run.get("path") not in {".github/workflows/platform-matrix.yml", ".github/workflows/attest-packages.yml"}):
        raise ValueError("platform run is not a successful trusted workflow for this SHA")
    listing = json_api(f"actions/runs/{run_id}/artifacts?per_page=100")
    if listing.get("total_count", 0) > 100:
        raise ValueError("too many platform artifacts")
    results = []
    seen = set()
    jobs = json_api(f"actions/runs/{run_id}/jobs?per_page=100")
    if jobs.get("total_count", 0) > 100:
        raise ValueError("too many platform jobs")
    for artifact in listing.get("artifacts", []):
        if (not artifact.get("name", "").startswith("native-tests-")
                or not artifact["name"].endswith(f"-attempt-{run['run_attempt']}")):
            continue
        aid = artifact.get("id")
        size = artifact.get("size_in_bytes")
        if type(aid) is not int or aid < 1 or type(size) is not int or not 0 < size <= MAX_BYTES:
            raise ValueError("invalid platform artifact metadata")
        if aid in seen or artifact["name"] in seen:
            raise ValueError("duplicate platform artifact identity")
        seen.update((aid, artifact["name"]))
        blob = gh_api(f"actions/artifacts/{aid}/zip")
        receipt, cases = verify_archive(blob, artifact, run, state)
        matching = [j for j in jobs.get("jobs", []) if j.get("conclusion") == "success"
                    and RUNNER[receipt["platform"]] in j.get("labels", [])
                    and j.get("name", "").endswith(f"{RUNNER[receipt['platform']]} / py{receipt['python_minor']}")
                    and all(any(s.get("name") == name and s.get("conclusion") == "success" for s in j.get("steps", []))
                            for name in ("Collect native platform evidence", "Upload native platform evidence"))]
        if len(matching) != 1:
            raise ValueError("platform evidence has no successful native producer job")
        output.joinpath(f"platform-{run_id}-{aid}.zip").write_bytes(blob)
        output.joinpath(f"platform-{run_id}-{aid}-metadata.json").write_text(
            json.dumps({"run": run, "artifact": artifact, "job": matching[0]}, sort_keys=True), encoding="utf-8")
        results.append({"run_id": run_id, "artifact_id": aid, "platform": receipt["platform"],
                        "python_minor": receipt["python_minor"],
                        "artifact_sha256": digest(blob), "cases": [c["id"] for c in cases]})
    if not results:
        raise ValueError("platform workflow published no native test evidence")
    return results


def collect(root: Path, output: Path) -> int:
    from core.paths import canonical_output
    from validate_local import source_state, run_step

    output = canonical_output(output)
    before = source_state(root)
    if before["dirty"] or output.exists() or output.is_relative_to(root):
        raise ValueError("native collection needs clean source and a new external output directory")
    if sys.platform not in RUNNER:
        raise ValueError("unsupported native platform")
    output.mkdir(mode=0o700)
    selectors = [s for s, platforms in REQUIREMENTS.items() if sys.platform in platforms]
    command = [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", "-o", "addopts=",
               f"--junitxml={output / 'junit.xml'}", *selectors]
    result = run_step(root, command, output / "test.log", 900)
    after = source_state(root)
    cases = cases_from_xml((output / "junit.xml").read_bytes())
    passed = result["returncode"] == 0 and before == after and all(c["status"] == "passed" for c in cases)
    receipt = {"schema": SCHEMA, "status": "passed" if passed else "failed",
               "revision": before["revision"], "content_fingerprint": content_fingerprint(before),
               "platform": sys.platform, "runner_os": os.environ.get("RUNNER_OS"),
               "python_minor": f"{sys.version_info.major}.{sys.version_info.minor}",
               "python": platform.python_version(), "repository": os.environ.get("GITHUB_REPOSITORY"),
               "run_id": int(os.environ.get("GITHUB_RUN_ID", "0")),
               "run_attempt": int(os.environ.get("GITHUB_RUN_ATTEMPT", "0")),
               "completed_at": datetime.now(timezone.utc).isoformat(), "command": command,
               "junit_sha256": digest(output.joinpath("junit.xml").read_bytes())}
    output.joinpath("receipt.json").write_text(json.dumps(receipt, sort_keys=True), encoding="utf-8")
    return 0 if passed else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--trusted-checkout", action="store_true", help="Acknowledge execution of reviewed repository tests")
    args = parser.parse_args()
    if not args.trusted_checkout:
        parser.error("native collection executes tests; review the source and pass --trusted-checkout")
    try:
        return collect(Path(__file__).resolve().parents[1], args.output.absolute())
    except (OSError, ValueError, ET.ParseError, subprocess.SubprocessError) as exc:
        print(f"Native platform evidence failed: {type(exc).__name__}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
