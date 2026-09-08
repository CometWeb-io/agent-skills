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

Bindings i hierarchie źródeł: [references/source-registry.json](references/source-registry.json) + [references/source-registry.md](references/source-registry.md).  
Provenance / security: [references/security-and-provenance.md](references/security-and-provenance.md).  
Output: [references/context-envelope.md](references/context-envelope.md) (JSON Schema: `protocol/cw-aip-v2/context.schema.json`).

## Workflow

### 1. Ustal tryb i profil

- `targeted` — 1 pytanie/obszar; zwykle 1–2 grupy źródeł.
- `standard` — bieżąca praca domenowa; zwykle 2–4 grupy.
- `delta` — „co się zmieniło”; wymagany jawny baseline.
- `full` — tylko po wyraźnej prośbie (boardroom / weekly).

```bash
python3 scripts/context_plan.py "<cel>" --json
```

Planer jest pomocniczy. Profile i `preferred_source_groups` bierz z
`source-registry.json` → `domains.*.preferred_source_groups` (oraz tabeli w
`source-registry.md`). Nie duplikuj ścieżek vaulta / CRM / decision IDs w tym pliku.

Nie over-fetchuj: social ≠ roadmap produktu; jedno pytanie GitHub ≠ full gateway.

### 2. Wykryj dostępne źródła

Preferuj: system of record → connector/lokalny artefakt → live/public → fallback.

Nie hard-code'uj nazw MCP. Użyj aktualnie dostępnego connectora. Niedostępne =
`unavailable` / `authority_gap`; nie awansuj fallbacku po cichu.

### 3. Repo snapshot tylko gdy potrzebny

```bash
python3 scripts/repo_snapshot.py --json
```

Root: `COMETWEB_ROOT` → `COMETWEB_CENTRUM` → `~/Github/CometWeb`. Lista:
`references/repos.txt`. Domyślnie ścieżki są redagowane (`--redact-paths`).
Dirty tree ≠ stan produkcji; sprawdź ahead/behind względem remote.

### 4. Zbieraj z provenance

Dla każdej grupy: `source_id`, `source_type`, `authority`, `retrieved_at`,
`effective_at?`, `freshness`, `access`, `sensitivity`, `summary`, `evidence_ref`.

`retrieved_at` ≠ `effective_at`. Authority ≠ freshness.

### 5. Konflikty i luki

Hierarchia z registry. Zachowaj `unresolved_conflict`. `authority_gap` gdy brak
SoR. Materialna nowa decyzja → decision-input binding z registry (nie hard-code).

### 6. Delta tylko wobec baseline'u

Baseline = poprzedni ContextEnvelope / timestampowany snapshot / wskazanie usera.
Bez baseline: `baseline.status=unavailable`, `deltas=[]`.

### 7. Public claim gate

Sprawdź evidence register z registry (`domains.claims`). Brak pokrycia →
`blocked_public_claims` z `reason`. Nie wymyślaj liczb.

### 8. Emituj ContextEnvelope

1. Krótki raport `Stan na <timestamp>`
2. Envelope zgodny ze schematem; waliduj:

```bash
python3 scripts/validate_context_envelope.py path/to/context-envelope.json
```

### 9. Handoff

Wskaż następny skill z katalogu CometWeb (np. `product-operator`,
`evidence-researcher`, `repo-to-roadmap`, `release-readiness`, `ai-council`,
`design-partner-finder`). Nie wykonuj ich kontraktu pod tą skillą.

## Format odpowiedzi

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

Nie wklejaj pełnych prywatnych dokumentów, maili ani stron Notion.
