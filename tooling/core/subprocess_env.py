"""Minimal environment construction for trusted child processes."""
from __future__ import annotations

import os

SAFE_BASE_ENV = frozenset({
    "PATH",
    "SYSTEMROOT",
    "WINDIR",
    "COMSPEC",
    "PATHEXT",
    "TMPDIR",
    "TMP",
    "TEMP",
    "HOME",
    "USERPROFILE",
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "TZ",
})


def build_runner_env(allowed_secret_names: set[str] | frozenset[str] | None = None) -> dict[str, str]:
    """Inherit only a safe base env plus explicitly allowed secret names."""
    allowed = set(allowed_secret_names or ())
    env = {key: value for key, value in os.environ.items() if key in SAFE_BASE_ENV}
    for key in allowed:
        value = os.environ.get(key)
        if value is not None:
            env[key] = value
    env["PYTHONNOUSERSITE"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env
