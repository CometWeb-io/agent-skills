"""tooling/real_host_eval.py: plan, dry run, isolated execution, grading and the scorecard.

No real host is started here. The host binaries are small scripts written into a
temp directory that log how they were called and print canned transcripts, so the
adapter, the isolation, the budget caps and the grading are all exercised offline.
"""

from __future__ import annotations

import io
import json
import os
import signal
import stat
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tooling"))

import real_host_eval as rhe  # noqa: E402

@pytest.fixture(autouse=True)
def fake_adapter_credentials(monkeypatch):
    # These fake processes test the harness; credentials remain synthetic.
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-harness-token")
    monkeypatch.setenv("OPENAI_API_KEY", "fake-harness-token")


GOLDEN = (ROOT / "evals/output/release-readiness/good-go-with-controls.md").read_text(encoding="utf-8")
BROKEN = GOLDEN.replace("## Verdict", "## Summary", 1)

FAKE_CLAUDE = r'''#!{python}
import json, os, sys, time
LOG = {log!r}
SCRIPT = json.load(open({script!r}))
argv = sys.argv[1:]
entry = {{"argv": argv, "env": dict(os.environ), "cwd": os.getcwd()}}
if "--plugin-dir" in argv:
    stage = argv[argv.index("--plugin-dir") + 1]
    entry["stage_has_skill"] = os.path.isfile(os.path.join(stage, "skills", "release-readiness", "SKILL.md"))
if argv == ["--version"]:
    open(LOG, "a").write(json.dumps({{"argv": argv}}) + "\n")
    print("9.9.9 (Fake Host)")
    sys.exit(0)
prompt = sys.stdin.read()
entry["prompt"] = prompt
open(LOG, "a").write(json.dumps(entry) + "\n")
for key, spec in SCRIPT.items():
    if key in prompt:
        break
else:
    sys.exit(3)
time.sleep(spec.get("sleep", 0))
print(json.dumps({{"type": "system", "subtype": "init", "model": spec.get("model", "fake-model-1")}}))
print("not json at all")
if spec.get("skill"):
    print(json.dumps({{"type": "assistant", "message": {{"content": [
        {{"type": "tool_use", "name": "Skill", "input": {{"skill": "cometweb-agent-skills:" + spec["skill"]}}}}]}}}}))
print(json.dumps({{"type": "result", "subtype": "success", "is_error": spec.get("is_error", False),
                  "result": spec.get("output", ""), "total_cost_usd": spec.get("cost", 0.01), "num_turns": 2,
                  "usage": {{"input_tokens": 100, "cache_read_input_tokens": 50, "output_tokens": 20}}}}))
sys.exit(spec.get("exit", 0))
'''

FAKE_CODEX = r'''#!{python}
import json, os, sys
LOG = {log!r}
SCRIPT = json.load(open({script!r}))
argv = sys.argv[1:]
open(LOG, "a").write(json.dumps({{"argv": argv, "env": dict(os.environ)}}) + "\n")
if argv == ["--version"]:
    print("codex-fake 0.0.1")
    sys.exit(0)
if argv[0] == "plugin":
    sys.exit(0)
prompt = sys.stdin.read()
spec = next(v for k, v in SCRIPT.items() if k in prompt)
if spec.get("skill"):
    print(json.dumps({{"type": "item.completed", "item": {{"type": "command_execution",
        "command": "sed -n 1,200p " + os.environ["CODEX_HOME"] + "/plugins/cache/skills/" + spec["skill"] + "/SKILL.md"}}}}))
print(json.dumps({{"type": "item.completed", "item": {{"type": "agent_message", "text": spec["output"]}}}}))
print(json.dumps({{"type": "turn.completed", "usage": spec.get("usage", {{"input_tokens": 1000, "cached_input_tokens": 0, "output_tokens": 200}})}}))
'''


def make_fake(tmp_path: Path, template: str, script: dict, name: str) -> tuple[Path, Path]:
    log = tmp_path / f"{name}.log"
    script_path = tmp_path / f"{name}-script.json"
    script_path.write_text(json.dumps(script), encoding="utf-8")
    binary = tmp_path / "bin" / name
    binary.parent.mkdir(exist_ok=True)
    binary.write_text(template.format(python=sys.executable, log=str(log), script=str(script_path)), encoding="utf-8")
    binary.chmod(binary.stat().st_mode | stat.S_IXUSR)
    return binary, log


def log_entries(log: Path) -> list[dict]:
    return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()] if log.exists() else []


def task(task_id: str, prompt: str, *, skill: str = "release-readiness", role: str = "positive",
         checks: tuple[str, ...] = ("routing", "output"), expected: str | None = "release-readiness",
         must_not: tuple[str, ...] = (), **extra) -> dict:
    return {"id": task_id, "skill": skill, "role": role, "source": "evals/routing/suite.json", "case_id": task_id,
            "prompt": prompt, "fixture": None, "lang": "en", "checks": list(checks),
            "expected_primary_skill": expected, "allowed_secondary_skills": [], "must_not_trigger": list(must_not),
            "preserve_literals": [], "review_notes": [], **extra}


def make_plan(tmp_path: Path, tasks: list[dict]) -> Path:
    plan = {"schema": rhe.PLAN_SCHEMA_V1, "repo_version": "0.0.0", "sources": {}, "excluded_sources": [],
            "selection": {}, "graded_skills": ["release-readiness"], "tasks": tasks, "skipped": []}
    plan["plan_sha256"] = rhe.plan_digest(plan)
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(plan), encoding="utf-8")
    return path


# --------------------------------------------------------------------------- plan


def test_plan_is_deterministic_and_never_reads_the_holdout():
    first = rhe.build_plan(per_skill=2, negatives_per_skill=1, seed=7)
    second = rhe.build_plan(per_skill=2, negatives_per_skill=1, seed=7)
    assert first == second
    assert first["acceptance_version"] == 2
    assert set(first["frozen_hashes"]) == {
        "candidate_sha256", "payload_sha256", "benchmark_sha256",
        "rubric_sha256", "host_config_sha256",
    }
    assert all(len(value) == 64 for value in first["frozen_hashes"].values())
    assert not any("holdout" in source for source in first["sources"])
    assert {t["source"] for t in first["tasks"]} <= set(rhe.ROUTING_SOURCES) | set(rhe.MODEL_SOURCES)
    with pytest.raises(ValueError, match="frozen holdout"):
        rhe.read_json(ROOT / "evals/routing/holdout.json")


def test_plan_caps_tasks_per_skill_and_assigns_checks():
    plan = rhe.build_plan(per_skill=2, negatives_per_skill=1)
    graded = set(plan["graded_skills"])
    by_skill: dict[str, list[dict]] = {}
    for t in plan["tasks"]:
        by_skill.setdefault(t["skill"], []).append(t)
    assert len(by_skill) >= 30
    for skill, tasks in by_skill.items():
        positives = [t for t in tasks if t["role"] != "negative"]
        negatives = [t for t in tasks if t["role"] == "negative"]
        assert len(positives) <= 2 and len(negatives) <= 1
        for t in positives:
            assert t["expected_primary_skill"] == skill
            assert ("output" in t["checks"]) == (skill in graded or bool(t["preserve_literals"]))
        for t in negatives:
            assert t["checks"] == ["routing"] and skill in t["must_not_trigger"]
    # model cases, which carry fixtures, come before bare routing prompts
    release = [t for t in plan["tasks"] if t["skill"] == "release-readiness" and t["role"] != "negative"]
    assert release[0]["role"] == "model" and release[0]["fixture"]


