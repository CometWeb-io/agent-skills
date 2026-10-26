# Semantic fidelity

Compare the rewrite with the source, not merely its fluency. For dense or ambiguous claims, use a compact claim map: proposition, negation, certainty/obligation, scope, attribution, conditions, evidence and exact protected spans. A separate ledger is unnecessary for a straightforward edit; expose it only when requested.

Check in both directions: each material output claim needs source support, and each material source claim must survive unless shortening was requested. Shortening may omit detail, but not a condition or caveat that changes the conclusion. Preserve unresolved ambiguity rather than guessing.

Look especially for changed meaning despite preserved tokens:

- “may improve” becoming “improves”, or an obligation becoming optional;
- an attributed report becoming the author's assertion;
- values or responsibilities moved to another entity;
- negation, chronology, causality, scope, thresholds or exceptions reversed;
- new examples, metrics or personal experiences without a source.

Quoted text and code stay exact unless the task explicitly permits changing them. An attributed paraphrase is not an exact quotation. Use the guard below for mechanical checks, followed by source-level semantic review.

## Deterministic invariant guard

Commands:

```bash
python scripts/rewrite_guard.py before.md after.md --summary
python scripts/rewrite_guard.py before.md after.md --strict --protect "Alice"
python scripts/rewrite_guard.py before.md after.md --protect-file protected.txt
```

The guard checks extractable hard invariants such as URLs, emails, dates, versions, DOI-like identifiers, numbers, number+unit pairs, Markdown destinations, paths, code, quotes, numeric citations, UUIDs, CVEs, RFC references, long CLI flags, environment-style identifiers, issue-like IDs, hashes, and selected proper-name candidates.

It also reports **semantic-risk warnings** when negation/modal/scope markers change unusually. These warnings are heuristics, not semantic proof.

Pass/fail is an **invariant verdict**. Neither the default nor `--strict` fails on
a semantic-risk warning — `--strict` covers introduced invariant-like tokens, not
meaning. A rewrite that inverts every claim keeps its invariants and exits `0`.
When a caller must stop on a possible meaning change, ask for it:

```bash
python scripts/rewrite_guard.py before.md after.md --fail-on-semantic-risk
```

It is opt-in because the markers fire on faithful paraphrase too: turning
"We are not committing to a date" into "No date is committed" drops a negation
token. Choose it when a missed inversion costs more than a false positive.

Use `--protect` for exact names, labels, or normative phrases that heuristics cannot infer safely.

Without `--summary` the guard prints one JSON object and exits `0` when `passed`, `1` otherwise (`2` on unreadable input):

```text
passed: the invariant verdict
strict, fail_on_semantic_risk: the flags in force
missing_invariants: {category: [{value, count}]} present before, absent after
added_invariants: {category: [{value, count}]} introduced by the rewrite; fail only with --strict
semantic_risk_markers: {negation|modality|scope: {removed: [...], added: [...]}}
warnings[], limitations[]: plain-language notes for the reviewer
version: guard version
```

Categories are the invariant kinds listed above (for example `urls`, `numbers`, `number_unit_pairs`, `quoted_spans`, `protected_terms`).
