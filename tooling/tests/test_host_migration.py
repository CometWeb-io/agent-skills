"""Native migration contracts using a stateful, file-writing CLI substitute.

No host executable, model, credentials or network is used. Native metadata and
payload bytes are deliberately separate, so frontmatter/list-only validation
cannot satisfy these controls.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tooling"))
import host_smoke  # noqa: E402


def write_source(root: Path, version: str, body: str) -> Path:
    root.mkdir()
    manifests = {
        "name": "cometweb-agent-skills", "version": version,
        "description": "Controlled migration source",
    }
    for rel in ["plugin.json", ".claude-plugin/plugin.json", ".cursor-plugin/plugin.json"]:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(manifests), encoding="utf-8")
    for rel in [".agents/plugins/marketplace.json", ".claude-plugin/marketplace.json"]:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"name": "cometweb-agent-skills", "owner": {"name": "Fixture"},
                                 "plugins": [{"name": "cometweb-agent-skills", "source": "."}]}))
    (root / "VERSION").write_text(version + "\n")
    (root / "LICENSE").write_text("Controlled fixture license\n")
    (root / "README.md").write_text("Controlled fixture\n")
    for name in ["alpha", "beta"]:
        skill = root / "skills" / name
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: Use for {name}. Do not use for unrelated work.\n---\n"
            + body + "\n", encoding="utf-8")
        (skill / "references").mkdir()
        (skill / "references" / "procedure.txt").write_text(body + " procedure\n")
    executable = root / "skills" / "alpha" / "helper.sh"
    executable.write_text("#!/bin/sh\nexit 0\n")
    if os.name == "posix":
        executable.chmod(0o755)
    return root


@pytest.fixture
def versions(tmp_path):
    return (write_source(tmp_path / "prior", "1.7.0", "Prior bounded action."),
            write_source(tmp_path / "current", "2.8.2", "Current changed bounded action."))


class FileNativeCLI:
    """Install real staged files; emit host-shaped JSON from independent state."""

    def __init__(self, host: str, work: Path, prior: Path, fault: str = ""):
        self.host, self.work, self.prior, self.fault = host, work, prior, fault
        self.market = None
        self.cache = None
        self.version = None
        self.install_count = self.remove_count = 0
        self.calls = []
        self.mutated = False

    def stage(self):
        assert self.market is not None
        return self.market / "plugin" if (self.market / "plugin" / "VERSION").exists() else self.market

    def target(self):
        return "cometweb-agent-skills@host-smoke" if self.host == "claude" else (
            "cometweb-agent-skills@cometweb-agent-skills")

    def rows(self):
        if self.version is None:
            return []
        if self.host == "claude":
            row = {"id": self.target(), "version": self.version, "enabled": True,
                   "scope": "user", "installPath": str(self.cache)}
        else:
            row = {"pluginId": self.target(), "name": "cometweb-agent-skills",
                   "marketplaceName": "cometweb-agent-skills", "version": self.version,
                   "installed": True, "enabled": True, "installedPath": str(self.cache),
                   "source": {"source": "local", "path": str(self.market)}}
        if self.host == "codex" and self.fault == "no_list_cache":
            row.pop("installedPath")
        if self.install_count == 2:
            if self.fault == "list_cache_disagreement":
                row["installedPath"] = str(self.work / "config/plugins/cache/unrelated")
                self.mutated = True
            elif self.fault == "source_disagreement":
                row["source"]["path"] = str(self.work / "another-market")
                self.mutated = True
            elif self.fault == "installed_false":
                row["installed"] = False
                self.mutated = True
            elif self.fault == "stale_version":
                row["version"] = "1.7.0"
                self.mutated = True
            elif self.fault == "disabled":
                row["enabled"] = False
                self.mutated = True
            elif self.fault == "duplicate_list":
                self.mutated = True
                return [row, dict(row)]
        return [row]

    def install(self, env):
        stage = self.stage()
        self.install_count += 1
        old_version = self.version
        self.version = (stage / "VERSION").read_text().strip()
        config = Path(env["CLAUDE_CONFIG_DIR" if self.host == "claude" else "CODEX_HOME"])
        market = "host-smoke" if self.host == "claude" else "cometweb-agent-skills"
        cache = config / "plugins" / "cache" / market / "cometweb-agent-skills" / self.version
        if cache.exists():
            shutil.rmtree(cache)
        shutil.copytree(stage, cache)
        self.cache = cache
        upgrade = self.install_count == 2
        if upgrade and self.fault in {"outside_cache", "cache_symlink"}:
            outside = self.work.parent / "untrusted-installed-cache"
            shutil.copytree(cache, outside)
            if self.fault == "cache_symlink":
                shutil.rmtree(cache)
                cache.symlink_to(outside, target_is_directory=True)
            else:
                self.cache = outside
            self.mutated = True
        if upgrade and self.fault == "body_changed":
            with (cache / "skills" / "alpha" / "SKILL.md").open("a") as f:
                f.write("Undeclared body replacement.\n")
            self.mutated = True
        if upgrade and self.fault == "extra_skill":
            p = cache / "skills" / "unlisted" / "SKILL.md"
            p.parent.mkdir()
            p.write_text("---\nname: unlisted\ndescription: Unlisted skill.\n---\nHidden body\n")
            self.mutated = True
        if upgrade and self.fault == "extra_payload":
            (cache / "unexpected.txt").write_text("An extra native payload file\n")
            self.mutated = True
        if upgrade and self.fault == "payload_symlink":
            p = cache / "skills" / "alpha" / "references" / "procedure.txt"
            p.unlink()
            p.symlink_to(self.prior / "skills" / "alpha" / "references" / "procedure.txt")
            self.mutated = True
        if self.install_count == 3 and self.fault == "rollback_mismatch":
            (cache / "skills" / "beta" / "references" / "procedure.txt").write_text("Wrong rollback body")
            self.mutated = True
        if self.host == "claude":
            return {"outcome": "ok", "updateOutcome": "updated", "oldVersion": old_version,
                    "newVersion": self.version, "version": self.version}
        installed = {"pluginId": self.target(), "version": self.version, "installedPath": str(self.cache)}
        if upgrade and self.fault == "add_id_disagreement":
            installed["pluginId"] = "other-plugin@cometweb-agent-skills"
            self.mutated = True
        elif upgrade and self.fault == "add_version_disagreement":
            installed["version"] = "1.7.0"
            self.mutated = True
        return installed

    def __call__(self, argv, env, cwd, *, timeout=None):
        config = Path(env["CLAUDE_CONFIG_DIR" if self.host == "claude" else "CODEX_HOME"])
        assert config.is_dir(), "Native CLI requires config directory before the first call"
        self.calls.append({"argv": list(argv), "env": dict(env), "cwd": str(cwd), "timeout": timeout})
        args = argv[1:]
        if args == ["--version"]:
            output = "test-native 9.0\n"
        elif args[:3] == ["plugin", "marketplace", "add"]:
            self.market = Path(args[3])
            output = "Local marketplace registered\n"
        elif args[:3] == ["plugin", "marketplace", "update"]:
            output = "Local marketplace refreshed\n"
        elif args[:2] in [["plugin", "add"], ["plugin", "install"], ["plugin", "update"]]:
            if self.install_count == 1 and self.fault == "command_failure":
                self.mutated = True
                return subprocess.CompletedProcess(argv, 7, "partial native output\n", "controlled failure\n")
            if self.install_count == 1 and self.fault == "timeout":
                self.mutated = True
                raise subprocess.TimeoutExpired(argv, timeout, output=b"partial native output\n",
                                                stderr=b"controlled timeout\n")
            output = json.dumps(self.install(env))
        elif args[:2] in [["plugin", "remove"], ["plugin", "uninstall"]]:
            self.remove_count += 1
            if self.remove_count == 2 and self.fault == "final_registered":
                self.mutated = True
            else:
                self.version = None
            output = "Removed target registration\n"
        elif args[:2] == ["plugin", "list"]:
            rows = self.rows()
            if self.install_count == 2 and self.fault == "malformed_list":
                output = "{broken native JSON"
                self.mutated = True
            elif self.install_count == 2 and self.fault == "wrong_shape":
                output = json.dumps({"installed": "invalid-row-list"} if self.host == "codex" else {"not": "a list"})
                self.mutated = True
            else:
                output = json.dumps(rows if self.host == "claude" else {"installed": rows, "available": []})
        else:
            raise AssertionError(f"Unexpected native command: {argv!r}")
        return subprocess.CompletedProcess(argv, 0, output, "")


def exercise(monkeypatch, tmp_path, versions, host, fault=""):
    prior, current = versions
    work, snapshots = tmp_path / "profile", tmp_path / "retained-caches"
    work.mkdir()
    fake = FileNativeCLI(host, work, prior, fault)
    monkeypatch.setattr(host_smoke, "run", fake)
    result = host_smoke.smoke_migration(host, "controlled-native-cli", work, prior, snapshots, root=current)
    return result, fake, work, snapshots


def phase_records(result):
    return result.facts["phases"]


def command_records(result):
    return result.facts["commands"]


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_same_profile_two_version_upgrade_rollback_and_retained_body(monkeypatch, tmp_path, versions, host):
    for name in ["ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN", "OPENAI_API_KEY", "CODEX_API_KEY"]:
        monkeypatch.setenv(name, "parent-auth-must-not-be-forwarded")
    result, fake, work, snapshots = exercise(monkeypatch, tmp_path, versions, host)
    assert result.status == "PASS", result.__dict__
    assert fake.install_count == 3 and fake.remove_count == 2
    assert fake.calls and all(call["timeout"] == 60 for call in fake.calls)
    assert len({(c["cwd"], c["env"]["HOME"], c["env"].get("CODEX_HOME"),
                 c["env"].get("CLAUDE_CONFIG_DIR")) for c in fake.calls}) == 1
    assert all(not any("KEY" in n or "TOKEN" in n for n in call["env"]) for call in fake.calls)
    assert len(command_records(result)) == len(fake.calls)
    phases = phase_records(result)
    assert [phases[n]["version"] for n in ["old", "new", "rollback"]] == ["1.7.0", "2.8.2", "1.7.0"]
    assert all(phases[n]["skills"] == 2 for n in ["old", "new", "rollback"])
    for phase, source in [("old", versions[0]), ("new", versions[1]), ("rollback", versions[0])]:
        snapshot = Path(phases[phase]["snapshot"])
        assert snapshot.is_relative_to(snapshots) and not snapshot.is_relative_to(work)
        for rel in ["skills/alpha/SKILL.md", "skills/beta/references/procedure.txt", "skills/alpha/helper.sh"]:
            assert (snapshot / rel).read_bytes() == (source / rel).read_bytes()
        if os.name == "posix":
            assert (snapshot / "skills/alpha/helper.sh").stat().st_mode & 0o111
        expected = {
            p.relative_to(source).as_posix(): (p.read_bytes(), p.stat().st_mode & 0o777)
            for p in source.rglob("*") if p.is_file()
            and not (host == "claude" and p.relative_to(source).as_posix()
                     == ".claude-plugin/marketplace.json")
        }
        retained = {p.relative_to(snapshot).as_posix(): (p.read_bytes(), p.stat().st_mode & 0o777)
                    for p in snapshot.rglob("*") if p.is_file()}
        assert retained == expected
    shutil.rmtree(work)
    assert all(Path(phases[n]["snapshot"]).is_dir() for n in ["old", "new", "rollback"])


@pytest.mark.parametrize("host", ["claude", "codex"])
@pytest.mark.parametrize("fault", [
    "stale_version", "body_changed", "extra_skill", "extra_payload", "outside_cache",
    "cache_symlink", "payload_symlink", "malformed_list", "wrong_shape", "disabled",
    "duplicate_list", "rollback_mismatch", "final_registered", "command_failure", "timeout",
])
def test_real_cache_or_native_metadata_defect_refuses_migration(monkeypatch, tmp_path, versions, host, fault):
    result, fake, _, snapshots = exercise(monkeypatch, tmp_path, versions, host, fault)
    assert fake.mutated, "Control did not reach its intended migration defect"
    assert result.status == "FAIL", (fault, result.__dict__)
    assert any(not check["ok"] for check in result.checks)
    assert command_records(result), "Failed native command evidence must remain in result"
    if fault in {"command_failure", "timeout"}:
        records = command_records(result)
        raw = json.dumps(records)
        assert "partial native output" in raw and "controlled " in raw
        if fault == "command_failure":
            assert records[-1].get("exit", records[-1].get("exit_code")) == 7
        else:
            assert records[-1].get("timeout") is True
        assert records[-1]["argv"] == fake.calls[-1]["argv"]
        assert len(records) == len(fake.calls)
    if fault in {"rollback_mismatch", "final_registered"}:
        assert snapshots.is_dir(), "Prior successful phase bytes must survive a late failure"
        assert list(snapshots.rglob("SKILL.md"))


def test_payload_hashes_bind_body_and_executable_mode(tmp_path, versions):
    _, current = versions
    before = host_smoke.payload_hashes(current)
    rel = "skills/alpha/SKILL.md"
    key = str(Path(rel))
    assert before[key]["sha256"] == hashlib.sha256((current / rel).read_bytes()).hexdigest()
    with (current / rel).open("a") as f:
        f.write("Changed body only\n")
    assert host_smoke.payload_hashes(current)[key]["sha256"] != before[key]["sha256"]
    if os.name == "posix":
        executable = "skills/alpha/helper.sh"
        assert before[executable]["mode"] == 0o755
        (current / executable).chmod(0o644)
        assert host_smoke.payload_hashes(current)[executable]["mode"] != before[executable]["mode"]


@pytest.mark.parametrize("kind", ["file-link", "directory-link", "root-link", "fifo"])
def test_payload_hashes_refuse_following_links_or_reading_special_files(tmp_path, monkeypatch, kind):
    root = tmp_path / "source"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "fake-key.txt").write_text("controlled nonsecret\n")
    if kind == "root-link":
        root.rmdir()
        root.symlink_to(outside, target_is_directory=True)
    elif kind == "file-link":
        (root / "link.txt").symlink_to(outside / "fake-key.txt")
    elif kind == "directory-link":
        (root / "nested").symlink_to(outside, target_is_directory=True)
    else:
        if not hasattr(os, "mkfifo"):
            pytest.skip("FIFO unavailable on this platform")
        os.mkfifo(root / "special")
    original_read = Path.read_bytes

    def guarded_read(path):
        # A broken special-file guard must fail promptly rather than block CI on the FIFO.
        if kind == "fifo" and path == root / "special":
            pytest.fail("Special-file bytes must never be opened")
        return original_read(path)

    monkeypatch.setattr(Path, "read_bytes", guarded_read)
    with pytest.raises((ValueError, OSError)):
        host_smoke.payload_hashes(root)


@pytest.mark.parametrize("args", [
    ["--migration-from", "prior", "--host", "codex"],
    ["--migration-from", "prior", "--host", "codex", "--require", "claude", "--json", "out.json"],
    ["--migration-from", "prior", "--host", "cursor", "--json", "out.json"],
])
def test_migration_cli_rejects_missing_persistent_report_or_unsupported_host(monkeypatch, args):
    def no_native(*unused, **kwargs):
        raise AssertionError("Invalid migration options must fail before starting commands")
    monkeypatch.setattr(host_smoke, "run", no_native)
    with pytest.raises(SystemExit) as error:
        host_smoke.main(args)
    assert error.value.code == 2


@pytest.mark.parametrize("fault", [
    "list_cache_disagreement", "add_id_disagreement", "add_version_disagreement",
    "source_disagreement", "installed_false",
])
def test_codex_add_and_list_must_bind_the_same_installation(monkeypatch, tmp_path, versions, fault):
    result, fake, _, _ = exercise(monkeypatch, tmp_path, versions, "codex", fault)
    assert fake.mutated
    assert result.status == "FAIL", result.__dict__
    assert any(not check["ok"] for check in result.checks)
    assert "new" in result.facts["phases"], "Keep cache bytes even when metadata binding fails"
    assert Path(result.facts["phases"]["new"]["snapshot"]).is_dir()


def test_codex_list_may_omit_cache_path_without_inventing_a_reported_path(monkeypatch, tmp_path, versions):
    result, fake, _, _ = exercise(monkeypatch, tmp_path, versions, "codex", "no_list_cache")
    assert result.status == "PASS", result.__dict__
    assert fake.install_count == 3
    for phase in ["old", "new", "rollback"]:
        entry = result.facts["phases"][phase]
        assert entry["native_list_cache_path_reported"] is False
        assert "installedPath" not in entry["row"] and "installPath" not in entry["row"]
        assert Path(entry["snapshot"]).is_dir()


@pytest.mark.parametrize("host", ["claude", "codex"])
def test_owned_profile_alias_is_canonicalized_without_forwarding_auth(monkeypatch, tmp_path, versions, host):
    prior, current = versions
    profile = tmp_path / "real-owned-profile"
    profile.mkdir()
    alias = tmp_path / "profile-alias"
    try:
        alias.symlink_to(profile, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"Directory symlink unavailable: {exc}")
    fake = FileNativeCLI(host, profile.resolve(), prior)
    monkeypatch.setattr(host_smoke, "run", fake)
    monkeypatch.setenv("OPENAI_API_KEY", "parent-auth-not-forwarded")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "parent-auth-not-forwarded")
    snapshots = tmp_path / "retained"
    result = host_smoke.smoke_migration(host, "controlled-native-cli", alias, prior, snapshots, root=current)
    assert result.status == "PASS", result.__dict__
    assert fake.install_count == 3
    for call in fake.calls:
        assert Path(call["cwd"]).is_relative_to(profile.resolve())
        assert Path(call["env"]["HOME"]).is_relative_to(profile.resolve())
        assert not any("KEY" in name or "TOKEN" in name for name in call["env"])
    assert all(Path(p["cache"]).is_relative_to(profile.resolve())
               for p in result.facts["phases"].values())