def test_plan_filters_and_rejects_unknown_skill():
    plan = rhe.build_plan(skills=["ai-council"], langs=["pl"], per_skill=5, negatives_per_skill=0)
    assert {t["skill"] for t in plan["tasks"]} == {"ai-council"}
    assert all(t["lang"] == "pl" for t in plan["tasks"])
    with pytest.raises(ValueError, match="unknown"):
        rhe.build_plan(skills=["no-such-skill"])


def test_edited_plan_is_refused(tmp_path):
    path = make_plan(tmp_path, [task("t1", "PROMPT-A")])
    data = json.loads(path.read_text())
    data["tasks"][0]["prompt"] = "something else"
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="edited after"):
        rhe.load_plan(path)


def test_v1_plan_remains_readable(tmp_path):
    path = make_plan(tmp_path, [task("t1", "PROMPT-A")])
    data = json.loads(path.read_text())
    data["schema"] = rhe.PLAN_SCHEMA_V1
    data.pop("acceptance_version", None)
    data["plan_sha256"] = rhe.plan_digest(data)
    path.write_text(json.dumps(data))
    assert rhe.load_plan(path)["schema"] == rhe.PLAN_SCHEMA_V1


def test_v2_fingerprint_drift_is_rejected(monkeypatch):
    plan = rhe.build_plan(skills=["release-readiness"], per_skill=1, negatives_per_skill=0)
    actual = dict(plan["frozen_hashes"])
    actual["benchmark_sha256"] = "0" * 64
    monkeypatch.setattr(rhe, "acceptance_fingerprints", lambda root=rhe.ROOT: actual)
    with pytest.raises(ValueError, match="benchmark_sha256"):
        rhe.assert_fingerprints_current(plan)


def test_canary_is_planted_as_parts_only():
    plan = rhe.build_plan(skills=["release-readiness"], per_skill=1, negatives_per_skill=0, canary=True)
    t = plan["tasks"][0]
    prompt = rhe.render_prompt(t)
    assert t["canary"]["instruction"] in prompt
    assert t["canary"]["token"] not in prompt


# --------------------------------------------------------------------------- run


def test_dry_run_is_the_default_and_starts_nothing(tmp_path, capsys):
    binary, log = make_fake(tmp_path, FAKE_CLAUDE, {"PROMPT": {"output": "x"}}, "claude")
    plan = make_plan(tmp_path, [task("t1", "PROMPT-A"), task("t2", "PROMPT-B")])
    code = rhe.main(["run", "--plan", str(plan), "--host", "claude", "--bin", str(binary),
                     "--out", str(tmp_path / "out"), "--condition", "both", "--price-in", "3", "--price-out", "15"])
    out = capsys.readouterr().out
    assert code == 0
    assert not log.exists(), "a dry run must not start the host, not even --version"
    assert not (tmp_path / "out").exists()
    assert "DRY RUN" in out and "--plugin-dir" in out and "--max-budget-usd 0.5" in out
    assert out.count("  run:   ") == 4 and "PROMPT-A" in out
    assert "hard cap 4 x $0.5 = $2.00" in out and "ESTIMATE 4 job(s)" in out


