---
name: cometweb-context
description: Builds a fresh, provenance-aware context snapshot for CometWeb before another skill makes product, strategy, GTM, outreach, content, or advisory decisions. Use when the task depends on current state across multiple sources, when the user asks to refresh context, check what changed, prepare for a meeting/review, or when an orchestrated CometWeb workflow needs a ContextEnvelope. Select only necessary sources, record freshness, authority, gaps and conflicts, and hand context to the next specialist. Do not use for simple conceptual questions or when one direct source is sufficient.
---

# CometWeb Context

Działaj jako **read-only context gateway**. Zbieraj minimalny, świeży i audytowalny kontekst potrzebny do następnego kroku. Nie zastępuj skilla domenowego i nie wydawaj jego decyzji.

## Twardy kontrakt

1. Pobieraj tylko źródła potrzebne do bieżącego celu.
2. Raportuj wyłącznie dane faktycznie odczytane w tej turze albo jawnie oznaczone jako odziedziczony baseline.
3. Dla każdego istotnego faktu zachowaj źródło, czas pobrania, autorytet źródła i poziom świeżości.
4. Nie scalaj sprzecznych źródeł po cichu. Zapisz konflikt i wskaż źródło nadrzędne tylko wtedy, gdy registry definiuje hierarchię.
5. Nie mutuj repo, Notion, CRM, maila, kalendarza, stron ani vaulta. Ten skill tylko czyta i przekazuje kontekst.
6. Nie wykonuj downstreamowej strategii, priorytetyzacji, audytu, decyzji Council ani wysyłki outboundu.
7. Nie czytaj sekretów, tokenów, plików konfiguracyjnych z credentialami ani nie publikuj treści oznaczonej jako prywatna/wewnętrzna.

Szczegóły źródeł i hierarchii: [references/source-registry.md](references/source-registry.md).  
Zasady provenance i bezpieczeństwa: [references/security-and-provenance.md](references/security-and-provenance.md).  
Kontrakt wyjścia: [references/context-envelope.md](references/context-envelope.md).

## Workflow

### 1. Ustal tryb i profil

Najpierw określ najmniejszy sensowny zakres:

- `targeted` — jedno konkretne pytanie lub jeden obszar; zwykle 1-2 grupy źródeł.
- `standard` — bieżący kontekst do pracy domenowej; zwykle 2-4 grupy źródeł.
- `delta` — użytkownik pyta "co się zmieniło"; wymagany jawny baseline.
- `full` — boardroom/weekly review/pełny refresh; używaj tylko po wyraźnej prośbie.

Jeśli lokalne uruchamianie skryptów jest dostępne, możesz użyć:

```bash
python3 scripts/context_plan.py "<cel użytkownika>" --json
```

Skrypt jest planerem pomocniczym, nie źródłem prawdy. Jeśli cel jest oczywisty, dobierz profil bez uruchamiania go.

Profile i domyślne źródła:

| Profil | Minimalny zestaw |
| --- | --- |
| product / roadmap / release context | repo/GitHub + CometWeb Insight + kanoniczny status/decisions + First Principles dla materialnych nowych decyzji; Notion tylko gdy potrzebne |
| GTM / pricing / positioning | decisions + First Principles + dokument kanoniczny tematu + live website; CRM gdy stan komercyjny ma znaczenie |
| outreach / design partner | CRM + ostatnia komunikacja, jeśli istnieje + ICP/SOP + strona/profil prospekta |
| personal brand / content | brand canon + evidence register + live public profiles/website + ostatnie istotne treści |
| meeting prep | Calendar + Contacts + CRM/komunikacja + dokumenty dotyczące rozmowy |
| weekly / boardroom | pełny refresh systemów rekordowych + jawny delta baseline |
| public claim verification | evidence register + pierwotne źródło claimu + miejsce publikacji |

Nie pobieraj sociali do roadmapy produktu, repo do prostego posta ani pełnego vaulta do jednego pytania.

### 2. Wykryj dostępne źródła

Przeczytaj odpowiednią sekcję w `references/source-registry.md`.

Preferuj w tej kolejności:

1. system of record / kanoniczne źródło,
2. bezpośredni connector lub lokalny artefakt,
3. źródło live/publiczne,
4. fallback o niższej wiarygodności.

Nie hard-code'uj nazw MCP typu `mcp__...`. Użyj aktualnie dostępnego connectora/toola dla GitHub, Notion, Gmail, Calendar, Contacts, CometWeb Insight, Files lub web. Jeśli źródło nie jest dostępne, wpisz `unavailable`; nie zastępuj go innym systemem bez oznaczenia degradacji.

### 3. Zbierz repo snapshot tylko gdy potrzebny

Jeśli masz lokalny dostęp do repozytoriów, uruchom:

