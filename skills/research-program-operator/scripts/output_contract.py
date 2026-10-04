"""Check a research-program-operator result against references/output-contract.md.

Replace these rules with the skill's real contract. Every rule is pinned by a
case in evals/cases.json: tooling/eval_strength.py disables one `if` at a time
and expects scripts/run_evals.py to fail, so a rule nothing pins is reported.
"""

from __future__ import annotations

STATUSES = {"complete", "partial", "blocked"}
STAGES = {"question", "protocol", "execution", "analysis", "manuscript", "closed"}
GATE_STATUSES = {"READY", "BLOCKED", "UNKNOWN", "NOT_REPORTED"}


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
    program = result.get("program")
    if not isinstance(program, dict):
        errors.append("program: required object")
        return errors
    for field in ("question", "as_of"):
        if not isinstance(program.get(field), str) or not program[field].strip():
            errors.append(f"program.{field}: required non-empty string")
    if program.get("stage") not in STAGES:
        errors.append("program.stage: invalid")
    studies = program.get("studies")
    if not isinstance(studies, list) or not studies:
        errors.append("program.studies: required non-empty list")
    else:
        study_ids: set[str] = set()
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
    for field in ("hypotheses", "gates", "next_studies", "governance", "unknowns"):
        if not isinstance(program.get(field), list):
            errors.append(f"program.{field}: required list")
    for index, gate in enumerate(program.get("gates", []) if isinstance(program.get("gates"), list) else []):
        if not isinstance(gate, dict):
            errors.append(f"program.gates[{index}]: must be object")
            continue
        if gate.get("status") not in GATE_STATUSES:
            errors.append(f"program.gates[{index}].status: invalid")
    handoff = result.get("research_handoff")
    if not isinstance(handoff, dict):
        errors.append("research_handoff: required object")
    else:
        for field in ("status", "target"):
            if not isinstance(handoff.get(field), str) or not handoff[field].strip():
                errors.append(f"handoff.{field}: required")
        if handoff.get("status") not in GATE_STATUSES:
            errors.append("handoff.status: invalid")
    return errors