def test_execute_isolates_the_host_and_grades_the_transcript(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
    monkeypatch.setenv("GITHUB_TOKEN", "must-not-leak")
    script = {"PROMPT-A": {"skill": "release-readiness", "output": GOLDEN, "cost": 0.02},
              "PROMPT-B": {"skill": "release-readiness", "output": "I can help with that."},
              "PROMPT-C": {"skill": "release-readiness", "output": BROKEN}}
    binary, log = make_fake(tmp_path, FAKE_CLAUDE, script, "claude")
    plan = make_plan(tmp_path, [
        task("pos", "PROMPT-A"),
        task("neg", "PROMPT-B", role="negative", checks=("routing",), expected=None, must_not=("release-readiness",)),
        task("broken", "PROMPT-C"),
    ])
    out = tmp_path / "out"
    code = rhe.main(["run", "--plan", str(plan), "--host", "claude", "--bin", str(binary), "--out", str(out),
                     "--execute"])
    assert code == 0
    calls = [e for e in log_entries(log) if e["argv"] != ["--version"]]
    assert len(calls) == 3
    home = str(Path.home())
    for call in calls:
        env = call["env"]
        assert env["HOME"] != home and env["CLAUDE_CONFIG_DIR"] != str(Path(home) / ".claude")
        assert env["HOME"].startswith(env["TMPDIR"]) and env["CLAUDE_CONFIG_DIR"].startswith(env["TMPDIR"])
        assert env["ANTHROPIC_API_KEY"] == "test-key-not-real"
        assert "GITHUB_TOKEN" not in env
        assert call["stage_has_skill"] is True
        assert "--tools" in call["argv"] and "Read,Glob,Grep,Skill" in call["argv"]
    assert len({c["env"]["HOME"] for c in calls}) == 3, "each run gets its own HOME"
    assert not Path(calls[0]["env"]["HOME"]).exists(), "temp HOMEs are removed after the run"

    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["host_version"] == "9.9.9 (Fake Host)"
    assert manifest["completed_jobs"] == 3 and manifest["models_reported"] == ["fake-model-1"]
    record = next(json.loads(p.read_text()) for p in out.glob("runs/*/record.json")
                  if json.loads(p.read_text())["task_id"] == "pos")
    assert record["activated_skills"] == ["release-readiness"]
    assert record["input_tokens"] == 150 and record["output_tokens"] == 20 and record["cost_source"] == "host_reported"
    assert "test-key-not-real" not in json.dumps(record)

    grades = {r["task_id"]: r["checks"] for r in rhe.grade_run(out)["results"]}
    assert grades["pos"]["routing"]["status"] == "pass"
    assert grades["pos"]["output"]["status"] == "pass"
    assert grades["neg"]["routing"]["status"] == "fail"
    assert "expected no skill" in grades["neg"]["routing"]["reason"]
    assert grades["broken"]["routing"]["status"] == "pass"
    assert grades["broken"]["output"]["status"] == "fail"
    assert any(e.startswith("SECTION_MISSING") or e.startswith("VERDICT_MISSING") for e in grades["broken"]["output"]["errors"])


def test_run_refuses_a_used_output_directory(tmp_path):
    binary, _ = make_fake(tmp_path, FAKE_CLAUDE, {"PROMPT": {"output": GOLDEN}}, "claude")
    plan = make_plan(tmp_path, [task("t1", "PROMPT-A")])
    out = tmp_path / "out"
    out.mkdir()
    (out / "old.json").write_text("{}")
    assert rhe.main(["run", "--plan", str(plan), "--host", "claude", "--bin", str(binary), "--out", str(out),
                     "--execute"]) == 2


def test_max_tasks_and_total_budget_stop_the_run(tmp_path):
    script = {"PROMPT": {"skill": "release-readiness", "output": GOLDEN, "cost": 0.3}}
    binary, log = make_fake(tmp_path, FAKE_CLAUDE, script, "claude")
    plan = rhe.load_plan(make_plan(tmp_path, [task(f"t{i}", f"PROMPT-{i}") for i in range(5)]))
    opts = rhe.RunOptions(host="claude", bin=str(binary), conditions=("plugin",), max_tasks=2)
    summary = rhe.execute(plan, opts, tmp_path / "a", stream=io.StringIO())
    assert summary["planned_jobs"] == 2 and summary["completed_jobs"] == 2

    opts = rhe.RunOptions(host="claude", bin=str(binary), conditions=("plugin",), max_tasks=5,
                          max_usd_per_task=0.5, max_total_usd=0.6)
    summary = rhe.execute(plan, opts, tmp_path / "b", stream=io.StringIO())
    # first run may spend up to 0.5 of 0.6; after it spent 0.3, another 0.5 could pass the cap
    assert summary["completed_jobs"] == 1 and summary["not_started_jobs"] == 4
    assert summary["stop_reason"].startswith("max_total_usd")

    opts = rhe.RunOptions(host="claude", bin=str(binary), conditions=("plugin",), max_tasks=5,
                          max_total_tokens=300)
    summary = rhe.execute(plan, opts, tmp_path / "c", stream=io.StringIO())
    assert summary["completed_jobs"] == 2 and summary["stop_reason"].startswith("max_total_tokens")


def test_timeouts_count_as_errors_and_stop_after_two_in_a_row(tmp_path, monkeypatch):
    monkeypatch.setattr(rhe, "TIMEOUT_RANGE", (1, 3600))
    binary, _ = make_fake(tmp_path, FAKE_CLAUDE, {"PROMPT": {"output": GOLDEN, "sleep": 5}}, "claude")
    plan = rhe.load_plan(make_plan(tmp_path, [task(f"t{i}", f"PROMPT-{i}") for i in range(3)]))
    opts = rhe.RunOptions(host="claude", bin=str(binary), conditions=("plugin",), timeout=1)
    summary = rhe.execute(plan, opts, tmp_path / "out", stream=io.StringIO())
    assert summary["error_jobs"] == 2 and summary["not_started_jobs"] == 1
    assert "consecutive errors" in summary["stop_reason"]
    # an unreported cost counts as the per-run cap, never as zero
    assert summary["spent_usd"] is None and summary["accounted_usd"] == pytest.approx(1.0)
    grades = rhe.grade_run(tmp_path / "out")
    assert grades["counts"] == {"completed": 0, "errors": 2, "not_run": 0}
    assert all(r["checks"]["output"]["status"] == "not_run" for r in grades["results"])


def test_not_run_materializes_every_scheduled_job_and_keeps_counts_separate(tmp_path):
    plan = rhe.load_plan(make_plan(tmp_path, [task("a", "PROMPT-A"), task("b", "PROMPT-B")]))
    opts = rhe.RunOptions(host="cursor", bin="cursor", conditions=rhe.CONDITIONS, max_tasks=4)
    summary = rhe.execute(plan, opts, tmp_path / "out", stream=io.StringIO())
    assert summary["completed_jobs"] == 0
    assert summary["error_jobs"] == 0
    assert summary["not_run_jobs"] == summary["planned_jobs"] == 4
    records = list((tmp_path / "out" / "runs").glob("*/record.json"))
    assert len(records) == 4
    assert all(json.loads(path.read_text())["status"] == "not_run" for path in records)
    grades = rhe.grade_run(tmp_path / "out")
    assert grades["counts"] == {"completed": 0, "errors": 0, "not_run": 4}
    report = rhe.build_report([grades])
    assert report["run_errors"] == 0 and report["run_not_run"] == 4


def test_retry_metadata_is_only_emitted_for_explicit_transient_failures():
    assert rhe.retry_metadata("timeout", None, "") == {
        "retryable": True, "retry_classification": "timeout", "attempt": 1,
    }
    assert rhe.retry_metadata("error", 503, "")["retry_classification"] == "exit_code_503"
    assert rhe.retry_metadata("error", 1, "invalid request") == {}


def test_codex_adapter_installs_the_plugin_and_reads_usage(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-not-real")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "must-not-reach-codex")
    script = {"PROMPT-A": {"skill": "release-readiness", "output": GOLDEN}}
    binary, log = make_fake(tmp_path, FAKE_CODEX, script, "codex")
    plan = rhe.load_plan(make_plan(tmp_path, [task("pos", "PROMPT-A")]))
    opts = rhe.RunOptions(host="codex", bin=str(binary), conditions=("plugin", "baseline"), max_tasks=2,
                          price_in=1.0, price_out=10.0, model="fake-model-2")
    summary = rhe.execute(plan, opts, tmp_path / "out", stream=io.StringIO())
    assert summary["completed_jobs"] == 2
    calls = log_entries(log)
    setups = [c["argv"][:2] for c in calls if c["argv"][0] == "plugin"]
    assert setups == [["plugin", "marketplace"], ["plugin", "add"]], "only the plugin condition installs it"
    execs = [c for c in calls if c["argv"][0] == "exec"]
    assert all(c["argv"][-1] == "-" and "--sandbox" in c["argv"] and "fake-model-2" in c["argv"] for c in execs)
    assert all("ANTHROPIC_API_KEY" not in c["env"] and c["env"]["OPENAI_API_KEY"] for c in execs)
    records = {json.loads(p.read_text())["condition"]: json.loads(p.read_text()) for p in (tmp_path / "out").glob("runs/*/record.json")}
    assert records["plugin"]["activated_skills"] == ["release-readiness"]
    assert records["plugin"]["cost_usd"] == pytest.approx(0.003)
    assert records["plugin"]["cost_source"] == "estimated_from_prices"

    no_prices = rhe.RunOptions(host="codex", bin=str(binary), conditions=("plugin",), max_total_usd=1.0)
    with pytest.raises(ValueError, match="native dollar cap"):
        rhe.execute(plan, no_prices, tmp_path / "out2", stream=io.StringIO())


def test_both_conditions_run_as_adjacent_pairs_and_report_a_paired_result(tmp_path):
    script = {"PROMPT": {"skill": "release-readiness", "output": GOLDEN}}
    binary, _ = make_fake(tmp_path, FAKE_CLAUDE, script, "claude")
    plan = rhe.load_plan(make_plan(tmp_path, [task(f"t{i}", f"PROMPT-{i}") for i in range(3)]))
    opts = rhe.RunOptions(host="claude", bin=str(binary), conditions=rhe.CONDITIONS, max_tasks=5)
    jobs = rhe.schedule(plan, opts)
    assert len(jobs) == 4, "an odd cap never splits a pair"
    assert [j["task"]["id"] for j in jobs[0::2]] == [j["task"]["id"] for j in jobs[1::2]]
    rhe.execute(plan, opts, tmp_path / "out", stream=io.StringIO())
    grades = rhe.grade_run(tmp_path / "out")
    baseline = [r for r in grades["results"] if r["condition"] == "baseline"]
    assert all(r["checks"]["routing"]["status"] == "n/a" for r in baseline)
    report = rhe.build_report([grades])
    assert report["paired"]["pairs"] == 2 and report["paired"]["both_pass"] == 2
    assert report["paired"]["comparable"] is False
    assert any("reasoning effort was not observed" in warning for warning in report["warnings"])
    text = rhe.render_markdown(report)
    assert "## Output - plugin" in text and "Plugin vs baseline" in text and "`release-readiness`" in text


# --------------------------------------------------------------------------- report


def test_wilson_interval_and_exact_sign_test():
    lo, hi = rhe.wilson(8, 10)
    assert lo == pytest.approx(0.4902, abs=1e-4) and hi == pytest.approx(0.9433, abs=1e-4)
    assert rhe.wilson(0, 0) is None
    lo, hi = rhe.wilson(0, 5)
    assert lo == 0.0 and hi == pytest.approx(0.4345, abs=1e-4)
    assert rhe.sign_test(5, 0) == pytest.approx(0.0625)
    assert rhe.sign_test(3, 3) == 1.0
    assert rhe.sign_test(0, 0) == 1.0


def _grades(condition: str, model: str, statuses: list[str], host_version: str = "1.0") -> dict:
    return {"schema": rhe.GRADES_SCHEMA, "plan_sha256": "p", "host": "claude", "host_version": host_version,
            "models_reported": [model], "payload_sha256": "x",
            "results": [{"run_id": f"{condition}{i}", "task_id": f"t{i}", "skill": "ai-council", "role": "positive",
                         "condition": condition, "repeat": 0, "run_status": "executed", "model": model,
                         "checks": {"output": {"status": s}}} for i, s in enumerate(statuses)]}


def test_report_flags_runs_that_are_not_comparable():
    report = rhe.build_report([_grades("plugin", "model-a", ["pass", "pass", "fail"]),
                               _grades("baseline", "model-b", ["fail", "pass", "fail"], host_version="2.0")])
    assert any("more than one model" in w for w in report["warnings"])
    assert any("host versions" in w for w in report["warnings"])
    assert report["paired"]["plugin_only_pass"] == 1 and report["paired"]["comparable"] is False
    cell = report["results"]["plugin"]["output"]["skills"]["ai-council"]
    assert cell["n"] == 3 and cell["pass"] == 2
    assert "Not comparable" in rhe.render_markdown(report)


def test_parse_events_keeps_only_known_skills():
    text = "\n".join([
        "garbage",
        json.dumps({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Skill", "input": {"skill": "made-up-skill"}},
            {"type": "tool_use", "name": "Read", "input": {"file_path": "/x/skills/ai-council/SKILL.md"}}]}}),
        json.dumps({"type": "result", "result": "done", "is_error": False}),
    ])
    parsed = rhe.parse_events(text, {"ai-council", "release-readiness"})
    assert parsed["activated_skills"] == ["ai-council"] and parsed["output"] == "done"
    assert parsed["input_tokens"] is None and parsed["cost_usd"] is None


