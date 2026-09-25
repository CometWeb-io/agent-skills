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
            "handoff-contract.md", "production-ops.md", "revision-protocol.md",
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
