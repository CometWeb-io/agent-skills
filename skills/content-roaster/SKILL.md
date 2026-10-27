---
name: content-roaster
description: >-
  Compatibility alias for content-reviewer with the ADVERSARIAL profile and retained
  cometweb.content-roaster/v6 tools. Use to roast, tear apart, red-team or brutally critique
  marketing, sales, product, editorial and long-form content with evidence and a repair.
  Do not use for scientific peer review, code critique, rewrite-only editing, primary fact
  research or SEO audits. This is one content review, not an extra reviewer or a multiagent mode.
---

# Content Roaster — compatibility entry

Immediately load and follow the installed `content-reviewer` SKILL.md. Read `../content-reviewer/SKILL.md` as the canonical instruction source; it must be installed alongside this adapter. If unavailable or excluded, stop with the missing dependency rather than improvise a weaker review.

Use `profile: ADVERSARIAL`. Run one review; this alias does not authorize extra passes, edits or external actions. Preserve the requested report contract: ordinary prose needs no JSON. Existing v6 callers keep v6; the profile alone does not select or convert a machine format.

## Retained v6 tools

- When a caller requires the existing v6 report or typed pipeline, read `references/output-contract.md` and `references/workflow.md`. Run `python3 scripts/validate_roast.py report.json`; do not substitute the review/v1 validator or fabricate missing fields.
- When formal operations or independent passes are requested, read `references/review-operations.md` and `references/assurance-protocol.md`; record only passes that actually ran.
- When a revision needs a resolution ledger, read `references/revision-protocol.md`.
- When domain prompts help, read `references/profiles.md` or `references/policy-packs.md`; packs cannot create evidence or upgrade severity.

Existing script paths, v6 fields, finding keys and revision semantics remain available. Validator success does not authenticate evidence, establish business impact or authorize publication.
