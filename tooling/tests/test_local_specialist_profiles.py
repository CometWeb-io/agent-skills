"""Functional qualification of local profiles; no claim of model behavior."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "specialist-profiles"
SCRIPTS = ROOT / "skills/skill-orchestrator/scripts"
BUILDER = ROOT / "skills/skill-orchestrator-multiagent/scripts/orchestrate_multiagent_kernel.py"
SPEC = importlib.util.spec_from_file_location("local_profile_tests", SCRIPTS / "specialist_profiles.py")
profiles = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(profiles)
IDS = tuple(profiles.OWNERS)


def example(pid):
    return json.loads((EXAMPLES / pid / "examples/draft.json").read_text())


def builder(goal, *args, path=BUILDER):
    return subprocess.run([sys.executable, str(path), goal, "--json", *args], capture_output=True, text=True, check=False)


@pytest.mark.parametrize("pid", IDS)
def test_draft_contract_keeps_unknowns_and_does_not_authorize(pid):
    result = profiles.validate_sidecar(example(pid), ROOT)
    assert result["accepted"] is True
    assert result["execution_authorized"] is False


@pytest.mark.parametrize("pid", IDS)
@pytest.mark.parametrize("mutation", ["owner", "authorization", "extra", "status", "unknowns", "evidence_duplicate", "evidence_kind", "result_extra", "profile", "nonfinite"])
def test_rejects_contract_changes(pid, mutation):
    value = example(pid)
    if mutation == "owner": value["owner_skill"] = "ai-council"
    elif mutation == "authorization": value["execution_authorized"] = True
    elif mutation == "extra": value["downstream_verdict"] = "GO"
    elif mutation == "status": value["status"] = "READY"
    elif mutation == "unknowns": value["status"] = "REVIEWABLE"
    elif mutation == "evidence_duplicate": value["evidence"].append(copy.deepcopy(value["evidence"][0]))
    elif mutation == "evidence_kind": value["evidence"][0]["kind"] = "LIVE_VERIFIED"
    elif mutation == "result_extra": value["result"]["auto_launch"] = True
    elif mutation == "profile": value["profile_id"] = "../ai-council"
    else: value["result"]["extra"] = float("nan")
    assert profiles.validate_sidecar(value, ROOT)["accepted"] is False


@pytest.mark.parametrize("pid", ["conversion-audit", "activation-onboarding", "sop-documentation"])
@pytest.mark.parametrize("verification", [{"method":"inspect"}, True, "", "   "])
def test_verification_type_and_nonblank(pid, verification):
    value = example(pid)
    rows = value["result"].get("observations", value["result"].get("steps"))
    rows[0]["verification"] = verification
    assert profiles.validate_sidecar(value, ROOT)["accepted"] is False


@pytest.mark.parametrize("kind", ["FRAMEWORK", "HYPOTHESIS"])
@pytest.mark.parametrize("pid", IDS)
def test_frameworks_cannot_prove_product_data(pid, kind):
    value = example(pid)
    value["evidence"][0]["kind"] = kind
    result = value["result"]
    if pid == "experiment-design":
        result["baseline_rate"]=.1; result["parameter_source_ids"]["baseline_rate"]=["S1"]
    elif pid == "activation-onboarding":
        result.update(activation_rate=0.2, activation_source_ids=["S1"])
    assert profiles.validate_sidecar(value, ROOT)["accepted"] is False


@pytest.mark.parametrize("pid", IDS)
def test_dangling_refs_fail_closed(pid):
    value = example(pid)
    result = value["result"]
    if pid == "conversion-audit": result["observations"][0]["source_ids"] = ["missing"]
    elif pid == "sop-documentation": result["steps"][0]["source_ids"] = ["missing"]
    elif pid == "experiment-design": result["parameter_source_ids"]["alpha"] = ["missing"]
    else: result["steps"][0]["source_ids"] = ["missing"]
    assert profiles.validate_sidecar(value, ROOT)["accepted"] is False


@pytest.mark.parametrize("baseline", [True, "0.2", -0.1, 1.1, float("inf"), float("nan")])
def test_baseline_invalid_numeric_types(baseline):
    value = example("conversion-audit")
    value["result"].update(baseline_rate=baseline, baseline_source_ids=["S1"])
    assert profiles.validate_sidecar(value, ROOT)["accepted"] is False


def test_unsupported_lift_and_permission_checkpoint():
    value = example("conversion-audit")
    value["result"]["hypotheses"][0]["expected_lift"] = 0.4
    assert profiles.validate_sidecar(value, ROOT)["accepted"] is False
    value = example("sop-documentation")
    value["result"]["steps"][0]["risk"] = "EXTERNAL_MUTATION"
    assert profiles.validate_sidecar(value, ROOT)["accepted"] is False
    value["result"]["steps"][0]["approval_requirement"] = "Action-specific user authorization before executing"
    assert profiles.validate_sidecar(value, ROOT)["accepted"] is True
    assert profiles.validate_sidecar(value, ROOT)["execution_authorized"] is False


def test_incomplete_experiment_cannot_be_reviewable():
    value = example("experiment-design")
    value.update(status="REVIEWABLE", unknowns=[])
    assert profiles.validate_sidecar(value, ROOT)["accepted"] is False
    value["result"].update(baseline_rate=.1, sample_size_per_variant=12000, mde_absolute=.02,
                           alpha=.05, power=.8, parameter_source_ids={key:["S1"] for key in value["result"]["parameter_source_ids"]}, method="FIXED_HORIZON",
                           randomization_unit="unique demo visitor", stopping_rule="After declared sample/window; no optional stopping", instrumentation="VERIFIED")
    # Supplied numbers are not validated calculations; accepted means internally complete only.
    assert profiles.validate_sidecar(value, ROOT)["accepted"] is True


@pytest.mark.parametrize("goal,expected", [
    ("Audyt CRO formularza", ["conversion-audit"]),
    ("Zaplanuj A/B test konwersji", ["conversion-audit","experiment-design"]),
    ("Post-signup user activation", ["activation-onboarding"]),
    ("Udokumentuj SOP eksportu lokalnego", ["sop-documentation"]),
    ("Przetłumacz cytat: CRO i SOP", []),
    ("Translate \"post-signup CRO\"", []),
    ("Employee onboarding checklist", []),
    ("Support triage only", []),
    ("Sformatuj cytat:\n> CRO SOP A/B", []),
    ("Zsumuj dwa i dwa", []),
])
def test_intent_routing_does_not_dispatch(goal, expected):
    assert profiles.select(goal, ROOT) == expected


@pytest.mark.parametrize("pid", IDS)
def test_generator_binds_one_owner_and_pinned_sidecar(pid):
    result = builder("Prepare the scoped demo artifact", "--specialist-profile", pid)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert len(payload["subagent_tasks"]) == 1
    task = payload["subagent_tasks"][0]
    assert task["skill"] == profiles.OWNERS[pid]
    assert task["specialist_profile"]["id"] == pid
    assert str(ROOT / "skills" / task["skill"] / "SKILL.md") in task["prompt"]
    assert Path(task["profile_output_schema"]).is_file()
    assert "does not authorize execution" in task["prompt"]


@pytest.mark.parametrize("flag", ["--with-prd-handoff", "--with-capability-packs"])
def test_unqualified_profile_pipeline_composition_is_rejected(flag):
    result = builder("demo SOP", "--specialist-profile", "sop-documentation", flag)
    assert result.returncode != 0
    assert "not qualified" in result.stderr or "require trusted context" in result.stderr


@pytest.mark.parametrize("goal", ["evidence then council", "weekly", "web app audit", "audit then release", "only research", "two plus two"])
def test_default_plan_and_tasks_unchanged(goal):
    old = json.loads((ROOT / "tooling/tests/fixtures/profile_default_tasks.json").read_text())["cases"][goal]
    assert json.loads(builder(goal).stdout) == old


@pytest.mark.parametrize("mutation", ["content", "license", "schema", "inventory", "owner", "path", "provenance"])
def test_tampering_prevents_task_attachment(tmp_path, mutation):
    clone = tmp_path / "pilot"
    shutil.copytree(ROOT / "specialist-profiles", clone / "specialist-profiles")
    shutil.copytree(ROOT / "registry", clone / "registry")
    resources = profiles._local_module(ROOT, "runtime_sources")
    for owner in resources.SKILLS:
        shutil.copytree(ROOT / "skills" / owner, clone / "skills" / owner, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    shutil.copytree(ROOT / "protocol", clone / "protocol")
    plan = profiles.plan_for_profile("CRO demo", "conversion-audit", clone)
    reg = clone / "registry/specialist-profiles.json"
    data = json.loads(reg.read_text())
    selected = data["profiles"][0]
    if mutation in {"content", "license", "schema"}:
        key = {"content":"entrypoint", "license":"license_file", "schema":"output_schema"}[mutation]
        p = clone / selected[key]
        p.write_text(p.read_text() + "changed")
    elif mutation == "inventory": selected["files"].pop(selected["entrypoint"])
    elif mutation == "owner": selected["owner_skill"] = "ai-council"
    elif mutation == "path": selected["entrypoint"] = "../outside/SKILL.md"
    else: selected["claim_class"] = "OBSERVED"
    reg.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        profiles.attach_task({"skill":"web-app-auditor","prompt":"demo"}, plan, clone)


def test_changed_plan_pointer_does_not_bind_another_owner():
    plan = profiles.plan_for_profile("CRO demo", "conversion-audit", ROOT)
    plan["specialist_profile"]["source_commit"] = "0" * 40
    with pytest.raises(ValueError): profiles.attach_task({"skill":"web-app-auditor","prompt":"demo"}, plan, ROOT)
    plan = profiles.plan_for_profile("CRO demo", "conversion-audit", ROOT)
    with pytest.raises(ValueError): profiles.attach_task({"skill":"ai-council","prompt":"demo"}, plan, ROOT)
