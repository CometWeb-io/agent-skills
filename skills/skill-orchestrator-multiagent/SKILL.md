---
name: skill-orchestrator-multiagent
description: Alias for skill-orchestrator with execution_mode=isolated_subagents. Use when the user asks for multiagent orchestration, separate agents per skill, Task/subagent per step, or strict isolation between Evidence Researcher, AI Council, auditors, and other skills. Do not use when a single specialist suffices, when the host has no subagent/Task API (use skill-orchestrator single_thread), for routing-only questions, or to bypass AI Council or Release Readiness policy.
---

# Skill Orchestrator — Multiagent (alias)

This package is a **thin alias**. Canonical planning and sequencing live in
`skill-orchestrator`.

Immediately load and follow:

[`../skill-orchestrator/SKILL.md`](../skill-orchestrator/SKILL.md)

with:

```text
execution_mode: isolated_subagents
```

Shared references (do not fork):

- `../skill-orchestrator/references/workflow-archetypes.md`
- `../skill-orchestrator/references/sequencing-rules.md`
- `references/multiagent-execution.md`
- `references/subagent-prompt-template.md`

Parent thread **plans and merges only**. Each specialist runs in its own subagent.
If Task/subagent API is unavailable, stop and recommend `@skill-orchestrator`
with `execution_mode=single_thread`.
