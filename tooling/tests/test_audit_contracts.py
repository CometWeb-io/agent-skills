"""All artifacts below are synthetic conformance fixtures, not application evidence."""
import copy
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

PATH = Path(__file__).resolve().parents[1] / "audit_contracts.py"
spec = importlib.util.spec_from_file_location("cw_audit_contracts", PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
NOW = dt.datetime(2026, 9, 12, 12, tzinfo=dt.timezone.utc)
SHA = "a" * 40


def trace():
    artifact = {"path":"evidence.txt", "sha256":hashlib.sha256(b"synthetic evidence\n").hexdigest()}
    base = {"revision":SHA,"environment":"synthetic-local","observed_at":"2026-09-12T10:00:00Z", "artifact":artifact}
    edge_ids = ["ui-api","api-auth","auth-db","db-ui"]
    result = {
        "schema":"cometweb.contract-trace/v1", "claim":"full_runtime_trace",
        "scope":{"revision":SHA,"build":"fixture-build-1","environment":"synthetic-local", "as_of":"2026-09-12T11:00:00Z", "inventory_status":"complete", "inventory_refs":["inventory"]},
        "nodes":[{"id":n,"kind":k,"locator":f"synthetic/{n}"} for n,k in [("ui","ui"),("api","api"),("auth","authorization"),("db","database")]],
        "edges":[{"id":edge,"from":a,"to":b,"contract":"Synthetic explicit expectation", "state":"pass","method":"runtime", "evidence_refs":["run"]} for edge,a,b in [("ui-api","ui","api"),("api-auth","api","auth"),("auth-db","auth","db"),("db-ui","db","ui")]],
        "evidence":[{**base,"id":"inventory","kind":"inventory","covers_edges":[]},
                    {**base,"id":"run","kind":"execution","build":"fixture-build-1","run_id":"synthetic-run", "journey_id":"save","scenario_id":"save-happy", "outcome":"pass", "covers_edges":edge_ids}],
        "journeys":[{"id":"save","edge_ids":edge_ids,"required_scenarios":["save-happy"]}],
        "scenarios":[{"id":"save-happy","journey_id":"save","state":"pass","evidence_refs":["run"]}],
    }
    return json.loads(json.dumps(result))


def checked(data, **kw):
    return mod.validate(data, now=NOW, **kw)


def test_valid_complete_records_are_not_authentication_or_release():
    result=checked(trace())
    assert result["result"]=="no_failures_in_declared_scope"
    assert result["release_authorization"]=="not_provided"
    assert result["artifact_integrity"]=="not_checked"
    assert result["evidence_authentication"]=="not_performed"
    assert result["coverage"]["runtime_assessed_edges"]==4


def test_verified_file_bytes_remain_not_authenticated(tmp_path):
    (tmp_path/"evidence.txt").write_bytes(b"synthetic evidence\n")
    result=checked(trace(), artifacts_root=tmp_path)
    assert result["artifact_integrity"]=="verified_local_bytes"
    assert result["evidence_authentication"]=="not_performed"


@pytest.mark.parametrize("collection",["nodes","edges","evidence","journeys","scenarios"])
def test_duplicate_ids_rejected(collection):
    data=trace();data[collection].append(copy.deepcopy(data[collection][0]))
    with pytest.raises(ValueError):checked(data)


@pytest.mark.parametrize("level",["trace","scope","node","edge","evidence","artifact","journey","scenario"])
def test_unknown_fields_rejected(level):
    data=trace(); target={"trace":data,"scope":data["scope"],"node":data["nodes"][0],"edge":data["edges"][0],"evidence":data["evidence"][0],"artifact":data["evidence"][0]["artifact"],"journey":data["journeys"][0],"scenario":data["scenarios"][0]}[level]
    target["typo_field"]=True
    with pytest.raises(ValueError):checked(data)


@pytest.mark.parametrize("field,value",[("revision","b"*40),("environment","production"),("build","other-build"),("observed_at","2026-09-12T11:01:00Z"),("observed_at","2026-09-12T10:00:00"),("outcome","fail"),("run_id","")])
def test_execution_must_match_actual_scope(field,value):
    data=trace();data["evidence"][1][field]=value
    with pytest.raises(ValueError):checked(data)


@pytest.mark.parametrize("value",["latest","abc1234","A"*40,"a"*39,7,None])
def test_full_git_sha_required(value):
    data=trace();data["scope"]["revision"]=value
    with pytest.raises(ValueError):checked(data)


def test_no_build_no_runtime_acceptance():
    data=trace();del data["scope"]["build"]
    with pytest.raises(ValueError):checked(data)


def test_future_audit_rejected():
    data=trace();data["scope"]["as_of"]="2026-09-13T11:00:00Z"
    with pytest.raises(ValueError):checked(data)


def test_timezone_equivalence_is_supported():
    data=trace();data["evidence"][1]["observed_at"]="2026-09-12T12:00:00+02:00"
    checked(data)


@pytest.mark.parametrize("field,value",[("from","missing"),("to","missing"),("evidence_refs",["missing"]),("evidence_refs",[]),("method","none"),("state","shipped")])
def test_edge_admission(field,value):
    data=trace();data["edges"][0][field]=value
    with pytest.raises(ValueError):checked(data)


def test_complete_inventory_is_not_self_asserted():
    data=trace();data["scope"]["inventory_refs"]=[]
    with pytest.raises(ValueError):checked(data)


def test_partial_inventory_propagates_incomplete():
    data=trace();data["claim"]="bounded";data["scope"]["inventory_status"]="partial"
    assert checked(data)["result"]=="incomplete"


def test_source_inspection_is_not_runtime():
    data=trace();run=data["evidence"][1]
    run["kind"]="source"
    for field in ("run_id","journey_id","scenario_id","outcome"):run.pop(field)
    for edge in data["edges"]:edge["method"]="source"
    data["scenarios"]=[]
    with pytest.raises(ValueError):checked(data)
    data["claim"]="full_source_trace"
    result=checked(data)
    assert result["coverage"]["source_assessed_edges"]==4
    assert result["coverage"]["runtime_assessed_edges"]==0
    assert result["result"]=="incomplete"


@pytest.mark.parametrize("scenario",["save-empty","save-retry","save-forbidden","save-partial"])
def test_happy_path_does_not_cover_other_required_scenarios(scenario):
    data=trace();data["claim"]="bounded"
    data["journeys"][0]["required_scenarios"].append(scenario)
    result=checked(data)
    assert "scenario:"+scenario in result["gaps"]
    assert result["result"]=="incomplete"


def test_spliced_unit_evidence_cannot_be_an_end_to_end_run():
    data=trace();data["evidence"][1]["covers_edges"]=["ui-api"]
    with pytest.raises(ValueError):checked(data)


def test_disconnected_path_is_rejected():
    data=trace();data["journeys"][0]["edge_ids"]=["ui-api","auth-db"]
    with pytest.raises(ValueError):checked(data)


def test_legitimate_round_trip_is_not_misdiagnosed_as_cycle_failure():
    assert checked(trace())["result"]=="no_failures_in_declared_scope"


@pytest.mark.parametrize("field",["journey_id","scenario_id"])
def test_execution_from_other_case_is_not_reused(field):
    data=trace();data["evidence"][1][field]="other"
    with pytest.raises(ValueError):checked(data)


def test_real_failure_is_not_hidden_by_complete_coverage():
    data=trace();data["evidence"][1]["outcome"]="fail"
    for edge in data["edges"]:edge["state"]="fail"
    data["scenarios"][0]["state"]="fail"
    result=checked(data)
    assert result["result"]=="failures_present"
    assert len(result["failures"])==5
    assert not result["gaps"]


def test_blocked_is_not_pass_or_bug():
    data=trace();data["claim"]="bounded"
    data["edges"][0].update(state="blocked",method="none",evidence_refs=[],reason="No authorized mutation")
    data["scenarios"][0].update(state="blocked",evidence_refs=[],reason="No authorized mutation")
    result=checked(data)
    assert result["result"]=="incomplete" and not result["failures"]


@pytest.mark.parametrize("value",["../outside","/absolute","x/../../escape","C:/absolute","x\\evil","x//y","./x","x/./y","x\ny"])
def test_artifact_path_escape_rejected(value):
    data=trace();data["evidence"][0]["artifact"]["path"]=value
    with pytest.raises(ValueError):checked(data)


def test_missing_evidence_file_rejected(tmp_path):
    with pytest.raises(ValueError):checked(trace(),artifacts_root=tmp_path)


def test_changed_file_rejected(tmp_path):
    (tmp_path/"evidence.txt").write_text("other")
    with pytest.raises(ValueError):checked(trace(),artifacts_root=tmp_path)


def test_evidence_symlink_rejected(tmp_path):
    (tmp_path/"elsewhere").write_text("synthetic evidence\n")
    (tmp_path/"evidence.txt").symlink_to(tmp_path/"elsewhere")
    with pytest.raises(ValueError):checked(trace(),artifacts_root=tmp_path)


def test_conflicting_artifact_hashes_rejected():
    data=trace();data["evidence"][1]["artifact"]["sha256"]="b"*64
    with pytest.raises(ValueError):checked(data)


@pytest.mark.parametrize("blob",[b'{"schema":1,"schema":2}',b'{"x":NaN}',b'{"x":Infinity}',b'[]',b'null',b'{',b'\xff'])
def test_strict_json_rejects_ambiguity(blob):
    with pytest.raises(ValueError):mod.loads(blob)


def test_oversized_input_rejected():
    with pytest.raises(ValueError):mod.loads(b" "*(mod.MAX_JSON+1))


def test_cli_invalid_never_leaks_content(tmp_path):
    path=tmp_path/"input.json";path.write_text('{"private":"do-not-echo-sentinel"}')
    out=subprocess.run([sys.executable,str(PATH),str(path)],capture_output=True,text=True)
    assert out.returncode==2
    assert "do-not-echo-sentinel" not in out.stdout+out.stderr


def test_cli_valid_results(tmp_path):
    path=tmp_path/"trace.json";path.write_text(json.dumps(trace()))
    out=subprocess.run([sys.executable,str(PATH),str(path)],capture_output=True,text=True)
    assert out.returncode==0
    data=trace();data["claim"]="bounded";data["scenarios"]=[]
    path.write_text(json.dumps(data))
    out=subprocess.run([sys.executable,str(PATH),str(path)],capture_output=True,text=True)
    assert out.returncode==1


def test_orphan_node_blocks_full_trace_claim():
    data=trace();data["nodes"].append({"id":"unconnected","kind":"queue","locator":"synthetic/unconnected"})
    with pytest.raises(ValueError):checked(data)
    data["claim"]="bounded"
    assert "node:unconnected" in checked(data)["gaps"]


@pytest.mark.parametrize("data",[None,True,42,"not an object",[],[{}]])
def test_invalid_top_level_api_inputs(data):
    with pytest.raises(ValueError):checked(data)


def test_malformed_nested_values_always_fail_closed():
    # Mutate every scalar leaf: one test with independently generated malformed inputs.
    source=trace()
    def leaves(value,path=()):
        if isinstance(value,dict):
            for k,v in value.items():yield from leaves(v,path+(k,))
        elif isinstance(value,list):
            for k,v in enumerate(value):yield from leaves(v,path+(k,))
        else:yield path
    count=0
    for path in leaves(source):
        for bad in [None,[],{},True,3.14]:
            data=copy.deepcopy(source);parent=data
            for key in path[:-1]:parent=parent[key]
            parent[path[-1]]=bad
            with pytest.raises(ValueError):checked(data)
            count+=1
    assert count>400


def test_evidence_root_symlink_ancestor_rejected(tmp_path):
    real=tmp_path/"real";real.mkdir();(real/"nested").mkdir()
    (real/"nested/evidence.txt").write_text("synthetic evidence\n")
    link=tmp_path/"link";link.symlink_to(real,target_is_directory=True)
    with pytest.raises(ValueError):checked(trace(),artifacts_root=link/"nested")


def test_oversized_artifact_rejected_before_hash_read(tmp_path,monkeypatch):
    (tmp_path/"evidence.txt").write_text("synthetic evidence\n")
    monkeypatch.setattr(mod,"MAX_FILE",4)
    with pytest.raises(ValueError):checked(trace(),artifacts_root=tmp_path)


def test_expectation_pin_blocks_removal_of_failed_scenario():
    data=trace();pin=checked(data)["contract_sha256"]
    data["journeys"][0]["required_scenarios"]=["replacement-happy"]
    data["scenarios"][0]["id"]="replacement-happy"
    data["evidence"][1]["scenario_id"]="replacement-happy"
    with pytest.raises(ValueError):checked(data,expected_contract_sha256=pin)


def test_expectation_pin_blocks_weaker_contract():
    data=trace();pin=checked(data)["contract_sha256"]
    data["edges"][0]["contract"]="Accept any response, even incorrect"
    with pytest.raises(ValueError):checked(data,expected_contract_sha256=pin)


def test_expectation_pin_allows_new_build_and_observations():
    data=trace();pin=checked(data)["contract_sha256"]
    data["scope"]["revision"]="b"*40;data["scope"]["build"]="build-2"
    for e in data["evidence"]:e["revision"]="b"*40
    data["evidence"][1]["build"]="build-2"
    assert checked(data,expected_contract_sha256=pin)["contract_pin"]=="matched"


def test_expectation_hash_is_independent_of_node_and_edge_listing_order():
    data=trace();pin=checked(data)["contract_sha256"]
    data["nodes"].reverse();data["edges"].reverse()
    assert checked(data,expected_contract_sha256=pin)["contract_pin"]=="matched"
