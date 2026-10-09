"""Opt-in local profiles: pinned instructions, isolated task binding, sidecar checks."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
OWNERS = {
    "conversion-audit": "web-app-auditor",
    "experiment-design": "brief-architect",
    "activation-onboarding": "product-operator",
    "sop-documentation": "content-writer",
}
PROFILE_GATE = "specialist-profile-owner/v2"

OUTPUTS = {
    "web-app-auditor": "FindingEnvelope",
    "brief-architect": "ArtifactEnvelope",
    "product-operator": "SpecialistHandoff",
    "content-writer": "ArtifactEnvelope",
}


def _file(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError("profile path must be relative")
    result = (root / relative).resolve()
    if not result.is_relative_to(root.resolve()) or not result.is_file():
        raise ValueError("profile path missing or outside root")
    return result


def load_registry(root: Path = ROOT) -> dict:
    registry = json.loads(_file(root, "registry/specialist-profiles.json").read_text())
    if not isinstance(registry, dict) or registry.get("schema") != "cometweb.specialist-profiles/local-v2":
        raise ValueError("invalid specialist profile registry")
    if registry.get("status") != "LOCAL_PILOT_NOT_QUALIFIED":
        raise ValueError("experimental registry status required")
    profiles = registry.get("profiles")
    if not isinstance(profiles, list) or not profiles:
        raise ValueError("missing profiles")
    seen = set()
    for profile in profiles:
        if not isinstance(profile, dict):
            raise ValueError("invalid profile")
        pid = profile.get("id")
        if not isinstance(pid, str) or pid not in OWNERS or pid in seen:
            raise ValueError("unknown or duplicate profile")
        seen.add(pid)
        if profile.get("owner_skill") != OWNERS[pid]:
            raise ValueError("profile owner mismatch")
        _file(root, f"skills/{OWNERS[pid]}/SKILL.md")
        if profile.get("license") != "MIT" or profile.get("claim_class") != "FRAMEWORK":
            raise ValueError("invalid profile provenance")
        if not re.fullmatch(r"[0-9a-f]{40}", str(profile.get("source_commit", ""))):
            raise ValueError("source commit must be pinned")
        if not re.fullmatch(r"[0-9a-f]{64}", str(profile.get("source_sha256", ""))):
            raise ValueError("source content must be pinned")
        patterns = profile.get("match_any")
        if not isinstance(patterns, list) or not patterns:
            raise ValueError("missing routing patterns")
        for pattern in patterns:
            if not isinstance(pattern, str) or not pattern:
                raise ValueError("invalid routing pattern")
            re.compile(pattern)
        inventory = profile.get("files")
        if not isinstance(inventory, dict) or not inventory:
            raise ValueError("missing profile inventory")
        prefix = f"specialist-profiles/{pid}/"
        expected = {str(p.relative_to(root)) for p in (root / prefix).rglob("*") if p.is_file()}
        expected.add(profile.get("license_file", ""))
        if set(inventory) != expected:
            raise ValueError("incomplete profile inventory")
        for key in ("entrypoint", "output_schema", "response_schema", "license_file"):
            if profile.get(key) not in inventory:
                raise ValueError("profile resources must be locked")
        if not profile["entrypoint"].startswith(prefix) or not profile["output_schema"].startswith(prefix):
            raise ValueError("profile resources outside profile")
        for relative, digest in inventory.items():
            if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                raise ValueError("invalid profile hash")
            if hashlib.sha256(_file(root, relative).read_bytes()).hexdigest() != digest:
                raise ValueError(f"profile integrity mismatch: {relative}")
    return registry


def _profile(root: Path, profile_id: str) -> dict:
    for profile in load_registry(root)["profiles"]:
        if profile["id"] == profile_id:
            return profile
    raise ValueError("unknown specialist profile")


def select(goal: str, root: Path = ROOT) -> list[str]:
    """Routing suggestions only; inspect active user intent, never prior envelopes."""
    if not isinstance(goal, str) or not goal.strip():
        raise ValueError("goal must be nonblank text")
    text = re.sub(r"```.*?```|`[^`]*`|\"[^\"]*\"|“[^”]*”", "", goal, flags=re.S)
    text = re.sub(r"(?m)^\s*>.*$", "", text)
    if re.search(r"przet[łl]umacz|translate|employee onboarding|onboarding pracownik|support triage", text, re.I):
        return []
    return [p["id"] for p in load_registry(root)["profiles"] if any(re.search(v, text, re.I) for v in p["match_any"])]


def plan_for_profile(goal: str, profile_id: str, root: Path = ROOT, trusted_context: dict | None = None) -> dict:
    if not isinstance(goal, str) or not goal.strip():
        raise ValueError("goal must be nonblank text")
    profile = _profile(root, profile_id)
    owner = profile["owner_skill"]
    if trusted_context is not None:
        trusted = _local_module(root, "trusted_profile_context")
        trusted.validate(trusted_context)
        if trusted_context["profile_id"] != profile_id or trusted_context["original_brief"] != goal.strip():
            raise ValueError("context must commit the exact original brief/profile")
    result = {
        "archetype": "single_skill", "goal_summary": goal.strip(),
        "steps": [{"skill": owner, "purpose": f"Apply local profile {profile_id} to the requested artifact only",
                   "envelope_out": OUTPUTS[owner], "read_skill": True, "handoff_gate":PROFILE_GATE,
                   "profile_lock":copy.deepcopy(profile), "gate_lock":gate_lock(root,profile_id), "retry_limit":2}],
        "single_skill_alternative": owner,
        "boundaries": ["Explicit local profile; canonical owner output plus a separate typed sidecar. No external execution authorization."],
        "specialist_profile": copy.deepcopy(profile),
    }
    if trusted_context is not None:
        result["steps"][0]["trusted_context"] = copy.deepcopy(trusted_context)
        result["steps"][0]["trusted_context_hash"] = trusted.digest(trusted_context)
    return result


def attach_task(task: dict, plan: dict, root: Path = ROOT) -> dict:
    declared = plan.get("specialist_profile")
    if not isinstance(declared, dict):
        raise ValueError("missing profile lock")
    current = _profile(root, declared.get("id"))
    if current != declared or task.get("skill") != current["owner_skill"]:
        raise ValueError("profile lock or task owner changed")
    result = copy.deepcopy(task)
    result["specialist_profile"] = current
    result["profile_result_schema"] = str(root / current["response_schema"])
    result["step_id"] = "step-1"
    result["handoff_gate"] = PROFILE_GATE
    result["gate_lock"] = plan["steps"][0]["gate_lock"]
    result["profile_output_schema"] = str(root / current["output_schema"])
    result["prompt"] += (
        "\nLocal specialist profile (FRAMEWORK guidance, not observed product evidence):\n"
        f"Read `{root / current['entrypoint']}` after the canonical owner entrypoint.\n"
        f"Return only the canonical owner in selected_skills and the profile ID in selected_profile_id. Put all substantive requested content in artifact; the sidecar is additional. Add a separate JSON sidecar enforced with `{result['profile_output_schema']}`.\n"
        "Validate the sidecar with specialist_profiles.py validate. The parent independently validates the full response and CW-AIP carrier before ledger completion. Acceptance is local contract validity only, does not authorize execution or prove semantic truth.\n"
    )
    return result


def validate_sidecar(value: object, root: Path = ROOT) -> dict:
    from jsonschema import Draft202012Validator

    errors = []
    try:
        if not isinstance(value, dict):
            raise ValueError("sidecar must be an object")
        json.dumps(value, allow_nan=False)
        profile = _profile(root, value.get("profile_id"))
        schema = json.loads(_file(root, profile["output_schema"]).read_text())
        Draft202012Validator.check_schema(schema)
        errors = [f"{list(e.path)}: {e.message}" for e in Draft202012Validator(schema).iter_errors(value)]
        if errors:
            return {"accepted": False, "execution_authorized": False, "errors": errors}
        evidence = {v["id"]: v for v in value["evidence"]}
        if len(evidence) != len(value["evidence"]):
            errors.append("duplicate evidence id")
        def check_refs(ids: list, *, factual: bool = False, required: bool = False) -> None:
            if required and not ids:
                errors.append("missing factual evidence references")
            for eid in ids:
                if eid not in evidence:
                    errors.append(f"dangling evidence id: {eid}")
                elif factual and evidence[eid]["kind"] not in {"USER_INPUT", "OBSERVED"}:
                    errors.append(f"framework/hypothesis cannot support product observation: {eid}")

        pid = value["profile_id"]
        data = value["result"]
        reviewable = value["status"] == "REVIEWABLE"
        if reviewable and value["unknowns"]:
            errors.append("unresolved unknowns prevent REVIEWABLE")
        check_refs(data["framework_source_ids"])
        if any(evidence[eid]["kind"] != "FRAMEWORK" for eid in data["framework_source_ids"] if eid in evidence):
            errors.append("method references require FRAMEWORK provenance")
        for row in data.get("hypotheses", []):
            check_refs(row["source_ids"])
        if pid == "conversion-audit":
            check_refs(data["baseline_source_ids"], factual=data["baseline_rate"] is not None, required=data["baseline_rate"] is not None)
            for row in data["observations"]:
                check_refs(row["source_ids"], factual=True, required=True)
        elif pid == "experiment-design":
            for key, ids in data["parameter_source_ids"].items():
                check_refs(ids, factual=True, required=data[key] is not None)
            if reviewable and (data["method"] == "UNKNOWN" or data["instrumentation"] != "VERIFIED" or
                               any(data[k] is None for k in ("baseline_rate", "sample_size_per_variant", "mde_absolute", "alpha", "power", "randomization_unit", "stopping_rule"))):
                errors.append("unresolved experiment design prevents REVIEWABLE")
            if data["alpha"] in (0, 1) or data["power"] in (0, 1):
                errors.append("alpha and power must lie strictly between 0 and 1")
        elif pid == "activation-onboarding":
            check_refs(data["activation_source_ids"], factual=data["activation_rate"] is not None, required=data["activation_rate"] is not None)
            measured = data["retention_link"] == "MEASURED"
            check_refs(data["retention_source_ids"], factual=measured, required=measured)
            for row in data["steps"]:
                observed = row["basis"] == "OBSERVED"
                check_refs(row["source_ids"], factual=observed, required=observed)
            if reviewable and (data["activation_definition"] is None or data["cohort"] is None):
                errors.append("undefined activation/cohort prevents REVIEWABLE")
        else:
            for row in data["steps"]:
                check_refs(row["source_ids"], factual=row["basis"] == "CONFIRMED", required=row["basis"] == "CONFIRMED")
                if row["risk"] == "EXTERNAL_MUTATION" and row["approval_requirement"] is None:
                    errors.append("external SOP action lacks a permission checkpoint")
            if reviewable and data["owner"] is None:
                errors.append("missing SOP owner prevents REVIEWABLE")
        for rows in (data.get("observations", []), data.get("hypotheses", []), data.get("steps", [])):
            ids = [v["id"] for v in rows]
            if len(ids) != len(set(ids)):
                errors.append("duplicate domain row id")
    except (ValueError, OSError, TypeError) as exc:
        errors.append(str(exc))
    return {"accepted": not errors, "execution_authorized": False, "errors": errors,
            "scope": "Local schema/reference checks only; factual truth and owner output require independent validation."}



def _canonical(value: object) -> bytes:
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()


def _hash(value: object) -> str:
    return "sha256:"+hashlib.sha256(_canonical(value)).hexdigest()


def _local_module(root: Path, name: str):
    spec = importlib.util.spec_from_file_location("profile_" + name, root / "skills/skill-orchestrator/scripts" / (name + ".py"))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def gate_lock(root: Path, profile_id: str) -> dict:
    _profile(root, profile_id)
    return {"schema": "cometweb.profile-gate-lock/v2", "files": _local_module(root, "runtime_sources").closure(root)}



def validate_profile_step(step: dict, root: Path = ROOT) -> None:
    profile=step.get("profile_lock")
    if not isinstance(profile,dict) or profile != _profile(root,profile.get("id")):
        raise ValueError("profile step lock changed")
    if "trusted_context" in step or "trusted_context_hash" in step:
        trusted = _local_module(root, "trusted_profile_context")
        trusted.validate(step.get("trusted_context"))
        if trusted.digest(step["trusted_context"]) != step.get("trusted_context_hash") or step["trusted_context"]["profile_id"] != profile["id"]:
            raise ValueError("trusted context commitment changed")
    if step.get("native_report_contract") is not None:
        if step["native_report_contract"] != _local_module(root, "typed_owner").VERSION or "trusted_context" not in step:
            raise ValueError("invalid typed native contract/context")
    if step.get("report_as_of") is not None:
        _local_module(root, "typed_owner").validate_timestamp(step["report_as_of"])
    limit=step.get("retry_limit")
    if isinstance(limit,bool) or not isinstance(limit,int) or not 1<=limit<=3:
        raise ValueError("profile retry_limit must be an integer 1..3")
    if step.get("handoff_gate") != PROFILE_GATE or step.get("skill") != profile["owner_skill"] or step.get("envelope_out") != OUTPUTS[profile["owner_skill"]]:
        raise ValueError("profile step owner/type mismatch")
    if step.get("gate_lock") != gate_lock(root,profile["id"]):
        raise ValueError("profile gate source changed; new plan/run required")


def validate_response(value: object, profile_id: str, root: Path = ROOT, trusted_context: dict | None = None, native_report_contract: str | None = None, report_as_of: str | None = None) -> dict:
    from jsonschema import Draft202012Validator
    errors=[]
    try:
        value=json.loads(_canonical(value))
        profile=_profile(root,profile_id)
        schema=json.loads(_file(root,profile["response_schema"]).read_text())
        typed = _local_module(root, "typed_owner")
        if native_report_contract is not None and native_report_contract != typed.VERSION:
            raise ValueError("unknown native report contract")
        if native_report_contract:
            if trusted_context is None: raise ValueError("typed report requires trusted context")
            schema = typed.response_schema(schema, profile["owner_skill"], root, trusted_context,report_as_of)
        elif trusted_context is not None:
            schema["properties"]["owner_output_json"] = {"type": "string", "pattern": "\\S"}
            schema["required"].append("owner_output_json")
        errors=[str(list(e.path))+": "+e.message for e in Draft202012Validator(schema).iter_errors(value)]
        if not errors:
            if value["selected_skills"] != [profile["owner_skill"]] or value["selected_profile_id"] != profile_id:
                errors.append("dispatch only the canonical owner; profile ID belongs in selected_profile_id")
            if value["sidecar"]["profile_id"] != profile_id or value["sidecar"]["owner_skill"] != profile["owner_skill"]:
                errors.append("response/sidecar profile or owner mismatch")
            errors.extend(validate_sidecar(value["sidecar"],root)["errors"])
            if trusted_context is not None:
                errors.extend(_local_module(root, "trusted_profile_context").check(value["sidecar"], trusted_context))
                owner = _local_module(root, "owner_admission")
                if native_report_contract:
                    errors.extend(typed.check(value, profile["owner_skill"], root, trusted_context))
                    native = value["owner_output"]
                else:
                    native = owner.parse_json(value["owner_output_json"])
                errors.extend(owner.validate(native, profile["owner_skill"], root)["errors"])
                if native_report_contract and profile["owner_skill"] == "brief-architect":
                    if native.get("status") != owner.validate(native, profile["owner_skill"], root)["kernel_result"]["status"]:
                        errors.append("native declared brief status differs from kernel")
            # Detect explicit delegation, not merely mentioning provenance metadata.
            lines=[line for line in value["artifact"].splitlines() if not line.lstrip().startswith(">")]
            if any(re.search(r"(?:hypotheses|recommendations|follow.?up|stopping rule|procedures?|verification steps|hipotezy|zalecenia)[^.!?;\n]{0,120}(?:in|see|refer to|w) (?:the )?sidecar",line,re.I) for line in lines):
                errors.append("essential owner artifact content delegated to sidecar")
    except (ValueError,TypeError,KeyError,OSError) as exc:
        errors.append(str(exc))
    return {"accepted":not errors,"errors":errors,"execution_authorized":False,"scope":"Local response/provenance contract; independent owner semantic acceptance remains required"}


def validate_envelope(envelope: object, step: dict, root: Path = ROOT) -> dict:
    validate_profile_step(step,root)
    envelope=json.loads(_canonical(envelope))
    if not isinstance(envelope,dict): raise ValueError("profile envelope must be an object")
    spec=importlib.util.spec_from_file_location("profile_wrapper",root/"skills/skill-orchestrator-multiagent/scripts/validate_envelope.py")
    wrapper=importlib.util.module_from_spec(spec);spec.loader.exec_module(wrapper)
    errors=wrapper.validate_envelope(envelope,expected_type=step["envelope_out"],final=True)
    if envelope.get("type") != step["envelope_out"] or envelope.get("producer") != step["skill"]:
        errors.append("profile envelope owner/type mismatch")
    if envelope.get("dependencies",[]) != []:
        errors.append("standalone profile carrier must have empty dependencies")
    result=validate_response(envelope.get("payload"),step["profile_lock"]["id"],root,step.get("trusted_context"),step.get("native_report_contract"),step.get("report_as_of"))
    errors.extend(result["errors"])
    return {"accepted":not errors,"errors":errors,"envelope_id":envelope.get("id"),"envelope_hash":_hash(envelope),"payload_hash":_hash(envelope.get("payload")),"gate_lock_hash":_hash(step["gate_lock"]),"producer":step["skill"],"expected_type":step["envelope_out"],"profile_accepted":not errors,"execution_authorized":False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    route = sub.add_parser("select")
    route.add_argument("goal")
    validate = sub.add_parser("validate")
    validate.add_argument("input_json", type=Path)
    response=sub.add_parser("validate-response")
    response.add_argument("input_json",type=Path)
    response.add_argument("--profile",required=True,choices=sorted(OWNERS))
    response.add_argument("--trusted-context-json", type=Path)
    args = parser.parse_args()
    try:
        result = {"suggested_profiles": select(args.goal), "dispatch": False} if args.command == "select" else validate_response(json.loads(args.input_json.read_text()),args.profile,trusted_context=json.loads(args.trusted_context_json.read_text()) if args.trusted_context_json else None) if args.command == "validate-response" else validate_sidecar(json.loads(args.input_json.read_text()))
    except (ValueError, OSError) as exc:
        result = {"accepted": False, "errors": [str(exc)]}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if result.get("accepted") is False:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
