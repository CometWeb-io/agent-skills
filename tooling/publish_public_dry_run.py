#!/usr/bin/env python3
"""Report that public distribution is disabled during private integration.

This command intentionally performs no filesystem or network writes. Public
release tooling must be reviewed separately before it is restored.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def stage(root: Path, selected: list[str]) -> dict:
    """Return an explicit disabled state; never export even when IDs are supplied."""
    return {
        "status": "disabled",
        "reason": "Public distribution is disabled for the private integration.",
        "skills": [],
        "published": False,
        "filesystem_modified": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--skill", action="append", default=[])
    args = parser.parse_args(argv)
    print(json.dumps(stage(args.root, args.skill), indent=2))
    # Default invocation can report disabled in a local validation pipeline.
    # An explicit export request is not reported as successfully performed.
    return 1 if args.skill else 0


if __name__ == "__main__":
    raise SystemExit(main())
