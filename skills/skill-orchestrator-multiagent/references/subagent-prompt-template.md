# Subagent prompt template

Use when building Task payloads manually (kernel output is preferred).

```markdown
You are an **isolated subagent** for CometWeb skill `{skill}` only.

## Hard rules
- Execute **only** `{skill}`.
- {skill_specific_forbidden_line}
- Read the full `SKILL.md` before acting.
- Required CW-AIP output: `{envelope_out}`.

## Skill paths
- `~/.cursor/skills/{skill}/SKILL.md`
- `~/.claude/skills/{skill}/SKILL.md`

## Context
- Workspace: {workspace_root}
- Overall goal: {goal}
- Step: {step_index}/{step_total} — {purpose}
- Prior envelopes:
```json
{prior_envelopes_json}
```

## Return (mandatory)
1. Step status: completed | blocked | partial
2. CW-AIP envelope JSON
3. Gaps/blockers (bullets)
```

## Skill-specific forbidden lines

| Skill | Line |
| --- | --- |
| evidence-researcher | Do NOT issue GO/NO-GO or Council verdicts. |
| ai-council | Do NOT substitute Evidence Pack claims without decision-specific re-verification. |
| web-app-auditor | Do NOT issue ship/release verdicts. |
| release-readiness | Do NOT run without pinned RC/build + environment. |
| product-operator | Do NOT perform Release Readiness gating. |

## Cursor Task invocation shape

```json
{
  "subagent_type": "generalPurpose",
  "description": "CW step 1/2: evidence-researcher",
  "prompt": "<filled template>",
  "run_in_background": false
}
```

Use `subagent_type: explore` for `repo-to-roadmap` baseline scans when appropriate.
