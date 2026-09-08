# Evaluation and Anti-Patterns v2

Run this review before final output. Use kernel validation whenever code execution is available.

## Assessment contract

- Is the target state explicit rather than inferred from vague words like "done"?
- Is repository scope pinned or access limitation disclosed?
- Is mode correct for the user's request?

## Coverage

- Did topology inventory precede keyword-search conclusions?
- Are all material domains accounted for?
- Are `NOT_APPLICABLE` rows justified?
- Are sampled/unavailable domains disclosed?
- If EXHAUSTIVE was requested, is every file accounted for?

## Project truth

- Are capabilities modeled separately from files?
- Are critical journeys checked end-to-end?
- Is implemented-but-unverified distinct from verified-working?
- Are history/hotspot signals treated as triage rather than defects?

## Evidence

- Does every material factual claim have a source?
- Are intent, implementation, release, outcome, and operational truth separated?
- Are current-sensitive claims backed by admissible current evidence?
- Are correlated sources prevented from inflating confidence?
- Are material contradictions surfaced?
- Is `MISSING` supported by the negative-evidence protocol rather than a search miss?

## Roadmap quality

- Are items outcome-shaped and root-cause clustered?
- Does each item link to claim IDs and target requirements?
- Does every item have observable acceptance criteria, verification method, and proof artifact?
- Are hard dependencies explicit and acyclic?
- Are `XL` items decomposed or justified?
- Are mandatory gates based on gate status rather than score?
- Are speculative problems routed to `VERIFY`/`VALIDATE` instead of expensive build work?
- Is numeric scoring subordinate to target blockers, gates, and dependencies?
- Is priority sensitivity disclosed when fragile?

## Business/product linkage

- Does each implementation item have a target requirement or credible user/business/reliability/risk/enablement path?
- Are outcome claims grounded in outcome evidence?
- Are client-ready/paid-production promises tied to acceptance evidence rather than architecture taste?

## Living roadmap

- Is there a baseline snapshot hash when the roadmap will be reused?
- Are revalidation triggers explicit?
- In DELTA mode, were affected claims and transitive hard dependents revalidated?
- Was the old snapshot preserved rather than overwritten?

## Composition

- Were specialist skills used when deep domain authority was required?
- Was AI Council used only for contested material decisions?
- Is execution-cycle selection left to product-operator?
- Does downstream handoff preserve stable IDs/evidence rather than only prose?

## Fail conditions

Fail the output if it contains any of these without explicit qualification:

- invented delivery dates or capacity,
- fake ROI or calibrated-looking probability with no basis,
- "whole repo reviewed" without coverage evidence,
- "feature works" from code presence alone,
- "released" from merged PR alone,
- `MISSING` from a search miss,
- `BLOCKER` created solely by a numeric score,
- unsupported security/privacy/legal conclusion from a generalist pass,
- large unordered backlog presented as roadmap,
- silent conflict between docs and implementation,
- a delta roadmap that ignores invalidated dependencies.

## Golden eval themes

The bundled tests should cover at least:

1. code presence cannot verify behavior,
2. merged change cannot verify release,
3. stale evidence cannot support current-sensitive claim,
4. unknown independence does not create fake corroboration,
5. absence requires complete negative-evidence protocol,
6. unverified mandatory gate becomes `VERIFY_NOW`, not blocker,
7. explicit gate `BLOCK` becomes blocker regardless score,
8. graph cycles/missing deps fail,
9. changed claim invalidates linked roadmap items and transitive dependents,
10. target-state change invalidates priority broadly,
11. item claim refs must exist,
12. acceptance criteria must specify verification/proof,
13. unjustified `NOT_APPLICABLE` fails validation,
14. `XL` execution item requires decomposition rationale.
