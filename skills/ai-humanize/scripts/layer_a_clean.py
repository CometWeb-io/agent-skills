#!/usr/bin/env python3
"""Deterministic Unicode hygiene for prose and Markdown.

The cleaner removes suspicious invisible/control characters from prose while
preserving Markdown code spans/blocks, emoji joiner/tag sequences, and common
script joiners that can be semantically meaningful. It never collapses ordinary
spaces or indentation.

Part of the ai-humanize skill (Apache-2.0).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

__version__ = "1.3.0"

BIDI_CONTROLS = {
    "\u202a", "\u202b", "\u202c", "\u202d", "\u202e",  # LRE RLE PDF LRO RLO
    "\u2066", "\u2067", "\u2068", "\u2069",  # LRI RLI FSI PDI
}

ALWAYS_STRIP = {
    "\u200b",  # ZERO WIDTH SPACE
    "\u2060",  # WORD JOINER
    "\ufeff",  # BOM / ZERO WIDTH NO-BREAK SPACE
    "\u00ad",  # SOFT HYPHEN
    "\u180e",  # MONGOLIAN VOWEL SEPARATOR (deprecated)
    "\u2061",  # FUNCTION APPLICATION
    "\u2062",  # INVISIBLE TIMES
    "\u2063",  # INVISIBLE SEPARATOR
    "\u2064",  # INVISIBLE PLUS
    "\u2065",  # reserved
    "\u206a", "\u206b", "\u206c", "\u206d", "\u206e", "\u206f",
}

EXOTIC_SPACES = {
    "\u00a0": " ", "\u2000": " ", "\u2001": " ", "\u2002": " ",
    "\u2003": " ", "\u2004": " ", "\u2005": " ", "\u2006": " ",
    "\u2007": " ", "\u2008": " ", "\u2009": " ", "\u200a": " ",
    "\u202f": " ", "\u205f": " ", "\u3000": " ",
}

CONFUSABLES = {
    "\u0430": "a", "\u0435": "e", "\u043e": "o", "\u0440": "p",
    "\u0441": "c", "\u0443": "y", "\u0445": "x",
    "\u0410": "A", "\u0415": "E", "\u041e": "O", "\u0420": "P",
    "\u0421": "C", "\u0425": "X",
}

PUA_RANGES = (
    (0xE000, 0xF8FF),
    (0xF0000, 0xFFFFD),
    (0x100000, 0x10FFFD),
)

COMPLEX_SCRIPT_RANGES = (
    (0x0590, 0x08FF),   # Hebrew, Arabic, Syriac, Thaana, NKo, Arabic ext.
    (0x0900, 0x0DFF),   # Indic blocks
    (0x0E00, 0x0FFF),   # Thai, Lao, Tibetan
    (0x1000, 0x109F),   # Myanmar
    (0x1780, 0x17FF),   # Khmer
    (0x1800, 0x18AF),   # Mongolian
    (0xA800, 0xA8FF),   # several Indic-derived scripts
    (0xA980, 0xA9DF),
    (0xAA00, 0xAA7F),
    (0x11000, 0x11FFF), # supplementary Brahmic scripts
)

FENCE_OPEN_RE = re.compile(r"^( {0,3})(`{3,}|~{3,})([^\r\n]*)$")
INLINE_CODE_RE = re.compile(r"(?<!`)(`+)(?!`)([^\n]*?)\1(?!`)")


def _in_ranges(cp: int, ranges: Sequence[Tuple[int, int]]) -> bool:
    return any(start <= cp <= end for start, end in ranges)


def is_emoji_base(ch: str) -> bool:
    if not ch:
        return False
    cp = ord(ch)
    return (
        0x1F000 <= cp <= 0x1FAFF
        or 0x1F1E6 <= cp <= 0x1F1FF
        or 0x2600 <= cp <= 0x27BF
        or cp in (0x20E3,)
    )


def is_complex_script(ch: str) -> bool:
    return bool(ch) and _in_ranges(ord(ch), COMPLEX_SCRIPT_RANGES)


def is_private_use(ch: str) -> bool:
    return _in_ranges(ord(ch), PUA_RANGES)


def is_noncharacter(ch: str) -> bool:
    cp = ord(ch)
    return 0xFDD0 <= cp <= 0xFDEF or (cp & 0xFFFF) in (0xFFFE, 0xFFFF)


def is_tag_character(ch: str) -> bool:
    cp = ord(ch)
    return 0xE0001 <= cp <= 0xE007F


def is_variation_selector(ch: str) -> bool:
    cp = ord(ch)
    return 0xFE00 <= cp <= 0xFE0F or 0xE0100 <= cp <= 0xE01EF


def _preserve_emoji_tag(text: str, index: int) -> bool:
    """Preserve subdivision-flag tag characters following BLACK FLAG."""
    j = index - 1
    while j >= 0 and is_tag_character(text[j]):
        j -= 1
    return j >= 0 and ord(text[j]) == 0x1F3F4


def _merge_spans(spans: Iterable[Tuple[int, int]]) -> List[Tuple[int, int]]:
    merged: List[Tuple[int, int]] = []
    for start, end in sorted(spans):
        if not merged or start > merged[-1][1]:
            merged.append((start, end))
        else:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
    return merged


def fenced_code_spans(text: str) -> List[Tuple[int, int]]:
    """Return CommonMark-like fenced code spans, including unclosed fences to EOF."""
    spans: List[Tuple[int, int]] = []
    active: Tuple[int, str, int] | None = None
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


def markdown_protected_spans(text: str) -> List[Tuple[int, int]]:
    """Return fenced and inline-code spans that should remain byte-for-byte stable."""
    fence_spans = fenced_code_spans(text)
    spans = list(fence_spans)

    def inside_fence(pos: int) -> bool:
        return any(start <= pos < end for start, end in fence_spans)

    for match in INLINE_CODE_RE.finditer(text):
        if not inside_fence(match.start()):
            spans.append((match.start(), match.end()))
    return _merge_spans(spans)


def _normalize(text: str, mode: str) -> Tuple[str, bool]:
    if mode == "none":
        return text, False
    form = "NFKC" if mode == "nfkc" else "NFC"
    normalized = unicodedata.normalize(form, text)
    return normalized, normalized != text


def _clean_segment(
    text: str,
    *,
    normalization: str,
    aggressive_homoglyphs: bool,
    strip_emoji_glue: bool,
    preserve_bidi_controls: bool,
    report: Dict,
) -> str:
    text, changed = _normalize(text, normalization)
    report["normalized"] = report["normalized"] or changed

    out: List[str] = []
    for i, ch in enumerate(text):
        prev = text[i - 1] if i else ""
        nxt = text[i + 1] if i + 1 < len(text) else ""

        if ch in ("\u200c", "\u200d"):
            if not strip_emoji_glue:
                if ch == "\u200d" and (is_emoji_base(prev) or is_emoji_base(nxt)):
                    out.append(ch)
                    continue
                if is_complex_script(prev) and is_complex_script(nxt):
                    out.append(ch)
                    continue
            report["removed"][unicodedata.name(ch, f"U+{ord(ch):04X}")] += 1
            continue

        if is_variation_selector(ch):
            if not strip_emoji_glue and (
                is_emoji_base(prev) or is_emoji_base(nxt)
                or is_complex_script(prev) or is_complex_script(nxt)
            ):
                out.append(ch)
                continue
            report["removed"][unicodedata.name(ch, f"U+{ord(ch):04X}")] += 1
            continue

        if is_tag_character(ch):
            if not strip_emoji_glue and _preserve_emoji_tag(text, i):
                out.append(ch)
                continue
            report["removed"][unicodedata.name(ch, f"U+{ord(ch):04X}")] += 1
            continue

        if ch in BIDI_CONTROLS:
            if preserve_bidi_controls:
                out.append(ch)
                continue
            report["removed"][unicodedata.name(ch, f"U+{ord(ch):04X}")] += 1
            continue

        if ch in ALWAYS_STRIP or is_private_use(ch) or is_noncharacter(ch):
            report["removed"][unicodedata.name(ch, f"U+{ord(ch):04X}")] += 1
            continue

        if ch in EXOTIC_SPACES:
            replacement = EXOTIC_SPACES[ch]
            report["replaced"][f"U+{ord(ch):04X} -> U+0020"] += 1
            out.append(replacement)
            continue

        if aggressive_homoglyphs and ch in CONFUSABLES:
            report["replaced"][f"confusable {ch} -> {CONFUSABLES[ch]}"] += 1
            out.append(CONFUSABLES[ch])
            continue

        out.append(ch)

    return "".join(out)


def clean_text(
    text: str,
    *,
    profile: str = "prose",
    normalization: str = "nfc",
    aggressive_homoglyphs: bool = False,
    strip_emoji_glue: bool = False,
    preserve_bidi_controls: bool = False,
) -> Tuple[str, Dict]:
    """Return cleaned text and a machine-readable report.

    profile="markdown" preserves fenced and inline code byte-for-byte.
    profile="prose" cleans the entire input. Ordinary spaces/tabs are never collapsed.
    """
    if profile not in {"prose", "markdown"}:
        raise ValueError("profile must be 'prose' or 'markdown'")
    if normalization not in {"none", "nfc", "nfkc"}:
        raise ValueError("normalization must be 'none', 'nfc', or 'nfkc'")

    report: Dict = {
        "removed": Counter(),
        "replaced": Counter(),
        "normalized": False,
        "normalization": normalization,
        "profile": profile,
        "protected_spans": 0,
        "version": __version__,
    }

    if profile == "markdown":
        spans = markdown_protected_spans(text)
        report["protected_spans"] = len(spans)
        parts: List[str] = []
        cursor = 0
        for start, end in spans:
            parts.append(_clean_segment(
                text[cursor:start],
                normalization=normalization,
                aggressive_homoglyphs=aggressive_homoglyphs,
                strip_emoji_glue=strip_emoji_glue,
                preserve_bidi_controls=preserve_bidi_controls,
                report=report,
            ))
            parts.append(text[start:end])
            cursor = end
        parts.append(_clean_segment(
            text[cursor:],
            normalization=normalization,
            aggressive_homoglyphs=aggressive_homoglyphs,
            strip_emoji_glue=strip_emoji_glue,
            preserve_bidi_controls=preserve_bidi_controls,
            report=report,
        ))
        cleaned = "".join(parts)
    else:
        cleaned = _clean_segment(
            text,
            normalization=normalization,
            aggressive_homoglyphs=aggressive_homoglyphs,
            strip_emoji_glue=strip_emoji_glue,
            preserve_bidi_controls=preserve_bidi_controls,
            report=report,
        )

    report["removed"] = dict(report["removed"])
    report["replaced"] = dict(report["replaced"])
    report["chars_removed"] = sum(report["removed"].values())
    report["chars_replaced"] = sum(report["replaced"].values())
    return cleaned, report


def _resolve_profile(requested: str, input_path: Path | None) -> str:
    if requested != "auto":
        return requested
    if input_path and input_path.suffix.lower() in {".md", ".markdown", ".mdx"}:
        return "markdown"
    return "prose"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Safe Unicode hygiene for prose/Markdown without collapsing indentation."
    )
    parser.add_argument("input", type=Path, nargs="?", help="Input file (default: stdin)")
    parser.add_argument("-o", "--output", type=Path, help="Output file (default: stdout)")
    parser.add_argument(
        "--profile", choices=("auto", "prose", "markdown"), default="auto",
        help="Cleaning profile. auto uses markdown for .md/.mdx files, prose otherwise.",
    )
    norm = parser.add_mutually_exclusive_group()
    norm.add_argument("--nfkc", action="store_true", help="Use compatibility normalization (opt-in).")
    norm.add_argument("--no-normalize", action="store_true", help="Disable Unicode normalization.")
    parser.add_argument(
        "--no-nfkc", action="store_true",
        help="Legacy compatibility flag; keeps the safer default NFC behavior.",
    )
    parser.add_argument(
        "--aggressive-homoglyphs", action="store_true",
        help="Replace a small conservative set of Cyrillic Latin-lookalikes.",
    )
    parser.add_argument(
        "--strip-emoji-glue", action="store_true",
        help="Paranoid mode: also strip emoji/script joiners, selectors, and tag characters.",
    )
    parser.add_argument(
        "--preserve-bidi-controls", action="store_true",
        help="Preserve Unicode bidi controls for legitimate RTL/mixed-direction documents.",
    )
    parser.add_argument(
        "--check", action="store_true",
        help="Do not write cleaned text; exit 1 if cleaning would change the input.",
    )
    parser.add_argument("--json", action="store_true", help="Print report as JSON to stderr.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args()

    try:
        raw = args.input.read_text(encoding="utf-8") if args.input else sys.stdin.read()
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    normalization = "nfkc" if args.nfkc else ("none" if args.no_normalize else "nfc")
    profile = _resolve_profile(args.profile, args.input)

    cleaned, report = clean_text(
        raw,
        profile=profile,
        normalization=normalization,
        aggressive_homoglyphs=args.aggressive_homoglyphs,
        strip_emoji_glue=args.strip_emoji_glue,
        preserve_bidi_controls=args.preserve_bidi_controls,
    )

    changed = cleaned != raw
    report["would_change"] = changed

    if not args.check:
        try:
            if args.output:
                args.output.write_text(cleaned, encoding="utf-8")
            else:
                sys.stdout.write(cleaned)
        except OSError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2), file=sys.stderr)
    elif report["chars_removed"] or report["chars_replaced"] or report["normalized"]:
        print(
            f"[layer_a] removed={report['chars_removed']} replaced={report['chars_replaced']} "
            f"normalization={report['normalization']} changed={report['normalized']} "
            f"profile={report['profile']}",
            file=sys.stderr,
        )
    if args.check:
        return 1 if changed else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
