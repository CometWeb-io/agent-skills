# Click-through law

Looking is not clicking. Reading source is not clicking. A screenshot is not
clicking. But unsafe execution is not required for "coverage" either.

Read `safety-and-mutations.md` before this file when a control may persist data
or cause an external effect.

## 1. Interactive map

For each in-scope control/pattern record:

```text
control:       visible name / accessible name / icon+context
role:          button | link | tab | input | select | toggle | menu | row-action | other
risk:          read-only | local-state | persistent | external | destructive | financial | permission
coverage:      tested | sampled | policy-blocked | environment-blocked | unreachable | out-of-scope
activation:    click | keyboard | both | inspected-only | not-run
result:        observed outcome
```

Include icon-only controls, disabled controls, fake-clickable cards/rows,
pagination, menus, chart legends, and app-controlled browser-back behavior.

## 2. Safe activation recipe

For a policy-allowed control:

1. Inspect label/icon/enabled state.
2. Focus it; note visible focus when relevant.
3. Exercise keyboard semantics when supported by capability.
4. Pointer/tap activation.
5. Observe durable state, URL, rendered feedback, console/network only if tools
   expose them.
6. Verify the promised side effect only when the mutation policy allows it.
7. Return/cancel/back and confirm sane state.

For a policy-blocked control, stop before commit. You may inspect confirmation
copy and cancel path if opening the confirmation itself is safe.

## 3. Standard vs forensic

### Standard

Test:

- all primary safe actions
- all unique interaction patterns
- all state variants that materially change behavior
- representative repeated rows/cards
- destructive/external/financial controls up to their safe boundary

Do not repeatedly click 200 identical row menus. Test representative state
variants and record the sampling rule.

### Forensic

No sampling. Activate every in-scope instance that policy and environment allow.
Policy-blocked instances remain accounted for, not executed.

## 4. Forms and components

Open/test supported tabs, accordions, dropdowns, popovers, date pickers, menus,
and form states according to depth. For forms, see `forms-and-states.md`.

Deep-link/hash/query persistence is a requirement only when the product/spec or
web semantics imply shareable/navigation state; otherwise treat URL persistence
as a heuristic/recommendation, not an automatic defect.

## 5. Multi-screen consistency

For area/flow:

- entry/return paths are coherent
- selected navigation matches location
- breadcrumb/heading/title are not misleading
- the same entity retains identity/status/money across list/detail/edit
- permissions presented in UI match reachable actions
- safe test mutations reappear in durable state without false-success UI

Breadcrumbs do not have to exist or be links on every app. File only when their
actual behavior contradicts a requirement/convention and harms navigation.

## 6. Touch/hover

At mobile/touch capability check:

- hover-only actions have a tap path
- primary/destructive hit areas are usable
- sticky chrome does not cover the job
- row click vs nested button does not cause accidental navigation

44x44 is a useful target, not a universal automatic defect threshold. When
using an accessibility standard as the basis, cite/measure the applicable
criterion rather than guessing.

## 7. Pattern hints, not severity law

These patterns deserve attention:

- primary control visibly does nothing
- label promises X, observed outcome is Y
- success feedback but durable state unchanged
- confirm completes but state does not change
- unexplained disabled primary action
- duplicate submit creates duplicate persistent effect
- control works only once until refresh

Assign severity from `evidence-and-report.md` based on actual job impact. Do not
hardcode blocker from the pattern name.

## 8. Coverage log

Report totals by status, e.g.:

```text
total in-scope:       47
tested:               31
sampled:               9
policy-blocked:        3
environment-blocked:   1
unreachable:           3
```

Forensic: `sampled` must be 0.
Standard: sampling must name the repeated pattern and representative states.
If a terminal requirement cannot be proven because it is policy/environment
blocked, verdict is `incomplete`, not a fake pass.
