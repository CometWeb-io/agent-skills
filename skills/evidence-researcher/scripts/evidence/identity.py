"""Identity helpers: URLs, IDs, fingerprints, pack hashes."""
from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Dict, List, Tuple
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .constants import (
    DEFAULT_TTL_DAYS,
    LIVE_VERIFICATION_TYPES,
    POLICY_VERSION,
    TRACKING_KEYS,
    CLAIM_TYPES,
)
from .util import _norm_text


def canonical_url(url: str) -> str:
    parts = urlsplit(url.strip())
    filtered: List[Tuple[str, str]] = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        low = key.casefold()
        if low.startswith("utm_") or low in TRACKING_KEYS:
            continue
        filtered.append((key, value))
    filtered.sort(key=lambda item: (item[0], item[1]))
    scheme = parts.scheme.lower()
    netloc = parts.netloc.lower()
    path = parts.path or "/"
    query = urlencode(filtered, doseq=True)
    return urlunsplit((scheme, netloc, path, query, ""))



def make_id(kind: str, value: str) -> str:
    prefixes = {
        "research": "res", "claim": "clm", "source": "src", "evidence": "ev",
        "contradiction": "ctr", "search": "srch", "gap": "gap", "watch": "watch",
    }
    if kind not in prefixes:
        raise ValueError(f"unsupported kind: {kind}")
    digest = hashlib.sha256(_norm_text(value).encode("utf-8")).hexdigest()[:12]
    return f"{prefixes[kind]}_{digest}"


def source_policy(claim_type: str) -> Dict[str, Any]:
    return {
        "claim_type": claim_type,
        "default_ttl_days": DEFAULT_TTL_DAYS.get(claim_type),
        "requires_live_verification": claim_type in LIVE_VERIFICATION_TYPES,
        "known_claim_type": claim_type in CLAIM_TYPES,
        "policy_version": POLICY_VERSION,
    }


def fingerprint_source(source: Dict[str, Any]) -> str:
    key = "|".join([
        _norm_text(source.get("canonical_ref")),
        _norm_text(source.get("source_version")),
        _norm_text(source.get("content_hash")),
        _norm_text(source.get("title")),
    ])
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def pack_hash(ledger: Dict[str, Any]) -> str:
    clean = copy.deepcopy(ledger)
    for field in ("pack_hash", "research_status", "stop_reason"):
        clean.pop(field, None)
    payload = json.dumps(clean, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

