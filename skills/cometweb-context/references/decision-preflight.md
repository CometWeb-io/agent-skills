# Decision preflight

Use this reference only when the requested context will feed a material decision.

## Trigger

Treat the request as material when it can change product direction, portfolio allocation, ICP, GTM, pricing,
packaging, launch timing, architecture/lock-in, a material public claim, or another hard-to-reverse commitment.

## Governance sources

Preferred current canonical sources in the GTM vault, when accessible:

1. `cometweb/strategia/First Principles.md` — decision decomposition doctrine.
2. `DECISIONS.md` — binding historical decisions and supersession.
3. `governance/decision-trace.md` — trace contract, if present.
4. `governance/first-principles-adoption.json` — adoption experiment only when reviewing the mechanism itself.

Do not copy doctrine into the envelope. Record only that it was loaded, its reference, and the constraint it
creates for the downstream skill.

## Downstream boundary

`cometweb-context` may say:

- `First Principles required: true`,
- `status: loaded|unavailable`,
- `constraint: use FP-6 or canonical fast path before material decision`.

It must not choose `GO | TEST | DEFER | NO-GO`, write an FP TRACE, or pretend that First Principles proves a
current product/business fact.
