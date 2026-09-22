#!/usr/bin/env python3
"""Render a validated CW-AIP v2 evidence or decision envelope as a WhyKit draft."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import importlib.util
import json
import pathlib
import re
import sys
from typing import Any

TOOLING = pathlib.Path(__file__).resolve().parent


def load_envelope_validator():
    path = TOOLING / "validate_envelope.py"
    spec = importlib.util.spec_from_file_location("_cometweb_cwaip_v2_validator", path)
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot load envelope validator: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.validate_envelope


validate_envelope = load_envelope_validator()

SUPPORTED_TYPES = {"EvidenceEnvelope", "DecisionEnvelope"}
DECISION_ID_RE = re.compile(r"D-[0-9]{3,}")
SOURCE_ID_RE = re.compile(r"E-[0-9]{3,}")


def fail(message: str) -> None:
    raise ValueError(message)


def yaml_string(value: object) -> str:
    """Return a JSON string, which is also a safe YAML scalar."""
    return json.dumps(str(value), ensure_ascii=False).replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def yaml_list(values: list[str]) -> str:
    return json.dumps(values, ensure_ascii=False).replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def markdown_inline(value: object) -> str:
    """Render producer data on one inert Markdown line."""
    text = html.escape(re.sub(r"\s+", " ", str(value)).strip(), quote=False)
    return re.sub(r"([\\`*_[\]{}()#+!|>])", r"\\\1", text)


def markdown_quote(value: object) -> list[str]:
    """Render producer data as an escaped blockquote, including every blank line."""
    lines = str(value).splitlines() or [""]
    return [f"> {markdown_inline(line)}" if line else ">" for line in lines]


def strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            fail(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def reject_json_constant(value: str) -> None:
    fail(f"invalid JSON constant: {value}")


def load_json(path: pathlib.Path) -> dict[str, Any]:
    data = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=strict_object,
        parse_constant=reject_json_constant,
    )
    if not isinstance(data, dict):
        fail("envelope must be a JSON object")
    return data


def iso_date(value: object, label: str) -> str:
    text = str(value)
    if len(text) < 10:
        fail(f"{label} must contain an ISO date")
    candidate = text[:10]
    try:
        dt.date.fromisoformat(candidate)
    except ValueError:
        fail(f"{label} must contain a valid ISO date")
    return candidate


def validate_ledger_fields(
    *,
    envelope_type: str,
    owner: str,
    decision_id: str | None,
    review_by: str | None,
    source_ids: list[str],
) -> None:
    if not owner.strip():
        fail("owner must be non-empty")
    invalid_sources = [source_id for source_id in source_ids if not SOURCE_ID_RE.fullmatch(source_id)]
    if invalid_sources:
        fail(f"invalid source_id: {invalid_sources[0]}")
    if len(source_ids) != len(set(source_ids)):
        fail("source_ids must be unique")
    if envelope_type == "DecisionEnvelope":
        if not decision_id or not DECISION_ID_RE.fullmatch(decision_id):
            fail("decision_id must match D-NNN")
        if not review_by:
            fail("review_by is required for DecisionEnvelope")
        iso_date(review_by, "review_by")


def front_matter(
    envelope: dict[str, Any],
    *,
    owner: str,
    source_ids: list[str],
    title: str,
    note_type: str,
    decision_id: str | None = None,
    review_by: str | None = None,
    payload_ref: str | None = None,
) -> str:
    created = iso_date(envelope["as_of"], "as_of")
    payload = envelope["payload"]
    lines = [
        "---",
        f"title: {yaml_string(markdown_inline(title))}",
        f"aliases: {yaml_list([decision_id] if decision_id else [])}",
        f"type: {note_type}",
    ]
    if decision_id:
        lines.append(f"decision_id: {decision_id}")
    lines.extend(
        [
            "status: draft",
            f"owner: {yaml_string(owner)}",
            f"created: {created}",
            f"last_updated: {created}",
        ]
    )
    if review_by:
        lines.append(f"review_by: {iso_date(review_by, 'review_by')}")
    upstream = list(envelope["dependencies"])
    if envelope["type"] == "DecisionEnvelope":
        upstream.extend(item for item in payload["evidence_deps"] if item not in upstream)
    provenance = [
            "source_of_truth: false",
            f"sensitivity: {envelope['sensitivity']}",
            f"source_ids: {yaml_list(source_ids)}",
            "tags: []",
            "provenance:",
            f"  producer: {yaml_string(f'{envelope['producer']}/{envelope['producer_version']}')}",
            f"  producer_run: {yaml_string(envelope['id'])}",
            f"  snapshot_hash: {yaml_string(payload.get('snapshot_hash') or payload.get('evidence_pack_hash'))}",
            f"  recorded_at: {yaml_string(envelope['generated_at'])}",
            f"  upstream: {yaml_list(upstream)}",
            f"  payload_hash: {yaml_string(envelope['payload_hash'])}",
    ]
    if payload_ref:
        provenance.append(f"  payload_ref: {yaml_string(payload_ref)}")
    if envelope["type"] == "DecisionEnvelope":
        provenance.append(f"  profile: {yaml_string(payload['profile'])}")
        if "human_approval" in payload:
            provenance.append(f"  human_approval: {yaml_string(payload['human_approval'])}")
    provenance.extend(["  human_reviewed: false", "---"])
    lines.extend(provenance)
    return "\n".join(lines)


def describe_source(source: dict[str, Any]) -> str:
    source_id = str(source.get("source_id", "unnamed"))
    title = source.get("title") or source.get("name") or source.get("source")
    location = source.get("location") or source.get("url") or source.get("path")
    parts = [markdown_inline(source_id)]
    if title:
        parts.append(markdown_inline(title))
    if location:
        parts.append(markdown_inline(location))
    return " — ".join(parts)


def describe_gap(gap: dict[str, Any]) -> str:
    identity = gap.get("gap_id") or gap.get("id")
    description = gap.get("description") or gap.get("text") or gap.get("reason") or "Unspecified gap"
    prefix = f"{markdown_inline(identity)}: " if identity else ""
    blocking = "blocking" if gap.get("blocking") else "non-blocking"
    return f"{prefix}{markdown_inline(description)} ({blocking})"


def evidence_body(envelope: dict[str, Any]) -> str:
    payload = envelope["payload"]
    title = envelope["subject"]
    claims: list[str] = []
    for claim in payload["material_claims"]:
        claims.append(
            f"- Claim {markdown_inline(claim['claim_id'])} — {markdown_inline(claim['status'])} / "
            f"{markdown_inline(claim['epistemic_kind'])} / {markdown_inline(claim['materiality'])}:"
        )
        claims.extend(markdown_quote(claim["text"]))
    claims = claims or ["- None recorded."]
    sources = [f"- {describe_source(source)}" for source in payload["sources"]] or ["- None recorded."]
    edges = [
        (
            f"- {markdown_inline(edge['claim_id'])} ← {markdown_inline(edge['source_id'])} "
            f"({markdown_inline(edge['direction'])}, {markdown_inline(edge['admission'])})"
        )
        for edge in payload["evidence_edges"]
    ] or ["- None recorded."]
    gaps = [f"- {describe_gap(gap)}" for gap in payload["gaps"]] or ["- None recorded."]
    contradictions: list[str] = []
    for item in payload["contradictions"]:
        contradictions.append("- Producer record:")
        contradictions.extend(markdown_quote(json.dumps(item, ensure_ascii=False, sort_keys=True, allow_nan=False)))
    contradictions = contradictions or ["- None recorded."]
    return "\n".join(
        [
            f"# {markdown_inline(title)}",
            "",
            "## Research question",
            "",
            *markdown_quote(payload["research_contract"]),
            "",
            "## Readiness",
            "",
            f"{markdown_inline(payload['readiness'])} as of {markdown_inline(payload['as_of'])}.",
            "",
            "## Material claims",
            "",
            *claims,
            "",
            "## Sources",
            "",
            *sources,
            "",
            "## Evidence links",
            "",
            *edges,
            "",
            "## Gaps",
            "",
            *gaps,
            "",
            "## Contradictions",
            "",
            *contradictions,
            "",
            "## Limitations",
            "",
            "This draft preserves the producer's claims and provenance. A human must review it and map",
            "source material to populated WhyKit evidence-register entries before approval.",
        ]
    )


def decision_body(envelope: dict[str, Any], decision_id: str) -> str:
    payload = envelope["payload"]
    gates = [
        f"- Gate {markdown_inline(gate['gate_id'])}: {markdown_inline(gate['status'])}" for gate in payload["gates"]
    ] or ["- None recorded."]

    def producer_list(values: list[str]) -> list[str]:
        rows: list[str] = []
        for value in values:
            rows.append("- Producer value:")
            rows.extend(markdown_quote(value))
        return rows or ["- None recorded."]

    controls = producer_list(payload["controls"])
    blockers = producer_list(payload["blockers"])
    dependencies = [f"- {markdown_inline(item)}" for item in payload["evidence_deps"]] or ["- None recorded."]
    return "\n".join(
        [
            f"# {decision_id} — {markdown_inline(payload['decision_question'])}",
            "",
            "## Decision ID",
            "",
            decision_id,
            "",
            "## Status",
            "",
            "Proposed. This generated draft is not an approval.",
            "",
            "## Context",
            "",
            *markdown_quote(payload["decision_question"]),
            "",
            "## Decision",
            "",
            f"Verdict: {markdown_inline(payload['verdict'])}.",
            "",
            *markdown_quote(payload["option"]),
            "",
            "## Rationale",
            "",
            "The producer did not supply a separate rationale; review the gates, controls and evidence below.",
            "",
            "## Evidence",
            "",
            *dependencies,
            "",
            "## Alternatives considered",
            "",
            "No alternatives were supplied by the producer.",
            "",
            "## Consequences",
            "",
            "### Gates",
            "",
            *gates,
            "",
            "### Controls",
            "",
            *controls,
            "",
            "### Blockers and trade-offs",
            "",
            *blockers,
        ]
    )


def render_draft(
    envelope: dict[str, Any],
    *,
    owner: str,
    decision_id: str | None = None,
    review_by: str | None = None,
    source_ids: list[str] | None = None,
    payload_ref: str | None = None,
) -> str:
    envelope_type = envelope.get("type")
    if envelope_type not in SUPPORTED_TYPES:
        fail("WhyKit draft conversion supports only EvidenceEnvelope and DecisionEnvelope")
    validate_envelope(envelope, final=True)
    ledger_source_ids = list(source_ids or [])
    validate_ledger_fields(
        envelope_type=envelope_type,
        owner=owner,
        decision_id=decision_id,
        review_by=review_by,
        source_ids=ledger_source_ids,
    )
    if envelope_type == "EvidenceEnvelope":
        header = front_matter(
            envelope,
            owner=owner,
            source_ids=ledger_source_ids,
            title=envelope["subject"],
            note_type="research",
            payload_ref=payload_ref,
        )
        body = evidence_body(envelope)
    else:
        assert decision_id is not None
        header = front_matter(
            envelope,
            owner=owner,
            source_ids=ledger_source_ids,
            title=f"{decision_id} — {envelope['payload']['decision_question']}",
            note_type="decision",
            decision_id=decision_id,
            review_by=review_by,
            payload_ref=payload_ref,
        )
        body = decision_body(envelope, decision_id)
    return f"{header}\n\n{body}\n"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render a finalized CW-AIP v2 EvidenceEnvelope or DecisionEnvelope as an unreviewed WhyKit draft."
    )
    parser.add_argument("envelope", help="Path to the CW-AIP v2 JSON envelope")
    parser.add_argument("--owner", required=True, help="Human owner recorded in WhyKit front matter")
    parser.add_argument("--decision-id", help="Explicit D-NNN identifier; required for DecisionEnvelope")
    parser.add_argument("--review-by", help="ISO review date; required for DecisionEnvelope")
    parser.add_argument("--source-id", action="append", default=[], help="Mapped WhyKit E-NNN ID; repeatable")
    parser.add_argument("--payload-ref", help="Stable reference to the producer's retained machine-readable payload")
    parser.add_argument("--output", help="Write the draft to this file instead of stdout")
    args = parser.parse_args()

    envelope = load_json(pathlib.Path(args.envelope))
    draft = render_draft(
        envelope,
        owner=args.owner,
        decision_id=args.decision_id,
        review_by=args.review_by,
        source_ids=args.source_id,
        payload_ref=args.payload_ref,
    )
    if args.output:
        with pathlib.Path(args.output).open("x", encoding="utf-8") as output_file:
            output_file.write(draft)
    else:
        sys.stdout.write(draft)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
