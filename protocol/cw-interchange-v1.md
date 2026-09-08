# CometWeb Agent Interchange Protocol (CW-AIP) v1

Minimal shared envelope for handoffs between CometWeb Agent Skills. Skills remain
standalone; consumers MAY apply stricter gates than the producer recorded.

## Design rules

1. **Envelope, not monolith** — only metadata + typed payload reference; skill-specific bodies stay in each skill's output contract.
2. **Producer truth** — `producer`, `protocol_version`, and `as_of` are set by the emitting skill and MUST NOT be rewritten downstream without a new envelope.
3. **Status is local** — `verified_for_research` ≠ `verified_for_decision` ≠ `verified_for_release`.
4. **No shadow CRM/PM** — interchange carries evidence and handoff intent, not full domain objects.

## Core fields (all envelopes)

| Field | Required | Description |
| --- | --- | --- |
| `id` | yes | Stable envelope ID (UUID or `{producer}:{kind}:{slug}`) |
| `type` | yes | Envelope kind (see below) |
| `producer` | yes | Skill name, e.g. `evidence-researcher` |
| `protocol_version` | yes | Always `1.0` for this spec |
| `subject` | yes | What the payload is about (repo, RC, competitor, account, decision question) |
| `as_of` | yes | ISO-8601 timestamp or pinned ref the producer used |
| `source` | no | Primary system-of-record class (`github`, `notion`, `gsc`, `live-app`, …) |
| `locator` | no | URI, commit, path, or internal pointer |
| `claim` | no | Human-readable summary when the envelope wraps a single claim |
| `authority` | no | `PRIMARY`, `DERIVATIVE`, `HEURISTIC`, `USER_ASSERTED`, … |
| `freshness` | no | `CURRENT`, `STALE`, `UNKNOWN`, `NOT_YET_EFFECTIVE`, `SUPERSEDED` |
| `confidence` | no | Producer-local score or band; never averaged across gates |
| `status` | no | Producer-local lifecycle state |
| `dependencies` | no | List of upstream envelope or claim IDs |

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

Kind-specific required fields: see schemas in `protocol/schemas/`.

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
- **Skill** (`VERSION` file per skill): independent release cadence; tag `skill-name-vX.Y.Z`.

## Migration

Skills MAY embed CW-AIP envelopes inside existing output contracts. Full migration notes:
`skills/evidence-researcher/references/migration-v1-v2.md` (evidence graph); other skills add `integrations.md` sections referencing this file.
