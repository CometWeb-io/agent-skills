# Output Contracts v2

## Contents

1. Global output rules
2. Queue triage
3. Case brief
4. Incident brief
5. Feedback/problem cluster
6. Retention watch
7. Commitment watch
8. Handoff watch
9. GitHub proposal
10. Account 360
11. Ops brief
12. Closure verification
13. Machine-readable record
14. Evidence notation

## 1. Global output rules

Adapt to the requested format, but keep decision-critical fields visible.

For current-state outputs include:

```text
as_of
coverage_status: COMPLETE | PARTIAL | SAMPLED | UNKNOWN
sources_checked
critical_sources_missing
```

When relevant, always keep separate:

```text
customer_impact_severity
operational_priority
evidence_grade
account_escalation
retention_risk
sla/deadline state
```

Do not substitute one composite "health" score unless the user's real system defines it.

Clearly distinguish:

- `Performed` — external mutation actually completed.
- `Proposed / Needs approval` — draft only.
- `Blocked` — cannot safely/correctly act yet.

## 2. Queue triage

```markdown
# Customer Ops Queue — <as_of>

**Coverage:** COMPLETE / PARTIAL / SAMPLED
**Sources:** ...
**Critical gaps:** ...

## Now
| Rank | Case | Account | Type | Evidence | Priority | Escalation | Retention | SLA/deadline | Owner | Next action |
|---|---|---|---|---|---|---|---|---|---|---|

## Incident / specialist gates
- <case> — <why gated> — <owner/next action>

## Overdue commitments
- ...

## Stalled / ownerless handoffs
- ...

## Emerging clusters
- <problem> — <account_count> accounts / <case_count> cases — <window> — <evidence grade>

## Data quality / contradictions
- ...

## Needs approval
- <exact mutation>
```

Prefer one-line reasons. Deep investigation belongs in linked case briefs.

## 3. Case brief

```markdown
# Case: <id / short symptom>

**As of:**
**Coverage:**
**State:**
**Account:**
**Type:**
**Evidence grade:**
**Operational priority:**
**Account escalation:**
**Retention risk:**
**Native SLA/deadline:**
**Owner:**

## Customer-visible problem
**Symptom:** ...
**Desired outcome / expected:** ...
**Confirmed impact:** ...

## Evidence
### Confirmed / observed
- [source + timestamp] ...

### Reported
- ...

### Unknowns / contradictions
- ...

### Hypotheses
- <hypothesis> — <next discriminating test>

## Linked work
- Cluster: ...
- Incident: ...
- GitHub issue/PR/release: ...
- Handoff: ...

## Commitments
- <promise/checkpoint> — <owner> — <due/status>

## Next action
**Owner:** ...
**Action:** ...
**Checkpoint/deadline:** ...

## Customer communication
**Status:** not requested / draft / sent
<message or reference if relevant>

## Verification / closure
**Verification criterion:** ...
**Current:** RESOLVED / VERIFIED / CLOSED / still open
```

## 4. Incident brief

```markdown
# Incident <id> — <customer symptom>

**As of:**
**State:** DETECTED / INVESTIGATING / IDENTIFIED / MITIGATING / MONITORING / RECOVERED / VERIFIED / CLOSED
**Customer-impact severity:** SEV1 / SEV2 / SEV3 / NOT_INCIDENT
**Specialist gates:** security / privacy / legal / reputation / none
**Commander:**
**Started / detected:**
**Known affected scope:**

## Customer impact
...

## Confirmed facts
- ...

## Unknowns
- ...

## Hypotheses
| Hypothesis | For | Against | Next test |
|---|---|---|---|

## Current mitigation / workaround
- ...

## Customer exposure
| Account/ref | Exposure | Comms | Recovery verification | Follow-up |
|---|---|---|---|---|

## Timeline
| Time | Event | Source |
|---|---|---|

## Canonical customer communication
- latest confirmed message/state
- next checkpoint or no confirmed ETA

## Engineering / prevention
- issue / PR / release / action items

## Verification
- criteria + evidence
```

Do not publish the exposure table to customers unless the user explicitly needs that
content and it is appropriate.

## 5. Feedback / problem cluster

```markdown
# Problem Cluster: <underlying problem>

**State:** CANDIDATE / CONFIRMED / ACTIONED / WATCHING / MONITORING / RESOLVED
**Window:**
**Accounts:** X
**Cases:** Y
**Segments:**
**Evidence grade:**

## Underlying job/problem
...

## Evidence
- <representative source/verbatim if permitted>

## Requested solutions
- ...

## What the evidence supports
- ...

## Support load
- <touches/cases/manual work if available>

## Counterexamples / contradictions
- ...

## Workaround / engineering dependency
- ...

## Product evidence handoff
- target skill/team + exact decision required

## Missing evidence
- ...
```

Never use case count as independent customer count.

## 6. Retention watch

Avoid a pseudo-precise numeric probability table.

