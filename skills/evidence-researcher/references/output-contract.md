# Evidence Pack Output Contract

## Default: progressive disclosure

Do not dump the full graph unless the user or consuming workflow needs it.

### 1. Research status

State:

- question and relevant scope,
- `as_of` for current claims,
- mode,
- status: `READY | PARTIAL | REFRESH_REQUIRED | BLOCKED_BY_CONTRADICTION`.

### 2. Bottom line

State what the evidence establishes, what it does not establish, and the highest-impact uncertainty. Keep recommendations downstream.

### 3. Material Claim Ledger

| Claim | Kind | Type | Status | Confidence | Best support | Opposition | Freshness |
| --- | --- | --- | --- | --- | --- | --- | --- |

Show critical/material claims. Supporting claims can remain machine-readable only.

### 4. Contradictions and gaps

Show only conflicts/gaps capable of changing the synthesis or downstream decision.

### 5. Coverage/readiness

Report at minimum:

- material claim readiness,
- authority-admissible support coverage,
- primary/system-of-record coverage,
- falsifier coverage,
- freshness coverage,
- unresolved critical contradictions/gaps,
- unknown source-independence count when material.

### 6. Handoff

Explicitly classify:

- claims safe for downstream use,
- claims requiring caveats,
- claims that must not be treated as facts,
- live evidence that a downstream decision skill must re-verify.

## Machine-readable pack

Use schema `2.0` from `evidence-graph.md`. Include the kernel `pack_hash` when preserving a snapshot.

## Citation discipline

Cite at the claim/evidence statement, not in a detached bibliography. Preserve pinpoint locators when the tool/source supports them. Do not reproduce long copyrighted/private passages merely to make provenance look stronger.
