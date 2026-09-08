---
name: ai-council
description: Run an always-current, evidence-governed AI decision council for material, high-stakes, multi-domain decisions where options, risk gates, forecasts, and living memory matter. Use when the user explicitly asks to "przepuść przez Radę", "zapytaj Radę", compare consequential options, challenge a major plan, decide GO/NO-GO/TEST/DEFER on strategic choices, verify whether a prior decision is still current, inspect Council health, or improve the Council itself. Do not use for routine weekly product prioritization, whole-repo roadmapping, release-candidate gates, customer support triage, or single-domain specialist work when a dedicated skill exists. Orchestrate blind advisers, conditional specialists, binding risk gates, live/fresh evidence, temporal truth, contradiction testing, forecasts, living Decision Memory, watch dependencies, human escalation, and champion/challenger evaluation.
---

# AI Council v5

Prowadź Radę jako **temporal decision intelligence system**, nie panel person. `scripts/council_kernel.py` jest deterministycznym źródłem prawdy dla Decision Contract, trybu, routingu, frameworków, evidence/freshness, consensus correction, minority protection, VOI, stop rule, gate'ów, forecasts, living-decision validity, portfolio conflicts, tool authority, eksperymentów, snapshotów i metryk. Nie odtwarzaj ręcznie reguł, które kernel może policzyć.

## Zasady nadrzędne

1. Rozdzielaj `adviser`, `specialist`, `gatekeeper`, `auditor`, `authority` zgodnie z `references/experts.md`.
2. Materialny constraint prawny/security/privacy/financial-risk nie jest zwykłym głosem większościowym.
3. **Current claim wymaga current evidence.** Dla materialnych time-sensitive claims zapisuj `as_of` i Temporal Status; stale/superseded/draft/not-yet-effective/unknown evidence nie może podtrzymywać bezwarunkowego GO/NO-GO.
4. Decision Snapshot jest immutable; bieżący stan decyzji żyje w `Decision Validity Overlay` (`VALID/WATCH/STALE/REOPEN/SUPERSEDED`).
5. Source Registry służy do discovery. Nigdy nie traktuj wpisu registry jako dowodu; otwórz bieżące źródło.
6. Dla internal claims wybieraj system-of-record, nie najwygodniejszy dokument.
7. `GO` nie jest autoryzacją do wykonania side effect. Dla T3/T4 użyj human approval.

## Profile kosztu poznawczego

Wybierz najmniejszy profil, który chroni decyzję. Budżety: `references/modes.md`.

| Profile | Kiedy | Load |
| --- | --- | --- |
| `LIGHT` | mała, odwracalna decyzja | `references/workflow-light.md` |
| `STANDARD` | domyślny materialny | `references/workflow-standard.md` |
| `DEEP` | wysoki lock-in / regulacja / multi-system | `references/workflow-deep.md` |

Nie ładuj DEEP cognitive path dla LIGHT. Kernel `plan` wybiera tryb, jeśli użytkownik go nie wymusi (`LIGHT`≈FAST).

## Workflow

1. Wybierz profil (tabela powyżej).
2. Załaduj **tylko** odpowiadający `workflow-*.md`.
3. Stosuj zasady nadrzędne i twarde granice z tego pliku.
4. Emituj Decision Snapshot / output według `references/output-contract.md`.

## Freshness gate

- `CURRENT` — admissible.
- `NEAR_EXPIRY` — admissible tylko jeśli policy/kernel tak uzna; pokaż warning.
- `STALE | SUPERSEDED | DRAFT | NOT_YET_EFFECTIVE | UNKNOWN` — materialny claim nie jest admissible.
- `freshness status = REFRESH_REQUIRED` → final gate ma prowadzić do `DEFER` do czasu odświeżenia albo usunięcia claimu z binding reasoning path.
- Dla materialnego prawa/regulatory/security wymagaj decision-specific live verification, nawet jeśli registry/cache wygląda świeżo.

## Gate statuses

Używaj wyłącznie:

- `NOT_REQUIRED`,
- `CLEAR`,
- `CLEAR_WITH_CONTROLS`,
- `COUNSEL_REQUIRED`,
- `BLOCK`.

Gatekeeper pokazuje podstawę, zakres i niepewność. Nie przedstawiaj Legal jako substytutu kwalifikowanej porady zawodowej.

## Living decisions

Przy pytaniu „czy to nadal aktualne?” nie twórz nowej decyzji od zera bez potrzeby:

1. pobierz immutable snapshot i bieżący overlay,
2. sprawdź Watch Dependencies i Source Registry,
3. odśwież tylko materialne/current claims i binding gates,
4. uruchom `validity`,
5. `REOPEN` → ponowna deliberacja ograniczona do zmienionych assumption/gate areas,
6. nie zmieniaj starego Snapshot Hash.

## Outcome / forecast review

- Rozliczaj Decision Reviews we właściwych horyzontach.
- Oddziel Outcome, Decision Quality, Execution Quality i Attribution.
- Rozlicz Forecasts przez `forecast-score` i Brier score.
- Zapisz Process Memory, jeśli freshness, routing, watch, gate, minority, Chairman lub human escalation dały ważną lekcję.

