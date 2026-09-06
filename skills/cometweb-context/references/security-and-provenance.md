# Security and provenance

## Klasyfikacja

- `public` — może być użyte publicznie po zwykłej weryfikacji.
- `internal` — operacyjny materiał firmowy, nie publikuj bez potrzeby.
- `confidential` — vault GTM, CRM, prywatne maile, notatki klientowskie, nie cytuj szeroko i nie przenoś do publicznych repo.
- `restricted` — sekrety, tokeny, credentiale, prywatne klucze, configi z hasłami. Nie odczytuj, jeśli nie jest to absolutnie wymagane; ten skill z definicji nie powinien ich potrzebować.

## Minimal disclosure

- Streszczaj prywatne dokumenty zamiast kopiować je w całości.
- Do downstream skilla przekazuj tylko fakty potrzebne do celu.
- Nie przekazuj danych osobowych z komunikacji, jeśli nie są potrzebne do zadania.
- Nie umieszczaj ścieżek lokalnych, tokenów ani surowych maili w materiałach publicznych.

## Provenance rules

Dla materialnego faktu zachowaj:

- źródło i identyfikator,
- sposób dostępu,
- czas pobrania,
- datę obowiązywania, jeśli dostępna,
- autorytet źródła,
- sensitivity,
- status świeżości.

Nie oznaczaj `fresh` wyłącznie dlatego, że dane zostały właśnie pobrane. `retrieved_at` oznacza czas pobrania; `effective_at` oznacza stan, którego dane dotyczą.

## Freshness heuristics

Domyślne heurystyki, jeśli system nie ma własnego SLA:

- live website / live connector: `fresh` w tej turze,
- repo HEAD / CI status: `fresh` w tej turze,
- CRM record: `fresh` jeśli connector zwraca bieżący rekord; inaczej `unknown`,
- decyzje biznesowe: ocena freshness zależy od statusu/valid_from/superseded_by, nie od wieku pliku,
- search cache / indeks: `unknown` lub `aging`, nigdy automatycznie `fresh`.

## Write boundary

`cometweb-context` jest read-only.

Nie:

- commituj/pushuj,
- edytuj Notion,
- zmieniaj CRM,
- wysyłaj/draftuj maili,
- aktualizuj kalendarza,
- publikuj postów,
- uruchamiaj deployu.

Jeżeli użytkownik prosi również o write, zakończ ContextEnvelope i przekaż zadanie do właściwego skilla/toola z jego własnymi zasadami potwierdzeń.
