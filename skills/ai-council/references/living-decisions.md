# Living decisions v5

## Immutable snapshot vs validity overlay

Decision Snapshot jest historycznym zapisem tego, co było wiadomo w momencie decyzji. Nigdy go nie przepisuj po zmianie świata.

Obok snapshotu utrzymuj mutable `Decision Validity Overlay`:

- `VALID` — brak materialnej zmiany,
- `WATCH` — pojawił się sygnał wymagający obserwacji/revalidacji,
- `STALE` — materialne evidence straciło ważność,
- `REOPEN` — materialna zależność zmieniła się na tyle, że decyzję trzeba ponownie rozpatrzyć,
- `SUPERSEDED` — decyzja została zastąpiona nowszą decyzją.

Uruchamiaj `validity` przy re-checku istniejącej decyzji.

## Watch dependencies

Notion: bind `watch_dependencies` via `~/.config/cometweb/ai-council-notion.json` (see example).

Twórz watch tylko dla zależności, których zmiana może zmienić verdict, ranking opcji, gate albo execution plan. Przykłady:

- nowa wersja prawa/guidance,
- security advisory dotyczące używanej zależności,
- cena/polityka konkurenta,
- MRR/churn/runway/capacity threshold,
- vendor/API policy,
- repo/dependency version,
- customer evidence threshold.

Każdy watch wiąż z Assumption Key, jeśli to możliwe. `Triggered` o wysokiej materialności prowadzi do `REOPEN`, nie do cichego nadpisania starej decyzji.

## Revalidation

Raportuj `Current As Of`, `Current Validity`, powód i liczbę watch triggerów. Revalidacja może być częściowa: sprawdzaj tylko zmienione/materialne obszary, ale ponownie uruchom binding gates, których podstawa się zmieniła.
