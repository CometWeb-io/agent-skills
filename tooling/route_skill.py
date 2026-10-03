#!/usr/bin/env python3
"""Deterministic routing diagnostics; not a model evaluator or a permission boundary.

Only pass the user's instruction, not the contents of retrieved documents.
"""
from __future__ import annotations
import argparse
from functools import lru_cache
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.casefold()).replace("ł", "l")
    return "".join(ch for ch in text if not unicodedata.combining(ch))


@lru_cache(maxsize=1024)
def _pattern(pattern: str):
    if not isinstance(pattern, str) or not pattern or len(pattern) > 4096:
        raise ValueError("invalid routing pattern")
    # Never casefold regex source: \\S/\\s, \\D/\\d and \\B/\\b are different operators.
    normalized = unicodedata.normalize("NFKD", pattern).replace("ł", "l").replace("Ł", "L")
    normalized = "".join(c for c in normalized if not unicodedata.combining(c))
    # Reject nested quantifiers that enable catastrophic backtracking on user prompts.
    if re.search(r"(?:\([^)]*[+*][^)]*\)|[+*])[+*{]", normalized):
        raise ValueError("unsafe nested quantifier in routing pattern")
    try:
        return re.compile(normalized, re.IGNORECASE)
    except re.error as exc:
        raise ValueError("invalid routing regular expression") from exc


def matches(pattern: str, text: str) -> bool:
    return _pattern(pattern).search(text) is not None


def _catalog(registry: dict, policy: dict) -> dict:
    if not isinstance(policy, dict) or policy.get("schema") != "cometweb.routing-policy/v1":
        raise ValueError("unsupported routing policy")
    if not isinstance(registry, dict) or not isinstance(registry.get("skills"), list) or not 1 <= len(registry['skills']) <= 500:
        raise ValueError("invalid registry")
    all_skills = {}
    for entry in registry["skills"]:
        if not isinstance(entry, dict):
            raise ValueError("invalid skill entry")
        sid = entry.get("id")
        if not isinstance(sid, str) or len(sid) > 64 or not ID.fullmatch(sid) or sid in all_skills:
            raise ValueError("invalid or duplicate skill identifier")
        if type(entry.get("explicit_only", False)) is not bool:
            raise ValueError("explicit_only must be a boolean")
        signals = entry.get("routing_signals", [])
        if not isinstance(signals, list):
            raise ValueError("signals must be a list")
        for signal in signals:
            if not isinstance(signal, (list, tuple)) or len(signal) != 2 or type(signal[0]) is not int or not 1 <= signal[0] <= 10000:
                raise ValueError("invalid routing signal")
            _pattern(signal[1])
        all_skills[sid] = entry
    for sid in all_skills:
        seen, current = set(), sid
        while current:
            if not isinstance(current, str) or current not in all_skills or current in seen:
                raise ValueError("missing or cyclic alias target")
            seen.add(current)
            current = all_skills[current].get("alias_of")
    for field in ("explicit_patterns", "denied_patterns"):
        group = policy.get(field, {})
        if not isinstance(group, dict):
            raise ValueError("invalid pattern group")
        for patterns in group.values():
            if not isinstance(patterns, list):
                raise ValueError("pattern group requires lists")
            for pattern in patterns:
                _pattern(pattern)
    guards = policy.get("narrow_intent_guards", {})
    if not isinstance(guards, dict):
        raise ValueError("invalid narrow intent guards")
    for guard in guards.values():
        if not isinstance(guard, dict) or not {"when", "unless"} <= guard.keys():
            raise ValueError("invalid narrow intent guard")
        _pattern(guard["when"]); _pattern(guard["unless"])
    _negation_rules(policy)
    workflow = policy.get("workflow_skill")
    if not isinstance(workflow, str) or not ID.fullmatch(workflow):
        raise ValueError("invalid workflow identifier")
    return {sid:entry for sid,entry in all_skills.items() if entry.get("lifecycle") == "active"}


def _negation_rules(policy: dict):
    """Validate and return (cues, boundary, max_scope_chars), or None when unset."""
    rules = policy.get("negation")
    if rules is None:
        return None
    if not isinstance(rules, dict) or not {"cues", "boundary", "max_scope_chars"} <= rules.keys():
        raise ValueError("invalid negation rules")
    cues, boundary, cap = rules["cues"], rules["boundary"], rules["max_scope_chars"]
    if not isinstance(cues, list) or not 1 <= len(cues) <= 32 or type(cap) is not int or not 1 <= cap <= 400:
        raise ValueError("invalid negation rules")
    return tuple(_pattern(c) for c in cues), _pattern(boundary), cap


def negated_spans(text: str, policy: dict) -> list[tuple[int, int]]:
    """Character ranges of ``text`` that sit inside a negated clause.

    A clause is the text between two boundary matches (punctuation, contrast or
    subordinating words such as "but", "just", "until", "tylko", "zanim"). The
    first cue found in a clause negates from the end of the cue to the end of
    that clause, capped at ``max_scope_chars``. Cues anchored with ``^`` only
    fire at the start of a clause, which keeps "find what's not working" or
    "sprawdz, czy strona nie dziala" out of scope.
    """
    rules = _negation_rules(policy)
    if rules is None:
        return []
    cues, boundary, cap = rules
    cuts = [0]
    for m in boundary.finditer(text):
        cuts.extend((m.start(), m.end()))
    cuts.append(len(text))
    spans = []
    for start, end in zip(cuts[::2], cuts[1::2], strict=True):
        clause = text[start:end]
        hits = [m.end() for cue in cues if (m := cue.search(clause))]
        if hits:
            begin = start + min(hits)
            if begin < end:
                spans.append((begin, min(end, begin + cap)))
    return spans


