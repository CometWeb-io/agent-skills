# Public target

This repository is the public canonical source for CometWeb Agent Skills.

## Stable contract

- One portable `skills/<id>/SKILL.md` package per skill.
- `registry/skills.json` is the source of routing and lifecycle metadata.
- CW-AIP v1 remains compatible; new typed envelopes use CW-AIP v2.
- Host adapters and generated tables are derived from the registry.
- CI checks package identity, references, compatibility, routing, behavior
  fixtures, and public-safety rules.

## Explicit limits

- Tests and eval fixtures validate deterministic contracts; they are not a
  substitute for model, host, connector, or end-to-end acceptance tests.
- A skill can prepare evidence, a decision, a draft, or a handoff. It does not
  grant authorization to send messages, change a CRM, publish content, or
  mutate a production system.
- Business-specific workflows use CW-AIP payloads. A second business-only
  protocol is not planned.

## Next improvements

1. Add a small number of provider-backed, human-reviewed workflow benchmarks.
2. Keep the public README organized around canonical workflows and outcomes.
3. Add framework dependencies only when a measured runtime need requires them.
