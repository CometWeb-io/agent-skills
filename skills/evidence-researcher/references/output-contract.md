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

| Claim | Kind | Basis | Scope | Type | Status | Confidence | Best support | Opposition | Freshness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

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
- unknown source-independence count when material,
- screening exclusions: count distinct excluded sources and list each reference,
  affected claim IDs and reason. For mixed-use artifacts, retain the allowed uses
  and edge-specific limits rather than blacklisting the source.

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

At first material citation, attribute a source's relevant commercial interest or
advocacy role once (`source-routing.md`). A participant's position is its own,
not a market consensus. Screening reasons in `notes` are human-readable judgments;
they are not separately enforced by the kernel. Keep edge `admission` consistent
with those judgments; `scope_fit: medium` alone does not impose a use restriction.

Preserve basis and explicit scope in the machine claim/edge records and the ledger.
Basis is verified_fact, user_supplied, assumption or framework_method; legacy
missing basis is unassessed. Basis is orthogonal to FACT/INFERENCE and source
class. INFERENCE stays supported, never VERIFIED. Nonfact or unassessed premises
belong under caveats, not safe factual handoff. A grader pass remains structural;
READY metadata or an explicit verified_fact label does not run observation.
Only the receiving consumer can rerun applicable caller-owned controlled checks.
