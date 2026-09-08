#!/usr/bin/env python3
"""Deterministic helpers for competitive-intelligence snapshots and events.

Standard-library only. The kernel deliberately does not browse, interpret strategy,
or decide whether evidence is truthful; it validates structure, computes stable
hashes/diffs, classifies likely event domains, calculates materiality, checks
freshness, and creates dedupe keys.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Iterable

REQUIRED_SNAPSHOT_KEYS = {
    "schema_version",
    "competitor_id",
    "competitor_name",
    "captured_at",
    "state",
    "evidence",
}

DEFAULT_IGNORED_PATH_SUFFIXES = {
    "captured_at",
    "generated_at",
    "observed_at",
    "last_verified_at",
    "scan_id",
    "snapshot_hash",
    "hash",
    "source_accessed_at",
}

CATEGORY_PATTERNS: list[tuple[str, tuple[str, ...]]] = [
    ("PRICING_PACKAGING", ("pricing", "price", "tier", "billing", "trial", "free_plan", "value_metric", "limit", "quota")),
    ("PRODUCT_CAPABILITY", ("product", "feature", "capabilit", "integration", "api", "release", "platform", "model", "workflow", "changelog")),
    ("POSITIONING_MESSAGING", ("positioning", "headline", "value_proposition", "target_segment", "use_case", "category_language", "messaging")),
    ("CUSTOMER_PROOF", ("proof", "customer", "case_study", "review", "rating", "testimonial")),
    ("DISCOVERY_GTM", ("discovery", "seo", "content", "organic", "paid_media", "ad", "campaign", "partner", "distribution")),
    ("COMPANY_ORG", ("company", "funding", "leadership", "hiring", "geograph", "acquisition", "merger", "headcount")),
    ("TECH_TRUST", ("tech_trust", "technology", "security", "compliance", "status", "certification", "reliability")),
    ("SALES_MOTION", ("sales", "enterprise", "procurement", "reseller", "contract", "sales_motion")),
]

SCORE_WEIGHTS = {
    "relevance": 0.30,
    "magnitude": 0.25,
    "confidence": 0.20,
    "novelty": 0.15,
    "persistence": 0.10,
}

TIER_FACTORS = {1: 1.00, 2: 0.85, 3: 0.70}


def _read_json(path: str | Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def snapshot_hash(snapshot: dict[str, Any]) -> str:
    return _sha256_text(_canonical_json(snapshot))


def state_hash(snapshot: dict[str, Any]) -> str:
    return _sha256_text(_canonical_json(snapshot.get("state", {})))


def validate_snapshot(snapshot: Any) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(snapshot, dict):
        return {"valid": False, "errors": ["snapshot must be a JSON object"], "warnings": []}

    missing = sorted(REQUIRED_SNAPSHOT_KEYS - set(snapshot.keys()))
    if missing:
        errors.append("missing required keys: " + ", ".join(missing))

    if "state" in snapshot and not isinstance(snapshot.get("state"), dict):
        errors.append("state must be an object")
    if "evidence" in snapshot and not isinstance(snapshot.get("evidence"), list):
        errors.append("evidence must be an array")

    competitor_id = snapshot.get("competitor_id")
    if competitor_id is not None and (not isinstance(competitor_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", competitor_id)):
        errors.append("competitor_id must be a stable lowercase slug")

    captured_at = snapshot.get("captured_at")
    if captured_at is not None:
        try:
            _parse_time(str(captured_at))
        except ValueError:
            errors.append("captured_at must be ISO-8601 with timezone")

    if isinstance(snapshot.get("evidence"), list):
        ids: set[str] = set()
        for i, ev in enumerate(snapshot["evidence"]):
            if not isinstance(ev, dict):
                errors.append(f"evidence[{i}] must be an object")
                continue
            eid = ev.get("evidence_id")
            if not eid:
                warnings.append(f"evidence[{i}] has no evidence_id")
            elif eid in ids:
                errors.append(f"duplicate evidence_id: {eid}")
            else:
                ids.add(str(eid))
            if not ev.get("source"):
                warnings.append(f"evidence[{i}] has no source")
            if not ev.get("last_verified_at"):
                warnings.append(f"evidence[{i}] has no last_verified_at")

    return {"valid": not errors, "errors": errors, "warnings": warnings}


def _ignored(path: str, extra_patterns: Iterable[str] | None = None) -> bool:
    last = path.split(".")[-1] if path else ""
    if last in DEFAULT_IGNORED_PATH_SUFFIXES:
        return True
    if extra_patterns:
        for pat in extra_patterns:
            if re.search(pat, path):
                return True
    return False


def _classify(path: str) -> str:
    p = path.lower()
    for category, patterns in CATEGORY_PATTERNS:
        if any(token in p for token in patterns):
            return category
    return "OTHER"


def _change_type(old_exists: bool, new_exists: bool) -> str:
    if not old_exists and new_exists:
        return "ADDED"
    if old_exists and not new_exists:
        return "REMOVED"
    return "MODIFIED"


def _event_key(competitor_id: str, category: str, path: str, before: Any, after: Any) -> str:
    payload = {
        "competitor_id": competitor_id,
        "category": category,
        "field_path": path,
        "before": before,
        "after": after,
    }
    return _sha256_text(_canonical_json(payload))


def diff_snapshots(old: dict[str, Any], new: dict[str, Any], extra_ignore_patterns: Iterable[str] | None = None) -> dict[str, Any]:
    competitor_id = str(new.get("competitor_id") or old.get("competitor_id") or "unknown")
    changes: list[dict[str, Any]] = []

    def walk(before: Any, after: Any, path: str, old_exists: bool = True, new_exists: bool = True) -> None:
        if path and _ignored(path, extra_ignore_patterns):
            return
        if old_exists and new_exists and type(before) is type(after):
            if isinstance(before, dict):
                keys = sorted(set(before) | set(after))
                for key in keys:
                    b_exists = key in before
                    a_exists = key in after
                    walk(before.get(key), after.get(key), f"{path}.{key}" if path else key, b_exists, a_exists)
                return
            if isinstance(before, list):
                if before == after:
                    return
                # Scalar lists are treated as sets: order-only changes are noise.
                if all(not isinstance(x, (dict, list)) for x in before + after):
                    before_set = {_canonical_json(x): x for x in before}
                    after_set = {_canonical_json(x): x for x in after}
                    for k in sorted(before_set.keys() - after_set.keys()):
                        item_path = path + "[]"
                        category = _classify(item_path)
                        changes.append({
                            "change_type": "REMOVED",
                            "field_path": item_path,
                            "before": before_set[k],
                            "after": None,
                            "category": category,
                            "event_key": _event_key(competitor_id, category, item_path, before_set[k], None),
                        })
                    for k in sorted(after_set.keys() - before_set.keys()):
                        item_path = path + "[]"
                        category = _classify(item_path)
                        changes.append({
                            "change_type": "ADDED",
                            "field_path": item_path,
                            "before": None,
                            "after": after_set[k],
                            "category": category,
                            "event_key": _event_key(competitor_id, category, item_path, None, after_set[k]),
                        })
                    return

                # Lists of records can be matched by a stable identity key so a price
                # change in one tier does not become an opaque whole-list modification.
                if before and after and all(isinstance(x, dict) for x in before + after):
                    stable_key = None
                    for candidate in ("id", "slug", "name", "url", "key"):
                        if all(candidate in x for x in before + after):
                            stable_key = candidate
                            break
                    if stable_key:
                        before_map = {str(x[stable_key]): x for x in before}
                        after_map = {str(x[stable_key]): x for x in after}
                        for identity in sorted(set(before_map) | set(after_map)):
                            b_exists = identity in before_map
                            a_exists = identity in after_map
                            item_path = f"{path}[{stable_key}={identity}]"
                            walk(before_map.get(identity), after_map.get(identity), item_path, b_exists, a_exists)
                        return

        if old_exists and new_exists and before == after:
            return

        category = _classify(path)
        change_type = _change_type(old_exists, new_exists)
        b = before if old_exists else None
        a = after if new_exists else None
        changes.append({
            "change_type": change_type,
            "field_path": path,
            "before": b,
            "after": a,
            "category": category,
            "event_key": _event_key(competitor_id, category, path, b, a),
        })

    # Compare normalized competitor state only. Evidence/scan metadata changes are
    # provenance updates, not competitor-state deltas.
    walk(old.get("state", {}), new.get("state", {}), "state")
    return {
        "competitor_id": competitor_id,
        "old_hash": snapshot_hash(old),
        "new_hash": snapshot_hash(new),
        "old_state_hash": state_hash(old),
        "new_state_hash": state_hash(new),
        "change_count": len(changes),
        "changes": changes,
    }


def _score_number(value: Any, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be numeric") from None
    if not math.isfinite(number) or number < 0 or number > 1:
        raise ValueError(f"{name} must be between 0 and 1")
    return number


def materiality_score(event: dict[str, Any]) -> dict[str, Any]:
    components: dict[str, float] = {}
    for name in SCORE_WEIGHTS:
        components[name] = _score_number(event.get(name, 0.0), name)

    try:
        tier = int(event.get("competitor_tier", 1))
    except (TypeError, ValueError):
        tier = 1
    tier_factor = TIER_FACTORS.get(tier, TIER_FACTORS[3])

    base = sum(components[name] * weight for name, weight in SCORE_WEIGHTS.items())
    score = max(0, min(100, round(base * 100 * tier_factor)))
    if score >= 80:
        severity = "CRITICAL"
    elif score >= 65:
        severity = "HIGH"
    elif score >= 45:
        severity = "MEDIUM"
    elif score >= 25:
        severity = "LOW"
    else:
        severity = "NOISE"

    return {
        "score": score,
        "severity": severity,
        "tier_factor": tier_factor,
        "components": components,
        "weights": SCORE_WEIGHTS,
    }


def event_key_from_json(event: dict[str, Any]) -> str:
    competitor_id = str(event.get("competitor_id", "unknown"))
    category = str(event.get("category", _classify(str(event.get("field_path", "")))))
    path = str(event.get("field_path", ""))
    return _event_key(competitor_id, category, path, event.get("before"), event.get("after"))


def _parse_time(value: str) -> dt.datetime:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = dt.datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include timezone")
    return parsed.astimezone(dt.timezone.utc)


def freshness(last_verified_at: str | None, ttl_days: int, as_of: str | None = None) -> dict[str, Any]:
    if not last_verified_at:
        return {"status": "UNKNOWN", "age_days": None, "ttl_days": ttl_days}
    verified = _parse_time(last_verified_at)
    now = _parse_time(as_of) if as_of else dt.datetime.now(dt.timezone.utc)
    age = max(0.0, (now - verified).total_seconds() / 86400.0)
    if ttl_days <= 0:
        raise ValueError("ttl_days must be positive")
    ratio = age / ttl_days
    if ratio <= 0.8:
        status = "CURRENT"
    elif ratio <= 1.0:
        status = "NEAR_EXPIRY"
    else:
        status = "STALE"
    return {"status": status, "age_days": round(age, 3), "ttl_days": ttl_days}




def _atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(value, f, ensure_ascii=False, sort_keys=True, indent=2)
        f.write("\n")
    tmp.replace(path)


def init_workspace(root: str | Path, subject_product: str | None = None) -> dict[str, Any]:
    root_path = Path(root)
    root_path.mkdir(parents=True, exist_ok=True)
    for name in ("competitors", "snapshots", "events", "reports", "raw"):
        (root_path / name).mkdir(parents=True, exist_ok=True)

    config_path = root_path / "config.json"
    created_config = False
    if not config_path.exists():
        config = {
            "schema_version": "1.0",
            "subject_product": {"name": subject_product} if subject_product else {},
            "competitors": [],
            "sources": [],
            "freshness_ttl_days": {
                "pricing": 7,
                "product": 14,
                "positioning": 14,
                "proof": 30,
                "discovery": 30,
                "company": 30,
                "tech_trust": 30,
            },
        }
        _atomic_write_json(config_path, config)
        created_config = True

    return {
        "root": str(root_path),
        "config_path": str(config_path),
        "created_config": created_config,
    }


def _safe_snapshot_timestamp(value: str) -> str:
    parsed = _parse_time(value)
    return parsed.strftime("%Y%m%dT%H%M%SZ")


def accept_snapshot(root: str | Path, snapshot_path: str | Path) -> dict[str, Any]:
    root_path = Path(root)
    init_workspace(root_path)
    snapshot = _read_json(snapshot_path)
    validation = validate_snapshot(snapshot)
    if not validation["valid"]:
        raise ValueError("invalid snapshot: " + "; ".join(validation["errors"]))

    competitor_id = str(snapshot["competitor_id"])
    current_path = root_path / "competitors" / competitor_id / "current.json"
    previous = _read_json(current_path) if current_path.exists() else None

    full_hash = snapshot_hash(snapshot)
    s_hash = state_hash(snapshot)
    timestamp = _safe_snapshot_timestamp(str(snapshot["captured_at"]))
    archive_path = root_path / "snapshots" / competitor_id / f"{timestamp}--{full_hash.split(':', 1)[1][:12]}.json"
    if not archive_path.exists():
        _atomic_write_json(archive_path, snapshot)

    delta = diff_snapshots(previous, snapshot) if isinstance(previous, dict) else None
    previous_state_hash = state_hash(previous) if isinstance(previous, dict) else None
    _atomic_write_json(current_path, snapshot)

    return {
        "competitor_id": competitor_id,
        "snapshot_hash": full_hash,
        "state_hash": s_hash,
        "previous_state_hash": previous_state_hash,
        "state_changed": previous_state_hash is None or previous_state_hash != s_hash,
        "snapshot_path": str(archive_path),
        "current_path": str(current_path),
        "change_count": delta["change_count"] if delta else 0,
        "changes": delta["changes"] if delta else [],
        "validation_warnings": validation["warnings"],
    }


def _iter_event_records(events_root: Path):
    if not events_root.exists():
        return
    for path in sorted(events_root.glob("*.jsonl")):
        with open(path, "r", encoding="utf-8") as f:
            for line_number, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(row, dict):
                    yield path, line_number, row


def _event_revision_signature(event: dict[str, Any]) -> str:
    relevant = {
        "verification_state": event.get("verification_state"),
        "materiality": event.get("materiality"),
        "disposition": event.get("disposition"),
        "status": event.get("status"),
        "implication": event.get("implication"),
        "implication_confidence": event.get("implication_confidence"),
    }
    return _sha256_text(_canonical_json(relevant))


def append_event(root: str | Path, event: dict[str, Any]) -> dict[str, Any]:
    root_path = Path(root)
    init_workspace(root_path)
    row = dict(event)

    for required in ("competitor_id", "category", "field_path"):
        if not row.get(required):
            raise ValueError(f"event requires {required}")

    row.setdefault("event_key", event_key_from_json(row))
    observed_at = row.get("first_observed_at") or row.get("last_verified_at")
    if not observed_at:
        observed_at = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
        row["first_observed_at"] = observed_at
    parsed_observed = _parse_time(str(observed_at))
    month = parsed_observed.strftime("%Y-%m")

    last_same: dict[str, Any] | None = None
    for _, _, existing in _iter_event_records(root_path / "events") or []:
        if existing.get("event_key") == row["event_key"]:
            last_same = existing

    if last_same and _event_revision_signature(last_same) == _event_revision_signature(row):
        return {
            "appended": False,
            "duplicate": True,
            "event_key": row["event_key"],
            "existing_event_id": last_same.get("event_id"),
        }

    event_id_seed = {
        "event_key": row["event_key"],
        "first_observed_at": observed_at,
        "revision_signature": _event_revision_signature(row),
    }
    row.setdefault("event_id", "evt-" + _sha256_text(_canonical_json(event_id_seed)).split(":", 1)[1][:16])
    if last_same:
        row.setdefault("revision_of", last_same.get("event_id"))

    event_path = root_path / "events" / f"{month}.jsonl"
    event_path.parent.mkdir(parents=True, exist_ok=True)
    with open(event_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")

    return {
        "appended": True,
        "duplicate": False,
        "revision": bool(last_same),
        "event_id": row["event_id"],
        "event_key": row["event_key"],
        "event_path": str(event_path),
    }


def _parse_event_json(value: str) -> dict[str, Any]:
    if value.startswith("@"):
        data = _read_json(value[1:])
    else:
        data = json.loads(value)
    if not isinstance(data, dict):
        raise ValueError("event JSON must be an object")
    return data


def _print(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Competitive Intelligence deterministic kernel")
    sub = p.add_subparsers(dest="command", required=True)

    h = sub.add_parser("hash", help="Compute canonical snapshot and normalized-state SHA-256")
    h.add_argument("--snapshot", required=True)

    v = sub.add_parser("validate-snapshot", help="Validate required snapshot structure")
    v.add_argument("--snapshot", required=True)

    d = sub.add_parser("diff", help="Compute normalized field-level snapshot delta")
    d.add_argument("--old", required=True)
    d.add_argument("--new", required=True)
    d.add_argument("--ignore-regex", action="append", default=[])

    s = sub.add_parser("score", help="Compute event materiality score")
    s.add_argument("--event-json", required=True, help="JSON object or @path/to/file.json")

    e = sub.add_parser("event-key", help="Compute stable dedupe key for an event transition")
    e.add_argument("--event-json", required=True, help="JSON object or @path/to/file.json")

    f = sub.add_parser("freshness", help="Evaluate a last-verified timestamp against TTL")
    f.add_argument("--last-verified-at")
    f.add_argument("--ttl-days", type=int, required=True)
    f.add_argument("--as-of")


    iw = sub.add_parser("init-workspace", help="Create the persistent CI workspace without overwriting config")
    iw.add_argument("--root", default=".competitive-intelligence")
    iw.add_argument("--subject-product")

    ac = sub.add_parser("accept-snapshot", help="Validate, archive, diff, and promote a snapshot to current.json")
    ac.add_argument("--root", default=".competitive-intelligence")
    ac.add_argument("--snapshot", required=True)

    ae = sub.add_parser("append-event", help="Append a deduplicated event or material revision to the event log")
    ae.add_argument("--root", default=".competitive-intelligence")
    ae.add_argument("--event-json", required=True, help="JSON object or @path/to/file.json")

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "hash":
            snapshot = _read_json(args.snapshot)
            _print({"snapshot_hash": snapshot_hash(snapshot), "state_hash": state_hash(snapshot)})
        elif args.command == "validate-snapshot":
            result = validate_snapshot(_read_json(args.snapshot))
            _print(result)
            if not result["valid"]:
                return 2
        elif args.command == "diff":
            _print(diff_snapshots(_read_json(args.old), _read_json(args.new), args.ignore_regex))
        elif args.command == "score":
            _print(materiality_score(_parse_event_json(args.event_json)))
        elif args.command == "event-key":
            _print({"event_key": event_key_from_json(_parse_event_json(args.event_json))})
        elif args.command == "freshness":
            _print(freshness(args.last_verified_at, args.ttl_days, args.as_of))
        elif args.command == "init-workspace":
            _print(init_workspace(args.root, args.subject_product))
        elif args.command == "accept-snapshot":
            _print(accept_snapshot(args.root, args.snapshot))
        elif args.command == "append-event":
            _print(append_event(args.root, _parse_event_json(args.event_json)))
        else:
            raise AssertionError("unreachable")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
