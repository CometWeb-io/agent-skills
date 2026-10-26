# Formal review provenance

Use this reference only when a caller requires v6 pass records or explicitly requests independent review. Self-checking within one context is not independent corroboration. Do not simulate additional reviewers.

Record only passes that actually ran in `assurance.pass_records`: pass id, source ids, opaque context ref, status and blindness to prior findings. `PRIMARY`, `SECONDARY` and `ARBITER` are retained machine-role labels for compatibility, not instructions to act out personas.

- `SINGLE_REVIEW`: one context, `independence=NONE`, `second_pass_status=NOT_RUN`.
- `SECOND_PASS`: an actual later pass, with `SAME_CONTEXT` or `SEPARATE_CONTEXT` as observed. If unavailable, record `UNAVAILABLE` and its limitation.
- `BLIND_DUAL_REVIEW`: only when explicitly requested and the host actually provides separate contexts reviewing the same pinned sources without seeing each other's findings. Requires `SEPARATE_CONTEXT` and `COMPLETED`.

Preserve disagreements and their source basis. Resolve them with evidence; do not vote or average severity. If a material disagreement remains unresolved, lower confidence or leave a verification gap. Provenance does not prove factual accuracy.
