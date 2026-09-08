# Project Truth Model

## Purpose

Build a model of the project that survives beyond a file-by-file summary. Treat code as one evidence source inside a project system, not as the roadmap itself.

## Project Surface Graph

Model material nodes such as:

- repository / workspace / package,
- application / service / worker / job,
- public interface / route / API / webhook,
- datastore / schema / migration path,
- authentication / authorization boundary,
- billing / entitlement boundary,
- integration / external dependency,
- deployment / runtime / environment,
- critical user journey,
- product requirement / approved decision,
- observability / incident / support surface.

Record only edges that matter to delivery or verification, for example runtime dependency, data flow, deploy dependency, auth boundary, event flow, hard implementation prerequisite, or shared ownership boundary.

For large repositories, use an available symbol/dependency map, language server, repository map, or equivalent as a routing aid. It helps decide what to inspect next; it is not proof that a behavior works.

## Capability Inventory

Represent user/product capabilities separately from source files. Use stable capability IDs.

Allowed states:

- `VERIFIED_WORKING` - behavior is directly verified at the required scope.
- `IMPLEMENTED_UNVERIFIED` - implementation is present but required behavior is not directly verified.
- `PARTIAL` - material pieces exist but the target outcome is incomplete.
- `STUBBED` - placeholder, mock-only, disabled, or non-production path.
- `BROKEN` - direct evidence shows the required behavior fails.
- `MISSING` - absence is verified using the negative-evidence protocol.
- `UNKNOWN` - evidence is insufficient to distinguish the states above.
- `NOT_APPLICABLE` - capability does not apply to the target state, with rationale.

Do not use `MISSING` from a keyword search miss. Use `UNKNOWN` until absence is verified.

Recommended capability row:

```json
{
  "capability_id": "CAP-auth-session",
  "name": "Authenticated session lifecycle",
  "state": "IMPLEMENTED_UNVERIFIED",
  "criticality": "high",
  "claim_refs": ["C-014", "C-015"],
  "target_requirement_refs": ["T-007"],
  "confidence": 0.78
}
```

## Critical Journeys

Trace end-to-end journeys that define the requested target state. Examples include:

- sign up -> first value,
- login -> protected action -> logout,
- checkout -> entitlement -> invoice,
- create -> persist -> retrieve -> edit -> delete,
- deploy -> migrate -> health check -> rollback,
- incident -> detect -> diagnose -> recover.

A critical journey can cross packages, repositories, services, queues, data stores, and external vendors. Do not call it verified because each component exists independently.

## Architecture Invariants

Record a small number of invariants when violating them would invalidate many roadmap conclusions. Examples:

- only one system writes a canonical record,
- entitlement is checked server-side for every paid action,
- migrations are forward-compatible for the release strategy,
- secrets never cross a client boundary,
- a background job is idempotent.

Treat invariants as claims requiring evidence, not as architectural preferences.

## Change-history signals

Use commit/PR history to find where to inspect, not to prove defects. Useful signals include:

- high-change hotspots,
- files/modules that repeatedly change together,
- repeated revert/fix-forward patterns,
- long-lived incomplete branches,
- recurring issue clusters,
- ownership or review bottlenecks.

Label these as `triage signals`. Convert them into roadmap work only after a material problem or risk path is verified.
