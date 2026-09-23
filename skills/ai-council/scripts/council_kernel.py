"""Facade for the AI Council kernel.

Public import path and CLI entrypoint stay at ``scripts/council_kernel.py``.
Implementation lives in the ``council`` package beside this file.
"""
from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from council import *  # noqa: F403
from council.cli import main

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError, RecursionError):
        import json

        print(
            json.dumps(
                {"status": "INVALID", "error": "invalid decision input", "execution_authorized": False}
            ),
            file=sys.stderr,
        )
        raise SystemExit(2) from None
