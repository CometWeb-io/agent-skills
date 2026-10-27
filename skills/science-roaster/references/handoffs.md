# Science Roaster handoffs

When a receiver requires a machine handoff, use `references/handoff-contract.md` (`cometweb.roaster-handoff/v2`). Carry only findings that survive counterevidence checks; unresolved questions stay in `unresolved_verification` rather than being promoted to defects.
| Need | Owner | Handoff condition |
| --- | --- | --- |
| External novelty/citation/standard verification | `evidence-researcher` | The manuscript or review requires evidence outside supplied sources |
| Research stage gates and next-study planning | `research-program-operator`; the user owns program decisions | Use when accepted findings need an authorized program/stage assessment or next-study plan; preserve unresolved questions and do not authorize research execution |
| Publication workflow | `longform-publisher` | Scientific content is repaired and must be released across manuscript/derived formats |
| Meaning-preserving prose rewrite | `ai-humanize` | Scientific meaning and uncertainty must remain invariant while prose changes |
| Marketing/editorial critique | `content-roaster` | The artifact is not governed by a scientific inference contract |
| Repository/code critique | `repo-roaster` | The question concerns source code, analysis code, pipelines, or repository architecture rather than manuscript claims |

Carry source/version identifier, review scope, claim ids, anchors, evidence states, unresolved verification questions, and highest-severity findings.

For revision workflows, also carry stable `finding_key` values, claim inferential types, root-cause ids, resolution status, and the minimum scientific verification contract.

A handoff does not authorize the downstream task. Run only the scope the user requested; unresolved questions remain questions.
