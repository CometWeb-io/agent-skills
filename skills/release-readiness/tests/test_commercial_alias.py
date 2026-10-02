"""`scope.commercial_model` must not be silently discarded.

SKILL.md used to name the scope field `commercial_model` while the engine read
only `scope.commercial`. A manifest written from the skill text therefore lost
its answer: `paid` became `unknown`, the billing gate was never derived, and the
operator saw an unresolved scope they had in fact resolved. The engine now
accepts the alias and refuses a contradiction.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("readiness_engine_alias", ROOT / "scripts" / "readiness_engine.py")
engine = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(engine)


def _scope(**extra):
    base = {
        "audience": "external",
        "risk_assessment_complete": True,
        "governance_surfaces": [],
        "risk_flags": {k: "no" for k in engine.SCOPE_FLAG_KEYS},
    }
    base.update(extra)
    return base


def test_alias_is_read_as_commercial() -> None:
    scope, gaps, _, _ = engine._normalize_scope(_scope(commercial_model="paid"), "saas_web")
    assert scope["commercial"] == "paid"
    assert "commercial" not in gaps
    assert "billing_entitlements" in engine._required_gates("saas_web", scope)


def test_alias_and_canonical_agreeing_is_fine() -> None:
    scope, _, _, _ = engine._normalize_scope(_scope(commercial="free", commercial_model="free"), "saas_web")
    assert scope["commercial"] == "free"


def test_alias_contradicting_canonical_is_rejected() -> None:
    with pytest.raises(engine.ManifestError, match="disagree"):
        engine._normalize_scope(_scope(commercial="free", commercial_model="paid"), "saas_web")


def test_invalid_alias_value_is_rejected() -> None:
    with pytest.raises(engine.ManifestError, match="scope.commercial invalid"):
        engine._normalize_scope(_scope(commercial_model="paid plan"), "saas_web")


def test_missing_both_stays_unknown() -> None:
    scope, gaps, _, _ = engine._normalize_scope(_scope(), "saas_web")
    assert scope["commercial"] == "unknown"
    assert "commercial" in gaps
