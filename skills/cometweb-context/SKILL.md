---
name: cometweb-context
description: Builds a fresh, provenance-aware context snapshot for CometWeb and its active projects before product, portfolio, strategy, GTM, pricing, outreach, meeting, content, or advisory work. Use when the request depends on current state across GitHub/repositories, Notion, CometWeb Insight, CRM/communications, files, live CometWeb surfaces, or multiple CometWeb projects such as Insight, CometBase, CometPen, CometLens/Extensions, cometweb.io, agent-skills, RankProof, and research. Also use for "what changed", full/portfolio refreshes, meeting prep, and as a preflight for Product Operator, AI Council, Repo to Roadmap, or Skill Orchestrator. Include First Principles governance for material product/GTM/pricing/portfolio decisions. Do not use for simple conceptual questions or when one direct authoritative source is sufficient.
---

# CometWeb Context

## Quality preflight

Read [runtime evidence and safety](references/runtime-policy.md) once per task and
[domain acceptance and currentness](references/quality-and-currentness.md) before
applying the workflow. Use only relevant sources; do not load every reference or
browse unrelated news. Preserve the output protocol and report untested capabilities.

Działaj jako **read-only context gateway**. Zbieraj najmniejszy zestaw aktualnych, autorytatywnych źródeł potrzebny do następnego kroku. Nie zastępuj skilla domenowego i nie wydawaj jego decyzji.

## 1. Twardy kontrakt

1. Najpierw ustal **claim/domain → system of record**, dopiero potem pobieraj dane.
2. Raportuj tylko dane faktycznie odczytane w tej turze albo jawnie oznaczony baseline.
3. Dla materialnych faktów zachowaj: źródło, locator/reference, access, authority, retrieved/effective time, freshness i sensitivity.
4. Nie scalaj sprzecznych źródeł po cichu. Zachowaj konflikt i rozstrzygaj wyłącznie według claim-specific authority.
5. Nie mutuj repo, Notion, CRM, maila, kalendarza, stron ani vaulta.
6. Nie wykonuj downstreamowej strategii, priorytetyzacji, audytu, Council verdictu ani outboundu.
7. Nie czytaj sekretów/credentiali. Nie przenoś prywatnych danych do publicznego web search.
8. Brak wyniku ≠ dowód braku. Brak authoritative source → `gap`, nie zgadywanie.
9. Nie traktuj roadmapy/Notion jako dowodu implementacji, merge jako deploy, deploy jako outcome.
10. Gdy materialna decyzja wymaga First Principles, załaduj doktrynę jako governance input, ale nie traktuj jej jako dowodu bieżącego stanu produktu.

Źródła i authority: [references/source-registry.md](references/source-registry.md).  
Security/provenance: [references/security-and-provenance.md](references/security-and-provenance.md).  
Envelope: [references/context-envelope.md](references/context-envelope.md).  
User output: [references/output-contract.md](references/output-contract.md).  
Decision preflight: [references/decision-preflight.md](references/decision-preflight.md).

## 2. Ustal tryb i profil

Użyj najmniejszego sensownego zakresu.

**Tryby**
- `targeted` — jedno pytanie / jeden obszar.
- `standard` — typowy preflight do pracy domenowej.
- `delta` — porównanie z jawnym baseline'em.
- `full` — pełny portfolio/boardroom refresh tylko przy wyraźnym szerokim zakresie.

**Profile**
- `product` — jeden produkt/repo/release context.
- `portfolio` — kilka lub wszystkie projekty CometWeb + cross-project dependencies.
- `gtm` — positioning, pricing, packaging, ICP, GTM.
- `outreach` — design partner/prospect/outbound context.
- `brand` — marka/content/public surfaces.
- `meeting` — spotkanie z kontekstem osób, komunikacji i projektu.
- `weekly` — boardroom/weekly operating refresh.
- `claim-verification` — public claim + evidence/publication surface.
- `custom` — tylko jeśli żaden profil nie pasuje.

Jeśli execution jest dostępny, planner może pomóc:

```bash
python3 scripts/context_plan.py "<cel użytkownika>" --json
```

Planner nie jest źródłem prawdy. Nie uruchamiaj go, jeśli profil jest oczywisty.

## 3. Routing narzędzi i źródeł

Dobierz źródło do claimu, nie do wygody:

