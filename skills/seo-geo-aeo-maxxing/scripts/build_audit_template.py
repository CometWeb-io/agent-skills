#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

PILLARS = ["foundation", "relevance", "authority", "geo", "aeo"]
MODES = {"RECON", "FULL", "PILLAR", "VERSUS", "DELTA"}


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def split_csv(value):
    if value is None:
        return None
    return [part.strip() for part in value.split(",") if part.strip()]


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate a complete MAXX audit JSON skeleton.")
    parser.add_argument("--mode", default="FULL", choices=sorted(MODES))
    parser.add_argument("--profile", default="balanced")
    parser.add_argument("--pillars", help="Comma-separated active pillars")
    parser.add_argument("--surfaces", help="Comma-separated target AI/search surfaces")
    parser.add_argument("--archetypes", default="", help="Comma-separated site archetypes")
    parser.add_argument("--subject", help="Optional audited URL/domain/label")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    registry = load_json(root / "references" / "check-registry.json")

    mode = args.mode.upper()
    pillars = split_csv(args.pillars)
    if pillars is None:
        if mode == "PILLAR":
            parser.error("PILLAR mode requires --pillars")
        pillars = list(PILLARS)
    if not pillars:
        parser.error("At least one active pillar is required")
    if len(pillars) != len(set(pillars)):
        parser.error("Duplicate pillars are not allowed")
    unknown = sorted(set(pillars) - set(PILLARS))
    if unknown:
        parser.error("Unknown pillars: " + ", ".join(unknown))
    if mode == "FULL" and set(pillars) != set(PILLARS):
        parser.error("FULL mode requires all five pillars")

    surfaces = split_csv(args.surfaces)
    if surfaces is None:
        surfaces = list(registry.get("default_surfaces", []))
    if len(surfaces) != len(set(surfaces)):
        parser.error("Duplicate surfaces are not allowed")
    unknown_surfaces = sorted(set(surfaces) - set(registry.get("surfaces", [])))
    if unknown_surfaces:
        parser.error("Unknown surfaces: " + ", ".join(unknown_surfaces))

    if args.profile not in registry.get("profiles", {}):
        parser.error("Unknown profile: " + args.profile)

    archetypes = split_csv(args.archetypes) or []
    if len(archetypes) != len(set(archetypes)):
        parser.error("Duplicate archetypes are not allowed")
    unknown_archetypes = sorted(set(archetypes) - set(registry.get("site_archetypes", [])))
    if unknown_archetypes:
        parser.error("Unknown site archetypes: " + ", ".join(unknown_archetypes))

    checks = []
    for cdef in registry["checks"]:
        if cdef["pillar"] not in pillars:
            continue
        if cdef.get("na_policy") == "surface" and cdef.get("surface") not in surfaces:
            checks.append({
                "id": cdef["id"],
                "verdict": "N/A",
                "reason": "Target surface intentionally out of scope for this audit."
            })
        else:
            checks.append({
                "id": cdef["id"],
                "verdict": "NOT_ASSESSED",
                "needed": "Collect evidence for: " + cdef["name"]
            })

    payload = {
        "registry_version": registry["version"],
        "mode": mode,
        "profile": args.profile,
        "site_archetypes": archetypes,
        "target_surfaces": surfaces,
        "active_pillars": pillars,
        "checks": checks,
        "gates": []
    }
    if args.subject:
        payload["subject"] = args.subject
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, json.JSONDecodeError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
