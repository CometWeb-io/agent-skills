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

## Kernel 5.0.1 — brak obserwacji nie oznacza stabilności

`watch` rozdziela `observation_status: OBSERVED | UNKNOWN`. Dla braku danych, nieznanego operatora, błędnej liczby albo procentowej zmiany względem zera zwraca `triggered: null`, nie `false`. Nie konwertuj tego pola automatycznie przez `bool()`.

Operatory liczbowe przyjmują skończone liczby JSON. `changed` porównuje zapis JSON, więc zachowuje różnice typów, także `1` i `1.0`. Schemat danych dostawcy powinien być stabilny; kernel nie normalizuje tych obserwacji po cichu.

Nieznana obserwacja lub brak jakichkolwiek watch dependencies prowadzą do `WATCH`, nie do `VALID`. Jawnie wykryta zmiana o wysokiej materialności prowadzi do `REOPEN`, nawet gdy inne evidence jest stare. Raport zachowuje wtedy wszystkie sygnały i dotknięte założenia. `STALE`, `WATCH` i `REOPEN` wymagają rewalidacji; niepoprawny termin następnej kontroli także wymaga przeglądu.

Nie jest to proces monitorujący w tle ani uwierzytelnianie snapshotu. `VALID` dotyczy wyłącznie przekazanych obserwacji, nie kompletności wszystkich zależności świata. [Pozostałe granice](kernel-admission.md).
