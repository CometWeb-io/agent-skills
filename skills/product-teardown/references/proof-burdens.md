# Proof burdens and mode budgets

## Table of contents

1. Evidence ceiling principle
2. Mode budgets
3. Verdict proof burdens
4. Evidence quality thresholds
5. Stop rules
6. Escalation rules

## 1. Evidence ceiling principle

A verdict cannot be stronger than the weakest decision-critical evidence lane.

Examples:

- Strong source implementation evidence plus no destination evidence -> `CANDIDATE`, not `ADOPT`.
- Strong destination pain plus speculative source mechanism -> usually `EXPERIMENT`, not `ADOPT`.
- High numeric transfer score plus unresolved IP/security blocker -> `REVIEW_REQUIRED`.
- Popularity across multiple products without outcome evidence -> prevalence signal only.

Do not use a weighted average to hide a critical gap.

## 2. Mode budgets

### SNAPSHOT

Purpose: answer a narrow question quickly.

Default limits:

- inspect only the source surfaces needed for the question;
- usually 2-5 material candidates;
- destination pass limited to problem, existing equivalent, and one or two key constraints;
- contradiction check only for top recommendation or material uncertainty;
- no broad repo archaeology;
- no multi-product census unless explicitly requested.

### STANDARD

Purpose: make a defensible transfer decision.

Default expectations:

- source flow/system map;
- destination problem/equivalent-capability check;
- 4-10 material patterns depending on evidence density;
- explicit transfer conditions and red team for top patterns;
- license/provenance pass when code/assets are involved;
- validation plan for uncertain high-value patterns.

### DEEP

Purpose: support consequential or code-level transfer.

Default expectations:

- source/version matrix;
- end-to-end capability trace for decision-critical mechanisms;
- destination architecture/constraint mapping;
- support and contradiction search for top claims;
- multi-source family synthesis when multiple sources exist;
- interaction/dependency analysis among top patterns;
- implementation alternatives;
- structural validation of the pattern ledger;
- explicit completion check.

DEEP has no pattern quota. Stop at decision saturation.

## 3. Verdict proof burdens

### CANDIDATE

Use when:

- source-derived pattern is useful;
- destination is absent, or target-side evidence is insufficient;
- no claim of target fit should be made yet.

Required:

- at least one source evidence item;
- mechanism hypothesis;
- transfer conditions;
- what destination evidence is missing.

### ADOPT

Required:

- destination exists;
- destination problem is evidenced;
- existing equivalent capability is checked;
- source behavior or implementation supporting the mechanism is directly evidenced;
- source evidence strength >= 0.65;
- destination evidence strength >= 0.65;
- implementation feasibility >= 0.60;
- strategic fit is not materially negative;
- legal/IP and security/privacy gates are `clear` or `not_required`;
- implementation path, success metric, rollback, and kill criteria are present;
- no unresolved critical contradiction.

For high-irreversibility architectural changes, prefer a spike/staged rollout before direct `ADOPT` unless destination architecture fit is unusually well established.

### EXPERIMENT

Required:

- destination exists;
- destination problem is evidenced;
- expected upside is material enough to justify testing;
- legal/IP and security/privacy gates are not blocking;
- uncertainty is resolvable through a reversible test, prototype, spike, shadow mode, benchmark, usability study, or staged rollout;
- falsifiable experiment/spike spec exists.

### BACKLOG

Use when fit is plausible but current timing, prerequisites, opportunity cost, or complexity make action unattractive.

Required:

- explicit reason for deferral;
- dependency or trigger that would justify reopening.

### REJECT

Use when:

- destination problem is absent;
- equivalent capability already solves it well enough;
- source mechanism is weak or unsupported;
- pattern imports disproportionate complexity;
- business-model/architecture mismatch is fundamental;
- opportunity cost dominates;
- pattern would reduce differentiation or create a harmful tradeoff.

A well-supported `REJECT` is a first-class teardown result.

### REVIEW_REQUIRED

Use when a mandatory constraint prevents a clean action:

- license/IP/provenance uncertainty;
- security/privacy blocker;
- permission/access limitation;
- other domain-specific gate outside the teardown's authority.

State exactly what review/evidence is required. Do not replace qualified legal/security review with the teardown skill.

## 4. Evidence quality thresholds

Suggested interpretation only:

- `0.90-1.00` - direct, specific, reproducible evidence with no material contradiction.
- `0.70-0.89` - strong evidence with limited inference/version uncertainty.
- `0.50-0.69` - plausible but materially incomplete or inferred.
- `<0.50` - weak support; do not present as established fact.

Use `UNKNOWN` when evidence is absent rather than assigning a pseudo-precise low confidence.

## 5. Stop rules

Stop inspecting when all are true:

- top pattern ordering is stable;
- no unresolved mandatory blocker remains inside teardown scope;
- new evidence is not changing mechanism, destination fit, or implementation path;
- additional sources are duplicating existing evidence groups;
- remaining unknowns are unlikely to change a verdict.

Continue only when another inspection can plausibly change:

- a top verdict;
- a mandatory gate;
- a critical implementation assumption;
- the pattern family chosen for the destination;
- the test required to resolve uncertainty.

## 6. Escalation rules

Escalate rather than absorb:

- legal/IP uncertainty that needs legal interpretation -> qualified review / AI Council gate;
- security/privacy acceptance -> security/privacy specialist or AI Council gate;
- repo-wide sequencing/resource allocation -> `repo-to-roadmap`;
- portfolio-level product priority -> `product-operator` or AI Council;
- broad external evidence dispute -> `evidence-researcher`.
