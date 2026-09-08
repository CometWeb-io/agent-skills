# Forms, empty, error, loading

Most meaningful product defects live outside the ideal happy-path render. Apply
`safety-and-mutations.md` before valid submission or terminal actions.

## 1. Form protocol

For each in-scope form/state class supported by capability:

1. **Initial** — defaults, locale, preselection, hidden assumptions.
2. **Empty submit** — only when submit is policy-safe; errors are discoverable.
3. **Invalid values** — boundary/type/length/whitespace cases that do not create
   dangerous external effects.
4. **Valid submit** — only in `safe-test-only` with disposable/test data; verify
   durable state, not only toast.
5. **Cancel/Esc/back** — user work is not silently persisted/lost contrary to
   product behavior.
6. **Failure** — exercise through a safe test mechanism when available; never
   sabotage production services to manufacture a 500.
7. **Disabled** — reason and semantics match state.
8. **File upload** — use benign test files; do not upload sensitive or malicious
   payloads as part of ordinary product QA.
9. **Multi-step** — state/validation is coherent across steps.

If valid submit is unsafe, inspect up to the pre-commit boundary and record it as
`policy-blocked`.

## 2. Validation quality

File severity by consequence:

- lockout, material data loss, or inability to complete a primary job can be
  major/blocker when proven
- vague error copy on a primary flow is often major/minor depending on recovery
- convenience preferences such as "inline errors are nicer" are heuristics

Do not impose password/confirmation patterns unless relevant to the product's
actual risk and requirements.

## 3. Empty states

Distinguish:

| State | Honest behavior |
|---|---|
| never had data | explains absence and useful next step where applicable |
| filter/search hid all | communicates no matches and active constraint |
| no permission | does not masquerade as empty success |
| request failed | does not claim there is simply no data |
| legitimate zero | renders zero rather than ambiguous blank |

## 4. Loading

Judge whether the user can tell work is in progress and avoid unsafe repeated
action. Skeleton vs spinner is not itself a defect. Exact time thresholds are
heuristics unless product requirements define them.

## 5. Errors

- user sees a recoverable failure, not only console output
- terminal-action failures preserve enough state to recover
- retry is available when useful and safe
- session/auth interruption does not silently corrupt state

Do not force real payment/delete/send failures in production. Use a sandbox,
mock/test path, or mark the path untested.

## 6. Toasts and dialogs

- confirmation identifies the consequential object/action when ambiguity matters
- cancel path is safe and predictable
- toast is supplementary; durable state remains authoritative
- dialog focus/dismissal behavior is accessible when applicable

## 7. Search, filter, sort, pagination

Check result correctness, visible active state, count arithmetic, reset/recovery,
and stable sort/pagination where relevant.

URL persistence/shareability is not universal. File it only with a stronger
basis (`product-requirement`, `platform-convention` for true navigation, or
observed user-job need); otherwise keep it as a recommendation.
