"""Executable release decisions on deliberately synthetic manifests, not live evidence."""
from __future__ import annotations
import copy
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys

import pytest

ENGINE = Path(os.environ.get("READINESS_ENGINE_UNDER_TEST", str(Path(__file__).resolve().parents[1] / "scripts/readiness_engine.py")))
spec = importlib.util.spec_from_file_location("release_engine_regressions", ENGINE)
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)
SHA = "a" * 40
AS_OF = "2026-09-12T18:00:00Z"
OBSERVED = "2026-09-12T17:00:00Z"


def green():
    manifest = {
        "manifest_version": 2, "profile": "saas_web", "mode": "standard",
        "release": {"id": "release-100", "commit_sha": SHA, "environment": "production", "as_of": AS_OF},
        "scope": {"audience": "external", "commercial": "free", "risk_assessment_complete": True,
                  "risk_flags": {k: "no" for k in engine.SCOPE_FLAG_KEYS}, "governance_surfaces": []},
        "checks": [], "governance_gates": [],
    }
    for gate in sorted(engine.PROFILE_REQUIRED_GATES["saas_web"]):
        manifest["checks"].append({
            "id": gate, "gate": gate, "domain": sorted(engine.GATE_DOMAINS[gate])[0], "title": gate,
            "status": "pass", "severity": "major", "binding": True, "evidence_level": "verified",
            "required_evidence": "verified", "freshness": "current",
            "evidence": {"summary": "Synthetic execution evidence", "last_verified_at": OBSERVED,
                         "candidate_ref": SHA, "environment": "production"},
        })
    return manifest


def first(m):
    return next(c for c in m["checks"] if c["gate"] == "candidate_verification")


def extra(status="fail"):
    return {"id": "extra-risk", "domain": "qa", "title": "Extra negative path", "status": status,
            "severity": "blocker", "binding": False, "evidence_level": "verified", "freshness": "current",
            "evidence": {"summary": "Synthetic result", "last_verified_at": OBSERVED}}


def test_complete_positive_control():
    assert engine.evaluate(green())["verdict"] == "GO"


@pytest.mark.parametrize("ref", ["release-100-old", "release-100", SHA[:7], SHA + "f", None,
                                  [SHA, "wrong"], [], False, {"commit_sha": "b" * 40}])
def test_other_or_weak_candidate_is_not_accepted(ref):
    m = green(); first(m)["evidence"]["candidate_ref"] = ref
    assert engine.evaluate(m)["verdict"] == "DEFER"


@pytest.mark.parametrize("environment", ["staging", None, "", False, [], "Production"])
def test_wrong_or_missing_environment_is_not_accepted(environment):
    m = green(); first(m)["evidence"]["environment"] = environment
    assert engine.evaluate(m)["verdict"] == "DEFER"


def test_environment_must_be_explicit_for_binding_execution():
    m = green(); first(m)["evidence"].pop("environment")
    assert engine.evaluate(m)["verdict"] == "DEFER"


def test_multiple_immutable_ids_all_bind():
    m = green(); m["release"]["image_digest"] = "sha256:" + "b" * 64
    for c in m["checks"]:
        c["evidence"]["candidate_ref"] = {"commit_sha": SHA, "image_digest": m["release"]["image_digest"]}
    assert engine.evaluate(m)["verdict"] == "GO"
    first(m)["evidence"]["candidate_ref"]["image_digest"] = "sha256:" + "c" * 64
    assert engine.evaluate(m)["verdict"] == "DEFER"


def test_scalar_does_not_cover_two_different_artifacts():
    m = green(); m["release"]["artifact_id"] = "immutable-build-artifact"
    assert engine.evaluate(m)["verdict"] == "DEFER"
    for c in m["checks"]:
        c["evidence"]["candidate_ref"] = [SHA, "immutable-build-artifact"]
    assert engine.evaluate(m)["verdict"] == "GO"


@pytest.mark.parametrize("key,value", [("id", None), ("environment", None), ("commit_sha", None),
                                      ("commit_sha", "abc1234"), ("commit_sha", []), ("artifact_id", True)])