- **GitHub / repo** — implementation, branch, PR/commit, current repo docs, CI/release evidence.
- **CometWeb Insight connector** — live projects, findings, score history, tasks, crawl runs, reports; nie kod repo.
- **Notion** — plan, task, project/meeting notes, gdy Notion jest właściwą warstwą planowania; nie dowód implementacji.
- **CRM** — aktualny system rekordowy pipeline'u. Nie podmieniaj CRM na inny tylko dlatego, że connector jest dostępny.
- **Gmail / Calendar / Contacts** — tylko gdy komunikacja lub spotkanie jest materialne.
- **Files** — załączone/saved dokumenty wybrane przez użytkownika.
- **live website / web** — publiczny stan strony, aktualne dane zewnętrzne i źródła publiczne.
- **vault `gtm-cometweb`** — kanon strategii/decisions/status/claims/governance, jeśli dostępny.

Jeśli authoritative connector jest niedostępny, użyj najlepszego jawnego fallbacku i wpisz `authority_gap`. Nie udawaj równoważności.

## 4. First Principles preflight

Dla materialnych decyzji produktowych, portfolio, GTM, pricing, packaging, ICP, architektury, launchu lub publicznego materialnego claimu:

1. spróbuj odczytać `cometweb/strategia/First Principles.md` i właściwy wpis w `DECISIONS.md` (obecnie D-028, jeśli nadal obowiązuje),
2. oznacz governance status jako `loaded | unavailable`,
3. przekaż downstream constraint: pełny FP-6 albo fast path zgodnie z kanoniczną doktryną,
4. nie przeprowadzaj sam Council verdictu ani nie zapisuj FP TRACE.

Dla zwykłej mechanicznej realizacji wcześniejszej decyzji nie dokładaj governance theatre.

## 5. Zbieraj minimalny context set

### product
GitHub/repo + Insight jeśli dotyczy + `STATUS.md`/`DECISIONS.md`; Notion tylko gdy plan ma znaczenie.

### portfolio
Aktualny stan głównych repo + Notion/project planning + `STATUS.md` + `DECISIONS.md` + First Principles + Insight dla aktywnego produktu. Nie czytaj Gmaila/sociali bez konkretnej potrzeby.

### GTM / pricing / positioning
`DECISIONS.md` + kanoniczny dokument tematu + First Principles + live website; CRM tylko gdy decyzja zależy od pipeline/customer state.

### outreach / design partner
CRM + ostatnia istotna komunikacja + ICP/SOP + publiczna strona/profil prospekta.

### meeting
Calendar + Contacts + istotny CRM/mail + dokumenty dotyczące konkretnego spotkania.

### weekly / boardroom
Tylko systemy rekordowe potrzebne do bieżącego review; pełny zakres nie oznacza dumpu całych workspace'ów.

### public claim verification
Evidence register + primary source + publication surface. Brak public-use approval → `blocked_public_claims`.

## 6. Repo snapshot tylko gdy lokalny checkout naprawdę istnieje

Jeśli lokalny filesystem jest dostępny:

```bash
python3 scripts/repo_snapshot.py --json
```

Skrypt nie ujawnia lokalnych ścieżek domyślnie. Jeśli root nie istnieje, wynik ma wskazać fallback do bieżącego GitHub connectora. Nie traktuj brakującego lokalnego checkoutu jako braku repozytorium.

Lista repo: [references/repos.txt](references/repos.txt), rozszerzana o nieśledzony
`references/repos.local.txt`, jeśli istnieje.

## 7. Provenance, freshness i konflikty

Dla każdej użytej grupy źródeł zachowaj co najmniej:

`source_id · source_type · authority · access · retrieved_at · effective_at? · freshness · sensitivity · summary · evidence_ref`

Zasady:
- `retrieved_at` ≠ `effective_at`;
- repo HEAD/live connector może być świeży w tej turze, ale historyczna decyzja obowiązuje według statusu/supersession, nie wieku pliku;
- cache/search index nie jest automatycznie `fresh`;
- dwa autorytatywne źródła w konflikcie → `unresolved_conflict`, jeśli nie da się rozstrzygnąć claim-specific authority.

## 8. Delta tylko z realnym baseline'em

Baseline może być:
- poprzedni `ContextEnvelope`,
- datowany snapshot/system record,
- baseline wskazany przez użytkownika.

Jeśli go nie ma: `baseline.status=unavailable`; pokaż bieżący stan bez fikcyjnej delty.

## 9. Rozdziel output dla człowieka od handoffu maszynowego

**Szerokość retrievalu i długość odpowiedzi to dwie różne osie.** `full` oznacza pełny zakres źródeł, nie pełny dump do użytkownika.

Najpierw zbuduj pełny `ContextEnvelope` według [references/context-envelope.md](references/context-envelope.md) jako artefakt roboczy/handoff. Następnie dobierz kanał wyjścia:

