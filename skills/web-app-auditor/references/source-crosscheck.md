# Source cross-check (local apps)

When the target is a codebase you can read, use it to **explain** UI
findings, not to replace the browser.

## 1. Order

1. See it in the UI (or prove you cannot reach it).
2. File the user-facing finding.
3. Then grep/read for the root cause (wrong reducer, off-by-one, badge
   using a stale length, tax function, copy duplicated in two files).
4. Put the pointer in `Root cause` (`src/routes/billing.tsx:184`).

When browser execution is unavailable, source may support a static finding at
`confidence: medium` only when the rendered/static consequence is deterministic.
Interaction outcomes remain inferred or `needs-repro`; never write "I clicked".

## 2. What source is good for

- Confirming a count used `items.length` instead of `items.filter(active)`.
- Finding a second hardcoded price.
- Tracing why a toggle snaps back (local state vs server).
- Discovering a route that should be in the area map.

## 3. What source is not

- A reason to skip Pass 2.
- A license to report unused variables, hook order, or "could use Zod"
  as audit findings. That is a different skill (code review).
- Proof that a network call actually happened. Observe network/telemetry, or
  state that execution was not verified.
- A reason to expose secrets, tokens, or personal data from config/logs in the
  report. Redact/minimize evidence.

## 4. Fixes

Only implement if the user asks. The audit report can include a one-line
suggested fix per finding. A follow-up turn then patches, with tests for
the contradiction (assert badge === rows, assert total === sum(lines)).