```markdown
# Retention Watch — <as_of>

| Account | Risk | Evidence | Exit intent | Time pressure | Strongest drivers | Missing evidence | Owner | Next action |
|---|---|---|---|---|---|---|---|---|

**Method:** operational heuristic, not churn probability unless an actual validated model is cited.
```

For HIGH/CRITICAL accounts, include a short evidence path and linked product/incident/
billing dependency.

## 7. Commitment watch

```markdown
# Customer Commitments — <as_of>

## Overdue
| Commitment | Case/account | Owner | Due | Source | Next action |
|---|---|---|---|---|---|

## Due soon
| Commitment | Case/account | Owner | Checkpoint | Dependency |
|---|---|---|---|---|

## Ownerless / conflicted
- ...

## Fulfilled since last review
- ...
```

Do not mark a commitment fulfilled unless the promised customer-facing/internal action can
be evidenced.

## 8. Handoff watch

```markdown
# Internal Handoffs — <as_of>

## Needs ownership
| Handoff | Case | From → To | Requested | State | Blocker | Next action |
|---|---|---|---|---|---|---|

## Blocked / overdue checkpoint
- ...

## Repeated reroutes
- ...

## Completed but customer not verified
- ...
```

Do not equate `DONE` handoff with customer closure.

## 9. GitHub proposal

Before issue body, show:

```text
Repository conventions: checked / partial / unavailable
Dedupe search: done / unavailable
Closest related issue: <id or none>
Engineering readiness: PASS / WARN / BLOCK
Privacy preflight: clear / findings-redacted / blocked / not-run
Write status: draft / created / updated
```

Then use `assets/github-issue-template.md` or the repository's native template/form.

After creation/update:

```text
Performed: <action>
GitHub: <issue id/url>
Read-back verified: yes/no
Linked customer cases/cluster: ...
```

## 10. Account 360

```markdown
# Account 360: <account> — <as_of>

**Coverage:** ...
**Operational question:** ...

## Current operational status
- risk / owner / next action

## Commercial context
- CRM/billing/contract facts only, with timestamp

## Open cases
- ...

## Incident exposure
- ...

## Usage / product health evidence
- ...

## Retention-risk evidence
- ...

## GitHub / engineering dependencies
- ...

## Commitments
- ...

## Handoffs
- ...

## Recent customer feedback / trust signals
- ...

## Recommended operational action
- ...

## Conflicts / stale / missing sources
- ...
```

## 11. Daily/weekly ops brief

```markdown
# Customer Ops Brief — <window> — as of <time>

**Coverage:** COMPLETE / PARTIAL / SAMPLED

## Now
- incidents / specialist gates
- P0/P1 cases
- breached/imminent provider-native SLA/deadlines
- explicit exit intent
- overdue commitments
- blocked/ownerless critical handoffs

## Next
- unresolved clusters
- engineering dependencies
- upcoming customer checkpoints/follow-up

## Watch
- emerging signals below action threshold

## Closed loop
- verified fixes
- customer follow-ups completed
- regressions/reopens

## Quality
- requester wait / reopens / verified-fix rate / handoff delay / promise breaches

## Metrics
- only with clear definitions/window/denominator

## Data quality
- unowned cases
- stale/conflicted records
- incomplete pagination/scope
- broken links / missing source data

## Needs approval
- exact writes/decisions
```

## 12. Closure verification

```markdown
# Closure Verification — <case>

**As of:**
**Internal remedy state:**
**Release/deployment verified:** yes/no/not-applicable/unknown
**Original symptom re-tested:** yes/no
**Verification method/evidence:**
**Customer follow-up:** pending/draft/sent/confirmed/waived
**Open commitments:**
**Open handoffs:**
**Reopen/regression evidence:**
**Closure gate:** PASS / WARN / BLOCK
**Resulting case state:** RESOLVED / VERIFIED / CLOSED / OPEN
**Remaining work:**
```

## 13. Machine-readable record

When the user is integrating with another agent/system, provide a compact JSON-like record
in addition to prose if useful:

```json
{
  "as_of": "ISO-8601",
  "coverage_status": "COMPLETE|PARTIAL|SAMPLED|UNKNOWN",
  "case_id": "...",
  "state": "...",
  "customer_symptom": "...",
  "evidence_grade": "HIGH|MEDIUM|LOW|CONFLICTED|UNKNOWN",
  "operational_priority": "P0|P1|P2|P3",
  "account_escalation": "STANDARD|EXPEDITED|EXECUTIVE",
  "retention_risk": "LOW|MEDIUM|HIGH|CRITICAL|UNKNOWN",
  "owner_class": "...",
  "next_action": "...",
  "next_checkpoint_at": null,
  "linked_ids": {},
  "open_commitments": [],
  "open_handoffs": [],
  "unknowns": [],
  "actions_performed": [],
  "actions_proposed": []
}
```

Do not output fields as facts when not sourced; use `null`/`UNKNOWN`.

## 14. Evidence notation

For material facts, prefer:

```text
[source system | object id | timestamp]
```

If the host supports native citations, cite the underlying source rather than inventing a
custom citation.