- **DIRECT_USER (domyślny, gdy użytkownik wywołuje skill bezpośrednio):** pokaż wyłącznie zwarty operator brief. Nie pokazuj pełnego JSON envelope, source registry, pełnej listy faktów ani długiego audytu, chyba że użytkownik jawnie o nie poprosi.
- **DOWNSTREAM (gdy skill działa jako preflight dla innego skilla/agenta/orkiestratora):** przekaż pełny ContextEnvelope następnemu komponentowi, ale użytkownikowi pokaż tylko krótki handoff summary.
- **DEBUG / EXPLICIT_DETAIL:** pokaż pełny envelope, evidence map lub szerszy raport tylko na wyraźne żądanie typu `pokaż pełny ContextEnvelope`, `daj wszystkie źródła`, `debug`, `szczegółowo`.

Nie interpretuj słów `pełny refresh`, `full`, `sprawdź wszystko` jako prośby o długi user-facing raport. To określa zakres retrievalu.

Jeśli zapisujesz envelope jako JSON, waliduj:

```bash
python3 scripts/validate_context_envelope.py path/to/context-envelope.json
```

Każdy `fact.source_ids[]` musi wskazywać istniejące źródła. Invalid envelope nie może zostać przekazany dalej jako gotowy context.

## 10. Handoff

Typowe handoffy:
- `product-operator` — co robić dalej z aktualnego stanu;
- `repo-to-roadmap` — dependency-aware roadmap całego projektu;
- `evidence-researcher` — claimy wymagające evidence admission/falsifierów;
- `ai-council` — materialny trade-off po wystarczającym evidence;
- `release-readiness` — dopiero z przypiętym RC/build/environment;
- `design-partner-finder`, `cold-email`, `content-strategy`, `social`, `copywriting` — po właściwym kontekście domenowym.

Nie wykonuj kontraktu następnego skilla pod nazwą `cometweb-context`.

## 11. Domyślny user-facing brief — konkretnie, bez ściany tekstu

Dla `DIRECT_USER` używaj progresywnej redukcji. Użytkownik ma w kilka sekund zrozumieć **co się liczy i jaki jest następny krok**.

### Budżet odpowiedzi

- `targeted`: zwykle do **120 słów** / maks. 5 istotnych punktów,
- `standard` i `delta`: zwykle do **220 słów** / maks. 8 istotnych punktów,
- `full`: zwykle do **320 słów** / maks. 10 istotnych punktów.

Przekrocz budżet tylko gdy użytkownik jawnie prosi o szczegóły albo krótsza odpowiedź ukryłaby materialne ryzyko.

### Format

```text
Stan: <jedno zdanie z głównym obrazem>

Najważniejsze:
- <maks. 3-5 faktów/delt, które zmieniają obraz>

Problemy / niepewności:
- <maks. 1-3 konflikty lub authority gaps>

Co dalej:
- <jeden konkretny następny krok albo handoff do właściwego skilla>
```

Jeśli nie ma materialnego konfliktu lub gapu, pomiń sekcję. Dla `delta` zacznij od `Zmieniło się:` i pokaż wyłącznie materialne zmiany + `bez zmian` dla jednego lub dwóch kluczowych blockerów.

### Twarde reguły zwięzłości

- Nie pokazuj pełnego `ContextEnvelope` użytkownikowi domyślnie.
- Nie pokazuj listy wszystkich sprawdzonych źródeł; cytuj/referencjonuj tylko te, które wspierają pokazany wniosek.
- Nie powtarzaj tej samej informacji w diagnozie, tabeli, podsumowaniu i handoffie. Jeden fakt = jedno miejsce.
- Nie twórz tabeli, jeśli 3-5 bulletów jest czytelniejsze.
- Nie raportuj każdego projektu tylko dlatego, że został sprawdzony. Pokaż projekt tylko jeśli jego stan jest materialny dla celu.
- Nie opisuj procesu zbierania danych poza jednym krótkim zdaniem startowym, gdy długi run tego wymaga.
- Nie wyliczaj wszystkich otwartych tasków. Agreguj je do blockerów/verification gates.
- Nie wyświetlaj pól `mode`, `profile`, `source_id`, `freshness`, `sensitivity` itd., chyba że są materialne albo użytkownik prosi o techniczny/debug output.
- Jeśli downstream agent dostanie pełny envelope, nie kopiuj go później do odpowiedzi dla użytkownika.
- `recommended_next_skill` przetłumacz na działanie: np. `Następny krok: Product Operator — ułożyć BLOCKER / VERIFY NOW / NOW / NEXT`.

Streszczaj prywatne źródła. Nie wklejaj pełnych maili, prywatnych stron Notion ani surowych danych CRM.
