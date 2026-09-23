"""Snapshot hashing and baseline/delta invalidation."""
from __future__ import annotations

import copy
import hashlib
from collections import defaultdict, deque
from typing import Any, Dict, List

from .constants import SCHEMA_VERSION
from .inventory import file_coverage_report
from .util import by_id, changed_ids, normalized, stable_json


def snapshot_core(payload: Dict[str, Any]) -> Dict[str, Any]:
    core = copy.deepcopy(payload)
    for key in ("snapshot_hash", "snapshot_hash_short", "validation"):
        core.pop(key, None)
    return core


def snapshot_report(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("roadmap payload must be an object")
    core = snapshot_core(payload)
    encoded = stable_json(core).encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()
    return {
        "schema_version": payload.get("schema_version", SCHEMA_VERSION),
        "snapshot_hash": f"sha256:{digest}",
        "snapshot_hash_short": digest[:16],
        "canonical_bytes": len(encoded),
    }


def _snapshot_consistency_errors(payload: Dict[str, Any]) -> List[str]:
    expected = snapshot_report(payload)
    return [f"{key} does not match supplied roadmap content" for key in ("snapshot_hash", "snapshot_hash_short")
            if key in payload and payload[key] != expected[key]]


def assessment_contract_sha256(payload: Dict[str, Any]) -> str:
    """Fingerprint the declared scope, not its approval or external authenticity."""
    assessment = payload.get("assessment", {})
    if not isinstance(assessment, dict):
        raise ValueError("assessment must be an object")
    contract = {
        "schema": "cometweb.roadmap-assessment-contract/v1",
        "mode": assessment.get("mode"),
        "repos": assessment.get("repos", []),
        "file_review_policy": assessment.get("file_review_policy", "all_inspected"),
        "target_contract": payload.get("target_contract"),
    }
    return hashlib.sha256(stable_json(contract).encode("utf-8")).hexdigest()


def delta_report(before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(before, dict) or not isinstance(after, dict):
        raise ValueError("before and after must be objects")

    if _snapshot_consistency_errors(before) or _snapshot_consistency_errors(after):
        raise ValueError("supplied snapshot hash does not match roadmap content")
    file_coverage_changed = stable_json(before.get("file_coverage")) != stable_json(after.get("file_coverage"))
    contract_changed = assessment_contract_sha256(before) != assessment_contract_sha256(after)
    file_coverage_issues = {label: report["errors"] for label, report in
                            (("before", file_coverage_report(before)), ("after", file_coverage_report(after)))
                            if report["errors"]}
    changed_claims, added_claims, removed_claims = changed_ids(before.get("claims", []), after.get("claims", []), "claim_id")
    changed_capabilities, added_capabilities, removed_capabilities = changed_ids(before.get("capabilities", []), after.get("capabilities", []), "capability_id")
    changed_items, added_items, removed_items = changed_ids(before.get("items", []), after.get("items", []), "id")

    target_changed = stable_json(before.get("target_contract", {})) != stable_json(after.get("target_contract", {}))
    coverage_changed = stable_json(before.get("coverage", [])) != stable_json(after.get("coverage", []))
    assessment_scope_changed = stable_json(before.get("assessment", {}).get("repos", [])) != stable_json(after.get("assessment", {}).get("repos", []))

    after_items = by_id(after.get("items", []), "id")
    after_capabilities = by_id(after.get("capabilities", []), "capability_id")
    revalidate: set[str] = set(changed_items)
    changed_claim_set = set(changed_claims)
    changed_cap_set = set(changed_capabilities)

    # A capability becomes suspect when any binding claim it references changed,
    # even when the capability row itself has not yet been updated.
    affected_capabilities = set(changed_cap_set)
    for cap_id, capability in after_capabilities.items():
        refs = {normalized(ref) for ref in (capability.get("claim_refs") or [])}
        if refs & changed_claim_set:
            affected_capabilities.add(cap_id)

    for item_id, item in after_items.items():
        refs = {normalized(ref) for ref in (item.get("problem_claim_refs") or [])}
        cap_refs = {normalized(ref) for ref in (item.get("capability_refs") or [])}
        if refs & changed_claim_set or cap_refs & affected_capabilities:
            revalidate.add(item_id)

    if target_changed or assessment_scope_changed or file_coverage_changed or contract_changed or file_coverage_issues:
        revalidate.update(after_items)

    outgoing: Dict[str, List[str]] = defaultdict(list)
    for item_id, item in after_items.items():
        for dep in item.get("depends_on", []) or []:
            dep_id = normalized(dep)
            if dep_id in after_items:
                outgoing[dep_id].append(item_id)

    queue = deque(sorted(revalidate))
    while queue:
        node = queue.popleft()
        for child in outgoing[node]:
            if child not in revalidate:
                revalidate.add(child)
                queue.append(child)

    source_fingerprints_before = sorted(
        normalized(row.get("fingerprint"))
        for claim in before.get("claims", []) if isinstance(claim, dict)
        for row in claim.get("evidence", []) if isinstance(row, dict) and row.get("fingerprint")
    )
    source_fingerprints_after = sorted(
        normalized(row.get("fingerprint"))
        for claim in after.get("claims", []) if isinstance(claim, dict)
        for row in claim.get("evidence", []) if isinstance(row, dict) and row.get("fingerprint")
    )
    fingerprints_changed = source_fingerprints_before != source_fingerprints_after

    validity = "REVALIDATE" if (revalidate or target_changed or coverage_changed or assessment_scope_changed or fingerprints_changed or file_coverage_changed or contract_changed or file_coverage_issues) else "VALID"

    return {
        "before_snapshot": snapshot_report(before)["snapshot_hash"],
        "after_snapshot": snapshot_report(after)["snapshot_hash"],
        "target_contract_changed": target_changed,
        "assessment_scope_changed": assessment_scope_changed,
        "coverage_changed": coverage_changed,
        "file_coverage_changed": file_coverage_changed,
        "assessment_contract_changed": contract_changed,
        "file_coverage_issues": file_coverage_issues,
        "source_fingerprints_changed": fingerprints_changed,
        "changed_claim_ids": changed_claims,
        "added_claim_ids": added_claims,
        "removed_claim_ids": removed_claims,
        "changed_capability_ids": changed_capabilities,
        "affected_capability_ids": sorted(affected_capabilities),
        "added_capability_ids": added_capabilities,
        "removed_capability_ids": removed_capabilities,
        "changed_item_ids": changed_items,
        "added_item_ids": added_items,
        "removed_item_ids": removed_items,
        "revalidate_item_ids": sorted(revalidate),
        "roadmap_validity": validity,
        "note": "Revalidation propagates through hard item dependencies. It does not infer hidden runtime coupling that was never modeled.",
    }

