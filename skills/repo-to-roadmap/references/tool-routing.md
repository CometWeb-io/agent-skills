# Tool and Source Routing v2

## Principle

Choose the system of record for the claim before choosing the easiest connector.

## Repository / GitHub

Use for:

- repo identity/default branch/ref,
- directory/tree/workspace inventory,
- manifests/configuration,
- code and schema evidence,
- tests and CI/release artifacts,
- issues/PRs/commits/branches,
- deployment/runtime configuration stored in repo.

Pin material implementation conclusions to a branch/ref/commit when possible.

Do not rely on code search alone for completeness. If the connector cannot enumerate the tree reliably, downgrade coverage rather than pretending search is exhaustive.

## Product context / Notion / Docs / Drive

Use for:

- desired target state,
- approved requirements/decisions,
- PRDs/specs,
- business constraints,
- historical rationale,
- prior roadmap snapshots.

Treat these as intent/history unless they contain separately verifiable implementation/runtime evidence.

## Analytics / telemetry

Use for:

- activation/adoption/conversion/retention,
- feature usage,
- error/latency/performance outcomes,
- deployment throughput/stability when captured,
- cohort/funnel behavior.

Verify event definitions and instrumentation quality before using a metric as binding evidence.

## Customer Ops / support / incidents

Use for repeated user pain, failure modes, support load, incidents, churn signals, and real workflow friction. Distinguish anecdote count from prevalence.

## Live application / browser

Use when the roadmap depends on actual UI behavior, form state, cross-screen consistency, runtime data correctness, or a critical user journey. Prefer a specialist web-app audit when deep QA is required.

## External web

Use only when a current external fact materially changes the roadmap, for example vendor/API behavior, platform support, standards, advisories, or regulation/policy.

Prefer current official/primary sources. Mark the claim current-sensitive and record `as_of` / verification time.

Never send private raw source chunks to public search.

## Missing access

Do not fill a connector gap from assumption. Mark the affected domain `UNAVAILABLE`, lower scope confidence, and state which roadmap decision remains unresolved.

## Read-only default

Discovery and roadmap creation are read-only by default. Do not create issues, edit docs, change repo files, merge PRs, or trigger deployments unless the user explicitly asks for that separate side effect and the active tool policy permits it.
