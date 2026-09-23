"""Shared helpers for the Evidence Researcher kernel."""
from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .constants import LIVE_VERIFICATION_TYPES

def _json_dump(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))


def _load_json(value: str) -> Any:
    """Read bounded UTF-8 JSON without duplicate-key or non-finite coercion."""
    limit = 8 * 1024 * 1024
    if value.lstrip().startswith(("{", "[")):
        text = value
    else:
        path = Path(value)
        if path.is_file():
            with path.open("rb") as handle:
                raw = handle.read(limit + 1)
            if len(raw) > limit:
                raise ValueError("JSON input exceeds size limit")
            text = raw.decode("utf-8")
        else:
            text = value
    if len(text.encode("utf-8")) > limit:
        raise ValueError("JSON input exceeds size limit")

    def unique(items):
        result = {}
        for key, item in items:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = item
        return result

    def reject_constant(value):
        raise ValueError("non-finite JSON number")

    result = json.loads(text, object_pairs_hook=unique, parse_constant=reject_constant)
    # A finite-looking exponent such as 1e999 can also decode to infinity.
    pending = [result]
    while pending:
        item = pending.pop()
        if isinstance(item, float) and not math.isfinite(item):
            raise ValueError("non-finite JSON number")
        if isinstance(item, dict):
            pending.extend(item.values())
        elif isinstance(item, list):
            pending.extend(item)
    return result


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not isinstance(value, str) or "T" not in value:
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    return dt if dt.tzinfo is not None else None


def _norm_text(value: Any) -> str:
    return " ".join(str(value or "").strip().casefold().split())


def _id_index(rows: Iterable[Dict[str, Any]], field: str) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        value = row.get(field)
        if isinstance(value, str) and value:
            out[value] = row
    return out


def _claim_needs_freshness(claim: Dict[str, Any]) -> bool:
    if claim.get("claim_type") in LIVE_VERIFICATION_TYPES | {"current_fact"}:
        return True
    if claim.get("temporal_sensitivity") in {"high", "medium"}:
        return True
    return claim.get("claim_type") not in {"historical_fact", "doctrine_framework"} and claim.get("temporal_sensitivity") != "static"


def _dependency_cycles(claims: List[Dict[str, Any]]) -> List[List[str]]:
    graph = {str(c.get("claim_id")): [str(x) for x in c.get("depends_on_claim_ids", [])] for c in claims if c.get("claim_id")}
    cycles: List[List[str]] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def dfs(node: str, stack: List[str]) -> None:
        if node in visiting:
            try:
                start = stack.index(node)
                cycle = stack[start:] + [node]
            except ValueError:
                cycle = [node, node]
            if cycle not in cycles:
                cycles.append(cycle)
            return
        if node in visited:
            return
        visiting.add(node)
        stack.append(node)
        for nxt in graph.get(node, []):
            if nxt in graph:
                dfs(nxt, stack)
        stack.pop()
        visiting.remove(node)
        visited.add(node)

    for node in graph:
        dfs(node, [])
    return cycles


def _source_lineage_cycles(sources: List[Dict[str, Any]]) -> List[List[str]]:
    graph = {str(s.get("source_id")): [str(x) for x in s.get("derived_from_source_ids", [])] for s in sources if s.get("source_id")}
    cycles: List[List[str]] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def dfs(node: str, stack: List[str]) -> None:
        if node in visiting:
            try:
                start = stack.index(node)
                cycle = stack[start:] + [node]
            except ValueError:
                cycle = [node, node]
            if cycle not in cycles:
                cycles.append(cycle)
            return
        if node in visited:
            return
        visiting.add(node)
        stack.append(node)
        for nxt in graph.get(node, []):
            if nxt in graph:
                dfs(nxt, stack)
        stack.pop()
        visiting.remove(node)
        visited.add(node)

    for node in graph:
        dfs(node, [])
    return cycles
