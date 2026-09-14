#!/usr/bin/env python3
"""Deterministic helper for selecting a minimal CometWeb context profile."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import unicodedata

_DEFAULT_PROFILES = {
    "product": ["github-product", "insight", "vault-status", "vault-decisions"],
    "portfolio": [
        "github-portfolio",
        "notion",
        "vault-status",
        "vault-decisions",
        "insight",
    ],
    "gtm": ["vault-decisions", "vault-first-principles", "vault-topic", "website", "crm-when-material"],
    "outreach": ["crm", "communications", "vault-icp-sop", "prospect-web"],
    "brand": ["vault-brand", "evidence-register", "public-profiles", "website"],
    "meeting": ["calendar", "contacts", "crm-or-communications", "relevant-docs"],
    "weekly": [
        "github-portfolio",
        "insight",
        "vault",
        "crm",
        "notion",
        "communications-when-relevant",
        "website",
    ],
    "claim-verification": ["evidence-register", "primary-claim-source", "publication-surface"],
    "custom": [],
}

RULES = [
    (r"weekly|boardroom|przegl[aą]d tygodni|review tygodni|weekly review", "weekly"),
    (
        r"full refresh|pełn.*refresh|pel[nł].*refresh|cał[ey].*cometweb|cale.*cometweb|wszystk.*projekt|portfolio|"
        r"insight.*base.*pen|base.*pen.*lens|cometweb.*projekty|notion.*github.*projekt|"
        r"przeanalizuj.*projekty|stan.*wszystk.*repo|skupi.*cometweb|focus.*cometweb",
        "portfolio",
    ),
    (r"meeting|spotkani|przygotuj mnie do|calendar|kalendar|mentor|rada nauk|review z", "meeting"),
    (r"outreach|design partner|prospekt|cold email|follow.?up|sprzeda|lead", "outreach"),
    (r"public claim|claim|evidence register|case study|wynik.*public|twierdzeni.*public", "claim-verification"),
    (r"personal brand|marka osobista|linkedin|threads|social|content|post", "brand"),
    (r"pricing|cennik|gtm|positioning|pozycjon|strategi|go.to.market|packaging|pakiet", "gtm"),
    (r"repo|roadmap|release|product|produkt|insight|cometpen|cometbase|cometlens|extension|wdroż|wdroz", "product"),
]

MATERIAL_DECISION = re.compile(
    r"czy powinni|should we|go.?no.?go|wybra[cć]|decyz|pricing|cennik|packaging|pakiet|"
    r"icp|gtm|pozycjon|portfolio|architektur|launch|public.*claim|materialn|strategi|"
    r"co robi[cć] dalej|priorytet|focus|alokacj|kt[oó]ry projekt|which project",
    re.IGNORECASE,
)


def norm(text: str) -> str:
    return unicodedata.normalize("NFKC", text).casefold()


def _deep_merge(base: dict, overlay: dict) -> dict:
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_merge(base[key], value)
        elif isinstance(value, list) and isinstance(base.get(key), list):
            by_id = {item.get("id"): item for item in base[key] if isinstance(item, dict)}
            for item in value:
                if isinstance(item, dict) and item.get("id") in by_id:
                    by_id[item["id"]].update(item)
                else:
                    base[key].append(item)
        else:
            base[key] = value
    return base


def load_source_registry(registry: pathlib.Path) -> dict:
    """Read the tracked registry and apply an untracked local overlay.

    Paths into a private vault are placeholders in the committed file and real
    values in source-registry.local.json beside it, which is gitignored. That
    keeps one registry shape for everyone while the concrete locations never
    reach a published tree.
    """
    data = json.loads(registry.read_text(encoding="utf-8"))
    local = registry.with_name(registry.stem + ".local" + registry.suffix)
    if local.is_file():
        overlay = json.loads(local.read_text(encoding="utf-8"))
        if not isinstance(overlay, dict):
            raise ValueError("local source registry overlay must be an object")
        _deep_merge(data, overlay)
    return data


def load_profiles(registry: pathlib.Path | None = None) -> dict[str, list[str]]:
    registry = registry or pathlib.Path(__file__).resolve().parents[1] / "references/source-registry.json"
    if not registry.is_file():
        return {name: list(groups) for name, groups in _DEFAULT_PROFILES.items()}
    data = load_source_registry(registry)
    profiles = data.get("profiles") if isinstance(data, dict) else None
    if not isinstance(profiles, dict):
        raise ValueError("source registry profiles must be an object")
    merged = {name: list(groups) for name, groups in _DEFAULT_PROFILES.items()}
    for name, body in profiles.items():
        groups = body.get("preferred_source_groups") if isinstance(body, dict) else None
        if name not in merged or not isinstance(groups, list) or any(not isinstance(g, str) or not g.strip() for g in groups):
            raise ValueError(f"invalid source registry profile: {name}")
        if len(groups) != len(set(groups)):
            raise ValueError(f"duplicate source group in profile: {name}")
        merged[name] = list(groups)
    return merged


PROFILES = load_profiles()


def pick_profiles(goal: str) -> dict:
    text = norm(goal)
    candidates = list(dict.fromkeys(profile for pattern, profile in RULES
                                   if re.search(pattern, text, re.IGNORECASE)))
    if not candidates and re.search(r"\bcometweb\b", text) and re.search(r"stan|zmieni|kontekst|context|review|przegl|priorytet|skupi|focus|alokacj|kt[oó]ry projekt", text):
        candidates = ["portfolio"]
    candidates = candidates or ["custom"]
    return {"primary": candidates[0], "candidates": candidates, "ambiguous": len(candidates) > 1}


def pick_profile(goal: str) -> str:
    return pick_profiles(goal)["primary"]


def pick_mode(goal: str, requested: str) -> str:
    if requested != "auto":
        return requested
    text = norm(goal)
    if re.search(r"co si[ęe] zmieni|delta|since|od ostat|co nowego", text):
        return "delta"
    if re.search(
        r"pełn.*refresh|pel[nł].*refresh|wszystkie [źz]r[oó]d|boardroom|weekly review|przegl[aą]d tygodni|review tygodni|"
        r"cał[ey].*cometweb|cale.*cometweb|wszystk.*projekt|full context|cał[ey].*portfolio",
        text,
    ):
        return "full"
    if re.search(r"jedn[ao] rzecz|tylko|konkretn|wąsk|wask|single", text):
        return "targeted"
    return "standard"


def requires_first_principles(goal: str, profile: str) -> bool:
    text = norm(goal)
    return bool(MATERIAL_DECISION.search(text))


def plan(goal: str, requested_mode: str = "auto") -> dict:
    profile = pick_profile(goal)
    mode = pick_mode(goal, requested_mode)
    groups = list(load_profiles()[profile])
    fp_required = requires_first_principles(goal, profile)
    if fp_required and "vault-first-principles" not in groups:
        groups.insert(0, "vault-first-principles")
    return {
        "profile": profile,
        "mode": mode,
        "source_groups": groups,
        "governance": {
            "first_principles_required": fp_required,
            "decision_log_required": fp_required,
        },
        **{key: value for key, value in pick_profiles(goal).items() if key != "primary"},
        "registry": "references/source-registry.json",
        "rule": "minimal-authoritative-sources-first",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("goal")
    parser.add_argument("--mode", choices=["auto", "targeted", "standard", "delta", "full"], default="auto")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    payload = plan(args.goal, args.mode)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"profile={payload['profile']} mode={payload['mode']}")
        print(f"first_principles_required={payload['governance']['first_principles_required']}")
        for source in payload["source_groups"]:
            print(f"- {source}")


if __name__ == "__main__":
    main()