def test_invalid_identity_has_explicit_gap(key, value):
    m = green(); m["release"][key] = value
    r = engine.evaluate(m)
    assert r["release_identity_gaps"] and r["verdict"] == "DEFER"


def test_zero_build_number_is_an_identity_not_a_boolean():
    m = green(); m["release"].pop("commit_sha"); m["release"]["build_number"] = 0
    for c in m["checks"]:
        c["evidence"]["candidate_ref"] = {"build_number": 0}
    assert engine.evaluate(m)["verdict"] == "GO"


def test_config_digest_is_bound_when_pinned():
    m = green(); m["release"]["config_digest"] = "sha256:" + "d" * 64
    assert engine.evaluate(m)["verdict"] == "DEFER"
    for c in m["checks"]:
        c["evidence"]["config_digest"] = m["release"]["config_digest"]
    assert engine.evaluate(m)["verdict"] == "GO"


@pytest.mark.parametrize("value", [None, "", "not-a-date", AS_OF, "2026-09-11T10:00:00Z"])
def test_invalid_or_expired_evidence_does_not_pass(value):
    m = green(); first(m)["evidence"]["expires_at"] = value
    assert engine.evaluate(m)["verdict"] == "DEFER"


@pytest.mark.parametrize("timestamp", ["2026-09-12", "2026-09-12T17:00:00", "2026-09-12T19:00:00Z", 123])
def test_observation_requires_timezone_and_cannot_be_after_assessment(timestamp):
    m = green(); first(m)["evidence"]["last_verified_at"] = timestamp
    assert engine.evaluate(m)["verdict"] == "DEFER"


def test_conflicting_observation_fields_are_not_cherry_picked():
    m = green(); first(m)["evidence"]["observed_at"] = "2026-09-12T16:00:00Z"
    assert engine.evaluate(m)["verdict"] == "DEFER"


def test_equivalent_offset_times_are_equal():
    m = green(); first(m)["evidence"]["observed_at"] = "2026-09-12T19:00:00+02:00"
    assert engine.evaluate(m)["verdict"] == "GO"


@pytest.mark.parametrize("key", ["control_owner", "mitigation"])
def test_null_control_metadata_is_not_a_control(key):
    m = green(); c = first(m)
    c.update(status="pass_with_controls", control_owner="qa", mitigation="manual check", control_due="2026-09-13T18:00:00Z")
    c[key] = None
    assert engine.evaluate(m)["verdict"] == "DEFER"


@pytest.mark.parametrize("key", ["approved_by", "owner", "rationale", "mitigation"])
def test_null_risk_acceptance_is_not_approval(key):
    m = green(); c = extra("accepted_risk"); c["severity"] = "major"
    c["risk_acceptance"] = dict(approved_by="owner", owner="qa", rationale="bounded", mitigation="manual", expires_at="2026-09-13T18:00:00Z")
    c["risk_acceptance"][key] = None; m["checks"].append(c)
    assert engine.evaluate(m)["verdict"] == "DEFER"


@pytest.mark.parametrize("minimum", ["missing", "claimed", "supported"])
def test_runtime_gate_evidence_floor_cannot_be_lowered(minimum):
    m = green(); c = first(m); c.update(required_evidence=minimum, evidence_level=minimum)
    c["evidence"].pop("candidate_ref")
    assert engine.evaluate(m)["verdict"] == "DEFER"


def test_static_documentation_floor_still_allows_supported():
    m = green(); c = next(c for c in m["checks"] if c["gate"] == "operator_docs")
    c.update(required_evidence="supported", evidence_level="supported")
    c["evidence"].pop("candidate_ref"); c["evidence"].pop("environment")
    assert engine.evaluate(m)["verdict"] == "GO"


@pytest.mark.parametrize("key", ["weight", "domain_weight", "threshold"])
@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_values_are_rejected(key, value):
    m = green()
    if key == "weight": first(m)["weight"] = value
    elif key == "domain_weight": m["domain_weights"] = {"qa": value}
    else: m["thresholds"] = {"go_score": value}
    with pytest.raises(engine.ManifestError): engine.evaluate(m)


