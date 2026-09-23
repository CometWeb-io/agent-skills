"""Shared security and I/O primitives for CometWeb agent-skills tooling."""
from __future__ import annotations

from .evidence import DEFAULT_RELEASE_EVIDENCE, EvidenceKind
from .git import GitResult, git_env, read_git
from .paths import canonical_input, canonical_output, refuse_self_symlink
from .subprocess_env import SAFE_BASE_ENV, build_runner_env

__all__ = [
    "DEFAULT_RELEASE_EVIDENCE",
    "EvidenceKind",
    "GitResult",
    "SAFE_BASE_ENV",
    "build_runner_env",
    "canonical_input",
    "canonical_output",
    "git_env",
    "read_git",
    "refuse_self_symlink",
]
