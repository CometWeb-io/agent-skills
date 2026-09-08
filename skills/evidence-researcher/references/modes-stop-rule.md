# Research Modes and Stop Rule

## QUICK

Use for narrow, low-downside verification.

Default operating envelope:

- 1-3 material claims,
- primary/official/system-of-record source first,
- falsifier pass for each material claim,
- minimal visible ledger,
- no exhaustive citation-chain tracing unless a blocker appears.

## STANDARD

Default for product, technical, business, marketing, and multi-source research.

Require:

- full material claim decomposition,
- authority routing per claim,
- separate support/falsifier passes,
- lineage/independence grouping,
- temporal admission,
- coverage audit,
- explicit gaps and handoff.

## DEEP

Use for consequential, disputed, regulated, high-uncertainty, due-diligence, or expensive-to-reverse research.

Add:

- deeper source lineage/citation-chain tracing,
- multiple plausible definitions and scope interpretations,
- method/population/jurisdiction fit review,
- explicit negative-evidence and absence-test design where relevant,
- retraction/correction/version checks,
- scenario-specific evidence gaps,
- qualified human expert escalation when evidence type requires it.

## Escalation triggers

Escalate one mode when:

- critical claim has only secondary evidence,
- current controlling evidence cannot be verified,
- independent source groups materially disagree,
- legal/security/privacy/safety evidence gates downstream action,
- answer depends on narrow jurisdiction/version/definition,
- evidence quality could change a high-impact downstream decision.

## Stop rule

Stop only when:

1. material evidence gate is `READY`,
2. no critical unresolved contradiction/gap remains,
3. falsifier coverage is complete,
4. current evidence is temporally admissible,
5. either two bounded rounds add no material novelty or expected information gain is no greater than research cost.

Use `evidence_kernel.py stop` for the deterministic gate. Expected information gain and cost remain analyst inputs; the kernel does not pretend to know them.
