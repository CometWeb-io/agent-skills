"""Supply-chain and privilege rules every GitHub Actions workflow must keep."""
import re
import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = sorted((ROOT / ".github" / "workflows").glob("*.y*ml"))
PINNED = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_./-]+@[0-9a-f]{40}$")
# Rights a job may request, and the step that justifies each one.
WRITE_JUSTIFIED_BY = {"id-token": "actions/attest@", "attestations": "actions/attest@"}


def load(path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def steps(data):
    for job_id, job in data["jobs"].items():
        for step in job.get("steps", []):
            yield job_id, step


def test_workflows_exist():
    assert WORKFLOWS


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_actions_are_pinned_to_a_commit_with_a_readable_tag(path):
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"\s*(?:-\s+)?uses:\s*(\S+)(.*)$", line)
        if not match or match.group(1).startswith("./"):
            continue
        assert PINNED.match(match.group(1)), f"{path.name}: unpinned action {match.group(1)}"
        # The SHA is what runs; the comment is what Dependabot and reviewers read.
        assert re.search(r"#\s*v\d", match.group(2)), f"{path.name}: {match.group(1)} lacks a '# vX' tag comment"


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_default_token_is_read_only(path):
    data = load(path)
    assert data.get("permissions") == {"contents": "read"}
    triggers = data.get("on", data.get(True))
    assert "pull_request_target" not in (triggers or {})


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_write_rights_are_job_scoped_and_used(path):
    data = load(path)
    for job_id, job in data["jobs"].items():
        uses = [step.get("uses", "") for step in job.get("steps", [])]
        for scope, level in (job.get("permissions") or {}).items():
            if level == "read":
                continue
            if scope == "contents" and job_id == "release" and path.name == "attest-packages.yml":
                assert job["needs"] == "attest"
                assert job["if"] == "startsWith(github.ref, 'refs/tags/v')"
                assert any("gh release create" in step.get("run", "") and "--draft" in step["run"]
                           and "--verify-tag" in step["run"] for step in job["steps"])
                continue
            assert scope in WRITE_JUSTIFIED_BY, f"{path.name}/{job_id}: unexpected {scope}: {level}"
            assert any(u.startswith(WRITE_JUSTIFIED_BY[scope]) for u in uses), f"{path.name}/{job_id}: unused {scope}"


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_jobs_are_bounded_and_do_not_keep_the_token(path):
    data = load(path)
    for job_id, job in data["jobs"].items():
        if "uses" in job:
            assert job["uses"].startswith("./.github/workflows/"), f"{path.name}/{job_id}: unpinned reusable workflow"
            continue  # Reusable jobs inherit timeouts from the called workflow.
        assert isinstance(job.get("timeout-minutes"), int), f"{path.name}/{job_id}: no timeout"
    for job_id, step in steps(data):
        if step.get("uses", "").startswith("actions/checkout@"):
            assert (step.get("with") or {}).get("persist-credentials") is False, f"{path.name}/{job_id}"


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_expressions_reach_shell_only_through_env(path):
    # An expression expanded inside run: is spliced into the script before the
    # shell parses it; passing it through env keeps it data.
    for job_id, step in steps(load(path)):
        assert "${{" not in step.get("run", ""), f"{path.name}/{job_id}: expression inside run: {step.get('name')}"


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_uv_installs_cache_and_locked_syncs(path):
    data = load(path)
    for job_id, step in steps(data):
        if step.get("uses", "").startswith("astral-sh/setup-uv@"):
            assert (step.get("with") or {}).get("enable-cache") is True, f"{path.name}/{job_id}"
        run = step.get("run", "")
        if "uv sync" in run:
            assert "--frozen" in run or "--locked" in run, f"{path.name}/{job_id}: uv sync may rewrite uv.lock"


def test_dependabot_tracks_pinned_actions():
    config = yaml.safe_load((ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8"))
    assert "github-actions" in {row["package-ecosystem"] for row in config["updates"]}


@pytest.mark.skipif(not shutil.which("bash") or not shutil.which("sha256sum"), reason="POSIX release preparation")
def test_release_asset_preparation_checks_bytes_and_avoids_name_collisions(tmp_path):
    fixture = tmp_path / "artifact"
    fixture.mkdir()
    (fixture / "agent-skills.cdx.json").write_text('{}\n')
    for skill in ("first", "second"):
        package = fixture / skill / "1.0.0"
        package.mkdir(parents=True)
        payload = ("archive for " + skill).encode()
        (package / "skill.zip").write_bytes(payload)
        (package / "skill.zip.sha256").write_text(hashlib.sha256(payload).hexdigest() + "  skill.zip\n")
    commands = tmp_path / "bin"
    commands.mkdir()
    gh = commands / "gh"
    gh.write_text(f"#!{sys.executable}\nimport shutil,sys\n"
                  + f"assert sys.argv[1:3] == ['run', 'download']\nshutil.copytree({str(fixture)!r}, sys.argv[-1])\n")
    gh.chmod(0o755)
    job = load(ROOT / ".github/workflows/attest-packages.yml")["jobs"]["release"]
    prepare = next(step["run"] for step in job["steps"] if "gh run download" in step.get("run", ""))
    env = {**os.environ, "PATH": str(commands) + os.pathsep + os.environ["PATH"],
           "RUN_ID": "fixture-run", "SOURCE_SHA": "a" * 40}
    good = tmp_path / "good"
    good.mkdir()
    result = subprocess.run(["bash", "-e", "-c", prepare], cwd=good, env=env,
                            capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    assets = good / "assets"
    assert {p.name for p in assets.glob("*.zip")} == {"first-1.0.0.zip", "second-1.0.0.zip"}
    for line in (assets / "SHA256SUMS").read_text().splitlines():
        digest, name = line.split(maxsplit=1)
        assert digest == hashlib.sha256((assets / name.strip()).read_bytes()).hexdigest()
    assert (assets / "SOURCE_COMMIT").read_text().strip() == "a" * 40
    (fixture / "first/1.0.0/skill.zip").write_bytes(b"tampered")
    bad = tmp_path / "bad"
    bad.mkdir()
    result = subprocess.run(["bash", "-e", "-c", prepare], cwd=bad, env=env,
                            capture_output=True, text=True, check=False)
    assert result.returncode != 0
    assert not list((bad / "assets").glob("*.zip"))
