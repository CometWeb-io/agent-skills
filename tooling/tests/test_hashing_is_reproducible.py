"""Content hashes must depend on content, and on nothing else.

Immutable snapshots, payload digests and contract hashes are what this
repository builds its release and decision records on. They break silently: one
iteration over a set, one timestamp folded into the payload, and two runs over
identical input disagree — while every example-based test still passes, because
each pins one run.

These checks vary the three things that actually move underneath a hash: the
run itself, the ordering of JSON keys, and PYTHONHASHSEED.
"""

from __future__ import annotations

import importlib.util
import json
import random
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

PAYLOAD = {
    "decision": "ship or wait",
    "options": ["a", "b", "c"],
    "evidence": [
        {"id": "e1", "claim": "x", "freshness": "CURRENT"},
        {"id": "e2", "claim": "y", "freshness": "STALE"},
    ],
    "gates": {"legal": "CLEAR", "privacy": "NOT_REQUIRED"},
    "score": 0.42,
}

HASHERS = [
    ("skills/ai-council/scripts/council_kernel.py", "snapshot_hash"),
    ("skills/competitive-intelligence/scripts/ci_kernel.py", "snapshot_hash"),
    ("skills/competitive-intelligence/scripts/ci_kernel.py", "state_hash"),
]


def load(rel: str):
    path = ROOT / rel
    spec = importlib.util.spec_from_file_location(f"hash_{path.stem}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def reorder(value, rnd: random.Random):
    if isinstance(value, dict):
        items = list(value.items())
        rnd.shuffle(items)
        return {k: reorder(v, rnd) for k, v in items}
    if isinstance(value, list):
        return [reorder(v, rnd) for v in value]
    return value


@pytest.mark.parametrize("rel,function", HASHERS, ids=lambda v: v.split("/")[-1] if "/" in str(v) else v)
def test_hash_is_stable_across_runs_and_key_order(rel: str, function: str) -> None:
    fn = getattr(load(rel), function)
    expected = fn(PAYLOAD)
    assert fn(PAYLOAD) == expected, "same input hashed differently twice"
    for seed in range(4):
        assert fn(reorder(PAYLOAD, random.Random(seed))) == expected, (
            f"{function} depends on JSON key order (seed {seed})"
        )


def test_package_payload_digest_is_reproducible() -> None:
    """A release that cannot be rebuilt byte-for-byte is not a release."""
    script = (
        "import sys, pathlib, importlib.util as iu;"
        "sys.path.insert(0, 'tooling');"
        "s = iu.spec_from_file_location('p', 'tooling/package_skill.py');"
        "m = iu.module_from_spec(s); s.loader.exec_module(m);"
        "print(m.payload(pathlib.Path('.'), 'ai-humanize')[1]['payload_sha256'])"
    )
    digests = set()
    for seed in ("0", "7", "99999"):
        proc = subprocess.run(
            [sys.executable, "-c", script], cwd=ROOT, capture_output=True, text=True,
            env={"PATH": "/usr/bin:/bin", "PYTHONHASHSEED": seed}, timeout=300,
        )
        assert proc.returncode == 0, proc.stderr[-400:]
        digests.add(proc.stdout.strip())
    assert len(digests) == 1, f"payload digest varies with PYTHONHASHSEED: {digests}"


def test_every_listed_hasher_exists() -> None:
    for rel, function in HASHERS:
        assert callable(getattr(load(rel), function, None)), f"{rel} has no {function}()"