@pytest.mark.parametrize("field,value", [("binding", "false"), ("binding", 1), ("binding", None),
                                         ("applicable", "false"), ("applicable", 0)])
def test_booleans_are_not_coerced(field, value):
    m = green(); first(m)[field] = value
    with pytest.raises(engine.ManifestError): engine.evaluate(m)


def test_large_finite_weights_do_not_overflow():
    m = green(); m["domain_weights"] = {d: 1e308 for d in engine.DOMAINS}
    for c in m["checks"]: c["weight"] = 1e308
    r = engine.evaluate(m)
    assert r["verdict"] == "GO" and math.isfinite(r["readiness_score"]) and r["readiness_score"] == 100


def test_null_summary_does_not_pass():
    m = green(); first(m)["evidence"]["summary"] = None
    assert engine.evaluate(m)["verdict"] == "DEFER"


def test_rounding_does_not_cross_coverage_floor():
    m = green(); m["domain_weights"] = {d: (1 if d == "qa" else 0) for d in engine.DOMAINS}
    first(m)["weight"] = 89.99
    c = extra("unknown"); c.update(severity="minor", weight=10.01); m["checks"].append(c)
    r = engine.evaluate(m)
    assert r["evidence_coverage"] == 90.0 and r["verdict"] == "DEFER"


def test_zero_weight_domain_cannot_hide_material_unknown():
    m = green(); m["domain_weights"] = {"qa": 0}; c = extra("unknown"); c["weight"] = 0.0001; m["checks"].append(c)
    assert engine.evaluate(m)["verdict"] == "DEFER"


@pytest.mark.parametrize("change", ["remove", "unknown", "na", "weaken"])
def test_blocker_disappearance_is_not_resolution(change):
    previous = green(); previous["checks"].append(extra())
    current = copy.deepcopy(previous)
    if change == "remove": current["checks"].pop()
    elif change == "unknown": current["checks"][-1]["evidence_level"] = "missing"
    elif change == "na": current["checks"][-1].update(status="na", na_reason="out of scope")
    else: current["checks"][-1].update(status="pass", severity="minor")
    delta = engine.compare(current, previous)
    assert "extra-risk" not in delta["resolved_blockers"]
    assert delta["current_verdict"] not in {"GO", "GO_WITH_CONTROLS"}


def test_retested_same_contract_blocker_is_resolved():
    previous = green(); previous["checks"].append(extra())
    current = copy.deepcopy(previous); current["checks"][-1]["status"] = "pass"
    delta = engine.compare(current, previous)
    assert delta["resolved_blockers"] == ["extra-risk"]
    assert delta["current_verdict"] == "GO"


def test_different_environment_is_not_closure_or_comparable_score():
    previous = green(); previous["checks"].append(extra())
    current = copy.deepcopy(previous); current["checks"][-1]["status"] = "pass"
    current["release"]["environment"] = "staging"
    for c in current["checks"]: c["evidence"]["environment"] = "staging"
    r = engine.compare(current, previous)
    assert not r["resolved_blockers"] and r["score_delta"] is None and r["environment_changed"]


def test_frozen_contract_changes_only_for_requirements():
    m = green(); original = engine.evaluate(m)["contract_hash"]
    first(m)["evidence"]["summary"] = "New source"
    assert engine.evaluate(m, expected_contract_hash=original)["contract_mismatch"] is False
    first(m)["title"] = "Weaker expectation"
    assert engine.evaluate(m, expected_contract_hash=original)["verdict"] == "DEFER"


def test_reverse_delta_time_is_rejected():
    p = green(); c = green(); c["release"]["as_of"] = "2026-09-12T17:30:00Z"
    with pytest.raises(engine.ManifestError): engine.compare(c, p)


@pytest.mark.parametrize("document", ['{"x":1,"x":2}', '{"x":NaN}', '{"x":1e999}', '[]'])
def test_strict_json_input(tmp_path, document):
    p = tmp_path / "input.json"; p.write_text(document)
    with pytest.raises(engine.ManifestError): engine._load(p)


