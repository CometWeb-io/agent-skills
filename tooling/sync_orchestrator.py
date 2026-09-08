#!/usr/bin/env python3
"""Keep skill-orchestrator-multiagent planner identical to skill-orchestrator."""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "skills" / "skill-orchestrator" / "scripts" / "orchestrate_kernel.py"
DST = ROOT / "skills" / "skill-orchestrator-multiagent" / "scripts" / "orchestrate_kernel.py"
REF_SRC = ROOT / "skills" / "skill-orchestrator" / "references"
REF_DST = ROOT / "skills" / "skill-orchestrator-multiagent" / "references"
SHARED_REFS = ("workflow-archetypes.md", "multiagent-execution.md", "subagent-prompt-template.md")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if not SRC.is_file():
        raise SystemExit(f"missing canonical kernel: {SRC}")

    errors: list[str] = []
    if not DST.is_file() or SRC.read_bytes() != DST.read_bytes():
        errors.append("orchestrate_kernel.py drift")

    for name in SHARED_REFS:
        left = REF_SRC / name
        right = REF_DST / name
        if left.is_file() and (not right.is_file() or left.read_bytes() != right.read_bytes()):
            errors.append(f"references/{name} drift")

    if args.check:
        if errors:
            print("FAIL: " + "; ".join(errors), file=sys.stderr)
            raise SystemExit(1)
        print("OK: orchestrator kernels in sync")
        return

    DST.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SRC, DST)
    REF_DST.mkdir(parents=True, exist_ok=True)
    for name in SHARED_REFS:
        left = REF_SRC / name
        if left.is_file():
            shutil.copy2(left, REF_DST / name)
    print("OK: synced orchestrator kernel + shared references into multiagent package")


if __name__ == "__main__":
    main()
