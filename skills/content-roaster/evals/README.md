# content-roaster evaluation corpus

Three complementary eval layers are shipped:

- `evals.json`: realistic behavior cases. Compare a candidate version against the previous released skill when a model harness is available.
- `trigger-evals.json`: positive and near-miss routing cases. Optimize for precision and recall; negatives are intentionally adjacent.
- `metamorphic-evals.json`: relations that should remain true when evidence scope, tone, revision state, or counterevidence changes.

The deterministic suite validates the corpus structure. It does **not** claim that model-level behavior passed unless those model runs were actually executed and graded.
