#!/usr/bin/env python3
"""Synchronize authoritative cross-runtime skill releases into registry/skills.json."""
from __future__ import annotations

import argparse
import json
import re
import sys
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tooling"))
from compatibility import safe_load_unique  # noqa: E402

REGISTRY = ROOT / "registry" / "skills.json"
SKILLS = ROOT / "skills"
HOST_TARGETS = [
    "chatgpt",
    "openai-codex",
    "claude-code",
    "cursor",
    "qwen-code",
    "qoder",
    "lingma",
    "alibaba-skills-portal",
]
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)


def parse_description(skill_md: Path) -> str:
    """The frontmatter description as a YAML loader reads it, whitespace-collapsed.

    Hosts read SKILL.md with a YAML parser, so a hand-rolled line reader here
    could register a different description than the one they route on: a
    blank line inside a folded block, a ``|`` literal, an escaped quote or a
    trailing comment all parse differently. Collapsing whitespace matches the
    comparison validate_repo.py makes between the package and the registry.
    """
    match = FRONTMATTER_RE.match(skill_md.read_text(encoding="utf-8"))
    if not match:
        raise ValueError(f"missing frontmatter: {skill_md}")
    # Duplicate keys are rejected rather than silently resolved.
    data = safe_load_unique(match.group(1))
    description = data.get("description") if isinstance(data, dict) else None
    if not isinstance(description, str) or not description.strip():
        raise ValueError(f"missing description: {skill_md}")
    return " ".join(description.split())


def package_identity(skill_id: str) -> tuple[str, str]:
    skill_dir = SKILLS / skill_id
    return (
        (skill_dir / "VERSION").read_text(encoding="utf-8").strip(),
        parse_description(skill_dir / "SKILL.md"),
    )


# Polish adversarial-review verbs and adjectives shared by the three roasters;
# each roaster pairs them with its own nouns (copy, code, science).
PL_ROAST = (r"(?:upiecz|zroastuj|rozjedz|rozwal|rozbierz|zmiazdz|zjedz|przejedz sie|red.?team\w*|bez litosci"
            r"|bezlitosn\w* (?:ocen|przejrz|skrytykuj|sprawdz|recenz)"
            r"|(?:ocen|przejrz|sprawdz|skrytykuj|przeanalizuj|recenzuj)\w* (?:\w+ )?bezlitosn\w*"
            r"|brutaln\w* (?:ocen|przejrz|skrytykuj|przeglad|recenzj)"
            r"|(?:wrog|brutaln|bezlitosn|forensyczn|adwersaryjn|tward)\w* (?:przeglad|recenzj|audyt|ocen)\w*)")


