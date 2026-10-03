#!/usr/bin/env python3
"""Deterministic routing diagnostics; not a model evaluator or a permission boundary.

Only pass the user's instruction, not the contents of retrieved documents.
"""
from __future__ import annotations
import argparse
from functools import lru_cache
import hashlib
import json
import math
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.casefold()).replace("ł", "l")
    # Format characters (zero-width space/joiner, soft hyphen, bidi controls) are
    # invisible: left in, they split a skill name so a denial stops matching it.
    return "".join(ch for ch in text if not unicodedata.combining(ch) and unicodedata.category(ch) != "Cf")


# Quoted, fenced or blockquoted text is someone else's words, not an invocation.
_QUOTED = re.compile(
    r"```.*?(?:```|\Z)"
    r'|"[^"\n]{0,2000}"'
    r"|\u201c[^\u201d]{0,2000}\u201d"
    r"|\u201e[^\u201c\u201d]{0,2000}[\u201c\u201d]"
    r"|\u00ab[^\u00bb]{0,2000}\u00bb"
    r"|^[ \t]{0,3}>.*$",
    re.DOTALL | re.MULTILINE,
)


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
    _sequence_rules(policy)
    _override_cues(policy)
    _lexical_rules(policy)
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


def _sequence_rules(policy: dict):
    """Validate and return (connector, min_step_score), or None when unset."""
    rules = policy.get("sequence")
    if rules is None:
        return None
    if not isinstance(rules, dict) or not {"connector", "min_step_score"} <= rules.keys():
        raise ValueError("invalid sequence rules")
    floor = rules["min_step_score"]
    if type(floor) is not int or not 1 <= floor <= 10000:
        raise ValueError("invalid sequence rules")
    return _pattern(rules["connector"]), floor


def sequence_steps(signal_text: str, active: dict, blocked: dict, policy: dict, canonical) -> list[str]:
    """Distinct specialists that win successive steps of a "do X, then Y" request.

    The prompt is cut at sequencing connectors ("then", "potem", "a po nim",
    "na tej podstawie", ...). In each step the specialist with the single
    highest signal score (at least ``min_step_score``) is that step's skill.
    An explicit-only skill such as the Council counts as a step when its own
    signals name it, because orchestrating it is still a request for it.
    Skills excluded by name, by a narrow-intent guard or aliases of the
    workflow skill never count. Consecutive repeats collapse to one step.
    """
    rules = _sequence_rules(policy)
    if rules is None:
        return []
    connector, floor = rules
    workflow = policy["workflow_skill"]
    cuts = [0]
    for m in connector.finditer(signal_text):
        cuts.extend((m.start(), m.end()))
    cuts.append(len(signal_text))
    if len(cuts) < 4:
        return []
    steps: list[str] = []
    for start, end in zip(cuts[::2], cuts[1::2], strict=True):
        segment = signal_text[start:end]
        best: dict[str, int] = {}
        for sid, entry in active.items():
            if blocked.get(sid, "requires_explicit_invocation") != "requires_explicit_invocation":
                continue
            canon = canonical(sid)
            if canon == workflow:
                continue
            score = sum(w for w, pat in entry.get("routing_signals", []) if matches(pat, segment))
            if score >= floor:
                best[canon] = max(best.get(canon, 0), score)
        if best:
            top = max(best.values())
            winners = [sid for sid, score in best.items() if score == top]
            if len(winners) == 1 and (not steps or steps[-1] != winners[0]):
                steps.append(winners[0])
    return steps
def _override_cues(policy: dict) -> tuple:
    rules = policy.get("untrusted_text")
    if rules is None:
        return ()
    cues = rules.get("override_cues") if isinstance(rules, dict) else None
    if not isinstance(cues, list) or not 1 <= len(cues) <= 32:
        raise ValueError("invalid untrusted_text rules")
    return tuple(_pattern(c) for c in cues)


def untrusted_spans(text: str, policy: dict) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    """(quoted, overridden) character ranges of normalized ``text``.

    ``quoted`` covers fenced code, blockquote lines and text in double or
    typographic quotes. ``overridden`` runs from the first override cue that is
    not itself quoted ("ignore previous instructions", "you are now") to the end
    of the prompt: whatever follows such a phrase reads as pasted content trying
    to steer the agent, not as the user's own request.
    """
    quoted = [(m.start(), m.end()) for m in _QUOTED.finditer(text)]
    starts = [
        m.start()
        for cue in _override_cues(policy)
        for m in cue.finditer(text)
        if not any(a <= m.start() < b for a, b in quoted)
    ]
    return quoted, ([(min(starts), len(text))] if starts else [])


