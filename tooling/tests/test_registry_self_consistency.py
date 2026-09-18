"""A skill's own advertised examples must route to it.

registry/skills.json carries trigger_examples and negative_trigger_examples for
every skill. They are copied into host adapters and shown to users as "say this
to get that skill" — so an example that the router sends elsewhere is a broken
promise, not a documentation nit. longform-publisher shipped one: its second
example scored zero on its own signals and went to release-readiness.

evals/routing/suite.json covers hand-picked cases; this covers the examples the
registry itself publishes, so the two cannot drift apart.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tooling"))
import run_routing_evals as routing  # noqa: E402


def _registry() -> list[dict]:
    return json.loads((ROOT / "registry" / "skills.json").read_text(encoding="utf-8"))["skills"]


@pytest.fixture(scope="module", autouse=True)
def _fresh_signals():
    routing.SIGNALS = routing.load_signals()


def _cases(key: str):
    return [
        pytest.param(s["id"], example, id=f"{s['id']}:{example[:40]}")
        for s in _registry()
        for example in s.get(key, [])
    ]


@pytest.mark.parametrize("skill,pattern", [
    pytest.param(s["id"], pat, id=f"{s['id']}:{pat[:30]}")
    for s in _registry() for _, pat in s["routing_signals"]
])
def test_every_routing_signal_compiles(skill: str, pattern: str) -> None:
    re.compile(pattern, re.IGNORECASE)


@pytest.mark.parametrize("skill,example", _cases("trigger_examples"))
def test_trigger_example_routes_to_its_own_skill(skill: str, example: str) -> None:
    got = routing.classify(example)
    assert got == skill, f"{example!r} routes to {got!r}; scores={routing.score_prompt(example)}"


@pytest.mark.parametrize("skill,example", _cases("negative_trigger_examples"))
def test_negative_example_does_not_route_to_the_skill(skill: str, example: str) -> None:
    got = routing.classify(example)
    assert got != skill, f"{example!r} is listed as a negative example yet routes to {skill}"


@pytest.mark.parametrize("skill", [s["id"] for s in _registry()])
def test_contract_fields_are_populated(skill: str) -> None:
    entry = next(s for s in _registry() if s["id"] == skill)
    for key in ("owns", "does_not_own", "trigger_examples", "negative_trigger_examples", "routing_signals"):
        assert entry.get(key), f"{skill}.{key} is empty"
