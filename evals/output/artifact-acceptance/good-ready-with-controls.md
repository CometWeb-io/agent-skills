# Acceptance: Field guide to onboarding emails

- Verdict: READY_WITH_CONTROLS
- Candidate: `guide-onboarding` v3 (sha256 `9f2c41d0`)
- Contract: `AC-ONB-1` (brief `BR-ONB-1`), profile EDITORIAL, mode STANDARD
- As of: 2026-09-30T14:00:00+02:00

## Blocking gates and findings

None. Every required gate passes and no BLOCKER or MAJOR finding is open.

## Gates

| Gate | Required | State | Evidence |
| --- | --- | --- | --- |
| brief_compliance | yes | PASS | EV-01: section checklist against `BR-ONB-1`, v3 |
| claim_integrity | yes | PASS | EV-02: claim ledger, 14/14 claims sourced, v3 |
| format_qa | yes | PASS | EV-03: PDF render check, 28 pages, v3 |
| link_validation | no | UNKNOWN | not run; not required by `AC-ONB-1` |

## Findings

- **AF-01** MINOR, open, non-blocking: the glossary repeats the definition of "activation" twice (EV-03).

## Controls

- **CTL-01** MINOR, covers AF-01. Owner: editor on duty. Revisit: before the v4 export, or within 14 days.

## Verdict explanation

All three required EDITORIAL gates pass with evidence bound to v3 and contract `AC-ONB-1`. The only open
finding, AF-01, is MINOR and carries a control with an owner and a revisit condition, so the verdict is
READY_WITH_CONTROLS rather than READY. No control bypasses a required gate.

## Handoff

- next_skill: `repair-operator` for AF-01
- stale_if_changed: true; any change to v3 makes this verdict stale.

```json
{
  "schema": "cometweb.artifact-acceptance/v1",
  "profile": "EDITORIAL",
  "mode": "STANDARD",
  "candidate": {"id": "guide-onboarding@v3", "version_or_hash": "9f2c41d0"},
  "contract": {"id": "AC-ONB-1", "brief_id": "BR-ONB-1"},
  "as_of": "2026-09-30T14:00:00+02:00",
  "gates": [
    {"gate_id": "brief_compliance", "required": true, "state": "PASS",
     "evidence": [{"source": "EV-01", "locator": "checklist.md#v3", "candidate_id": "guide-onboarding@v3", "observed_at": "2026-09-30T13:10:00+02:00"}]},
    {"gate_id": "claim_integrity", "required": true, "state": "PASS",
     "evidence": [{"source": "EV-02", "locator": "claims.csv", "candidate_id": "guide-onboarding@v3", "observed_at": "2026-09-30T13:25:00+02:00"}]},
    {"gate_id": "format_qa", "required": true, "state": "PASS",
     "evidence": [{"source": "EV-03", "locator": "render-report.txt", "candidate_id": "guide-onboarding@v3", "observed_at": "2026-09-30T13:40:00+02:00"}]},
    {"gate_id": "link_validation", "required": false, "state": "UNKNOWN", "evidence": []}
  ],
  "findings": [{"severity": "MINOR", "open": true, "blocks_acceptance": false}],
  "controls": [{"severity": "MINOR", "issue": "duplicated glossary definition", "owner": "editor on duty",
                "revisit_condition": "before the v4 export or within 14 days", "candidate_id": "guide-onboarding@v3"}],
  "verdict": "READY_WITH_CONTROLS",
  "stale_if_changed": true,
  "next_skill": "repair-operator"
}
```
