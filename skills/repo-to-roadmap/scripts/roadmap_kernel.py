#!/usr/bin/env python3
"""Deterministic validation helpers for repo-to-roadmap v2.

The kernel never discovers roadmap work and never replaces project judgment. It
validates evidence admissibility, applies bounded priority/gate rules, checks
coverage and dependency graphs, creates immutable snapshot hashes, computes
baseline/delta invalidation, and validates the machine-readable roadmap payload.

Implementation lives in the ``roadmap`` package; this module re-exports the public API
so existing import paths (including importlib file loads) keep working.
"""
from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from roadmap import *  # noqa: F401,F403
from roadmap import __all__ as __all__  # noqa: E402
from roadmap.cli import main  # noqa: E402
from roadmap.util import parse_json_arg as _parse_json_arg  # noqa: E402


def parse_json_arg(value: str):
    """Facade wrapper so monkeypatch.setattr(kernel, 'MAX_JSON_BYTES', ...) still applies."""
    return _parse_json_arg(value, max_bytes=MAX_JSON_BYTES)


if __name__ == "__main__":
    sys.exit(main())
