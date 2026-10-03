# Audit report — billing area (http://localhost:3000/billing)

- Date: 2026-09-30
- Protocol: web-app-auditor 1.1
- Mode / depth: area / standard
- Persona: signed-in owner
- Viewports: 1280x800, 390x844
- Capability profile: hybrid
- Environment: local
- Mutation policy: safe-test-only
- Confidence: high
- Validator: passed
- Verdict: ship with fixes

## Verdict

Ship with fixes. The billing area works end to end, but the navigation badge reports 4 invoices while the table and footer show 3 (F-001), which leaves the owner with contradictory billing state. One cancel action was policy-blocked and is accounted for in coverage.

## Scope

```text
TARGET: http://localhost:3000/billing
MODE: area
DEPTH: standard
IN: /billing
OUT: /marketing
VIEWPORTS: 1280x800, 390x844
PERSONA: signed-in owner
CAPABILITY: hybrid
ENVIRONMENT: local
MUTATIONS: safe-test-only
STOP: all primary actions tested
```

Covered: /billing at both viewports.
Skipped/blocked: subscription cancel (policy-blocked under safe-test-only).
Sampling rule: one representative row action per invoice state; all primary actions tested.

## Counts

| blocker | major | minor | nit | needs-repro | recommendations |
|--------:|------:|------:|----:|------------:|----------------:|
| 0 | 1 | 0 | 0 | 0 | 1 |

## Findings

### F-001 — Invoice badge says 4 while the table contains 3 invoices

- Kind: defect
- Severity: major
- Confidence: high
- Where: /billing, 1280x800, owner
- Repro:
  1. Open /billing
  2. Compare the nav badge with the visible invoice rows
- Expected: the invoice count matches the represented invoice set.
- Expected basis: observed-consistency, arithmetic
- Actual: the badge shows 4 while the table and footer show 3.
- Evidence: E-001
- Impact: the owner sees contradictory billing state and cannot trust the navigation count.
- Root cause: unknown

### F-002 — Invoice table has no empty-state hint for new accounts

- Kind: recommendation
- Severity: n/a
- Confidence: medium
- Where: /billing, 390x844, owner
- Expected: a short hint explains when the first invoice appears.
- Expected basis: heuristic
- Actual: the table area is blank.
- Evidence: none (recommendation)
- Impact: new owners may think billing is broken.

## Evidence manifest

| Evidence | Type | Location | Supports | Redacted |
|---|---|---|---|---|
| E-001 | screenshot | F-001-badge-count.png | F-001 | yes |

## Coverage

```text
total in-scope: 12
tested: 9
sampled: 2
policy-blocked: 1
environment-blocked: 0
unreachable: 0
```

## Recommended next audit

Re-run billing after the count source is corrected.

```json
{
  "schemaVersion": "1.1",
  "target": "http://localhost:3000/billing",
  "mode": "area",
  "depth": "standard",
  "confidence": "high",
  "verdict": "ship_with_fixes",
  "validator": "passed",
  "capabilities": {
    "profile": "hybrid",
    "browser": true,
    "source": true,
    "screenshots": true,
    "console": true,
    "network": true,
    "filesystem": true,
    "codeExecution": true
  },
  "environment": {
    "kind": "local",
    "mutationPolicy": "safe-test-only"
  },
  "scope": {
    "in": [
      "/billing"
    ],
    "out": [
      "/marketing"
    ],
    "viewports": [
      "1280x800",
      "390x844"
    ],
    "persona": "signed-in owner",
    "covered": [
      "/billing"
    ],
    "skipped": []
  },
  "counts": {
    "blocker": 0,
    "major": 1,
    "minor": 0,
    "nit": 0,
    "needsRepro": 0,
    "recommendations": 1
  },
  "findings": [
    {
      "id": "F-001",
      "kind": "defect",
      "severity": "major",
      "confidence": "high",
      "title": "Invoice badge says 4 while the table contains 3 invoices",
      "where": {
        "route": "/billing",
        "viewport": "1280x800",
        "persona": "owner"
      },
      "repro": [
        "Open /billing",
        "Compare the nav badge with the visible invoice rows"
      ],
      "expected": "The invoice count should match the represented invoice set.",
      "expectedBasis": [
        "observed-consistency",
        "arithmetic"
      ],
      "actual": "The badge shows 4 while the table and footer show 3.",
      "evidence": [
        "E-001"
      ],
      "impact": "The owner sees contradictory billing state and cannot trust the navigation count.",
      "rootCause": "unknown"
    },
    {
      "id": "F-002",
      "kind": "recommendation",
      "severity": "n/a",
      "confidence": "medium",
      "title": "Invoice table has no empty-state hint for new accounts",
      "where": {
        "route": "/billing",
        "viewport": "390x844",
        "persona": "owner"
      },
      "repro": [
        "Open /billing on a new account"
      ],
      "expected": "A short hint explains when the first invoice appears.",
      "expectedBasis": [
        "heuristic"
      ],
      "actual": "The table area is blank.",
      "evidence": [],
      "impact": "New owners may think billing is broken.",
      "rootCause": "unknown"
    }
  ],
  "evidence": [
    {
      "id": "E-001",
      "type": "screenshot",
      "location": "F-001-badge-count.png",
      "supports": [
        "F-001"
      ],
      "redacted": "yes"
    }
  ],
  "coverage": {
    "totalInScope": 12,
    "tested": 9,
    "sampled": 2,
    "policyBlocked": 1,
    "environmentBlocked": 0,
    "unreachable": 0,
    "samplingRule": "One representative row action per invoice state; all primary actions tested."
  },
  "contradictionMatrix": [],
  "outOfScope": [],
  "recommendedNextAudit": "Re-run billing after the count source is corrected."
}
```
