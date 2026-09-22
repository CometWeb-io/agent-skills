# Repo Roaster examples

## Strong MAJOR finding

**Anchor:** `src/pay.py::settle`.

**Observed:** provider charge occurs before durable idempotency persistence.

**Reachability:** plausible from `POST /settle` through the service call.

**Falsifier pass:** searched wrapper idempotency, provider idempotency keys, and outbox; none found in the inspected path.

**Risk:** crash/retry can duplicate settlement.

**Verification:** inject a failure after provider success and retry.

## Bad finding

> There is no authorization in this repository.

Why it fails: a single grep miss does not prove absence. Inventory trust-boundary entry points, search relevant middleware/config/call sites, and use `NOT_FOUND` only with an explicit absence proof. Otherwise record a verification gap.

## Withdrawn finding

Initial concern: endpoint appears unauthenticated. False-positive pass finds router-level middleware applied to the whole group. Remove the finding rather than preserving it as a weaker joke.

## Static-only discipline

Dangerous helper code that has no established caller is not automatically CRITICAL. Mark reachability `STATIC_ONLY` or `UNKNOWN` and avoid exploitability claims.

## Invariant-first severity

Before calling a retry bug CRITICAL, tie it to an invariant such as `external settlement occurs at most once per idempotency key`, show a plausible execution path, and identify the blast radius. A suspicious helper with no caller is not enough.

## RECHECK review

A fix adds provider idempotency but only in one call site while another worker path still calls the provider directly. Mark the original finding `PARTIAL` or `OPEN`, then add a new finding only if the second path represents a distinct defect or repair burden.

## Challenger / Defender / Arbiter example

**Challenger:** a public route appears to call a destructive operation without an authorization check.

**Defender search:** inspect router/group middleware, upstream policy enforcement, service-layer guards, database authorization, feature flags, deployment exposure, and tests that exercise the path.

**Arbiter:** CRITICAL survives only if reachability and impact remain plausible after those controls are considered. If the route is internal-only, unreachable, or guarded upstream, downgrade or withdraw.

The final report must distinguish static suspicion from an established execution path.
