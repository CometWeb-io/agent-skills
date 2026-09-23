"""CLI entrypoint and immutable result output."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Iterable, List

from .compare import compare
from .evaluate import evaluate
from .manifest import ManifestError, _load


def write_output(path: Path, text: str, inputs: Iterable[Path] = ()) -> None:
    """Create a result without overwriting source manifests or existing different results."""
    if path.resolve() in {p.resolve() for p in inputs}:
        raise ManifestError("output must not replace an input manifest")
    if path.exists() and path.is_symlink():
        raise ManifestError("output itself must not be a symlink")
    blob = (text + "\n").encode("utf-8")
    if path.exists():
        if path.is_file() and path.stat().st_size == len(blob) and path.read_bytes() == blob:
            return
        raise ManifestError("output already exists with different contents")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".readiness-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(blob)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, path)
    except OSError as exc:
        raise ManifestError("could not create immutable output") from exc
    finally:
        Path(temporary).unlink(missing_ok=True)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate a release-readiness v2 manifest")
    parser.add_argument("--input", required=True, type=Path, help="Path to readiness manifest JSON")
    parser.add_argument("--previous", type=Path, help="Optional previous manifest for delta analysis")
    parser.add_argument("--expected-contract-hash", help="Independent SHA-256 of frozen assessment requirements")
    parser.add_argument("--output", type=Path, help="Optional path for result JSON")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    parser.add_argument("--validate-only", action="store_true", help="Validate/evaluate but emit only validation summary")
    parser.add_argument("--ci-policy", choices=("none", "strict", "controlled"), default="none",
                        help="strict: only GO exits 0; controlled: GO and GO_WITH_CONTROLS exit 0")
    args = parser.parse_args(argv)

    try:
        manifest = _load(args.input)
        previous = _load(args.previous) if args.previous else None
        pinned = args.expected_contract_hash
        if previous is not None and pinned is None:
            pinned = evaluate(previous)["contract_hash"]
        result = evaluate(manifest, expected_contract_hash=pinned)
        if previous is not None:
            result["delta"] = compare(manifest, previous, expected_contract_hash=pinned)
        if args.validate_only:
            result = {
                "valid": True,
                "verdict": result["verdict"],
                "snapshot_hash": result["snapshot_hash"],
                "contract_hash": result["contract_hash"],
                "contract_mismatch": result["contract_mismatch"],
                "missing_required_gates": result["missing_required_gates"],
                "scope_gaps": result["scope_gaps"],
            }
    except ManifestError as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2

    text = json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True, allow_nan=False)
    try:
        if args.output:
            write_output(args.output, text, [args.input] + ([args.previous] if args.previous else []))
    except (ManifestError, OSError):
        print(json.dumps({"error": "output could not be safely written"}), file=sys.stderr)
        return 2
    print(text)

    if args.ci_policy == "strict":
        return 0 if result.get("verdict") == "GO" else 1
    if args.ci_policy == "controlled":
        return 0 if result.get("verdict") in ("GO", "GO_WITH_CONTROLS") else 1
    return 0
