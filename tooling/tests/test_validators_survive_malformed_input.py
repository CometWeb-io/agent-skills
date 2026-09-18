"""A validator must report malformed input, not die on it.

Membership written as `value in ALLOWED` raises TypeError when the value is a
list or a dict, and every value these functions read comes from a JSON file the
caller supplies. Two kernels did exactly that — product-teardown's ledger
validator in fourteen places, longform-publisher's report validator in ten — so
a malformed file killed the validator instead of being validated.

This walks every validator in the repo rather than the two that were caught.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

# (module path, function name). Functions are expected to return a result for
# bad input, or raise a *deliberate* ValueError — never TypeError/AttributeError.
VALIDATORS = [
    ("skills/product-teardown/scripts/validate_pattern_ledger.py", "validate"),
    ("skills/longform-publisher/scripts/publication_kernel.py", "validate_report"),
    ("skills/cometweb-context/scripts/validate_context_envelope.py", "validate"),
    ("skills/evidence-researcher/scripts/evidence_kernel.py", "validate_ledger"),
    ("skills/repo-to-roadmap/scripts/roadmap_kernel.py", "validate_roadmap"),
    # validate_acceptance takes (item_id, criteria); the payload is its second
    # argument, so it is swept with a fixed id below.
    ("skills/repo-to-roadmap/scripts/roadmap_kernel.py", "validate_acceptance:2"),
    ("skills/repo-to-roadmap/scripts/roadmap_kernel.py", "validate_target_contract"),
    ("tooling/validate_envelope.py", "validate_envelope"),
]

# Shapes a hostile or simply broken JSON file can produce. The enum-ish keys are
# the ones that get compared against a set.
MALFORMED = [
    pytest.param([], id="root-is-a-list"),
    pytest.param("text", id="root-is-a-string"),
    pytest.param(None, id="root-is-null"),
    pytest.param(
        {k: [] for k in ("schema", "protocol_version", "kind", "mode", "status",
                         "state", "verdict", "shape", "current_stage",
                         "publication_type", "materiality")},
        id="enum-fields-are-lists",
    ),
    pytest.param(
        {k: {"nested": 1} for k in ("schema", "mode", "status", "shape", "verdict")},
        id="enum-fields-are-dicts",
    ),
]


def load(rel: str):
    path = ROOT / rel
    spec = importlib.util.spec_from_file_location(f"probe_{path.stem}", path)
    assert spec and spec.loader, f"cannot load {rel}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("rel,function", VALIDATORS, ids=lambda v: Path(v).stem if "/" in str(v) else v)
@pytest.mark.parametrize("payload", MALFORMED)
def test_validator_does_not_crash(rel: str, function: str, payload) -> None:
    name, _, arity = function.partition(":")
    fn = getattr(load(rel), name)
    args = ("probe-id", payload) if arity == "2" else (payload,)
    try:
        fn(*args)
    except ValueError:
        pass  # a deliberate, reported rejection
    except (TypeError, AttributeError, KeyError, IndexError) as exc:
        pytest.fail(f"{rel}:{function} crashed on {payload!r}: {type(exc).__name__}: {exc}")


def test_every_listed_validator_exists() -> None:
    # A renamed function would otherwise silently drop out of the sweep.
    for rel, function in VALIDATORS:
        assert (ROOT / rel).is_file(), f"missing {rel}"
        name = function.partition(":")[0]
        assert callable(getattr(load(rel), name, None)), f"{rel} has no {name}()"