def _blank(text: str, spans: list[tuple[int, int]]) -> str:
    for start, end in spans:
        text = text[:start] + " " * (end - start) + text[end:]
    return text


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


# ---------------------------------------------------------------------------
# Lexical ranker: BM25 over each skill's own text, used only when the regex
# signals are silent or near-tied. See evals/routing/README.md, "Lexical ranker".
# ---------------------------------------------------------------------------

_WORD = re.compile(r"[a-z0-9]+")
_LEXICAL_PARAMS = {
    "k1": (float, 0.1, 5.0), "b": (float, 0.0, 1.0), "negative_weight": (float, 0.0, 2.0),
    "min_score": (float, 0.0, 1000.0), "min_margin": (float, 0.0, 1000.0),
    "min_ratio": (float, 1.0, 100.0), "min_terms": (int, 1, 20),
    "tie_margin": (float, 0.0, 1000.0), "tie_ratio": (float, 1.0, 100.0),
    "stem_chars": (int, 3, 20),
}
_LEXICAL_FIELDS = ("description", "owns", "trigger_examples", "lexicon")


def _lexical_rules(policy: dict):
    """Validate and return the ``lexical`` policy block, or None when unset."""
    rules = policy.get("lexical")
    if rules is None:
        return None
    if not isinstance(rules, dict) or type(rules.get("enabled")) is not bool:
        raise ValueError("invalid lexical rules")
    for key, (kind, low, high) in _LEXICAL_PARAMS.items():
        value = rules.get(key)
        if type(value) not in ((int, float) if kind is float else (int,)) or not low <= value <= high:
            raise ValueError(f"invalid lexical parameter {key}")
    weights = rules.get("field_weights")
    if not isinstance(weights, dict) or set(weights) != set(_LEXICAL_FIELDS) or any(
        type(w) is not int or not 0 <= w <= 10 for w in weights.values()
    ):
        raise ValueError("invalid lexical field weights")
    for key in ("stopwords", "suffixes"):
        words = rules.get(key)
        if not isinstance(words, list) or len(words) > 2000 or any(
            not isinstance(w, str) or not _WORD.fullmatch(w) for w in words
        ):
            raise ValueError(f"invalid lexical {key}")
    abstain = rules.get("abstain")
    if not isinstance(abstain, list) or len(abstain) > 32:
        raise ValueError("invalid lexical abstain patterns")
    for pattern in abstain:
        _pattern(pattern)
    lexicon = rules.get("lexicon")
    if not isinstance(lexicon, dict) or len(lexicon) > 500:
        raise ValueError("invalid lexicon")
    vetoes = rules.get("veto")
    if not isinstance(vetoes, dict) or len(vetoes) > 500:
        raise ValueError("invalid lexical veto")
    for group in (lexicon, vetoes):
        for sid, terms in group.items():
            if not isinstance(sid, str) or not ID.fullmatch(sid) or not isinstance(terms, list) or len(terms) > 400:
                raise ValueError("invalid lexicon entry")
            if any(not isinstance(t, str) or not 1 <= len(t) <= 80 for t in terms):
                raise ValueError("invalid lexicon term")
    return rules


def _stem(token: str, suffixes: tuple[str, ...], cap: int) -> str:
    """Light, language-agnostic stemming: drop up to two inflectional endings, then truncate.

    Truncation does most of the work for Polish ("konkurencji", "konkurencja")
    and English derivations ("competitor", "competitive"); endings are only
    removed while at least four characters remain.
    """
    for _ in range(2):
        for suffix in suffixes:
            if token.endswith(suffix) and len(token) - len(suffix) >= 4:
                token = token[: -len(suffix)]
                break
        else:
            break
    return token[:cap]


def _short_words(rules: dict) -> frozenset[str]:
    """Two-letter words worth keeping ("qa", "ux", "ci"): exactly those the lexicon lists."""
    return frozenset(t for terms in rules["lexicon"].values() for t in terms if len(t) == 2 and _WORD.fullmatch(t))


def lexical_terms(text: str, rules: dict, *, unigrams: bool = True) -> list[str]:
    """Stemmed unigrams plus bigrams of adjacent content words, in order of appearance.

    With ``unigrams=False`` only the bigrams of a multi-word phrase are returned,
    so a lexicon phrase such as "go live" adds the pair, not a loose "go".
    """
    stop = frozenset(rules["stopwords"])
    short = _short_words(rules)
    suffixes = tuple(sorted(rules["suffixes"], key=len, reverse=True))
    stems: list[str | None] = []
    for word in _WORD.findall(normalize(text)):
        keep = word not in stop and (len(word) > 2 or word in short)
        stems.append(_stem(word, suffixes, rules["stem_chars"]) if keep else None)
    pairs = [f"{a}_{b}" for a, b in zip(stems, stems[1:], strict=False) if a and b and a != b]
    if not unigrams and pairs:
        return pairs
    return [s for s in stems if s] + pairs


