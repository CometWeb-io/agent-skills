"""Mutable state shared across ledger validators."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Set


@dataclass
class LedgerValidationState:
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    contract: Dict[str, Any] = field(default_factory=dict)
    claims: List[Any] = field(default_factory=list)
    sources: List[Any] = field(default_factory=list)
    evidence: List[Any] = field(default_factory=list)
    contradictions: List[Any] = field(default_factory=list)
    searches: List[Any] = field(default_factory=list)
    gaps: List[Any] = field(default_factory=list)
    claim_ids: Set[str] = field(default_factory=set)
    source_ids: Set[str] = field(default_factory=set)
    accepted_support_by_claim: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    accepted_contradict_by_claim: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    completed_falsifier_claims: Set[str] = field(default_factory=set)
    contradiction_claim_ids: Set[str] = field(default_factory=set)
