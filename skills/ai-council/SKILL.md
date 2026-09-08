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

Wybierz najmniejszy profil, który chroni decyzję. Szczegóły budżetów: `references/modes.md`.

| Profile | Kiedy | Ścieżka |
| --- | --- | --- |
| `LIGHT` | mała, odwracalna decyzja; użytkownik chce szybki sanity check | Decision Contract → 2–3 perspektywy → evidence sanity → key risks → `GO` / `TEST` / `DEFER` (bez forecasting/portfolio/living-decision machinery) |
| `STANDARD` | domyślny dla materialnych decyzji | blind round → evidence/falsifier → gates → minority → Decision Snapshot |
| `DEEP` | wysoki lock-in, regulacja, multi-system | pełny workflow poniżej (forecasting, portfolio, living decision, champion/challenger) |

Nie ładuj DEEP cognitive path dla LIGHT. Kernel `plan` nadal wybiera tryb, jeśli użytkownik go nie wymusi.

## Workflow decyzji

1. Ustal dokładne `as_of` w lokalnej strefie użytkownika i zbuduj canonical Decision Contract przez `contract`. Uzupełnij tylko znane dane. Przeczytaj `references/decision-contract.md`.
2. Dla materialnych internal claims uruchom `context-route`; wybierz system-of-record według `references/internal-context.md`.
3. Uruchom `plan`. Kernel wybiera `Council Mode` (`LIGHT`≈FAST, `STANDARD`, `DEEP`), budżet, role, frameworki, critical evidence areas i wymagane temporal stages, chyba że użytkownik wymusi tryb. Dla `LIGHT` przejdź skróconą ścieżkę z tabeli powyżej i pomiń kroki forecasting/portfolio/living-decision chyba że risk surface wymusi gate.
4. Jeśli archetyp ma sensowne historyczne analogie, zbuduj outside view przez `base-rate` **bez czytania historycznych verdictów blind ekspertom**. Base rate jest priorem dla późniejszej syntezy, nie informacją dla blind round.
5. Pobierz prywatną wiedzę per role/capability pack. Użyj `references/knowledge-routing.md` i `references/capability-packs.md`.
6. Wykonaj blind round adviserów i relewantnych specialistów. Nie odczytuj Decision Memory przed zakończeniem wszystkich blind memos.
7. Wymagaj w memo: vote, confidence, thesis, claims, assumptions, risks, strongest falsifier, what changes my mind, evidence needed oraz provenance lane.
8. Zbuduj Assumption Ledger (`importance × uncertainty`). Przeczytaj `references/assumptions.md`.
9. Dopiero teraz odczytaj Decision Memory. Rankuj tylko ograniczoną liczbę analogii i kalibruj na rozliczonych decyzjach z odpowiednią sample strength.
10. Wykonaj rebuttals i `crux`. Double-crux ma być falsyfikowalnym założeniem.
11. Dla każdego materialnego claimu określ typ i authority przez `source-authority`. Przeczytaj `references/source-authority.md`.
12. Zbierz Live Evidence zgodnie z budżetem. Dla prawa/regulacji/security/vendor policy/aktualnych cen używaj bieżących primary/official sources.
13. Uruchom `temporal` dla materialnych current claims, a następnie `freshness` dla całego materialnego evidence set. Przeczytaj `references/freshness.md`.
14. Uruchom `coverage` oraz `contradiction`. Dla top claims wykonaj osobny support search i contradiction search. Critical unresolved contradiction blokuje decision readiness.
15. Jeśli wymagany, wykonaj premortem z ownerem, leading indicator, mitigation i contingency.
16. Uruchom gatekeeperów z planera. Legal kieruj przez `legal` i `references/legal-risk.md`; Security/Privacy/Financial Risk/Responsible AI/Reputation uruchamiaj wg risk surface.
17. Uruchom `consensus` i `independence-grade`. Raportuj Raw Consensus, Adjusted Consensus i realną klasę niezależności `I0–I4`; liczba agentów nie jest liczbą niezależnych ekspertów.
18. W STANDARD/DEEP uruchom `minority`; zachowaj materialny independent dissent.
19. Uruchom Red Team i Evidence Judge. Chairman może zobaczyć tylko accepted **i temporally admissible** material evidence.
20. Wykonaj counterfactual/best-alternative/no-action/timing zgodnie z trybem i ryzykiem.
21. Policz `voi`, gdy dodatkowy research/test ma koszt. Po każdej dodatkowej rundzie uruchom `stop`; unresolved mandatory gate/freshness blocker nie pozwala zakończyć procesu.
22. Dla DEEP/high-stakes utwórz 1–5 rozstrzygalnych forecasts, jeśli mają wartość. Użyj `references/forecasting.md`.
23. Jeśli decyzja konkuruje o zasoby z innymi decyzjami/projektami, uruchom `portfolio`. Przeczytaj `references/portfolio.md`.
24. Zbuduj confidence decomposition: thesis, evidence, execution oraz relewantne finance/legal/security/privacy/timing.
25. Chairman proponuje `GO | NO-GO | TEST | DEFER`, recommended option/allocation/sequence i reasoning map.
26. Policz Required Confidence i uruchom `gate` z gate statuses, freshness status i human approval state. `BLOCK` nie jest przegłosowywany; `COUNSEL_REQUIRED` → DEFER.
27. Jeśli potrzebna jest kwalifikowana opinia, wygeneruj `handoff` packet według `references/human-escalation.md`.
28. Dla `TEST` zbuduj pełny Experiment Spec według `references/experiments.md`.
29. Przed zewnętrznym write/send/destructive/financial action uruchom `tool-authority`; T3/T4 wymagają explicit human approval. Przeczytaj `references/tool-authority.md`.
30. Utwórz immutable Decision Snapshot z wersjami Council/Kernel i temporal metadata; policz Snapshot Hash.
31. Zbuduj/odśwież Decision Validity Overlay przez `validity`. Dla materialnych zależności utwórz Watch Dependencies zgodnie z `references/living-decisions.md`.
32. Sformatuj wynik według `references/output-contract.md`.
33. Zapisz Decision Memory lifecycle `Writing → Complete`; Decision oznacz `Complete` jako ostatni rekord.

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
