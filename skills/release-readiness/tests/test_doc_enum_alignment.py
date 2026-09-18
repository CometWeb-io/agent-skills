"""Values SKILL.md tells an agent to write must be values the engine accepts.

SKILL.md listed the audience as "library consumers" and the commercial model as
"not applicable". Both are prose spellings of engine enum members
(`library_consumers`, `not_applicable`), so an agent copying them verbatim —
which is what a skill file is for — produced a manifest the engine rejected
before any assessment could start. references/manifest-schema.md had it right;
the file read first did not.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _engine():
    path = ROOT / "scripts" / "readiness_engine.py"
    spec = importlib.util.spec_from_file_location("readiness_engine", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


DOCS = [ROOT / "SKILL.md", ROOT / "references" / "manifest-schema.md"]


# Only keys whose allowed values SKILL.md spells out inline. PROFILES and MODES
# are excluded on purpose: their members read as ordinary English ("a mobile app
# with backend billing..."), so scanning prose for them finds sentences, not
# declarations.
DECLARED = [("AUDIENCES", "audience"), ("COMMERCIAL", "commercial_model")]


def _declaration_lines(text: str, doc_key: str) -> list[str]:
    """Bullet lines that define the key's allowed values, not prose about it."""
    return [
        line for line in text.splitlines()
        if line.lstrip().startswith("-") and doc_key in line and ("|" in line or "/" in line)
    ]


@pytest.mark.parametrize("enum_name,doc_key", DECLARED, ids=lambda v: v)
def test_declared_values_are_engine_values(enum_name: str, doc_key: str) -> None:
    allowed = set(getattr(_engine(), enum_name))
    # Members are lowercase with underscores; the bug was a space instead.
    near_miss = {m.replace("_", " ") for m in allowed if "_" in m}
    seen_a_declaration = False
    for doc in DOCS:
        for line in _declaration_lines(doc.read_text(encoding="utf-8"), doc_key):
            seen_a_declaration = True
            for bad in near_miss:
                assert bad not in line.lower(), (
                    f"{doc.name} declares {bad!r} where the engine accepts "
                    f"{bad.replace(' ', '_')!r}: {line.strip()}"
                )
    assert seen_a_declaration, f"no document declares allowed values for {doc_key}"


def test_skill_md_lists_every_audience_and_commercial_value() -> None:
    engine = _engine()
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    for enum_name in ("AUDIENCES", "COMMERCIAL"):
        for member in getattr(engine, enum_name):
            assert member in text, f"SKILL.md never mentions {enum_name} member {member!r}"
