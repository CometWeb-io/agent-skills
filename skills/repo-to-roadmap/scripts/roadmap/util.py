"""Shared helpers for the repo-to-roadmap kernel."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

from .constants import (
    FRESHNESS,
    MAX_JSON_BYTES,
)


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def require_score(value: Any, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be numeric") from exc
    if not 0 <= number <= 5:
        raise ValueError(f"{field} must be between 0 and 5")
    return number


def require_probability_like(value: Any, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be numeric") from exc
    if not 0 <= number <= 1:
        raise ValueError(f"{field} must be between 0 and 1")
    return number


def normalized(value: Any) -> str:
    return str(value).strip()


def normalized_lower(value: Any) -> str:
    return normalized(value).lower()


def normalized_upper(value: Any) -> str:
    return normalized(value).upper()


def require_choice(value: Any, field: str, choices: set[str], case: str = "lower") -> str:
    if case == "upper":
        clean = normalized_upper(value)
    else:
        clean = normalized_lower(value)
    if clean not in choices:
        allowed = ", ".join(sorted(choices))
        raise ValueError(f"{field} must be one of: {allowed}")
    return clean


def default_claim_type(lane: str) -> str:
    return {
        "implementation": "presence",
        "intent": "intent",
        "outcome": "outcome",
        "operational": "operational",
        "external": "external_current",
    }[lane]


def freshness_value(value: Any) -> str:
    raw = normalized(value or "UNKNOWN")
    aliases = {
        "current": "CURRENT",
        "recent": "CURRENT",
        "near_expiry": "NEAR_EXPIRY",
        "near-expiry": "NEAR_EXPIRY",
        "not_time_sensitive": "NOT_TIME_SENSITIVE",
        "not-time-sensitive": "NOT_TIME_SENSITIVE",
        "dated": "STALE",
        "stale": "STALE",
        "superseded": "SUPERSEDED",
        "unknown": "UNKNOWN",
    }
    clean = aliases.get(raw.lower(), raw.upper())
    if clean not in FRESHNESS:
        raise ValueError(f"freshness must be one of: {', '.join(sorted(FRESHNESS))}")
    return clean


def stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def by_id(rows: Any, field: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    if not isinstance(rows, list):
        return result
    for row in rows:
        if not isinstance(row, dict) or row.get(field) in (None, ""):
            continue
        result[normalized(row[field])] = row
    return result


def changed_ids(before_rows: Any, after_rows: Any, field: str) -> Tuple[List[str], List[str], List[str]]:
    before = by_id(before_rows, field)
    after = by_id(after_rows, field)
    all_ids = sorted(set(before) | set(after))
    changed = [item_id for item_id in all_ids if stable_json(before.get(item_id)) != stable_json(after.get(item_id))]
    removed = sorted(set(before) - set(after))
    added = sorted(set(after) - set(before))
    return changed, added, removed


def parse_json_arg(value: str, *, max_bytes: int | None = None) -> Any:
    def unique_pairs(rows):
        result = {}
        for key, val in rows:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = val
        return result
    def reject_constant(_):
        raise ValueError("non-finite JSON number")
    limit = MAX_JSON_BYTES if max_bytes is None else max_bytes
    if value.startswith("@"):
        with open(value[1:], "rb") as handle:
            raw = handle.read(limit + 1)
    else:
        raw = value.encode("utf-8")
    if len(raw) > limit:
        raise ValueError("JSON input exceeds byte limit")
    data = json.loads(raw, object_pairs_hook=unique_pairs, parse_constant=reject_constant)
    stable_json(data).encode("utf-8")  # Also reject overflowed floats and lone surrogates.
    return data

