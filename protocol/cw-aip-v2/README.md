# CW-AIP v2

Unified interchange for CometWeb Agent Skills.

## Design

1. **Small core** — identity, producer, time, sensitivity, dependencies, opaque payload + hash.
2. **Typed payloads** — each envelope kind has its own JSON Schema under this directory.
3. **Status locality preserved** — research ≠ decision ≠ release (enforced by payload type + consumer gates).
4. **v1 compatibility** — `protocol/cw-aip-v1/` remains valid for existing domain skills; new work prefers v2 wrappers.

## Core fields

See `core.schema.json`:

`id`, `type`, `producer`, `producer_version`, `protocol_version` (`2.0`), `subject`,
`generated_at`, `as_of`, `sensitivity`, `dependencies`, `payload`, `payload_hash`.

All twelve fields are required and no other top-level field is allowed;
producer-specific data goes inside `payload`. Further rules the schema alone does
not express, enforced by `tooling/validate_envelope.py`:

- `generated_at` MUST be an RFC 3339 date-time with a timezone (`Z` or `±hh:mm`).
  ISO 8601 forms outside RFC 3339 (basic format, week dates, missing offset) are
  rejected. `as_of` stays a free non-empty string so it can carry a pinned ref.
- `type` MUST name a kind with a payload schema (table below). `SpecialistHandoff`,
  `ArtifactEnvelope` and `SnapshotMetadata` are reserved in the core enum for
  continuity with v1, but have no enforced v2 payload schema yet, so the validator
  rejects them; keep emitting those kinds as v1 envelopes. Draft payload schemas
  for them are published for review (see [Draft payload schemas](#draft-payload-schemas)).
- `payload_hash` is the canonical hash defined below, or the draft marker
  `pending`. A finalized handoff (`--final`) MUST NOT carry `pending`.

## Payload hash

`payload_hash` is `sha256:` followed by the lowercase hex SHA-256 of the
canonical serialization of `payload`:

1. Serialize `payload` as JSON with object keys sorted by Unicode code point,
   no insignificant whitespace (`,` and `:` separators), and non-ASCII characters
   written as UTF-8 rather than `\u` escapes. Only the quotation mark, the backslash and control
   characters below U+0020 are escaped: `\b \f \n \r \t` in short form, the rest
   as lowercase `\u00xx`.
2. `NaN` and `Infinity` are not JSON and make the payload unhashable.
3. Hash the UTF-8 bytes.

This is exactly `json.dumps(payload, ensure_ascii=False, sort_keys=True,
separators=(",", ":"), allow_nan=False)` in Python. It is not RFC 8785 (JCS):
numbers keep the producer's JSON number formatting, so producers in other
languages SHOULD avoid non-integer floats in payloads or reproduce Python's float
formatting. Validators accept the hash with or without the `sha256:` prefix and
compare hex case-insensitively. `python3 tooling/validate_envelope.py FILE
--print-hash` prints the expected value.

## Payload schemas

| Type | Schema |
| --- | --- |
| ContextEnvelope | `context.schema.json` (`cometweb.context/v2`) |
| EvidenceEnvelope | `evidence.schema.json` (`cometweb.evidence/v2`) |
| DecisionEnvelope | `decision.schema.json` (`cometweb.decision/v2`) |
| FindingEnvelope | `finding.schema.json` (`cometweb.finding/v2`) |
| RoadmapEnvelope | `roadmap.schema.json` (`cometweb.roadmap/v2`) |
| ReleaseEnvelope | `release.schema.json` (`cometweb.release/v2`) |

Validators:

- `tooling/validate_envelope.py` — full envelope: core, typed payload, payload
  hash, `--final`. Runs every check below.
- `skills/cometweb-context/scripts/validate_context_envelope.py`
- `tooling/validate_evidence_envelope.py`
- `tooling/validate_decision_envelope.py`

`jsonschema` is optional. Without it each validator falls back to standard-library
checks that MUST reject the same documents; Finding, Roadmap and Release payloads
are checked against their schema files by a small built-in interpreter that
refuses any schema keyword it cannot enforce.

Semantic rules beyond the schemas: an `EvidenceEnvelope` may not mark an
`INFERENCE` claim `VERIFIED`, every edge must reference a known claim and source,
claim IDs are unique, and `READY` excludes blocking gaps and unresolved
critical/material contradictions. A `DecisionEnvelope` with verdict `GO` may not
have blockers, a `BLOCK` or `COUNSEL_REQUIRED` gate, or `human_approval:
required`. A `ReleaseEnvelope` with verdict `GO` or `GO_WITH_CONTROLS` may not have
blockers: controls bound residual risk, they do not clear a blocker.

Conformance cases, valid and invalid, live in `fixtures/cwaip-v2/conformance/` and
run through `tooling/tests/test_cwaip_conformance.py` with and without
`jsonschema`.

Finalized `EvidenceEnvelope` and `DecisionEnvelope` handoffs can be rendered as
unreviewed WhyKit drafts with `tooling/whykit_draft.py`. The adapter never
allocates ledger IDs or approves a record; see
[`docs/WHYKIT-INTEGRATION.md`](https://github.com/CometWeb-io/agent-skills/blob/main/docs/WHYKIT-INTEGRATION.md).

## Draft payload schemas

The reserved kinds have draft payload schemas under `draft/`. They are proposals
for review, not part of the protocol: no validator applies them, the multiagent
gate does not consult them, and a v2 envelope of a reserved kind is still
rejected. Their `schema` constants end in `/v2-draft` so a draft payload can never
be mistaken for a promoted one. Fields may change before promotion.

| Reserved kind | Draft schema | Required payload fields |
| --- | --- | --- |
| SpecialistHandoff | `draft/specialist-handoff.schema.json` (`cometweb.specialist/v2-draft`) | `skill`, `scope`, `stop_rule`, `return_contract` |
| ArtifactEnvelope | `draft/artifact.schema.json` (`cometweb.artifact/v2-draft`) | `artifact_kind`, `artifact_hash`, `locator` |
| SnapshotMetadata | `draft/snapshot.schema.json` (`cometweb.snapshot/v2-draft`) | `snapshot_id`, `baseline_id`, `delta_of`, `snapshot_hash` |

Each draft uses only the schema keywords the standard-library fallback enforces,
so promotion needs no new fallback code. Example payloads live in
`fixtures/cwaip-v2/draft/`. Promoting a draft means dropping the `-draft` suffix,
moving the schema next to the others, adding it to the table above and to
`tooling/validate_envelope.py`, and adding conformance cases.

## Enum conventions

v2 payloads use **lowercase** enums (`primary`, `fresh`, `public`).
v1 core used `PRIMARY` / `CURRENT`. Adapters MUST normalize at the boundary; do not mix
conventions inside one payload document.

## Migration rule

- New envelopes from `cometweb-context` → Context payload validated by v2 schema.
- Existing Evidence/Decision producers may keep emitting v1 until their package bumps.
- Orchestrators SHOULD accept both and record `protocol_version` per envelope. The
  multiagent gate (`skills/skill-orchestrator-multiagent/scripts/validate_envelope.py`)
  dispatches on `protocol_version`, checks the bundled v1 or v2 core schema, and for
  v2 recomputes `payload_hash` and rejects a `GO` (or release `GO_WITH_CONTROLS`)
  verdict that lists blockers. A step planned as v1 `DecisionHandoff` accepts a v2
  `DecisionEnvelope` (Council) or `ReleaseEnvelope` (Release Readiness).

## Spec revisions

The wire value stays `protocol_version: "2.0"`; the third component numbers
revisions of this document and its schemas. A revision MAY reject documents that
were incoherent under the earlier text; it MUST NOT change the meaning of a field
or reject the output of a shipped producer.

### 2.0.1 — 2026-10-02

- `ReleaseEnvelope`: `GO` and `GO_WITH_CONTROLS` reject a non-empty `blockers`
  array, in `tooling/validate_envelope.py` (with and without `jsonschema`) and in
  the multiagent gate. New conformance cases `release-go-with-blockers` and
  `release-go-with-controls-with-blockers` (invalid) and
  `release-no-go-with-blockers` (valid).
- Draft, unenforced payload schemas for `SpecialistHandoff`, `ArtifactEnvelope`
  and `SnapshotMetadata` under `draft/`.

### 2.0.0

- Core envelope, payload hash, and the Context, Evidence, Decision, Finding,
  Roadmap and Release payload schemas.
