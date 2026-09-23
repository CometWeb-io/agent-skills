"""Freshness policy hooks for ledger validation.

Ledger-level freshness gates that require timezone-aware as_of live in ``temporal``.
Per-source TTL evaluation runs later via ``temporal_status`` during coverage/audit.
"""
from __future__ import annotations

from typing import Any, Dict

from .context import LedgerValidationState


def validate(ledger: Dict[str, Any], state: LedgerValidationState) -> None:
    return
