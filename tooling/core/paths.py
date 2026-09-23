"""Path canonicalization that rejects path *self* symlinks, not system ancestors.

macOS uses symlink ancestors such as /var -> /private/var. Blanket
`any(p.is_symlink() for p in path.parents)` incorrectly rejects valid paths.
"""
from __future__ import annotations

from pathlib import Path


def refuse_self_symlink(path: Path) -> Path:
    raw = path.expanduser()
    if raw.is_symlink():
        raise ValueError("path itself must not be a symlink")
    return raw


def canonical_input(path: Path) -> Path:
    """Resolve an existing input; reject if the leaf path is a symlink."""
    raw = refuse_self_symlink(path).absolute()
    if raw.is_symlink():
        raise ValueError("input itself must not be a symlink")
    return raw.resolve(strict=True)


def canonical_output(path: Path) -> Path:
    """Resolve output location; allow missing leaf; reject leaf symlink."""
    raw = refuse_self_symlink(path).absolute()
    if raw.exists() and raw.is_symlink():
        raise ValueError("output itself must not be a symlink")
    parent = raw.parent.resolve(strict=True)
    return parent / raw.name
