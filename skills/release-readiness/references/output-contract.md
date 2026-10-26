# Release decision output

For an ordinary status request, give candidate, target environment, as-of time and verdict, followed by the decisive blockers or evidence gaps and the smallest closure verification. Keep unknowns separate from observed failures. No fixed section count, full gate table or repeated review narrative is required.

If unresolved scope warnings prevent reliance on the engine result, say so explicitly and retain its raw verdict as diagnostic output. Do not present that raw GO as a completed release assessment.

## Formal receiver or CI

When a receiver, CI job or user requires the formal result, retain the complete engine JSON, its manifest/snapshot hashes, required/missing gates, scope warnings and evidence limitations. Do not substitute prose for required machine fields. Read manifest-schema.md and ci-integration.md for the actual interface; this file does not redefine it.

A requested detailed release packet may include the gate matrix, risk controls, governance decisions, evidence coverage, owners and rollout/recovery conditions. Include each only when it is material to the decision or required by the receiver. Evidence coverage and readiness score are diagnostics; neither overrides a blocking gate.

## Revalidation

A new candidate, configuration or material evidence change invalidates any pass that no longer binds to the assessed identity. Update the manifest and rerun the engine. Do not edit an old snapshot to make it describe a new candidate. A GO remains a bounded assessment, not authority to deploy, charge, migrate or publish.