OVERRIDES: dict[str, dict] = {
    "founder-led-sales-operator": {
        "release_status": "FROZEN",
        "tier": "domain",
        "owns": ["founder-led commercial next action", "sales-stage reconciliation", "commercial gates and proof progression"],
        "does_not_own": ["broad prospect-list generation", "pricing/packaging strategy", "post-sale customer operations"],
        "trigger_examples": ["What should I do next with these qualified prospects?", "Which founder-led deals should I move, verify, wait, or stop?"],
        "negative_trigger_examples": ["Build me a broad list of 100 prospects", "Design our SaaS pricing tiers"],
        "routing_signals": [[12, "founder-led sales operator|founder led sales"], [10, "qualified prospects?.*(next|move|follow.?up|convert)"], [9, "commercial (next action|gate|proof|stage)"], [8, "pipeline.*(verify|wait|stop|paid conversion)"]],
        "required_capabilities": [],
        "optional_capabilities": ["filesystem", "code_execution", "web", "connectors"],
    },
    "research-program-operator": {
        "release_status": "FROZEN",
        "tier": "domain",
        "owns": ["research-program stage gates", "research/manuscript readiness", "next-study planning"],
        "does_not_own": ["one-off claim verification", "final publication formatting", "cross-domain portfolio allocation"],
        "trigger_examples": ["What should this study do next?", "Reconcile this research project from methodology through manuscript readiness"],
        "negative_trigger_examples": ["Verify this single factual claim", "Format this finished paper as DOCX"],
        "routing_signals": [[12, "research program operator|research-program"], [10, "study.*(what next|readiness|methodology|manuscript)"], [9, "research.*(stage gate|submission readiness|next study)"], [8, "academic project.*(blocker|authorship|governance)"]],
        "required_capabilities": [],
        "optional_capabilities": ["filesystem", "code_execution", "web", "files", "connectors"],
    },
    "portfolio-operator": {
        "release_status": "ACTIVE",
        "tier": "foundation",
        "owns": ["cross-domain allocation", "capacity conflicts", "focus/pause/delegate decisions"],
        "does_not_own": ["deep single-product sequencing", "release GO/NO_GO", "specialist implementation"],
        "trigger_examples": ["What should I focus on for the next 14 days across all my projects?", "Which commitments conflict and what should I pause?"],
        "negative_trigger_examples": ["What should we build next inside this one repo?", "Is this release candidate safe to ship?"],
        "routing_signals": [[10, "\\bbetween (?:my|our)\\b.{0,80}\\b(?:what (?:do|should) (?:i|we) (?:prioriti[sz]e|focus on|drop|cut)|how (?:do|should) (?:i|we) (?:split|allocate|divide))"], [10, "\\b(?:rozdziel|podziel|rozplanuj)\\w*\\b.{0,20}\\bczas\\w*\\b.{0,20}\\bmiedzy\\b"], [9, "\\bwhat should (?:i|we) (?:cut|drop|pause|delegate|say no to)\\b"], [10, "\\bco (?:powinienem|powinnam|powinnismy|mam|mamy|moge|warto) (?:odpuscic|wstrzymac|oddelegowac|rzucic|przesunac|skreslic)"], [12, "portfolio operator|portfolio-wide"], [10, "next (7|14|30) days.*(projects|commitments|focus)"], [9, "capacity conflicts?|what should (i|we) pause|across multiple projects"], [8, "client.*product.*research|cross-domain allocation"], [9, "focus on across (all )?(my|our) (projects|commitments)|across (all )?(my|our) (projects|commitments).{0,40}(focus|pause|drop|delegate)|\\bacross (?:all )?(?:my|our)\\b.{0,80}\\b(?:what should (?:i|we) (?:focus|pause|drop|delegate)|focus on for the next)"], [10, "\\b(?:na )?czym (?:mam|mamy|powinienem|powinnam|powinnismy) sie skupic\\b.{0,120}\\b(?:projekt|klient|produkt)|\\bnajblizsze (?:\\d+|dwa|trzy|cztery) (?:tygodni|tygodnie|dni)\\b.{0,100}\\bprojekt|\\bmiedzy (?:projektami|produktem|produktami)\\b|\\bco (?:wstrzymac|odpuscic|oddelegowac)\\b|\\bza duzo (?:rzeczy|projektow|zobowiazan)|\\bzobowiazan\\w*\\b.{0,60}\\b(?:gryz|koliduj|konflikt|nie dowioz)|\\bpriorytet\\w*\\b.{0,40}\\bmiedzy\\b"]],
        "required_capabilities": [],
        "optional_capabilities": ["filesystem", "code_execution", "connectors"],
    },
    "longform-publisher": {
        "release_status": "FROZEN",
        "tier": "domain",
        "owns": ["canonical long-form manuscript", "publication lifecycle and claim-use reconciliation", "derived-artifact release readiness"],
        "does_not_own": ["primary evidence research", "generic prose humanization", "DOCX/PDF rendering internals"],
        "trigger_examples": ["Refresh this old ebook into a publication-ready 2026 edition", "Build this evidence-backed report through manuscript, DOCX and PDF release readiness"],
        "negative_trigger_examples": ["Humanize this paragraph", "Rotate this PDF page"],
        "routing_signals": [[11, "\\breconcil\\w*\\b.{0,60}\\bmanuscript|\\b(?:html|pdf|docx|epub)\\b.{0,20}\\b(?:and|/|,) ?(?:the )?(?:html|pdf|docx|epub)\\b.{0,60}\\b(?:disagree|differ|drift|out of sync|mismatch|don.t match)"], [11, "\\bregenerat\\w*\\b.{0,30}\\b(?:docx|pdf|html)\\b.{0,10}(?:\\band\\b|/|,) ?(?:the )?(?:docx|pdf|html)\\b|\\bregenerat\\w*\\b.{0,30}\\bderived\\b|(existing|current|old|previous) (ebook|white paper|report|handbook|playbook|guide)\\b.{0,80}\\b(?:manuscript|edition)\\b"], [12, "longform publisher|publication workflow"], [11, "(ebook|white paper|playbook|handbook|guide|report)\\b.{0,60}\\b(?:publication.ready|release.ready|new edition|\\d{4} edition)"], [10, "canonical manuscript|publication-report\\.json"], [10, "\\b(?:e-?book|white paper|report|handbook|playbook|guide)\\b.{0,80}\\b(?:docx|pdf) ?(?:/|and|,|&) ?(?:the )?(?:docx|pdf)\\b"], [10, "through (?:the )?manuscript|manuscript\\b.{0,60}\\b(?:derived|lineage|regenerat\\w*|rebuil\\w*|edition)\\b|\\b(?:docx|pdf)\\b.{0,40}\\bfrom (?:the |one |a |its )?(?:canonical |single )?manuscript"], [9, "\\brefresh\\w*\\b.{0,30}\\b(?:e-?book|white paper|handbook|playbook|guide)\\b|\\brefresh\\w*\\b.{0,30}\\breport\\b.{0,40}\\b(?:edition|manuscript|docx|pdf)\\b|derived artifacts?.*(docx|pdf)"], [10, "\\bmanuskrypt\\w*\\b.{0,80}\\b(?:docx|pdf|wydani|edycj|przebuduj|generowan|wygeneruj)|\\b(?:kanoniczn|jedn)\\w* manuskrypt|\\b(?:docx|pdf)\\b.{0,40}\\b(?:z manuskryptu|zgadzaj\\w* sie z manuskrypt)|\\b(?:nowe|nowa|kolejne|kolejna) (?:wydanie|edycj\\w*)\\b.{0,60}\\b(?:raport|white ?paper|handbook|poradnik|przewodnik|e-?book|playbook)|\\b(?:odswiez|zaktualizuj|uaktualnij)\\w*\\b.{0,40}\\b(?:raport|white ?paper|handbook|poradnik|przewodnik|playbook)\\w*\\b.{0,40}\\b(?:wydani|edycj|manuskrypt)"]],
        "required_capabilities": [],
        "optional_capabilities": ["filesystem", "code_execution", "web", "files"],
    },
    "product-operator": {
        "release_status": "ACTIVE",
        "tier": "domain",
        "required_capabilities": [],
        "optional_capabilities": ["filesystem", "code_execution", "git", "connectors"],
    },
    "artifact-acceptance": {
        "release_status": "ACTIVE",
        "tier": "domain",
        "owns": ["knowledge-artifact acceptance gates", "evidence-backed artifact verdicts", "candidate and contract traceability"],
        "does_not_own": ["software release verdicts", "initial editorial review", "consequential strategic decisions"],
        "trigger_examples": ["Is this report ready to publish against its brief?", "Run the final acceptance gate on this knowledge artifact"],
        "negative_trigger_examples": ["Is this software release ready?", "Review this article for the first time"],
        "routing_signals": [[10, "\\b(?:met|meeting)\\b.{0,30}\\bacceptance (?:checklist|criteri\\w*|contract)|\\bacceptance criterion\\b"], [10, "\\b(?:pass\\w*|meets?|satisf\\w*|fulfil\\w*|against)\\b.{0,30}\\b(?:the |its |our |this )?acceptance (?:checklist|criteria|contract|requirements)"], [10, "\\b(?:meets?|satisf\\w*|pass\\w*|fulfil\\w*)\\b.{0,30}\\b(?:the |its |our |this )?(?:brief|acceptance (?:criteria|contract)|evidence requirements)\\b|\\bmeasured against (?:the |its |our )?(?:brief|acceptance (?:criteria|contract))"], [10, "\\bkontrakt\\w* akceptacyjn|\\bspelnia\\w*\\b.{0,40}\\b(?:brief|kontrakt|kryteri\\w* (?:akceptacji|odbioru))"], [12, "artifact acceptance|acceptance gate.*(artifact|report|content)|report ready against its brief"], [10, "ready.*(publish|deliver).*brief"], [9, "final (artifact|knowledge) gate"], [8, "artifact.*(READY_WITH_CONTROLS|NOT_READY|DEFER)"], [7, "acceptance contract.*evidence"], [10, "\\bfinal acceptance\\b.{0,40}\\b(?:report|artifact|candidate|contract|brief|deliverable)\\b"], [10, "\\b(?:koncow\\w*|ostateczn\\w*|finaln\\w*) (?:odbior|akceptacj|bramk|werdykt)\\w*\\b.{0,60}\\b(?:raport|white ?paper|e-?book|prezentacj|dokument|brief|material|poradnik|artefakt|opracowan)|\\bodbior\\w*\\b.{0,40}\\b(?:raportu|white ?papera|e-?booka|prezentacji|dokumentu|materialu|poradnika|artefaktu|opracowania)\\b|\\b(?:spelnia|spelni|przechodzi)\\w*\\b.{0,40}\\bkryteri\\w* akceptacji|\\b(?:raport|white ?paper|e-?book|prezentacj|dokument|material|poradnik|opracowan)\\w*\\b.{0,60}\\bgotow\\w*\\b.{0,40}\\b(?:wedlug|zgodnie z|wobec|wzgledem) (?:briefu|kryteriow)|\\bostatni\\w* bramk\\w*\\b.{0,60}\\b(?:raport|white ?paper|e-?book|prezentacj|dokument|material|poradnik)"], [10, "\\b(?:raport|white ?paper|e-?book|prezentacj|dokument|material|poradnik|opracowan|artykul)\\w*\\b.{0,60}\\b(?:mozemy|mozna) (?:juz )?(?:go |je |to )?(?:oddac|wyslac|przekazac|opublikowac)\\b"]],
        "required_capabilities": [],
        "optional_capabilities": ["filesystem", "code_execution", "files"],
    },
    "benchmark-curator": {
        "release_status": "ACTIVE",
        "tier": "foundation",
        "owns": ["benchmark and eval corpus design", "holdout and contamination controls", "benchmark revision hashes"],
        "does_not_own": ["model experiment execution", "rubric design", "skill editing"],
        "trigger_examples": ["Curate a clean holdout benchmark for this skill", "Design the discovery and regression corpus"],
        "negative_trigger_examples": ["Run the model experiment and claim lift", "Design the grading rubric"],
        "routing_signals": [[10, "\\b(?:curat|assembl|build|collect|write)\\w*\\b.{0,30}\\b(?:evaluation|eval|benchmark|routing) prompts\\b|\\bholdout split\\b|\\bsealed holdout\\b"], [10, "\\b(?:build|assembl|creat|curat|design|construct|dedupe|deduplicat|stratif|freez|version|rebuild|grow|expand|maintain)\\w*\\b.{0,50}\\b(?:regression|evaluation|eval|golden|challenge|benchmark) (?:set|dataset|corpus|cases)\\b|\\b(?:evaluation|eval) dataset\\b.{0,60}\\b(?:dedupe|deduplicat|stratif|freez|difficulty|provenance|holdout)"], [10, "\\b(?:test|eval\\w*) cases\\b.{0,60}\\b(?:holdout|negative controls?|difficulty|strat)"], [10, "\\bzlot\\w* zestaw|\\b(?:zbior|zestaw)\\w* przypadk\\w*\\b.{0,80}\\b(?:holdout|kontrol\\w* negatywn|trudn|latw|regresyjn|adwersaryjn|adversarial|ocen\\w* skill)|\\bkontrol\\w* negatywn"], [20, "curate.*(clean )?holdout benchmark"], [12, "benchmark curator|benchmark.*corpus"], [10, "golden set|regression corpus|challenge set"], [9, "holdout.*(contamination|leakage|clean)"], [8, "eval dataset.*(taxonomy|provenance|duplicate)"], [7, "freeze.*benchmark.*hash"], [10, "\\b(?:zestaw|korpus)\\w* (?:testow|ewaluacyjn|regresyjn|referencyjn|przypadkow testow)\\w*|\\bgolden set\\w*|\\bholdout\\w*\\b.{0,80}\\b(?:wyciek|kontaminac|czyst|duplikat|odizol)|\\bkontaminac\\w*|\\b(?:zbuduj|przygotuj|uloz|zaprojektuj|uporzadkuj|wyczysc)\\w*\\b.{0,40}\\b(?:benchmark\\w*|korpus\\w*)\\b"]],
        "required_capabilities": [],
        "optional_capabilities": ["filesystem", "code_execution"],
    },
    "brief-architect": {
        "release_status": "ACTIVE",
        "tier": "domain",
        "owns": ["artifact brief and execution contract", "observable acceptance criteria", "evidence policy and handoff fields"],
        "does_not_own": ["final artifact production", "broad product discovery", "consequential strategic decisions"],
        "trigger_examples": ["Turn this vague request into an executable brief", "Define acceptance criteria before we write the report"],
        "negative_trigger_examples": ["Write the final article", "Choose the product strategy"],
        "routing_signals": [[10, "\\b(?:turn|convert|shape)\\w*\\b.{0,30}\\binto (?:a |an )?(?:\\w+ )?brief\\b"], [10, "\\b(?:write|draft|create|prepare)\\b.{0,10}\\b(?:the |a )?brief (?:first|before)\\b"], [9, "\\b(?:audience|readers?|purpose|goal|scope)\\b.{0,30}\\b(?:audience|readers?|purpose|goal|scope)\\b.{0,40}\\b(?:evidence (?:rules|policy)|source policy|done.criteria|acceptance criteria|success criteria|definition of done)"], [10, "\\b(?:pin down|define|nail down|agree on|settle|clarify|spell out|lock down)\\b.{0,40}\\b(?:audience|readers?|scope|goal|objective|done.criteria|definition of done|acceptance criteria|success criteria|source policy|evidence policy)\\b.{0,60}\\b(?:audience|readers?|scope|goal|objective|criteria|policy)\\b"], [8, "\\b(?:too )?(?:fuzzy|vague|unclear|underspecified)\\b.{0,40}\\b(?:request|ask|assignment|task|commission)\\b"], [10, "\\b(?:ustal|ustalmy|okresl|zdefiniuj|doprecyzuj|spisz)\\w*\\b.{0,40}\\b(?:odbiorc|grup\\w* docelow|cel\\b|kryteri|polityk\\w* zrodel|zakres)\\w*.{0,60}\\b(?:odbiorc|cel\\b|kryteri|polityk|zakres)"], [10, "(write|draft|create) (a|the) (content |research |writing )?brief for|brief before (anyone|we) (starts? )?(writ|research)"], [20, "vague request.*executable brief|acceptance criteria before|vague.*(ebook|report|guide).*artifact brief"], [12, "brief architect|artifact brief"], [10, "turn this vague request into a brief"], [9, "acceptance criteria before (writing|research|production)"], [8, "evidence policy.*handoff"], [7, "underspecified.*(artifact|report|guide)"], [10, "\\b(?:executable|execution|artifact) contract\\b"], [10, "\\b(?:rozpisz|napisz|przygotuj|zrob|stworz|uloz|opracuj)\\w*\\b.{0,40}\\bbrief\\w*\\b.{0,40}\\b(?:zanim|przed)\\b|\\b(?:rozpisz|ulozyc|uloz|zrob|przygotuj|stworz)\\w*\\b.{0,30}\\b(?:porzadny|konkretny|jasny|dobry|pelny)\\w* brief|\\bkontrakt\\w* (?:wykonawcz|realizacyjn)\\w*|\\bdoprecyzuj\\w*\\b.{0,40}\\b(?:zlecenie|zadanie|prosbe|brief|zamowienie|zapytanie)|\\b(?:ustal|ustalmy|zdefiniuj|spisz|okresl)\\w*\\b.{0,40}\\bkryteri\\w* akceptacji\\b"], [10, "\\bbrief\\w*\\b.{0,40}\\b(?:odbiorc|grup\\w* docelow|kryteri\\w* (?:odbioru|akceptacji|sukcesu))"]],
        "required_capabilities": [],
        "optional_capabilities": ["filesystem", "code_execution", "files"],
    },
    "content-reviewer": {
        "release_status": "ACTIVE",
        "tier": "domain",
        "owns": ["constructive content review", "evidence-backed editorial findings", "review coverage and repair direction"],
        "does_not_own": ["adversarial roasting", "full content rewrites", "final publication acceptance"],
        "trigger_examples": ["Review this draft against its brief", "Give me actionable editorial QA before publication"],
        "negative_trigger_examples": ["Brutally roast this landing page", "Rewrite the whole article"],
        "routing_signals": [[9, "\\breview\\b.{0,40}\\b(?:page|faq|docs?|documentation|copy|post|article|guide|chapter|draft|section)\\b.{0,40}\\bfor (?:clarity|accuracy|consistency|readability|completeness|structure|gaps|missing)"], [9, "\\bwhere (?:the|my|its|our) (?:argument|logic|structure|flow|reasoning)\\b.{0,20}\\b(?:is |gets |feels )?(?:weak|unclear|confusing|breaks|thin)"], [10, "\\b(?:editorial|constructive) (?:notes|feedback|pass|comments|review)\\b"], [9, "\\b(?:review|feedback on|notes on)\\b.{0,40}\\b(?:draft|chapter|article|guide|whitepaper|white paper|post|section)\\b.{0,80}\\b(?:clarity|structure|flow|gaps?|brief|reader|usefulness|consisten\\w*)\\b"], [10, "\\b(?:ocen|przejrzyj|zrecenzuj|sprawdz)\\w*\\b.{0,40}\\b(?:szkic|artykul|rozdzial|poradnik|wpis|tekst|dokumentacj)\\w*\\b.{0,80}\\b(?:struktur|jasnos|czytelnik|briefem|briefu|niespojn|brakuj|niejasn|uwag)"], [9, "review (this|the|my) (article|blog post|guide|report|white paper|documentation|draft)"], [12, "content reviewer|editorial (review|qa)"], [10, "review this (draft|article|report).*brief"], [9, "pre.publication review|actionable editorial findings"], [8, "content.*(clarity|specificity|internal consistency).*review"], [7, "constructive review.*content"], [10, "\\breview (?:this|the|my) (?:draft|article|report|paragraph|section|text|copy|post|chapter)\\b.{0,40}\\bagainst (?:the|its|our|this) brief\\b"], [9, "\\b(?:przejrzyj|zrecenzuj|ocen|sprawdz)\\w*\\b.{0,40}\\b(?:artykul|tekst|szkic|wpis|poradnik|dokumentacj|raport|draft|rozdzial)\\w*\\b.{0,40}\\b(?:pod katem|wzgledem|wobec|zgodnie z)\\b.{0,15}\\bbrief|\\b(?:redakcyjn|merytoryczn)\\w* (?:korekt|recenzj|przeglad|uwag|qa|ocen)\\w*|\\brecenzj\\w*\\b.{0,30}\\b(?:tekstu|artykulu|wpisu|szkicu|poradnika|dokumentacji|raportu|rozdzialu)\\b|\\bkonstruktywn\\w*\\b.{0,30}\\b(?:ocen|recenzj|przejrz|uwag|feedback)|\\b(?:ocen|przejrz|recenzj)\\w*\\b.{0,30}\\bkonstruktywn|\\b(?:zyczliw|lagodn)\\w*\\b.{0,40}\\b(?:recenzj|ocen|przeglad|uwag)|\\b(?:recenzj|ocen|przeglad)\\w*\\b.{0,40}\\b(?:zyczliw|lagodn)"]],
        "required_capabilities": [],
        "optional_capabilities": ["filesystem", "code_execution", "web", "files"],
    },
    "content-roaster": {
        "release_status": "ACTIVE",
        "tier": "domain",
        "owns": ["adversarial content review", "proof-debt and claim-pressure diagnosis", "repair verification contracts"],
        "does_not_own": ["scientific peer review", "repository/code critique", "rewrite-only editing"],
        "trigger_examples": ["Roast this landing page with evidence", "Red-team the claims and objections in this offer"],
        "negative_trigger_examples": ["Peer-review this scientific manuscript", "Audit the repository code"],
        "routing_signals": [[14, "content roaster|content roast|roast.*(landing page|offer|article|copy)"], [12, "red.team.*(content|copy|offer)"], [10, "adversarial.*(content|marketing|sales) review"], [9, "proof debt|claim.*counterevidence.*repair"], [8, "brutal.*critique.*(copy|content|page)"], [12, "(?:roast|tear (?:it |this |them )?apart|rip (?:it )?apart|red.team|stress.test|poke holes in|(?:brutal|harsh|ruthless|savage)(?:ly)? (?:critique|review|roast)).{0,60}(?:\\b(?:landing|pricing|product|home|sales|procurement|trust|comparison|trial|feature)[ -]?page|\\b(?:e-?mails?|newsletter|outbound|sales deck|pitch deck|deck|post|linkedin|blog|article|case study|one.pager|brochure|ad copy|headline|cta|offer|copy|messaging|positioning|(?:marketing|sales|launch|product) claims?)\\b)"], [18, "(?:roast|tear (?:it |this |them )?apart|rip (?:it )?apart|red.team|stress.test|poke holes in|(?:brutal|harsh|ruthless|savage)(?:ly)? (?:critique|review|roast)).{0,60}\\b(?:e-?book|white.?paper|lead magnet)"], [11, "\\b(?:re-?check|re-?review|re-?roast|re-?audit).{0,40}(?:landing page|homepage|pricing page|product page|sales page|\\bcopy\\b|\\boffer\\b|e-?mail|\\bdeck\\b|case stud|announcement|\\barticle|blog post|newsletter|white ?paper|e-?book|lead magnet)"], [10, "\\bproof (?:gaps?|audit|burden)\\b"], [6, "skeptical (?:b2b |enterprise |procurement )?(?:buyer|customer|prospect)"], [12, PL_ROAST + ".{0,60}(?:ofert|stron|landing|cennik|maila?\\b|e-?mail|wpis|post|artykul(?! naukow)|deck|prezentacj|copy|case study|ebook|newsletter)"]],
        "required_capabilities": [],
        "optional_capabilities": ["filesystem", "code_execution", "web", "files"],
    },
    "content-writer": {
        "release_status": "ACTIVE",
        "tier": "domain",
        "owns": ["evidence-aware content production", "claim-discipline ledger", "reader-facing informational artifacts"],
        "does_not_own": ["persuasion-first campaign copy", "primary evidence research", "publication release orchestration"],
        "trigger_examples": ["Write the evidence-backed guide from this brief", "Create the reader-facing report without inventing claims"],
        "negative_trigger_examples": ["Humanize this paragraph only", "Run the primary research first"],
        "routing_signals": [[10, "\\b(?:write|draft|create|produce|compose)\\w*\\b.{0,40}\\b(?:explainer|article|guide|post|overview|whitepaper|white paper)\\b.{0,80}\\b(?:citing|cite|cites|with|backed by|using)\\s{1,3}(?:\\w{1,20}\\s{1,3}){0,2}?sources\\b"], [10, "\\b(?:write|draft|create|produce|compose)\\w*\\b.{0,30}\\b(?:well.sourced|sourced|cited|fact.checked|referenced)\\b.{0,20}\\b(?:explainer|article|guide|post|report|overview)"], [10, "\\b(?:write|draft|create|produce|compose)\\w*\\b.{0,30}\\b(?:research|evidence).backed (?:guide|article|explainer|report|post)|\\b(?:notes|interview notes|transcripts?)\\b.{0,20}\\binto\\b.{0,30}\\b(?:article|guide|explainer|documentation|doc page|knowledge.base)"], [12, "content writer|write.*(evidence.backed|informational|evidence.aware) (guide|report|article|explainer article)"], [10, "create.*reader.facing (artifact|report|guide)"], [9, "write.*from this brief.*(article|report|documentation)"], [8, "claim.discipline.*(draft|content)"], [7, "evidence.aware.*(prose|content)"], [10, "\\b(?:napisz|przygotuj|stworz|zredaguj|opracuj)\\w*\\b.{0,40}\\b(?:artykul|wpis|tekst|poradnik|dokumentacj|przewodnik|explainer|opis)\\w*\\b.{0,80}\\b(?:na podstawie|z (?:tego|tych|moich|naszych) (?:briefu|notatek|materialow)|ze zrodl|zrodlami|rzetelni|bez wymysl|rejestr\\w* twierdzen)"]],
        "required_capabilities": [],
        "optional_capabilities": ["filesystem", "code_execution", "web", "files"],
    },
    "feedback-integrator": {
        "release_status": "ACTIVE",
        "tier": "foundation",
        "owns": ["recurrent failure pattern synthesis", "evidence-backed improvement proposals", "regression test proposals"],
        "does_not_own": ["silent self-modification", "single-signal generalization", "product or research analytics"],
        "trigger_examples": ["Turn repeated skill failures into a regression plan", "Run a retrospective across these quality incidents"],
        "negative_trigger_examples": ["Patch the skill silently from one correction", "Analyze product retention"],
        "routing_signals": [[10, "\\b(?:users?|reviewers?) corrected\\b.{0,40}\\bskills?\\b|\\bskill outputs?\\b.{0,60}\\binstruction changes?"], [10, "\\bkeeps? (?:going wrong|failing|breaking)\\b.{0,40}\\bskills?\\b|\\bskills?\\b.{0,60}\\bkeeps? (?:going wrong|failing|breaking)"], [9, "\\bacross (?:the )?(?:last|past) \\w+ (?:skill runs|runs|acceptance failures|failures|evals|incidents)\\b"], [10, "\\b(?:same|recurring|repeated)\\b.{0,30}\\b(?:mistakes?|errors?|failures?|findings?|problems?)\\b.{0,100}\\b(?:skills?|instructions?|regression tests?|evals?|runs?|routing)\\b"], [10, "\\bretro(?:spective)?\\b.{0,60}\\b(?:eval|skill|run|routing|acceptance|quality)\\w*\\b.{0,20}\\b(?:failures?|incidents?|mistakes?|corrections?)"], [10, "recurring (failure patterns?|mistakes|findings)|same mistakes across"], [9, "\\b(?:eval|skill) runs?\\b.{0,40}\\bfail\\w*|\\bskill improvements?\\b"], [20, "retrospective.*quality incidents"], [12, "feedback integrator|\\bintegrat\\w*\\b.{0,40}\\bfeedback\\b.{0,60}\\b(?:skills?|skill runs?|evals?|routing|instructions|regression tests?)\\b|aggregate recurring reviewer findings"], [10, "repeated.*(skill failure|quality failure|user correction)"], [9, "retrospective.*(skill|quality workflow)"], [8, "failure pattern.*regression test"], [7, "improve reliability.*repeated incidents"], [10, "\\b(?:te same|powtarzaj\\w*|wracaj\\w*|ciagle|stale|nawracaj\\w*)\\b.{0,40}\\b(?:bled|uwag|porazk|poprawk|problem|znalezisk|poprawiaj|wpadk)\\w*\\b.{0,100}\\b(?:skill|agent|ewaluac|eval|przebieg|instrukcj|routing|recenzent|regresyjn|wzorzec|wzorc)|\\bretrospektyw\\w*\\b.{0,60}\\b(?:skill|agent|ewaluac|eval|przebieg|instrukcj|jakosc|porazk)|\\b(?:zbierz|zagreguj)\\w*\\b.{0,30}\\bpowtarzaj\\w*"]],
        "required_capabilities": [],
        "optional_capabilities": ["filesystem", "code_execution", "git"],
    },
    "quality-loop-operator": {
        "release_status": "ACTIVE",
        "tier": "foundation",
        "owns": ["quality workflow state and sequencing", "specialist handoffs and revalidation", "quality rollout lifecycle"],
        "does_not_own": ["general multi-skill orchestration", "consequential strategy decisions", "software production-readiness verdicts"],
        "trigger_examples": ["Run the full content quality loop", "Resume this quality workflow from the last accepted stage"],
        "negative_trigger_examples": ["Orchestrate an unrelated product workflow", "Give a software release GO/NO_GO"],
        "routing_signals": [[10, "\\bbrief\\b.{0,30}\\breview\\b.{0,40}\\brepair\\b.{0,30}\\baccept"], [12, "\\b(?:kick off|start|launch|resume|restart|drive)\\b.{0,20}\\b(?:the |a )?(?:full |complete )?quality (?:loop|workflow)\\b"], [11, "\\b(?:canary|staged rollout)\\b.{0,80}\\b(?:skill|candidate)\\b|\\b(?:skill|candidate)\\b.{0,80}\\b(?:canary|staged rollout)"], [20, "full content quality loop"], [14, "quality loop operator|quality workflow|full artifact quality loop"], [12, "full quality loop|resume.*quality workflow"], [10, "brief.*review.*roast.*repair.*acceptance"], [9, "quality.*(revalidation|rollout|rollback)"], [8, "coordinate quality specialists"], [12, "run (?:the )?(?:full |complete |whole |entire )?quality loop|\\bquality loop\\b.{0,60}(brief|review|roast|repair|accept)"], [12, "\\bpetl\\w* jakosci|\\bcykl\\w* jakosci|\\bspecjalist\\w* (?:od |ds\\.? )?jakosci"]],
        "required_capabilities": [],
        "optional_capabilities": ["filesystem", "code_execution", "git", "web", "files"],
    },
    "repair-operator": {
        "release_status": "ACTIVE",
        "tier": "domain",
        "owns": ["finding-to-repair planning", "authorized bounded repairs", "fresh repair verification"],
        "does_not_own": ["initial broad audit", "inventing new requirements", "production release verdicts"],
        "trigger_examples": ["Turn these review findings into the smallest repair set", "Apply the authorized fixes and verify they close the root cause"],
        "negative_trigger_examples": ["Audit the whole repo from scratch", "Decide whether the release is ready"],
        "routing_signals": [[11, "\\b(?:address|fix|repair|close|resolve)\\w*\\b.{0,20}\\b(?:the |all |these )?(?:accepted |open |approved )?findings\\b.{0,30}\\bfrom\\b.{0,20}\\b(?:[\\w-]+ )?(?:review|audit|roast|acceptance|qa)\\b"], [11, "\\b(?:fix|repair|address|resolve|close)\\w*\\b.{0,30}\\b(?:everything|all|each|the issues?|what)\\b.{0,20}\\b(?:the )?(?:reviewers?|auditors?|roasters?|audit|review|qa)\\b.{0,10}\\b(?:flagged|found|raised|reported|caught)"], [12, "\\b(?:napraw|popraw|zamknij|wdroz)\\w*\\b.{0,60}\\b(?:z|po|wynik\\w*)\\b.{0,30}\\b(?:audyt|recenzj|review|roast|przeglad|odbior|akceptacj)\\w*|\\b(?:napraw|popraw)\\w*\\b.{0,40}\\b(?:co )?(?:wyszl\\w*|znalazl\\w*|wykazal\\w*)\\b.{0,20}\\b(?:w |z |po )?(?:roasc|roast|audyt|recenzj|review|przeglad)\\w*"], [10, "\\b(?:najmniejsz|minimaln)\\w* zestaw\\w* (?:poprawek|zmian|napraw)|\\bminimal (?:patch|fix|repair) set|\\bfindings\\b.{0,60}\\b(?:into|to) (?:a )?(?:minimal |smallest )?(?:patch|fix|repair) set"], [20, "authorized fixes.*verify.*root cause"], [12, "repair operator|repair set|repair the accepted review findings"], [10, "fix these findings.*(root cause|verify)"], [9, "convert.*findings.*(repair|patch)"], [8, "authorized.*(repair|fix).*fresh verification"], [7, "close.*finding.*without regressions"], [10, "\\brepair (?:the )?findings?\\b"], [10, "(fix|repair|close) (the |these |all )?(accepted )?(review|roast|audit|acceptance) findings"], [10, "apply (the )?fixes (from|for) (the |this |that )?(last |latest )?(review|roast|audit|acceptance)"], [12, "\\b(?:napraw|popraw|wdroz|wprowadz|zamknij|zamien)\\w*\\b.{0,60}\\b(?:uwag|znalezisk|bled|poprawk|problem)\\w*\\b.{0,40}\\b(?:z|po)\\b.{0,5}\\b(?:code review|recenzj|review|audyt|roast|przeglad|odbior|akceptacj)|\\b(?:zaakceptowan|zatwierdzon)\\w* (?:uwag|znalezisk|poprawk|bled)\\w*|\\b(?:uwag|znalezisk|bled)\\w*\\b.{0,40}\\b(?:ktore|co) (?:zatwierdzil|zaakceptowal)|\\bplan\\w* naprawcz|\\b(?:znalezisk|uwag)\\w*\\b.{0,60}\\bnapraw\\w*"]],
        "required_capabilities": [],
        "optional_capabilities": ["filesystem", "code_execution", "git"],
    },
    "repo-roaster": {
        "release_status": "ACTIVE",
        "tier": "domain",
        "owns": ["adversarial repository review", "critical-invariant and reachability analysis", "executable engineering repair contracts"],
        "does_not_own": ["whole-project roadmapping", "runtime web QA", "final production release verdicts"],
        "trigger_examples": ["Roast this repository with file and test evidence", "Red-team the critical invariants and failure paths in this codebase"],
        "negative_trigger_examples": ["Create the whole-project roadmap", "Decide whether the release can ship"],
        "routing_signals": [[14, "repo roast|repository roast|roast.*(repo|codebase)|brutalny przeglad repo"], [12, "red.team.*(repository|codebase|software)"], [10, "adversarial.*(repository|codebase) review"], [9, "critical invariant.*(repo|code)"], [8, "file.*symbol.*reachability.*blast radius"], [12, "red.team (this|the|our|my) (pr|pull request)\\b|roast (this|the|our|my) (pr|pull request)\\b"], [12, "(?:roast|tear (?:it |this |them )?apart|rip (?:it )?apart|red.team|stress.test|poke holes in|(?:brutal|harsh|ruthless|savage)(?:ly)? (?:critique|review|roast)).{0,60}\\b(?:repo|repos|repository|repositories|codebase|monorepo|pull requests?|prs?|diff|branch|commits?|code)\\b"], [11, "\\b(?:re-?check|re-?review|re-?roast|re-?audit).{0,40}\\b(?:branch|prs?|pull requests?|repo|repository|codebase|diff|commits?)\\b|\\b(?:old|previous|earlier|prior|original) (?:repo|code|codebase) findings"], [10, "\\b(?:forensic|hostile|adversarial|brutal|ruthless) (?:repo|code|codebase|pr) (?:review|audit|roast)"], [10, "\\b(?:forensic|deep) (?:code |repo )?(?:review|audit)\\b.{0,40}\\b(?:worker|service|module|repo|repository|codebase|code|queue|handler|migration)s?\\b"], [6, "\\breview (?:this|the|our|my) .{0,30}\\b(?:repo|repository|codebase|monorepo|diff|pull request|pr|branch|commit)\\b"], [8, "\\b(?:repo|repository|codebase|monorepo|diff|pull request|pr|branch|code)\\b.{0,80}(?:trust boundar|blast radius|reachab|tenant isolation|idempoten|race condition|double.charge|tool.call|partial.failure|data.integrity)"], [12, PL_ROAST + ".{0,40}(?:\\brepo|repozytori|\\bkod|codebase|\\bpr\\b|pull request|\\bdiff|galez)"]],
        "required_capabilities": [],
        "optional_capabilities": ["filesystem", "code_execution", "git"],
    },
    "rubric-designer": {
        "release_status": "ACTIVE",
        "tier": "foundation",
        "owns": ["evaluation rubric design", "observable pass/fail evidence floors", "rubric revision hashes"],
        "does_not_own": ["judging the candidate", "writing the artifact", "running empirical skill benchmarks"],
        "trigger_examples": ["Design and freeze a review rubric before evaluation", "Define blocker rules and evidence floors for this benchmark"],
        "negative_trigger_examples": ["Score the candidate using the rubric", "Run the A/B experiment"],
        "routing_signals": [[10, "\\b(?:zaprojektuj|przygotuj|stworz|ustal|zdefiniuj|napisz|zbuduj)\\w*\\b.{0,30}\\bkryteri\\w* (?:oceny|oceniania|punktacji)|\\bzaliczeni\\w*\\b.{0,20}\\bniezaliczeni"], [10, "\\b(?:reviewer|review|grading|evaluation|assessment) scorecards?\\b"], [20, "define blocker rules.*evidence floors"], [12, "rubric designer|design.*(evaluation|review) rubric"], [10, "freeze.*rubric|rubric hash"], [9, "pass/fail.*(criteria|semantics)"], [8, "evidence floor.*(rubric|scorecard)"], [7, "blocker rules.*evaluation"], [10, "(create|design|build|write|draft|define).{0,40}\\b(grading|scoring|evaluation|review) (rubric|criteria|scorecard)"], [10, "\\brubryk\\w*|\\bkart\\w* ocen\\w*|\\bkryteri\\w* (?:pass/fail|zaliczenia)|\\bpass/fail\\b|\\bwarunk\\w* blokuj"]],
        "required_capabilities": [],
        "optional_capabilities": ["filesystem", "code_execution"],
    },
    "science-roaster": {
        "release_status": "ACTIVE",
        "tier": "domain",
        "owns": ["adversarial scientific peer review", "claim/evidence and validity analysis", "methodological repair verification"],
        "does_not_own": ["generic content critique", "repository/code review", "research-program planning"],
        "trigger_examples": ["Reviewer-2 roast this manuscript", "Red-team the methods, estimand, and validity of this study"],
        "negative_trigger_examples": ["Critique this marketing article", "Audit the software repository"],
        "routing_signals": [[12, "\\b(?:journal|peer|academic) referee\\b|\\breferee\\b.{0,40}\\b(?:paper|manuscript|meta.analysis|study|preprint|thesis)"], [12, "\\bkrytyczn\\w*\\b.{0,40}\\b(?:manuskrypt|preprint|metodolog|artykul\\w* naukow|prac\\w* (?:naukow|doktorsk|magistersk)|wnioski przyczynow)|\\b(?:manuskrypt|preprint|metodolog)\\w*\\b.{0,40}\\bkrytyczn|\\bwnios\\w* przyczynow"], [11, "\\b(?:critique|criticize|challenge|scrutini[sz]e)\\b.{0,40}\\b(?:statistic\\w*|causal claims?|methodology|methods|inference|study design)\\b.{0,60}\\b(?:paper|manuscript|preprint|study|thesis)\\b"], [14, "science roaster|scientific peer review|reviewer.{0,3}2|\\breviewer (?:#|no\\.? |number )?(?:2|two)\\b"], [10, "\\bauthors?'? response\\b|\\bresponse to (?:the )?reviewers\\b|\\brebuttal letter\\b"], [12, "roast.*(manuscript|(?<!white )paper|(?<!case )study|protocol)"], [10, "red.team.*(scientific|study|method|validation (?:split|study|design|set)|confound)"], [9, "estimand.*validity.*(review|critique)"], [8, "methodological.*(repair|counterevidence)"], [12, "re-?review.{0,30}(revised|revision of).{0,20}(paper|manuscript|(?<!case )study)|peer.review (my|this|the|our) (paper|manuscript|study)"], [12, "(?:roast|tear (?:it |this |them )?apart|rip (?:it )?apart|red.team|stress.test|poke holes in|(?:brutal|harsh|ruthless|savage)(?:ly)? (?:critique|review|roast)).{0,60}\\b(?:manuscript|preprint|(?<!white )paper|thesis|dissertation|grant (?:proposal|application)|preregistration|meta.analysis|systematic review|(?<!case )study|(?:clinical|randomi[sz]ed|controlled) trial|causal (?:inference|claims?)|statistical (?:analysis|inference|claims?)|survival analysis|methods section)\\b"], [10, "\\bpeer.review(?:er)? .{0,40}\\b(?:paper|manuscript|preprint|study|analysis|thesis|grant|protocol|trial|methods|meta.analysis)\\b|\\b(?:hostile|harsh|critical|hypercritical|skeptical) (?:peer|journal|academic|scientific) reviewer"], [12, PL_ROAST + ".{0,60}(?:naukow|manuskrypt|(?<!wyniki )(?<!wynikow )(?<!wynikach )badani|preprint|rozpraw|grantow|protokol|prac\\w* (?:magistersk|doktorsk|licencjack|naukow))"], [10, "(?:hiper)?krytyczn\\w* recenzent|recenzent\\w* (?:nr |numer |#)?2\\b"]],
        "required_capabilities": [],
        "optional_capabilities": ["filesystem", "code_execution", "web", "files"],
    },
    "skill-auditor": {
        "release_status": "ACTIVE",
        "tier": "foundation",
        "owns": ["skill package audits", "routing, portability, and contract review", "package and supply-chain hygiene"],
        "does_not_own": ["editing the audited skill", "empirical behavioral benchmarking", "production release verdicts"],
        "trigger_examples": ["Audit this Agent Skill package for routing and portability risks", "Quality-check the skill library before publication"],
        "negative_trigger_examples": ["Edit the skill instructions", "Benchmark model behavior with and without the skill"],
        "routing_signals": [[11, "\\bskills?\\b.{0,80}\\b(?:scope overlap|trigger overlap|overlapping triggers|eval blind spots?|package hygiene|supply.chain)|\\b(?:scope overlap|trigger overlap|overlapping triggers|eval blind spots?|package hygiene|supply.chain)\\w*\\b.{0,80}\\bskills?\\b"], [11, "\\b(?:audit|review|check|harden)\\w*\\b.{0,40}\\b(?:agent )?skills? (?:repo|repository|library|catalog)\\b"], [20, "quality.check.*skill library"], [12, "skill auditor|audit.*(agent skill|skill package|skill library)|zaudytuj biblioteke skilli|przeanalizuj.{0,80}repo.{0,20}agent[ -]skills|(?:audyt|przejrzyj|zweryfikuj jakosc).{0,80}(?:skilli|katalogu umiejetnosci agentow)|sprawdz.{0,80}skill-[a-z-]+.{0,80}(?:test|kolid|routing)"], [10, "skill.*(routing|portability|package hygiene).*audit"], [9, "audit.*skill.*(trigger|reference|eval)"], [8, "supply.chain.*skill|public.*skill.*hardening"], [7, "skill registry.*drift.*audit"], [10, "\\b(?:kolizj|konflikt|nachodz)\\w*\\b.{0,40}\\b(?:wyzwalacz|triggerow|opisow skilli|skilli)|\\bhigien\\w* paczek|\\bpaczk\\w* skill|\\brejestr\\w* skilli|\\b(?:opisy|opisow) skilli\\b.{0,40}\\b(?:nachodz|pokrywa|routing)|\\bskill\\w*\\b.{0,60}\\b(?:kolizj|nachodz|przenosnos|wyzwalacz)"]],
        "required_capabilities": [],
        "optional_capabilities": ["filesystem", "code_execution", "git"],
    },
    "skill-evaluator": {
        "release_status": "ACTIVE",
        "tier": "foundation",
        "owns": ["skill experiment design", "behavioral lift and resource measurement", "host and model comparisons"],
        "does_not_own": ["static package audits", "editing the skill", "universal superiority claims"],
        "trigger_examples": ["Measure whether this skill improves behavior over the baseline", "Design a fair A/B eval for the new skill version"],
        "negative_trigger_examples": ["Static-audit the package", "Claim this skill is universally best from one run"],
        "routing_signals": [[10, "\\bwith.(?:versus|vs\\.?|and).without\\b|\\b(?:with|without) (?:the )?skill (?:loaded|enabled|vs|versus)"], [20, "measure whether this skill improves behavior over the baseline"], [12, "skill evaluator|\\bevaluat\\w*\\b.{0,40}\\b(?:this|the|our|new|agent|an?) (?:[\\w-]{1,40} )?skill\\b(?! gaps?\\b| levels?\\b| sets?\\b)"], [12, "\\b(?:measure|test|check|experiment\\w*)\\b.{0,60}\\bskill\\b.{0,40}\\b(?:improves?|lifts?|helps?|better than|beats?|baseline)\\b"], [10, "benchmark.*(skill|model behavior)|A/B.*skill"], [9, "measure.{0,40}(?:behavioral lift|trigger (?:precision|recall)|(?:discovery|trigger|routing) (?:rate|accuracy)|trigger precision and recall)"], [8, "compare.*(no.skill|baseline).*skill|\\bcompar\\w*\\b.{0,40}\\bskill\\b.{0,60}\\b(?:no.skill|baseline|prior version)\\b"], [7, "host/model.*(comparison|experiment)"], [10, "\\b(?:zmierz|porownaj|sprawdz|przetestuj)\\w*\\b.{0,60}\\bskill\\w*\\b.{0,60}\\b(?:lepsz|gorsz|daje|pomaga|bazow|baseline|bez skilla|a/b)|\\bczy (?:ten |nowy |nasz )?skill\\b.{0,30}\\b(?:cokolwiek |w ogole |cos )?(?:daje|pomaga|dziala lepiej)|\\b(?:precyzj|czulos)\\w*\\b.{0,40}\\bwyzwalan|\\bskill\\w*\\b.{0,60}\\b(?:bazow\\w* model|bez skilla)"]],
        "required_capabilities": [],
        "optional_capabilities": ["filesystem", "code_execution", "git"],
    },
}


