#!/usr/bin/env python3
"""Deterministic routing eval proxy for skill metadata collision regression tests."""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "evals" / "routing" / "suite.json"

# Per-skill weighted signals (unicode-normalized substring / regex). Higher = stronger.
SIGNALS: dict[str, list[tuple[int, str]]] = {
    "cometweb-context": [
        (12, r"od[sś]wie[zż].*kontekst|refresh context|context envelope|przygotuj kontekst"),
        (11, r"aktualny stan|potrzebuj[eę] kontekstu|contextenvelope|context-only"),
        (10, r"kontekst.*(spotkani|review|insight|boardroom|cometweb)|context snapshot|stan na "),
        (8, r"delta baseline|authority_gap|provenance-aware context"),
        (6, r"context gateway|minimal.?source"),
    ],
    "ai-council": [
        (10, r"przepu[śs][ćc]? przez rad"),
        (10, r"\bai council\b"),
        (10, r"\bcouncil:"),
        (8, r"\bcouncil health\b"),
        (8, r"living decision"),
        (8, r"champion.challenger"),
        (8, r"pricing decision still current"),
        (7, r"strategic (go|no-go|defer)"),
        (7, r"acquiring .* diligence"),
        (6, r"what price should we charge"),
        (6, r"material options"),
        (6, r"decision council"),
    ],
    "release-readiness": [
        (10, r"release candidate|release gate|go_with_controls|\bno_go\b"),
        (10, r"\brc[\s.-]?\d|build v?\d+\.\d+|artifact digest"),
        (9, r"ready for production|ready to ship|wypu[śs]ci[ćc].*produkc"),
        (9, r"hotfix readiness|pre-deploy audit|launch gate|production gate"),
        (8, r"readiness manifest|release readiness"),
        (7, r"post-incident release|revalidat.*release"),
        (6, r"can we ship"),
    ],
    "repo-to-roadmap": [
        (10, r"analyze the (whole|entire) (repo|project|codebase)"),
        (10, r"przeanalizuj ca[łl][eąa] repo"),
        (9, r"whole-project baseline|roadmap from scratch|first-time.*roadmap"),
        (9, r"project topology|target state.*roadmap|paid_production"),
        (8, r"co zosta[łl]o do wdro[żz]enia|roadmap.*acceptance proof"),
        (8, r"update the roadmap after|delta roadmap|exhaustively.*roadmap"),
        (8, r"what gates are missing before any future production"),
        (8, r"what is left before production for the whole platform"),
        (7, r"what is left to build|what.?s left before production for the whole"),
        (7, r"client-ready.*roadmap|roadmap.*client-ready"),
        (6, r"create.*roadmap.*repo|gaps before any future production"),
    ],
    "product-operator": [
        (10, r"what (should we|to) (do|build|fix|verify) (next|this week)"),
        (10, r"what changed since (the )?last review"),
        (10, r"co robimy dalej"),
        (10, r"priorytetyzowa[cć].*sprint|w sprincie|ship .* this week"),
        (9, r"can we ship .* this week"),
        (9, r"roadmap.*repo agree|plan ahead of code|shipped without outcome"),
        (9, r"does our roadmap match|actually implemented in the repo"),
        (9, r"weekly (product|sprint)|control loop|existing roadmap"),
        (8, r"blocker|verify now|now/next/later/stop"),
        (8, r"stuck between planned and implemented|daily standup"),
        (8, r"github.*notion state"),
        (7, r"unstick|priority thrash|what should we stop"),
        (7, r"specialist audits should we run"),
        (6, r"mamy roadmap"),
    ],
    "evidence-researcher": [
        (10, r"evidence pack"),
        (9, r"fact-check|due diligence|falsifier"),
        (8, r"verify claims|source lineage|negative evidence"),
        (8, r"contradiction|derivative source"),
        (7, r"prepare evidence for council"),
        (6, r"pricing claims for .* vendors"),
    ],
    "web-app-auditor": [
        (10, r"click through|click-through|web app audit|live app audit"),
        (9, r"qa audit|forensic audit|accessibility of the registration"),
        (8, r"usability-risk|needs-repro|scope card"),
        (7, r"file defects with evidence"),
    ],
    "competitive-intelligence": [
        (10, r"competitor watchlist|competitor digest|competitive intelligence"),
        (10, r"one-time deep profile of .* pricing"),
        (9, r"what changed on competitor|since last month.?s snapshot"),
        (9, r"competitor.*pricing page|summarize competitor pricing"),
        (8, r"competitor dropped|should we respond strategically"),
        (7, r"monitor competitors|competitor delta"),
    ],
    "product-teardown": [
        (10, r"\bteardown\b|reverse-engineer"),
        (9, r"transferable pattern|what can we (borrow|learn) from"),
        (8, r"wyci[ąa]gnij wzorce|co warto wdro[żz]y"),
        (7, r"synthesize onboarding patterns|architecture patterns"),
    ],
    "design-partner-finder": [
        (10, r"design partner|learning contract|partner charter"),
        (9, r"partner cohort|partnerability|live-ready vs desk"),
        (8, r"score design partner|pilot cohort"),
    ],
    "customer-ops": [
        (10, r"support queue|customer case|account 360"),
        (9, r"incident candidate|churn signal|non-renewal"),
        (8, r"support.*engineering|dedupe github issues"),
        (8, r"resolved.*verified|stuck between resolved and verified"),
        (7, r"build a crm"),
    ],
    "seo-geo-aeo-maxxing": [
        (12, r"seo/geo/aeo|seo geo aeo|seo/ geo/ aeo"),
        (10, r"seo audit|visibility audit|aeo visibility"),
        (9, r"indexable|canonical|search visibility audit"),
        (8, r"geo audit registry fresh"),
    ],
    "ai-humanize": [
        (10, r"humanize|humanise|sound less like ai"),
        (9, r"remove ai tells|invisible unicode|deep rewrite"),
        (5, r"fix typos"),
    ],
    "skill-orchestrator": [
        (16, r"zorkiestruj|zorkiestr"),
        (14, r"najpierw .* potem"),
        (12, r"orchestrate:|@skill-orchestrator|skill orchestrator"),
        (11, r"\borchestrat(e|:|\b)"),
        (10, r"orchestrat.*skill|sequence.*skill|multi.?step workflow"),
        (10, r"verify.*then run council|claims first.*then.*council"),
        (10, r"then run council|research.*then.*council"),
        (10, r"evidence.*(then|→|->|potem).*(council|rad[ęe])"),
        (10, r"which cometweb skill|which skill should I use"),
        (9, r"full workflow|end.to.end|ca[łl][yąa] workflow"),
        (9, r"zr[oó]b wszystko|od researchu do (decyzji|rady)"),
        (9, r"chain.*skill|run everything needed"),
        (8, r"audit.*(then|→|->|potem).*(release|ship|readiness)"),
        (7, r"help me pick.*skill"),
    ],
    "skill-orchestrator-multiagent": [
        (20, r"one subagent per skill|subagent per step"),
        (12, r"skill-orchestrator-multiagent|@skill-orchestrator-multiagent"),
        (12, r"\bmultiagent\b|\bmulti-agent\b|\bmulti agent\b"),
        (11, r"separate agent per skill|one agent per skill|osobn(y|e) agent"),
        (10, r"wymus.*subagent|wymus.*agent"),
        (9, r"multiagent.*orchestrat|orchestrat.*multiagent"),
    ],
}


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def score_prompt(prompt: str) -> dict[str, int]:
    text = normalize(prompt)
    scores: dict[str, int] = {}
    for skill, patterns in SIGNALS.items():
        total = 0
        for weight, pattern in patterns:
            if re.search(pattern, text, re.I):
                total += weight
        if total:
            scores[skill] = total
    return scores


