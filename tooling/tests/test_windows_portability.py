"""Regressions for the Windows failures of portable tooling, without model calls."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import subprocess
import sys

import pytest

import grade_output as grader
import package_skill as package
import run_behavior_evals as runner

ROOT = Path(__file__).resolve().parents[2]
UNICODE = "Zażółć gęślą jaźń → \u200b"


def test_autocrlf_checkout_preserves_frozen_bytes_and_binary(tmp_path):
    """Checkout policy must protect byte-pinned files, not normalize their hashes."""
    source = ROOT / "evals/routing/holdout.json"
    frozen = source.read_bytes()
    expected_hash = "e14eacb0865e00819b04a0659903c4109b1908ab5e8b2f87ce5805950d22ab59"
    assert hashlib.sha256(frozen).hexdigest() == expected_hash
    skill = b"---\nname: demo\ndescription: A synthetic portable skill fixture.\n---\n# Demo\n"
    contents = {"holdout.json": frozen, "SKILL.md": skill, "image.bin": b"\x00\x01\r\n\xff\n"}
    env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}

    def git(*args):
        return subprocess.run(["git", "-c", "commit.gpgsign=false", *args], cwd=tmp_path,
                              env=env, capture_output=True, encoding="utf-8", check=True)

    git("init", "-q")
    git("config", "core.autocrlf", "true")
    git("config", "user.name", "Fixture")
    git("config", "user.email", "fixture@example.invalid")
    if (ROOT / ".gitattributes").exists():
        (tmp_path / ".gitattributes").write_bytes((ROOT / ".gitattributes").read_bytes())
    for name, blob in contents.items():
        (tmp_path / name).write_bytes(blob)
    git("add", ".")
    git("commit", "-qm", "Synthetic checkout fixture")
    for name in contents:
        (tmp_path / name).unlink()
    git("checkout-index", "--all", "--force")
    for name, blob in contents.items():
        assert (tmp_path / name).read_bytes() == blob, name
    assert hashlib.sha256((tmp_path / "holdout.json").read_bytes()).hexdigest() == expected_hash
    package.validate_frontmatter((tmp_path / "SKILL.md").read_bytes(), "demo")


def test_frontmatter_accepts_crlf_without_rewriting_payload_bytes():
    blob = b"---\r\nname: demo\r\ndescription: A synthetic CRLF package fixture.\r\n---\r\n# Demo\r\n"
    package.validate_frontmatter(blob, "demo")
    entries = {"SKILL.md": blob, "VERSION": b"1.0.0\n", "LICENSE": b"Synthetic license.\n"}
    manifest = {"schema": "cometweb.package/v1", "skill": "demo", "version": "1.0.0",
                "policy_sha256": "a" * 64, "runtime_acceptance": "not_assessed",
                "files": {name: hashlib.sha256(data).hexdigest() for name, data in entries.items()}}
    manifest["payload_sha256"] = package.digest(package.canonical({
        "files": manifest["files"], "policy_sha256": manifest["policy_sha256"]}))
    import io
    import zipfile
    archive = package.archive(entries, manifest)
    assert package.inspect_archive(archive)["files"]["SKILL.md"] == hashlib.sha256(blob).hexdigest()
    with zipfile.ZipFile(io.BytesIO(archive)) as zipped:
        assert zipped.read("SKILL.md") == blob


@pytest.mark.parametrize("blob", [
    b"name: demo\r\ndescription: Missing delimiters.\r\n",
    b"---\r\nname: demo\r\ndescription: Missing closing delimiter.\r\n",
    b"---\r\nname: other\r\ndescription: Wrong skill identity.\r\n---\r\n",
    b"---\r\nname: demo\r\nname: other\r\ndescription: Duplicate identity.\r\n---\r\n",
])
def test_crlf_does_not_bless_invalid_frontmatter(blob):
    with pytest.raises(ValueError):
        package.validate_frontmatter(blob, "demo")


def test_behavior_subprocess_roundtrips_unicode_under_cp1252(tmp_path, monkeypatch):
    scripts = tmp_path / "skills/demo/scripts"
    scripts.mkdir(parents=True)
    (scripts / "echo.py").write_text(
        "import json, sys\nvalue = json.load(sys.stdin)\n"
        "print(json.dumps(value, ensure_ascii=False))\n", encoding="utf-8")
    monkeypatch.setattr(runner, "SKILLS", tmp_path / "skills")
    # Windows' parent-side default codec, while the real child emits UTF-8.
    monkeypatch.setattr(subprocess, "_text_encoding", lambda: "cp1252")
    case = {"id": "unicode", "run": ["scripts/echo.py"], "stdin": {"text": UNICODE},
            "expect": {"exit_code": 0, "json": {"text": UNICODE}}}
    assert runner.run_command_case("demo", case) == []
    case["expect"]["json"]["text"] = "Incorrect result"
    assert any("expected 'Incorrect result'" in issue for issue in runner.run_command_case("demo", case))


@pytest.mark.parametrize("output,expected", [
    (r"Workspace root: C:\scratch\case", "Workspace root: {tmp}"),
    ("Workspace root: C:/scratch/case", "Workspace root: {tmp}"),
    (r"missing: 'C:\scratch\case\science-roaster\evals\trigger-evals.json'",
     "missing: '{tmp}/science-roaster/evals/trigger-evals.json'"),
    (r"missing: 'C:\\scratch\\case\\science-roaster\\evals\\trigger-evals.json'",
     "missing: '{tmp}/science-roaster/evals/trigger-evals.json'"),
    (r'{"path":"C:\\scratch\\case\\input.json"}', '{"path":"{tmp}/input.json"}'),
])
def test_scratch_path_spelling_is_portable(output, expected):
    assert runner.normalize_scratch_paths(output, PureWindowsPath(r"C:\scratch\case"),
                                          {"stdout_contains": [expected]}) == expected


def test_scratch_normalization_preserves_wrong_roots_filenames_and_nonpath_escapes():
    text = r"C:\scratch\case-other\input.json C:\foreign\case\input.json literal\n"
    expect = {"stdout_contains": ["{tmp}/input.json"]}
    root = PureWindowsPath(r"C:\scratch\case")
    assert runner.normalize_scratch_paths(text, root, expect) == text
    wrong = r"missing C:\scratch\case\different.json"
    assert "{tmp}/input.json" not in runner.normalize_scratch_paths(wrong, root, expect)


def test_json_escaped_unicode_scratch_root_remains_a_valid_json_path():
    root = PureWindowsPath("C:/Users/Zażółć/case")
    captured = json.dumps({"path": str(root / "input.json")})
    normalized = runner.normalize_scratch_paths(captured, root, {"json": {"path": "{tmp}/input.json"}})
    assert json.loads(normalized) == {"path": "{tmp}/input.json"}


def test_missing_suite_refusal_has_portable_relative_path(monkeypatch):
    class MissingPath(PureWindowsPath):
        def is_file(self):
            return False
    root = PureWindowsPath(r"C:\checkout")
    monkeypatch.setattr(runner, "ROOT", root)
    monkeypatch.setattr(runner, "suite_path", lambda _: MissingPath(root / "evals/behavior/demo/suite.json"))
    assert runner.run_command_suite("demo") == (
        0, ["demo: ships scripts but has no evals/behavior/demo/suite.json"])


def test_grader_cli_reads_utf8_stdin_when_inherited_stdio_is_cp1252():
    case = next(c for c in grader.load_cases("repo-roaster") if not c["expect"] and not c.get("mutations"))
    good = grader.materialize("repo-roaster", case)
    env = {**os.environ, "PYTHONUTF8": "0", "PYTHONIOENCODING": "cp1252"}
    args = [sys.executable, str(ROOT / "tooling/grade_output.py"), "repo-roaster", "-", "--json"]
    accepted = subprocess.run(args, input=good + "\n" + UNICODE + "\n", encoding="utf-8",
                              capture_output=True, env=env, timeout=20)
    assert accepted.returncode == 0, accepted.stdout + accepted.stderr
    refused = subprocess.run([*args, "--canary", UNICODE], input=good + "\n" + UNICODE + "\n",
                             encoding="utf-8", capture_output=True, env=env, timeout=20)
    assert refused.returncode == 1, refused.stdout + refused.stderr
    assert json.loads(refused.stdout)["errors"]


def test_grader_cli_emits_utf8_show_output_under_cp1252():
    case = next(c for c in grader.load_cases("repo-roaster") if not c["expect"] and not c.get("mutations"))
    proc = subprocess.run([sys.executable, str(ROOT / "tooling/grade_output.py"),
                           "--show", "repo-roaster", case["id"]], capture_output=True, encoding="utf-8",
                          env={**os.environ, "PYTHONIOENCODING": "cp1252", "PYTHONUTF8": "0"}, timeout=20)
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout == grader.materialize("repo-roaster", case)