def default_entry(skill_id: str) -> dict:
    version, description = package_identity(skill_id)
    spec = OVERRIDES[skill_id]
    return {
        "id": skill_id,
        "version": version,
        "lifecycle": "active",
        "visibility": "public_canonical",
        "tier": spec["tier"],
        "alias_of": None,
        "description": description,
        "explicit_only": False,
        "owns": spec["owns"],
        "does_not_own": spec["does_not_own"],
        "trigger_examples": spec["trigger_examples"],
        "negative_trigger_examples": spec["negative_trigger_examples"],
        "inputs": ["user goal"],
        "outputs": ["skill-specific artifact"],
        "dependencies": [],
        "compatible_hosts": list(HOST_TARGETS),
        "host_targets": list(HOST_TARGETS),
        "required_capabilities": list(spec["required_capabilities"]),
        "optional_capabilities": list(spec["optional_capabilities"]),
        "execution_capabilities": ["standard"],
        "eval_suite": None,
        "release_status": spec["release_status"],
        "routing_signals": spec["routing_signals"],
    }


def pending_packages() -> list[str]:
    """Overrides whose package body has not landed on disk yet.

    The metadata for a release is written here before the package itself is
    staged, so an override without a SKILL.md is a package still in flight,
    not a broken repo. Skip it instead of crashing on the missing file.
    """
    return sorted(
        skill_id
        for skill_id in OVERRIDES
        if not (SKILLS / skill_id / "SKILL.md").is_file()
    )


