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

In the human brief, `NOT_CREATED` means no sidecar was produced;
`NOT_VALIDATED` means a sidecar exists but complete validation did not succeed
or did not run. These are disclosure labels, not sidecar readiness values or
proof of validation. State the reason and next step.

`portfolio-report.json` includes this envelope (empty lanes may be omitted):

```json
{
  "protocol_version": "1.0",
  "as_of": "2026-09-10T10:00:00+02:00",
  "horizon": "14d",
  "primary_goal": "...",
  "portfolio_scope": ["project-a"],
  "constraints": [],
  "capacity": {"source": "unknown"},
  "coverage": {"calendar": "unavailable"},
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

- full `validate` requires protocol version 1.0 or 1.1, `as_of` with timezone,
  non-empty `horizon` and `primary_goal`, `portfolio_scope` identifiers, an explicit
  `capacity.source`, non-empty `coverage` source states, and a valid `readiness`;
- a goal explicitly `UNKNOWN` or an empty scope requires `BLOCKED` readiness;
- `PROVISIONAL` and `BLOCKED` readiness require an explicit reason;
- `capacity.source=unknown` -> numeric capacity hours must be absent;
- `capacity.source=relative-only` also prohibits numeric capacity hours;
- supplied capacity hours must be finite non-negative numbers; zero is allowed;
- `must_do[]` and `now[]` require non-empty text `done_when` and a non-empty
  `evidence[]`; each entry is a non-empty text reference or an object with
  non-empty text `source` and `locator`;
- a future gate that does not block the current goal cannot appear in `must_do[]`;
- do not fabricate missing external commitments or deadlines;
- `must_do[]`/`now[]` that need specialist depth stay outcome-level with `scope_level=portfolio` and require `portfolio_outcome`; the renderer uses `portfolio_outcome` instead of deeper internal `action` text;
- any user-facing exact date, deadline, numeric target, currency amount, count, or time KPI requires `evidence_ref` or `user_defined=true`;
- `delegate[]` must name a non-empty text executor, question and return contract; known specialist skills are valid, while external people/agents/systems require `delegate_evidence_ref` or explicit user definition;
- hypothetical executors belong in `delegate_candidate[]` or `pause_drop[]`, not `delegate[]`.

`valid=true` means these structural checks passed, not that sources, deadlines,
executor availability, freshness, user authorization, or the business conclusion
were independently verified. `render` does not validate a report. See
`references/validation-migration.md` for the legacy partial-input migration.
