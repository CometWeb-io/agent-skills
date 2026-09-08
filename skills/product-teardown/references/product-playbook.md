# Product, app, API, and website teardown playbook

## Table of contents

1. Select the job and state space
2. Flow-first inspection
3. State coverage
4. Product system map
5. Monetization and distribution
6. Trust, support, and operations
7. API/developer surfaces
8. Evidence cautions

## 1. Select the job and state space

Start with the decision question and select only the jobs/surfaces that can answer it.

Do not inventory every screen by default.

Record relevant context:

- anonymous vs authenticated;
- plan/tier/account role;
- platform/device;
- new vs mature workspace/account;
- experiment/cohort if known;
- locale/region if material.

## 2. Flow-first inspection

Start from jobs, not screens. Typical critical flows include:

- discover -> understand -> start;
- signup -> setup -> first value;
- create -> edit -> validate -> publish;
- invite -> collaborate -> approve;
- detect issue -> investigate -> fix -> verify;
- upgrade -> pay -> use gated capability;
- fail -> recover -> contact support;
- import/integrate -> map -> validate -> sync;
- long-running action -> progress -> completion -> retry/recovery.

For each flow capture entry, steps, decisions, state transitions, feedback, persistence, exit, and recovery.

## 3. State coverage

Inspect meaningful states, not only happy path:

- empty/first-use;
- loading/skeleton/progress;
- success/confirmation;
- validation/error;
- partial data/offline/retry;
- permission denied/role differences;
- limits/quotas/paywall;
- destructive confirmation/undo;
- long-running/background completion;
- stale/conflicting/concurrent edits;
- integration disconnected/degraded;
- partial failure in bulk actions.

Patterns often live in state handling rather than the primary screen.

## 4. Product system map

Map only what explains the candidate pattern:

- visible object model;
- navigation/workspace/account hierarchy;
- permissions/ownership;
- workflow/state machine;
- automation/agent surfaces;
- integrations/import/export;
- notifications/collaboration;
- settings/admin/billing/support;
- user-visible audit/history/versioning.

Do not infer backend entities solely from UI nouns.

## 5. Monetization and distribution

When relevant inspect:

- upgrade trigger;
- value metric: seat, usage, object, feature, time, outcome, etc.;
- trial/freemium transition;
- upgrade friction/recovery;
- sharing/export artifacts that create distribution;
- templates/examples/community/integrations that reduce activation cost;
- packaging differences that change observed behavior.

Do not infer conversion lift from existence of these mechanics.

## 6. Trust, support, and operations

Look for transferable mechanisms in:

- audit history/change visibility;
- permissions/destructive controls;
- explainability of automated actions;
- incident/error communication;
- contextual diagnostics/support entry;
- privacy/security settings;
- accessibility/keyboard behavior;
- export/delete/retention controls;
- failure recovery and human override.

## 7. API/developer surfaces

When product value depends on developers or integrations, inspect:

- auth/token model as documented;
- API object model and consistency;
- pagination/idempotency/retry behavior;
- webhooks/events and delivery semantics;
- SDK/CLI ergonomics;
- sandbox/test mode;
- rate limits/error semantics;
- docs examples and migration/versioning patterns.

Treat documented semantics as documented behavior unless runtime/code evidence is available.

## 8. Evidence cautions

- Marketing pages reveal positioning, not necessarily in-product behavior.
- A demo may be scripted, gated, or pre-release.
- A screenshot proves only represented state/version.
- Behavior can vary by plan, role, geography, platform, account age, or experiment.
- Third-party complaints prove reported perception, not root cause.
- Public UI cannot prove backend implementation.
- Repeated UX conventions do not prove causal outcome.