def desired_registry(current: dict) -> dict:
    result = deepcopy(current)
    by_id = {entry["id"]: entry for entry in result["skills"]}
    pending = set(pending_packages())
    for skill_id, spec in OVERRIDES.items():
        if skill_id in pending:
            continue
        version, description = package_identity(skill_id)
        if skill_id not in by_id:
            entry = default_entry(skill_id)
            result["skills"].append(entry)
            by_id[skill_id] = entry
        entry = by_id[skill_id]
        entry["version"] = version
        entry["description"] = description
        entry["release_status"] = spec["release_status"]
        entry["host_targets"] = list(HOST_TARGETS)
        entry["compatible_hosts"] = list(HOST_TARGETS)
        entry["required_capabilities"] = list(spec["required_capabilities"])
        entry["optional_capabilities"] = list(spec["optional_capabilities"])
        if skill_id != "product-operator":
            for key in ("tier", "owns", "does_not_own", "trigger_examples", "negative_trigger_examples", "routing_signals"):
                entry[key] = deepcopy(spec[key])
    result["skills"] = sorted(result["skills"], key=lambda entry: entry["id"])
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    current = json.loads(REGISTRY.read_text(encoding="utf-8"))
    pending = pending_packages()
    if pending:
        print(f"PENDING: package not on disk, skipped: {', '.join(pending)}")
    desired = desired_registry(current)
    rendered = json.dumps(desired, ensure_ascii=False, indent=2) + "\n"
    existing = REGISTRY.read_text(encoding="utf-8")
    if args.check:
        if existing != rendered:
            print("FAIL: registry/skills.json is not synchronized")
            return 1
        print("OK: registry/skills.json synchronized")
        return 0
    REGISTRY.write_text(rendered, encoding="utf-8")
    print(f"OK: synchronized {len(OVERRIDES) - len(pending)} authoritative releases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
