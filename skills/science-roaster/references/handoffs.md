# Science Roaster handoffs

Machine handoffs use `references/handoff-contract.md` (`cometweb.roaster-handoff/v2`). Carry only post-arbitration accepted findings; unresolved questions stay in `unresolved_verification` rather than being promoted to defects.
| Need | Owner | Handoff condition |
| --- | --- | --- |
| External novelty/citation/standard verification | `evidence-researcher` | The manuscript or review requires evidence outside supplied sources |
| Research stage gates and next-study planning | `research-program-operator` | Accepted findings must become program decisions or next experiments |
| Publication workflow | `longform-publisher` | Scientific content is repaired and must be released across manuscript/derived formats |
| Meaning-preserving prose rewrite | `ai-humanize` | Scientific meaning and uncertainty must remain invariant while prose changes |
| Marketing/editorial critique | `content-roaster` | The artifact is not governed by a scientific inference contract |
| Repository/code critique | `repo-roaster` | The question concerns source code, analysis code, pipelines, or repository architecture rather than manuscript claims |

Carry source/version identifier, review scope, claim ids, anchors, evidence states, unresolved verification questions, and highest-severity findings.

For revision workflows, also carry stable `finding_key` values, claim inferential types, root-cause ids, resolution status, and the minimum scientific verification contract.
