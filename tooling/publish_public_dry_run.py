#!/usr/bin/env python3
"""Stage only explicitly approved skill/version/payload tuples; never publish remotely."""
from __future__ import annotations
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from package_skill import ROOT, MANIFEST, canonical, digest, identifier, payload, safe_path


def approvals(root: Path) -> tuple[list[dict], str]:
    data = json.loads((root / "registry/public-allowlist.json").read_text())
    if data.get("schema") != "cometweb.public-allowlist/v1" or not isinstance(data.get("approved"), list):
        raise ValueError("invalid public allowlist")
    seen = set()
    for item in data["approved"]:
        identifier(item["id"])
        if item["id"] in seen or not re.fullmatch(r"[a-f0-9]{64}", str(item.get("payload_sha256", ""))) or not isinstance(item.get("version"), str):
            raise ValueError("duplicate or malformed approval")
        seen.add(item["id"])
    return data["approved"], digest(canonical(data))


def mirror_entries(root: Path, ids: list[str], allowed: dict) -> dict[str, bytes]:
    registry = json.loads((root / "registry/skills.json").read_text())
    active = {s["id"]: s for s in registry["skills"] if s.get("lifecycle") == "active"}
    output = {}
    for sid in ids:
        if sid not in active or sid not in allowed:
            raise ValueError("each active skill needs approval")
        entries, manifest = payload(root, sid)
        if manifest["version"] != allowed[sid].get("version") or manifest["payload_sha256"] != allowed[sid]["payload_sha256"]:
            raise ValueError("source has changed since publication approval")
        for name, data in {**entries, MANIFEST: canonical(manifest)}.items():
            output[f"skills/{sid}/{name}"] = data
    output["registry/skills.json"] = canonical({"schema": registry["schema"], "skills": [{k: active[sid].get(k) for k in ("id", "version", "description", "alias_of", "compatible_hosts")} for sid in ids]})
    output["README.md"] = b"# CometWeb Agent Skills\n\nGenerated public subset. Each skill contains its own license and package manifest. Structural validation is not runtime acceptance.\n"
    return output


def verify_mirror(root: Path, mirror: Path) -> dict:
    """Recompute every expected byte from approved source; never trust a mutable receipt alone."""
    from public_safety import files, scan
    receipt = json.loads((mirror / "MIRROR-MANIFEST.json").read_text())
    approved, policy_hash = approvals(root)
    if receipt.get("schema") != "cometweb.public-mirror/v1" or receipt.get("allowlist_sha256") != policy_hash or not approved:
        raise ValueError("mirror does not match current publication approvals")
    ids = receipt.get("skills")
    if not isinstance(ids, list) or not ids or len(ids) != len(set(ids)):
        raise ValueError("invalid mirror skill inventory")
    expected = {n: digest(data) for n, data in mirror_entries(root, ids, {a["id"]: a for a in approved}).items()}
    actual = {p.relative_to(mirror).as_posix(): digest(p.read_bytes()) for p in files(mirror) if p.relative_to(mirror).as_posix() != "MIRROR-MANIFEST.json"}
    if actual != expected or actual != receipt.get("files") or scan(mirror):
        raise ValueError("mirror integrity or public-safety verification failed")
    return receipt


def stage(root: Path, selected: list[str]) -> dict:
    approved, policy_hash = approvals(root)
    allowed = {a["id"]: a for a in approved}
    ids = selected or sorted(allowed)
    if len(ids) != len(set(ids)) or any(sid not in allowed for sid in ids):
        raise ValueError("each selected skill requires an explicit publication approval")
    if not ids:
        return {"status": "disabled", "reason": "No approved public payloads; no export produced", "skills": []}
    expected_entries = mirror_entries(root, ids, allowed)
    out = safe_path(root, "dist/public-mirror")
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".public-stage-", dir=out.parent) as temporary:
        staging = Path(temporary) / "tree"
        staging.mkdir()
        for name, data in expected_entries.items():
            target = safe_path(staging, name)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        from public_safety import files
        receipt = {"schema": "cometweb.public-mirror/v1", "allowlist_sha256": policy_hash, "skills": ids,
                   "files": {p.relative_to(staging).as_posix(): digest(p.read_bytes()) for p in files(staging)}}
        (staging / "MIRROR-MANIFEST.json").write_bytes(canonical(receipt))
        # No ignored return code, cwd trick, alternate grep or safety bypass.
        subprocess.run([sys.executable, str(root / "tooling/public_safety.py"), "--root", str(staging)], check=True, capture_output=True, timeout=120)
        verify_mirror(root, staging)
        lock = safe_path(root, "dist/.public-export.lock")
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        backup = Path(temporary) / "previous"
        try:
            if out.exists():
                out.rename(backup)
            try:
                staging.rename(out)
            except OSError:
                if backup.exists():
                    backup.rename(out)
                raise
        finally:
            os.close(fd)
            lock.unlink()
    return {"status": "staged", "skills": ids, "path": "dist/public-mirror", "published": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--skill", action="append", default=[])
    args = parser.parse_args()
    try:
        print(json.dumps(stage(args.root, args.skill), indent=2))
        return 0
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        print(f"Public export blocked ({type(exc).__name__}); no safety bypass is supported.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
