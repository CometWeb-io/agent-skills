# Operating modes

Modes control evidence breadth, not permission to produce a wall of text. Source authority never changes by mode.

## PULSE
Use for a fast "what next?" checkpoint. Return a state headline, readiness, the most material BLOCKER/VERIFY NOW/DECISION NOW, up to 3 NOW actions, and one material unknown if needed.

## STANDARD
Default mode. Build a bounded Product State Ledger around the current goal and active work. Reconcile planning, implementation, verification, shipping, and decision-relevant outcome evidence. Sequence `BLOCKER / VERIFY NOW / DECISION NOW / NOW / NEXT / LATER / STOP`.

## DEEP
Use for comprehensive, finish-the-product, client-ready, production-ready, or explicit exhaustive analysis. Expand evidence coverage across material surfaces and dependencies, but keep the Human brief bounded; depth belongs in the machine sidecar and specialist handoffs.

## DELTA
Use only with a real previous Product Operator snapshot/baseline. Report only material stage, blocker, unresolved-decision, and priority changes. A prior snapshot is not current evidence.

## RELEASE
Focus on a named release or ship horizon. Separate release scope/intent, implementation, verification, deploy evidence, operational/customer readiness, unresolved release decisions, and post-release outcome only when decision-relevant. Delegate exhaustive readiness to `release-readiness` when needed.

## Operating contract

Resolve from available context before asking the user:

```text
TARGET:          <product / repo(s) / workspace>
MODE:            PULSE | STANDARD | DEEP | DELTA | RELEASE
GOAL:            <current product/business objective or UNKNOWN>
HORIZON:         <this week / sprint / release / quarter / user-defined>
GITHUB:          <repo(s) or unavailable>
NOTION:          <page/database/data source(s) or unavailable>
PRODUCT CONTEXT: <canonical source or unavailable>
OUTCOME DATA:    <analytics/customer/revenue/support or unavailable/not-required>
PRIOR SNAPSHOT:  <snapshot or unavailable>
MUTATIONS:       read-only
AS OF:           <ISO timestamp with timezone>
```

Defaults: `STANDARD` for ordinary "what next?" work; `DEEP` for comprehensive/finish/client-ready/production-ready
requests; `RELEASE` for a named release or readiness horizon; `DELTA` only when a real previous snapshot/baseline
exists; `PULSE` for a fast checkpoint.

If a source is unavailable, continue with reduced coverage when the remaining evidence can still support a
useful result. Do not fabricate missing state. Do not ask for information that a connected source can resolve.
