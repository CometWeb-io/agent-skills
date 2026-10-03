Stan: READY — Master 1.0.0 is locked and the PDF and HTML editions passed lineage, QA and parity.

PUBLICATION SUMMARY

| Field | Value |
| --- | --- |
| Publication | Field Guide to Release Notes |
| Type | GUIDE |
| Mode | BUILD |
| Master | manuscript.md @ 1.0.0 |
| Derived | PDF, HTML |

CURRENT STAGE

- RELEASE_READY

NEXT MILESTONE

- Upload the PDF and HTML editions to https://example.com/guides — Done: the live URL serves master 1.0.0 and is recorded in publication_evidence

publication-report.json:

```json
{
 "protocol_version": "longform-publisher/1",
 "as_of": "2026-10-02T15:00:00+02:00",
 "mode": "BUILD",
 "status": "READY",
 "status_reason": "Master 1.0.0 is locked and the PDF and HTML editions passed lineage, QA and parity.",
 "publication": {"id": "pub-ops-guide", "title": "Field Guide to Release Notes", "type": "GUIDE", "audience": "Product teams at example-org", "objective": "Teach a repeatable release-notes workflow."},
 "source_policy": {"mode": "SOURCE_BOUND", "authorized_source_ids": ["SRC-01", "SRC-02"]},
 "sources": [
  {"id": "SRC-01", "system": "USER", "locator": "example-org internal style guide v4", "authorized": true, "freshness": "CURRENT", "observed_at": "2026-09-28T10:00:00+02:00"},
  {"id": "SRC-02", "system": "USER", "locator": "https://example.com/research/release-notes-survey-2026", "authorized": true, "freshness": "CURRENT", "observed_at": "2026-09-28T10:30:00+02:00"}
 ],
 "lifecycle": {"brief_complete": true, "sources_admitted": true, "outline_locked": true, "draft_complete": true, "claims_reconciled": true, "edited_complete": true, "master_locked": true, "release_ready": true},
 "current_stage": "RELEASE_READY",
 "canonical_master": {"path": "manuscript.md", "version": "1.0.0", "sha256": "3f6c2a9e1b7d4058a2c9e6f1b0d3a7c5e8f2b4d6a9c1e3f5b7d9a2c4e6f8b0d1"},
 "sections": [
  {"id": "s1", "heading": "Why release notes fail", "status": "COMPLETE"},
  {"id": "s2", "heading": "The workflow", "status": "COMPLETE"}
 ],
 "claim_uses": [
  {"id": "CU-01", "section_id": "s1", "claim_text": "In the 2026 survey, 37% of respondents skip release notes longer than one screen.", "materiality": "MATERIAL", "claim_kind": "FACT", "support_status": "SUPPORTED", "evidence_refs": ["SRC-02"], "citation_state": "PRESENT", "citation_marker": "[2]", "volatile_current": false, "freshness_state": "CURRENT"},
  {"id": "CU-02", "section_id": "s2", "claim_text": "Write the user-visible change first.", "materiality": "SUPPORTING", "claim_kind": "AUTHOR_ASSERTION", "support_status": "NOT_REQUIRED", "evidence_refs": [], "citation_state": "NOT_REQUIRED", "volatile_current": false, "freshness_state": "NOT_TIME_SENSITIVE"}
 ],
 "protected_facts": [
  {"id": "PF-01", "value": "37%", "required": true}
 ],
 "fidelity": {"required": true, "passed": true, "checked_at": "2026-10-01T18:00:00+02:00"},
 "edit_history": [
  {"type": "AI_HUMANIZE", "status": "COMPLETE"}
 ],
 "unresolved_gaps": [],
 "derived_artifacts": [
  {"id": "pdf1", "format": "PDF", "path": "field-guide.pdf", "master_sha256": "3f6c2a9e1b7d4058a2c9e6f1b0d3a7c5e8f2b4d6a9c1e3f5b7d9a2c4e6f8b0d1", "generation_status": "COMPLETE", "qa_required": true, "qa_status": "PASS", "parity_status": "PASS", "direct_material_edit": false},
  {"id": "html1", "format": "HTML", "path": "field-guide.html", "master_sha256": "3f6c2a9e1b7d4058a2c9e6f1b0d3a7c5e8f2b4d6a9c1e3f5b7d9a2c4e6f8b0d1", "generation_status": "COMPLETE", "qa_required": false, "qa_status": "NOT_REQUIRED", "parity_status": "PASS", "direct_material_edit": false}
 ],
 "publication_evidence": [],
 "actions": {"blockers": [], "verify_now": [], "decision_now": [], "now": [], "next_milestone": [{"id": "nm1", "action": "Upload the PDF and HTML editions to https://example.com/guides", "done_when": "the live URL serves master 1.0.0 and is recorded in publication_evidence"}], "delegate": [], "waiting": [], "stop": []}
}
```
