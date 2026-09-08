# Research Contract

## Purpose

Normalize the research problem before retrieval so scope drift, temporal ambiguity, and downstream misuse are visible.

## Required fields

```json
{
  "question": "Atomic research question or tightly scoped umbrella question",
  "objective": "Why this evidence is needed",
  "scope": {
    "jurisdiction": null,
    "geography": null,
    "population": null,
    "product": null,
    "version": null,
    "time_window": null
  },
  "as_of": "timezone-aware ISO 8601 when current claims matter",
  "mode": "QUICK | STANDARD | DEEP",
  "consumers": ["ai-council"],
  "constraints": [],
  "known_facts": [],
  "known_unknowns": [],
  "privacy_lane": "PUBLIC | PRIVATE | USER_SUPPLIED"
}
```

## Rules

- Do not invent missing scope. Preserve `unknown` explicitly.
- Add `as_of` whenever a material claim can change over time.
- Consumer names define handoff requirements, not the research verdict.
- `known_facts` are intake claims until evidence verifies them; do not silently grant them `VERIFIED` status.
- If scope materially changes after retrieval begins, update the contract and re-evaluate affected claims rather than silently widening the answer.

## Claim planning

Before deep search, identify:

1. critical claims that can change the downstream outcome,
2. material supporting claims,
3. definitions needed to avoid false disagreement,
4. known unknowns and likely falsifiers,
5. claim types that require current live verification.

## Research ID

Use a deterministic research ID from question + `as_of` + mode for a snapshot. Do not reuse an old ID after materially changing the question or time basis.
