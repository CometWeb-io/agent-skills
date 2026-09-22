# Real-world operational playbook

Use this guide for production reviews involving multiple content artifacts, analytics, evidence documents, revisions, stakeholders, or incomplete access.

## Intake

1. Pin the primary artifact and version.
2. Record supporting sources separately: analytics, customer evidence, research, brand constraints, prior review, revision.
3. State the requested business action and decision cost. If unknown, keep it unknown.
4. Decide whether external verification is authorized. Do not silently browse.
5. Create a review session manifest when more than one source or revision is involved.

## Evidence acquisition order

Prefer evidence in this order: artifact itself -> supplied system-of-record proof -> authorized analytics/customer evidence -> authorized external verification. Do not let generic conversion doctrine outrank direct artifact evidence.

## Production failure modes

- The page is fine but the offer is weak: diagnose OFFER/PRODUCT rather than rewriting copy.
- The claim could be true but proof is absent: record proof debt; do not call it false.
- Analytics are aggregate-only: do not infer causality or reader objections from them.
- Only screenshots/excerpts are available: lower coverage and block omission claims that require full-artifact search.
- Multiple stakeholders disagree: preserve the review contract and source evidence; do not turn preferences into defects.

## Review budget

For FULL/RED_TEAM prioritize: central promise, quantitative/outcome claims, proof before commitment, objection handling, CTA/commitment mismatch, and cross-artifact inconsistency. Stop adding MINOR findings once they no longer change the recommended repair.

## Closure

A revision closes a finding only when its original acceptance check passes. A rewritten sentence is not closure when the root cause was missing proof, offer design, product capability, or audience mismatch.
