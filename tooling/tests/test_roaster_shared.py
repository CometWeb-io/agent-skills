"""Shared roaster resources must not drift silently."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).resolve().parents[1] / "sync_roaster_shared.py"


def load_module():
    spec = importlib.util.spec_from_file_location("sync_roaster_shared", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_reference_drift_is_detected_and_repaired(tmp_path: Path) -> None:
    module = load_module()
    root = tmp_path
    canonical = root / "skills" / "repo-roaster"
    targets = [root / "skills" / name for name in ("content-roaster", "science-roaster")]
    for base in (canonical, *targets):
        for name in ("scan_source_risks.py", "validate_evals.py"):
            path = base / "scripts" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("same script", encoding="utf-8")
        for name in (
            "adversarial-protocol.md", "assurance-protocol.md", "eval-protocol.md",
            "handoff-contract.md", "production-ops.md", "review-operations.md", "revision-protocol.md",
            "source-safety.md", "workspace-ops.md",
        ):
            path = base / "references" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("same contract", encoding="utf-8")
    drift = targets[0] / "references" / "source-safety.md"
    drift.write_text("weakened contract", encoding="utf-8")
    module.ROOT = root
    module.CANONICAL = canonical
    module.TARGETS = tuple(targets)
    assert any("source-safety.md" in error for error in module.verify())
    module.sync()
    assert drift.read_text(encoding="utf-8") == "same contract"


def test_sync_replaces_leaf_symlink_without_following_it(tmp_path: Path) -> None:
    module = load_module()
    root = tmp_path
    canonical = root / "skills" / "repo-roaster"
    target = root / "skills" / "content-roaster"
    filename = "references/source-safety.md"
    expected = b"canonical contract"
    source = canonical / filename
    candidate = target / filename
    outside = root / "outside.txt"
    source.parent.mkdir(parents=True)
    candidate.parent.mkdir(parents=True)
    source.write_bytes(expected)
    outside.write_bytes(b"do not modify")
    candidate.symlink_to(outside)
    module.ROOT = root
    module.CANONICAL = canonical
    module.TARGETS = (target,)
    module.SHARED = (filename,)

    assert module.sync() == ["skills/content-roaster/references/source-safety.md"]
    assert outside.read_bytes() == b"do not modify"
    assert not candidate.is_symlink()
    assert candidate.read_bytes() == expected


@pytest.mark.skipif(os.name == "nt", reason="POSIX executable and permission bits")
@pytest.mark.parametrize("mode", [0o755, 0o644])
@pytest.mark.parametrize("content_changed", [True, False])
def test_sync_preserves_canonical_mode_and_repairs_mode_only_drift(tmp_path, mode, content_changed):
    module = load_module()
    filename = "scripts/shared.py"
    canonical = tmp_path / "skills/repo-roaster"
    target = tmp_path / "skills/content-roaster"
    source, candidate = canonical / filename, target / filename
    source.parent.mkdir(parents=True)
    candidate.parent.mkdir(parents=True)
    source.write_bytes(b"canonical")
    source.chmod(mode)
    candidate.write_bytes(b"changed" if content_changed else b"canonical")
    candidate.chmod(0o600)
    module.ROOT, module.CANONICAL, module.TARGETS, module.SHARED = tmp_path, canonical, (target,), (filename,)
    assert any("mode drift" in error for error in module.verify())
    assert module.sync() == ["skills/content-roaster/scripts/shared.py"]
    assert candidate.read_bytes() == b"canonical"
    assert candidate.stat().st_mode & 0o777 == mode
    assert module.verify() == []
    assert module.sync() == []


def test_content_local_protocols_survive_sync_but_science_stays_shared(tmp_path: Path) -> None:
    module = load_module()
    module.ROOT = tmp_path
    module.CANONICAL = tmp_path / "skills/repo-roaster"
    content = tmp_path / "skills/content-roaster"
    science = tmp_path / "skills/science-roaster"
    module.TARGETS = (content, science)
    module.SHARED = tuple(module.CONTENT_LOCAL)
    for filename in module.SHARED:
        for package, text in ((module.CANONICAL, "shared"), (content, "compact"), (science, "drift")):
            path = package / filename
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
    errors = module.verify()
    assert len(errors) == len(module.SHARED)
    assert all("science-roaster" in error for error in errors)
    assert len(module.sync()) == len(module.SHARED)
    assert all((content / name).read_text() == "compact" for name in module.SHARED)
    assert module.verify() == []
    assert module.sync() == []
