#!/usr/bin/env python3
from __future__ import annotations

from typing import Any

import argparse
import hashlib
import json
import re
from pathlib import Path

STAGES = [
    "BRIEFED",
    "SOURCE_READY",
    "OUTLINE_LOCKED",
    "DRAFTED",
    "CLAIMS_RECONCILED",
    "EDITED",
    "MASTER_LOCKED",
    "FORMAT_READY",
    "RELEASE_READY",
    "PUBLISHED",
]


def _derived_ready(report: dict[str, Any]) -> bool:
    artifacts = report.get("derived_artifacts") or []
    master_hash = (report.get("canonical_master") or {}).get("sha256")
    if not artifacts or not master_hash:
        return False
    for item in artifacts:
        if item.get("generation_status") != "COMPLETE":
            return False
        if item.get("master_sha256") != master_hash:
            return False
        fmt = str(item.get("format") or "").upper()
        if fmt in {"DOCX", "PDF"}:
            if item.get("qa_required") is not True or item.get("qa_status") != "PASS":
                return False
        elif item.get("qa_required") is True and item.get("qa_status") != "PASS":
            return False
        elif item.get("qa_required") is False and item.get("qa_status") not in {"PASS", "NOT_REQUIRED"}:
            return False
        if item.get("parity_status") != "PASS":
            return False
    return True


def infer_stage(report: dict[str, Any]) -> str:
    lifecycle = report.get("lifecycle") or {}
    if not lifecycle.get("brief_complete"):
        return "BRIEFED"
    stage = "BRIEFED"
    if not lifecycle.get("sources_admitted"):
        return stage
    stage = "SOURCE_READY"
    if not lifecycle.get("outline_locked"):
        return stage
    stage = "OUTLINE_LOCKED"
    if not lifecycle.get("draft_complete"):
        return stage
    stage = "DRAFTED"
    if not lifecycle.get("claims_reconciled"):
        return stage
    stage = "CLAIMS_RECONCILED"
    if not lifecycle.get("edited_complete"):
        return stage
    stage = "EDITED"
    if not lifecycle.get("master_locked"):
        return stage

    fidelity = report.get("fidelity") or {}
    if fidelity.get("required") is True and fidelity.get("passed") is not True:
        return stage

    stage = "MASTER_LOCKED"
    if not _derived_ready(report):
        return stage
    stage = "FORMAT_READY"
    if not lifecycle.get("release_ready"):
        return stage
    stage = "RELEASE_READY"
    if not report.get("publication_evidence"):
        return stage
    return "PUBLISHED"


VALID_MODES = {"BUILD", "SOURCE_BOUND", "RESEARCH_EXPAND", "REFRESH"}


def _stage_index(stage: str) -> int:
    try:
        return STAGES.index(stage)
    except ValueError:
        return -1


