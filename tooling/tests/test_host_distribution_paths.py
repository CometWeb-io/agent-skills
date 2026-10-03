"""Every path a host manifest names must exist, and every version must agree.

registry/hosts.json once advertised a Cursor extra at the repository root
(`extras/cursor-rule.mdc`) that only existed inside some skill packages, while
the file the installer really uses lived elsewhere. Nothing read the field, so
nothing noticed. These checks resolve each path against the root it is
relative to, and fail when a new path-like key appears without being classified.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SKILLS = ROOT / "skills"

# hosts.json keys whose values are paths relative to the repository root.
REPO_PATH_KEYS = {"marketplace_manifest", "plugin_root", "source_of_truth", "routing_rule", "routing_rule_fallback",
                  "plugin_rule"}
# hosts.json keys whose values are paths relative to one skill package.
PACKAGE_PATH_KEYS = {"agents_file", "package_optional_extras", "required_files"}
# hosts.json keys that hold home-directory install targets, not repository paths.
INSTALL_TARGET_KEYS = {"skill_dirs", "legacy_skill_dirs"}
PATH_LIKE_KEY = re.compile(r"(_file|_files|_manifest|_root|_rule|_extras|_dirs|_of_truth|_fallback)$")

PLUGIN_FILES = (
    "plugin.json",
    ".claude-plugin/plugin.json",
    ".cursor-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
    ".cursor-plugin/marketplace.json",
    ".agents/plugins/marketplace.json",
)


def read_json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def hosts() -> dict[str, dict]:
    return read_json("registry/hosts.json")["hosts"]


def as_list(value: object) -> list[str]:
    return [value] if isinstance(value, str) else list(value)


def skill_ids() -> list[str]:
    return sorted(path.parent.name for path in SKILLS.glob("*/SKILL.md"))


def test_every_path_like_host_key_is_classified() -> None:
    known = REPO_PATH_KEYS | PACKAGE_PATH_KEYS | INSTALL_TARGET_KEYS
    unclassified = {
        f"{host}.{key}"
        for host, profile in hosts().items()
        for key in profile
        if PATH_LIKE_KEY.search(key) and key not in known
    }
    assert not unclassified, f"classify these hosts.json keys in this test: {sorted(unclassified)}"


@pytest.mark.parametrize("host", sorted(hosts()))
def test_repository_paths_in_hosts_json_exist(host: str) -> None:
    profile = hosts()[host]
    for key in REPO_PATH_KEYS & profile.keys():
        for relative in as_list(profile[key]):
            path = (ROOT / relative).resolve()
            assert path.exists(), f"{host}.{key}: {relative} does not exist"
            assert path == ROOT or ROOT in path.parents, f"{host}.{key}: {relative} escapes the repository"


@pytest.mark.parametrize("host", sorted(hosts()))
def test_package_paths_in_hosts_json_are_shipped(host: str) -> None:
    profile = hosts()[host]
    for key in PACKAGE_PATH_KEYS & profile.keys():
        for relative in as_list(profile[key]):
            shipped_by = [sid for sid in skill_ids() if (SKILLS / sid / relative).is_file()]
            assert shipped_by, f"{host}.{key}: no skill package ships {relative}"
            assert not (ROOT / relative).exists() or key == "required_files", (
                f"{host}.{key}: {relative} is package-relative but also exists at the repository root"
            )


def test_cursor_installer_uses_the_rule_files_named_in_hosts_json() -> None:
    cursor = hosts()["cursor"]
    installer = (ROOT / "scripts" / "install-cursor.sh").read_text(encoding="utf-8")
    assert f'RULE_SRC="$ROOT/{cursor["routing_rule"]}"' in installer
    assert f'LEGACY_RULE_SRC="$ROOT/{cursor["routing_rule_fallback"]}"' in installer


@pytest.mark.parametrize("skill", skill_ids())
def test_extras_named_in_a_skill_install_guide_exist(skill: str) -> None:
    guide = SKILLS / skill / "INSTALL.md"
    if not guide.is_file():
        pytest.skip("package has no INSTALL.md")
    for relative in re.findall(r"`(extras/[^`\s]+)`", guide.read_text(encoding="utf-8")):
        assert (SKILLS / skill / relative).is_file(), f"{skill}/INSTALL.md names missing {relative}"


def relative_strings(value: object, key: str = "") -> list[tuple[str, str]]:
    """Every string in a manifest that is a path: './'-prefixed or a local source path."""
    found: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for child_key, child in value.items():
            if child_key == "$schema":
                continue
            found.extend(relative_strings(child, child_key))
    elif isinstance(value, list):
        for child in value:
            found.extend(relative_strings(child, key))
    elif isinstance(value, str) and (value.startswith("./") or (key in {"path", "source"} and value.startswith("."))):
        found.append((key, value))
    return found


@pytest.mark.parametrize("manifest", PLUGIN_FILES)
def test_relative_paths_in_plugin_manifests_resolve_inside_the_repository(manifest: str) -> None:
    data = read_json(manifest)
    for key, relative in relative_strings(data):
        path = (ROOT / relative).resolve()
        assert path.exists(), f"{manifest}: {key}={relative} does not exist"
        assert path == ROOT or ROOT in path.parents, f"{manifest}: {key}={relative} escapes the repository"


def test_relative_path_scan_sees_nested_sources() -> None:
    sample = {"$schema": "./ignored.json", "plugins": [{"source": {"source": "local", "path": "./x"}}, {"source": "./y"}]}
    assert relative_strings(sample) == [("path", "./x"), ("source", "./y")]


@pytest.mark.parametrize("marketplace", (".cursor-plugin/marketplace.json", ".agents/plugins/marketplace.json"))
def test_local_marketplace_source_is_a_loadable_plugin_root(marketplace: str) -> None:
    source = read_json(marketplace)["plugins"][0]["source"]
    root = (ROOT / (source if isinstance(source, str) else source["path"])).resolve()
    assert (root / "plugin.json").is_file()
    assert sorted(p.parent.name for p in (root / "skills").glob("*/SKILL.md")) == skill_ids()


def test_every_manifest_version_matches_version_file() -> None:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    assert re.fullmatch(r"\d+\.\d+\.\d+", version)
    for manifest in PLUGIN_FILES:
        data = read_json(manifest)
        versions = [("version", data.get("version"))] + [
            (f"plugins[{entry.get('name')}].version", entry.get("version")) for entry in data.get("plugins", [])
        ]
        for label, value in versions:
            # Claude Code and Codex cache an installed plugin by this version, so
            # a manifest that lags VERSION keeps users on the old skill set.
            assert value in (None, version), f"{manifest}: {label}={value!r} != VERSION {version!r}"
    assert read_json(".claude-plugin/plugin.json")["version"] == version


def test_registry_versions_match_package_version_files() -> None:
    registry = {entry["id"]: entry["version"] for entry in read_json("registry/skills.json")["skills"]}
    on_disk = {sid: (SKILLS / sid / "VERSION").read_text(encoding="utf-8").strip() for sid in skill_ids()}
    assert registry == on_disk


def load_openai_validator():
    spec = importlib.util.spec_from_file_location("validate_openai_plugin", ROOT / "tooling" / "validate_openai_plugin.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda entry: entry.pop("policy"), "policy.installation"),
        (lambda entry: entry["policy"].update(installation="SOMETIMES"), "policy.installation"),
        (lambda entry: entry["policy"].pop("authentication"), "policy.authentication"),
        (lambda entry: entry.pop("category"), "category"),
    ],
)
def test_openai_validator_requires_policy_and_category(
    mutation, message: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    validator = load_openai_validator()
    data = read_json(".agents/plugins/marketplace.json")
    mutation(data["plugins"][0])
    broken = tmp_path / "marketplace.json"
    broken.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr(validator, "MARKETPLACE", broken)
    monkeypatch.setattr(validator, "load", lambda path: json.loads(path.read_text(encoding="utf-8")))
    with pytest.raises(SystemExit):
        validator.main()
    assert message in capsys.readouterr().err


def test_openai_validator_accepts_the_shipped_marketplace(capsys: pytest.CaptureFixture[str]) -> None:
    load_openai_validator().main()
    assert "OK: validate_openai_plugin" in capsys.readouterr().out


@pytest.mark.skipif(shutil.which("claude") is None, reason="Claude Code CLI not installed")
@pytest.mark.parametrize("manifest", (".claude-plugin/plugin.json", ".claude-plugin/marketplace.json"))
def test_claude_cli_validates_the_plugin_strictly(manifest: str, tmp_path: Path) -> None:
    # An isolated config dir and HOME keep the real Claude Code settings untouched.
    env = {"PATH": os.environ["PATH"], "HOME": str(tmp_path / "home"),
           "CLAUDE_CONFIG_DIR": str(tmp_path / "claude")}
    result = subprocess.run(["claude", "plugin", "validate", "--strict", "--json", str(ROOT / manifest)],
                            env=env, capture_output=True, text=True, check=False, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report["success"] is True
    assert not report["manifest"]["errors"] and not report["manifest"]["warnings"]


@pytest.mark.skipif(shutil.which("claude") is None, reason="Claude Code CLI not installed")
def test_claude_loads_every_skill_from_the_working_tree(tmp_path: Path) -> None:
    env = {"PATH": os.environ["PATH"], "HOME": str(tmp_path / "home"), "CLAUDE_CONFIG_DIR": str(tmp_path / "claude")}
    result = subprocess.run(["claude", "--plugin-dir", str(ROOT), "plugin", "details", "cometweb-agent-skills"],
                            env=env, capture_output=True, text=True, check=False, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
    match = re.search(r"Skills \((\d+)\)\s+(.+)", result.stdout)
    assert match, result.stdout
    assert int(match.group(1)) == len(skill_ids())
    assert sorted(match.group(2).split(", ")) == skill_ids()
