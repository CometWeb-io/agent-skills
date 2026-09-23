from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from typing import Any

def _norm(text: str) -> str:
    return str(text or "").casefold()


def _hits(text: str, keywords: list[str] | tuple[str, ...]) -> int:
    t = _norm(text)
    return sum(1 for kw in keywords if kw.casefold() in t)


def _clamp01(value: Any) -> float:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return 0.0
    if math.isnan(value) or math.isinf(value):
        return 0.0
    return max(0.0, min(1.0, value))


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(v for v in values if v))


def _setish(value: Any) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, str):
        return {value} if value else set()
    out = set()
    for item in value:
        if isinstance(item, dict):
            token = item.get("id") or item.get("key") or item.get("claim_id") or item.get("text") or item.get("value")
            if token:
                out.add(str(token))
        elif item:
            out.add(str(item))
    return out


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    union = a | b
    return len(a & b) / len(union) if union else 0.0


def _boolean(value: Any, name: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{name} must be boolean")
    return value


def _finite_number(value: Any, name: str) -> float:
    if type(value) not in (int, float):
        raise ValueError(f"{name} must be a finite number")
    try:
        number = float(value)
    except OverflowError as exc:
        raise ValueError(f"{name} must be finite") from exc
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number


def _unit_interval(value: Any, name: str) -> float:
    number = _finite_number(value, name)
    if not 0 <= number <= 1:
        raise ValueError(f"{name} must be between zero and one")
    return number


def _aware_time(value: Any, name: str) -> datetime:
    if not isinstance(value, str) or len(value) > 64 or "T" not in value:
        raise ValueError(f"{name} must be a timezone-aware timestamp")
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{name} is not an ISO timestamp") from exc
    if stamp.tzinfo is None:
        raise ValueError(f"{name} requires a timezone")
    return stamp


def _rows(value: Any, name: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or len(value) > 10000 or any(not isinstance(v, dict) for v in value):
        raise ValueError(f"{name} must be a bounded list of objects")
    return value


def _strings(value: Any, name: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(v, str) or not v.strip() for v in value):
        raise ValueError(f"{name} must be a list of nonempty strings")
    if len(value) > 10000 or len(value) != len(set(value)):
        raise ValueError(f"{name} contains duplicate or excessive identifiers")
    return value


def _mode_name(mode: Any) -> str:
    if not isinstance(mode, str):
        raise ValueError("mode must be FAST, LIGHT, STANDARD or DEEP")
    normalized = mode.strip().upper()
    if normalized == "LIGHT":
        normalized = "FAST"
    if normalized not in {"FAST", "STANDARD", "DEEP"}:
        raise ValueError("unknown council mode")
    return normalized


def _load_cli_json(text: str) -> Any:
    if len(text.encode("utf-8")) > 4 * 1024 * 1024:
        raise ValueError("JSON input exceeds limit")
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result
    def number(text):
        value = float(text)
        if not math.isfinite(value):
            raise ValueError("non-finite JSON number")
        return value
    def constant(_):
        raise ValueError("non-finite JSON constant")
    return json.loads(text, object_pairs_hook=pairs, parse_float=number, parse_constant=constant)

def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    raw = str(value).strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        try:
            # Date-only fallback: deliberately naive, and every caller
            # reconciles tzinfo against the other operand before comparing.
            return datetime.strptime(raw[:10], "%Y-%m-%d")  # noqa: DTZ007
        except ValueError:
            return None


def _recency_factor(updated_at: str | None, as_of: str | None) -> float:
    updated = _parse_date(updated_at)
    # Timezone-aware: utcnow() is deprecated and returns a naive value, which
    # is a poor default in a kernel whose whole job is temporal correctness.
    now = _parse_date(as_of) or datetime.now(timezone.utc)
    if not updated:
        return 0.0
    if updated.tzinfo is not None and now.tzinfo is None:
        now = now.replace(tzinfo=updated.tzinfo)
    if updated.tzinfo is None and now.tzinfo is not None:
        updated = updated.replace(tzinfo=now.tzinfo)
    age_days = max(0, (now - updated).days)
    return math.exp(-age_days / 730.0)

def _is_non_thesis_row(row: dict[str, Any]) -> bool:
    attrs = set(row.get("outcome_attribution") or [])
    if "thesis_wrong" in attrs or "thesis_correct" in attrs:
        return False
    return bool(attrs & {"execution_failure", "external_shock", "wrong_timing"})


def _sample_strength(n: int) -> str:
    return "none" if n < 5 else ("weak" if n < 15 else "normal")

def _hours_between(older: datetime, newer: datetime) -> float:
    if older.tzinfo is not None and newer.tzinfo is None:
        newer = newer.replace(tzinfo=older.tzinfo)
    if older.tzinfo is None and newer.tzinfo is not None:
        older = older.replace(tzinfo=newer.tzinfo)
    return max(0.0, (newer - older).total_seconds() / 3600.0)
