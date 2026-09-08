# Workflow archetypes

Same archetypes and step order as **skill-orchestrator**. Planning kernel:
`scripts/orchestrate_kernel.py` (mirrored copy).

Multiagent mode changes **execution only** — one subagent per step, not the plan logic.

See `skill-orchestrator/references/workflow-archetypes.md` in the repo bundle for the
full archetype table. Quick reference:

| Archetype | Steps |
| --- | --- |
| research_then_council | evidence-researcher → ai-council |
| research_then_operator | evidence-researcher → product-operator |
| audit_then_release | web-app-auditor → release-readiness |
| orchestrated_goal | evidence → optional operator → optional council |

Execution rules: `multiagent-execution.md`.