def classify(prompt: str) -> str | None:
    scores = score_prompt(prompt)
    if not scores:
        return None
    return max(scores, key=scores.get)


def load_suite() -> dict:
    data = json.loads(SUITE.read_text(encoding="utf-8"))
    if "cases" not in data or not isinstance(data["cases"], list):
        raise AssertionError("suite.json must contain cases[]")
    return data


def validate_case(case: dict, index: int) -> None:
    required = ("id", "prompt", "expected_primary_skill", "must_not_trigger", "reason")
    for key in required:
        if key not in case:
            raise AssertionError(f"case[{index}] missing {key}")


def main() -> int:
    data = load_suite()
    failures: list[str] = []
    for index, case in enumerate(data["cases"]):
        validate_case(case, index)
        predicted = classify(case["prompt"])
        expected = case["expected_primary_skill"]
        if predicted != expected:
            scores = score_prompt(case["prompt"])
            failures.append(
                f"{case['id']}: expected {expected}, got {predicted!r} "
                f"(scores={scores}) — {case['reason']}"
            )
        for blocked in case["must_not_trigger"]:
            if predicted == blocked:
                failures.append(
                    f"{case['id']}: must_not_trigger {blocked} but was primary — {case['reason']}"
                )

    if failures:
        for line in failures:
            print(f"FAIL: {line}", file=sys.stderr)
        print(f"\n{len(failures)} routing eval failure(s)", file=sys.stderr)
        return 1

    print(f"OK: {len(data['cases'])} routing eval cases passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
