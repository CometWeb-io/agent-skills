"""Run the canonical owner's existing validator. No semantic truth claim."""
import importlib.util
import json
import sys
from pathlib import Path

def module(root, name, relative):
    spec = importlib.util.spec_from_file_location(name, root / relative)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result

def validate(value, owner, root: Path):
    errors = []
    if not isinstance(value, dict) or not value:
        return {"accepted": False, "errors": ["nonempty structured owner_output required"]}
    if owner == "brief-architect":
        result = module(root, "profile_brief_owner", "skills/brief-architect/scripts/kernel.py").readiness(value)
        if result["status"] not in {"READY", "PROVISIONAL", "BLOCKED"}:
            errors.append("canonical brief owner invalid: " + str(result))
        if not value.get("acceptance_criteria"):
            errors.append("owner brief requires substantive acceptance criteria")
    elif owner == "product-operator":
        result = module(root, "profile_product_owner", "skills/product-operator/scripts/operator_kernel.py").validate_report(value)
        errors.extend(result["errors"])
        if not any(value.get(k) for k in ("blockers", "verify_now", "decision_now", "now")):
            errors.append("owner operator requires a bounded actionable item")
    elif owner == "content-writer":
        result = module(root, "profile_writer_owner", "skills/content-writer/scripts/kernel.py").validate(value)
        errors.extend(result["errors"])
        if not value.get("claims") or value.get("mode") != "DRAFT":
            errors.append("owner writer requires draft claim report; no publication authorization")
    elif owner == "web-app-auditor":
        result = module(root, "profile_audit_owner", "skills/web-app-auditor/scripts/validate_report.py").validate(value)
        errors.extend(result.errors)
        if not value.get("findings") or value.get("environment", {}).get("mutationPolicy") != "read-only":
            errors.append("owner audit requires supplied findings and read-only scope")
        result = {"errors": result.errors, "warnings": result.warnings}
    else:
        errors.append("unsupported canonical owner")
        result = {}
    return {"accepted": not errors, "errors": errors, "kernel_result": result,
            "scope": "native owner structural checks; artifact semantics independently graded"}


def parse_json(text):
    if not isinstance(text, str):
        raise ValueError("owner_output_json must be JSON text")
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate native owner key: " + key)
            result[key] = value
        return result
    value = json.loads(text, object_pairs_hook=pairs)
    json.dumps(value, allow_nan=False)
    return value
