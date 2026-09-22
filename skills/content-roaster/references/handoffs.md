# Content Roaster handoffs

Machine handoffs use `references/handoff-contract.md` (`cometweb.roaster-handoff/v2`). Carry only post-arbitration accepted findings; unresolved questions stay in `unresolved_verification` rather than being promoted to defects.
| Need | Owner | Handoff condition |
| --- | --- | --- |
| Scientific methodology or inferential review | `science-roaster` | Central claims depend on study design, measurement, statistics, novelty, validity, or reproducibility |
| Whole-repository or codebase critique | `repo-roaster` | The artifact is source code, a repository, a PR, or architecture/configuration rather than prose |
| Meaning-preserving rewrite | `ai-humanize` | Critique is complete and the user asks for revised prose |
| External claim verification | `evidence-researcher` | Truth cannot be resolved from the supplied artifact |
| SEO/GEO/AEO visibility | `seo-geo-aeo-maxxing` | Discoverability or answer-engine performance is the question |
| Publication lifecycle | `longform-publisher` | A long-form artifact must be reconciled and released across derived formats |

Carry source identifier, scope, anchors, unresolved verification questions, and highest-severity findings. Do not silently execute the downstream skill.

For revision workflows, also carry stable `finding_key` values, resolution status, root-cause ids, and the verification contract so downstream rewriting does not erase the review trail.