def test_canary_followed_fails_the_output_check(tmp_path):
    plan = rhe.build_plan(skills=["release-readiness"], per_skill=1, negatives_per_skill=0, canary=True)
    t = plan["tasks"][0]
    graded = rhe.graded_skills()
    assert rhe.output_check(t, GOLDEN, graded)["status"] == "pass"
    result = rhe.output_check(t, GOLDEN + f"\nReference: {t['canary']['token']}\n", graded)
    assert result["status"] == "fail" and "INJECTION_FOLLOWED:canary-file" in result["errors"]


def test_options_are_bounded():
    with pytest.raises(ValueError):
        rhe.validate_options(rhe.RunOptions(host="claude", bin="x", conditions=("plugin",), max_tasks=10_000))
    with pytest.raises(ValueError):
        rhe.validate_options(rhe.RunOptions(host="claude", bin="x", conditions=("plugin",), price_in=1.0))
    with pytest.raises(ValueError):
        rhe.validate_options(rhe.RunOptions(host="claude", bin="x", conditions=("plugin",), model="a b; rm"))


def test_execute_not_run_is_nonzero_but_dry_run_stays_successful(tmp_path):
    plan = make_plan(tmp_path, [task("a", "PROMPT-A")])
    args = ["run", "--plan", str(plan), "--host", "cursor", "--out", str(tmp_path / "out")]
    assert rhe.main(args) == 0
    assert not (tmp_path / "out").exists()
    assert rhe.main([*args, "--execute"]) == 3
    assert json.loads((tmp_path / "out" / "manifest.json").read_text())["execution_status"] == "NOT_RUN"


@pytest.mark.parametrize("host,effort,flag,value", [
    ("claude", "high", "--effort", "high"),
    ("codex", "high", "--config", 'model_reasoning_effort="high"'),
])
def test_reasoning_effort_uses_host_native_flags(host, effort, flag, value, tmp_path):
    opts = rhe.RunOptions(host=host, bin=host, conditions=("plugin",), reasoning_effort=effort)
    rhe.validate_options(opts)
    _, command = rhe.build_commands(opts, "plugin", tmp_path / "stage", tmp_path / "output.md")
    assert command[command.index(flag) + 1] == value


@pytest.mark.parametrize("host,effort", [("cursor", "high"), ("claude", "ultra"), ("codex", "invented")])
def test_unsupported_effort_is_not_silently_mapped(host, effort):
    with pytest.raises(ValueError, match="unsupported reasoning effort"):
        rhe.validate_options(rhe.RunOptions(host=host, bin=host, conditions=("plugin",), reasoning_effort=effort))


# --------------------------------------------------------------------------- adversarial runner controls

@pytest.mark.parametrize("schema", [rhe.PLAN_SCHEMA_V1, rhe.PLAN_SCHEMA_V2])
@pytest.mark.parametrize("bad", ["../escape", "/absolute", "a/../../../escape", "a\\b", "..", "x" * 201,
                                 "a\x00b", "zażółć", None, []])
def test_self_consistent_plan_rejects_unsafe_ids(tmp_path, schema, bad):
    plan = rhe.build_plan(skills=["release-readiness"], per_skill=1, negatives_per_skill=0)
    plan["schema"] = schema
    if schema == rhe.PLAN_SCHEMA_V1:
        plan.pop("acceptance_version")
    plan["tasks"][0]["id"] = bad
    plan["plan_sha256"] = rhe.plan_digest(plan)
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(plan))
    with pytest.raises(ValueError, match="task.*id"):
        rhe.load_plan(path)


@pytest.mark.parametrize("patch", [{"skill": "../escape"}, {"prompt": []}, {"checks": ["bogus"]},
                                  {"fixture": []}, {"must_not_trigger": [None]}, {"canary": []}])
def test_task_contract_is_validated(tmp_path, patch):
    data = task("a", "PROMPT")
    data.update(patch)
    with pytest.raises(ValueError):
        rhe.load_plan(make_plan(tmp_path, [data]))


def test_duplicate_ids_and_incomplete_v2_are_refused(tmp_path):
    with pytest.raises(ValueError, match="duplicate"):
        rhe.load_plan(make_plan(tmp_path, [task("a", "X"), task("a", "Y")]))
    path = make_plan(tmp_path, [task("a", "X")])
    plan = json.loads(path.read_text())
    plan["schema"] = rhe.PLAN_SCHEMA_V2
    plan["plan_sha256"] = rhe.plan_digest(plan)
    path.write_text(json.dumps(plan))
    with pytest.raises(ValueError, match="v2"):
        rhe.load_plan(path)


def test_not_run_cli_rejects_traversal_before_writing(tmp_path):
    path = make_plan(tmp_path, [task("x/../../../escaped", "PROMPT")])
    out = tmp_path / "out"
    assert rhe.main(["run", "--plan", str(path), "--host", "cursor", "--out", str(out), "--execute"]) == 2
    assert not out.exists() and not (tmp_path / "escaped").exists()


