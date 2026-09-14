# Source registry

Spis: 1. Reguły · 2. Governance/vault · 3. Product/repo · 4. Insight · 5. Planning/Notion · 6. CRM · 7. Communications · 8. Public web · 9. Files · 10. Fallbacks

## 1. Reguły ogólne

- Najpierw claim/domain → system of record, potem retrieval.
- Authority opisuje rolę źródła dla konkretnego claimu, nie prestiż systemu.
- Freshness i authority są niezależne.
- Brak search hitu nie dowodzi braku.
- Nie public-searchuj faktu wewnętrznego, jeśli istnieje system rekordowy.

Authority: `system_of_record | canonical | primary | secondary | fallback`.

Profile źródeł są definiowane w `source-registry.json` → `profiles.*.preferred_source_groups`. Planner odczytuje rejestr; przy wielu trafieniach zwraca `candidates` i `ambiguous`. `primary` jest pierwszą regułą dopasowania, nie wynikiem rankingu. CRM pozostaje zewnętrznym wiązaniem runtime.

## 2. Governance i vault GTM

Jeśli `gtm-cometweb` jest dostępny, preferuj:

1. `DECISIONS.md` — binding decisions / supersession.
2. `STATUS.md` — bieżący stan portfolio i granice claimów.
3. kanoniczny dokument domenowy.
4. wiki/notatki/drafty — kontekst pomocniczy.

Mapa:

| Temat | Kanoniczny wzorzec |
| --- | --- |
| First Principles | `cometweb/strategia/First Principles.md` |
| decyzje | `DECISIONS.md` |
| decision trace | `governance/decision-trace.md` |
| adoption review | `governance/first-principles-adoption.json` |
| bieżący status | `STATUS.md` |
| GTM | `cometweb/strategia/GTM Master*` |
| ICP / design partners | `cometweb/strategia/ICP.md` |
| pricing | `cometweb/strategia/Pricing Governance.md` |
| cold email SOP | `osobiste/procedury/SOP_Cold_Email_Agencja.md` |
| pilot queue | `boardroom/klienci/pilot-queue.md` |
| client register | `boardroom/klienci/register.json` |
| public claims | `claims/evidence-register.json` |

Historyczne/advisory candidate IDs nie są binding decyzjami. Tylko kanoniczny `DECISIONS.md` alokuje `D-xxx`.
Jeśli istnieje `governance/decision-candidate-aliases.json`, użyj go do rozróżnienia legacy labels od decyzji.

## 3. Product / repo

Claim-specific kolejność:

1. przypięty release/CI/deploy artifact — release/deploy claims,
2. aktualny GitHub default branch / commit / PR — implementation claims,
3. aktywny lokalny checkout — dirty/local work only,
4. docs/Notion — intent/planning, nie implementation proof.

Lokalny snapshot: `scripts/repo_snapshot.py`; repo registry: `references/repos.txt`.

Ścieżki do lokalizacji prywatnych są w commitowanym rejestrze placeholderami. Realne
wartości trzymaj obok, w nieśledzonych `references/repos.local.txt` i
`references/source-registry.local.json` — oba są wczytywane jako nakładka, więc lokalny
checkout widzi całość, a publikowane drzewo nie ujawnia układu prywatnego repozytorium.
Nie inferuj runtime z samego kodu.

## 4. CometWeb Insight

Connector Insight może być SoR dla live projektów, findings, score history, tasks, crawl runs i reports. Nie jest
SoR dla kodu repo, CI, deployu ani publicznej strony marketingowej.

## 5. Planning / Notion

Notion używaj do planów, tasków, project pages, meeting notes i next steps, gdy jest właściwą warstwą. Nie
traktuj statusu Notion jako dowodu `implemented`, `verified`, `shipped` ani `outcome`.

## 6. CRM / pipeline

Użyj faktycznego CRM będącego systemem rekordowym. Jeśli obecnie jest nim Twenty, a connector nie jest dostępny:

- ustaw CRM jako `unavailable`,
- użyj jawnego exportu/register jako `secondary|fallback`, jeśli istnieje,
- nie awansuj HubSpot/Notion do SoR bez potwierdzonej migracji.

## 7. Gmail / Calendar / Contacts

Tylko gdy cel wymaga komunikacji lub spotkania:
- Gmail: ostatni istotny wątek, nie szeroki inbox dump.
- Calendar: konkretne spotkanie/czas/uczestnicy/opis.
- Contacts: resolution osoby/odbiorcy.

## 8. Public web / live website

Dla aktualnego publicznego stanu strony preferuj live page/official source. Search cache jest fallbackiem i ma
freshness `unknown|aging`, jeśli nie ma bieżącego potwierdzenia.

## 9. Files

Załączone lub zapisane pliki wybrane przez użytkownika są jawnie dozwolonym źródłem wejściowym. Zachowaj
provenance i nie mieszaj ich z live state bez oznaczenia różnicy wersji/czasu.

## 10. Fallbacki

| Brak | Fallback | Wymagana degradacja |
| --- | --- | --- |
| lokalne repo | GitHub connector | brak dirty/local-only state |
| GitHub connector | public GitHub/web dla publicznego repo | cache/freshness gap |
| właściwy CRM | export/register | `authority_gap` |
| Notion | vault/attached docs | brak workspace-only plan state |
| live website | official cached/public source | nie potwierdza live UI |
| First Principles source | decision log / pointer only | `governance_gap`; nie odtwarzaj doktryny z pamięci |

Każdą degradację zapisz w `gaps`.
