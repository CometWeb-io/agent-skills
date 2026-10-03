# ArtifactBrief — data-retention explainer for Example Health customers

## Brief status

- Status: PROVISIONAL
- Reason: one material decision (D-01) is still open and one material assumption is in use; drafting may start on the assumed branch, but the brief is not READY.
- Mode: DEEP
- Brief: `brief-retention-explainer` version 3, supersedes `brief-retention-explainer-v2`
- Risk level: HIGH

## Objective and audience

- Objective: explain to clinic administrators how long Example Health keeps appointment records and how they request deletion.
- Audience: practice managers at small clinics who handle patient data requests; not lawyers.
- Use moment: when a patient asks the clinic to delete their history.
- Scope: retention periods, the deletion request flow and what the clinic must tell the patient.

## Exclusions

- Legal advice or jurisdiction-by-jurisdiction analysis.
- Any statement about competitors' retention practices.

## Evidence policy

- Policy: SOURCE_BOUND
- Freshness boundary: only the retention policy at example.org/policy revision 2026-08 and the support runbook it links.

## Deliverables

- DL-01: help-centre article (EN) of at most 900 words.
- DL-02: a one-table summary for the admin dashboard tooltip.

## Acceptance criteria

| ID | Priority | Check | Evidence required | Verification method |
| --- | --- | --- | --- | --- |
| AC-01 | MUST | Every retention period quotes the policy clause it comes from | yes | Compare each period with the clause in policy revision 2026-08 |
| AC-02 | MUST | The deletion flow lists every step a clinic must take, in order, with the expected response time | yes | Walk the flow in the staging tenant and record each screen |
| AC-03 | MUST | No sentence promises deletion faster than the policy states | no | Search the draft for time promises and check each against AC-01 |

## Protected invariants

- INV-01: the article never says data is "permanently erased" while backups still hold it.
- INV-02: the article never gives legal advice; it points to the clinic's own counsel.

## Known

- The policy sets a 30-day backup window after deletion (example.org/policy, clause 4.2).

## Assumptions

- Material assumption: the audience reads English; a Polish version would be a new brief (value used until D-01 is answered).

## Decisions needed

- D-01 — open: does the article cover archived records older than seven years, which follow a separate process? Owner to answer; it changes AC-02 and the scope.

## Recommended next skill

Return D-01 to the requester. Once answered, `content-writer` with this brief at version 4.

```json
{
  "schema": "cometweb.artifact-brief/v1",
  "brief_id": "brief-retention-explainer",
  "brief_version": 3,
  "supersedes_brief_id": "brief-retention-explainer-v2",
  "mode": "DEEP",
  "status": "PROVISIONAL",
  "objective": "Explain to clinic administrators how long appointment records are kept and how to request deletion.",
  "audience": "Practice managers at small clinics who handle patient data requests",
  "use_moment": "When a patient asks the clinic to delete their history",
  "scope": "Retention periods, the deletion request flow and what the clinic must tell the patient",
  "risk_level": "HIGH",
  "exclusions": ["Legal advice", "Competitor retention practices"],
  "evidence_policy": "SOURCE_BOUND",
  "freshness_boundary": "Policy revision 2026-08 at example.org/policy",
  "deliverables": [{"id": "DL-01", "type": "article"}, {"id": "DL-02", "type": "table"}],
  "acceptance_criteria": [
    {"id": "AC-01", "priority": "MUST", "check": "Every retention period quotes its policy clause", "observable": true, "evidence_required": true, "verification_method": "Compare each period with policy revision 2026-08"},
    {"id": "AC-02", "priority": "MUST", "check": "Deletion flow lists every step in order with response time", "observable": true, "evidence_required": true, "verification_method": "Walk the flow in the staging tenant"},
    {"id": "AC-03", "priority": "MUST", "check": "No sentence promises deletion faster than the policy states", "observable": true, "evidence_required": false}
  ],
  "protected_invariants": [
    {"id": "INV-01", "rule": "Never say data is permanently erased while backups hold it"},
    {"id": "INV-02", "rule": "Never give legal advice"}
  ],
  "known": ["30-day backup window after deletion, clause 4.2"],
  "assumptions": [{"value": "The audience reads English", "material": true}],
  "decision_needed": [{"id": "D-01", "question": "Does the article cover archived records older than seven years?", "material": true, "resolved": false}],
  "recommended_next_skill": "content-writer"
}
```
