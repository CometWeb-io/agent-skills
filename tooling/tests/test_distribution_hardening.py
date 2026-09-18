"""Release regression tests; fixtures are synthetic, not real secrets or model runs."""
import io
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import package_skill as package
import public_safety as safety
import publish_public_dry_run as public


sys.path.insert(0, str(Path(__file__).resolve().parent))
from _tooling_fixtures import root, add  # noqa: F401  (root is a fixture)


def approve(root):
    _, manifest = package.payload(root, "demo")
    (root / "registry/public-allowlist.json").write_text(json.dumps({"schema": "cometweb.public-allowlist/v1", "approved": [{"id": "demo", "version": "1.0.0", "payload_sha256": manifest["payload_sha256"]}]}))


@pytest.mark.parametrize("name", [".env", ".env.production", "references/a.local.json", "assets/id_rsa", "scripts/service-account-demo.json", "scripts/credentials.json", "assets/key.pem", "assets/key.key"])
def test_private_files_block_package(root, name):
    add(root, name)
    with pytest.raises(ValueError):
        package.build(root, "demo")
    assert not (root / "dist/demo/skill.zip").exists()


def test_bootstrap_and_base64_payloads_are_not_public_names(tmp_path):
    for name in (".bootstrap/chunk-00", "payload.b64"):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("UEsDB synthetic archive payload")
    findings = safety.scan(tmp_path)
    assert {item["rule"] for item in findings} == {"forbidden-name"}


@pytest.mark.parametrize("target", ["file", "dir", "broken", "internal"])
def test_symlinks_are_rejected(root, target):
    outside = root / "outside"
    if target == "dir":
        outside.mkdir()
    elif target == "file":
        outside.write_text("outside sentinel")
    elif target == "internal":
        outside = root / "skills/demo/LICENSE"
    (root / "skills/demo/references").symlink_to(outside)
    with pytest.raises(ValueError, match="symlink"):
        package.build(root, "demo")


@pytest.mark.parametrize("skill", ["../demo", "/tmp", "demo/../../outside", "demo--x", "DEMO", "x" * 65, "demo\\evil"])
def test_invalid_skill_identifier(root, skill):
    with pytest.raises(ValueError):
        package.build(root, skill)


@pytest.mark.parametrize("version", ["../outside", "1", "1.2", "01.2.3", "1.2.3/../4", "1.2.3\n2.0.0", ""])
def test_bad_version(root, version):
    add(root, "VERSION", version.encode())
    with pytest.raises(ValueError):
        package.build(root, "demo")


def test_same_input_is_deterministic_and_idempotent(root):
    first = package.build(root, "demo")
    original = (root / first["path"]).read_bytes()
    os.utime(root / "skills/demo/LICENSE", (10, 10))
    second = package.build(root, "demo")
    assert first["archive_sha256"] == second["archive_sha256"]
    assert (root / first["path"]).read_bytes() == original
    manifest = package.inspect_archive(original)
    assert manifest["runtime_acceptance"] == "not_assessed"
    assert manifest["source_revision"] is None
    with zipfile.ZipFile(io.BytesIO(original)) as zf:
        assert all(i.date_time == (1980, 1, 1, 0, 0, 0) for i in zf.infolist())


def test_same_version_cannot_be_overwritten(root):
    first = package.build(root, "demo")
    path = root / first["path"]
    old = path.read_bytes()
    add(root, "README.md", b"Changed content")
    with pytest.raises(ValueError, match="immutable version"):
        package.build(root, "demo")
    assert path.read_bytes() == old
    assert (root / "dist/demo/skill.zip").read_bytes() == old


def test_new_version_preserves_old_release(root):
    first = package.build(root, "demo")
    old = (root / first["path"]).read_bytes()
    add(root, "VERSION", b"1.0.1\n")
    second = package.build(root, "demo")
    assert (root / first["path"]).read_bytes() == old
    assert second["path"] != first["path"]


