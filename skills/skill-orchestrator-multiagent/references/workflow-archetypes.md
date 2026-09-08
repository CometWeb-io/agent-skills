# Workflow archetypes

Deterministic labels from `scripts/orchestrate_kernel.py`. The agent may skip
steps that clearly do not apply after reading the user goal.

| Archetype | Typical steps | When |
| --- | --- | --- |
| `research_then_council` | evidence-researcher → ai-council | Material decision after claim verification |
| `research_then_operator` | evidence-researcher → product-operator | Weekly ops blocked on unverified claims |
| `audit_then_release` | web-app-auditor → release-readiness | QA findings must feed a pinned RC gate |
| `competitive_then_council` | competitive-intelligence → evidence-researcher? → ai-council | Competitor event → strategic response |
| `orchestrated_goal` | evidence-researcher → (product-operator?) → (ai-council?) | End-to-end goal; kernel prunes steps |
| `single_skill` | one specialist | User asked for one skill only |
| `disambiguate_only` | routing recommendation | User needs skill selection, not execution |

## Default end-to-end (`orchestrated_goal`)

When the user tags `@skill-orchestrator` with a broad goal:

1. **Evidence Researcher** if material factual claims are in scope.
2. **Product Operator** if the goal mentions roadmap, weekly ops, GitHub/Notion, or priorities.
3. **AI Council** only when the goal implies a material decision (pricing, GO/NO-GO, Rada).

Do not run Council for routine research or triage.

## Polish triggers

| User phrase | Archetype |
| --- | --- |
| od researchu do Rady / przepuść przez Radę po dowodach | `research_then_council` |
| zrób wszystko / cały workflow | `orchestrated_goal` |
| audit potem release | `audit_then_release` |
| który skill / nie wiem co wybrać | `disambiguate_only` |
