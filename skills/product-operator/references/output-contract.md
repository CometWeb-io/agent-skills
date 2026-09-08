# Output contract

Default to a compact operating brief in the user's language.

## Human report

### Header

```text
As Of: <timestamp + timezone>
Mode: <PULSE|STANDARD|DEEP|DELTA|RELEASE>
Target: <product/repo>
Goal: <goal or UNKNOWN>
Horizon: <horizon>
Readiness: READY | PROVISIONAL | BLOCKED
Coverage: GitHub <verified|partial|unavailable> | Notion <verified|partial|unavailable> | Product Context <verified|partial|unavailable> | Outcome Data <verified|partial|unavailable|not-required>
```

### Product state
One short paragraph separating what is planned, built, verified, shipped, and producing decision-relevant
outcome evidence.

### What changed
For DELTA/repeated run only. Report stage/issue/blocker/priority changes that alter action, not raw diffs.

### Blocking conditions
Only confirmed decision-relevant blockers/gates/dependency cycles.

### VERIFY NOW
Maximum 3. Use for high-value uncertainty/current-evidence gaps that must be resolved before confident work.

### NOW
Normally 1-3 actions. Each includes:

```text
Action
Why now
Evidence
Dependency / unlock
Done when
Confidence
```

### NEXT
Maximum 5, in dependency order.

### LATER
Only items worth preserving but intentionally inactive.

### WATCH
External dependency/metric/trigger to monitor. Omit when empty.

### STOP / DO NOT DO
Only evidence-backed duplicate/superseded/premature work. Omit when empty.

### Drift and contradictions
Show only material cross-source/evidence drift. Include source/timestamp when available.

### Delegations
Name specialist + exact question only when its answer can change priority.

### Unknowns
At most 3 material gaps; state what could change if resolved.

### Bottom line
One sentence: **what should the team do next?**

## Machine-readable `operator-report.json`

Recommended shape:

```json
{
  "protocol_version": "2.0",
  "as_of": "2026-08-25T22:03:12+02:00",
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
  "readiness": {"status": "READY", "reasons": []},
  "decision": "Verify release-critical billing before adding scope.",
  "blockers": [],
  "verify_now": [],
  "now": [
    {
      "id": "A-001",
      "action": "...",
      "why_now": "...",
      "done_when": "...",
      "confidence": 0.91,
      "depends_on": [],
      "evidence": [
        {
          "source": "github",
          "locator": "path/PR/commit",
          "claim": "...",
          "claim_type": "implementation",
          "freshness_status": "CURRENT"
        }
      ]
    }
  ],
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

For `VERIFY NOW`, `NOW`, and `NEXT`, evidence + measurable `done_when` are mandatory. Never output an owner,
deadline, capacity, customer requirement, or metric unless it is supplied by an authoritative source/user.

When filesystem support exists, create `operator-snapshot.json` separately via the kernel rather than embedding
snapshot hash logic manually in prose.
