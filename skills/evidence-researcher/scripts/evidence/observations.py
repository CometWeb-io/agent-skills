"""Execute caller-owned checks against controlled local JSON, not supplied receipts."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import stat
from typing import Any

from .constants import OBSERVATION_OPERATORS, OBSERVATION_SCOPES
from .util import _load_json, _member, _parse_dt
from .validators import validate_ledger

_LIMIT = 4 * 1024 * 1024
_PLAN_FIELDS = {"version", "research_id", "as_of", "context_hash", "checks"}
_CHECK_FIELDS = {"claim_id", "claim_hash", "source_id", "source_hash", "evidence_id", "evidence_hash",
                 "path", "sha256", "pointer", "expected", "observed_scope"}


def _canonical(value: Any) -> bytes:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    if len(encoded) > _LIMIT:
        raise ValueError("check input exceeds size limit")
    return encoded


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _parts(path: Any) -> list[str]:
    if not isinstance(path, str) or not 1 <= len(path) <= 512 or any(c in path for c in ("\\", ":", "\0")):
        raise ValueError("invalid controlled source path")
    parts = path.split("/")
    if len(parts) > 16 or any(part in {"", ".", ".."} for part in parts):
        raise ValueError("invalid controlled source path")
    return parts


def _tokens(pointer: Any) -> list[str]:
    if not isinstance(pointer, str) or not 1 <= len(pointer) <= 512 or not pointer.startswith("/"):
        raise ValueError("check requires a nonempty JSON pointer")
    parts = pointer[1:].split("/")
    if len(parts) > 32 or re.search(r"~(?![01])", pointer):
        raise ValueError("invalid JSON pointer")
    return [part.replace("~1", "/").replace("~0", "~") for part in parts]


def _read_source(root: Path, parts: list[str]) -> bytes:
    # Walk opened directories: resolving then opening a pathname leaves a symlink race.
    directory = os.open(root.anchor, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    source = None
    try:
        for part in (*root.parts[1:], *parts[:-1]):
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            os.close(directory)
            directory = child
        source = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        before = os.fstat(source)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size > _LIMIT:
            raise ValueError("source is not a bounded unaliased regular file")
        chunks = []
        total = 0
        while True:
            chunk = os.read(source, min(65536, _LIMIT + 1 - total))
            if not chunk:
                break
            total += len(chunk)
            if total > _LIMIT:
                raise ValueError("source exceeds size limit")
            chunks.append(chunk)
        after = os.fstat(source)
        if (before.st_size, before.st_mtime_ns, before.st_ctime_ns, before.st_nlink) != (
                after.st_size, after.st_mtime_ns, after.st_ctime_ns, after.st_nlink) or total != after.st_size:
            raise ValueError("source changed during observation")
        return b"".join(chunks)
    finally:
        if source is not None:
            os.close(source)
        os.close(directory)


def _value_at(value: Any, tokens: list[str]) -> Any:
    for token in tokens:
        if isinstance(value, dict):
            value = value[token]
        elif isinstance(value, list) and re.fullmatch(r"0|[1-9][0-9]*", token):
            value = value[int(token)]
        else:
            raise ValueError("pointer does not identify a value")
    return value


def observe_facts(ledger: dict, plan: dict, source_root: str | Path, consumer_context: dict) -> dict:
    """Rerun explicit checks; root/plan/context must be independently controlled by the caller.

    A check establishes the pinned structured proposition in the observed scope.
    It does not authenticate a document's authority, interpret arbitrary prose,
    prove external currentness, or grant permission to execute a decision.
    """
    if not isinstance(plan, dict) or set(plan) != _PLAN_FIELDS or plan.get("version") != "local-fact-check/v1":
        raise ValueError("invalid local fact-check plan")
    if not isinstance(consumer_context, dict) or not consumer_context:
        raise ValueError("actual consumer context is required")
    if _parse_dt(plan.get("as_of")) is None:
        raise ValueError("fact-check plan requires an aware as_of")
    checks = plan.get("checks")
    if not isinstance(checks, list) or not 1 <= len(checks) <= 32:
        raise ValueError("fact-check plan requires 1 to 32 checks")
    seen = set()
    for check in checks:
        if not isinstance(check, dict):
            raise ValueError("invalid fact-check fields")
        operator = check.get("operator", "equals")
        if not _member(operator, OBSERVATION_OPERATORS):
            raise ValueError("unsupported fact-check operator")
        extra = {"operator", "where"} if operator == "count_matching" else ({"operator"} if "operator" in check else set())
        if set(check) != _CHECK_FIELDS | extra:
            raise ValueError("invalid fact-check fields")
        if operator == "count_matching":
            where, expected = check["where"], check["expected"]
            if (not isinstance(where, dict) or not 1 <= len(where) <= 32
                    or any(not isinstance(k, str) or not 1 <= len(k) <= 128 or type(v) not in (str, int, float, bool, type(None)) for k, v in where.items())
                    or isinstance(expected, bool) or not isinstance(expected, int) or expected < 0):
                raise ValueError("count requires bounded scalar filters and a nonnegative integer")
        if operator == "text_present" and (check.get("observed_scope") != "document_content"
                or not isinstance(check.get("expected"), str) or not 1 <= len(check["expected"]) <= 4096):
            raise ValueError("text presence requires a bounded literal and document-content scope")
        for field in ("claim_id", "source_id", "evidence_id"):
            if not isinstance(check[field], str) or not check[field].strip():
                raise ValueError("fact-check identity is missing")
        if check["claim_id"] in seen:
            raise ValueError("duplicate checked claim")
        seen.add(check["claim_id"])
        for field in ("claim_hash", "source_hash", "evidence_hash", "sha256"):
            if not isinstance(check[field], str) or not re.fullmatch(r"[0-9a-f]{64}", check[field]):
                raise ValueError("invalid fact-check hash")
        if not _member(check["observed_scope"], OBSERVATION_SCOPES):
            raise ValueError("unsupported observation scope")
        _parts(check["path"])
        _tokens(check["pointer"])
    if not isinstance(plan["context_hash"], str) or not re.fullmatch(r"[0-9a-f]{64}", plan["context_hash"]):
        raise ValueError("invalid consumer context hash")
    report = {"status": "NOT_ASSESSED", "plan_hash": _digest(plan), "context_hash": _digest(consumer_context),
              "claims": [], "execution_authorized": False,
              "limit": "controlled local propositions only; external authority and currentness are not authenticated"}
    if not validate_ledger(ledger)["valid"]:
        report["reason"] = "invalid_ledger"
        return report
    if (plan["context_hash"] != report["context_hash"] or plan["research_id"] != ledger["research_id"]
            or plan["as_of"] != ledger["research_contract"]["as_of"]):
        report["reason"] = "consumer_or_research_binding_mismatch"
        return report
    if (os.open not in os.supports_dir_fd or any(not hasattr(os, name) for name in (
            "O_DIRECTORY", "O_NOFOLLOW", "O_NONBLOCK"))):
        report["reason"] = "safe_source_open_unavailable"
        return report
    root = Path(source_root)
    if not root.is_absolute():
        raise ValueError("controlled source root must be absolute")
    claims = {row["claim_id"]: row for row in ledger["claims"]}
    sources = {row["source_id"]: row for row in ledger["sources"]}
    edges = {row["evidence_id"]: row for row in ledger["evidence"]}
    for check in checks:
        claim = claims.get(check["claim_id"])
        source = sources.get(check["source_id"])
        edge = edges.get(check["evidence_id"])
        row = {"claim_id": check["claim_id"], "status": "NOT_ASSESSED",
               "observed_scope": check["observed_scope"]}
        report["claims"].append(row)
        if (not claim or not source or not edge or _digest(claim) != check["claim_hash"]
                or _digest(source) != check["source_hash"] or _digest(edge) != check["evidence_hash"]):
            row["reason"] = "record_binding_mismatch"
            continue
        if (claim.get("basis") != "verified_fact" or claim.get("epistemic_kind") != "FACT"
                or claim.get("status") != "VERIFIED" or edge.get("basis") != "verified_fact"
                or edge["claim_id"] != check["claim_id"] or edge["source_id"] != check["source_id"]
                or edge.get("direction") != "SUPPORT" or edge.get("admission") != "ACCEPTED"
                or edge.get("locator") != check["pointer"]):
            row["reason"] = "not_an_applicable_fact_edge"
            continue
        try:
            raw = _read_source(root, _parts(check["path"]))
            row["source_sha256"] = hashlib.sha256(raw).hexdigest()
            if row["source_sha256"] != check["sha256"]:
                row.update(status="MISMATCH", reason="source_revision_mismatch")
                continue
            text = raw.decode("utf-8")
            # The CLI loader also accepts paths; source bytes must never select another file.
            if not text.lstrip().startswith(("{", "[")):
                raise ValueError("source must contain structured JSON")
            data = _load_json(text)
            if not isinstance(data, (dict, list)):
                raise ValueError("source must contain structured JSON")
            actual = _value_at(data, _tokens(check["pointer"]))
            if check.get("operator", "equals") == "count_matching":
                if not isinstance(actual, list) or len(actual) > 100000 or any(not isinstance(item, dict) for item in actual):
                    raise ValueError("count requires a bounded array of objects")
                filters = {k: _canonical(v) for k, v in check["where"].items()}
                actual = sum(all(k in item and _canonical(item[k]) == v for k, v in filters.items()) for item in actual)
            expected = check["expected"]
            if check.get("operator", "equals") == "text_present":
                if not isinstance(actual, str):
                    raise ValueError("text presence requires a string field")
                actual, expected = expected in actual, True
            row["status"] = "MATCH" if _canonical(actual) == _canonical(expected) else "MISMATCH"
            row["reason"] = "predicate_matched" if row["status"] == "MATCH" else "predicate_mismatch"
        except (OSError, ValueError, TypeError, KeyError, IndexError, UnicodeError, RecursionError):
            # No raw path, JSON excerpt or value in errors: controlled sources can be private.
            row["reason"] = "source_unreadable_or_invalid"
    report["status"] = "CHECKED" if all(row["status"] == "MATCH" for row in report["claims"]) else "NOT_CHECKED"
    return report
