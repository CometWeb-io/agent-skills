# Optional snippet for AGENTS.md / CLAUDE.md

```markdown
## Web app audits

For QA, click-through, data-integrity, UI/UX, responsive, form/state, or
accessibility audits of user-facing web surfaces, load `web-app-auditor`.

Do not dilute these rules:

- Scope, capability profile, environment, and mutation policy before interaction.
- Production/unknown is read-only; policy-blocked actions still count in coverage.
- Standard = all critical/unique patterns + representative repeated instances.
- Forensic = no sampling.
- Recalculate material numbers and cross-check repeated facts.
- Separate defect/usability-risk/recommendation/needs-repro.
- Every finding states Expected basis and evidence IDs.
- Do not claim browser actions, network failures, or validator execution that did
  not actually occur.
- Audit is not implementation or penetration testing unless separately requested.
```