```bash
python3 scripts/repo_snapshot.py --json
```

Root wybieraj kolejno z `COMETWEB_ROOT`, `COMETWEB_CENTRUM`, a na końcu `~/Github/CometWeb`. Lista repo jest w `references/repos.txt` i może być nadpisana argumentami skryptu.

Jeśli lokalny checkout jest mirror/stale albo niedostępny, preferuj GitHub connector dla aktualnego stanu. Nie traktuj dirty tree jako dowodu stanu produkcji.

### 4. Zbieraj z provenance

Dla każdej użytej grupy źródeł zapisuj co najmniej:

- `source_id`
- `source_type`
- `authority`
- `retrieved_at`
- `effective_at` jeśli źródło podaje datę obowiązywania
- `freshness`: `fresh | aging | stale | unknown`
- `access`: `live | local | connector | cached | fallback`
- `sensitivity`: `public | internal | confidential | restricted`
- krótki `summary`
- `evidence_ref` lub identyfikator pozwalający wrócić do artefaktu

Nie używaj daty modyfikacji pliku jako automatycznego `effective_at` decyzji biznesowej.

### 5. Rozwiąż konflikty i luki

- Użyj hierarchii per domena z `source-registry.md`.
- Nowsze nie zawsze znaczy nadrzędne; decyzja kanoniczna może przeważać nad późniejszą notatką roboczą.
- Jeśli dwa źródła o podobnym autorytecie są sprzeczne, zachowaj oba i wpisz `unresolved_conflict`.
- Jeśli authoritative source jest niedostępny, nie awansuj fallbacku do poziomu authoritative. Oznacz `authority_gap`.
- Dokumenty historyczne, drafty i cache nie mogą samodzielnie tworzyć bieżącego stanu.
- Przy materialnej nowej decyzji pobierz kanoniczne `cometweb/strategia/First Principles.md` (D-028) jako warstwę wejściową. Jeśli historyczny advisor używa kolidującego provisional `D-xxx`, rozwiąż alias przez `governance/decision-candidate-aliases.json`; nie awansuj kandydata do decyzji.

### 6. Delta tylko wobec jawnego baseline'u

Dla `delta` porównuj bieżący snapshot wyłącznie z:

- poprzednim `ContextEnvelope`,
- snapshotem/systemowym rekordem z jawnym timestampem,
- baseline'em wskazanym przez użytkownika.

Jeśli baseline'u nie ma, ustaw `baseline_status: unavailable` i podaj bieżący stan bez wymyślonego "vs poprzednio".

### 7. Gate dla publicznych claimów

Przed użyciem liczby, wyniku, case study lub obietnicy w materiale publicznym:

1. sprawdź `claims/evidence-register.json` albo aktualny równoważny rejestr,
2. potwierdź `public_use` / status dopuszczenia,
3. zachowaj źródło i freshness,
4. jeśli brak pokrycia, wpisz claim do `blocked_public_claims`.

Ten skill nie naprawia claimu i nie wymyśla zastępczej liczby.

### 8. Emituj `ContextEnvelope`

Zwróć dwa poziomy:

1. krótki raport dla użytkownika `Stan na <timestamp>`,
2. ustandaryzowany `ContextEnvelope` według `references/context-envelope.md`.

Jeśli envelope został zapisany jako JSON, zweryfikuj:

```bash
python3 scripts/validate_context_envelope.py path/to/context-envelope.json
```

### 9. Handoff

- Jeśli użytkownik chciał tylko refresh/stanu: zakończ na envelope.
- Jeśli skill jest krokiem orkiestratora: przekaż envelope do następnego specjalisty jako zależność.
- Jeśli użytkownik chce również pracę właściwą, wskaż właściwy kolejny skill, ale nie wykonuj jego kontraktu pod nazwą `cometweb-context`.

Typowe handoffy:

- `repo-to-roadmap` / `product-operator` — stan produktu i priorytety,
- `release-readiness` — tylko po przypięciu RC/build/environment,
- `design-partner-finder` — discovery/qualification,
- `cold-email` — outbound copy po zebraniu kontekstu prospekta,
- `content-strategy` / `social` / `copywriting` — treści i marka,
- `ai-council` — dopiero gdy istnieje materialna decyzja i odpowiednie evidence.

## Domyślny format odpowiedzi

```text
Stan na <ISO-8601>
- Tryb/profil: ...
- Sprawdzone: ...
- Niedostępne / zdegradowane: ...
- Najważniejsze delty: ... / baseline unavailable
- Konflikty i luki: ...
- Public claims blocked: ...

Handoff
- recommended_next_skill: ...
- context_snapshot_id: ...
- constraints: ...
```

Nie wklejaj do odpowiedzi pełnych prywatnych dokumentów, maili ani stron Notion. Streszczaj minimalnie i zachowuj referencje.
