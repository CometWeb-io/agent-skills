# Leakage detection

A holdout must remain meaningfully unseen by the candidate-development process.

Before freezing a DEEP benchmark:

1. Record known case exposure for the candidate and its development history.
2. Detect exact duplicates between dev and holdout.
3. Detect near-duplicate prompts or fixtures using a declared similarity rule.
4. Treat a known exposed holdout case as contaminated even if wording changed later.
5. Keep mined production failures in regression/dev unless a fresh independent holdout is created.
6. Freeze a corpus fingerprint alongside the benchmark hash.

Scan statuses (`leakage_scan.status`; a single case uses `contamination_status`, see `references/benchmark-model.md`):

- `CLEAN` — no detected exact/near leakage and no known exposure under the declared scan.
- `SUSPECT` — near-duplicate or unresolved provenance requires review before freeze.
- `CONTAMINATED` — known exposure or exact leakage invalidates the holdout claim.

A `CLEAN` scan is bounded evidence, not proof that no hidden contamination exists.

No leakage scanner ships with this skill. `scripts/kernel.py` catches exact duplicate prompts only, after folding case and whitespace; near-duplicate detection is a manual or external step. Record the similarity rule you applied and the corpus fingerprint with the benchmark revision, in `leakage_scan`.