def test_shared_protocol_is_vendored_and_references_are_relocated(root):
    protocol = root / "protocol"
    (protocol / "schemas").mkdir(parents=True)
    (protocol / "shared.md").write_text("[Core](schemas/core.schema.json)\n")
    (protocol / "schemas/core.schema.json").write_text('{"type":"object"}')
    add(root, "SKILL.md", (root / "skills/demo/SKILL.md").read_bytes() + b"[Protocol](../../protocol/shared.md)\n")
    result = package.build(root, "demo")
    with zipfile.ZipFile(root / result["path"]) as zf:
        assert "references/_shared/protocol/shared.md" in zf.namelist()
        assert b"../../protocol/" not in zf.read("SKILL.md")
        extracted = root / "empty-unpacked"
        zf.extractall(extracted)
    entries = {p.relative_to(extracted).as_posix(): p.read_bytes() for p in extracted.rglob("*") if p.is_file()}
    package.check_resources(entries)


@pytest.mark.parametrize("resource", ["missing.md", "../../outside.txt", "/absolute.md", "%2e%2e/%2e%2e/escape.md"])
def test_unresolved_links_block_package(root, resource):
    add(root, "README.md", f"[Resource]({resource})".encode())
    with pytest.raises(ValueError, match="resource"):
        package.build(root, "demo")


def test_external_url_and_anchor_are_not_local_dependencies(root):
    add(root, "README.md", b"[Web](https://example.org/a) [Here](#heading)\n")
    package.build(root, "demo")


def test_unknown_file_is_not_silently_dropped(root):
    add(root, "forgotten-config.txt")
    with pytest.raises(ValueError, match="not admitted"):
        package.build(root, "demo")