def _split_description(text: str) -> tuple[str, str]:
    """(positive, negative) sentences: "Do not use for X (use Y)" describes neighbours."""
    positive, negative = [], []
    for sentence in re.split(r"(?<=[.!?])\s+", text or ""):
        (negative if re.match(r"\s*(?:do not|don't|never|not for)\b", sentence, re.I) else positive).append(sentence)
    return " ".join(positive), " ".join(negative)


_INDEX_CACHE: dict[str, dict] = {}


def _lexical_index(active: dict, rules: dict) -> dict:
    """BM25 statistics for every active skill; cached on the content that feeds it."""
    source = {
        sid: [entry.get("description", ""), entry.get("owns", []), entry.get("does_not_own", []),
              entry.get("trigger_examples", []), entry.get("negative_trigger_examples", []),
              rules["lexicon"].get(sid, [])]
        for sid, entry in sorted(active.items())
    }
    key = hashlib.sha256(json.dumps([source, rules], sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    if key in _INDEX_CACHE:
        return _INDEX_CACHE[key]
    weights = rules["field_weights"]

    def strings(value) -> list[str]:
        return [v for v in value if isinstance(v, str)] if isinstance(value, list) else []

    positive, negative = {}, {}
    for sid, (description, owns, not_owned, examples, counter_examples, lexicon) in source.items():
        pos_text, neg_text = _split_description(description if isinstance(description, str) else "")
        tf: dict[str, int] = {}
        for field, texts in (("description", [pos_text]), ("owns", strings(owns)),
                             ("trigger_examples", strings(examples)), ("lexicon", strings(lexicon))):
            for text in texts:
                # A field mentions a term once however often it repeats it. The
                # loose words of a lexicon phrase count like description words;
                # the phrase itself (its bigrams) and single-word entries carry
                # the lexicon weight.
                terms = set(lexical_terms(text, rules))
                strong = set(lexical_terms(text, rules, unigrams=False)) if field == "lexicon" else terms
                for term in terms:
                    weight = weights[field] if term in strong else weights["description"]
                    tf[term] = tf.get(term, 0) + weight
        positive[sid] = {t: n for t, n in tf.items() if n}
        neg: set[str] = set()
        for text in [neg_text, *strings(not_owned), *strings(counter_examples)]:
            neg.update(lexical_terms(text, rules))
        negative[sid] = neg
    df: dict[str, int] = {}
    for tf in positive.values():
        for term in tf:
            df[term] = df.get(term, 0) + 1
    total = len(positive) or 1
    lengths = {sid: sum(tf.values()) for sid, tf in positive.items()}
    index = {
        "tf": positive, "negative": negative, "lengths": lengths,
        "avg": (sum(lengths.values()) / total) or 1.0,
        "idf": {t: math.log(1 + (total - n + 0.5) / (n + 0.5)) for t, n in df.items()},
    }
    if len(_INDEX_CACHE) > 16:
        _INDEX_CACHE.clear()
    _INDEX_CACHE[key] = index
    return index


def _contains_phrase(text: str, phrase: str) -> bool:
    """True when ``phrase`` occurs in normalized ``text`` as whole words (a literal, not a regex)."""
    words = _WORD.findall(normalize(phrase))
    return bool(words) and re.search(r"(?<![a-z0-9])" + r"\W{1,3}".join(map(re.escape, words)) + r"(?![a-z0-9])", text) is not None


def lexical_scores(signal_text: str, active: dict, eligible: list[str], rules: dict) -> dict[str, dict]:
    """BM25 score and per-term contributions for each eligible skill with any match.

    Query terms count once each. A term that also appears in the skill's own
    "do not use" text, does-not-own list or negative examples is subtracted at
    ``negative_weight`` of its positive value, so a neighbour named in a
    description does not pull the request toward the skill that disowns it.
    """
    index = _lexical_index(active, rules)
    query = list(dict.fromkeys(lexical_terms(signal_text, rules)))
    k1, b, neg_w = rules["k1"], rules["b"], rules["negative_weight"]
    out: dict[str, dict] = {}
    for sid in eligible:
        tf, negative = index["tf"].get(sid, {}), index["negative"].get(sid, set())
        norm = 1 - b + b * index["lengths"].get(sid, 0) / index["avg"]
        contributions: dict[str, float] = {}
        for term in query:
            idf = index["idf"].get(term)
            if idf is None:
                continue
            value = idf * tf[term] * (k1 + 1) / (tf[term] + k1 * norm) if term in tf else 0.0
            if term in negative:
                value -= neg_w * idf
            if value:
                contributions[term] = round(value, 3)
        positive_terms = [t for t, v in contributions.items() if v > 0]
        # A veto phrase narrows the request below what the skill owns ("a roadmap
        # for paying down one debt" is not a whole-project baseline).
        vetoed = [v for v in rules["veto"].get(sid, []) if _contains_phrase(signal_text, v)]
        if positive_terms:
            # Distinct ideas, not tokens: "tear down" is one concept however it
            # splits, so a matched pair absorbs the two words it is made of.
            pairs = [t for t in positive_terms if "_" in t]
            covered = {w for t in pairs for w in t.split("_")}
            concepts = len(pairs) + sum(1 for t in positive_terms if "_" not in t and t not in covered)
            out[sid] = {
                "score": round(sum(contributions.values()), 3),
                "matched_terms": 0 if vetoed else concepts,
                "contributions": dict(sorted(contributions.items(), key=lambda kv: -abs(kv[1]))),
            }
            if vetoed:
                out[sid]["vetoed_by"] = vetoed
    return out


def _denied_by_name(sid: str, text: str) -> bool:
    # Bound the prohibition to a named skill, not the rest of the paragraph.
    lead = r"(?:\b(?:do not|don['’]?t|never)\s+(?:use|run|load|invoke|activate)\s+|\b(?:without|no)\s+(?:using\s+)?|\bnie\s+(?:uzywaj|uruchamiaj|wlaczaj|korzystaj z)\s+|\bbez\s+)"
    return re.search(lead + r"(?:the\s+)?[$@]?" + re.escape(sid) + r"(?![\w-])", text) is not None


def route(prompt: str, registry: dict, policy: dict, *, invoked: tuple[str, ...] = (),
          lexical: bool | None = None, explain: bool = False) -> dict:
    active = _catalog(registry, policy)
    if not isinstance(prompt, str) or len(prompt) > 65536 or not isinstance(invoked, (tuple, list)) or any(not isinstance(s, str) for s in invoked):
        raise ValueError("invalid routing request")
    text = normalize(prompt)
    quoted, overridden = untrusted_spans(text, policy)
    # Denials read the whole prompt; invocations and signals only the user's own words.
    own_text = _blank(text, quoted + overridden)
    signal_text = _blank(mask_negated(text, policy), quoted + overridden)
    if any(sid not in active for sid in invoked):
        raise ValueError("explicit invocation references an unavailable skill")
    explicit, scores, blocked = set(invoked), {}, {}
    for sid in active:
        if re.search(r"(?<![\w-])[$@]" + re.escape(sid) + r"(?![\w-])", own_text):
            explicit.add(sid)
        # Natural "use product-operator" / "run evidence-researcher" invocations.
        if re.search(
            r"(?<![\w-])(?:use|run|invoke|load)\s+(?:the\s+)?" + re.escape(sid) + r"(?![\w-])",
            own_text,
        ):
            explicit.add(sid)
        if any(matches(p, own_text) for p in policy.get("explicit_patterns", {}).get(sid, [])):
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
    # A request that hands different steps to different specialists ("audit the
    # signup flow, then gate the release") is a workflow, whatever one step scored.
    steps: list[str] = []
    if not invoked and kind != "workflow" and workflow in active and workflow not in blocked:
        steps = sequence_steps(signal_text, active, blocked, policy, _canonical)
        if len(set(steps)) > 1:
            primary, kind, candidates = workflow, "workflow", [workflow]
    # Lexical fallback: only when signals are silent or near-tied, never over an
    # explicit invocation, an exclusion, a guard or a multi-step workflow.
    rules = _lexical_rules(policy)
    use_lexical = rules is not None and (rules["enabled"] if lexical is None else lexical)
    lexical_result = None
    regex_candidates = list(candidates)
    abstained = (
        use_lexical and kind == "no_skill"
        and next((p for p in rules["abstain"] if matches(p, signal_text)), None)
    )
    if use_lexical and not explicit and kind in ("no_skill", "ambiguous") and len(set(steps)) <= 1 and not abstained:
        pool = list(candidates) if kind == "ambiguous" else [sid for sid in active if sid not in blocked]
        ranked = lexical_scores(signal_text, active, pool, rules)
        order = sorted(ranked, key=lambda sid: (-ranked[sid]["score"], sid))
        # Only skills backed by enough distinct concepts compete; a single strong
        # phrase ("tear down", "quality loop") neither wins nor blocks a winner.
        supported = [sid for sid in order if ranked[sid]["matched_terms"] >= rules["min_terms"]]
        top = supported[0] if supported else None
        # A near-tie stays ambiguous when the text gives any other candidate more
        # than one concept of its own ("a roadmap from scratch and what to do
        # this week" is two requests, not one with a stray word).
        if kind == "ambiguous" and any(ranked[sid]["matched_terms"] > 1 for sid in order if sid != top):
            top = None
        top_score = ranked[top]["score"] if top else 0.0
        runner = max([ranked[sid]["score"] for sid in supported[1:]] + [0.0])
        if kind == "ambiguous":
            margin, ratio = rules["tie_margin"], rules["tie_ratio"]
        else:
            margin, ratio = rules["min_margin"], rules["min_ratio"]
        accepted = bool(top) and (
            top_score >= rules["min_score"]
            and top_score - runner >= margin
            and (runner <= 0 or top_score / runner >= ratio)
        )
        lexical_result = {"pool": kind, "accepted": accepted, "ranked": [
            {"skill": sid, "score": ranked[sid]["score"], "matched_terms": ranked[sid]["matched_terms"],
             **({"vetoed_by": ranked[sid]["vetoed_by"]} if "vetoed_by" in ranked[sid] else {})}
            for sid in order[:5]]}
        if accepted:
            primary, candidates = top, [top]
            kind = "workflow" if _canonical(top) == workflow else "single_skill"
            if explain:
                lexical_result["contributions"] = {sid: ranked[sid]["contributions"] for sid in order[:3]}
        elif explain:
            lexical_result["contributions"] = {sid: ranked[sid]["contributions"] for sid in order[:3]}
    if explain and rules is not None and lexical_result is None:
        # Shown for diagnosis only: what the ranker would have said, had it been asked.
        ranked = lexical_scores(signal_text, active, [sid for sid in active if sid not in blocked], rules)
        order = sorted(ranked, key=lambda sid: (-ranked[sid]["score"], sid))
        lexical_result = {"pool": "not_consulted", "accepted": False,
                          "ranked": [{"skill": sid, "score": ranked[sid]["score"],
                                      "matched_terms": ranked[sid]["matched_terms"]} for sid in order[:5]],
                          "contributions": {sid: ranked[sid]["contributions"] for sid in order[:3]}}
    result = {"status": kind, "primary_skill": primary, "candidates": candidates, "scores": scores, "blocked": blocked, "override_suspected": bool(overridden), "mode": "deterministic_proxy", "runtime_acceptance": "not_assessed"}
    if len(set(steps)) > 1:
        result["sequence"] = steps
    if lexical_result is not None and (lexical_result["accepted"] or explain):
        result["decided_by"] = "lexical" if lexical_result["accepted"] else ("signals" if regex_candidates else "none")
        result["lexical"] = lexical_result
        if regex_candidates != candidates:
            result["signal_candidates"] = regex_candidates
    if explain:
        result.setdefault("decided_by", "explicit" if explicit else "sequence" if len(set(steps)) > 1 else "signals" if candidates else "none")
        result["explain"] = {
            "explicit": sorted(explicit),
            "signals": {
                sid: [[w, pat] for w, pat in active[sid].get("routing_signals", []) if matches(pat, signal_text)]
                for sid in sorted(scores)
            },
            "negated_spans": negated_spans(text, policy),
            "lexical_enabled": use_lexical,
            "lexical_abstained_on": abstained or None,
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prompt")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--invoke", action="append", default=[])
    parser.add_argument("--explain", action="store_true",
                        help="show matched signals, negated spans and lexical ranker contributions")
    toggle = parser.add_mutually_exclusive_group()
    toggle.add_argument("--lexical", dest="lexical", action="store_true", default=None,
                        help="force the lexical fallback on, whatever the policy says")
    toggle.add_argument("--no-lexical", dest="lexical", action="store_false",
                        help="force the lexical fallback off")
    args = parser.parse_args()
    registry = json.loads((args.root / "registry/skills.json").read_text())
    policy = json.loads((args.root / "registry/routing-policy.json").read_text())
    result = route(args.prompt, registry, policy, invoked=tuple(args.invoke), lexical=args.lexical, explain=args.explain)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
