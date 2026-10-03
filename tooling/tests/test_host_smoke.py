"""tooling/host_smoke.py: parsers, the static Cursor check, and the real CLIs when installed.

The CLI-backed tests skip cleanly when a host is absent, the way CI sees them.
No test here reaches a model: every command is a manifest, install or listing
command run under a temporary HOME and config directory.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tooling"))
import host_smoke  # noqa: E402

EXPECTED = host_smoke.expected_skills()
VERSION = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]

DETAILS = """\
demo 0.0.1
Component inventory
  Skills (3)  alpha, beta-two, gamma
  Agents (0)

Per-component (rounded)
  component  always-on  on-invoke
  alpha           ~230      ~2.1k
  beta-two        < 20       < 20
  gamma           ~1.2k      ~590
"""


def test_claude_details_parser_reads_names_and_estimates() -> None:
    names, estimates = host_smoke.parse_claude_details(DETAILS)
    assert names == ["alpha", "beta-two", "gamma"]
    assert estimates == {"alpha": "~230", "beta-two": "< 20", "gamma": "~1.2k"}
    assert host_smoke.estimate_tokens("~1.2k") == 1200
    assert host_smoke.estimate_tokens("< 20") is None


@pytest.mark.parametrize(
    ("estimate", "description", "seen"),
    [
        ("~230", "d" * 893, True),     # ai-council-sized description, read in full
        ("< 20", "d" * 893, False),    # Claude saw no description at all
        ("~60", "d" * 893, False),     # only a fragment reached the listing
        ("< 20", "short", True),       # a short description legitimately rounds to < 20
    ],
)
def test_description_seen_compares_the_estimate_with_the_text(estimate: str, description: str, seen: bool) -> None:
    assert host_smoke.description_seen(estimate, "ai-council", description) is seen


def codex_prompt(lines: list[str]) -> list[dict]:
    text = "## Skills\n### Available skills\n" + "\n".join(lines) + "\n</skills_instructions>"
    return [{"type": "message", "content": [{"type": "input_text", "text": text}]}]


def test_codex_listing_and_truncation_report() -> None:
    full = {
        "alpha": "Does alpha work. Use for alpha. Do not use for beta.",
        "beta": "Does beta work.",
        "gamma": "Does gamma.  Do not use for alpha.",
    }
    prompt = codex_prompt([
        "- other-plugin:alpha: not ours (file: r0/alpha/SKILL.md)",
        "- cometweb-agent-skills:alpha: Does alpha work. Use for alpha. (file: r1/alpha/SKILL.md)",
        "- cometweb-agent-skills:beta: Does beta work. (file: r1/beta/SKILL.md)",
        "- cometweb-agent-skills:gamma: Something else entirely (file: r1/gamma/SKILL.md)",
    ])
    shown = host_smoke.codex_skill_listing(prompt)
    assert shown == {"alpha": "Does alpha work. Use for alpha.", "beta": "Does beta work.",
                     "gamma": "Something else entirely"}
    cut = host_smoke.codex_truncation(shown, full)
    assert sorted(cut) == ["alpha", "gamma"]
    assert cut["alpha"] == {"shown": 31, "full": 52, "prefix": True, "do_not_clause": "lost"}
    assert cut["gamma"]["prefix"] is False


@pytest.mark.parametrize(
    ("shown", "state"),
    [
        ("Does alpha. Do not use for beta or gamma. Do not use for delta.", "kept"),   # both sentences shown
        ("Does alpha. Do not use for beta or gamma. Do not use", "partial"),          # second sentence cut
        ("Does alpha. Do not use for beta", "partial"),                               # cut mid-sentence
        ("Does alpha.", "lost"),
    ],
)
def test_do_not_clause_state_separates_kept_partial_and_lost(shown: str, state: str) -> None:
    full = {"alpha": "Does alpha. Do not use for beta or gamma. Do not use for delta. Use when alpha is named."}
    assert host_smoke.codex_truncation({"alpha": shown}, full)["alpha"]["do_not_clause"] == state


def test_do_not_clause_span_covers_consecutive_sentences_only() -> None:
    text = "Does x (e.g. y). Do not use for a, b. Do not trigger for c. Use when d. Do not mix."
    start, end = host_smoke.do_not_clause_span(text)
    assert text[start:end] == "Do not use for a, b. Do not trigger for c."
    assert host_smoke.do_not_clause_span("No guardrail here.") is None


def test_codex_clause_summary_counts_every_skill() -> None:
    full = {"a": "A. Do not use for x.", "b": "B. Do not use for y. Use when z.", "c": "C only."}
    shown = {"a": "A. Do not use for x.", "b": "B. Do not use", "c": "C only."}
    summary = host_smoke.codex_clause_summary(shown, full)
    assert summary == {"kept": ["a"], "partial": ["b"], "lost": [], "none": ["c"]}


def test_stage_payload_copies_the_plugin_and_nothing_else(tmp_path: Path) -> None:
    stage = host_smoke.stage_payload(tmp_path / "stage")
    assert (stage / ".claude-plugin" / "plugin.json").is_file()
    assert sorted(p.parent.name for p in (stage / "skills").glob("*/SKILL.md")) == sorted(EXPECTED)
    assert not (stage / "tooling").exists()
    assert not list(stage.rglob("__pycache__"))


def test_cursor_static_check_passes_on_the_repository(tmp_path: Path) -> None:
    result = host_smoke.smoke_cursor(ROOT, EXPECTED)
    assert result.status == "PASS", [c for c in result.checks if not c["ok"]]
    assert "plugin ships its routing rule where Cursor discovers rules" in [c["check"] for c in result.checks]


def test_cursor_key_sets_come_from_hosts_json() -> None:
    hosts = json.loads((ROOT / "registry" / "hosts.json").read_text(encoding="utf-8"))["hosts"]["cursor"]
    fmt = host_smoke.cursor_format(ROOT)
    assert fmt["manifest_keys"] == hosts["plugin_format"]["manifest_keys"]
    assert fmt["plugin_rule"] == hosts["plugin_rule"]


def test_stage_payload_carries_the_plugin_rule(tmp_path: Path) -> None:
    stage = host_smoke.stage_payload(tmp_path / "stage")
    assert (stage / "rules" / "cometweb-agent-skills.mdc").is_file()


def broken_cursor_copy(tmp_path: Path) -> Path:
    copy = host_smoke.stage_payload(tmp_path / "copy")
    for rel in host_smoke.CURSOR_RULES:
        (copy / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, copy / rel)
    return copy


@pytest.mark.parametrize(
    ("mutate", "failed_check"),
    [
        (lambda c: _edit_json(c / ".cursor-plugin" / "plugin.json", name="Bad Name"),
         "plugin.json name is a valid Cursor plugin name"),
        (lambda c: _edit_json(c / ".cursor-plugin" / "plugin.json", logo="../outside.png"),
         "manifest paths are relative and stay inside the plugin"),
        (lambda c: _edit_json(c / ".cursor-plugin" / "marketplace.json", owner={}),
         "marketplace has name, owner.name and plugins"),
        (lambda c: (c / "skills" / "empty-dir").mkdir(), "no skills/ subdirectory lacks a SKILL.md"),
        (lambda c: (c / "extras" / "cursor-routing.mdc").write_text("---\ndescription: x\n---\n", encoding="utf-8"),
         "extras/cursor-routing.mdc has Cursor rule frontmatter"),
        (lambda c: _edit_json(c / ".cursor-plugin" / "plugin.json", displayName="Shown Name"),
         "plugin.json uses only keys Cursor documents"),
        (lambda c: _edit_json(c / ".cursor-plugin" / "plugin.json", author={"name": "A", "url": "https://example.com"}),
         "plugin.json uses only keys Cursor documents"),
        (lambda c: _edit_json(c / ".cursor-plugin" / "marketplace.json", interface={}),
         "marketplace.json uses only keys Cursor documents"),
        (lambda c: shutil.rmtree(c / "rules"),
         "plugin ships its routing rule where Cursor discovers rules"),
        (lambda c: _edit_json(c / ".cursor-plugin" / "plugin.json", rules="extras/"),
         "plugin ships its routing rule where Cursor discovers rules"),
    ],
)
def test_cursor_static_check_catches_each_defect(tmp_path: Path, mutate, failed_check: str) -> None:
    copy = broken_cursor_copy(tmp_path)
    mutate(copy)
    result = host_smoke.smoke_cursor(copy, EXPECTED)
    assert result.status == "FAIL"
    assert [c["check"] for c in result.checks if not c["ok"]] == [failed_check]


def _edit_json(path: Path, **changes: object) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    data.update(changes)
    path.write_text(json.dumps(data), encoding="utf-8")


def test_required_host_that_is_missing_fails(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    missing = str(tmp_path / "no-such-codex")
    assert host_smoke.main(["--host", "codex", "--codex-bin", missing]) == 0
    assert host_smoke.main(["--host", "codex", "--codex-bin", missing, "--require", "codex"]) == 1
    assert "FAIL  openai-codex" in capsys.readouterr().out


@pytest.mark.skipif(shutil.which("claude") is None, reason="Claude Code CLI not installed")
def test_claude_validates_loads_and_installs_every_skill(tmp_path: Path) -> None:
    result = host_smoke.smoke_claude(shutil.which("claude"), tmp_path, EXPECTED, VERSION)
    assert result.status == "PASS", [c for c in result.checks if not c["ok"]]


CODEX = os.environ.get("CODEX_BIN") or shutil.which("codex")


@pytest.mark.skipif(CODEX is None, reason="Codex CLI not installed (set CODEX_BIN to opt in)")
def test_codex_installs_and_lists_every_skill(tmp_path: Path) -> None:
    result = host_smoke.smoke_codex(CODEX, tmp_path, EXPECTED, VERSION)
    assert result.status == "PASS", [c for c in result.checks if not c["ok"]]
