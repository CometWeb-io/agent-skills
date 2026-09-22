# Decision log

Record governance decisions separately from findings/evidence. A decision changes workflow interpretation or authorization; it does not rewrite what was observed.

Use decision records for policy revisions, reviewer/roaster conflict resolution, controls/waivers, `WONT_FIX`, reopen decisions, and champion/challenger promotion/hold.

Preserve at minimum:

- `decision_id`, `run_id`, `candidate_id`;
- `decision_type`, `outcome`, `rationale`;
- `evidence_refs[]` that point to immutable evidence/finding identifiers;
- `decided_at` with timezone;
- previous/current hash when a hash-chained log is available.

Never mutate the evidence ledger to make it agree with a decision. If the evidence changes, create new evidence and a new decision.
