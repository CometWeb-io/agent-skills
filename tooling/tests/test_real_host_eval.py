"""tooling/real_host_eval.py: plan, dry run, isolated execution, grading and the scorecard.

No real host is started here. The host binaries are small scripts written into a
temp directory that log how they were called and print canned transcripts, so the
adapter, the isolation, the budget caps and the grading are all exercised offline.
"""

from __future__ import annotations

import io
import json
import os
import stat
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tooling"))

import real_host_eval as rhe  # noqa: E402

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
out = argv[argv.index("--output-last-message") + 1]
if spec.get("skill"):
    print(json.dumps({{"type": "item.completed", "item": {{"type": "command_execution",
        "command": "sed -n 1,200p " + os.environ["CODEX_HOME"] + "/plugins/cache/skills/" + spec["skill"] + "/SKILL.md"}}}}))
print(json.dumps({{"type": "item.completed", "item": {{"type": "agent_message", "text": spec["output"]}}}}))
print(json.dumps({{"type": "turn.completed", "usage": {{"input_tokens": 1000, "cached_input_tokens": 0, "output_tokens": 200}}}}))
open(out, "w").write(spec["output"])
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
    plan = {"schema": rhe.PLAN_SCHEMA, "repo_version": "0.0.0", "sources": {}, "excluded_sources": [],
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
    record = next(json.loads(p.read_text()) for p in out.glob("runs/*pos/record.json"))
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
    assert summary["spent_usd"] == pytest.approx(1.0)
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
    with pytest.raises(ValueError, match="reports no cost"):
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
    assert report["paired"]["comparable"] is True
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