def mask_negated(text: str, policy: dict) -> str:
    """Blank negated clause text so routing signals cannot match inside it.

    Blanking (rather than checking where a match starts) also stops a greedy
    signal such as ``roast.*codebase`` from starting in a positive clause and
    reaching into a negated one. Offsets are preserved.
    """
    out = text
    for start, end in negated_spans(text, policy):
        out = out[:start] + " " * (end - start) + out[end:]
    return out


def _denied_by_name(sid: str, text: str) -> bool:
    # Bound the prohibition to a named skill, not the rest of the paragraph.
    lead = r"(?:\b(?:do not|don['’]?t|never)\s+(?:use|run|load|invoke|activate)\s+|\b(?:without|no)\s+(?:using\s+)?|\bnie\s+(?:uzywaj|uruchamiaj|wlaczaj|korzystaj z)\s+|\bbez\s+)"
    return re.search(lead + r"(?:the\s+)?[$@]?" + re.escape(sid) + r"(?![\w-])", text) is not None


def route(prompt: str, registry: dict, policy: dict, *, invoked: tuple[str, ...] = ()) -> dict:
    active = _catalog(registry, policy)
    if not isinstance(prompt, str) or len(prompt) > 65536 or not isinstance(invoked, (tuple, list)) or any(not isinstance(s, str) for s in invoked):
        raise ValueError("invalid routing request")
    text = normalize(prompt)
    signal_text = mask_negated(text, policy)
    if any(sid not in active for sid in invoked):
        raise ValueError("explicit invocation references an unavailable skill")
    explicit, scores, blocked = set(invoked), {}, {}
    for sid in active:
        if re.search(r"(?<![\w-])[$@]" + re.escape(sid) + r"(?![\w-])", text):
            explicit.add(sid)
        # Natural "use product-operator" / "run evidence-researcher" invocations.
        if re.search(
            r"(?<![\w-])(?:use|run|invoke|load)\s+(?:the\s+)?" + re.escape(sid) + r"(?![\w-])",
            text,
        ):
            explicit.add(sid)
        if any(matches(p, text) for p in policy.get("explicit_patterns", {}).get(sid, [])):
            explicit.add(sid)
        if _denied_by_name(sid, text) or any(matches(p, text) for p in policy.get("denied_patterns", {}).get(sid, [])):
            blocked[sid] = "explicitly_excluded"
    # A thin alias must not bypass exclusion or unavailability of its canonical skill.
    for sid, entry in active.items():
        current = entry.get("alias_of")
        while current:
            if current not in active:
                blocked[sid] = "canonical_skill_unavailable"
                break
            if blocked.get(current) == "explicitly_excluded":
                blocked[sid] = "explicitly_excluded"
                break
            current = active[current].get("alias_of")
    for sid, entry in active.items():
        if sid in blocked:
            explicit.discard(sid)
            continue
        if entry.get("explicit_only") and sid not in explicit:
            blocked[sid] = "requires_explicit_invocation"
            continue
        guard = policy.get("narrow_intent_guards", {}).get(sid)
        # A negated exception ("don't humanize it") must not lift the guard.
        if guard and sid not in explicit and matches(guard["when"], text) and not matches(guard["unless"], signal_text):
            blocked[sid] = "outside_declared_scope"
            continue
        # Explicit invocations and exclusions keep their own rules.
        total = sum(weight for weight, pattern in entry.get("routing_signals", []) if matches(pattern, signal_text))
        if total or sid in explicit:
            scores[sid] = total
    def _canonical(sid: str) -> str:
        current = sid
        seen: set[str] = set()
        while current in active and current not in seen:
            seen.add(current)
            alias = active[current].get("alias_of")
            if not alias:
                return current
            current = alias
        return current

    workflow = policy["workflow_skill"]
    candidates = sorted(explicit & scores.keys())
    if not candidates and scores:
        highest = max(scores.values())
        # Exact top score first. Near-ties among incompatible specialists (within
        # one point of the highest) must not silently collapse to the winner.
        top = [sid for sid, score in scores.items() if score == highest]
        near = [sid for sid, score in scores.items() if score >= highest - 1]
        specialist_canons = {
            _canonical(sid) for sid in near if _canonical(sid) != workflow
        }
        if len(specialist_canons) > 1:
            candidates = sorted(sid for sid in near if _canonical(sid) != workflow)
        else:
            candidates = sorted(top)
    primary, kind = None, "no_skill"
    if len(candidates) > 1:
        if len(explicit & scores.keys()) > 1:
            kind = "workflow"
            primary = workflow if workflow in active and workflow not in blocked else None
        else:
            kind = "ambiguous"
    elif candidates:
        primary = candidates[0]
        canonical = _canonical(primary)
        kind = "workflow" if canonical == workflow else "single_skill"
    return {"status": kind, "primary_skill": primary, "candidates": candidates, "scores": scores, "blocked": blocked, "mode": "deterministic_proxy", "runtime_acceptance": "not_assessed"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prompt")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--invoke", action="append", default=[])
    args = parser.parse_args()
    registry = json.loads((args.root / "registry/skills.json").read_text())
    policy = json.loads((args.root / "registry/routing-policy.json").read_text())
    print(json.dumps(route(args.prompt, registry, policy, invoked=tuple(args.invoke)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
