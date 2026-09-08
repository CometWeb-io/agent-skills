#!/usr/bin/env python3
"""Deterministic helper for selecting a minimal CometWeb context profile."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import unicodedata

_DEFAULT_PROFILES = {
    "product": ["repo", "insight", "vault-status", "vault-first-principles"],
    "gtm": ["vault-decisions", "vault-first-principles", "vault-topic", "website"],
    "outreach": ["crm", "communications", "vault-icp-sop", "prospect-web"],
    "brand": ["vault-brand", "evidence-register", "public-profiles", "website"],
    "meeting": ["calendar", "contacts", "crm-or-communications", "relevant-docs"],
    "weekly": ["repo", "insight", "vault", "crm", "notion", "communications", "website", "public-profiles"],
    "claim-verification": ["evidence-register", "primary-claim-source", "publication-surface"],
    "custom": [],
}

RULES = [
    (r"weekly|boardroom|tygodni|pełn.*refresh|pel[nł].*refresh", "weekly"),
    (r"meeting|spotkani|przygotuj mnie do|calendar|kalendar|przygotuj kontekst", "meeting"),
    (r"outreach|design partner|prospekt|cold email|follow.?up|sprzeda", "outreach"),
    (r"personal brand|marka osobista|linkedin|threads|social|content|post", "brand"),
    (r"public claim|claim|evidence register|case study|wynik.*public", "claim-verification"),
    (r"pricing|gtm|positioning|pozycjon|strategi|go.to.market", "gtm"),
    (r"repo|roadmap|release|product|insight|cometpen|cometbase|extension|wdroż|wdroz|kontekst produktu", "product"),
]


def load_profiles() -> dict[str, list[str]]:
    registry = pathlib.Path(__file__).resolve().parent.parent / "references" / "source-registry.json"
    if not registry.is_file():
        return dict(_DEFAULT_PROFILES)
    try:
        data = json.loads(registry.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return dict(_DEFAULT_PROFILES)
    profiles = data.get("profiles") or {}
    merged = dict(_DEFAULT_PROFILES)
    for name, body in profiles.items():
        groups = body.get("preferred_source_groups")
        if isinstance(groups, list):
            merged[name] = [str(item) for item in groups]
    return merged


PROFILES = load_profiles()


def norm(text: str) -> str:
    return unicodedata.normalize("NFKC", text).casefold()


def pick_profile(goal: str) -> str:
    text = norm(goal)
    for pattern, profile in RULES:
        if re.search(pattern, text, re.IGNORECASE):
            return profile
    return "custom"


def pick_mode(goal: str, requested: str) -> str:
    if requested != "auto":
        return requested
    text = norm(goal)
    if re.search(r"co si[ęe] zmieni|delta|since|od ostat", text):
        return "delta"
    if re.search(r"pełn.*refresh|pel[nł].*refresh|wszystkie [źz]r[oó]d|boardroom|weekly|tygodni", text):
        return "full"
    if re.search(r"jedn[ao] rzecz|tylko|konkretn", text):
        return "targeted"
    return "standard"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("goal")
    parser.add_argument("--mode", choices=["auto", "targeted", "standard", "delta", "full"], default="auto")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    profiles = load_profiles()
    profile = pick_profile(args.goal)
    mode = pick_mode(args.goal, args.mode)
    payload = {
        "profile": profile,
        "mode": mode,
        "source_groups": profiles.get(profile, []),
        "rule": "minimal-sources-first",
        "registry": "references/source-registry.json",
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"profile={profile} mode={mode}")
        for source in payload["source_groups"]:
            print(f"- {source}")


if __name__ == "__main__":
    main()
