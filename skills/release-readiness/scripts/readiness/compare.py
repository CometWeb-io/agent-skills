"""Delta analysis between successive readiness assessments."""

from __future__ import annotations

from typing import Any, Dict

from .evaluate import evaluate
from .manifest import IMMUTABLE_KEYS, ManifestError, _parse_dt


def compare(current_manifest: Dict[str, Any], previous_manifest: Dict[str, Any], *, expected_contract_hash: str | None = None) -> Dict[str, Any]:
    previous = evaluate(previous_manifest)
    current = evaluate(current_manifest, expected_contract_hash=expected_contract_hash or previous["contract_hash"])
    def ids(rows):
        return {r["id"] for r in rows}
    cur_block, prev_block = ids(current["blocking_failures"]), ids(previous["blocking_failures"])
    cur_unknown, prev_unknown = ids(current["binding_unknowns"]), ids(previous["binding_unknowns"])
    prev_checks = {c["id"]: c for c in previous_manifest["checks"]}
    cur_checks = {c["id"]: c for c in current_manifest["checks"]}
    changed, weakened = [], set()
    contract_keys = ("gate", "domain", "title", "binding", "severity", "required_evidence", "applicable", "weight")
    for cid in sorted(prev_checks.keys() | cur_checks.keys()):
        a, b = prev_checks.get(cid), cur_checks.get(cid)
        if a is None or b is None:
            changed.append({"id": cid, "change": "added" if a is None else "removed"})
            continue
        keys = (*contract_keys, "status", "evidence_level", "freshness", "evidence")
        diffs = {k: {"from": a.get(k), "to": b.get(k)} for k in keys if a.get(k) != b.get(k)}
        if diffs:
            changed.append({"id": cid, "change": "modified", "fields": diffs})
        if any(k in diffs for k in contract_keys):
            weakened.add(cid)
    removed = prev_checks.keys() - cur_checks.keys()
    # A disappearance or downgrade is not a verified resolution.
    passing = {cid for cid, state in current["check_states"].items() if state in ("pass", "pass_with_controls")} - weakened
    resolved_blocks = prev_block & passing
    resolved_unknowns = prev_unknown & passing
    previous_release, current_release = previous["release"], current["release"]
    environment_changed = previous_release.get("environment") != current_release.get("environment")
    config_changed = previous_release.get("config_digest") != current_release.get("config_digest")
    if environment_changed or config_changed:
        # Evidence from a different deployment context is not closure of this context.
        resolved_blocks, resolved_unknowns = set(), set()
    requirements_changed = previous["contract_hash"] != current["contract_hash"]
    comparable = not (environment_changed or config_changed or requirements_changed)
    current_time, previous_time = _parse_dt(current_release.get("as_of")), _parse_dt(previous_release.get("as_of"))
    if current_time is None or previous_time is None or current_time < previous_time:
        raise ManifestError("delta chronology is invalid")
    identity_keys = (*IMMUTABLE_KEYS, "id", "tag", "deployment_id")
    prev_missing = set(previous["missing_required_gates"])
    cur_required = set(current["required_gates"])
    provided_gates = (prev_missing - set(current["missing_required_gates"])) & cur_required
    resolved_gates = {gate for gate in provided_gates
                      if all(current["check_states"][c["id"]] in ("pass", "pass_with_controls")
                             for c in current_manifest["checks"] if c.get("gate") == gate and c.get("binding") is True)}
    return {
        "previous_verdict": previous["verdict"], "current_verdict": current["verdict"],
        "verdict_changed": previous["verdict"] != current["verdict"],
        "candidate_changed": any(previous_release.get(k) != current_release.get(k) for k in identity_keys),
        "environment_changed": environment_changed, "configuration_changed": config_changed,
        "requirements_changed": requirements_changed, "scores_comparable": comparable,
        "contract_mismatch": current["contract_mismatch"],
        "score_delta": round(current["gating_metrics"]["readiness_score"] - previous["gating_metrics"]["readiness_score"], 1) if comparable else None,
        "coverage_delta": round(current["gating_metrics"]["evidence_coverage"] - previous["gating_metrics"]["evidence_coverage"], 1) if comparable else None,
        "new_blockers": sorted(cur_block - prev_block), "resolved_blockers": sorted(resolved_blocks),
        "removed_blockers": sorted(prev_block & removed),
        "blockers_no_longer_proven_resolved": sorted(prev_block - cur_block - resolved_blocks),
        "new_binding_unknowns": sorted(cur_unknown - prev_unknown), "resolved_binding_unknowns": sorted(resolved_unknowns),
        "removed_binding_unknowns": sorted(prev_unknown & removed),
        "changed_check_requirements": sorted(weakened),
        "new_missing_required_gates": sorted(set(current["missing_required_gates"]) - set(previous["missing_required_gates"])),
        "resolved_missing_required_gates": sorted(resolved_gates),
        "provided_required_gates": sorted(provided_gates),
        "no_longer_required_gates": sorted(set(previous["required_gates"]) - cur_required),
        "changed_checks": changed,
        "previous_snapshot_hash": previous["snapshot_hash"], "current_snapshot_hash": current["snapshot_hash"],
    }
