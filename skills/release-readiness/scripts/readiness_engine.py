#!/usr/bin/env python3
"""Deterministic release-readiness gate engine v2.

The engine intentionally separates:
- scope completeness,
- required-gate completeness,
- evidence admissibility,
- governance gates,
- weighted readiness,
- release verdict.

A high score can never override a binding failure, a missing required gate,
or an unresolved governance blocker.

Implementation lives in the ``readiness`` package; this module is a thin facade
that preserves the historical import path and public API for tests and CLI.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from readiness import *  # noqa: F403
from readiness import main  # noqa: F401
from readiness import (  # noqa: F401 — private helpers used by bootstrap/tests
    _binding_evidence_issues,
    _binding_evidence_valid,
    _candidate_evidence_matches,
    _candidate_matches,
    _contract_check,
    _contract_hash,
    _control_valid,
    _domain_weights,
    _effective_status,
    _evidence_obj,
    _evidence_time_issues,
    _identity_value,
    _invalid_constant,
    _load,
    _normalize_check,
    _normalize_governance_gate,
    _normalize_scope,
    _num,
    _parse_dt,
    _pct,
    _release_ids,
    _release_identity_gaps,
    _required_gates,
    _revalidation_triggers,
    _risk_acceptance_valid,
    _slim_check,
    _snapshot_hash,
    _summarize_domain,
    _text,
    _thresholds,
    _unique_pairs,
    _validate_json,
)

if __name__ == "__main__":
    raise SystemExit(main())
