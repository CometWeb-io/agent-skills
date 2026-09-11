# Output contract

Separate the **Human brief** from the **Machine sidecar**. The operator may do deep reconciliation internally; the user should still receive the smallest decision-ready answer.

## Human brief

Default to the user's language. Optimize for scan time, not completeness.

### Word budgets

- `PULSE`: usually <= **180 words**.
- `STANDARD` / `DELTA`: usually <= **350 words**.
- `DEEP` / `RELEASE`: usually <= **500 words**.

Exceed only when the user explicitly asks for detail or compression would hide a material risk.

### Default shape

```text
Stan: <one sentence; include readiness/horizon only when useful>

BLOCKER
- <max 3 confirmed current-goal gates; omit if empty>

VERIFY NOW
- <max 3 unknowns/tests that can change the path>

DECISION NOW
- <max 3 unresolved material choices that Product Operator must not decide>

NOW
- <1-3 concrete actions>

NEXT
- <max 3 user-facing follow-ons in dependency order>

STOP
- <max 3 evidence-backed things not to spend attention on>
```

Omit empty sections. `LATER`, `WATCH`, drift, and unknowns appear only when they materially change the user's next move.


### BLOCKER contract

For protocol 2.2 machine sidecars, every `blockers[]` item must include:

```text
id
condition
blocks_current_goal: true
blocked_item: <current goal or critical-path action that cannot proceed>
why_blocking
evidence[]
```

If `blocks_current_goal=false`, the item is not a `BLOCKER`; place a future gate in `LATER/WATCH` or an unproven current-path risk in `VERIFY NOW`. Do not call something a blocker while also saying it "does not block" the current action.

### Human item compression

For an action, prefer one line:

`**Action** — <what to do>. Done: <observable condition>.`

Add one short `Why` sentence only if the sequencing is non-obvious. Do not print evidence objects, confidence scores, source maps, or dependency metadata unless they are the point of the question.

For `DECISION NOW`, prefer:

`**<question>** — options: <A> / <B>. Handoff: <specialist>. Done: <binding decision recorded>.`

Do not answer the unresolved choice inside Product Operator.

### Noise suppression

Do not print:
- full coverage matrices by default;
- full state ledgers;
- raw `operator-report.json`;
- source registries or every checked source;
- tool-call narration;
- non-impacting connector/rate/tool-limit warnings;
- repeated summaries of the same fact.

A tool-limit or connector gap is user-facing only when it is **decision-relevant**: it changes readiness, blocks a critical claim, or could alter BLOCKER / VERIFY NOW / DECISION NOW / NOW.

If outcome data such as CRM is unavailable, state the gap once and continue with bounded sequencing when defensible. Never fabricate the metric.

## Machine sidecar

For `STANDARD`, `DEEP`, `DELTA`, and `RELEASE`, preserve full evidence and state in `operator-report.json` when filesystem/execution support exists. The sidecar can be detailed even when the Human brief is short.

Recommended shape:

```json
{
  "protocol_version": "2.2",
  "as_of": "2026-09-07T17:24:00+02:00",
  "mode": "STANDARD",
  "target": "owner/repo",
  "goal": "Ship the paid client-ready release",
  "horizon": "next release",
  "mutations": "read-only",
  "coverage": {
    "github": "verified",
    "notion": "verified",
    "product_context": "verified",
    "outcome_data": "partial"
  },
  "readiness": {"status": "PROVISIONAL", "reasons": []},
  "decision": "Resolve the material offer decision, then execute the verified critical path.",
  "blockers": [],
  "verify_now": [],
  "decision_now": [
    {
      "id": "D-A1",
      "question": "Should the first pilot cohort be free or paid?",
      "decision_domain": "pricing",
      "why_now": "The answer changes outbound and offer copy.",
      "options": ["free bounded pilot", "paid pilot"],
      "delegated_to": "ai-council + pricing/offers",
      "done_when": "One option is explicitly decided and becomes binding.",
      "evidence": []
    }
  ],
  "now": [],
  "next": [],
  "later": [],
  "watch": [],
  "stop": [],
  "drift": [],
  "delegations": [],
  "unknowns": [],
  "state_items": []
}
```

For `VERIFY NOW`, `NOW`, and `NEXT`, evidence + measurable `done_when` are mandatory in the sidecar. For `DECISION NOW`, require the question, decision domain, at least two unresolved options, specialist handoff, evidence, and `done_when`; do not include a selected option/recommendation/verdict.

Never invent owner, deadline, capacity, customer requirement, or metric unless supplied by an authoritative source/user.

Create `operator-snapshot.json` separately via the kernel when useful rather than embedding snapshot hash logic in prose.
