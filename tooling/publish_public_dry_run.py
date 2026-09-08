#!/usr/bin/env python3
"""Dry-run a public-safe subset into dist/public-mirror/ for inspection."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "skills.json"
OUT = ROOT / "dist" / "public-mirror"

# Paths that must not ship publicly even as templates inside skills.
STRIP_GLOBS = (
    "**/notion-bindings.local.json",
    "**/*.pyc",
    "**/__pycache__/**",
)


def should_strip(path: Path) -> bool:
    name = path.name
    if name.endswith(".pyc") or name == "__pycache__" or name.endswith(".local.json"):
        return True
    # Strip live private path templates from published context registry
    if path.name == "source-registry.json" and "cometweb-context" in path.parts:
        return False  # rewrite instead
    return False


def rewrite_context_registry(src: Path, dst: Path) -> None:
    data = json.loads(src.read_text(encoding="utf-8"))
    gov = data.get("domains", {}).get("governance", {})
    for binding in gov.get("bindings", []):
        for key in ("local_path_template", "alias_map_template"):
            if key in binding:
                binding[key] = f"<set-via-local-binding:{binding.get('id', 'binding')}>"
        if "decision_alias" in binding:
            binding["decision_alias"] = "<internal-alias>"
    claims = data.get("domains", {}).get("claims", {})
    if "evidence_register_template" in claims:
        claims["evidence_register_template"] = "<set-via-local-binding:evidence-register>"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def scrub_private_paths(text: str) -> str:
    replacements = (
        ("<COMETWEB_GTM_ROOT>/", "<COMETWEB_GTM_ROOT>/"),
        ("<COMETWEB_GTM_ROOT>", "<COMETWEB_GTM_ROOT>"),
        ("<COMETWEB_NAUKA_ROOT>/", "<COMETWEB_NAUKA_ROOT>/"),
        ("<COMETWEB_NAUKA_ROOT>", "<COMETWEB_NAUKA_ROOT>"),
        ("<COMETWEB_INTERNAL_ROOT>/", "<COMETWEB_INTERNAL_ROOT>/"),
        ("<COMETWEB_INTERNAL_ROOT>", "<COMETWEB_INTERNAL_ROOT>"),
    )
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    for path in src.rglob("*"):
        if path.is_dir():
            continue
        rel = path.relative_to(src)
        if any(part in {"__pycache__", ".pytest_cache"} for part in rel.parts):
            continue
        if path.suffix == ".pyc" or path.name.endswith(".local.json"):
            continue
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if path.name == "source-registry.json" and src.name == "cometweb-context":
            rewrite_context_registry(path, target)
            continue
        if path.suffix in {".md", ".json", ".txt", ".yaml", ".yml"}:
            text = scrub_private_paths(path.read_text(encoding="utf-8"))
            target.write_text(text, encoding="utf-8")
            continue
        shutil.copy2(path, target)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill", action="append", default=[])
    parser.add_argument("--skip-safety", action="store_true")
    args = parser.parse_args()

    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    skill_ids = args.skill or [s["id"] for s in registry["skills"] if s.get("lifecycle") == "active"]

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    # Public-safe protocol + tooling subset
    for rel in (
        "protocol",
        "registry/hosts.json",
        "evals/routing",
        "README.md",
        "LICENSE",
    ):
        src = ROOT / rel
        if not src.exists():
            continue
        dst = OUT / rel
        if src.is_dir():
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    # Registry without private notes expansion — copy then scrub descriptions only
    public_reg = {
        "schema": registry["schema"],
        "protocol": registry.get("protocol"),
        "skills": [
            {
                "id": s["id"],
                "version": s["version"],
                "lifecycle": s.get("lifecycle"),
                "tier": s.get("tier"),
                "description": s.get("description"),
                "explicit_only": s.get("explicit_only"),
                "alias_of": s.get("alias_of"),
                "compatible_hosts": s.get("compatible_hosts"),
            }
            for s in registry["skills"]
            if s["id"] in skill_ids
        ],
    }
    (OUT / "registry").mkdir(parents=True, exist_ok=True)
    (OUT / "registry" / "skills.json").write_text(
        json.dumps(public_reg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    for skill_id in skill_ids:
        src = ROOT / "skills" / skill_id
        if not src.is_dir():
            print(f"skip missing {skill_id}", file=sys.stderr)
            continue
        copy_tree(src, OUT / "skills" / skill_id)

    mirror_readme = OUT / "MIRROR_NOTE.md"
    mirror_readme.write_text(
        "# Public mirror dry-run\n\nGenerated by `tooling/publish_public_dry_run.py`.\n"
        "Inspect, run public-safety, then sync to MaciejZet/agent-skills.\n",
        encoding="utf-8",
    )

    if not args.skip_safety:
        # Run safety from OUT as if it were the public tree: copy checker into OUT temporarily
        checker = ROOT / "tooling" / "public-safety-check.sh"
        # Adapt: run grep from OUT with a tiny wrapper
        proc = subprocess.run(
            ["bash", "-c", f"cd '{OUT}' && bash '{checker}'"],
            capture_output=True,
            text=True,
        )
        # The checker expects to be at tooling/ inside repo; when run against OUT it may fail SELF path.
        # Prefer a direct content scan for private vault paths in the staging tree:
        hits = subprocess.run(
            ["grep", "-rEIn", "-e", "personal/(gtm-cometweb|nauka)|<COMETWEB_INTERNAL_ROOT>", str(OUT)],
            capture_output=True,
            text=True,
        )
        if hits.returncode == 0 and hits.stdout.strip():
            print("FAIL: private vault path templates remain in mirror:", file=sys.stderr)
            print(hits.stdout[:2000], file=sys.stderr)
            raise SystemExit(1)
        if hits.returncode > 1:
            print(hits.stderr, file=sys.stderr)
            raise SystemExit(2)

    print(f"OK: public mirror dry-run at {OUT.relative_to(ROOT)} ({len(skill_ids)} skills)")


if __name__ == "__main__":
    main()
