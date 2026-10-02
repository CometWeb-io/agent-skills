"""Supply-chain and privilege rules every GitHub Actions workflow must keep."""
import re
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
            assert scope in WRITE_JUSTIFIED_BY, f"{path.name}/{job_id}: unexpected {scope}: {level}"
            assert any(u.startswith(WRITE_JUSTIFIED_BY[scope]) for u in uses), f"{path.name}/{job_id}: unused {scope}"


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_jobs_are_bounded_and_do_not_keep_the_token(path):
    data = load(path)
    for job_id, job in data["jobs"].items():
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
