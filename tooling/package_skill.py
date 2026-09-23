#!/usr/bin/env python3
"""Build self-contained, scanned, deterministic and immutable skill packages."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

import yaml
from public_safety import MAX_FILE_BYTES, check_blob, files
from markdown_resources import destinations

ROOT = Path(__file__).resolve().parents[1]
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
VERSION = re.compile(r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)(?:-[0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*)?(?:\+[0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*)?\Z")
LINK = re.compile(r"(?<=\]\()([^\s)]+)(?=\))")
MANIFEST = "PACKAGE-MANIFEST.json"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(data: object) -> bytes:
    return (json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def identifier(value: str) -> str:
    if len(value) > 64 or not SLUG.fullmatch(value):
        raise ValueError("invalid skill identifier")
    return value


def safe_path(root: Path, relative: str) -> Path:
    path = root / relative
    if Path(relative).is_absolute() or ".." in PurePosixPath(relative).parts:
        raise ValueError("path must stay inside its root")
    for candidate in (root, *[root.joinpath(*PurePosixPath(relative).parts[:i]) for i in range(1, len(PurePosixPath(relative).parts) + 1)]):
        if candidate.is_symlink():
            raise ValueError("symlink in path")
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("path escapes root")
    return path


def validate_frontmatter(blob: bytes, skill: str) -> None:
    match = re.match(r"\A---\s*\n(.*?)\n---(?:\n|\Z)", blob.decode("utf-8"), re.S)
    if not match:
        raise ValueError("SKILL.md is missing YAML frontmatter")
    from compatibility import UniqueLoader
    # UniqueLoader subclasses yaml.SafeLoader; duplicate keys are rejected.
    data = yaml.load(match.group(1), Loader=UniqueLoader)  # nosec B506
    if not isinstance(data, dict) or data.get("name") != skill:
        raise ValueError("frontmatter name must match the skill directory")
    desc = data.get("description")
    if not isinstance(desc, str) or not 1 <= len(desc.strip()) <= 1024:
        raise ValueError("description must contain 1-1024 characters")


def payload(root: Path, skill: str) -> tuple[dict[str, bytes], dict]:
    identifier(skill)
    policy = json.loads((root / "registry/package-policy.json").read_text())
    if policy.get("schema") != "cometweb.package-policy/v1":
        raise ValueError("unknown package policy")
    source = safe_path(root, "skills/" + skill)
    entries = {}
    for path in files(source):
        rel = path.relative_to(source).as_posix()
        if "\\" in rel or any(ord(c) < 32 for c in rel) or path.stat().st_size > MAX_FILE_BYTES:
            raise ValueError("unsafe filename or package input exceeds scan budget")
        if rel.casefold() in {n.casefold() for n in entries}:
            raise ValueError("case-insensitive path collision")
        data = path.read_bytes()
        if check_blob(rel, data, public=False):
            raise ValueError(f"unsafe package input: {rel}; matched values redacted")
        if not (rel in policy["root_files"] or PurePosixPath(rel).parts[0] in policy["directories"]):
            raise ValueError(f"file not admitted by package-policy.json: {rel}")
        entries[rel] = data
    for name in policy["required_files"]:
        if not entries.get(name, b"").strip():
            raise ValueError(f"missing required file: {name}")
    version = entries["VERSION"].decode().strip()
    if not VERSION.fullmatch(version):
        raise ValueError("invalid VERSION")
    validate_frontmatter(entries["SKILL.md"], skill)
    # Only explicitly admitted repository roots may be bundled. Never chase arbitrary links.
    for shared in policy["shared_roots"]:
        identifier(shared)
        marker = f"../../{shared}/"
        if not any(marker.encode() in value for key, value in entries.items() if key.endswith(".md")):
            continue
        for path in files(safe_path(root, shared)):
            rel = "references/_shared/" + path.relative_to(root).as_posix()
            if "\\" in rel or any(ord(c) < 32 for c in rel) or path.stat().st_size > MAX_FILE_BYTES:
                raise ValueError("unsafe shared filename or resource exceeds scan budget")
            data = path.read_bytes()
            if check_blob(rel, data, public=False):
                raise ValueError(f"unsafe shared resource: {rel}")
            if rel.casefold() in {n.casefold() for n in entries}:
                raise ValueError(f"vendored resource collision: {rel}")
            entries[rel] = data
        # Rewrite the documented repo-relative resource prefix, including inline code paths.
        for name, data in list(entries.items()):
            if name.endswith(".md"):
                prefix = os.path.relpath("references/_shared/" + shared, str(PurePosixPath(name).parent)).replace(os.sep, "/")
                entries[name] = data.replace(marker.encode(), (prefix + "/").encode())
    check_resources(entries)
    manifest = {
        "schema": "cometweb.package/v1", "skill": skill, "version": version,
        "policy_sha256": digest(canonical(policy)),
        "files": {name: digest(data) for name, data in sorted(entries.items())},
        "runtime_acceptance": "not_assessed",
    }
    manifest["payload_sha256"] = digest(canonical({"files": manifest["files"], "policy_sha256": manifest["policy_sha256"]}))
    return entries, manifest


def check_resources(entries: dict[str, bytes]) -> None:
    """Validate Markdown local file links and relative JSON Schema $ref targets after relocation."""
    for name, blob in entries.items():
        targets = []
        if name.endswith(".md"):
            targets = destinations(blob.decode("utf-8"))
        elif name.endswith(".schema.json"):
            def refs(value):
                if isinstance(value, dict):
                    if isinstance(value.get("$ref"), str):
                        yield value["$ref"]
                    for child in value.values():
                        yield from refs(child)
                elif isinstance(value, list):
                    for child in value:
                        yield from refs(child)
            targets = list(refs(json.loads(blob)))
        for target in targets:
            url = urlsplit(target.strip("<>"))
            if url.scheme or url.netloc or not url.path:
                continue
            value = unquote(url.path)
            joined = os.path.normpath(str(PurePosixPath(name).parent / value)).replace(os.sep, "/")
            if joined.startswith(("../", "/")) or (joined not in entries and not any(k.startswith(joined.rstrip("/") + "/") for k in entries)):
                raise ValueError(f"unresolved local resource: {name} -> {value}")


def archive(entries: dict[str, bytes], manifest: dict) -> bytes:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_STORED) as zf:
        for name, blob in sorted({**entries, MANIFEST: canonical(manifest)}.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (0o100755 if blob.startswith(b"#!") else 0o100644) << 16
            zf.writestr(info, blob)
    return stream.getvalue()


def inspect_archive(blob: bytes) -> dict:
    """Validate payload identity as well as hashes; metadata cannot certify itself."""
    import unicodedata

    def unique(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate manifest key")
            result[key] = value
        return result

    def invalid_number(_):
        raise ValueError("non-finite manifest value")

    if len(blob) > 80 * 1024 * 1024:
        raise ValueError("archive exceeds admission budget")
    try:
        with zipfile.ZipFile(io.BytesIO(blob)) as zf:
            infos = zf.infolist()
            names = [i.filename for i in infos]
            folded = [unicodedata.normalize("NFC", n).casefold() for n in names]
            if not names or len(names) > 8192 or len(folded) != len(set(folded)):
                raise ValueError("empty, oversized or duplicate ZIP inventory")
            for item in infos:
                name = item.filename
                if (PurePosixPath(name).is_absolute() or "\\" in name or ":" in name
                        or any(p in {"", ".", ".."} for p in name.split("/"))
                        or any(ord(c) < 32 for c in name)):
                    raise ValueError("unsafe or nonportable ZIP path")
                kind = (item.external_attr >> 16) & 0o170000
                if kind not in {0, 0o100000} or item.is_dir() or item.flag_bits & 1:
                    raise ValueError("special, encrypted or non-regular ZIP entry")
                if item.file_size > MAX_FILE_BYTES:
                    raise ValueError("ZIP entry exceeds verification budget")
            if sum(i.file_size for i in infos) > 64 * 1024 * 1024:
                raise ValueError("ZIP exceeds verification budget")
            raw = zf.read(MANIFEST)
            if len(raw) > 4 * 1024 * 1024:
                raise ValueError("package manifest exceeds budget")
            manifest = json.loads(raw, object_pairs_hook=unique, parse_constant=invalid_number)
            required = {"schema", "skill", "version", "policy_sha256", "files", "runtime_acceptance", "payload_sha256"}
            optional = {"source_revision", "source_tree"}
            if not isinstance(manifest, dict) or not required <= manifest.keys() or not manifest.keys() <= required | optional:
                raise ValueError("invalid package manifest fields")
            if manifest["schema"] != "cometweb.package/v1" or manifest["runtime_acceptance"] != "not_assessed":
                raise ValueError("package metadata cannot assert runtime acceptance")
            if not isinstance(manifest["skill"], str):
                raise ValueError("invalid package identity")
            identifier(manifest["skill"])
            if not isinstance(manifest["version"], str) or not VERSION.fullmatch(manifest["version"]):
                raise ValueError("invalid manifest version")
            for field in ("policy_sha256", "payload_sha256"):
                if not isinstance(manifest[field], str) or not re.fullmatch(r"[0-9a-f]{64}", manifest[field]):
                    raise ValueError("invalid manifest fingerprint")
            present = optional & manifest.keys()
            if present:
                if present != optional:
                    raise ValueError("incomplete source provenance")
                revision, state = manifest["source_revision"], manifest["source_tree"]
                if state == "unavailable":
                    if revision is not None:
                        raise ValueError("unavailable source cannot have a revision")
                elif (state not in {"clean", "dirty"} or not isinstance(revision, str)
                      or not re.fullmatch(r"[0-9a-f]{40}", revision)):
                    raise ValueError("inconsistent source provenance")
            entries = {n: zf.read(n) for n in names if n != MANIFEST}
            for name, data in entries.items():
                if check_blob(name, data, public=False):
                    raise ValueError("unsafe package content; matched values redacted")
            for name in ("SKILL.md", "VERSION", "LICENSE"):
                if not entries.get(name, b"").strip():
                    raise ValueError("required package identity file missing")
            validate_frontmatter(entries["SKILL.md"], manifest["skill"])
            if entries["VERSION"].decode("utf-8").strip() != manifest["version"]:
                raise ValueError("manifest version disagrees with VERSION")
            actual = {n: digest(data) for n, data in entries.items()}
            if manifest["files"] != actual:
                raise ValueError("package manifest mismatch")
            expected = digest(canonical({"files": actual, "policy_sha256": manifest["policy_sha256"]}))
            if manifest["payload_sha256"] != expected:
                raise ValueError("package payload fingerprint mismatch")
            check_resources(entries)
            return manifest
    except (KeyError, TypeError, UnicodeError, json.JSONDecodeError, zipfile.BadZipFile,
            yaml.YAMLError, RuntimeError, RecursionError) as exc:
        raise ValueError("invalid package archive") from exc


def write_atomic(path: Path, blob: bytes, *, immutable: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise ValueError("output symlink rejected")
    fd, temporary = tempfile.mkstemp(prefix=".package-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(blob)
            handle.flush()
            os.fsync(handle.fileno())
        if immutable:
            os.link(temporary, path)  # exclusive creation; another writer cannot be overwritten
        else:
            os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def build(root: Path, skill: str) -> dict:
    entries, manifest = payload(root, skill)
    out = safe_path(root, f"dist/{skill}/{manifest['version']}/skill.zip")
    if out.exists():
        old = inspect_archive(out.read_bytes())
        if old["payload_sha256"] != manifest["payload_sha256"]:
            raise ValueError("immutable version conflict: bump VERSION; existing release is unchanged")
    else:
        try:
            from core.git import read_git

            revision = read_git(root, "rev-parse", "HEAD").stdout.decode().strip()
            dirty = bool(read_git(root, "status", "--porcelain").stdout.strip())
            manifest.update(source_revision=revision, source_tree="dirty" if dirty else "clean")
        except (OSError, subprocess.SubprocessError):
            manifest.update(source_revision=None, source_tree="unavailable")
        data = archive(entries, manifest)
        inspect_archive(data)
        try:
            write_atomic(out, data, immutable=True)
        except FileExistsError as exc:
            if inspect_archive(out.read_bytes())["payload_sha256"] != manifest["payload_sha256"]:
                raise ValueError("concurrent immutable version conflict") from exc
    data = out.read_bytes()
    latest = safe_path(root, f"dist/{skill}/skill.zip")
    write_atomic(latest, data, immutable=False)
    write_atomic(safe_path(root, f"dist/{skill}/{manifest['version']}/skill.zip.sha256"), (digest(data) + "  skill.zip\n").encode(), immutable=False)
    return {"status": "packaged", "skill": skill, "version": manifest["version"], "payload_sha256": manifest["payload_sha256"], "archive_sha256": digest(data), "path": out.relative_to(root).as_posix(), "runtime_acceptance": "not_assessed"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--versioned", action="store_true", help="Compatibility flag; all releases are now versioned")
    args = parser.parse_args()
    try:
        print(json.dumps(build(args.root, args.skill), indent=2))
        return 0
    except (OSError, ValueError, KeyError, zipfile.BadZipFile, yaml.YAMLError) as exc:
        print(f"Packaging blocked: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