## Council health i champion/challenger

Mierz również: stale-evidence catch rate, freshness blocks, contradiction coverage, source-registry misses, system-of-record verification, watch-trigger precision, reopen quality, forecast calibration, portfolio conflicts i human escalation resolution. Nie optymalizuj learned routing/TTL na próbkach `<5` bez silnego zewnętrznego uzasadnienia. Użyj `eval-compare` dla challengera.

## Twarde granice

- Nie czytaj Decision Memory przed zakończeniem blind round.
- Nie pokazuj blind ekspertom peer memos/outcomes/calibration/Red Team/Chairman preference.
- Framework, doctrine, wcześniejsza decyzja i Source Registry nie są current fact.
- Nie pokazuj Chairmanowi rejected ani temporally inadmissible evidence.
- Nie wysyłaj prywatnych raw chunks do publicznego web search.
- Unknown independence nie jest independent confirmation.
- Nie używaj słowa `current` dla materialnego claimu bez jawnego `as_of` i verification state.
- Nie koduj aktualnego brzmienia prawa, security advisories, cen ani vendor policy jako stałych w skillu.
- Nie nadpisuj immutable snapshotu podczas revalidacji.
- Nie pozwalaj większości przegłosować `BLOCK`.
- `GO/NO-GO` wymagają odpowiedniego confidence i CLEAR freshness.
- Preferuj TEST, gdy tani odwracalny eksperyment ma dodatni VOI.
- DEFER, gdy binding evidence/gate/freshness/human approval pozostaje nierozstrzygnięty.

## Notion Decision Memory

Workspace bindings are **not** shipped in this public skill.

Lookup order (first file that exists wins):

1. `$COMETWEB_CONFIG_HOME/ai-council-notion.json` (default home: `~/.config/cometweb/`)
2. `references/notion-bindings.local.json` (optional, gitignored — for one-off overrides)

Shape: copy `references/notion-bindings.example.json`. Required databases: Decisions,
Expert Votes, Experiments, Assumptions, Evidence, Framework Uses, Process Memory,
Decision Reviews, Watch Dependencies, Forecasts, Source Registry.

Przed zapisem pobierz aktualny schema. Przeczytaj `references/notion-memory.md`.

## Kernel CLI v5

```bash
python scripts/council_kernel.py contract --query "Czy wejść na nowy rynek?" --context-json '{"financial_impact":0.8}'
python scripts/council_kernel.py plan --contract-json '{...}'
python scripts/council_kernel.py context-route --query "jaki jest aktualny stan repo?"
python scripts/council_kernel.py source-authority --claim-type law_regulation
python scripts/council_kernel.py temporal --row-json '{...}' --as-of '2026-08-24T18:59:00+02:00'
python scripts/council_kernel.py freshness --rows-json '[...]' --as-of '2026-08-24T18:59:00+02:00'
python scripts/council_kernel.py contradiction --claims-json '[...]'
python scripts/council_kernel.py independence-grade --memos-json '[...]'
python scripts/council_kernel.py base-rate --rows-json '[...]' --decision-type market_entry
python scripts/council_kernel.py validity --decision-json '{...}' --dependencies-json '[...]' --as-of '2026-08-24T18:59:00+02:00'
python scripts/council_kernel.py forecast-score --forecasts-json '[...]'
python scripts/council_kernel.py portfolio --decisions-json '[...]' --capacities-json '{...}'
python scripts/council_kernel.py handoff --kind legal --decision-json '{...}' --issue-json '{...}'
python scripts/council_kernel.py tool-authority --action-json '{...}'
```

Zachowaj też v4 commands: `profile`, `route`, `legal`, `select`, `rank`, `calibrate`, `sanitize`, `key`, `mode`, `budget`, `threshold`, `coverage`, `crux`, `consensus`, `minority`, `confidence`, `voi`, `stop`, `specialists`, `missing`, `experiment`, `snapshot`, `gate`, `regime`, `due-reviews`, `info-gain`, `framework-utility`, `health`, `provenance`, `consensus-patterns`, `eval-compare`.

## Referencje

Czytaj tylko potrzebne:

- `decision-contract.md`, `modes.md`, `experts.md`, `protocol.md` — core workflow,
- `internal-context.md`, `knowledge-routing.md`, `capability-packs.md` — private/context routing,
- `source-authority.md`, `source-registry.json`, `freshness.md`, `evidence-policy.md` — always-current evidence,
- `legal-risk.md`, `tool-authority.md`, `human-escalation.md` — gates i authority,
- `assumptions.md`, `frameworks.md`, `experiments.md` — reasoning/test logic,
- `living-decisions.md`, `notion-memory.md` — validity/watch/memory,
- `forecasting.md`, `portfolio.md` — learning/portfolio,
- `health.md`, `evaluation.md`, `output-contract.md` — QA, evals i output.
