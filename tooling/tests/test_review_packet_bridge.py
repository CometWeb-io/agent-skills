"""Synthetic in-process runner fixtures. No provider or host calls are performed."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import build_review_packets as bridge
import package_skill
import run_model_evals as runner
import review_skill_evals as review


def records_for(suite,requests):
    result=[]
    for index,(key,request) in enumerate(requests.items()):
        cid,condition=key
        output=f"Synthetic conformance response {index}; NOT a model call"
        response={"schema":"cometweb.eval-response/v1","status":"completed", "execution_kind":"model",
                  "model":"synthetic-label","host":"synthetic-host","response_id":f"synthetic-{index}",
                  "output":output,"usage":{},"tool_trace":[],"capabilities":request["capabilities"]}
        result.append({"case":cid,"repeat":0,"condition":condition,"status":"executed","response":response,
                       "input_sha256":package_skill.digest(package_skill.canonical(request)),
                       "output_sha256":hashlib.sha256(output.encode()).hexdigest(),"elapsed_seconds":0.02,
                       "blind_id":f"output-{index:04d}"})
    return result


@pytest.fixture
def packet_source(tmp_path):
    roots=[]
    for variant in ("current","candidate"):
        root=tmp_path/variant;(root/"skills/demo").mkdir(parents=True)
        (root/"skills/demo/SKILL.md").write_text(f"Synthetic {variant} instructions")
        roots.append(root)
    cases=[{"id":f"case-{i}","skill":"demo","prompt":f"Synthetic task {i}","fixture":{"x":i},"rubric":["Do not invent evidence"]} for i in range(2)]
    suite={"schema":"cometweb.model-evals/v1","cases":cases}
    requests={(c["id"],v):runner.prepare(c,v,*roots,256) for c in cases for v in runner.CONDITIONS}
    return suite,requests,records_for(suite,requests),roots


def test_bridge_exports_no_invented_reviews_or_unknown_zero_cost(packet_source):
    suite,requests,records,_=packet_source
    packets=bridge.build_packets(suite,requests,records)
    assert len(packets)==1 and packets[0]["status"]=="pending_reviews"
    packet=packets[0]
    assert packet["bundle"]["reviews"]==[]
    assert review.compare(packet["bundle"])["comparison_status"]=="incomplete"
    assert all(r["tokens"] is None for r in packet["bundle"]["runs"])
    assert all(r["reviewer"] is None and all(x is None for x in r["scores"].values()) for r in packet["review_template"]["reviews"])


@pytest.mark.parametrize("mutation",["missing","duplicate","mock","input","output","model"])
def test_bad_runs_not_exported_as_valid_comparison(packet_source,mutation):
    suite,requests,records,_=packet_source
    if mutation=="missing":records.pop()
    elif mutation=="duplicate":records.append(copy.deepcopy(records[0]))
    elif mutation=="mock":records[0]["response"]["execution_kind"]="mock"
    elif mutation=="input":records[0]["input_sha256"]="a"*64
    elif mutation=="output":records[0]["output_sha256"]="a"*64
    else:records[0]["response"]["model"]="other"
    with pytest.raises(ValueError):bridge.build_packets(suite,requests,records)


def test_different_reference_bundles_are_separate_cohorts(packet_source):
    suite,requests,_,_=packet_source
    for v in ("current","candidate"):
        requests[("case-1",v)]["instructions"]["references/extra.md"]="Synthetic extra reference"
    records=records_for(suite,requests)
    packets=bridge.build_packets(suite,requests,records)
    assert len(packets)==2
    assert all(len(p["bundle"]["experiment"]["cases"])==1 for p in packets)


def test_changed_task_between_conditions_is_rejected(packet_source):
    suite,requests,_,_=packet_source
    requests[("case-1","candidate")]["prompt"]="Easier replacement task"
    with pytest.raises(ValueError):bridge.build_packets(suite,requests,records_for(suite,requests))


def test_one_unchanged_cohort_is_not_claimed_as_improvement(packet_source):
    suite,requests,_,_=packet_source
    requests[("case-1","candidate")]["instructions"]=copy.deepcopy(requests[("case-1","current")]["instructions"])
    packets=bridge.build_packets(suite,requests,records_for(suite,requests))
    assert sorted(p["status"] for p in packets)==["no_instruction_change","pending_reviews"]


def test_runner_to_review_to_comparison_end_to_end_without_models(packet_source,tmp_path,monkeypatch):
    suite,_,_,roots=packet_source
    calls=[]
    def synthetic_execute(request,command,timeout):
        # Counterfeit labels exercise plumbing, explicitly not execution authenticity.
        idx=len(calls);calls.append(request)
        output=f"Synthetic integration output {idx}"
        return {"schema":"cometweb.eval-response/v1","status":"completed","execution_kind":"model",
                "model":"synthetic-test-label","host":"synthetic-test-host","response_id":f"synthetic-{idx}",
                "output":output,"usage":{"input_tokens":10,"output_tokens":20},"tool_trace":[],"capabilities":request["capabilities"]},0.01
    monkeypatch.setattr(runner,"execute",synthetic_execute)
    out=tmp_path/"output"
    result=runner.run(suite,*roots,["not-launched"],out,max_runs=6,max_output_tokens=256)
    assert len(calls)==6 and result["comparison_status"]=="unreviewed"
    packet=result["review_packets"][0];directory=out/packet["path"]
    payload=json.loads((directory/"comparison.json").read_text())
    grades=json.loads((directory/"review-template.json").read_text())
    for row in grades["reviews"]:
        row.update(reviewer="synthetic-test-reviewer",review_kind="model_assisted",
                   scores={d:3 for d in bridge.DIMENSIONS},evidence={d:"Synthetic plumbing test annotation" for d in bridge.DIMENSIONS})
    (directory/"completed-reviews.json").write_text(json.dumps(grades))
    proc=subprocess.run([sys.executable,str(Path(review.__file__)),str(directory/"comparison.json"),"--reviews",str(directory/"completed-reviews.json"),"--expected-experiment-sha256",packet["experiment_sha256"]],capture_output=True,text=True)
    assert proc.returncode==0,proc.stdout+proc.stderr
    result=json.loads(proc.stdout)
    assert result["comparison_status"]=="reviewed"
    assert result["experiment_pin"]=="matched"
    assert result["quality_verdict"]=="human_decision_required"
    assert json.loads((directory/"comparison.json").read_text())["reviews"]==[]
    assert result["runtime_installation_acceptance"]=="not_assessed"


@pytest.mark.parametrize("field",["blind_id","response_id"])
def test_duplicate_execution_identity_rejected_globally(packet_source,field):
    suite,requests,records,_=packet_source
    if field=="blind_id":records[3][field]=records[0][field]
    else:records[3]["response"][field]=records[0]["response"][field]
    with pytest.raises(ValueError):bridge.build_packets(suite,requests,records)
