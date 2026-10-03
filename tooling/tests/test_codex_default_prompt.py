"""Codex `interface.default_prompt` is one sentence that invokes the skill as `$skill-id`.

Codex inserts the default prompt when a user picks a skill, and its
skill-creator reference asks for a short single sentence that names the skill
explicitly as `$skill-name`. The old generator sliced the description at 200
characters, which cut words in half ("asks to humanize t") and never named the
skill, so picking it from the list did not invoke it.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tooling"))

from route_skill import route  # noqa: E402

REGISTRY = json.loads((ROOT / "registry" / "skills.json").read_text(encoding="utf-8"))
POLICY = json.loads((ROOT / "registry" / "routing-policy.json").read_text(encoding="utf-8"))
ACTIVE = [entry for entry in REGISTRY["skills"] if entry.get("lifecycle") == "active"]


def load_generator():
    spec = importlib.util.spec_from_file_location("generate_adapters", ROOT / "tooling" / "generate_adapters.py")
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


GEN = load_generator()


def shipped_prompt(skill_id: str) -> str:
    data = yaml.safe_load((ROOT / "skills" / skill_id / "agents" / "openai.yaml").read_text(encoding="utf-8"))
    return data["interface"]["default_prompt"]


@pytest.mark.parametrize("skill_id", [entry["id"] for entry in ACTIVE])
def test_shipped_prompt_invokes_the_skill_in_one_short_sentence(skill_id: str) -> None:
    prompt = shipped_prompt(skill_id)
    assert re.search(r"(?<![\w$-])\$" + re.escape(skill_id) + r"(?![\w-])", prompt), prompt
    assert len(prompt) <= GEN.DEFAULT_PROMPT_MAX, prompt
    assert prompt.endswith("."), prompt
    assert not re.search(r"[.!?]\s+\S", prompt), f"more than one sentence: {prompt}"


@pytest.mark.parametrize("skill_id", [entry["id"] for entry in ACTIVE])
def test_the_router_reads_the_shipped_prompt_as_an_invocation_of_that_skill(skill_id: str) -> None:
    # Explicit-only skills such as the Council included: `$id` is an invocation.
    result = route(shipped_prompt(skill_id), REGISTRY, POLICY)
    assert result["primary_skill"] == skill_id, result


def test_summary_becomes_a_lower_cased_for_clause() -> None:
    prompt = GEN.default_prompt({"id": "alpha"}, "Claim decomposition and Evidence Packs.")
    assert prompt == "Use $alpha for claim decomposition and Evidence Packs."


def test_an_acronym_keeps_its_capitals() -> None:
    assert GEN.default_prompt({"id": "alpha"}, "SEO audits.") == "Use $alpha for SEO audits."


def test_a_long_source_is_clipped_at_a_word_boundary() -> None:
    words = [f"word{i}" for i in range(60)]
    prompt = GEN.default_prompt({"id": "alpha"}, " ".join(words))
    assert len(prompt) <= GEN.DEFAULT_PROMPT_MAX
    last = prompt.removeprefix("Use $alpha for ").removesuffix(".").split()[-1]
    assert last in words, f"clipped mid-word: {last!r}"


def test_without_a_summary_the_first_description_sentence_follows_a_colon() -> None:
    entry = {"id": "alpha", "description": "Run a careful audit of things. Use when asked. Do not use otherwise."}
    assert GEN.default_prompt(entry) == "Use $alpha: run a careful audit of things."


@pytest.mark.parametrize(
    "curated, problem",
    [
        ("Run the council on my question.", "does not invoke $alpha"),
        ("Use $alpha now. Then do more.", "more than one sentence"),
        ("Use $alpha " + "very " * 40 + "carefully.", "characters"),
    ],
    ids=["no-dollar-invocation", "two-sentences", "too-long"],
)
def test_a_hand_tuned_prompt_that_breaks_the_rule_stops_generation(
    monkeypatch: pytest.MonkeyPatch, curated: str, problem: str
) -> None:
    monkeypatch.setitem(GEN.DEFAULT_PROMPTS, "alpha", curated)
    with pytest.raises(SystemExit, match=re.escape(problem)):
        GEN.default_prompt({"id": "alpha"})


def test_every_hand_tuned_prompt_names_a_registry_skill() -> None:
    assert set(GEN.DEFAULT_PROMPTS) <= {entry["id"] for entry in REGISTRY["skills"]}


def test_string_values_are_quoted_and_keys_are_not() -> None:
    # Codex's openai.yaml reference: quote all string values, keep keys unquoted.
    text = (ROOT / "skills" / "science-roaster" / "agents" / "openai.yaml").read_text(encoding="utf-8")
    assert re.search(r'^  default_prompt: "Use \$science-roaster for ', text, re.M)
    for line in text.splitlines():
        key, sep, value = line.strip().lstrip("- ").partition(": ")
        if sep and value not in {"true", "false"}:
            assert value.startswith('"') and not key.startswith('"'), line
