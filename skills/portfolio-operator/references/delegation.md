# Delegation map

Portfolio Operator owns cross-domain allocation, not specialist depth.

| Need | Delegate to | Portfolio Operator consumes |
| --- | --- | --- |
| Deep next-actions/state inside one product/repo | Product Operator | current critical path, blockers, verify/decision/now/next/stop |
| Pinned release readiness / GO-NO_GO | Release Readiness | release verdict, hard gates, required controls |
| Customer incident/support/account risk | Customer Ops | severity, commitments, customer-visible state, next operational action |
| Material claim verification/due diligence | Evidence Researcher | accepted claims, contradictions, gaps |
| Consequential strategic/portfolio trade-off | AI Council | decision/verdict + conditions |
| Execute a chain of multiple specialist skills | Skill Orchestrator | final specialist/control-plane result |
| Whole-repo baseline/roadmap | Repo to Roadmap | verified project truth + dependency-aware roadmap |
| Design partners | Design Partner Finder | qualified candidates/readiness |
| Broad sales prospect list | Prospecting | qualified account list |
| Cold outreach copy | Cold Email | messages/sequences |
| Pricing/packaging | Pricing | decision-relevant pricing recommendation/evidence |
| Marketing plan/channel execution | relevant marketing specialist | domain output only |

## Handoff shape

Keep handoffs narrow:

```text
Goal:
Why this specialist is needed:
Current evidence:
Question to answer:
What would change in the portfolio plan:
Return contract:
```

Do not send the entire portfolio ledger unless the specialist truly needs it.

## Re-entry

After a specialist result materially changes commitments, risk, timing, or expected outcome, rerun Portfolio Operator allocation. If it does not change allocation, keep the result as supporting evidence and do not churn priorities.

If a named specialist is unavailable, expose the handoff and the resulting uncertainty. Do not impersonate the missing specialist.

## Specialist depth ceiling

Portfolio Operator owns **allocation**, not the specialist's internal work breakdown. A portfolio-facing item may contain only:

- the portfolio outcome (`portfolio_outcome` when specialist depth exists);
- why it deserves capacity now;
- an observable portfolio-level `done_when`;
- the specialist handoff when deeper analysis is needed.

Do not copy a Product Operator backlog, release checklist, client implementation checklist, research methodology, or technical component list into `MUST DO`/`NOW`.

## Delegation reality gate

`DELEGATE` means an executor exists. Treat these as valid:

- a known specialist skill/control plane in the delegation map;
- a person/agent/system explicitly named by the user;
- a person/agent/system supported by `delegate_evidence_ref`.

If the executor is merely desirable, hypothetical, unavailable, or not confirmed, emit `DELEGATE CANDIDATE` or pause the work. Never assume an agent creates additional capacity merely because delegation would be convenient.

When `portfolio_outcome` is present, render that field to the user and keep deeper `action` text machine-side only.
