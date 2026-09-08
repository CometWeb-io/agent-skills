#!/usr/bin/env python3
"""Check extractable invariants across a prose rewrite.

The guard catches hard drift that is easy to verify mechanically and emits
heuristic warnings for semantic-risk markers such as negation, modality, and
scope. It is not a semantic verifier.

Part of the ai-humanize skill (Apache-2.0).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

__version__ = "1.3.0"

URL_RE = re.compile(r"https?://[^\s<>\])}]+")
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
ISO_DATE_RE = re.compile(r"(?<!\d)\d{4}-\d{2}-\d{2}(?!\d)")
VERSION_RE = re.compile(r"(?<![\w.])v?\d+(?:\.\d+){1,3}(?:[-+][0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?(?![\w])")
DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+\b", re.IGNORECASE)
UUID_RE = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b", re.IGNORECASE)
CVE_RE = re.compile(r"\bCVE-\d{4}-\d{4,7}\b", re.IGNORECASE)
RFC_RE = re.compile(r"\bRFC[ -]?\d{3,5}\b", re.IGNORECASE)
LONG_FLAG_RE = re.compile(r"(?<![\w-])--[A-Za-z0-9][A-Za-z0-9_-]*")
ENV_RE = re.compile(r"\b[A-Z][A-Z0-9]+(?:_[A-Z0-9]+)+\b")
ISSUE_RE = re.compile(r"(?<!\w)#\d+\b|\b[A-Z][A-Z0-9]+-\d+\b")
HASH_CANDIDATE_RE = re.compile(r"(?<![0-9A-Fa-f])[0-9A-Fa-f]{7,40}(?![0-9A-Fa-f])")
STANDARD_RE = re.compile(r"\b(?:ISO|IEC|WCAG|SOC)\s*(?:[-:]\s*)?[A-Z0-9][A-Z0-9.-]*(?:\s+[A-Z0-9][A-Z0-9.-]*)?\b")
NUMBER_RE = re.compile(
    r"(?<!\d)(?:[$€£]\s*)?[+-]?(?:\d{1,3}(?:[ ,]\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?)(?:\s?%)?(?!\d)"
)
UNIT_RE = re.compile(
    r"(?<![\w.])([+-]?(?:\d{1,3}(?:[ ,]\d{3})+|\d+(?:[.,]\d+)?))\s*"
    r"(%|B|KB|MB|GB|TB|KiB|MiB|GiB|TiB|ms|s|min|h|Hz|kHz|MHz|GHz|px|pt|em|rem|"
    r"kg|mg|g|km|cm|mm|m|°C|°F|V|A|W|kW|MW|GW|MB/s|GB/s|req/s|rps|qps)\b",
    re.IGNORECASE,
)
CURRENCY_RE = re.compile(
    r"(?:[$€£]\s*[+-]?(?:\d{1,3}(?:[ ,]\d{3})+|\d+)(?:[.,]\d+)?|"
    r"[+-]?(?:\d{1,3}(?:[ ,]\d{3})+|\d+)(?:[.,]\d+)?\s*(?:USD|EUR|GBP|PLN))\b",
    re.IGNORECASE,
)
MD_LINK_DEST_RE = re.compile(r"\[[^\]]+\]\(([^)\s]+)(?:\s+['\"][^'\"]*['\"])?\)")
NUMERIC_CITATION_RE = re.compile(r"(?<!\w)\[(\d+(?:\s*[-,]\s*\d+)*)\]")
PATH_RE = re.compile(
    r"(?<![\w:])(?:[A-Za-z]:\\(?:[^\\\s]+\\)*[^\\\s]+|(?:\.{0,2}/)?(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+)"
)
QUOTE_RE = re.compile(r'“([^”\n]+)”|„([^”\n]+)”|"([^"\n]+)"')
NAME_TOKEN = r"[A-Z][A-Za-z0-9]*(?:[-.][A-Za-z0-9]+)*"
PROPER_NAME_RE = re.compile(
    rf"\b(?:{NAME_TOKEN}\s+{NAME_TOKEN}(?:\s+{NAME_TOKEN})*|"
    r"[A-Z][a-z]+[A-Z][A-Za-z0-9-]*|[A-Z]{2,}[A-Z0-9-]*)\b"
)
FENCE_OPEN_RE = re.compile(r"^( {0,3})(`{3,}|~{3,})([^\r\n]*)$")
INLINE_CODE_RE = re.compile(r"(?<!`)(`+)(?!`)([^\n]*?)\1(?!`)")

NEGATION_RE = re.compile(
    r"\b(?:no|not|never|without|cannot|can't|doesn't|don't|isn't|aren't|won't|"
    r"nie|bez|nigdy|brak|nie może|nie mogą)\b",
    re.IGNORECASE,
)
MODALITY_RE = re.compile(
    r"\b(?:must|should|may|might|could|can|cannot|required|recommended|optional|likely|unlikely|"
    r"musi|muszą|należy|powinien|powinna|powinno|powinni|może|mogą|opcjonalny|opcjonalna|"
    r"prawdopodobnie|nieprawdopodobne)\b",
    re.IGNORECASE,
)
SCOPE_RE = re.compile(
    r"\b(?:only|all|every|some|any|none|at least|at most|up to|more than|less than|"
    r"tylko|wyłącznie|wszyscy|wszystkie|każdy|każda|niektórzy|niektóre|co najmniej|co najwyżej|więcej niż|mniej niż)\b",
    re.IGNORECASE,
)


def counter(items: Iterable[str]) -> Counter[str]:
    # Rewrites routinely remove repetition. Guard invariant presence, not mention count.
    values = {item.strip() for item in items if item and item.strip()}
    return Counter({value: 1 for value in values})


def _quoted_values(text: str) -> Iterable[str]:
    for match in QUOTE_RE.finditer(text):
        yield next(group for group in match.groups() if group is not None)


def _hash_values(text: str) -> Iterable[str]:
    for value in HASH_CANDIDATE_RE.findall(text):
        # Avoid ordinary alphabetic words composed only of a-f.
        if any(ch.isdigit() for ch in value) and any(ch.lower() in "abcdef" for ch in value):
            yield value


def _fenced_spans(text: str) -> List[tuple[int, int]]:
    spans: List[tuple[int, int]] = []
    active: tuple[int, str, int] | None = None
    offset = 0
    for line in text.splitlines(keepends=True):
        body = line.rstrip("\r\n")
        if active is None:
            match = FENCE_OPEN_RE.match(body)
            if match:
                fence = match.group(2)
                active = (offset, fence[0], len(fence))
        else:
            start, char, length = active
            close_re = re.compile(rf"^ {{0,3}}{re.escape(char)}{{{length},}}[ \t]*$")
            if close_re.match(body):
                spans.append((start, offset + len(line)))
                active = None
        offset += len(line)
    if active is not None:
        spans.append((active[0], len(text)))
    return spans


def _remove_intervals(text: str, spans: Sequence[tuple[int, int]]) -> str:
    parts: List[str] = []
    cursor = 0
    for start, end in spans:
        parts.append(text[cursor:start])
        cursor = end
    parts.append(text[cursor:])
    return "".join(parts)


def extract(text: str, protected_terms: Sequence[str] = ()) -> Dict[str, Counter[str]]:
    fence_spans = _fenced_spans(text)
    fenced = [text[start:end] for start, end in fence_spans]
    without_fenced = _remove_intervals(text, fence_spans)
    inline = [m.group(2) for m in INLINE_CODE_RE.finditer(without_fenced)]
    without_code = INLINE_CODE_RE.sub("", without_fenced)

    protected_present = [term for term in protected_terms if term and term in text]
    return {
        "urls": counter(value.rstrip(".,;:!?") for value in URL_RE.findall(text)),
        "emails": counter(EMAIL_RE.findall(text)),
        "iso_dates": counter(ISO_DATE_RE.findall(without_code)),
        "versions": counter(VERSION_RE.findall(without_code)),
        "dois": counter(DOI_RE.findall(without_code)),
        "uuids": counter(UUID_RE.findall(without_code)),
        "cves": counter(value.upper() for value in CVE_RE.findall(without_code)),
        "rfc_refs": counter(value.upper().replace(" ", "-") for value in RFC_RE.findall(without_code)),
        "standards": counter(STANDARD_RE.findall(without_code)),
        "number_unit_pairs": counter(" ".join(m.groups()) for m in UNIT_RE.finditer(without_code)),
        "currency_amounts": counter(CURRENCY_RE.findall(without_code)),
        "numbers": counter(NUMBER_RE.findall(without_code)),
        "markdown_link_destinations": counter(MD_LINK_DEST_RE.findall(text)),
        "inline_code": counter(inline),
        "fenced_code_blocks": counter(fenced),
        "paths": counter(value.rstrip(".,;:!?") for value in PATH_RE.findall(without_code)),
        "quoted_spans": counter(_quoted_values(without_code)),
        "numeric_citations": counter(NUMERIC_CITATION_RE.findall(without_code)),
        "cli_flags": counter(LONG_FLAG_RE.findall(without_code)),
        "env_identifiers": counter(ENV_RE.findall(without_code)),
        "issue_ids": counter(ISSUE_RE.findall(without_code)),
        "hashes": counter(_hash_values(without_code)),
        "proper_name_candidates": counter(PROPER_NAME_RE.findall(without_code)),
        "protected_terms": counter(protected_present),
    }


def _semantic_markers(text: str) -> Dict[str, Counter[str]]:
    return {
        "negation": counter(m.group(0).lower() for m in NEGATION_RE.finditer(text)),
        "modality": counter(m.group(0).lower() for m in MODALITY_RE.finditer(text)),
        "scope": counter(m.group(0).lower() for m in SCOPE_RE.finditer(text)),
    }


def subtract(left: Counter[str], right: Counter[str]) -> List[dict]:
    diff = left - right
    return [{"value": value, "count": count} for value, count in sorted(diff.items())]


def _semantic_deltas(before: str, after: str) -> dict:
    a = _semantic_markers(before)
    b = _semantic_markers(after)
    deltas = {}
    for kind in a:
        removed = subtract(a[kind], b[kind])
        added = subtract(b[kind], a[kind])
        if removed or added:
            deltas[kind] = {"removed": removed, "added": added}
    return deltas


def compare(
    before: str,
    after: str,
    *,
    strict: bool = False,
    protected_terms: Sequence[str] = (),
) -> dict:
    a = extract(before, protected_terms)
    b = extract(after, protected_terms)
    missing = {kind: subtract(a[kind], b[kind]) for kind in a}
    added = {kind: subtract(b[kind], a[kind]) for kind in a}
    missing = {kind: vals for kind, vals in missing.items() if vals}
    added = {kind: vals for kind, vals in added.items() if vals}
    semantic_risk = _semantic_deltas(before, after)

    passed = not bool(missing) and (not strict or not bool(added))
    warnings: List[str] = []
    if added and not strict:
        warnings.append("New invariant-like tokens were introduced; review for factual drift.")
    if strict and added:
        warnings.append("Strict mode treats introduced invariant-like tokens as failure.")
    if semantic_risk:
        warnings.append("Negation, modality, or scope markers changed; review semantic fidelity manually.")

    return {
        "passed": passed,
        "strict": strict,
        "missing_invariants": missing,
        "added_invariants": added,
        "semantic_risk_markers": semantic_risk,
        "warnings": warnings,
        "limitations": [
            "Does not verify semantic equivalence, causal relations, attribution, or factual truth.",
            "Semantic-risk markers are heuristic and may change legitimately during paraphrase.",
            "Single-token proper names are not inferred reliably; pass them with --protect.",
            "Quoted material is exact-match protected and can over-constrain intentional quote paraphrases.",
            "Does not detect or remove statistical provenance watermarks.",
        ],
        "version": __version__,
    }


def _load_protected_terms(values: Sequence[str], files: Sequence[Path]) -> List[str]:
    terms = [value for value in values if value]
    for path in files:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                terms.append(line)
    return list(dict.fromkeys(terms))


def _occurrence_count(groups: Dict[str, List[dict]]) -> int:
    return sum(item["count"] for values in groups.values() for item in values)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check hard textual invariants across a rewrite.")
    parser.add_argument("before", type=Path, help="Original text file")
    parser.add_argument("after", type=Path, help="Rewritten text file")
    parser.add_argument(
        "--strict", action="store_true",
        help="Fail on added invariant-like tokens as well as missing ones.",
    )
    parser.add_argument(
        "--protect", action="append", default=[], metavar="TEXT",
        help="Exact protected term/span. Repeat for single-token names or normative phrases.",
    )
    parser.add_argument(
        "--protect-file", action="append", default=[], type=Path, metavar="PATH",
        help="UTF-8 file with one exact protected term per line.",
    )
    parser.add_argument(
        "--summary", action="store_true",
        help="Print a one-line summary instead of full JSON.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args()

    try:
        before = args.before.read_text(encoding="utf-8")
        after = args.after.read_text(encoding="utf-8")
        protected_terms = _load_protected_terms(args.protect, args.protect_file)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    result = compare(before, after, strict=args.strict, protected_terms=protected_terms)

    if args.summary:
        status = "PASS" if result["passed"] else "FAIL"
        miss = _occurrence_count(result["missing_invariants"])
        add = _occurrence_count(result["added_invariants"])
        semantic = len(result["semantic_risk_markers"])
        print(
            f"{status}  missing={miss}  added={add}  semantic_warnings={semantic} "
            f"strict={str(result['strict']).lower()}"
        )
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))

    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
