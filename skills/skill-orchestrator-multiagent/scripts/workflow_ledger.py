#!/usr/bin/env python3
"""Thin alias to the canonical skill-orchestrator workflow ledger."""
from __future__ import annotations

import runpy
from pathlib import Path


def main() -> None:
    canonical = Path(__file__).resolve().parents[2] / "skill-orchestrator" / "scripts" / "workflow_ledger.py"
    if not canonical.is_file():
        raise SystemExit("canonical skill-orchestrator workflow_ledger.py is not installed")
    runpy.run_path(str(canonical), run_name="__main__")


if __name__ == "__main__":
    main()
