#!/usr/bin/env python3
"""Operator-run blind/baseline behavior eval harness (skeleton).

Does not call LLMs in CI. Records fixture expectations and optional comparison
artifacts under dist/eval-reports/<skill>/<version>/.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BEHAVIOR = ROOT / "evals" / "behavior"
OUT = ROOT / "dist" / "eval-reports"


def load_suites() -> list[dict]:
    suites = []
    if not BEHAVIOR.is_dir():
        return suites
    for path in sorted(BEHAVIOR.glob("*/suite.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        data["_path"] = str(path.relative_to(ROOT))
        data["_skill"] = path.parent.name
        suites.append(data)
    return suites


def structural_report(suite: dict) -> dict:
    cases = suite.get("cases") or []
    return {
        "skill": suite["_skill"],
        "suite_path": suite["_path"],
        "suite_version": suite.get("suite_version"),
        "case_count": len(cases),
        "case_ids": [c.get("id") for c in cases],
        "mode": "structural",
        "note": "LLM blind comparison is operator-run; CI only checks fixture structure.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill", default=None)
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument(
        "--baseline",
        type=Path,
        default=None,
        help="Optional previous report JSON for delta summary",
    )
    args = parser.parse_args()

    suites = load_suites()
    if args.skill:
        suites = [s for s in suites if s["_skill"] == args.skill]
    if not suites:
        raise SystemExit("no behavior suites found")

    reports = [structural_report(s) for s in suites]
    payload = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "reports": reports,
    }
    blob = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    payload["fingerprint"] = hashlib.sha256(blob.encode()).hexdigest()[:16]

    if args.baseline and args.baseline.is_file():
        baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
        old_ids = {
            r["skill"]: set(r.get("case_ids") or [])
            for r in baseline.get("reports", [])
        }
        deltas = []
        for report in reports:
            prev = old_ids.get(report["skill"], set())
            cur = set(report["case_ids"])
            deltas.append(
                {
                    "skill": report["skill"],
                    "added": sorted(cur - prev),
                    "removed": sorted(prev - cur),
                }
            )
        payload["baseline_delta"] = deltas

    print(json.dumps(payload, ensure_ascii=False, indent=2))

    if args.write_report:
        for report in reports:
            version_path = ROOT / "skills" / report["skill"] / "VERSION"
            version = version_path.read_text().strip() if version_path.is_file() else "0.0.0"
            out_dir = OUT / report["skill"] / version
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = out_dir / "behavior-structural.json"
            out_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
            print(f"OK: wrote {out_file.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
