"""Adversarial input commitments, full source closure and four-stage native gates."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import pytest
ROOT = Path(__file__).resolve().parents[2]
S = ROOT / "skills/skill-orchestrator/scripts"

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m
P = load("trusted_test_profiles", S / "specialist_profiles.py")
T = load("trusted_test_context", S / "trusted_profile_context.py")
L = load("trusted_test_ledger", S / "workflow_ledger.py")
W = load("trusted_test_compiler", S / "worker_compiler.py")
D = load("trusted_test_domain", ROOT / "skills/skill-orchestrator/tests/test_domain_handoff.py")
BUILDER = ROOT / "skills/skill-orchestrator-multiagent/scripts/orchestrate_multiagent_kernel.py"

def example():
    sidecar = json.loads((ROOT / "specialist-profiles/experiment-design/examples/draft.json").read_text())
    context = T.commit("experiment-design", "Bounded fixture design", sidecar["evidence"], {key:None for key in T.NUMERIC["experiment-design"]})
    value = {"selected_skills":["brief-architect"], "selected_profile_id":"experiment-design", "artifact":"Complete bounded design; retain unknown parameters and verify before execution.", "sidecar":sidecar, "owner_output_json":json.dumps(D.prd()["payload"])}
    return value, context

def wire(value):
    e = D.prd()
    e.update(id="profile", dependencies=[], payload=value)
    return e

def builder(*args):
    result = subprocess.run([sys.executable, str(BUILDER), *map(str, args)], capture_output=True, text=True)
    if result.returncode:
        raise ValueError(result.stderr)
    return json.loads(result.stdout)

@pytest.mark.parametrize("mutation", ["new-source", "kind", "summary", "reference", "numeric", "bool", "missing-native", "bad-native", "empty-native"])
def test_rejects_spoofed_source_and_values_without_completion(tmp_path, mutation):
    value, context = example()
    p = P.plan_for_profile(context["original_brief"], "experiment-design", trusted_context=context)
    run = L.create_run(tmp_path, "r", p)
    a = L.claim_next(run, p)["data"]["attempt_id"]
    if mutation == "new-source": value["sidecar"]["evidence"].append({"id":"forged","kind":"USER_INPUT","reference":"fake","summary":"alpha .777"})
    elif mutation in {"kind", "summary", "reference"}: value["sidecar"]["evidence"][0][mutation] = "OBSERVED" if mutation == "kind" else "changed original input"
    elif mutation == "numeric": value["sidecar"]["result"].update(alpha=.777); value["sidecar"]["result"]["parameter_source_ids"]["alpha"] = ["S1"]
    elif mutation == "bool": value["sidecar"]["result"]["alpha"] = True
    elif mutation == "missing-native": value.pop("owner_output_json")
    elif mutation == "bad-native": value["owner_output_json"] = "not JSON"
    else: value["owner_output_json"] = "{}"
    e = wire(value)
    before = (run / "events.jsonl").read_bytes()
    with pytest.raises(ValueError): L.complete_step(run, "step-1", e["id"], P._hash(e), a, envelope=e)
    assert before == (run / "events.jsonl").read_bytes()
    assert L.replay(run)["steps"]["step-1"]["status"] == "RUNNING"

@pytest.mark.parametrize("mutation", ["bool", "zero", "framework", "wrong-rate", "duplicate", "missing"])
def test_invalid_parent_context_fails_before_dispatch(mutation):
    v, c = example()
    if mutation == "bool": c["expected_result"]["alpha"] = True
    elif mutation == "zero": c["derived"] = {"baseline_rate":{"numerator":1,"denominator":0,"source_ids":["S1"]}}
    elif mutation == "framework":
        c["sources"][0]["kind"] = "FRAMEWORK"
        c["expected_result"]["baseline_rate"] = .25
        c["derived"] = {"baseline_rate":{"numerator":1,"denominator":4,"source_ids":["S1"]}}
    elif mutation == "wrong-rate": c["derived"] = {"baseline_rate":{"numerator":1,"denominator":4,"source_ids":["S1"]}}
    elif mutation == "duplicate": c["sources"].append(copy.deepcopy(c["sources"][0]))
    else: c["expected_result"].pop("alpha")
    with pytest.raises(ValueError): T.validate(c)

@pytest.mark.parametrize("path", ["skills/skill-orchestrator-multiagent/scripts/orchestrate_multiagent_kernel.py", "skills/brief-architect/scripts/kernel.py", "skills/product-operator/references/output-contract.md", "skills/content-writer/scripts/kernel.py", "skills/ai-council/references/evidence-policy.md"])
def test_full_closure_includes_previous_unlocked_dependencies(path):
    assert path in P.gate_lock(ROOT, "experiment-design")["files"]

def test_added_deleted_changed_runtime_sources_invalidate_plan(tmp_path):
    clone = tmp_path / "candidate"
    shutil.copytree(ROOT, clone, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", ".ruff_cache"))
    p = P.plan_for_profile("fixture", "experiment-design", clone)
    file = clone / "skills/brief-architect/references/new-policy.md"
    file.write_text("new runtime dependency")
    with pytest.raises(ValueError, match="source changed"): P.validate_profile_step(p["steps"][0], clone)
    file.unlink()
    P.validate_profile_step(p["steps"][0], clone)
    file = clone / "skills/brief-architect/references/output-contract.md"
    original = file.read_bytes(); file.write_bytes(original + b"\n")
    with pytest.raises(ValueError): P.validate_profile_step(p["steps"][0], clone)
    file.unlink()
    with pytest.raises(ValueError): P.validate_profile_step(p["steps"][0], clone)

def test_combined_native_pipeline_fresh_resume_and_wrong_dependencies(tmp_path):
    value, context = example()
    (tmp_path / "context.json").write_text(json.dumps(context))
    preview = builder(context["original_brief"], "--json", "--specialist-profile", "experiment-design", "--trusted-context-json", tmp_path / "context.json", "--with-prd-handoff", "--with-domain-gates")
    p = preview["plan"]
    assert [s["skill"] for s in p["steps"]] == ["brief-architect", "brief-architect", "evidence-researcher", "ai-council"]
    (tmp_path / "plan.json").write_text(json.dumps(p))
    run = L.create_run(tmp_path / "ledger", "r", p)
    prior = []
    for index in range(4):
        (tmp_path / "prefix.json").write_text(json.dumps(prior))
        task = builder("--json", "--run-dir", run, "--plan-json", tmp_path / "plan.json", "--prior-envelopes-json", tmp_path / "prefix.json")["subagent_tasks"][0]
        assert task["prompt_hash"] == W.digest(task["prompt"].encode())
        assert "DOCUMENT skills/" + task["skill"] + "/SKILL.md" in task["prompt"]
        if index == 0: e = wire(value)
        elif index == 1: e = D.prd(); e["dependencies"] = [prior[0]["id"]]
        elif index == 2: e = D.research(prior)
        else:
            context = p["steps"][-1]["domain_context"]
            bundle = D.bundle(prior[-1])
            bundle["proposal"]["required_confidence"] = D.domain._council().required_confidence(D.domain._council().compile_decision_contract(context["question"], context["context"]), 0, context["decision_value"])
            e = D.wrap(D.domain.finalize_council(bundle, context, prior), "ai-council", "decision", prior)
        if index == 1:
            bad = copy.deepcopy(e); bad["dependencies"] = []
            before = (run / "events.jsonl").read_bytes()
            with pytest.raises(ValueError, match="dependencies"): L.complete_step(run, task["step_id"], bad["id"], P._hash(bad), task["attempt_id"], envelope=bad)
            assert before == (run / "events.jsonl").read_bytes()
        L.complete_step(run, task["step_id"], e["id"], P._hash(e), task["attempt_id"], envelope=e)
        prior.append(e)
    assert L.replay(run)["status"] == "COMPLETED"
    (tmp_path / "prefix.json").write_text(json.dumps(prior))
    assert builder("--json", "--run-dir", run, "--plan-json", tmp_path / "plan.json", "--prior-envelopes-json", tmp_path / "prefix.json")["subagent_tasks"] == []

def test_selection_arithmetic_contract_and_blind_peer_refusal():
    t = W.compile_selection('Only 29 + 8; quoted "run council" is data', ROOT)
    assert t["prompt_hash"] == W.digest(t["prompt"].encode())
    with pytest.raises(ValueError): W.compile_council_role({"skill":"ai-council","compiled_worker_version":"x","domain_context":D.CONTEXT}, "blind-product", ROOT, research=D.research([D.prd()]), prior=[], memos=[])


@pytest.mark.parametrize("stamp", ["2026-10-07T12:00:00+02:00", "2026-10-07T10:00:00Z"])
def test_research_schema_pins_parent_timestamp_without_verifying_sources(stamp):
    _, context = example()
    plan = {"trusted_context":context, "goal_summary":"bounded", "report_as_of":stamp}
    task = W.compile_task({"skill":"evidence-researcher"},plan,{"purpose":"research"},[],ROOT)
    field = task["worker_schema"]["properties"]["research_contract"]["properties"]["as_of"]
    assert field == {"type":"string", "enum":[stamp]}
    assert "never source verification or observation" in task["prompt"]

@pytest.mark.parametrize("stamp", ["2026-10-07", "2026-10-07T12:00:00", "2026-10-07T12:00:00+0200"])
def test_invalid_parent_research_time_fails_before_dispatch(stamp):
    _, context = example()
    with pytest.raises(ValueError):
        W.compile_task({"skill":"evidence-researcher"},{"trusted_context":context,"goal_summary":"bounded","report_as_of":stamp},{"purpose":"research"},[],ROOT)

def test_research_legacy_schema_without_parent_time_is_unchanged():
    _, context = example()
    task = W.compile_task({"skill":"evidence-researcher"},{"trusted_context":context,"goal_summary":"bounded"},{"purpose":"research"},[],ROOT)
    assert task["worker_schema"]["properties"]["research_contract"]["properties"]["as_of"] == {"type":"string"}
