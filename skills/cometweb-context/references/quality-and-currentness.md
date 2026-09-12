# A fresh context is a source-backed snapshot, not a memory dump

Maintainer review: 2026-09-12. This date does not certify live task inputs.

Choose authority for the claim: deployed configuration for availability, a repository
revision for implementation, billing records for payment, an explicit decision record
for intent, and current communication for a commitment. A newer file is not necessarily
more authoritative. Preserve disagreements and stale-versus-current distinctions.

Use timezone-aware ISO timestamps. Retrieval cannot occur after envelope generation;
a future effective date can describe a scheduled change, not a completed one. A delta
requires an identified available baseline. Missing baseline means “cannot compare”,
not “nothing changed”. Empty source locators and empty fact statements are not evidence.

Limit a local repository snapshot to the configured root. Do not follow a registry
path outside it, and do not mistake a subdirectory for its parent Git repository.
Keep workstation paths out of normal errors as well as normal results.

Use only the sources necessary for the question. Keep personal data, credentials,
customer exports, and private strategy out of public claims. A high-confidence fact
still needs an appropriate source and sensitivity. First Principles guide choices;
they are not proof of shipping, revenue, market demand, or a scientific result.

## Evidence that would block acceptance

Stop approval when a decisive claim lacks an inspectable source, a required operation
was not executed, a protected invariant changes, or validation fails. Return the
bounded result and the specific missing evidence; do not fill the gap with confidence.

## Task-time source checks

Open the applicable current primary/system-of-record source before relying on a volatile
claim. Record actual version, effective/observed time, scope, and retrieval limitations.
The shared source-review ledger schedules maintenance; it cannot establish currentness
of every operational claim. Stable methodological guidance above is an editorial
operating policy, not a claim of a new universal standard.

No external product/legal facts are hard-coded in this domain supplement. Live
operational facts must come from the systems of record selected for the task.
