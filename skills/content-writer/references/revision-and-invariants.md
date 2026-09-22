# Revision, source policy, and invariant control

Use this reference for revisions, source-bounded work, or artifacts where changing one section can silently invalidate another.

## Candidate lineage

Keep `candidate_id`, `parent_candidate_id`, and `brief_id` stable and explicit. A revision must have a new candidate identity; never overwrite evidence so it appears to belong to the new candidate.

## Source policies

- `SOURCE_BOUND`: material factual support may come only from explicitly approved sources.
- `EVIDENCE_REQUIRED`: material claims require admissible support; missing support remains unresolved.
- `CONTEXTUAL_DRAFT`: drafting can continue, but the candidate is not release-eligible while material factual uncertainty remains.
- `CREATIVE`: evidence is not the organizing constraint, but factual assertions still cannot be invented.

For high-risk factual claims, prefer `PRIMARY`, `OFFICIAL`, or `SYSTEM_OF_RECORD` authority. A secondary source may discover a claim without being strong enough to carry it.

## Claim graph

Use `depends_on_claim_ids` when a conclusion relies on intermediate claims. Reject dangling dependencies and cycles. A supported conclusion cannot remain supported if a material dependency becomes unresolved.

## Protected invariants

Record every protected invariant from the brief and an explicit `PASS|FAIL|UNKNOWN` check after substantial edits. Do not trade factual accuracy, required wording, legal/compliance boundaries, or user-specified exclusions for smoother prose.
