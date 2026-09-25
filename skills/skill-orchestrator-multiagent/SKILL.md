---
name: skill-orchestrator-multiagent
description: Alias for skill-orchestrator with execution_mode=isolated_subagents. Use when the user asks for multiagent orchestration, separate agents per skill, Task/subagent per step, or strict isolation between Evidence Researcher, AI Council, auditors, and other skills. Do not use when a single specialist suffices, when the host has no subagent/Task API (use skill-orchestrator single_thread), for routing-only questions, or to bypass AI Council or Release Readiness policy.
---

# Skill Orchestrator — Multiagent (alias)

This package is a **thin alias**. Canonical planning and sequencing live in
`skill-orchestrator`, which must be installed alongside this package. If it is
unavailable, stop and ask the user to install it; do not improvise the missing
planning contract.

Immediately load and follow:

the installed `skill-orchestrator` skill entrypoint

with:

```text
execution_mode: isolated_subagents
```

Shared references (do not fork):

- `skill-orchestrator` workflow archetypes and sequencing rules from its installed package
- `references/multiagent-execution.md`
- `references/subagent-prompt-template.md`

Parent thread **plans and merges only**. Each specialist runs in its own subagent.
If Task/subagent API is unavailable, stop and recommend `@skill-orchestrator`
with `execution_mode=single_thread`.
