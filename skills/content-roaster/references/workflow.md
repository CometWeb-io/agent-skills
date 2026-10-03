# Content Roaster: full workflow

The detailed procedure behind the step index in `SKILL.md`. Open this file before any non-QUICK review, and whenever a step's detail is needed in QUICK mode. The core contract, admission gates, and hard boundaries in `SKILL.md` still govern every step; nothing here relaxes them.

## Workflow steps

### 1. Establish source scope

Create `source_manifest`. Record whether each source is a full artifact, excerpt, screenshot transcription, analytics excerpt, supplied research, or other material. Include version/hash/as-of metadata when available. Never claim complete coverage from a fragment.

### 1A-1D. Review setup

Follow `references/review-operations.md` (shared): plan the review budget, apply the source instruction firewall, build the evidence register, and choose the assurance mode.

### 2. Recover the decision contract

Record audience, desired action, decision stage, decision cost, constraints, and unknowns. Do not invent a persona or funnel state just to make the roast more specific.

### 3. Build the message chain

Reconstruct:

`problem -> promise -> mechanism -> proof -> objection handling -> action`

Use `unknown` for elements not recoverable from the source. The message chain is descriptive evidence, not a recommendation.

### 4. Build the claim map

For every material promise record:

- claim type: `FACTUAL`, `QUANTITATIVE`, `COMPARATIVE`, `OUTCOME`, `MECHANISM`, `GUARANTEE`, or `SUBJECTIVE`;
- decision role: `PRIMARY` or `SUPPORTING`;
- exact source anchor with `source_id`;
- proof status: `PRESENT`, `WEAK`, `ABSENT`, or `EXTERNAL_REQUIRED`;
- proof burden: `LOW`, `MEDIUM`, `HIGH`, or `VERY_HIGH`.

A strong claim deserves proportionate proof. Do not call an unproved claim false merely because the artifact does not prove it.

### 5. Build proof-debt and objection ledgers

`proof_debt_ledger` records material gaps between claim burden and supplied evidence. `objection_ledger` records only objections that could materially alter the requested action. Do not pad either ledger with generic marketing doctrine.

### 5A. Diagnose the layer that actually failed

Build `diagnosis_ledger` for material problems. Classify the root layer as `COPY`, `PROOF`, `POSITIONING`, `OFFER`, `PRODUCT`, `AUDIENCE`, `STRUCTURE`, `UX`, or `MIXED`, link it to claims/evidence, and name the downstream repair owner. Do not prescribe a copy rewrite for a product, proof, or offer failure disguised as wording friction.

### 6. Scan the reader journey

Search for the first point where the artifact asks the reader to believe, understand, or commit more than it has earned. Classify friction as discovery, cognitive/comprehension, trust, decision, or action friction.

### 7. Generate candidate findings

Each candidate needs a stable `finding_key`, optional aliases, severity, category, evidence state, evidence strength, scope sensitivity, exact anchor with `source_id`, linked claim ids, decision impact, materiality, observation, failure mode, consequence, repair class, repair, verification contract, and confidence. `roast_line` is optional.

Every admitted finding also records `evidence_refs`, a structured `confidence_basis`, and `residual_risk` after the proposed repair. High confidence is not a writing style: it requires direct enough evidence, sufficient scope support, and addressed counterevidence.

Use `MISSING` only with an `omission_basis`. Use `VERIFY_EXTERNAL` when the truth cannot be decided from the artifact. Use `INFERRED` only with an inference basis.

Severity:

- `BLOCKER`: undermines the central promise, trust, or requested action.
- `MAJOR`: materially weakens comprehension, differentiation, persuasion, credibility, or commitment readiness.
- `MINOR`: local weakness with bounded impact.

BLOCKER requires a PRIMARY claim, decision impact `TRUST`, `DECISION`, or `ACTION`, evidence strength above WEAK, and scope sensitivity below HIGH.

### 8. Run Challenger -> Defender -> Arbiter

Before admitting BLOCKER or MAJOR, open `references/severity-calibration.md`, then open `references/adversarial-protocol.md`. Search the entire reviewed scope for proof, qualification, intentional sequencing, brand constraints, or counterexamples that neutralize or narrow the attack. Emit only the post-arbitration finding.

### 9. Compress root causes

Group findings when one underlying issue and one repair explain multiple symptoms. A report with 15 near-identical copy complaints is weaker than a report that identifies the mechanism producing them.

### 10. Test the repair

Run the counterfactual repair test. Verification must state method, success condition, and failure signal. If the proposed check cannot distinguish fixed from unfixed, rewrite the repair.

### 11. Re-review revisions

For DELTA mode open `references/revision-protocol.md`. Preserve stable finding keys, allow aliases for moved/renamed findings, rerun old acceptance conditions, and distinguish artifact improvement from merely increased reviewer scope.

### 12. Preserve what survives

Record strong elements worth protecting during revision. Do not force praise.

### Assurance and disagreement closure

Follow the closure section of `references/review-operations.md` before declaring the outcome.

### 13. Declare review outcome

Choose exactly one:

- `MATERIAL_FINDINGS`
- `NO_MATERIAL_FINDINGS`
- `INSUFFICIENT_EVIDENCE`

Always populate `outcome_basis` with the surviving finding ids, withdrawn/unresolved candidate counts, and a bounded reason. If evidence is insufficient, mark at least one quality gate `BLOCKED`, return no material findings, and say what evidence is needed. A clean result needs an auditable basis just as much as a material finding does. Do not disguise missing evidence as a positive result.

### 14. End with one core fix

Return exactly one highest-leverage repair sentence, or a bounded no-fix/evidence-needed statement when appropriate.

## Lens definitions

Use `GENERAL` unless the user clearly asks for one or more lenses:

- `POSITIONING`: audience, category, differentiation, value proposition, mechanism, proof.
- `CONVERSION`: sequencing, objections, commitment, CTA proportionality, friction, trust.
- `EDITORIAL`: logic, information architecture, density, repetition, readability.
- `TRUST`: claim-evidence fit, provenance, qualification, caveats, overstatement.
- `OFFER`: package, risk reversal, price/value logic, constraints, proof before commitment.
- `TECHNICAL_DOCUMENTATION`: task clarity, prerequisites, examples, failure handling, precision.

Open `references/rubric.md` for FULL or RED_TEAM reviews.