def test_cli_strict_prevents_scope_deletion(tmp_path):
    previous = green(); previous["checks"].append(extra())
    current = green()
    for name, data in (("previous", previous), ("current", current)):
        (tmp_path / (name + ".json")).write_text(json.dumps(data))
    r = subprocess.run([sys.executable, str(ENGINE), "--input", str(tmp_path/"current.json"),
                        "--previous", str(tmp_path/"previous.json"), "--ci-policy", "strict"], capture_output=True, text=True)
    assert r.returncode == 1, r.stderr
    assert json.loads(r.stdout)["verdict"] == "DEFER"


def test_bootstrap_floors_match_engine_without_duplicate_policy():
    bp = ENGINE.with_name("bootstrap_manifest.py")
    spec = importlib.util.spec_from_file_location("bootstrap_hardening_regression", bp)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    m = module.build({"profile":"saas_web", "scope":green()["scope"], "release":green()["release"]})
    assert all(c["required_evidence"] == engine.GATE_EVIDENCE_FLOORS[c["gate"]] for c in m["checks"])
    assert all(c["status"] == "unknown" and not c["evidence"] for c in m["checks"])


@pytest.mark.parametrize("defect", ["empty_evidence", "null_summary", "missing_timestamp", "expired", "wrong_environment"])
def test_nonbinding_material_pass_still_needs_evidence(defect):
    m = green(); c = extra("pass"); m["checks"].append(c)
    if defect == "empty_evidence": c["evidence"] = {}
    elif defect == "null_summary": c["evidence"]["summary"] = None
    elif defect == "missing_timestamp": c["evidence"].pop("last_verified_at")
    elif defect == "expired": c["evidence"]["expires_at"] = OBSERVED
    else: c["evidence"]["environment"] = "staging"
    assert engine.evaluate(m)["verdict"] == "DEFER"


@pytest.mark.parametrize("defect", ["null_summary", "bad_expiry", "expired", "conflicting_time", "wrong_environment"])
def test_governance_clear_has_temporal_and_scope_guards(defect):
    m = green(); ev = {"summary":"Synthetic review", "last_verified_at": OBSERVED}
    m["scope"]["governance_surfaces"] = ["privacy"]
    m["governance_gates"] = [{"surface":"privacy", "status":"clear", "evidence":ev}]
    if defect == "null_summary": ev["summary"] = None
    elif defect == "bad_expiry": ev["expires_at"] = "bad"
    elif defect == "expired": ev["expires_at"] = AS_OF
    elif defect == "conflicting_time": ev["observed_at"] = "2026-09-12T16:00:00Z"
    else: ev["environment"] = "staging"
    assert engine.evaluate(m)["verdict"] == "DEFER"


def test_removed_unknown_is_not_resolved():
    p = green(); p["checks"].append({**extra("unknown"), "binding": True})
    d = engine.compare(green(), p)
    assert "extra-risk" not in d["resolved_binding_unknowns"]
    assert d["removed_binding_unknowns"] == ["extra-risk"]


def test_explicitly_reviewed_new_scope_can_be_assessed_without_false_resolution():
    p = green(); p["checks"].append(extra())
    c = green(); reviewed_hash = engine.evaluate(c)["contract_hash"]
    d = engine.compare(c, p, expected_contract_hash=reviewed_hash)
    assert d["current_verdict"] == "GO" and not d["resolved_blockers"]
    assert not d["scores_comparable"]


def test_governance_block_still_wins_over_contract_mismatch():
    m = green(); m["governance_gates"] = [{"surface":"privacy", "status":"block"}]
    assert engine.evaluate(m, expected_contract_hash="0"*64)["verdict"] == "NO_GO"


def test_contract_digest_is_order_independent_but_tracks_policy():
    m = green(); original = engine.evaluate(m)["contract_hash"]
    m["checks"].reverse(); assert engine.evaluate(m)["contract_hash"] == original
    m["thresholds"] = {"go_score": 99}
    assert engine.evaluate(m)["contract_hash"] != original