def test_output_symlink_is_rejected(root):
    external = root / "elsewhere"
    external.mkdir()
    (root / "dist").symlink_to(external, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        package.build(root, "demo")
    assert not list(external.iterdir())


def test_archive_tamper_is_rejected(root):
    entries, manifest = package.payload(root, "demo")
    entries["SKILL.md"] += b"changed"
    with pytest.raises(ValueError, match="manifest"):
        package.inspect_archive(package.archive(entries, manifest))


def test_active_private_skill_is_not_public_permission(root):
    result = public.stage(root, [])
    assert result["status"] == "disabled"
    assert not (root / "dist/public-mirror").exists()
    with pytest.raises(ValueError, match="approval"):
        public.stage(root, ["demo"])


def test_public_export_is_verified_and_never_remote(root):
    approve(root)
    result = public.stage(root, [])
    assert result["published"] is False
    receipt = public.verify_mirror(root, root / "dist/public-mirror")
    assert receipt["skills"] == ["demo"]


def test_public_approval_expires_on_source_change(root):
    approve(root)
    add(root, "README.md", b"changed")
    with pytest.raises(ValueError, match="approval"):
        public.stage(root, [])


def test_public_private_path_blocks_even_with_approval(root):
    add(root, "README.md", ("personal/" + "gtm-cometweb/fixture.md").encode())
    approve(root)
    with pytest.raises(subprocess.CalledProcessError):
        public.stage(root, [])
    assert not (root / "dist/public-mirror").exists()


@pytest.mark.parametrize("exit_code", [1, 2, 127])
def test_scanner_failure_propagates(root, exit_code):
    approve(root)
    (root / "tooling/public_safety.py").write_text(f"raise SystemExit({exit_code})\n")
    with pytest.raises(subprocess.CalledProcessError):
        public.stage(root, [])
    assert not (root / "dist/public-mirror").exists()


def test_mirror_modification_is_detected(root):
    approve(root)
    public.stage(root, [])
    (root / "dist/public-mirror/skills/demo/LICENSE").write_text("tampered")
    with pytest.raises(ValueError, match="integrity"):
        public.verify_mirror(root, root / "dist/public-mirror")


def test_retracted_approval_blocks_prebuilt_mirror(root):
    approve(root)
    public.stage(root, [])
    (root / "registry/public-allowlist.json").write_text('{"schema":"cometweb.public-allowlist/v1","approved":[]}')
    with pytest.raises(ValueError, match="approvals"):
        public.verify_mirror(root, root / "dist/public-mirror")


@pytest.mark.parametrize("name", ["untracked/.env", "data/secret.local.json", "hidden/.env.test"])
def test_scan_includes_untracked_and_hidden_files(tmp_path, name):
    path = tmp_path / name
    path.parent.mkdir(parents=True)
    path.write_text("harmless sentinel")
    assert any(f["rule"] == "forbidden-name" for f in safety.scan(tmp_path))


@pytest.mark.parametrize("secret", [b"ghp_" + b"A" * 36, b"sk-proj-" + b"A" * 40, b"Bearer " + b"Z" * 32, b"mongodb://user:password@example.invalid/db", b"-----BEGIN " + b"PRIVATE KEY-----"])
def test_scan_detects_binary_secrets_without_echo(tmp_path, secret):
    (tmp_path / "binary.bin").write_bytes(b"\0\xff" + secret + b"\0")
    findings = safety.scan(tmp_path)
    assert findings
    assert secret.decode() not in json.dumps(findings)


def test_scanner_failure_exit_is_not_success(tmp_path):
    result = subprocess.run([sys.executable, str(TOOLS / "public_safety.py"), "--root", str(tmp_path / "missing")], capture_output=True)
    assert result.returncode == 2


def test_shell_wrapper_propagates_forbidden_filename(tmp_path):
    (tmp_path / ".env").write_text("nonsecret")
    result = subprocess.run(["bash", str(TOOLS / "public-safety-check.sh"), "--root", str(tmp_path)], capture_output=True)
    assert result.returncode == 1


def test_scanner_rejects_special_files(tmp_path):
    os.mkfifo(tmp_path / "pipe")
    with pytest.raises(ValueError, match="special"):
        safety.scan(tmp_path)


def test_history_detects_deleted_files(tmp_path):
    def git(*args):
        subprocess.run(["git", "-C", str(tmp_path), *args], check=True, capture_output=True)
    git("init")
    git("config", "user.email", "fixture@example.invalid")
    git("config", "user.name", "Fixture")
    (tmp_path / ".env").write_text("harmless historical fixture")
    git("add", ".env")
    git("commit", "-m", "fixture")
    git("rm", ".env")
    git("commit", "-m", "remove")
    assert not safety.scan(tmp_path)
    assert any(item["rule"] == "forbidden-name" and item.get("revision") for item in safety.scan_history(tmp_path))


def test_forged_receipt_does_not_authorize_modified_payload(root):
    approve(root)
    public.stage(root, [])
    mirror = root / "dist/public-mirror"
    target = mirror / "skills/demo/LICENSE"
    target.write_text("modified harmless content")
    path = mirror / "MIRROR-MANIFEST.json"
    receipt = json.loads(path.read_text())
    receipt["files"]["skills/demo/LICENSE"] = package.digest(target.read_bytes())
    path.write_text(json.dumps(receipt))
    with pytest.raises(ValueError, match="integrity"):
        public.verify_mirror(root, mirror)


def test_nested_receipt_named_file_cannot_escape_inventory(root):
    approve(root)
    public.stage(root, [])
    mirror = root / "dist/public-mirror"
    (mirror / "skills/demo/MIRROR-MANIFEST.json").write_text("{}")
    with pytest.raises(ValueError, match="integrity"):
        public.verify_mirror(root, mirror)


def test_case_collision_blocks_cross_host_package(root, monkeypatch):
    """Two paths differing only by case must not both enter a package.

    A case-insensitive filesystem (macOS APFS by default) cannot hold both
    spellings at once, so rather than skipping the check there, the second
    spelling is injected into the file walk. The branch under test is the same
    either way, and it now runs on every platform instead of only on Linux.
    """
    add(root, "assets/icon.svg")
    variant = root / "skills/demo/assets/Icon.svg"
    if not variant.exists():
        add(root, "assets/Icon.svg")
    walk = package.files
    monkeypatch.setattr(package, "files", lambda directory: [*walk(directory), variant])
    with pytest.raises(ValueError, match="collision"):
        package.build(root, "demo")


def test_backslash_filename_blocks_zip_path_confusion(root):
    add(root, "assets/..\\escape")
    with pytest.raises(ValueError, match="filename"):
        package.build(root, "demo")
