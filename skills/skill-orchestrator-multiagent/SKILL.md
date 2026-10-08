---
name: skill-orchestrator-multiagent
description: Alias for skill-orchestrator with execution_mode=isolated_subagents. Do not use when a single specialist suffices, when the host has no subagent/Task API (use skill-orchestrator single_thread), for routing-only questions, or to bypass AI Council or Release Readiness policy. Use when the user asks for multiagent orchestration, separate agents per skill, Task/subagent per step, or strict isolation between Evidence Researcher, AI Council, auditors, and other skills.
---

# Skill Orchestrator — Multiagent (alias)

This package is a **thin alias**. Canonical planning and sequencing live in
`skill-orchestrator`, which must be installed alongside this package. If it is
unavailable, stop and ask the user to install it; do not improvise the missing
planning contract.

Immediately load and follow the installed `skill-orchestrator` SKILL.md with:

```text
execution_mode: isolated_subagents
```

Shared references (do not fork):

- `references/workflow-archetypes.md` — read before choosing; sequencing stays in `skill-orchestrator`.
- `references/multiagent-execution.md` — read before launching the first subagent
- `references/subagent-prompt-template.md` — build every subagent prompt from it

Script inputs and outputs (payload builder, envelope gate): `references/kernel-contract.md`.

Parent thread **plans and merges only**. Each specialist runs in its own subagent.
If Task/subagent API is unavailable, stop and recommend `@skill-orchestrator`
with `execution_mode=single_thread`.

For resumable runs, use the canonical `skill-orchestrator` local workflow
ledger (`references/run-ledger-contract.md` in that package). The alias does
not maintain a second ledger or add semantics to CW-AIP, Council verdicts, or
Release Readiness verdicts.

For `--with-prd-handoff`, read `references/prd-handoff.md` before dispatch.

Local profiles: `references/specialist-profiles.md`; sidecars do not replace owner gates.


Read [compiled-worker.md](references/compiled-worker.md) before compiled dispatch.
