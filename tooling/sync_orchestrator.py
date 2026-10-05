#!/usr/bin/env python3
"""Keep skill-orchestrator-multiagent planner identical to skill-orchestrator.

Also keeps the CW-AIP schemas bundled with the multiagent envelope validator
byte-identical to their canonical copies under protocol/.
"""
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
SHARED_REFS = (
    "workflow-archetypes.md",
    "multiagent-execution.md",
    "subagent-prompt-template.md",
    "run-ledger-contract.md",
)
# Bundled reference name -> canonical protocol schema.
PROTOCOL_COPIES = {
    "envelope.core.schema.json": ROOT / "protocol" / "cw-aip-v1" / "schemas" / "envelope.core.schema.json",
    "evidence-envelope.schema.json": ROOT / "protocol" / "cw-aip-v1" / "schemas" / "evidence-envelope.schema.json",
    "decision-handoff.schema.json": ROOT / "protocol" / "cw-aip-v1" / "schemas" / "decision-handoff.schema.json",
    "cw-aip-v2.core.schema.json": ROOT / "protocol" / "cw-aip-v2" / "core.schema.json",
}


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
        # SHARED_REFS is a declared contract, so a file missing on either side is
        # a defect. Skipping when the source copy is absent let a deletion pass
        # silently and stopped the two skills being compared at all.
        if not left.is_file():
            errors.append(f"references/{name} missing from skill-orchestrator")
            continue
        if not right.is_file():
            errors.append(f"references/{name} missing from skill-orchestrator-multiagent")
            continue
        if left.read_bytes() != right.read_bytes():
            errors.append(f"references/{name} drift")

    for name, canonical in PROTOCOL_COPIES.items():
        bundled = REF_DST / name
        if not canonical.is_file():
            errors.append(f"canonical protocol schema missing: {canonical.relative_to(ROOT)}")
        elif not bundled.is_file():
            errors.append(f"references/{name} missing from skill-orchestrator-multiagent")
        elif canonical.read_bytes() != bundled.read_bytes():
            errors.append(f"references/{name} drift from {canonical.relative_to(ROOT)}")

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
    for name, canonical in PROTOCOL_COPIES.items():
        if canonical.is_file():
            shutil.copy2(canonical, REF_DST / name)
    print("OK: synced orchestrator kernel, shared references and protocol schemas into multiagent package")


if __name__ == "__main__":
    main()