def validate_report(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("protocol_version") != "longform-publisher/1":
        errors.append("PROTOCOL_VERSION_INVALID")

    mode = report.get("mode")
    if mode not in VALID_MODES:
        errors.append("MODE_INVALID")

    sources = report.get("sources") or []
    source_by_id = {s.get("id"): s for s in sources if s.get("id")}
    policy = report.get("source_policy") or {}
    if mode == "SOURCE_BOUND" or policy.get("mode") == "SOURCE_BOUND":
        allowed = set(policy.get("authorized_source_ids") or [])
        if any(s.get("id") not in allowed or s.get("authorized") is not True for s in sources):
            errors.append("SOURCE_BOUND_UNAUTHORIZED_SOURCE")

    for claim in report.get("claim_uses") or []:
        refs = claim.get("evidence_refs") or []
        if any(ref not in source_by_id for ref in refs):
            errors.append("EVIDENCE_REF_UNRESOLVED")
        material = claim.get("materiality") in {"CRITICAL", "MATERIAL"}
        if material and claim.get("claim_kind") == "FACT":
            refs = claim.get("evidence_refs") or []
            if claim.get("support_status") != "SUPPORTED" or not refs:
                errors.append("MATERIAL_CLAIM_UNSUPPORTED")
            if claim.get("volatile_current") is True and refs:
                freshness = [source_by_id.get(ref, {}).get("freshness") for ref in refs]
                if not any(x in {"CURRENT", "NEAR_EXPIRY"} for x in freshness):
                    errors.append("VOLATILE_CLAIM_STALE_EVIDENCE")

    lifecycle = report.get("lifecycle") or {}
    master = report.get("canonical_master") or {}
    if lifecycle.get("draft_complete") and (not master.get("path") or not master.get("sha256")):
        errors.append("CANONICAL_MASTER_REQUIRED")

    if lifecycle.get("release_ready"):
        for gap in report.get("unresolved_gaps") or []:
            if gap.get("materiality") == "CRITICAL" and gap.get("status") not in {"CLOSED", "RESOLVED", "SCOPED_OUT"}:
                errors.append("CRITICAL_GAP_OPEN")
                break

    declared = report.get("current_stage")
    inferred = infer_stage(report)
    if declared not in STAGES:
        errors.append("CURRENT_STAGE_INVALID")
    elif _stage_index(declared) > _stage_index(inferred):
        errors.append("STAGE_INFLATION")

    if declared == "PUBLISHED" and not report.get("publication_evidence"):
        errors.append("PUBLISHED_WITHOUT_EVIDENCE")

    publication_type = str((report.get("publication") or {}).get("type") or "").upper()
    if publication_type in {"SCIENTIFIC_MANUSCRIPT", "ACADEMIC_PAPER", "RESEARCH_PAPER"} and declared in {"RELEASE_READY", "PUBLISHED"}:
        readiness = report.get("scientific_readiness") or {}
        readiness_ok = (
            readiness.get("status") == "PASS"
            and readiness.get("source") == "research-program-operator"
            and readiness.get("evidence_ref") in source_by_id
        )
        if not readiness_ok:
            errors.append("SCIENTIFIC_READINESS_REQUIRED")

    return list(dict.fromkeys(errors))


_PLACEHOLDER_PATTERNS = [
    re.compile(r"\[\s*TODO\b", re.IGNORECASE),
    re.compile(r"\bTBD\b", re.IGNORECASE),
    re.compile(r"\bFIXME\b", re.IGNORECASE),
    re.compile(r"\bLOREM\s+IPSUM\b", re.IGNORECASE),
    re.compile(r"\{\{[^{}]+\}\}"),
]


def check_manuscript(report: dict[str, Any], manuscript_text: str) -> list[str]:
    errors: list[str] = []
    master = report.get("canonical_master") or {}
    expected_hash = master.get("sha256")
    actual_hash = hashlib.sha256(manuscript_text.encode("utf-8")).hexdigest()
    if expected_hash and expected_hash != actual_hash:
        errors.append("MASTER_HASH_MISMATCH")

    lifecycle = report.get("lifecycle") or {}
    if lifecycle.get("master_locked") or lifecycle.get("release_ready") or report.get("current_stage") in {"MASTER_LOCKED", "FORMAT_READY", "RELEASE_READY", "PUBLISHED"}:
        if any(pattern.search(manuscript_text) for pattern in _PLACEHOLDER_PATTERNS):
            errors.append("UNRESOLVED_PLACEHOLDER")

    for fact in report.get("protected_facts") or []:
        if fact.get("required") is True:
            value = str(fact.get("value") or "")
            if value and value not in manuscript_text:
                errors.append("PROTECTED_FACT_MISSING")

    for claim in report.get("claim_uses") or []:
        if claim.get("citation_state") == "REQUIRED":
            marker = claim.get("citation_marker")
            if not marker or marker not in manuscript_text:
                errors.append("CITATION_MARKER_MISSING")

    rewrite_types = {"AI_HUMANIZE", "STRONG_REWRITE", "DEEP_REWRITE", "SUBSTANTIAL_REWRITE"}
    edited = any(item.get("type") in rewrite_types and item.get("status") == "COMPLETE" for item in report.get("edit_history") or [])
    fidelity = report.get("fidelity") or {}
    if edited and not (fidelity.get("required") is True and fidelity.get("passed") is True):
        errors.append("POST_EDIT_FIDELITY_REQUIRED")

    return list(dict.fromkeys(errors))


def check_derived(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    master_hash = (report.get("canonical_master") or {}).get("sha256")
    for item in report.get("derived_artifacts") or []:
        fmt = str(item.get("format") or "").upper()
        if item.get("generation_status") != "COMPLETE":
            errors.append("DERIVED_GENERATION_INCOMPLETE")
        if master_hash and item.get("master_sha256") != master_hash:
            errors.append("DERIVED_MASTER_HASH_MISMATCH")
        if item.get("direct_material_edit") is True:
            errors.append("DERIVED_MATERIAL_EDIT_FORBIDDEN")
        if fmt in {"DOCX", "PDF"}:
            if item.get("qa_required") is not True:
                errors.append("VISUAL_QA_REQUIRED")
            elif item.get("qa_status") != "PASS":
                errors.append("VISUAL_QA_MISSING")
        elif item.get("qa_required") is True and item.get("qa_status") != "PASS":
            errors.append("DERIVED_QA_MISSING")
        if item.get("parity_status") != "PASS":
            errors.append("DERIVED_PARITY_FAILED")
    return list(dict.fromkeys(errors))


LANE_TITLES = [
    ("blockers", "BLOCKER"),
    ("verify_now", "VERIFY NOW"),
    ("decision_now", "DECISION NOW"),
    ("now", "NOW"),
    ("next_milestone", "NEXT MILESTONE"),
    ("delegate", "DELEGATE"),
    ("waiting", "WAITING"),
    ("stop", "STOP"),
]


def _render_action(item: Any) -> str:
    if isinstance(item, str):
        return item
    if not isinstance(item, dict):
        return str(item)
    text = item.get("action") or item.get("question") or item.get("label") or item.get("id") or "Action"
    done = item.get("done_when")
    if done:
        return f"{text} — Done: {done}"
    return str(text)


def render_manifest(report: dict[str, Any]) -> str:
    publication = report.get("publication") or {}
    master = report.get("canonical_master") or {}
    artifacts = report.get("derived_artifacts") or []
    formats = ", ".join(str(a.get("format")) for a in artifacts if a.get("format")) or "none"
    lines = [
        f"Stan: {report.get('status', 'PROVISIONAL')} — {report.get('status_reason', 'Publication state requires review.')}",
        "",
        "PUBLICATION SUMMARY",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Publication | {publication.get('title', 'UNKNOWN')} |",
        f"| Type | {publication.get('type', 'UNKNOWN')} |",
        f"| Mode | {report.get('mode', 'UNKNOWN')} |",
        f"| Master | {master.get('path', 'UNKNOWN')} @ {master.get('version', 'UNKNOWN')} |",
        f"| Derived | {formats} |",
        "",
        "CURRENT STAGE",
        "",
        f"- {report.get('current_stage', infer_stage(report))}",
    ]
    actions = report.get("actions") or {}
    for key, title in LANE_TITLES:
        items = actions.get(key) or []
        if not items:
            continue
        lines.extend(["", title, ""])
        for item in items:
            lines.append(f"- {_render_action(item)}")
    return "\n".join(lines).rstrip() + "\n"


def check_brief(report: dict[str, Any], brief_text: str) -> list[str]:
    expected = render_manifest(report).rstrip("\n")
    actual = brief_text.rstrip("\n")
    errors: list[str] = []
    if actual != expected:
        errors.append("BRIEF_MISMATCH")
    return errors


def _load_json(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _emit_errors(errors: list[str]) -> int:
    if errors:
        for error in errors:
            print(error)
        return 1
    print("OK")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Longform Publisher deterministic kernel")
    sub = parser.add_subparsers(dest="command", required=True)

    p_validate = sub.add_parser("validate")
    p_validate.add_argument("--report-json", required=True)

    p_manuscript = sub.add_parser("check-manuscript")
    p_manuscript.add_argument("--report-json", required=True)
    p_manuscript.add_argument("--manuscript-file", required=True)

    p_render = sub.add_parser("render-manifest")
    p_render.add_argument("--report-json", required=True)
    p_render.add_argument("--output", required=True)

    p_derived = sub.add_parser("check-derived")
    p_derived.add_argument("--report-json", required=True)

    p_brief = sub.add_parser("check-brief")
    p_brief.add_argument("--report-json", required=True)
    p_brief.add_argument("--brief-file", required=True)

    args = parser.parse_args(argv)
    report = _load_json(args.report_json)

    if args.command == "validate":
        return _emit_errors(validate_report(report))
    if args.command == "check-manuscript":
        text = Path(args.manuscript_file).read_text(encoding="utf-8")
        return _emit_errors(check_manuscript(report, text))
    if args.command == "render-manifest":
        Path(args.output).write_text(render_manifest(report), encoding="utf-8")
        print("OK")
        return 0
    if args.command == "check-derived":
        return _emit_errors(check_derived(report))
    if args.command == "check-brief":
        text = Path(args.brief_file).read_text(encoding="utf-8")
        return _emit_errors(check_brief(report, text))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
