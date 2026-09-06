# Source registry

Spis: 1. Reguły ogólne · 2. Product/repo · 3. CometWeb Insight · 4. Vault GTM/brand · 5. CRM · 6. Notion · 7. Gmail/Calendar/Contacts · 8. Social/public web · 9. Pliki użytkownika · 10. Fallbacki

## 1. Reguły ogólne

- Najpierw ustal system of record dla konkretnego claimu, dopiero potem pobieraj dane.
- `authority` opisuje rolę źródła, nie jakość techniczną connectora.
- `freshness` i `authority` są niezależne. Świeża notatka robocza nie przebija starszej, nadal obowiązującej decyzji kanonicznej.
- Nie traktuj braku wyniku wyszukiwania jako dowodu braku zjawiska.

Sugerowane poziomy `authority`: `system_of_record`, `canonical`, `primary`, `secondary`, `fallback`.

## 2. Product / repo

Źródła:

1. przypięty release/CI/deploy artifact, jeśli pytanie dotyczy produkcji lub release,
2. aktualny GitHub repo/branch/commit,
3. lokalny checkout, gdy wiadomo, że jest aktywnym źródłem pracy,
4. dokumentacja/Notion jako intencja, nie dowód implementacji.

Dla lokalnego snapshotu użyj `scripts/repo_snapshot.py`. Registry repo znajduje się w `references/repos.txt`.

Nie trzymaj w skillu na stałe nazwy aktualnego deployment brancha. Jeżeli jest to materialne, pobierz ją z aktualnej konfiguracji deploy/AGENTS/CI albo oznacz jako niezweryfikowaną.

## 3. CometWeb Insight

Jeśli dostępny jest connector CometWeb Insight, używaj go do aktualnych:

- projektów,
- module findings,
- score history,
- tasks,
- crawl runs,
- reports.

Nie używaj Insight jako źródła prawdy o kodzie repo ani jako zastępstwa dla release artifactu.

## 4. Vault GTM / marka

Domyślny root, jeśli lokalny filesystem jest dostępny:

`$COMETWEB_ROOT/<COMETWEB_GTM_ROOT>/`

Hierarchia ogólna:

1. `DECISIONS.md` — zatwierdzone decyzje,
2. `STATUS.md` — bieżący status,
3. kanoniczny dokument tematu,
4. wiki/notatki/drafty — kontekst pomocniczy.

Mapa tematyczna:

| Temat | Wzorzec / plik |
| --- | --- |
| decyzje | `DECISIONS.md` |
| First Principles / material decision input | `cometweb/strategia/First Principles.md` (D-028) |
| decision trace | `governance/decision-trace.md` |
| legacy decision-candidate aliases | `governance/decision-candidate-aliases.json` |
| bieżący status | `STATUS.md` |
| GTM | `cometweb/strategia/GTM Master*` |
| ICP / design partners | `cometweb/strategia/ICP.md` |
| pricing | `cometweb/strategia/Pricing Governance.md` |
| roboczy pipeline/export | `cometweb/sprzedaz/CRM_Agencje.md` |
| cold email SOP | `osobiste/procedury/SOP_Cold_Email_Agencja.md` |
| pilot queue | `boardroom/klienci/pilot-queue.md` |
| client register | `boardroom/klienci/register.json` |
| personal brand canon | `osobiste/marka/profil_osobisty.md`, `osobiste/marka/kanaly_publiczne.md` |
| public claims | `claims/evidence-register.json` |

Dokument z `status: historical-*`, `draft`, `archive` lub równoważnym oznaczeniem nie jest bieżącym source of truth, chyba że użytkownik jawnie prosi o historię.

Dla materialnej nowej decyzji produktowej, GTM, pricingowej, packagingowej lub portfelowej pobierz `First Principles.md` jako canonical decision-input obok właściwego systemu of record. Nie traktuj go jako dowodu bieżącego stanu. Jeżeli dokument doradczy używa provisional `D-xxx`, sprawdź `governance/decision-candidate-aliases.json`; tylko nagłówki w `DECISIONS.md` alokują kanoniczne identyfikatory decyzji.

Nie zapisuj w skillu listy "znanych luk na dziś". Takie luki mają być pobierane z aktualnych źródeł lub poprzedniego envelope.

## 5. CRM / pipeline

Dla stanu sprzedaży użyj rzeczywistego CRM będącego systemem rekordowym. Jeżeli aktualnie jest nim Twenty CRM, traktuj Twenty jako `system_of_record`.

Jeśli connector do właściwego CRM jest niedostępny:

- ustaw źródło CRM jako `unavailable`,
- roboczy plik `CRM_Agencje.md` może być `secondary` lub `fallback`,
- Notion nie staje się automatycznie źródłem pipeline'u.

Nie zastępuj Twenty przez HubSpot ani inny CRM bez jawnego potwierdzenia, że migracja/system of record się zmienił.

## 6. Notion

Używaj connectora Notion do:

- decyzji/notatek, jeśli to właśnie Notion jest wskazanym kanonem,
- planów, tasków i next steps,
- stron projektowych potrzebnych do danego celu.

Pobieraj tylko konkretne strony. Nie dumpuj całego workspace. W odpowiedzi zwracaj tytuł/ID/referencję i krótkie streszczenie, nie pełną prywatną treść.

Jeśli inny system jest systemem rekordowym (np. CRM, GitHub, release artifact), Notion ma niższy autorytet w tej domenie.

## 7. Gmail / Calendar / Contacts

Używaj tylko gdy cel wymaga aktualnej komunikacji lub przygotowania do spotkania.

- Gmail: ostatni istotny wątek z prospektem/partnerem/klientem, nie szeroki przegląd inboxa.
- Calendar: konkretne spotkanie, czas, uczestnicy i opis.
- Contacts: rozwiązywanie tożsamości uczestników/odbiorców.

Nie czytaj komunikacji prywatnej niezwiązanej z celem.

## 8. Social media i public web

Preferencja:

1. zalogowana przeglądarka / odpowiedni connector/plugin, jeśli dostępny,
2. oficjalny publiczny profil/strona,
3. web search/cache jako fallback.

Dla sociali zapisuj, czy dane są `live` czy `search_cache`. Nie twierdź, że liczby/followers/posts są aktualne, jeśli pochodzą wyłącznie z indeksu wyszukiwarki.

Dla CometWeb strony live są źródłem prawdy o tym, co aktualnie widzi użytkownik. Dokument strategii nie dowodzi, że zmiana została wdrożona na stronie.

## 9. Pliki użytkownika

Jeżeli użytkownik dołączył brief, research, PDF, arkusz lub inny plik dotyczący celu, traktuj go jako jawne źródło wejściowe. Zachowaj jego referencję i nie mieszaj jego treści z danymi live bez oznaczenia provenance.

## 10. Fallbacki

| Brak | Fallback | Degradacja |
| --- | --- | --- |
| lokalne repo | GitHub connector | brak dirty/local-only state |
| GitHub connector | public GitHub/web, jeśli repo publiczne | możliwe opóźnienie/cache |
| właściwy CRM | eksport/kanoniczny plik roboczy | `authority_gap` |
| Notion | vault/załączone pliki | brak workspace-only context |
| live browser social | oficjalny profil/web search | `access=fallback`, freshness może być `unknown` |
| live website blocked | alternate fetch/web cache | nie potwierdza aktualnego UI |

Każdą degradację wpisuj do `gaps` w ContextEnvelope.
