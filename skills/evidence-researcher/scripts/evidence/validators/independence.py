"""Independence-group and duplicate-fingerprint validators."""
from __future__ import annotations

from typing import Any, Dict, List

from ..identity import fingerprint_source
from ..util import _norm_text
from .context import LedgerValidationState


def validate(ledger: Dict[str, Any], state: LedgerValidationState) -> None:
    warnings = state.warnings
    sources = state.sources

    source_fingerprints: Dict[str, List[str]] = {}
    canonical_groups: Dict[str, set[str]] = {}
    for source in sources:
        if not isinstance(source, dict):
            continue
        fp = fingerprint_source(source)
        source_fingerprints.setdefault(fp, []).append(str(source.get("source_id")))
        cref = _norm_text(source.get("canonical_ref"))
        if cref:
            canonical_groups.setdefault(cref, set()).add(str(source.get("independence_group") or ""))

    for _fingerprint, sids in source_fingerprints.items():
        if len(sids) > 1:
            warnings.append(f"duplicate source fingerprint across source_ids: {', '.join(sorted(sids))}")
    for cref, groups in canonical_groups.items():
        nonempty = {g for g in groups if g}
        if len(nonempty) > 1:
            warnings.append(f"same canonical_ref assigned to multiple independence groups: {cref}")
