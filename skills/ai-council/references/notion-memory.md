# Notion Decision Memory v5

## Data sources

Bind your own Notion databases outside the public skill tree.

Lookup order:

1. `$COMETWEB_CONFIG_HOME/ai-council-notion.json` — default `~/.config/cometweb/ai-council-notion.json`
2. `references/notion-bindings.local.json` — optional gitignored override in a clone

Use `notion-bindings.example.json` as the schema. Do not commit real `collection://`
IDs or hub URLs.

Required logical databases:

- Decisions
- Expert Votes
- Experiments
- Assumptions
- Evidence
- Framework Uses
- Process Memory
- Decision Reviews
- Watch Dependencies
- Forecasts
- Source Registry

Optional: a Notion hub page URL for operator navigation.

## Blind firewall

Przed zakończeniem blind round nie czytaj Decisions/Votes/Framework outcomes.

## Immutable Decision Snapshot

Snapshot zawiera wiedzę dostępną w momencie decyzji: Decision Contract, versions, mode/roles, blind memos, assumptions, evidence metadata, temporal verification state, gates, consensus, confidence, Chairman proposal i final gate. Późniejszy review nigdy go nie nadpisuje.

## Mutable Validity Overlay

Na Decisions utrzymuj addytywnie: `Current Validity`, `Validity Reason`, `Last Revalidated At`, `Next Revalidation At`, `Current As Of`, stale evidence count, Contradiction Coverage, Watch Trigger Count, Independence Grade Summary, Forecast Summary, Human Approval Required.

Zmiana świata aktualizuje overlay i Watch/Process Memory; nie zmienia historycznego snapshotu.

## Evidence v5

Dopisuj temporal fields i contradiction state zgodnie z `references/freshness.md` oraz `references/evidence-policy.md`.

## Transaction pattern

1. Decision `Writing`.
2. Votes/Assumptions/Evidence/Framework Uses/Experiment/Forecasts/Watch Dependencies `Writing`.
3. Zweryfikuj relacje, freshness i wymagane pola.
4. Dzieci → `Complete`.
5. Decision → `Complete` jako ostatni.

`Writing`/`Invalid` nie wpływa na learning.

## Process Memory

Legacy Event Type może pozostać dla kompatybilności. Nowe zdarzenia zapisuj też w `Event Type v5`, np. `freshness_block`, `source_superseded`, `decision_reopened`, `watch_triggered`, `forecast_resolved`, `human_escalation`.

## Source Registry

Registry jest discovery-only. Nie ucz się z wpisu registry jako z faktu o świecie. Aktualność potwierdza live source.
