"""These are runner-contract/unit tests with synthetic responses, NOT model evaluations."""
import json
import subprocess
import sys
from pathlib import Path
import pytest
TOOLS=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(TOOLS))
from run_model_evals import CONDITIONS, execute, prepare, run, validate_response, validate_suite
from openai_eval_runner import build_request, convert_response


def response(**changes):
    value={"schema":"cometweb.eval-response/v1","status":"completed","execution_kind":"mock","model":"synthetic-test-model","host":"synthetic-test-host","response_id":"mock-id","output":"Synthetic text 20%","usage":{"input_tokens":1,"output_tokens":2},"tool_trace":[],"capabilities":{"tools":False}}
    value.update(changes)
    return value


def case():
    return {"id":"fixture-case","skill":"demo","prompt":"Edit this sentence.","fixture":{"text":"20% may help"},"rubric":["Preserve uncertainty"],"preserve_literals":["20%"]}


@pytest.fixture
def roots(tmp_path):
    roots=[]
    for label in ("current","candidate"):
        root=tmp_path/label
        source=root/"skills/demo"
        source.mkdir(parents=True)
        (source/"SKILL.md").write_text("Synthetic "+label+" instructions")
        roots.append(root)
    return tuple(roots)


def test_no_skill_baseline_does_not_receive_skill_instructions(roots):
    baseline=prepare(case(),"no_skill",*roots,256)
    current=prepare(case(),"current",*roots,256)
    candidate=prepare(case(),"candidate",*roots,256)
    assert baseline["instructions"] == {}
    assert current["instructions"] != candidate["instructions"]
    assert baseline["prompt"] == current["prompt"] == candidate["prompt"]
    assert baseline["fixture"] == current["fixture"] == candidate["fixture"]


def test_mock_does_not_count_as_model_run():
    with pytest.raises(ValueError):
        validate_response(response())
    validate_response(response(),allow_mock=True)


@pytest.mark.parametrize("changes", [{"status":"incomplete"},{"output":""},{"response_id":None},{"model":""},{"usage":{"input_tokens":None}},{"usage":{"input_tokens":True}},{"usage":{"input_tokens":-1}},{"tool_trace":[{"tool":"invented"}]}])
def test_malformed_or_contradictory_runner_records_fail(changes):
    with pytest.raises(ValueError):
        validate_response(response(**changes),allow_mock=True)


def test_real_process_runner_contract_with_explicit_mock_label(tmp_path):
    script=tmp_path/"mock_runner.py"
    script.write_text("import json,sys\nrequest=json.load(sys.stdin)\nassert request['schema']=='cometweb.eval-request/v1'\nprint("+repr(json.dumps(response()))+")\n")
    data,elapsed=execute({"schema":"cometweb.eval-request/v1","capabilities":{"tools":False}},[sys.executable,str(script)],10,allow_mock=True)
    assert data["execution_kind"] == "mock" and elapsed >= 0
    with pytest.raises(ValueError):
        execute({"schema":"cometweb.eval-request/v1","capabilities":{"tools":False}},[sys.executable,str(script)],10)


def test_runner_failure_is_not_an_empty_success(tmp_path):
    with pytest.raises(subprocess.CalledProcessError):
        execute({},[sys.executable,"-c","raise SystemExit(2)"],10)


def test_run_budget_blocks_before_any_runner_call(roots,tmp_path):
    suite={"schema":"cometweb.model-evals/v1","cases":[case()]}
    with pytest.raises(ValueError,match="budget"):
        run(suite,*roots,["not-called"],tmp_path/"output",max_runs=2)
    assert not (tmp_path/"output").exists()


def test_identical_versions_are_not_an_improvement_experiment(roots,tmp_path):
    suite={"schema":"cometweb.model-evals/v1","cases":[case()]}
    with pytest.raises(ValueError,match="identical"):
        run(suite,roots[0],roots[0],["not-called"],tmp_path/"output")


def test_interrupted_execution_retains_error_and_unrun_counts(roots,tmp_path):
    suite={"schema":"cometweb.model-evals/v1","cases":[case()]}
    result=run(suite,*roots,[sys.executable,"-c","raise SystemExit(2)"],tmp_path/"output")
    assert result["planned_runs"] == 3 and result["completed_runs"] == 0 and result["errors"] == 1
    assert result["comparison_status"] == "incomplete_or_unmatched"
    assert result["quality_verdict"] == "pending_human_review"
    assert (tmp_path/"output/records.json").exists()


def test_suite_has_16_real_prompts_but_no_claimed_model_runs():
    suite=json.loads((TOOLS.parent/"evals/model/suite.json").read_text())
    assert len(validate_suite(suite)) == 16
    proc=subprocess.run([sys.executable,str(TOOLS/"run_model_evals.py")],capture_output=True,text=True,check=True)
    record=json.loads(proc.stdout)
    assert record["status"] == "not_run" and record["model_calls"] == 0


def test_api_adapter_is_stateless_and_does_not_enable_tools():
    request={"schema":"cometweb.eval-request/v1","prompt":"task","fixture":{"text":"data"},"instructions":{},"capabilities":{"tools":False},"max_output_tokens":256}
    body=build_request(request,"configured-model-id")
    assert body["store"] is False
    assert "tools" not in body and "previous_response_id" not in body and "conversation" not in body
    assert "instructions" not in body


def test_text_adapter_refuses_tool_benchmark():
    with pytest.raises(ValueError):
        build_request({"schema":"cometweb.eval-request/v1","capabilities":{"tools":True}},"model")


def test_api_adapter_preserves_incomplete_and_unknown_usage():
    result=convert_response({"status":"incomplete","output":[],"usage":None})
    assert result["status"] == "incomplete" and result["usage"] == {} and result["output"] == ""


def test_missing_credentials_exit_without_network(monkeypatch):
    import openai_eval_runner as adapter
    monkeypatch.delenv("OPENAI_API_KEY",raising=False)
    monkeypatch.delenv("COMETWEB_EVAL_MODEL",raising=False)
    monkeypatch.setattr(adapter.urllib.request,"urlopen",lambda *_a,**_k:pytest.fail("network must not run"))
    assert adapter.main() == 2
