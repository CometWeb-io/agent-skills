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


def shared_refs() -> tuple[str, ...]:
    spec = importlib.util.spec_from_file_location("sync_orchestrator", GUARD)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module.SHARED_REFS


def run_guard() -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(GUARD), "--check"],
        capture_output=True, text=True, timeout=120,
    )


@pytest.fixture
def restore(tmp_path):
    """Move a file aside and put it back, whatever the assertion does."""
    saved: list[tuple[Path, Path]] = []

    def hide(path: Path):
        backup = tmp_path / path.name
        shutil.copy2(path, backup)
        saved.append((path, backup))
        path.unlink()

    def append(path: Path, text: str):
        backup = tmp_path / f"append-{path.name}"
        shutil.copy2(path, backup)
        saved.append((path, backup))
        path.write_text(path.read_text(encoding="utf-8") + text, encoding="utf-8")

    yield hide, append
    for path, backup in saved:
        shutil.copy2(backup, path)


def test_guard_passes_on_a_healthy_tree() -> None:
    assert run_guard().returncode == 0, run_guard().stderr


def test_kernel_drift_fails(restore) -> None:
    _, append = restore
    append(DST / "scripts" / "orchestrate_kernel.py", "\n# drift\n")
    assert run_guard().returncode == 1


@pytest.mark.parametrize("name", shared_refs())
@pytest.mark.parametrize("side", ["source", "destination"])
def test_missing_shared_reference_fails_on_either_side(restore, name: str, side: str) -> None:
    hide, _ = restore
    base = SRC if side == "source" else DST
    path = base / "references" / name
    if not path.is_file():
        pytest.skip(f"{name} is not present on the {side} side")
    hide(path)
    proc = run_guard()
    assert proc.returncode == 1, f"deleting {name} from the {side} passed the guard"
    assert name in proc.stderr, proc.stderr


@pytest.mark.parametrize("name", shared_refs())
def test_shared_reference_drift_fails(restore, name: str) -> None:
    _, append = restore
    append(DST / "references" / name, "\ndrift\n")
    assert run_guard().returncode == 1
