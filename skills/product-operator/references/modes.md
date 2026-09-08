# Operating modes

Modes control evidence breadth and output depth. They do not change source authority.

## PULSE
Use for a fast "what next?" checkpoint.

Minimum evidence:
- explicit/canonical current goal;
- repo metadata + recent relevant state;
- active roadmap/release work when available;
- known blockers and one material unknown.

Prefer a prior snapshot as a retrieval index. Return state headline, readiness, blockers/VERIFY NOW, NOW, and one key unknown. Do not pretend PULSE is a complete release audit.

## STANDARD
Default mode. Build a bounded Product State Ledger around the current goal and active work. Reconcile planning,
implementation, verification, shipping, and decision-relevant outcome evidence. Rank and sequence
`VERIFY NOW / NOW / NEXT / LATER / STOP`.

## DEEP
Use for comprehensive, finish-the-product, client-ready, production-ready, or explicit exhaustive analysis.
Expand across all material product surfaces and critical dependencies. Cover all material release/customer trust
surfaces, but do not scan irrelevant files or archived backlog for coverage theater.

A DEEP run may delegate to specialist skills; Product Operator remains the synthesis/sequencing layer.

## DELTA
Use only with a real previous Product Operator snapshot/baseline. Preserve scope when possible and report:
- stage transitions;
- new/resolved evidence/drift issues;
- new/closed blockers;
- priorities entering/leaving VERIFY NOW/NOW/NEXT;
- items completed, regressed, stalled, superseded, or removed;
- priority thrash when state did not materially change.

A prior snapshot is not current evidence. Revalidate material current claims.

## RELEASE
Focus on a named release or ship horizon. Separate:
- release scope/intent;
- implementation complete;
- verification complete;
- release/deploy evidence;
- operational/customer readiness supplied by specialist evidence when needed;
- post-release measurement only when decision-relevant.

A release plan in Notion is not release evidence. A merged PR is not deployment evidence.
