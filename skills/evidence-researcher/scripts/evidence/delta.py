"""Ledger delta comparison."""
from __future__ import annotations

from typing import Any, Dict

from .constants import VERSION
from .identity import fingerprint_source, pack_hash
from .util import _id_index, _norm_text


def delta(old: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    old_claims = _id_index([c for c in old.get("claims", []) if isinstance(c, dict)], "claim_id")
    new_claims = _id_index([c for c in new.get("claims", []) if isinstance(c, dict)], "claim_id")
    old_sources = [s for s in old.get("sources", []) if isinstance(s, dict)]
    new_sources = [s for s in new.get("sources", []) if isinstance(s, dict)]
    old_by_fp = {fingerprint_source(s): s for s in old_sources}
    new_by_fp = {fingerprint_source(s): s for s in new_sources}

    added_claims = sorted(set(new_claims) - set(old_claims))
    removed_claims = sorted(set(old_claims) - set(new_claims))
    changed_claims = []
    for cid in sorted(set(old_claims) & set(new_claims)):
        before = old_claims[cid]
        after = new_claims[cid]
        changes = {}
        for field in ("claim_text", "claim_type", "materiality", "status", "confidence"):
            if before.get(field) != after.get(field):
                changes[field] = {"old": before.get(field), "new": after.get(field)}
        if changes:
            changed_claims.append({"claim_id": cid, "changes": changes})

    added_sources = [new_by_fp[fp].get("source_id") for fp in sorted(set(new_by_fp) - set(old_by_fp))]
    removed_sources = [old_by_fp[fp].get("source_id") for fp in sorted(set(old_by_fp) - set(new_by_fp))]
    old_by_ref = {_norm_text(s.get("canonical_ref")): s for s in old_sources if s.get("canonical_ref")}
    new_by_ref = {_norm_text(s.get("canonical_ref")): s for s in new_sources if s.get("canonical_ref")}
    source_version_changes = []
    for ref in sorted(set(old_by_ref) & set(new_by_ref)):
        before = old_by_ref[ref].get("source_version")
        after = new_by_ref[ref].get("source_version")
        if before != after:
            source_version_changes.append({"canonical_ref": new_by_ref[ref].get("canonical_ref"), "old": before, "new": after})

    old_ctr = _id_index([c for c in old.get("contradictions", []) if isinstance(c, dict)], "contradiction_id")
    new_ctr = _id_index([c for c in new.get("contradictions", []) if isinstance(c, dict)], "contradiction_id")
    contradiction_changes = []
    for cid in sorted(set(old_ctr) & set(new_ctr)):
        if old_ctr[cid].get("resolution") != new_ctr[cid].get("resolution"):
            contradiction_changes.append({
                "contradiction_id": cid,
                "old": old_ctr[cid].get("resolution"),
                "new": new_ctr[cid].get("resolution"),
            })

    return {
        "old_pack_hash": pack_hash(old),
        "new_pack_hash": pack_hash(new),
        "added_claim_ids": added_claims,
        "removed_claim_ids": removed_claims,
        "changed_claims": changed_claims,
        "added_source_ids": added_sources,
        "removed_source_ids": removed_sources,
        "source_version_changes": source_version_changes,
        "contradiction_resolution_changes": contradiction_changes,
        "kernel_version": VERSION,
    }

