# Output contract v5

Domyślnie zwróć zwarty decision report. DEEP może być dłuższy tylko gdy treść wpływa na decyzję.

## Temporal header

Na początku pokaż:

- `As Of` z timezone,
- `Current Validity: VALID | WATCH | STALE | REOPEN | SUPERSEDED`, jeśli decyzja ma historię,
- Freshness summary dla materialnych obszarów,
- najstarszy materialny admissible evidence age, jeśli istotny,
- liczbę aktywnych/triggered Watch Dependencies.

Nie używaj słowa `current` dla materialnego claimu bez temporal verification.

## Verdict

`GO | NO-GO | TEST | DEFER` — Overall Decision Confidence `0–100%`.

Pokaż także:

- Council Mode,
- Required Confidence,
- recommended option/allocation/sequence,
- Evidence Coverage + Critical Gap,
- Contradiction Coverage + critical unresolved contradictions,
- binding gate statuses,
- Human Approval status, jeśli wymagany,
- jednozdaniową rekomendację.

## Confidence map

Pokaż tylko materialne: Thesis, Evidence, Execution, Financial, Legal, Security, Privacy, Timing. Wskaż weakest/binding dimension.

## Independence and forecasts

Dla STANDARD/DEEP pokaż Raw vs Adjusted Consensus i skrócony Independence Grade summary, gdy correlation ma znaczenie. Dla DEEP/high-stakes pokaż 1–3 najważniejsze forecast probabilities, jeśli zostały utworzone.

## Why

2–5 najważniejszych przesłanek z `[F] [A] [I] [FMW] [O]`.

## Double-crux / minority

Pokaż najważniejszą falsyfikowalną niewiadomą i materialny minority report. W DEEP pokaż rezultat alternative/no-action/timing, gdy zmienia wniosek.

## Gates / assumptions / evidence gaps

Pokaż tylko required gates i 1–3 najwyższe Assumption Risk. Dla `CLEAR_WITH_CONTROLS` podaj controls. `COUNSEL_REQUIRED` → konkretne pytanie/handoff. `BLOCK` → binding constraint.

## What changes the decision

Podaj materialne observations/triggers. Jeśli decyzja ma trwałe zależności, zaproponuj Watch Dependencies.

## TEST

Dla TEST pełny Experiment Contract z kill criteria i decision rule.

## Memory

Podaj: zapisano/nie, Decision Key, Snapshot Version/Hash skrócony, Current Validity, history signal strength. Nie ujawniaj prywatnych treści.
