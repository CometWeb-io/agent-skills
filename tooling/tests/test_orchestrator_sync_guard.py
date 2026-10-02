"""The drift guard has to fail on every shape of drift, including deletion.

skill-orchestrator-multiagent is described as an alias that shares a kernel and
three reference files with skill-orchestrator. sync_orchestrator.py exists to
stop them diverging — but it compared a shared reference only `if left.is_file()`,
so removing that file from the source skill made the comparison disappear
instead of failing. The alias could then drift in exactly the way the tool is
meant to prevent.
"""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
GUARD = ROOT / "tooling" / "sync_orchestrator.py"
SRC = ROOT / "skills" / "skill-orchestrator"
DST = ROOT / "skills" / "skill-orchestrator-multiagent"
SRC_REL = SRC.relative_to(ROOT)
DST_REL = DST.relative_to(ROOT)


def shared_refs() -> tuple[str, ...]:
    spec = importlib.util.spec_from_file_location("sync_orchestrator", GUARD)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module.SHARED_REFS


def run_guard(root: Path = ROOT) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(root / "tooling" / "sync_orchestrator.py"), "--check"],
        capture_output=True, text=True, timeout=120,
    )


@pytest.fixture
def sandbox(tmp_path) -> Path:
    """A private copy of everything the guard reads.

    Mutating the real checkout would race with any test that reads the same
    files while the suite runs in parallel.
    """
    root = tmp_path / "repo"
    (root / "tooling").mkdir(parents=True)
    shutil.copy2(GUARD, root / "tooling" / GUARD.name)
    ignore = shutil.ignore_patterns("__pycache__")
    for rel in (SRC.relative_to(ROOT), DST.relative_to(ROOT), Path("protocol")):
        shutil.copytree(ROOT / rel, root / rel, ignore=ignore)
    return root


@pytest.fixture
def restore(sandbox):
    """Delete or append to a file inside the sandbox; return the sandbox root."""

    def hide(rel: Path):
        (sandbox / rel).unlink()

    def append(rel: Path, text: str):
        path = sandbox / rel
        path.write_text(path.read_text(encoding="utf-8") + text, encoding="utf-8")

    return hide, append, sandbox


def test_guard_passes_on_a_healthy_tree() -> None:
    assert run_guard().returncode == 0, run_guard().stderr


def test_sandbox_copy_passes_before_mutation(sandbox) -> None:
    # Otherwise every drift test below would pass on an incomplete copy.
    proc = run_guard(sandbox)
    assert proc.returncode == 0, proc.stderr


def test_kernel_drift_fails(restore) -> None:
    _, append, root = restore
    append(DST_REL / "scripts" / "orchestrate_kernel.py", "\n# drift\n")
    assert run_guard(root).returncode == 1


@pytest.mark.parametrize("name", shared_refs())
@pytest.mark.parametrize("side", ["source", "destination"])
def test_missing_shared_reference_fails_on_either_side(restore, name: str, side: str) -> None:
    hide, _, root = restore
    rel = (SRC_REL if side == "source" else DST_REL) / "references" / name
    if not (root / rel).is_file():
        pytest.skip(f"{name} is not present on the {side} side")
    hide(rel)
    proc = run_guard(root)
    assert proc.returncode == 1, f"deleting {name} from the {side} passed the guard"
    assert name in proc.stderr, proc.stderr


@pytest.mark.parametrize("name", shared_refs())
def test_shared_reference_drift_fails(restore, name: str) -> None:
    _, append, root = restore
    append(DST_REL / "references" / name, "\ndrift\n")
    assert run_guard(root).returncode == 1


def protocol_copies() -> tuple[str, ...]:
    spec = importlib.util.spec_from_file_location("sync_orchestrator", GUARD)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return tuple(module.PROTOCOL_COPIES)


@pytest.mark.parametrize("name", protocol_copies())
def test_bundled_protocol_schema_drift_fails(restore, name: str) -> None:
    # The multiagent gate validates against these copies, so a stale copy would
    # accept or reject envelopes differently from the canonical protocol schema.
    _, append, root = restore
    append(DST_REL / "references" / name, "\n")
    proc = run_guard(root)
    assert proc.returncode == 1
    assert name in proc.stderr, proc.stderr


@pytest.mark.parametrize("name", protocol_copies())
def test_missing_bundled_protocol_schema_fails(restore, name: str) -> None:
    hide, _, root = restore
    hide(DST_REL / "references" / name)
    proc = run_guard(root)
    assert proc.returncode == 1
    assert name in proc.stderr, proc.stderr
