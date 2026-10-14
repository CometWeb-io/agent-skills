#!/usr/bin/env python3
"""Count raw UTF-8 body tokens separated by Python Unicode whitespace.

Kept identical in content-writer and ai-humanize for standalone installation.
"""

import argparse
import json
from pathlib import Path


def report(verdict, word_count=None, min_words=None, max_words=None, error=None):
    result = {
        "verdict": verdict,
        "word_count": word_count,
        "min_words": min_words,
        "max_words": max_words,
        "checked_bounds": verdict in {"PASS", "FAIL"},
    }
    if error:
        result["error"] = error
    print(json.dumps(result))


class Parser(argparse.ArgumentParser):
    def error(self, message):
        report("ERROR", error=message)
        self.exit(2)


def main():
    parser = Parser(description=__doc__)
    parser.add_argument("body", type=Path, help="Explicit body-only UTF-8 file; no section extraction.")
    parser.add_argument("--min-words", type=int)
    parser.add_argument("--max-words", type=int)
    args = parser.parse_args()
    low, high = args.min_words, args.max_words
    if (low is not None and low < 0) or (high is not None and high < 0):
        report("ERROR", min_words=low, max_words=high, error="Bounds must be nonnegative integers.")
        return 2
    if low is not None and high is not None and low > high:
        report("ERROR", min_words=low, max_words=high, error="Minimum exceeds maximum.")
        return 2
    try:
        if not args.body.is_file():
            raise OSError("Not a regular file")
        count = len(args.body.read_text(encoding="utf-8").split())
    except (OSError, UnicodeError, ValueError):
        report("ERROR", min_words=low, max_words=high, error="Cannot read a regular UTF-8 body file.")
        return 2
    if low is None and high is None:
        verdict = "COUNTED"
    else:
        verdict = "PASS" if (low is None or count >= low) and (high is None or count <= high) else "FAIL"
    report(verdict, count, low, high)
    return 1 if verdict == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
