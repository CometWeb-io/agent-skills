"""The README skill catalog is generated, and generation refuses drift.

The catalog used to be hand-written, so a version bump or a new skill made it
stale without anyone noticing. Now generate_adapters.py renders it between two
markers from registry/skills.json (skill set, versions, status) and
registry/readme-catalog.json (grouping and one-line summaries), and
`generate_adapters.py --check` fails when README.md differs from that output.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load_generator():
    spec = importlib.util.spec_from_file_location("generate_adapters", ROOT / "tooling" / "generate_adapters.py")
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def registry() -> list[dict]:
    return json.loads((ROOT / "registry" / "skills.json").read_text(encoding="utf-8"))["skills"]


def catalog() -> dict:
    return json.loads((ROOT / "registry" / "readme-catalog.json").read_text(encoding="utf-8"))


def entry(skill_id: str, version: str = "1.0.0", **extra) -> dict:
    return {"id": skill_id, "version": version, **extra}


def one_group(*rows: tuple[str, str]) -> dict:
    return {"groups": [{"title": "Group", "skills": [{"id": i, "summary": s} for i, s in rows]}]}


def test_readme_block_is_current() -> None:
    gen = load_generator()
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert gen.render_readme(readme, registry(), catalog()) == readme, (
        "README catalog is stale: run `uv run python tooling/generate_adapters.py`"
    )


def test_every_registry_version_appears_in_the_readme() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for skill in registry():
        assert f"| [`{skill['id']}`](skills/{skill['id']}/) |" in readme
        row = next(line for line in readme.splitlines() if line.startswith(f"| [`{skill['id']}`]"))
        assert row.endswith(f"| {skill['version']} |"), row


def test_version_comes_from_the_registry_not_the_catalog() -> None:
    gen = load_generator()
    text = gen.build_readme_catalog([entry("alpha", "2.3.4")], one_group(("alpha", "Does alpha things.")))
    assert "| [`alpha`](skills/alpha/) | Does alpha things. | 2.3.4 |" in text
    assert "**1 skills.**" in text


@pytest.mark.parametrize(
    "skills, rows, word",
    [
        ([entry("alpha"), entry("beta")], [("alpha", "A.")], "missing=['beta']"),
        ([entry("alpha")], [("alpha", "A."), ("ghost", "G.")], "unknown=['ghost']"),
        ([entry("alpha")], [("alpha", "A."), ("alpha", "Again.")], "duplicated=['alpha']"),
    ],
    ids=["registry-skill-without-summary", "summary-for-unknown-skill", "skill-listed-twice"],
)
def test_catalog_and_registry_must_name_the_same_skills(skills, rows, word) -> None:
    gen = load_generator()
    with pytest.raises(SystemExit) as raised:
        gen.build_readme_catalog(skills, one_group(*rows))
    assert word in str(raised.value)


def test_status_notes_are_derived_from_the_registry() -> None:
    gen = load_generator()
    text = gen.build_readme_catalog(
        [entry("alpha", explicit_only=True), entry("beta", release_status="FROZEN"), entry("gamma")],
        one_group(("alpha", "A."), ("beta", "B."), ("gamma", "C.")),
    )
    assert "| A. *(runs only when named)* |" in text
    assert "| B. *(frozen)* |" in text
    assert "| C. |" in text


def test_only_the_marked_block_is_rewritten() -> None:
    gen = load_generator()
    current = f"intro\n\n{gen.README_BEGIN}\nstale\n{gen.README_END}\n\noutro\n"
    rendered = gen.render_readme(current, [entry("alpha")], one_group(("alpha", "A.")))
    assert rendered.startswith(f"intro\n\n{gen.README_BEGIN}\n")
    assert rendered.endswith(f"{gen.README_END}\n\noutro\n")
    assert "stale" not in rendered


def test_a_readme_without_markers_is_an_error_not_a_silent_skip() -> None:
    gen = load_generator()
    with pytest.raises(SystemExit, match="no catalog block"):
        gen.render_readme("no markers here\n", [entry("alpha")], one_group(("alpha", "A.")))


def test_check_mode_reports_a_stale_readme(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    gen = load_generator()
    readme = tmp_path / "README.md"
    readme.write_text(f"{gen.README_BEGIN}\nstale\n{gen.README_END}\n", encoding="utf-8")
    catalog_path = tmp_path / "readme-catalog.json"
    catalog_path.write_text(json.dumps(catalog()), encoding="utf-8")
    monkeypatch.setattr(gen, "readme_file", lambda: readme)
    monkeypatch.setattr(gen, "readme_catalog_file", lambda: catalog_path)
    assert gen.expected_artifacts(registry())[readme] != readme.read_text(encoding="utf-8")
