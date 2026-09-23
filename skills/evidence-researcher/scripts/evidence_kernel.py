#!/usr/bin/env python3
"""Deterministic kernel for Evidence Researcher v2.

The kernel validates and audits evidence packs. It never discovers facts or decides
whether a source is substantively true; those remain model/tool responsibilities.

Implementation lives in the ``evidence`` package; this module re-exports the public API
so existing import paths (including importlib file loads) keep working.
"""
from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from evidence import *  # noqa: F401,F403
from evidence import __all__ as __all__  # noqa: E402
from evidence.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
