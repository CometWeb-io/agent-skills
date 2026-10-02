# CometWeb Agent Interchange Protocol (CW-AIP) v1

Minimal shared envelope for handoffs between CometWeb Agent Skills. Skills remain
standalone; consumers MAY apply stricter gates than the producer recorded.

The key words MUST, MUST NOT, SHOULD and MAY are used as described in RFC 2119.
New typed envelopes use CW-AIP v2 (`protocol/cw-aip-v2/README.md`); v1 stays valid for
existing producers.

The canonical copy of this document and its schemas is `protocol/cw-aip-v1/`.
`protocol/cw-interchange-v1.md` and `protocol/schemas/` are byte-identical mirrors
kept for existing links; a test fails if they drift.

## Design rules

1. **Envelope, not monolith** — only metadata + typed payload reference; skill-specific bodies stay in each skill's output contract.
2. **Producer truth** — `producer`, `protocol_version`, and `as_of` are set by the emitting skill and MUST NOT be rewritten downstream without a new envelope.
3. **Status is local** — `verified_for_research` ≠ `verified_for_decision` ≠ `verified_for_release`.
4. **No shadow CRM/PM** — interchange carries evidence and handoff intent, not full domain objects.

## Core fields (all envelopes)

| Field | Required | Description |
| --- | --- | --- |
| `id` | yes | Non-empty string. SHOULD be stable: a UUID or `{producer}:{kind}:{slug}` |
| `type` | yes | Envelope kind; exactly one of the kinds listed below |
| `producer` | yes | Non-empty skill name, e.g. `evidence-researcher` |
| `protocol_version` | yes | The JSON string `"1.0"` (not the number `1.0`) |
| `subject` | yes | Non-empty string: what the payload is about (repo, RC, competitor, account, decision question) |
| `as_of` | yes | Non-empty string. SHOULD be an RFC 3339 timestamp; MAY be a pinned ref (commit, snapshot ID) the producer used |
| `source` | no | Primary system-of-record class (`github`, `notion`, `gsc`, `live-app`, …); free text |
| `locator` | no | URI, commit, path, or internal pointer |
| `claim` | no | Human-readable summary when the envelope wraps a single claim |
| `authority` | no | Closed set: `PRIMARY`, `DERIVATIVE`, `HEURISTIC`, `USER_ASSERTED`, `UNKNOWN` |
| `freshness` | no | Closed set: `CURRENT`, `STALE`, `UNKNOWN`, `NOT_YET_EFFECTIVE`, `SUPERSEDED` |
| `confidence` | no | Producer-local: a number in `[0, 1]` or a non-empty band label such as `high`. Never averaged across gates |
| `status` | no | Producer-local lifecycle state; free text |
| `dependencies` | no | Array of upstream envelope or claim IDs (strings) |
| `payload` | per kind | JSON object with the kind-specific body. Optional in the core schema; required by the kind schemas. See [Validation](#validation) |

Enum values are uppercase and case-sensitive. v2 uses lowercase enums; adapters
MUST normalize at the boundary rather than mix conventions in one document.

JSON Schema: [`schemas/envelope.core.schema.json`](schemas/envelope.core.schema.json).

## Envelope kinds

### `ArtifactEnvelope`

Immutable snapshot of a structured artifact (roadmap baseline, CI snapshot, audit report JSON, Evidence Pack hash).

### `EvidenceEnvelope`

Material claims + accepted evidence edges + gaps. Emitted by **Evidence Researcher**; consumed by Council, Product Operator, Release Readiness, SEO, etc.

### `FindingEnvelope`

Single defect, usability risk, recommendation, or needs-repro item from **Web App Auditor** or specialist audits.

### `DecisionHandoff`

Council or Release Readiness output bound for action tracking — verdict, gates, blockers, controls. Not authorization to deploy.

### `SpecialistHandoff`

Delegation packet from Product Operator / Customer Ops / Competitive Intelligence to a specialist skill with scope, stop rule, and return contract.

### `SnapshotMetadata`

Pointer to an immutable snapshot plus diff lineage (`baseline_id`, `delta_of`, `hash`).

Two kinds have a kind schema that adds payload requirements on top of the core:

| Kind | Schema | Required payload fields |
| --- | --- | --- |
| `EvidenceEnvelope` | [`schemas/evidence-envelope.schema.json`](schemas/evidence-envelope.schema.json) | `research_contract`, `material_claims[]` (`claim_id`, `text`, `epistemic_kind` = `FACT`/`INFERENCE`, `status`), `evidence_pack_hash` |
| `DecisionHandoff` | [`schemas/decision-handoff.schema.json`](schemas/decision-handoff.schema.json) | `verdict`; `blockers` MUST be empty when `verdict` is `GO` or `GO_WITH_CONTROLS` |

The other kinds are constrained by the core schema only; their payload shape is
defined by the producing skill's output contract.

## Validation

- The core schema sets `additionalProperties: false`. A top-level field not listed
  above makes the envelope invalid; producer-specific data MUST go inside `payload`.
- The core schema leaves `payload` optional. Each kind schema requires it, so an
  `EvidenceEnvelope` or `DecisionHandoff` without a `payload` is invalid.
- An authorizing verdict cannot carry open blockers: a `DecisionHandoff` whose
  `verdict` is `GO` or `GO_WITH_CONTROLS` MUST have an empty or absent `blockers`
  array. Controls bound residual risk; they do not clear a blocker. Other verdict
  strings (`NO_GO`, `DEFER`, Council verdicts other than `GO`) MAY list blockers.
- The orchestrator's between-step gate
  (`skills/skill-orchestrator-multiagent/scripts/validate_envelope.py`) validates
  each envelope against its kind schema when the kind has one, and against the core
  schema otherwise. It also requires an object `payload` for every v1 kind. It needs
  `jsonschema` and fails closed without it, or when a bundled schema is missing.
- Conformance cases, valid and invalid, live in `fixtures/cwaip-v1/conformance/`
  and are run by `tooling/tests/test_cwaip_conformance.py`.

## Canonical flows

```text
question → Evidence Researcher → EvidenceEnvelope
                                      ↓
              Product Operator / Council / Release Readiness / SEO / …

Web App Auditor → FindingEnvelope[] → Release Readiness → DecisionHandoff

Competitive Intelligence → SnapshotMetadata + events → Council (DecisionHandoff)

Repo to Roadmap → ArtifactEnvelope (roadmap baseline) → Product Operator

Product Operator → SpecialistHandoff → specialist skills
```

## Versioning

- **Protocol** (`protocol_version`): bumped only when core fields or envelope kinds change.
- **Spec revision**: a third component (`1.0.1`) records tightened kind-schema rules
  and clarifications. It never appears on the wire; envelopes keep
  `protocol_version: "1.0"`. A revision MAY tighten a kind schema to reject
  documents that were incoherent under the earlier text; it MUST NOT change the
  meaning of a field or reject the output of a shipped producer.
- **Skill** (`VERSION` file per skill): independent release cadence; tag `skill-name-vX.Y.Z`.

## Spec revisions

### 1.0.1 — 2026-10-02

- The `EvidenceEnvelope` and `DecisionHandoff` kind schemas require `payload`.
  Earlier they constrained it only when present, so an envelope with no `payload`
  passed the kind check while carrying no evidence or verdict, although the text
  already required producers to emit one. Every shipped producer and conformance
  fixture sends it.
- `DecisionHandoff`: `GO` and `GO_WITH_CONTROLS` reject a non-empty `blockers` array.
- The orchestrator gate applies the kind schemas instead of the core schema only.
- New conformance cases: `evidence-missing-payload`, `decision-handoff-missing-payload`,
  `decision-handoff-go-with-blockers`, `decision-handoff-go-with-controls-with-blockers`
  (invalid) and `decision-handoff-no-go-with-blockers` (valid).

### 1.0.0

- Initial core envelope, six kinds, and the `EvidenceEnvelope` and
  `DecisionHandoff` kind schemas.

## Migration

Skills MAY embed CW-AIP envelopes inside existing output contracts. Full migration notes:
`skills/evidence-researcher/references/migration-v1-v2.md` (evidence graph); other skills add `integrations.md` sections referencing this file.
