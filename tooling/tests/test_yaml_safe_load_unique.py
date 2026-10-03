"""Frontmatter and host metadata are read with yaml.safe_load plus a duplicate-key pass.

The tooling used a custom SafeLoader subclass through yaml.load, which needed
`# nosec B506` to get past the scanner. The duplicate check now runs on the
composed node tree, so every YAML read goes through safe_load and no
suppression is left to justify.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from adapter_metadata import merge_openai
from compatibility import parse_frontmatter, safe_load_unique

ROOT = Path(__file__).resolve().parents[2]


def test_plain_mapping_loads() -> None:
    assert safe_load_unique("name: demo\ndescription: text\n") == {"name": "demo", "description": "text"}


@pytest.mark.parametrize("text", [
    "name: a\nname: b\n",
    "outer:\n  key: 1\n  key: 2\n",
    "items:\n  - {k: 1, k: 2}\n",
    "name: a\n'name': b\n",
])
def test_duplicate_keys_are_rejected_at_any_depth(text: str) -> None:
    with pytest.raises(ValueError, match="duplicate YAML key"):
        safe_load_unique(text)


def test_keys_of_different_types_are_not_duplicates() -> None:
    assert safe_load_unique("1: int\n'1': str\n") == {1: "int", "1": "str"}


def test_python_tags_are_refused() -> None:
    with pytest.raises(yaml.YAMLError):
        safe_load_unique("x: !!python/object/apply:os.system ['true']\n")


def test_aliases_are_walked_once() -> None:
    assert safe_load_unique("a: &x {k: 1}\nb: *x\n") == {"a": {"k": 1}, "b": {"k": 1}}


def test_frontmatter_with_two_descriptions_is_rejected(tmp_path: Path) -> None:
    skill = tmp_path / "SKILL.md"
    skill.write_text("---\nname: demo\ndescription: one\ndescription: two\n---\nBody\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate YAML key"):
        parse_frontmatter(skill)


def test_openai_metadata_with_duplicate_key_is_rejected() -> None:
    with pytest.raises(ValueError, match="duplicate YAML key"):
        merge_openai({}, "interface:\n  display_name: A\n  display_name: B\n", {})


def test_no_unsafe_yaml_load_or_b506_suppression_remains() -> None:
    offenders = []
    for path in sorted(ROOT.glob("tooling/**/*.py")) + sorted(ROOT.glob("skills/*/scripts/**/*.py")):
        text = path.read_text(encoding="utf-8")
        if "nosec B506" in text or re.search(r"\byaml\.load\(", text):
            offenders.append(path.relative_to(ROOT).as_posix())
    offenders = [p for p in offenders if p != "tooling/tests/test_yaml_safe_load_unique.py"]
    assert not offenders, offenders
