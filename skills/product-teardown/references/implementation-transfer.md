# Implementation transfer playbook

## Table of contents

1. Transfer modes
2. Transfer packet
3. Implementation options
4. Architecture and operations
5. Experiment/spike design
6. Rollout and rollback
7. Reuse/IP discipline

## 1. Transfer modes

Classify how the destination should use the source lesson:

- `INSPIRE` - adopt the principle/problem framing, design independently.
- `REIMPLEMENT` - implement an equivalent mechanism in destination-native code/architecture.
- `INTEGRATE` - use a third-party/open component or service as a dependency.
- `REUSE_CODE` - reuse source code under verified license/provenance obligations.
- `REUSE_ASSET` - reuse copy/design/assets only with explicit permission/license; treat as a separate IP/trademark/trade-dress concern.

Default to `INSPIRE` or `REIMPLEMENT` when the user needs the mechanism rather than literal source reuse.

## 2. Transfer packet

For each top pattern, produce:

```text
Pattern ID
Destination problem evidence
Existing equivalent capability
Chosen transfer mode
Target surfaces/modules
Required data/contracts/permissions
Prerequisites
Implementation option(s)
Migration/rollout needs
Observability/support needs
Effort band + uncertainty
Success metric + baseline
Guardrails
Rollback/kill criteria
Open decisions
```

Do not invent file paths, baselines, or metrics.

## 3. Implementation options

When source implementation is unknown or destination architecture allows several valid approaches, give 1-3 destination-native options.

For each option state:

- implementation shape;
- why it fits;
- main tradeoff;
- dependency/operational burden;
- what evidence would choose between options.

Do not pretend one option is "how the source does it" unless code/runtime evidence proves that.

## 4. Architecture and operations

For structural patterns, include only decision-relevant implications:

- boundary ownership;
- data model/contracts;
- auth/permission implications;
- async/background behavior;
- failure/retry/idempotency needs;
- observability and support surface;
- migration/backfill/compatibility;
- feature flag/staged rollout when appropriate;
- test strategy for the changed boundary.

Avoid transplanting source architecture optimized for another scale, team topology, language, or deployment model.

## 5. Experiment/spike design

Select validation method by uncertainty:

### Behavioral uncertainty

Use prototype, usability test, staged rollout, or A/B test when measurement conditions support it.

### Technical feasibility uncertainty

Use technical spike, benchmark, shadow mode, or compatibility proof.

### Operational uncertainty

Use limited-scope rollout with observability, incident/support guardrails, and rollback.

### Causal/value uncertainty

Use a product experiment with a primary metric, guardrails, baseline, and decision rule.

Every `EXPERIMENT` should define:

```text
Hypothesis
Test type
Primary metric
Guardrail
Baseline
Success rule
Timebox/sample condition
Kill criteria
What result changes the verdict
```

## 6. Rollout and rollback

For non-trivial adoption, specify:

- feature flag or containment boundary when possible;
- migration path;
- compatibility period if needed;
- observation window;
- rollback trigger;
- data cleanup/recovery implications.

Reversibility is part of the transfer decision, not an afterthought.

## 7. Reuse/IP discipline

Before `REUSE_CODE`:

- inspect repository license;
- inspect relevant file notices/headers;
- note attribution/copy-left/source-availability obligations as evidenced;
- identify dependency licenses when copied code embeds or vendors dependencies;
- route unresolved interpretation to review.

Before `REUSE_ASSET`:

- verify explicit rights/permission;
- separate copyright, trademark, trade dress, and contract/TOS concerns;
- prefer independent design when rights are unclear.

Public visibility is not permission to copy.
