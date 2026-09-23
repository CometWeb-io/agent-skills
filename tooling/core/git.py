"""Hardened, read-oriented Git subprocess wrapper."""
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GitResult:
    stdout: bytes
    returncode: int = 0


def git_env() -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update(
        GIT_CONFIG_NOSYSTEM="1",
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_OPTIONAL_LOCKS="0",
        GIT_TERMINAL_PROMPT="0",
        GIT_NO_REPLACE_OBJECTS="1",
    )
    return env


def read_git(
    repo: Path,
    *args: str,
    timeout: int = 30,
    check: bool = True,
) -> GitResult:
    """Run a non-interactive Git command with hooks/fsmonitor/config isolated."""
    proc = subprocess.run(
        [
            "git",
            "--no-pager",
            "--no-replace-objects",
            "-c",
            "core.fsmonitor=false",
            "-c",
            f"core.hooksPath={os.devnull}",
            "-c",
            "core.pager=cat",
            "-c",
            "protocol.allow=never",
            "-C",
            str(repo),
            *args,
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=git_env(),
        check=False,
        timeout=timeout,
    )
    if check and proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, proc.args, proc.stdout, proc.stderr)
    return GitResult(stdout=proc.stdout, returncode=proc.returncode)