def test_no_deployment_authorization_from_a_valid_manifest():
    r = engine.evaluate(green())
    assert r["assessment_basis"] == "declared_manifest"
    assert r["deployment_authorization"] == "not_provided"
    assert r["evidence_authentication"] == "not_performed"


def test_evidence_downgrade_explains_what_to_fix():
    m = green(); first(m)["evidence"].update(candidate_ref="wrong", environment="staging", expires_at="bad")
    r = engine.evaluate(m); c = next(x for x in r["evidence_downgrades"] if x["id"] == "candidate_verification")
    assert {"candidate_binding_missing_or_mismatched", "environment_missing_or_mismatched", "expiry_invalid"} <= set(c["evidence_issues"])


def test_cli_malformed_input_exits_two(tmp_path):
    p = tmp_path/"manifest.json"; p.write_text('{"manifest_version":2,"manifest_version":2}')
    r = subprocess.run([sys.executable,str(ENGINE),"--input",str(p),"--ci-policy","strict"],capture_output=True,text=True)
    assert r.returncode == 2 and "error" in json.loads(r.stderr)
    assert "Traceback" not in r.stderr


def test_evaluation_does_not_mutate_callers_nested_input():
    m = green(); original = copy.deepcopy(m)
    engine.evaluate(m)
    assert m == original


def test_unknown_risk_flag_name_is_not_ignored():
    m = green(); m["scope"]["risk_flags"]["auth_chagne"] = "yes"
    with pytest.raises(engine.ManifestError): engine.evaluate(m)


def test_huge_native_integer_is_rejected_before_json_rendering():
    m = green(); m["extra"] = 2 ** 20000
    with pytest.raises(engine.ManifestError): engine.evaluate(m)


def test_risk_removed_from_scope_does_not_resolve_a_missing_gate():
    p = green(); p["mode"] = "deep"; p["scope"]["risk_flags"]["auth_change"] = "yes"
    d = engine.compare(green(), p)
    assert "auth_access_control" in d["no_longer_required_gates"]
    assert "auth_access_control" not in d["resolved_missing_required_gates"]


def test_adding_unknown_gate_is_presence_not_resolution():
    p = green(); c = copy.deepcopy(p)
    p["checks"] = [x for x in p["checks"] if x["gate"] != "candidate_verification"]
    first(c)["status"] = "unknown"
    d = engine.compare(c, p)
    assert "candidate_verification" in d["provided_required_gates"]
    assert "candidate_verification" not in d["resolved_missing_required_gates"]


def test_cli_output_cannot_destroy_input(tmp_path):
    p = tmp_path/"input.json"; p.write_text(json.dumps(green())); before = p.read_bytes()
    r = subprocess.run([sys.executable,str(ENGINE),"--input",str(p),"--output",str(p)],capture_output=True,text=True)
    assert r.returncode == 2 and p.read_bytes() == before and not r.stdout


def test_output_immutability_and_idempotence(tmp_path):
    p = tmp_path/"result.json"
    engine.write_output(p, '{"result":1}')
    engine.write_output(p, '{"result":1}')
    before = p.read_bytes()
    with pytest.raises(engine.ManifestError): engine.write_output(p, '{"result":2}')
    assert p.read_bytes() == before


@pytest.mark.parametrize("ancestor", [False, True])
def test_output_symlink_is_rejected(tmp_path, ancestor):
    target = tmp_path/"real"; target.mkdir()
    link = tmp_path/"link"
    if ancestor:
        link.symlink_to(target, target_is_directory=True); out = link/"out.json"
    else:
        link.symlink_to(target/"out.json"); out = link
    with pytest.raises(engine.ManifestError): engine.write_output(out, '{}')
    assert not (target/"out.json").exists()


def test_bootstrap_does_not_destroy_context(tmp_path):
    p = tmp_path/"context.json"; p.write_text(json.dumps(green())); before = p.read_bytes()
    r = subprocess.run([sys.executable,str(ENGINE.with_name("bootstrap_manifest.py")),"--context",str(p),"--output",str(p)],capture_output=True,text=True)
    assert r.returncode == 2 and p.read_bytes() == before and not r.stdout
