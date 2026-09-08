# Handoff Contracts

## Product Operator handoff

`repo-to-roadmap` produces the baseline or delta truth. A downstream `product-operator` should receive a compact machine-readable handoff, not reconstruct priorities from prose.

Include:

- snapshot hash and assessment ref/date,
- target-state profile and requirement IDs,
- active roadmap item IDs and lanes,
- hard dependencies,
- acceptance criteria and verification method,
- claim refs and evidence confidence,
- unresolved `VERIFY_NOW` / `VALIDATE` items,
- watch dependencies and revalidation triggers,
- deferred/parked items with reason,
- explicit note that lane/score is not authorization to implement.

The operator owns cycle selection and execution sequencing under current capacity. It must not silently rewrite the baseline evidence ledger.

## AI Council handoff

Use AI Council for a material decision where evidence does not uniquely determine the route, such as build-vs-buy, platform migration, scope cut, risk acceptance, or portfolio conflict.

Send:

- decision question,
- options,
- relevant claim IDs and admissible evidence,
- target requirements affected,
- constraints,
- reversibility/lock-in,
- cost of delay if known,
- unresolved assumptions.

Import the Council result as a `decision_ref`. Do not relabel Council judgment as implementation evidence.

## Specialist handoff

For security, privacy, web-app QA, SEO/GEO/AEO, analytics, customer research, pricing, CRO, or other specialist domains:

1. send the narrow evidence-backed question,
2. preserve the specialist's finding IDs/source refs,
3. separate facts from recommendations,
4. normalize only material findings into claims/capabilities/items,
5. retain specialist severity/gate semantics where compatible,
6. do not duplicate the specialist audit inside this skill.
