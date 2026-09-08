# Refresh and Delta Research

## Principle

Evidence Packs are immutable snapshots. Current truth may change; do not overwrite history to make an old pack look current.

## Refresh plan

Use `refresh-plan` to classify material source dependencies:

- `REFRESH_NOW` — stale/superseded/draft/not-yet-effective/unknown,
- `REFRESH_SOON` — near expiry,
- `REVERIFY_ON_NEXT_MATERIAL_RUN` — live-verification claim class,
- `NO_ACTION` — no current refresh action.

## Delta workflow

When revisiting prior research:

1. load prior Evidence Pack,
2. build a new Research Contract and `as_of`,
3. inspect refresh-plan dependencies,
4. refresh affected claims/sources first,
5. run falsifier/version checks for changed areas,
6. compare snapshots with `delta`,
7. preserve both pack hashes.

Do not re-run unrelated stable historical evidence unless a changed dependency affects it.

## Delta report

Track at minimum:

- added/removed claims,
- claim status/text/materiality changes,
- added/removed source artifacts,
- contradiction resolution changes,
- old/new pack hashes.

A delta is evidence state change, not automatically a decision change. Downstream consumers decide whether the change is material to their own contract.
