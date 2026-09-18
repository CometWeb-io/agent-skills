"""Every skill script must import cleanly, and its no-argument defaults must run.

A missing name in a branch that only executes when an optional argument is
absent — a default "as of today", say — passes both a syntax check and a test
suite that always supplies the argument. It then fails in front of a user. This
module walks every skill script instead of waiting for someone to notice.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def skill_scripts() -> list[Path]:
    return sorted(
        path
        for path in ROOT.glob("skills/*/scripts/*.py")
        if not path.name.startswith("_")
    )


def load(path: Path):
    """Load a skill script the way its own callers do.

    The script's directory goes on sys.path, because several kernels import a
    sibling by bare name, and the module is registered in sys.modules before
    execution, because dataclass and typing machinery resolves annotations
    through it.
    """
    directory = str(path.parent)
    name = f"skillscript_{path.parents[1].name.replace('-', '_')}_{path.stem}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader, f"cannot load {path}"
    module = importlib.util.module_from_spec(spec)
    added = directory not in sys.path
    if added:
        sys.path.insert(0, directory)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(name, None)
        if added:
            sys.path.remove(directory)
    return module


@pytest.mark.parametrize("script", skill_scripts(), ids=lambda p: f"{p.parents[1].name}/{p.name}")
def test_skill_script_imports(script: Path) -> None:
    load(script)


def test_every_skill_with_scripts_is_covered() -> None:
    # A skill that loses its scripts directory would otherwise silently drop out
    # of the parametrization above.
    with_scripts = {p.parents[1].name for p in skill_scripts()}
    on_disk = {
        d.name
        for d in (ROOT / "skills").iterdir()
        if d.is_dir() and (d / "scripts").is_dir() and any((d / "scripts").glob("*.py"))
    }
    assert with_scripts == on_disk


DATE_DEFAULTS = [
    ("seo-geo-aeo-maxxing", "score_maxx.py", "get_as_of", (None,)),
    ("ebook-publisher", "ebook_check.py", "current_date", ()),
]


@pytest.mark.parametrize("skill,filename,function,args", DATE_DEFAULTS, ids=lambda v: str(v))
def test_date_defaults_resolve_without_arguments(skill, filename, function, args) -> None:
    """The default-date branches are the ones no other test exercises."""
    module = load(ROOT / "skills" / skill / "scripts" / filename)
    import datetime as dt

    value = getattr(module, function)(*args)
    assert isinstance(value, dt.date)


def test_ebook_current_date_falls_back_to_utc(monkeypatch) -> None:
    """Force the fallback branch.

    current_date() prefers a named timezone and only reaches its UTC fallback
    when zoneinfo is unavailable. On a machine where zoneinfo works, that branch
    never executes, so a missing name inside it stays invisible — which is
    exactly how one was introduced here.
    """
    module = load(ROOT / "skills" / "ebook-publisher" / "scripts" / "ebook_check.py")
    import builtins
    import datetime as dt

    real_import = builtins.__import__

    def refuse_zoneinfo(name, *args, **kwargs):
        if name == "zoneinfo":
            raise ImportError("zoneinfo unavailable in this test")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", refuse_zoneinfo)
    assert isinstance(module.current_date(), dt.date)
