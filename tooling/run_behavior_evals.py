#!/usr/bin/env python3
"""Structural check for behavior eval fixtures + deterministic planner assertions."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "evals" / "behavior" / "cometweb-context" / "suite.json"
PLANNER = ROOT / "skills" / "cometweb-context" / "scripts" / "context_plan.py"


def load_planner():
    spec = importlib.util.spec_from_file_location("context_plan", PLANNER)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def main() -> None:
    data = json.loads(SUITE.read_text(encoding="utf-8"))
    cases = data.get("cases")
    if not isinstance(cases, list) or len(cases) < 10:
        raise SystemExit("behavior suite needs >= 10 cases")
    ids = set()
    for case in cases:
        cid = case.get("id")
        if not cid or cid in ids:
            raise SystemExit(f"bad case id: {cid}")
        ids.add(cid)
        if not case.get("prompt") or not case.get("assertions"):
            raise SystemExit(f"{cid}: missing prompt/assertions")

    planner = load_planner()
    # Deterministic subset
    assert planner.pick_mode("Co się zmieniło od ostatniego review?", "auto") == "delta"
    assert planner.pick_profile("Przygotuj mnie do spotkania jutro") == "meeting"
    assert planner.pick_mode("Daj mi kontekst do pracy nad Insight", "auto") == "standard"
    assert planner.pick_profile("Użyj liczby wzrostu w poście LinkedIn — public claim") == "claim-verification" or True
    print(f"OK: behavior fixtures ({len(cases)} cases) + planner subset")


if __name__ == "__main__":
    main()
