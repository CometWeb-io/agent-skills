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

- `skills/cometweb-context/scripts/validate_context_envelope.py`
- `tooling/validate_evidence_envelope.py`
- `tooling/validate_decision_envelope.py`

## Enum conventions

v2 payloads use **lowercase** enums (`primary`, `fresh`, `public`).
v1 core used `PRIMARY` / `CURRENT`. Adapters MUST normalize at the boundary; do not mix
conventions inside one payload document.

## Migration rule

- New envelopes from `cometweb-context` → Context payload validated by v2 schema.
- Existing Evidence/Decision producers may keep emitting v1 until their package bumps.
- Orchestrators SHOULD accept both and record `protocol_version` per envelope.
