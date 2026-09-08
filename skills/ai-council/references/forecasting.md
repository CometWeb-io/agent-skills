# Forecasting and base rates v5

## Outside view first

Dla powtarzalnych archetypów decyzji uruchom `base-rate` przed dominacją inside-view narrative. Base rate jest użyteczny tylko, gdy próbka i regime fit są sensowne; kernel nie uznaje próbki `<5` za podstawę uczenia.

## Forecasts

Dla DEEP i materialnych decyzji twórz 1–5 rozstrzygalnych prognoz, np.:

- `P(hit target by 90d)`,
- `P(major execution delay)`,
- `P(regulatory blocker)`,
- `P(customer adoption threshold)`,
- `P(runway breach)`.

Każda prognoza ma:

- jednoznaczne event definition,
- probability `0–1`,
- horizon/due date,
- expert ID lub Chairman,
- Independence Grade,
- późniejszy outcome.

Notion: bind `forecasts` via `~/.config/cometweb/ai-council-notion.json` (see example).

## Calibration

Po rozstrzygnięciu licz Brier score przez `forecast-score`. Nie utożsamiaj dobrego końcowego verdictu z dobrą kalibracją probabilistyczną. Ucz się osobno per ekspert, typ decyzji i regime.
