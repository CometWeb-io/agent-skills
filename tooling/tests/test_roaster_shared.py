"""Shared roaster resources must not drift silently."""

from __future__ import annotations

import importlib.util
from pathlib import Path


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
    drift = targets[0] / "references" / "adversarial-protocol.md"
    drift.write_text("weakened contract", encoding="utf-8")
    module.ROOT = root
    module.CANONICAL = canonical
    module.TARGETS = tuple(targets)
    assert any("adversarial-protocol.md" in error for error in module.verify())
    module.sync()
    assert drift.read_text(encoding="utf-8") == "same contract"


def test_sync_replaces_leaf_symlink_without_following_it(tmp_path: Path) -> None:
    module = load_module()
    root = tmp_path
    canonical = root / "skills" / "repo-roaster"
    target = root / "skills" / "content-roaster"
    filename = "references/adversarial-protocol.md"
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

    assert module.sync() == ["skills/content-roaster/references/adversarial-protocol.md"]
    assert outside.read_bytes() == b"do not modify"
    assert not candidate.is_symlink()
    assert candidate.read_bytes() == expected
