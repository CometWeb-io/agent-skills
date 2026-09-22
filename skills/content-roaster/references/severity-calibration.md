# Content severity calibration

Use severity to encode decision damage, not writing ugliness.

## BLOCKER

Admit only when the reviewed evidence shows that the primary promise, trust basis, or intended action is materially undermined for the stated audience and decision stage. Require:

- a PRIMARY claim or the central message chain;
- evidence strength STRONG or MODERATE;
- confidence not LOW;
- scope sensitivity LOW or MEDIUM;
- materiality centrality CENTRAL and consequence HIGH;
- impact on TRUST, DECISION, or ACTION;
- a surviving Challenger -> Defender -> Arbiter pass.

Examples: the offer asks for a high-cost commitment before the buyer can establish what is being sold; a guarantee directly contradicts the stated commercial terms; a primary quantitative outcome claim has no decision-relevant proof where proof is necessary for the requested commitment.

## MAJOR

Use when the content can still work, but a meaningful persuasion, comprehension, differentiation, credibility, or objection-handling failure materially weakens the intended decision path.

Examples: a central mechanism is buried after the CTA; a comparative claim lacks a comparison basis; the strongest proof is mismatched to the primary promise; a major objection is unanswered at the decision point.

## MINOR

Use for local friction whose repair improves clarity or trust without changing the main decision path.

Examples: local redundancy, weak heading hierarchy, avoidable jargon, an imprecise supporting sentence.

## Downgrade tests

Downgrade when any of these are true:

- the problem appears only under a speculative audience assumption;
- the alleged omission sits outside the reviewed scope;
- counterevidence elsewhere in the artifact materially answers the concern;
- the issue is stylistic preference without an observable reader consequence;
- the repair would not change the decision path or acceptance condition.

## Stop condition

If the review cannot establish audience/action context or inspect enough of the artifact to support the claimed consequence, prefer `INSUFFICIENT_EVIDENCE` or a lower-severity, scope-bounded finding rather than inflating severity.