def test_dollar_ceiling_without_native_cap_is_refused_before_host(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic")
    binary, log = make_fake(tmp_path, FAKE_CLAUDE, {"PROMPT": {"output": "ok"}}, "fake")
    plan = rhe.load_plan(make_plan(tmp_path, [task("a", "PROMPT")]))
    opts = rhe.RunOptions(host="codex", bin=str(binary), conditions=("baseline",), max_total_usd=1,
                          price_in=1, price_out=1)
    with pytest.raises(ValueError, match="native.*cap"):
        rhe.execute(plan, opts, tmp_path / "out", stream=io.StringIO())
    assert not log.exists() and not (tmp_path / "out").exists()


@pytest.mark.parametrize("field,value", [("max_total_usd", float("nan")), ("max_total_usd", float("inf")),
                                        ("price_in", -1), ("price_in", float("nan")), ("price_out", float("inf"))])
def test_invalid_budget_numbers_are_rejected(field, value):
    opts = rhe.RunOptions(host="claude", bin="fake", conditions=("baseline",), price_in=1, price_out=1)
    setattr(opts, field, value)
    with pytest.raises(ValueError):
        rhe.validate_options(opts)


@pytest.mark.skipif(os.name != "posix", reason="POSIX process-group qualification")
def test_capture_limit_is_enforced_while_host_is_running(tmp_path, monkeypatch):
    monkeypatch.setattr(rhe, "MAX_CAPTURE", 4096)
    code = "import os,time\nfor _ in range(10000): os.write(1,b'x'*1024); os.write(2,b'y'*1024)\ntime.sleep(20)"
    started = time.monotonic()
    result = rhe._run_capped([sys.executable, "-c", code], dict(os.environ), tmp_path, "", 5,
                             tmp_path / "events", tmp_path / "stderr")
    assert len(result) == 3 and result[2] is True
    assert time.monotonic() - started < 3
    assert (tmp_path / "events").stat().st_size <= 4096
    assert (tmp_path / "stderr").stat().st_size <= 4096


@pytest.mark.skipif(os.name != "posix", reason="POSIX process-group qualification")
@pytest.mark.parametrize("parent_exits", [False, True])
def test_timeout_kills_inherited_process_group(tmp_path, parent_exits):
    pidfile = tmp_path / "child.pid"
    heartbeat = tmp_path / "heartbeat"
    child_code = f"import time\nwhile True:\n open({str(heartbeat)!r},'a').write('alive\\n'); time.sleep(.05)"
    code = ("import subprocess,sys,time\np=subprocess.Popen([sys.executable,'-c'," + repr(child_code) + "])\n"
            f"open({str(pidfile)!r},'w').write(str(p.pid))\n"
            f"while not __import__('os').path.exists({str(heartbeat)!r}): time.sleep(.01)\n"
            + ("sys.exit(0)" if parent_exits else "time.sleep(30)"))
    child = None
    try:
        result = rhe._run_capped([sys.executable, "-c", code], dict(os.environ), tmp_path, "", 1,
                                 tmp_path / "events", tmp_path / "stderr")
        child = int(pidfile.read_text())
        assert result[1] is True
        assert heartbeat.exists()
        observed = heartbeat.read_bytes()
        time.sleep(.2)
        assert heartbeat.read_bytes() == observed, "inherited child must stop producing effects"
    finally:
        if child is None and pidfile.exists():
            child = int(pidfile.read_text())
        if child:
            try:
                os.kill(child, signal.SIGKILL)
            except ProcessLookupError:
                pass


@pytest.mark.skipif(os.name != "posix", reason="POSIX permissions")
def test_not_run_outputs_are_private_under_permissive_umask(tmp_path):
    plan = rhe.load_plan(make_plan(tmp_path, [task("a", "PROMPT")]))
    old = os.umask(0)
    try:
        out = tmp_path / "out"
        rhe.execute(plan, rhe.RunOptions(host="cursor", bin="cursor", conditions=("plugin",)), out)
    finally:
        os.umask(old)
    for path in [out, *out.rglob("*")]:
        assert stat.S_IMODE(path.stat().st_mode) == (0o700 if path.is_dir() else 0o600)


@pytest.mark.skipif(os.name != "posix", reason="POSIX symlinks")
def test_output_symlinks_and_hardlinks_cannot_overwrite_external_files(tmp_path):
    target = tmp_path / "outside"
    target.write_text("preserved")
    link = tmp_path / "link"
    link.symlink_to(target)
    with pytest.raises((OSError, ValueError)):
        rhe.write_json(link, {"overwritten": True})
    link.unlink()
    os.link(target, link)
    with pytest.raises((OSError, ValueError)):
        rhe.write_json(link, {"overwritten": True})
    assert target.read_text() == "preserved"


@pytest.mark.skipif(os.name != "posix", reason="POSIX symlinks")
def test_symlink_output_directory_is_refused(tmp_path):
    target = tmp_path / "outside"
    target.mkdir()
    out = tmp_path / "out"
    out.symlink_to(target, target_is_directory=True)
    plan = rhe.load_plan(make_plan(tmp_path, [task("a", "PROMPT")]))
    with pytest.raises(ValueError, match="symlink"):
        rhe.execute(plan, rhe.RunOptions(host="cursor", bin="cursor", conditions=("plugin",)), out)
    assert list(target.iterdir()) == []


def test_estimated_budget_reserves_before_admission_and_stops_on_unknown_cost(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic")
    binary, log = make_fake(tmp_path, FAKE_CODEX, {"PROMPT": {"output": "ok", "usage": None}}, "codex")
    plan = rhe.load_plan(make_plan(tmp_path, [task("a", "PROMPT"), task("b", "PROMPT")]))
    opts = rhe.RunOptions(host="codex", bin=str(binary), conditions=("baseline",), price_in=1, price_out=1,
                          max_estimated_total_usd=.000001)
    summary = rhe.execute(plan, opts, tmp_path / "too-small", stream=io.StringIO())
    assert summary["not_started_jobs"] == 2
    assert all(entry["argv"] == ["--version"] for entry in log_entries(log))
    opts.max_estimated_total_usd = 1
    summary = rhe.execute(plan, opts, tmp_path / "unknown", stream=io.StringIO())
    assert summary["completed_jobs"] == 1 and summary["not_started_jobs"] == 1
    assert summary["spent_usd"] is None and summary["cost_complete"] is False
    assert "unknown cost" in summary["stop_reason"]
    assert summary["estimated_budget_is_hard_cap"] is False


def test_native_cap_is_not_rounded_up_and_unknown_spend_uses_reservation(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "synthetic")
    cap = .123456789
    opts = rhe.RunOptions(host="claude", bin="fake", conditions=("baseline",), max_usd_per_task=cap,
                          max_total_usd=cap)
    command = rhe.build_commands(opts, "baseline", tmp_path, tmp_path / "unused")[1]
    assert command[command.index("--max-budget-usd") + 1] == str(cap)
    binary, log = make_fake(tmp_path, FAKE_CLAUDE, {"PROMPT": {"output": "ok", "cost": None}}, "claude")
    opts.bin = str(binary)
    plan = rhe.load_plan(make_plan(tmp_path, [task("a", "PROMPT"), task("b", "PROMPT")]))
    summary = rhe.execute(plan, opts, tmp_path / "out", stream=io.StringIO())
    assert summary["completed_jobs"] == 1 and summary["not_started_jobs"] == 1
    assert summary["accounted_usd"] == pytest.approx(cap, abs=.000001)
    assert summary["spent_usd"] is None and summary["cost_complete"] is False
    assert len(log_entries(log)) == 2


def test_native_estimate_cannot_release_a_hard_budget_reservation(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "synthetic")
    binary, _ = make_fake(tmp_path, FAKE_CLAUDE, {"PROMPT": {"output": "ok", "cost": None}}, "claude")
    opts = rhe.RunOptions(host="claude", bin=str(binary), conditions=("baseline",), max_total_usd=.5,
                          price_in=0, price_out=0)
    plan = rhe.load_plan(make_plan(tmp_path, [task("a", "PROMPT"), task("b", "PROMPT")]))
    summary = rhe.execute(plan, opts, tmp_path / "out", stream=io.StringIO())
    assert summary["completed_jobs"] == 1 and summary["not_started_jobs"] == 1
    assert summary["spent_usd"] is None and summary["accounted_usd"] == .5


@pytest.mark.parametrize("cost", [-1, True, float("nan"), float("inf"), 10**1000])
def test_untrusted_cost_never_becomes_a_valid_charge(cost):
    parsed = rhe.parse_events(json.dumps({"type": "result", "result": "ok", "total_cost_usd": cost}), set())
    assert parsed["cost_usd"] is None and parsed["is_error"] is True


@pytest.mark.parametrize("usage", [{"input_tokens": -1}, {"input_tokens": "bad"},
                                   {"input_tokens": True}, {"input_tokens": 10**1000}])
def test_invalid_usage_is_unknown_and_an_error(usage):
    parsed = rhe.parse_events(json.dumps({"type": "turn.completed", "usage": usage}), set())
    assert parsed["input_tokens"] is None and parsed["is_error"] is True


@pytest.mark.skipif(os.name != "posix", reason="POSIX process-group qualification")
def test_large_prompt_does_not_deadlock_against_full_output_pipes(tmp_path, monkeypatch):
    monkeypatch.setattr(rhe, "MAX_CAPTURE", 4096)
    code = "import os,time; os.write(1,b'x'*1000000); time.sleep(20)"
    start = time.monotonic()
    result = rhe._run_capped([sys.executable, "-c", code], dict(os.environ), tmp_path, "p" * 1_000_000,
                             2, tmp_path / "events", tmp_path / "stderr")
    assert result[2] is True and time.monotonic() - start < 2


def test_run_directory_is_independent_of_task_id_and_checks_containment(tmp_path):
    plan = rhe.load_plan(make_plan(tmp_path, [task("safe.name", "PROMPT")]))
    job = rhe.schedule(plan, rhe.RunOptions(host="cursor", bin="cursor", conditions=("plugin",)))[0]
    assert "safe.name" not in job["run_id"]
    rhe.prepare_output(tmp_path / "out")
    with pytest.raises(ValueError, match="run id"):
        rhe.job_directory(tmp_path / "out", "a/../../escape")
    if os.name == "posix":
        (tmp_path / "out" / "runs").rmdir()
        (tmp_path / "out" / "runs").symlink_to(tmp_path)
        with pytest.raises(ValueError, match="escapes"):
            rhe.job_directory(tmp_path / "out", job["run_id"])


def test_v1_cannot_claim_fingerprintless_v2_acceptance(tmp_path):
    path = make_plan(tmp_path, [task("a", "PROMPT")])
    plan = json.loads(path.read_text())
    plan["acceptance_version"] = 2
    plan["plan_sha256"] = rhe.plan_digest(plan)
    path.write_text(json.dumps(plan))
    with pytest.raises(ValueError, match="v1.*v2"):
        rhe.load_plan(path)


@pytest.mark.parametrize("field,value", [("repeat", True), ("repeat", 1.5), ("max_tasks", 1.5),
                                        ("timeout", True), ("max_turns", 1.5), ("max_total_tokens", 1.5)])
def test_schedule_options_are_typed(field, value):
    opts = rhe.RunOptions(host="claude", bin="fake", conditions=("baseline",))
    setattr(opts, field, value)
    with pytest.raises(ValueError, match="integer"):
        rhe.validate_options(opts)


@pytest.mark.skipif(os.name != "posix", reason="POSIX special files")
def test_private_output_refuses_fifo_without_blocking(tmp_path):
    fifo = tmp_path / "fifo"
    os.mkfifo(fifo)
    start = time.monotonic()
    with pytest.raises((OSError, ValueError)):
        rhe.write_json(fifo, {})
    assert time.monotonic() - start < 1


@pytest.mark.parametrize("skill", ["ai-humanize", "ebook-publisher"])
def test_output_without_executable_checks_is_not_assessed(skill):
    result = rhe.output_check(task("a", "PROMPT", skill=skill), "anything", rhe.graded_skills())
    assert result["status"] == "not_assessed"
    assert result["reason"] == "no_executable_output_check"


def test_literal_only_assessment_is_explicit_and_empty_literals_do_not_pass():
    data = task("a", "PROMPT", skill="ai-humanize", preserve_literals=[""])
    assert rhe.output_check(data, "anything", rhe.graded_skills())["status"] == "not_assessed"
    data["preserve_literals"] = ["EV-1"]
    result = rhe.output_check(data, "EV-1", rhe.graded_skills())
    assert result["status"] == "pass" and result["assessment_scope"] == "pinned_literals_only"
    assert rhe.output_check(data, "missing", rhe.graded_skills())["status"] == "fail"


def test_literal_only_output_cannot_hide_a_followed_canary():
    from grade_output import new_canary
    data = task("a", "PROMPT", skill="ai-humanize", preserve_literals=["EV-1"], canary=new_canary())
    result = rhe.output_check(data, "EV-1 " + data["canary"]["token"], rhe.graded_skills())
    assert result["status"] == "fail" and "INJECTION_FOLLOWED:canary-file" in result["errors"]
    data["preserve_literals"] = []
    assert rhe.output_check(data, "clean text", rhe.graded_skills())["status"] == "not_assessed"


def test_alias_accepts_a_valid_canonical_artifact():
    text = (ROOT / "evals/output/skill-orchestrator/good-council-go.md").read_text()
    result = rhe.output_check(task("a", "PROMPT", skill="skill-orchestrator-multiagent"), text, rhe.graded_skills())
    assert result["status"] == "pass" and result["rubric_skill"] == "skill-orchestrator"


def test_alias_uses_the_canonical_output_rubric():
    alias = "skill-orchestrator-multiagent"
    assert alias in rhe.graded_skills()
    data = task("a", "PROMPT", skill=alias)
    result = rhe.output_check(data, "not a valid orchestrator artifact", rhe.graded_skills())
    assert result["status"] == "fail" and result["rubric_skill"] == "skill-orchestrator"
    assert result["rubric"] == "fail"
    plan = rhe.build_plan(skills=[alias], per_skill=1, negatives_per_skill=0)
    assert "output" in plan["tasks"][0]["checks"]


def test_unassessed_outputs_are_visible_and_excluded_from_rates_and_pairs():
    plugin = _grades("plugin", "model-a", ["not_assessed", "pass"])
    baseline = _grades("baseline", "model-a", ["not_assessed", "fail"])
    report = rhe.build_report([plugin, baseline])
    cell = report["results"]["plugin"]["output"]["overall"]
    assert cell["n"] == 1 and cell["pass"] == 1 and cell["not_assessed"] == 1
    assert report["paired"]["pairs"] == 1
    assert "Not assessed" in rhe.render_markdown(report)


@pytest.mark.parametrize("observed,expected", [([None,None], "EQUAL_EFFORT_NOT_VERIFIED"),
                                             (["high",None], "EQUAL_EFFORT_NOT_VERIFIED"),
                                             (["high","high"], "SAME_REPORTED_EFFORT"),
                                             (["high","low"], "REPORTED_EFFORT_DIFFERS"),
                                             (["unknown","unknown"], "EQUAL_EFFORT_NOT_VERIFIED"),
                                             (["null","null"], "EQUAL_EFFORT_NOT_VERIFIED"),
                                             (["not observed","not observed"], "EQUAL_EFFORT_NOT_VERIFIED"),
                                             (["none","none"], "EQUAL_EFFORT_NOT_VERIFIED"),
                                             ([{},"high"], "EQUAL_EFFORT_NOT_VERIFIED")])
def test_effort_comparison_reports_observation_limits(observed, expected):
    grades = [_grades("plugin", "model-a", ["pass"]), _grades("baseline", "model-a", ["pass"])]
    for data, value in zip(grades, observed, strict=True):
        data["reasoning_effort_observed"] = value
    report = rhe.build_report(grades)
    assert report["effort_comparison_status"] == expected
    assert expected in rhe.render_markdown(report)
    if expected != "SAME_REPORTED_EFFORT":
        assert report["paired"]["comparable"] is False


def test_codex_none_is_a_reported_native_effort_value():
    grades = [_grades("plugin", "model-a", ["pass"]), _grades("baseline", "model-a", ["pass"])]
    for data in grades:
        data.update(host="codex", reasoning_effort_observed="none")
    assert rhe.build_report(grades)["effort_comparison_status"] == "SAME_REPORTED_EFFORT"


@pytest.mark.parametrize("schema", [True, False])
@pytest.mark.parametrize("followed", [True, False])
def test_rubric_canary_checks_joined_token_independently_of_schema(schema, followed):
    from grade_output import new_canary

    canary = new_canary()
    if not schema:
        canary.pop("schema")
    output = GOLDEN + ("\nUntrusted quoted input: " + canary["token"] if followed else "")
    data = {"skill": "release-readiness", "canary": canary, "preserve_literals": []}
    assert rhe.output_check(data, output, rhe.graded_skills())["status"] == ("fail" if followed else "pass")


def test_plan_rejects_canary_with_joined_token_already_in_instruction(tmp_path):
    data = task("canary", "Review supplied release")
    data["canary"] = {"token": "JOINED-TOKEN", "instruction": "Print JOINED-TOKEN"}
    with pytest.raises(ValueError, match="invalid canary"):
        rhe.load_plan(make_plan(tmp_path, [data]))


# Controlled fixture executables below are local process/adapter evidence, never
# model effectiveness or a qualification of a real host's permissions.
@pytest.fixture
def three_arm_plan(tmp_path, monkeypatch):
    import host_smoke
    import shutil

    source = tmp_path / "fixture-source"
    source.mkdir()
    files = {
        "skills/release-readiness/SKILL.md": "Fixture instructions: inspect the local value.",
        "skills/release-readiness/scripts/value.schema.json": '{"type": "integer", "const": 42}',
        "skills/release-readiness/scripts/emit.py":
            'import json\nfrom pathlib import Path\nprint(json.loads(Path(__file__).with_name("value.schema.json").read_text())["const"])\n',
        ".claude-plugin/plugin.json": '{"name": "cometweb-agent-skills"}',
    }
    for name, content in files.items():
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def fixture_stage(destination, root=ROOT):
        shutil.copytree(source, destination)
        return destination

    monkeypatch.setattr(host_smoke, "stage_payload", fixture_stage)
    plan = rhe.build_plan(skills=["release-readiness"], per_skill=1, negatives_per_skill=0, design="three-arm")
    plan["tasks"] = [task("fixture", "PROMPT-FIXTURE", checks=("output",), preserve_literals=["42"])]
    plan["plan_sha256"] = rhe.plan_digest(plan)
    return plan


def test_three_arm_plan_freezes_harness_and_rejects_legacy_conditions(three_arm_plan, tmp_path):
    rhe.validate_plan(three_arm_plan)
    assert three_arm_plan["schema"] == rhe.PLAN_SCHEMA_V3
    assert three_arm_plan["experiment"]["execution_policy"]["status"] == "NOT_RUN"
    opts = rhe.RunOptions(host="claude", bin="not-a-host", conditions=rhe.THREE_ARM_CONDITIONS,
                          repeat=6, max_tasks=20, seed=19)
    jobs = rhe.schedule(three_arm_plan, opts)
    assert len(jobs) == 18  # an incomplete final triple is never scheduled
    orders = [tuple(j["condition"] for j in jobs[i:i + 3]) for i in range(0, 18, 3)]
    assert len(set(orders)) == 6
    assert jobs == rhe.schedule(three_arm_plan, opts)
    assert all(j["experiment"] == three_arm_plan["experiment"] for j in jobs)
    with pytest.raises(ValueError, match="legacy"):
        rhe.schedule(three_arm_plan, rhe.RunOptions(host="claude", bin="x", conditions=rhe.CONDITIONS))
    broken = json.loads(json.dumps(three_arm_plan))
    broken["experiment"]["harness_sha256"] = "0" * 64
    broken["plan_sha256"] = rhe.plan_digest(broken)
    with pytest.raises(ValueError, match="identity changed"):
        rhe.validate_plan(broken)


def test_three_arm_execute_refuses_unenforced_helpers_before_any_host_process(three_arm_plan, tmp_path):
    binary, log = make_fake(tmp_path, FAKE_CLAUDE, {"PROMPT": {"output": "42"}}, "claude")
    opts = rhe.RunOptions(host="claude", bin=str(binary), conditions=rhe.THREE_ARM_CONDITIONS, max_tasks=3)
    out = tmp_path / "blocked"
    result = rhe.execute(three_arm_plan, opts, out)
    assert result["execution_status"] == "NOT_RUN"
    assert result["not_run_jobs"] == 3
    assert not log.exists()
    records = [json.loads(p.read_text()) for p in out.glob("runs/*/record.json")]
    assert len(records) == 3
    assert all(r["not_run_reason"] == "ENFORCED_HELPER_BOUNDARY_UNAVAILABLE" for r in records)
    assert all(r["resources"]["input_tokens"] is None and r["task_outcome_status"] == "not_assessed" for r in records)
    grades = rhe.grade_run(out)
    report = rhe.build_report([grades])
    assert grades["counts"] == {"completed": 0, "errors": 0, "not_run": 3}
    assert len(report["run_results"]) == 3
    assert all(c["pairs"] == 0 and c["exact_p_two_sided"] is None for c in report["matched_comparisons"])
    manifest = json.loads((out / "manifest.json").read_text())
    manifest["experiment"]["harness_sha256"] = "0" * 64
    (out / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="manifest differs"):
        rhe.grade_run(out)


def test_three_arm_local_fixture_really_executes_identical_helper_and_reads_only_skill_in_c(
        three_arm_plan, tmp_path):
    import host_smoke

    binary = tmp_path / "fixture-host"
    binary.write_text(f'''#!{sys.executable}
import json, pathlib, subprocess, sys
sys.stdin.read()
root = pathlib.Path.cwd() / "bundled/skills/release-readiness"
helper = root / "scripts/emit.py"
instructions = root / "SKILL.md"
value = subprocess.check_output([sys.executable, str(helper)], text=True).strip() if helper.exists() else None
result = {{"value": value, "instructions": instructions.read_text() if instructions.exists() else None}}
print(json.dumps({{"type": "result", "result": json.dumps(result)}}))
''')
    binary.chmod(0o700)
    opts = rhe.RunOptions(host="claude", bin=str(binary), conditions=rhe.THREE_ARM_CONDITIONS, max_tasks=3)
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    stage = host_smoke.stage_payload(scratch / "stage")
    out = tmp_path / "fixture-results"
    rhe.prepare_output(out)
    observations = {}
    receipts = {}
    for job in rhe.schedule(three_arm_plan, opts):
        record = rhe.run_job(job, opts, rhe.HOSTS["claude"], stage, out, scratch, {"release-readiness"})
        run_dir = out / "runs" / job["run_id"]
        observations[job["condition"]] = json.loads((run_dir / "output.md").read_text())
        receipts[job["condition"]] = record
        assert record["status"] == "executed"
        assert record["model"] is None and record["resources"]["input_tokens"] is None
        assert record["metadata_status"]["model"] == "unavailable"
        assert record["receipt"]["files"]["output.md"]["sha256"] == rhe.sha256((run_dir / "output.md").read_bytes())
    assert observations["native"] == {"value": None, "instructions": None}
    assert observations["tools"] == {"value": "42", "instructions": None}
    assert observations["skill"] == {"value": "42", "instructions": "Fixture instructions: inspect the local value."}
    assert receipts["tools"]["bundled_tools_sha256"] == receipts["skill"]["bundled_tools_sha256"]
    commands = [r["argv"] for r in receipts.values()]
    assert {c[c.index("--tools") + 1] for c in commands} == {"Read,Glob,Grep,Bash,Skill"}


def test_three_arm_matches_within_cohort_and_never_overwrites_duplicates():
    def rows():
        return [{"run_id": c, "task_id": "case", "repeat": 0, "condition": c, "model": "fixture-model",
                 "skill": "release-readiness", "run_status": "executed", "checks": {"output": {"status": "pass"}}}
                for c in rhe.THREE_ARM_CONDITIONS]
    grades = {"results": rows()}
    comparisons = rhe.matched_comparisons([grades])
    assert len(comparisons) == 3 and all(c["pairs"] == 1 for c in comparisons)
    # Combining separate one-arm cohorts must not invent same-case matches.
    assert all(c["pairs"] == 0 for c in rhe.matched_comparisons([
        {"results": [rows()[0]]}, {"results": [rows()[1]]}]))
    grades["results"].append(dict(grades["results"][0]))
    native_tools = rhe.matched_comparisons([grades])[0]
    assert native_tools["pairs"] == 0 and native_tools["ambiguous_cases"] == 1
    grades = {"results": rows()}
    grades["results"][1]["model"] = None
    assert rhe.matched_comparisons([grades])[0]["pairs"] == 0


def test_three_arm_partial_failure_and_schedule_stop_keep_every_receipt(three_arm_plan, tmp_path, monkeypatch):
    # Inject fixture readiness only; this does not qualify or enable a native backend.
    frozen_policy = rhe.three_arm_execution_policy("all")
    monkeypatch.setattr(rhe, "three_arm_execution_policy", lambda host:
                        frozen_policy if host == "all" else {"status": "READY", "scope": "fixture_only"})
    binary, _ = make_fake(tmp_path, FAKE_CLAUDE,
                          {"PROMPT": {"output": "partial 42", "exit": 23}}, "claude")
    opts = rhe.RunOptions(host="claude", bin=str(binary), conditions=rhe.THREE_ARM_CONDITIONS,
                          max_tasks=3, max_consecutive_errors=1)
    out = tmp_path / "failure"
    summary = rhe.execute(three_arm_plan, opts, out)
    assert summary["error_jobs"] == 1 and summary["not_run_jobs"] == 2 and summary["not_started_jobs"] == 2
    records = [json.loads(p.read_text()) for p in sorted(out.glob("runs/*/record.json"))]
    assert len(records) == 3
    failure = next(r for r in records if r["status"] == "error")
    assert failure["receipt"]["output_status"] == "partial_or_unavailable"
    assert "output.md" in failure["receipt"]["files"]
    assert all(r["resources"]["input_tokens"] is None for r in records if r["status"] == "not_run")
    assert rhe.grade_run(out)["counts"] == {"completed": 0, "errors": 1, "not_run": 2}


def test_three_arm_version_probe_failure_keeps_terminal_records(three_arm_plan, tmp_path, monkeypatch):
    frozen_policy = rhe.three_arm_execution_policy("all")
    monkeypatch.setattr(rhe, "three_arm_execution_policy", lambda host:
                        frozen_policy if host == "all" else {"status": "READY", "scope": "fixture_only"})
    binary = tmp_path / "failing-version"
    binary.write_text(f"#!{sys.executable}\nimport sys\nprint('partial version')\nsys.exit(23)\n")
    binary.chmod(0o700)
    opts = rhe.RunOptions(host="claude", bin=str(binary), conditions=rhe.THREE_ARM_CONDITIONS, max_tasks=3)
    out = tmp_path / "version-failure"
    summary = rhe.execute(three_arm_plan, opts, out)
    assert summary["error_jobs"] == 3 and summary["host_version"] is None
    assert (out / "host-version.stdout.txt").read_text() == "partial version\n"
    records = [json.loads(p.read_text()) for p in out.glob("runs/*/record.json")]
    assert len(records) == 3 and all(r["error_reason"] == "HOST_VERSION_PROBE_FAILED" for r in records)
    assert all(r["resources"]["cost_usd"] is None for r in records)


def test_three_arm_cli_dry_run_never_invokes_binary(three_arm_plan, tmp_path, capsys):
    plan_path = tmp_path / "three-arm.json"
    plan_path.write_text(json.dumps(three_arm_plan))
    binary, log = make_fake(tmp_path, FAKE_CLAUDE, {"PROMPT": {"output": "42"}}, "claude")
    assert rhe.main(["run", "--plan", str(plan_path), "--host", "claude", "--bin", str(binary),
                     "--condition", "three-arm", "--max-tasks", "3"]) == 0
    printed = capsys.readouterr().out
    assert "DRY RUN" in printed and "native,tools,skill" in printed and "bytes/4" in printed
    assert not log.exists()


def test_three_arm_process_start_failure_keeps_existing_job_receipt(three_arm_plan, tmp_path, monkeypatch):
    frozen_policy = rhe.three_arm_execution_policy("all")
    monkeypatch.setattr(rhe, "three_arm_execution_policy", lambda host:
                        frozen_policy if host == "all" else {"status": "READY", "scope": "fixture_only"})
    binary, _ = make_fake(tmp_path, FAKE_CLAUDE, {"PROMPT": {"output": "42"}}, "claude")
    original = rhe._run_capped

    def fail_task(argv, *args, **kwargs):
        if argv[-1] != "--version":
            raise PermissionError("fixture process denied")
        return original(argv, *args, **kwargs)

    monkeypatch.setattr(rhe, "_run_capped", fail_task)
    opts = rhe.RunOptions(host="claude", bin=str(binary), conditions=rhe.THREE_ARM_CONDITIONS,
                          max_tasks=3, max_consecutive_errors=1)
    out = tmp_path / "start-failure"
    result = rhe.execute(three_arm_plan, opts, out)
    assert result["error_jobs"] == 1 and result["not_run_jobs"] == 2
    records = [json.loads(p.read_text()) for p in out.glob("runs/*/record.json")]
    failure = next(r for r in records if r["status"] == "setup_error")
    assert failure["error_type"] == "PermissionError"
    assert failure["receipt"]["files"]["prompt.txt"]["sha256"]
    assert failure["resources"]["input_tokens"] is None
