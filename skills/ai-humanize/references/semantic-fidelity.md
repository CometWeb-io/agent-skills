# Semantic fidelity

A natural rewrite is a failure if it changes the proposition. Surface fluency is secondary to preserving what the source commits to.

## Claim ledger

For `strong` rewrites with dense factual content and for every `deep` rewrite, reduce the source to a small internal ledger before writing.

For each material claim capture:

- **proposition**: what is asserted;
- **polarity**: positive / negative;
- **modality**: must / should / may / likely / uncertain / conditional;
- **scope**: who or what the claim applies to, including geography, segment, quantity, and time window;
- **attribution**: author assertion vs quote vs report vs external source;
- **conditions**: only if, unless, when, after, before, except;
- **evidence**: numbers, citations, examples, measurements;
- **hard invariants**: names, dates, values, units, versions, identifiers, quotes, URLs, code.

Do not expose the ledger unless the user asks for an audit.

## Drift classes

Check for these failures after rewriting:

### Omission

A material claim, caveat, exception, or condition disappeared.

### Strengthening

`may improve` became `improves`; `associated with` became `causes`; `early evidence` became `proven`.

### Weakening

A mandatory condition became optional, or a definite source statement became tentative without reason.

### Negation flip

`does not support` became `supports`, or a negative condition disappeared into a smoother sentence.

### Scope drift

`some users` became `users`; `EU customers` became `customers`; `up to 10 MB` became `10 MB` without the bound.

### Attribution drift

`The study reports X` became `X is true`; `Alice said X` became the author's own assertion.

### Role swap

Values, responsibilities, actors, labels, or outcomes were preserved individually but attached to the wrong entity.

### Chronology or causality inversion

`after` became `before`; correlation became cause; prerequisite and consequence were swapped.

### Unsupported concretization

A vague source statement was replaced with a specific feature, metric, customer, anecdote, example, implementation detail, or citation that was not supplied.

## Shortening

If the user explicitly asks to shorten:

- omissions are allowed;
- keep claims that determine the conclusion;
- keep caveats that materially constrain those claims;
- do not remove uncertainty simply because it is verbose;
- do not compress two differently scoped claims into one stronger generalization.

## Final entailment pass

Before delivery, ask for each material sentence in the rewrite:

1. Is this supported by the source or explicit user instruction?
2. Is its polarity the same?
3. Is its confidence no stronger?
4. Is its scope no broader?
5. Is attribution preserved?
6. Are conditions and exceptions still attached to the right claim?

Then reverse the check: for each material source claim, find where it survives in the rewrite.

`rewrite_guard.py` helps with hard tokens. This semantic pass is still required because token preservation alone cannot catch role swaps or causal drift.
