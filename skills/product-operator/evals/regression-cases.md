# Product Operator regression cases

Expected behavior matters more than exact wording.

## State/evidence truth

1. **Notion Done, no code proof** -> `PLAN_AHEAD_OF_CODE`; never call implemented.
2. **Code exists, verification unknown** -> `CODE_AHEAD_OF_VERIFICATION`; verification can outrank new scope.
3. **Verified, no deploy proof** -> `VERIFIED_NOT_SHIPPED`; never call live.
4. **Shipped, outcome unknown, outcome is decision-relevant** -> `SHIP_WITHOUT_OUTCOME_EVIDENCE`.
5. **Shipped, outcome unknown, outcome not decision-relevant** -> do not force telemetry work.
6. **Implementation claimed only by Notion** -> wrong-authority evidence; GitHub/repo proof required.
7. **Required-current evidence stale/unknown** -> not admissible for READY current claim.
8. **Static suspicious UI source, no behavior proof** -> do not claim user-facing defect; delegate verification.

## Source coverage

9. **Missing Notion** -> continue with planning claims narrowed; coverage/readiness degrade, no fabricated backlog state.
10. **Missing canonical product context** -> goal/ICP is INFERRED/UNKNOWN; use product-marketing if priority depends on it.
11. **Prior snapshot exists** -> use as retrieval baseline only; revalidate current material claims.
12. **Old snapshot conflicts with GitHub current state** -> GitHub wins for implementation; snapshot is historical only.

## Prioritization/sequencing

13. **High-impact low-evidence blocker candidate** -> `VERIFY NOW`, not confirmed blocker.
14. **Low-materiality polish** -> LATER even if cheap.
15. **Decision-relevant instrumentation with high learning value** -> can rise to VERIFY NOW/NOW/NEXT depending on evidence and goal.
16. **Five attractive NOW items** -> human brief remains bounded; validator rejects excess non-critical items.
17. **B depends on A** -> sequence A before B even if B score is higher.
18. **A <-> B dependency cycle** -> surface planning problem; never choose arbitrary order.
19. **Missing external dependency** -> surface as blocker/watch, not silently ignore.
20. **STOP candidate** -> requires supersession/dominance/prematurity evidence, never low score alone.

## Living loop

21. **Identical state and same candidate data across runs** -> same deterministic rank/order.
22. **Identical state but action moves NOW -> NEXT** -> `PRIORITY_THRASH` unless judgment change is explicitly justified.
23. **Implemented UNKNOWN -> PRESENT** -> delta contains stage transition and re-ranks dependent work.
24. **Verification PASS -> FAIL** -> delta surfaces regression; release-dependent work must respond.
25. **Goal materially changes** -> old priorities can be superseded; do not treat priority movement as thrash if state-driving goal changed.

## Specialist boundaries

26. **Broad repo-wide roadmap request** -> delegate/consume `repo-to-roadmap`; Product Operator sequences result.
27. **Exhaustive production readiness** -> delegate/consume `release-readiness`; Product Operator does not recreate every readiness domain.
28. **Support/incidents/churn signal mining** -> `customer-ops` owns deep analysis.
29. **External primary-source contradiction research** -> `evidence-researcher` owns deep evidence work.
30. **Competitor surveillance** -> `competitive-intelligence` owns continuous profiling.
31. **Design partner account discovery** -> `design-partner-finder` owns prospect discovery/qualification.
32. **High-lock-in strategic fork** -> Product Operator frames dependencies, then AI Council decides.
