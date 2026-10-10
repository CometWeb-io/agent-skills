"""Validate research-program state without inferring publication authorization."""

from __future__ import annotations

from datetime import date, datetime

STATUSES = ("complete", "partial", "blocked",)
STAGES = ("question", "protocol", "execution", "analysis", "manuscript", "closed",)
GATE_STATUSES = ("READY", "BLOCKED", "UNKNOWN", "NOT_REPORTED",)
STUDY_STATUSES = ("planned", "reported", "executed", "failed",)
HANDOFF_STAGES = {"next-study": STAGES,
                  "science-roaster": ("protocol", "execution", "analysis", "manuscript", "closed"),
                  "longform-publisher": ("manuscript", "closed")}


def valid_date(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        if len(value) == 10:
            date.fromisoformat(value)
            return True
        return datetime.fromisoformat(value.replace("Z", "+00:00")).tzinfo is not None
    except ValueError:
        return False


def validate(result: object) -> list[str]:
    if not isinstance(result, dict):
        return ["result: must be an object"]
    errors: list[str] = []
    summary = result.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        errors.append("summary: required non-empty string")
    if result.get("status") not in STATUSES:
        errors.append("status: must be complete, partial or blocked")
    not_verified = result.get("not_verified")
    if not isinstance(not_verified, list):
        errors.append("not_verified: required list")
    elif result.get("status") == "complete" and not_verified:
        errors.append("status: complete contradicts a non-empty not_verified")
    if isinstance(not_verified, list) and any(not isinstance(v, str) or not v.strip() for v in not_verified):
        errors.append("not_verified: entries must be non-empty strings")
    program = result.get("program")
    if not isinstance(program, dict):
        errors.append("program: required object")
        return errors
    for field in ("question", "as_of"):
        if not isinstance(program.get(field), str) or not program[field].strip():
            errors.append(f"program.{field}: required non-empty string")
    if not valid_date(program.get("as_of")):
        errors.append("program.as_of: must be ISO date or timezone-aware timestamp")
    if program.get("stage") not in STAGES:
        errors.append("program.stage: invalid")
    studies = program.get("studies")
    study_ids: set[str] = set()
    if not isinstance(studies, list) or not studies:
        errors.append("program.studies: required non-empty list")
    else:
        for index, study in enumerate(studies):
            prefix = f"program.studies[{index}]"
            if not isinstance(study, dict):
                errors.append(f"{prefix}: must be object")
                continue
            study_id = study.get("id")
            if not isinstance(study_id, str) or not study_id.strip():
                errors.append(f"{prefix}.id: required")
            elif study_id in study_ids:
                errors.append(f"{prefix}.id: duplicate")
            else:
                study_ids.add(study_id)
            for field in ("name", "status", "estimand"):
                if not isinstance(study.get(field), str) or not study[field].strip():
                    errors.append(f"{prefix}.{field}: required")
            if study.get("status") not in STUDY_STATUSES:
                errors.append(f"{prefix}.status: invalid")
            if isinstance(study.get("estimand"), str) and study["estimand"].strip().casefold() in {"unknown", "not reported", "tbd"}:
                errors.append(f"{prefix}.estimand: must define the quantity being estimated")
            if result.get("status") == "complete" and (study.get("status") not in ("reported", "executed")
                    or not isinstance(study.get("evidence"), list) or not study["evidence"]
                    or any(not isinstance(v, str) or not v.strip() for v in study["evidence"])):
                errors.append(f"{prefix}: complete requires reported/executed study with evidence locators")
    for field in ("hypotheses", "gates", "next_studies", "governance", "unknowns"):
        if not isinstance(program.get(field), list):
            errors.append(f"program.{field}: required list")
    for field in ("hypotheses", "governance", "unknowns"):
        rows = program.get(field)
        if isinstance(rows, list) and any(not isinstance(v, str) or not v.strip() for v in rows):
            errors.append(f"program.{field}: entries must be non-empty strings")
    if isinstance(program.get("next_studies"), list):
        for index, study in enumerate(program["next_studies"]):
            prefix = f"program.next_studies[{index}]"
            if not isinstance(study, dict):
                errors.append(f"{prefix}: must be object")
                continue
            for field in ("id", "estimand", "falsifier", "evidence_requirement", "stop_rule", "continue_rule"):
                if not isinstance(study.get(field), str) or not study[field].strip():
                    errors.append(f"{prefix}.{field}: required")
            dependencies = study.get("dependencies")
            if not isinstance(dependencies, list) or any(not isinstance(v, str) or v not in study_ids for v in dependencies):
                errors.append(f"{prefix}.dependencies: must reference existing studies")
    for index, gate in enumerate(program.get("gates", []) if isinstance(program.get("gates"), list) else []):
        if not isinstance(gate, dict):
            errors.append(f"program.gates[{index}]: must be object")
            continue
        if gate.get("status") not in GATE_STATUSES:
            errors.append(f"program.gates[{index}].status: invalid")
        if not isinstance(gate.get("id"), str) or not gate["id"].strip():
            errors.append(f"program.gates[{index}].id: required")
        if gate.get("status") == "READY" and (not isinstance(gate.get("evidence"), list) or not gate["evidence"]
                or any(not isinstance(v, str) or not v.strip() for v in gate["evidence"])):
            errors.append(f"program.gates[{index}].evidence: READY requires evidence locators")
    if result.get("status") == "complete":
        for field in ("governance", "unknowns"):
            if program.get(field):
                errors.append(f"program.{field}: complete requires no unresolved items")
        if not isinstance(program.get("gates"), list) or not program["gates"] or any(
                not isinstance(g, dict) or g.get("status") != "READY" for g in program["gates"]):
            errors.append("program.gates: complete requires non-empty READY gates")
    handoff = result.get("research_handoff")
    if not isinstance(handoff, dict):
        errors.append("research_handoff: required object")
    else:
        for field in ("status", "target"):
            if not isinstance(handoff.get(field), str) or not handoff[field].strip():
                errors.append(f"handoff.{field}: required")
        if handoff.get("status") not in GATE_STATUSES:
            errors.append("handoff.status: invalid")
        if handoff.get("target") not in ("next-study", "science-roaster", "longform-publisher"):
            errors.append("handoff.target: must be next-study, science-roaster or longform-publisher; never publication")
        if handoff.get("status") == "READY":
            target = handoff.get("target")
            stages = HANDOFF_STAGES.get(target, ()) if isinstance(target, str) else ()
            if program.get("stage") not in stages:
                errors.append("handoff.target: READY target is incompatible with program.stage")
            if handoff.get("target") == "next-study" and not program.get("next_studies"):
                errors.append("program.next_studies: READY next-study requires a bounded study plan")
        if handoff.get("status") == "READY" and (result.get("status") != "complete" or errors):
            errors.append("handoff.status: READY requires a valid complete program; not publication authorization")
    return errors


def assess(result: object) -> dict:
    errors = validate(result)
    return {"status": "INVALID" if errors else result["status"].upper(), "errors": errors}
