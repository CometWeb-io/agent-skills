"""Parent-authored input commitments. They prove input fidelity, never real-world truth."""
import copy
import hashlib
import json

NUMERIC = {
    "conversion-audit": ("baseline_rate",),
    "experiment-design": ("baseline_rate", "sample_size_per_variant", "mde_absolute", "alpha", "power"),
    "activation-onboarding": ("activation_rate",),
    "sop-documentation": (),
}

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()

def digest(value):
    return "sha256:" + hashlib.sha256(canonical(value)).hexdigest()

def commit(profile_id, original_brief, sources, expected, derived=None):
    value = {"schema": "cometweb.trusted-profile-context/v1", "profile_id": profile_id,
             "original_brief": original_brief, "sources": copy.deepcopy(sources),
             "expected_result": copy.deepcopy(expected), "derived": copy.deepcopy(derived or {})}
    validate(value)
    return value

def validate(value):
    canonical(value)
    if not isinstance(value, dict) or set(value) != {"schema", "profile_id", "original_brief", "sources", "expected_result", "derived"}:
        raise ValueError("invalid trusted context fields")
    if value["schema"] != "cometweb.trusted-profile-context/v1" or value["profile_id"] not in NUMERIC:
        raise ValueError("invalid trusted context version/profile")
    if not isinstance(value["original_brief"], str) or not value["original_brief"].strip():
        raise ValueError("original brief must be supplied by parent")
    sources = value["sources"]
    if not isinstance(sources, list) or not sources:
        raise ValueError("trusted source inventory required")
    ids = []
    for row in sources:
        if not isinstance(row, dict) or set(row) != {"id", "kind", "reference", "summary"}:
            raise ValueError("invalid trusted source fields")
        if any(not isinstance(v, str) or not v.strip() for v in row.values()):
            raise ValueError("trusted sources require nonblank text")
        if row["kind"] not in {"USER_INPUT", "OBSERVED", "FRAMEWORK", "HYPOTHESIS"}:
            raise ValueError("invalid trusted source kind")
        ids.append(row["id"])
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate trusted source ID")
    expected = value["expected_result"]
    if not isinstance(expected, dict) or not set(NUMERIC[value["profile_id"]]).issubset(expected):
        raise ValueError("all quantitative fields need explicit supplied value or null")
    if not isinstance(value["derived"], dict):
        raise ValueError("derived facts must be declared")
    for key in NUMERIC[value["profile_id"]]:
        n = expected[key]
        if n is not None and (isinstance(n, bool) or not isinstance(n, (int, float)) or not 0 <= n <= (10**9 if key == "sample_size_per_variant" else 1)):
            raise ValueError("invalid protected quantitative field: " + key)
    for key, derivation in value["derived"].items():
        if key not in NUMERIC[value["profile_id"]] or not isinstance(derivation, dict) or set(derivation) != {"numerator", "denominator", "source_ids"}:
            raise ValueError("invalid derived fact")
        n, d = derivation["numerator"], derivation["denominator"]
        if any(isinstance(x, bool) or not isinstance(x, int) for x in (n, d)) or d <= 0 or not 0 <= n <= d:
            raise ValueError("invalid cohort arithmetic")
        if not derivation["source_ids"] or any(i not in ids for i in derivation["source_ids"]):
            raise ValueError("derived fact lacks original source")
        by_id = {s["id"]: s for s in sources}
        if any(by_id[i]["kind"] not in {"USER_INPUT", "OBSERVED"} for i in derivation["source_ids"]):
            raise ValueError("framework cannot establish cohort arithmetic")
        if expected.get(key) != n / d:
            raise ValueError("derived fact differs from declared arithmetic")
    return value

def check(sidecar, context):
    validate(context)
    errors = []
    if sidecar.get("profile_id") != context["profile_id"]:
        errors.append("trusted input profile mismatch")
    original = {s["id"]: s for s in context["sources"]}
    for row in sidecar.get("evidence", []):
        if original.get(row.get("id")) != row:
            errors.append("new or changed source identity/content/kind: " + str(row.get("id")))
    result = sidecar.get("result", {})
    for key, value in context["expected_result"].items():
        actual = result.get(key)
        if type(actual) is not type(value) and not (isinstance(actual, (int, float)) and not isinstance(actual, bool) and isinstance(value, (int, float)) and not isinstance(value, bool)):
            errors.append("input-bound type changed: " + key)
        elif actual != value:
            errors.append("input-bound value changed: " + key)
    return errors
