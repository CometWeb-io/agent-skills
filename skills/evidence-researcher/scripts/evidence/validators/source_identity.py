"""Source field and lineage identity validators."""
from __future__ import annotations

from typing import Any, Dict

from ..constants import PROVENANCE_LANES, SOURCE_CLASSES, SOURCE_ROLES
from ..util import _source_lineage_cycles
from .context import LedgerValidationState


def validate(ledger: Dict[str, Any], state: LedgerValidationState) -> None:
    errors = state.errors
    sources = state.sources
    source_ids = state.source_ids

    for i, source in enumerate(sources):
        if not isinstance(source, dict):
            continue
        sid = source.get("source_id") or f"sources[{i}]"
        if not source.get("title"):
            errors.append(f"{sid}.title is required")
        if not source.get("canonical_ref"):
            errors.append(f"{sid}.canonical_ref is required")
        if source.get("source_class") not in SOURCE_CLASSES:
            errors.append(f"{sid}.source_class is invalid")
        if source.get("source_role") not in SOURCE_ROLES:
            errors.append(f"{sid}.source_role is invalid")
        if source.get("provenance_lane") not in PROVENANCE_LANES:
            errors.append(f"{sid}.provenance_lane is invalid")
        derived = source.get("derived_from_source_ids", [])
        if not isinstance(derived, list):
            errors.append(f"{sid}.derived_from_source_ids must be a list")
            derived = []
        for parent in derived:
            if parent not in source_ids:
                errors.append(f"{sid} derives from unknown source_id {parent}")
            if parent == source.get("source_id"):
                errors.append(f"{sid} cannot derive from itself")

    for cycle in _source_lineage_cycles([src for src in sources if isinstance(src, dict)]):
        errors.append("source lineage cycle: " + " -> ".join(cycle))
