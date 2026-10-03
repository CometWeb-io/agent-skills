#!/usr/bin/env python3
"""Prove the plugin loads in real host CLIs without spending a single model token.

    uv run python tooling/host_smoke.py                  # every host whose CLI is on PATH
    uv run python tooling/host_smoke.py --require claude # fail, not skip, when claude is missing
    uv run python tooling/host_smoke.py --codex-bin /path/to/codex --json report.json

Each host runs against a staged copy of the working tree, with HOME and the
host's config directory pointed at a fresh temporary directory, so the real
installs and settings on the machine are never read or written. Only
commands that do not reach a model are used:

claude  `plugin validate --strict` on both manifests and on a plugin-only stage
        (with a negative control that must be flagged, proving skills are
        scanned); `--plugin-dir … plugin details` for the skill names and the
        always-on token estimate, which is computed from each description; and
        a local-marketplace `install` whose cached SKILL.md files must match
        the source byte for byte in name and description.
codex   `plugin marketplace add` of the stage, `plugin add`, `plugin list
        --json`, and `debug prompt-input`, which renders the exact skill list
        the model would see. Descriptions Codex shortens to fit its listing
        budget are reported, and each "Do not use" clause is classed as kept
        whole, partly cut or lost.
cursor  Static only: Cursor's agent CLI lists plugins only through an account
        marketplace, so the manifests, the default `skills/` layout and the
        routing rules are checked against Cursor's documented plugin format
        (the key sets in registry/hosts.json `cursor.plugin_format`).

A host whose CLI is absent is SKIP, unless named in --require. Exit status is
non-zero when any exercised host FAILs.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tooling"))
from compatibility import read_frontmatter, safe_load_unique  # noqa: E402

PLUGIN = "cometweb-agent-skills"
# What a host needs to load the plugin; tooling, tests and docs stay behind.
PAYLOAD = (".claude-plugin", ".cursor-plugin", ".agents", "plugin.json", "skills", "rules", "VERSION", "LICENSE",
           "NOTICE", "README.md")
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache", "*.local.json", "*.local.txt")
TIMEOUT = 180

# Cursor plugin reference (https://cursor.com/docs/reference/plugins); the key
# sets live in registry/hosts.json with the date they were checked.
CURSOR_PLUGIN_NAME = re.compile(r"^[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$")
CURSOR_PATH_KEYS = ("logo", "rules", "agents", "skills", "commands", "hooks", "mcpServers")
CURSOR_RULES = ("rules/cometweb-agent-skills.mdc", "docs/generated-cursor-routing.mdc", "extras/cursor-routing.mdc")


def cursor_format(root: Path = ROOT) -> dict:
    """`cursor.plugin_format` from hosts.json, plus the path of the rule the plugin ships."""
    cursor = json.loads((root / "registry" / "hosts.json").read_text(encoding="utf-8"))["hosts"]["cursor"]
    return {**cursor["plugin_format"], "plugin_rule": cursor["plugin_rule"]}


@dataclass
class HostResult:
    host: str
    status: str = "PASS"  # PASS | FAIL | SKIP
    checks: list[dict] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def check(self, name: str, ok: bool, detail: str = "") -> bool:
        self.checks.append({"check": name, "ok": bool(ok), "detail": detail})
        if not ok:
            self.status = "FAIL"
        return bool(ok)

    def skip(self, reason: str) -> HostResult:
        self.status = "SKIP"
        self.findings.append(reason)
        return self


def expected_skills(root: Path = ROOT) -> dict[str, str]:
    """{name: description} as the repository's own parser reads every SKILL.md."""
    out: dict[str, str] = {}
    for skill_md in sorted((root / "skills").glob("*/SKILL.md")):
        data = read_frontmatter(skill_md)
        out[str(data.get("name", skill_md.parent.name))] = str(data.get("description", ""))
    return out


def stage_payload(dest: Path, root: Path = ROOT) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    for rel in PAYLOAD:
        src = root / rel
        if src.is_dir():
            shutil.copytree(src, dest / rel, ignore=IGNORE)
        elif src.is_file():
            shutil.copy2(src, dest / rel)
    return dest


