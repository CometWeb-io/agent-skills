# Repo Roaster handoffs

Machine handoffs use `references/handoff-contract.md` (`cometweb.roaster-handoff/v2`). Carry only post-arbitration accepted findings; unresolved questions stay in `unresolved_verification` rather than being promoted to defects.
| Need | Owner | Handoff condition |
| --- | --- | --- |
| Dependency-aware plan from current repo to target state | `repo-to-roadmap` | Accepted findings must become sequenced implementation work |
| Pinned release candidate GO/NO_GO | `release-readiness` | The user asks whether a specific candidate/environment can ship |
| Runtime browser/UI verification | `web-app-auditor` | A source finding requires reproduction in a website or web app |
| Learn transferable patterns from another product/repo | `product-teardown` | The goal is adaptation, not adversarial critique |
| Scientific validity of research code/results | `science-roaster` | The engineering artifact is secondary to the scientific inference |
| Material factual verification outside the repo | `evidence-researcher` | A dependency, standard, vendor, or claim requires external evidence |

Carry repository/ref, coverage ledger, anchors, absence proofs, verification gaps, and highest-severity findings.

For RECHECK or implementation handoffs, also carry stable `finding_key` values, invariant refs, critical-path refs, resolution status, and the verification contract needed to prove the fix.
