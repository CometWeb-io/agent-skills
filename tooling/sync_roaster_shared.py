#!/usr/bin/env python3
"""Keep shared roaster scripts and references byte-identical across packages."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHARED = (
    "scripts/scan_source_risks.py",
    "scripts/validate_evals.py",
    "references/adversarial-protocol.md",
    "references/assurance-protocol.md",
    "references/eval-protocol.md",
    "references/handoff-contract.md",
    "references/production-ops.md",
    "references/revision-protocol.md",
    "references/source-safety.md",
    "references/workspace-ops.md",
)
CANONICAL = ROOT / "skills" / "repo-roaster"
TARGETS = (
    ROOT / "skills" / "content-roaster",
    ROOT / "skills" / "science-roaster",
)


def verify() -> list[str]:
    errors: list[str] = []
    for filename in SHARED:
        canonical = CANONICAL / filename
        if not canonical.is_file():
            errors.append(f"missing canonical: {canonical.relative_to(ROOT)}")
            continue
        expected = canonical.read_bytes()
        for target in TARGETS:
            candidate = target / filename
            if not candidate.is_file():
                errors.append(f"missing: {candidate.relative_to(ROOT)}")
                continue
            if candidate.read_bytes() != expected:
                errors.append(f"shared resource drift: {candidate.relative_to(ROOT)}")
    return errors


def sync() -> list[str]:
    written: list[str] = []
    for filename in SHARED:
        expected = (CANONICAL / filename).read_bytes()
        for target in TARGETS:
            candidate = target / filename
            if not candidate.is_file() or candidate.read_bytes() != expected:
                candidate.write_bytes(expected)
                written.append(candidate.relative_to(ROOT).as_posix())
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync", action="store_true")
    args = parser.parse_args(argv)
    if args.sync == args.check:
        parser.error("choose exactly one of --check or --sync")
    if args.sync:
        written = sync()
        print(f"OK: synced {len(written)} file(s)" if written else "OK: already in sync")
        return 0
    errors = verify()
    for error in errors:
        print(f"FAIL: {error}", file=sys.stderr)
    if errors:
        return 1
    print(f"OK: {len(SHARED)} shared roaster resources match across {1 + len(TARGETS)} packages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