def isolated_env(base: Path, **extra: str) -> dict[str, str]:
    home = base / "home"
    home.mkdir(parents=True, exist_ok=True)
    env = {"PATH": os.environ.get("PATH", ""), "HOME": str(home), "TMPDIR": str(base),
           "LANG": "C.UTF-8", "NO_COLOR": "1", "CI": "1"}
    env.update(extra)
    return env


def run(argv: list[str], env: dict[str, str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(argv, env=env, cwd=cwd, capture_output=True, text=True, check=False, timeout=TIMEOUT)


def normalise(text: str) -> str:
    return " ".join(text.split())


# --------------------------------------------------------------------------- claude

def parse_claude_details(text: str) -> tuple[list[str], dict[str, str]]:
    """Skill names and per-skill always-on estimates from `claude plugin details`."""
    match = re.search(r"Skills \((\d+)\)\s+(.+)", text)
    names = [n.strip() for n in match.group(2).split(",")] if match else []
    estimates: dict[str, str] = {}
    for line in text.splitlines():
        row = re.match(r"^\s+([a-z0-9][a-z0-9-]*)\s+(< ?\d+|~[\d.]+k?)\s+(< ?\d+|~[\d.]+k?)\s*$", line)
        if row:
            estimates[row.group(1)] = row.group(2)
    return names, estimates


def estimate_tokens(value: str) -> float | None:
    value = value.replace(" ", "")
    if value.startswith("<"):
        return None
    number = value.lstrip("~")
    return float(number[:-1]) * 1000 if number.endswith("k") else float(number)


def description_seen(estimate: str, name: str, description: str) -> bool:
    """Claude's always-on estimate is about (name + description) / 4 tokens.

    A description Claude failed to read (empty, unparsed frontmatter) shows as
    "< 20"; a matching estimate shows the whole description reached the listing.
    """
    expected = (len(name) + len(description)) / 4
    got = estimate_tokens(estimate)
    if got is None:
        return expected < 20
    return abs(got - expected) <= max(20.0, 0.25 * expected)


def validate_report(claude: str, target: Path, env: dict[str, str], cwd: Path) -> tuple[int, dict]:
    proc = run([claude, "plugin", "validate", "--strict", "--json", str(target)], env, cwd)
    try:
        return proc.returncode, json.loads(proc.stdout)
    except json.JSONDecodeError:
        return proc.returncode, {"success": False, "raw": (proc.stdout + proc.stderr)[-2000:]}


def report_issues(report: dict) -> list[str]:
    issues = []
    manifest = report.get("manifest") or {}
    for level in ("errors", "warnings"):
        issues += [f"manifest {level[:-1]}: {item.get('message')}" for item in manifest.get(level, [])]
    for item in report.get("contents", []):
        for level in ("errors", "warnings"):
            issues += [f"{item.get('file')}: {entry.get('message')}" for entry in item.get(level, [])]
    return issues


def smoke_claude(claude: str, work: Path, expected: dict[str, str], version: str) -> HostResult:
    result = HostResult("claude-code")
    env = isolated_env(work, CLAUDE_CONFIG_DIR=str(work / "claude-config"))
    stage = stage_payload(work / "stage")
    proc = run([claude, "--version"], env, work)
    result.facts["cli_version"] = proc.stdout.strip()

    for manifest in (".claude-plugin/plugin.json", ".claude-plugin/marketplace.json"):
        code, report = validate_report(claude, stage / manifest, env, work)
        issues = report_issues(report)
        result.check(f"validate --strict {manifest}", code == 0 and report.get("success") and not issues,
                     "; ".join(issues))

    # With a marketplace.json beside it, validate stops at the marketplace; a
    # plugin-only copy makes it walk skills/. The control proves it really did.
    plugin_only = stage_payload(work / "plugin-only")
    (plugin_only / ".claude-plugin" / "marketplace.json").unlink()
    code, report = validate_report(claude, plugin_only, env, work)
    issues = report_issues(report)
    result.check("validate --strict every SKILL.md", code == 0 and report.get("success") and not issues,
                 "; ".join(issues))
    control = stage_payload(work / "control")
    (control / ".claude-plugin" / "marketplace.json").unlink()
    victim = sorted(expected)[0]
    (control / "skills" / victim / "SKILL.md").write_text("no frontmatter\n", encoding="utf-8")
    _, report = validate_report(claude, control, env, work)
    flagged = [line for line in report_issues(report) if f"/{victim}/SKILL.md" in line]
    result.check("negative control: broken SKILL.md is reported", bool(flagged),
                 "validator did not read skills/ — the SKILL.md check above proves nothing" if not flagged else "")

    proc = run([claude, "--plugin-dir", str(stage), "plugin", "details", PLUGIN], env, work)
    names, estimates = parse_claude_details(proc.stdout)
    result.check("--plugin-dir discovers every skill", sorted(names) == sorted(expected),
                 f"missing={sorted(set(expected) - set(names))} extra={sorted(set(names) - set(expected))}")
    unread = [n for n, d in expected.items() if n not in estimates or not description_seen(estimates[n], n, d)]
    result.check("every description reaches the always-on listing", not unread,
                 ", ".join(f"{n}={estimates.get(n)}" for n in unread))
    always_on = re.search(r"Always-on:\s+~?([\d,]+) tok", proc.stdout)
    if always_on:
        result.facts["always_on_tokens"] = int(always_on.group(1).replace(",", ""))

    # Install the way a user does, from a marketplace, into the isolated config.
    market = work / "market"
    stage_payload(market / "plugin")
    (market / "plugin" / ".claude-plugin" / "marketplace.json").unlink()
    (market / ".claude-plugin").mkdir(parents=True)
    (market / ".claude-plugin" / "marketplace.json").write_text(json.dumps({
        "name": "host-smoke", "owner": {"name": "host-smoke"},
        "plugins": [{"name": PLUGIN, "source": "./plugin", "description": "host smoke"}],
    }), encoding="utf-8")
    added = run([claude, "plugin", "marketplace", "add", str(market)], env, work)
    result.check("marketplace add (local)", added.returncode == 0, added.stderr[-500:])
    installed = run([claude, "plugin", "install", f"{PLUGIN}@host-smoke"], env, work)
    result.check("plugin install", installed.returncode == 0, (installed.stdout + installed.stderr)[-500:])
    listed = run([claude, "plugin", "list", "--json"], env, work)
    try:
        rows = json.loads(listed.stdout)
    except json.JSONDecodeError:
        rows = []
    row = next((r for r in rows if r.get("id") == f"{PLUGIN}@host-smoke"), None)
    result.check("plugin list shows the installed version", bool(row) and row.get("version") == version,
                 json.dumps(row)[:300])
    if row and row.get("installPath"):
        cached = Path(row["installPath"])
        drift = [n for n, d in expected.items()
                 if not (cached / "skills" / n / "SKILL.md").is_file()
                 or read_frontmatter(cached / "skills" / n / "SKILL.md").get("description") != d]
        result.check("installed copy carries every skill unchanged", not drift, ", ".join(drift))
    details = run([claude, "plugin", "details", f"{PLUGIN}@host-smoke"], env, work)
    names, _ = parse_claude_details(details.stdout)
    result.check("installed plugin discovers every skill", sorted(names) == sorted(expected),
                 f"found {len(names)} of {len(expected)}")
    return result


# --------------------------------------------------------------------------- codex

def codex_skill_listing(prompt_input: object, namespace: str = PLUGIN) -> dict[str, str]:
    """{skill: description as shown to the model} from `codex debug prompt-input` JSON."""
    texts: list[str] = []
    stack = [prompt_input]
    while stack:
        node = stack.pop()
        if isinstance(node, str):
            texts.append(node)
        elif isinstance(node, dict):
            stack.extend(node.values())
        elif isinstance(node, list):
            stack.extend(node)
    pattern = re.compile(rf"^- {re.escape(namespace)}:([a-z0-9-]+): (.*) \(file: [^)]*\)$", re.M)
    return {m.group(1): m.group(2) for text in texts for m in pattern.finditer(text)}


SENTENCE_START = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")


def do_not_clause_span(text: str) -> tuple[int, int] | None:
    """(start, end) of the first run of consecutive sentences that open with "Do not"."""
    starts = [0, *(m.end() for m in SENTENCE_START.finditer(text))]
    bounds = list(zip(starts, [*(m.start() for m in SENTENCE_START.finditer(text)), len(text)], strict=True))
    span: tuple[int, int] | None = None
    for start, end in bounds:
        if text.startswith("Do not", start):
            span = (span[0] if span else start, end)
        elif span:
            break
    return span


def clause_state(seen: str, whole: str) -> str:
    """kept | partial | lost | none: how much of the "Do not" clause a shortened prefix keeps."""
    span = do_not_clause_span(whole)
    if span is None:
        return "none"
    if not whole.startswith(seen):
        return "lost"
    if len(seen) >= span[1]:
        return "kept"
    return "partial" if len(seen) > span[0] else "lost"


def codex_truncation(shown: dict[str, str], expected: dict[str, str]) -> dict[str, dict]:
    """Per shortened skill: how much of the description Codex shows, and what is left of its guardrail."""
    out = {}
    for name, full in expected.items():
        seen, whole = normalise(shown.get(name, "")), normalise(full)
        if seen == whole:
            continue
        out[name] = {"shown": len(seen), "full": len(whole), "prefix": whole.startswith(seen),
                     "do_not_clause": clause_state(seen, whole)}
    return out


def codex_clause_summary(shown: dict[str, str], expected: dict[str, str]) -> dict[str, list[str]]:
    """Every skill, shortened or not, grouped by what the model sees of its "Do not" clause."""
    summary: dict[str, list[str]] = {"kept": [], "partial": [], "lost": [], "none": []}
    for name, full in sorted(expected.items()):
        summary[clause_state(normalise(shown.get(name, "")), normalise(full))].append(name)
    return summary


def smoke_codex(codex: str, work: Path, expected: dict[str, str], version: str) -> HostResult:
    result = HostResult("openai-codex")
    codex_home = work / "home" / ".codex"
    codex_home.mkdir(parents=True, exist_ok=True)
    env = isolated_env(work, CODEX_HOME=str(codex_home))
    stage = stage_payload(work / "stage")
    empty = work / "cwd"
    empty.mkdir()
    proc = run([codex, "--version"], env, empty)
    result.facts["cli_version"] = proc.stdout.strip()

    added = run([codex, "plugin", "marketplace", "add", str(stage)], env, empty)
    result.check("marketplace add (local)", added.returncode == 0, (added.stdout + added.stderr)[-500:])
    install = run([codex, "plugin", "add", f"{PLUGIN}@{PLUGIN}", "--json"], env, empty)
    result.check("plugin add", install.returncode == 0, (install.stdout + install.stderr)[-500:])
    listed = run([codex, "plugin", "list", "--json"], env, empty)
    try:
        rows = json.loads(listed.stdout).get("installed", [])
    except (json.JSONDecodeError, AttributeError):
        rows = []
    row = next((r for r in rows if r.get("name") == PLUGIN), None)
    result.check("plugin list shows it installed and enabled",
                 bool(row) and row.get("enabled") and row.get("version") == version, json.dumps(row)[:300])

    rendered = run([codex, "debug", "prompt-input"], env, empty)
    try:
        shown = codex_skill_listing(json.loads(rendered.stdout))
    except json.JSONDecodeError:
        shown = {}
    result.check("model-visible skill list names every skill", sorted(shown) == sorted(expected),
                 f"missing={sorted(set(expected) - set(shown))} extra={sorted(set(shown) - set(expected))}")
    cut = codex_truncation(shown, expected)
    result.check("every shown description is a prefix of the SKILL.md one",
                 all(v["prefix"] for v in cut.values()), ", ".join(n for n, v in cut.items() if not v["prefix"]))
    result.facts["descriptions_shortened"] = len(cut)
    result.facts["shown_chars"] = sum(len(v) for v in shown.values())
    result.facts["full_chars"] = sum(len(normalise(v)) for v in expected.values())
    clauses = codex_clause_summary(shown, expected)
    result.facts["do_not_clause"] = clauses
    if cut:
        result.findings.append(
            f"Codex shortens {len(cut)} of {len(expected)} descriptions to fit its skill-list budget "
            f"({result.facts['shown_chars']} of {result.facts['full_chars']} characters shown).")
    result.findings.append(
        f"'Do not' clause in the model-visible list: {len(clauses['kept'])} kept whole, "
        f"{len(clauses['partial'])} cut part-way, {len(clauses['lost'])} lost, {len(clauses['none'])} without one"
        + (f"; cut: {', '.join(clauses['partial'] + clauses['lost'])}" if clauses["partial"] or clauses["lost"] else "")
        + ".")
    return result


# --------------------------------------------------------------------------- cursor

def read_mdc_frontmatter(path: Path) -> dict | None:
    match = re.match(r"^---\s*\n(.*?)\n---", path.read_text(encoding="utf-8"), re.S)
    return safe_load_unique(match.group(1)) if match else None


def relative_path_ok(value: object) -> bool:
    values = value if isinstance(value, list) else [value]
    return all(isinstance(v, str) and not v.startswith("/") and ".." not in Path(v).parts for v in values)


def smoke_cursor(root: Path, expected: dict[str, str], cursor_agent: str | None = None,
                 work: Path | None = None) -> HostResult:
    result = HostResult("cursor")
    fmt = cursor_format()
    plugin = json.loads((root / ".cursor-plugin" / "plugin.json").read_text(encoding="utf-8"))
    result.check("plugin.json name is a valid Cursor plugin name",
                 isinstance(plugin.get("name"), str) and bool(CURSOR_PLUGIN_NAME.match(plugin["name"])),
                 str(plugin.get("name")))
    author = plugin.get("author")
    result.check("author, when present, has a name",
                 author is None or (isinstance(author, dict) and isinstance(author.get("name"), str)), str(author))
    bad_paths = [k for k in CURSOR_PATH_KEYS if k in plugin and not relative_path_ok(plugin[k])]
    result.check("manifest paths are relative and stay inside the plugin", not bad_paths, ", ".join(bad_paths))
    undocumented = sorted(set(plugin) - set(fmt["manifest_keys"]))
    if isinstance(author, dict):
        undocumented += [f"author.{k}" for k in sorted(set(author) - set(fmt["author_keys"]))]
    result.check("plugin.json uses only keys Cursor documents", not undocumented, ", ".join(undocumented))

    market = json.loads((root / ".cursor-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    owner = market.get("owner")
    result.check("marketplace has name, owner.name and plugins",
                 isinstance(market.get("name"), str) and isinstance(owner, dict)
                 and isinstance(owner.get("name"), str) and isinstance(market.get("plugins"), list),
                 json.dumps({k: market.get(k) for k in ("name", "owner")}))
    entries = market.get("plugins") or []
    names = [e.get("name") for e in entries]
    result.check("marketplace plugin names are unique", len(names) == len(set(names)), str(names))
    plugin_root = (market.get("metadata") or {}).get("pluginRoot", "")
    for entry in entries:
        source = entry.get("source")
        source_path = source if isinstance(source, str) else (source or {}).get("path")
        target = (root / plugin_root / str(source_path)).resolve()
        result.check(f"marketplace source for {entry.get('name')} is a plugin root",
                     relative_path_ok(source_path) and (target / ".cursor-plugin" / "plugin.json").is_file(),
                     str(source_path))
    undocumented = sorted(set(market) - set(fmt["marketplace_keys"]))
    result.check("marketplace.json uses only keys Cursor documents", not undocumented, ", ".join(undocumented))

    # No `skills` key: Cursor discovers skills/<dir>/SKILL.md by default.
    skills_dir = root / str(plugin.get("skills", "skills"))
    found = sorted(p.parent.name for p in skills_dir.glob("*/SKILL.md"))
    result.check("default skills/ layout holds every skill", found == sorted(expected),
                 f"found {len(found)} of {len(expected)}")
    stray = sorted(p.name for p in skills_dir.iterdir() if p.is_dir() and not (p / "SKILL.md").is_file())
    result.check("no skills/ subdirectory lacks a SKILL.md", not stray, ", ".join(stray))

    # A manifest `rules` key replaces folder discovery, so the rule must sit in
    # the default rules/ directory with no such key.
    rule = root / fmt["plugin_rule"]
    result.check("plugin ships its routing rule where Cursor discovers rules",
                 "rules" not in plugin and rule.is_file() and rule.parent == root / fmt["rules_dir"]
                 and rule.suffix in fmt["rule_extensions"],
                 f"rules key={plugin.get('rules')!r}, {fmt['plugin_rule']} exists={rule.is_file()}")
    for rel in CURSOR_RULES:
        if not (root / rel).is_file():
            continue
        fm = read_mdc_frontmatter(root / rel)
        ok = (isinstance(fm, dict) and isinstance(fm.get("description"), str) and fm["description"].strip() != ""
              and isinstance(fm.get("alwaysApply"), bool)
              and (fm.get("globs") is None or isinstance(fm["globs"], (str, list)))
              and set(fm) <= set(fmt["rule_frontmatter_keys"]))
        result.check(f"{rel} has Cursor rule frontmatter", ok, json.dumps(fm, default=str)[:300])

    if cursor_agent and work is not None:
        proc = run([cursor_agent, "--version"], isolated_env(work), work)
        result.facts["cli_version"] = proc.stdout.strip()
        result.findings.append("cursor-agent lists plugins only through an account marketplace; the CLI was not "
                               "used to load the plugin, so Cursor coverage is static.")
    return result


# --------------------------------------------------------------------------- main

def find_cli(name: str, explicit: str | None) -> str | None:
    if explicit:
        return explicit if Path(explicit).is_file() else None
    return shutil.which(name)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--host", action="append", choices=("claude", "codex", "cursor"),
                        help="host to run (repeatable; default: all)")
    parser.add_argument("--require", default="", help="comma-separated hosts that must not be skipped")
    parser.add_argument("--claude-bin", default=os.environ.get("CLAUDE_BIN"))
    parser.add_argument("--codex-bin", default=os.environ.get("CODEX_BIN"))
    parser.add_argument("--json", type=Path, help="also write the full report here")
    args = parser.parse_args(argv)
    hosts = args.host or ["claude", "codex", "cursor"]
    required = {h.strip() for h in args.require.split(",") if h.strip()}
    unknown = required - {"claude", "codex", "cursor"}
    if unknown:
        parser.error(f"unknown --require host(s): {sorted(unknown)}")

    expected = expected_skills()
    version = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]
    results: list[HostResult] = []
    with tempfile.TemporaryDirectory(prefix="host-smoke-") as tmp:
        base = Path(tmp)
        if "claude" in hosts:
            cli = find_cli("claude", args.claude_bin)
            results.append(smoke_claude(cli, base / "claude", expected, version) if cli
                           else HostResult("claude-code").skip("claude CLI not found"))
        if "codex" in hosts:
            cli = find_cli("codex", args.codex_bin)
            results.append(smoke_codex(cli, base / "codex", expected, version) if cli
                           else HostResult("openai-codex").skip("codex CLI not found (pass --codex-bin)"))
        if "cursor" in hosts:
            (base / "cursor").mkdir()
            results.append(smoke_cursor(ROOT, expected, shutil.which("cursor-agent"), base / "cursor"))

    short = {"claude-code": "claude", "openai-codex": "codex", "cursor": "cursor"}
    failed = False
    for res in results:
        if res.status == "SKIP" and short[res.host] in required:
            res.status = "FAIL"
        failed |= res.status == "FAIL"
        print(f"{res.status:4}  {res.host}  {res.facts.get('cli_version', '')}".rstrip())
        for c in res.checks:
            print(f"      {'ok  ' if c['ok'] else 'FAIL'}  {c['check']}" + (f" — {c['detail']}" if c["detail"] and not c["ok"] else ""))
        for note in res.findings:
            print(f"      note  {note}")
    if args.json:
        args.json.write_text(json.dumps({"skills": len(expected), "version": version,
                                         "results": [res.__dict__ for res in results]}, indent=2) + "\n",
                             encoding="utf-8")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
