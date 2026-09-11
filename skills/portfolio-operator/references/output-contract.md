# Output contract

Separate the concise **Human brief** from the detailed **Machine sidecar**.

## Human brief

Default to the user's language.

For a standard 14-day plan:

- normally <=450 words;
- <=10 user-facing actions total;
- one line per action when possible;
- use domain tags such as `[CLIENT]`, `[PRODUCT]`, `[RESEARCH]` rather than duplicating priorities into separate reports.

Default order:

```text
Stan: <READY | PROVISIONAL | BLOCKED — one sentence>

MUST DO
- [DOMAIN] <action> — Done: <observable condition>

CAPACITY CONFLICTS
- <conflict + decision/constraint>

NOW
- [DOMAIN] <action> — Done: <observable condition>

DELEGATE
- <confirmed specialist/owner> — <narrow question>

DELEGATE CANDIDATE
- <possible owner/agent> — <what must be confirmed>

WAITING
- [DOMAIN] <why no capacity now / what unblocks it>

PAUSE / DROP
- [DOMAIN] <what stops receiving capacity and why>

NEXT
- [DOMAIN] <dependency-ordered follow-on>
```

Omit empty sections.

Do not print scores, every checked source, full ledger, tool narration, or connector-limit noise unless it changes the plan.

## Machine sidecar

Recommended `portfolio-report.json`:

```json
{
  "protocol_version": "1.0",
  "as_of": "2026-09-10T10:00:00+02:00",
  "horizon": "14d",
  "primary_goal": "...",
  "portfolio_scope": [],
  "constraints": [],
  "capacity": {"source": "unknown"},
  "coverage": {},
  "readiness": {"status": "PROVISIONAL", "reason": "..."},
  "portfolio_items": [],
  "must_do": [],
  "capacity_conflicts": [],
  "now": [],
  "delegate": [],
  "delegate_candidate": [],
  "waiting": [],
  "pause_drop": [],
  "next": [],
  "decision_now": [],
  "unknowns": []
}
```

### Validation invariants

- `capacity.source=unknown` -> numeric capacity hours must be absent;
- `must_do[]` and `now[]` require `done_when` and `evidence[]`;
- a future gate that does not block the current goal cannot appear in `must_do[]`;
- do not fabricate missing external commitments or deadlines;
- `must_do[]`/`now[]` that need specialist depth stay outcome-level with `scope_level=portfolio` and require `portfolio_outcome`; the renderer uses `portfolio_outcome` instead of deeper internal `action` text;
- any user-facing exact date, deadline, numeric target, currency amount, count, or time KPI requires `evidence_ref` or `user_defined=true`;
- `delegate[]` must name a narrow question/return contract and a real executor; known specialist skills are valid, while external people/agents/systems require `delegate_evidence_ref` or explicit user definition;
- hypothetical executors belong in `delegate_candidate[]` or `pause_drop[]`, not `delegate[]`.
