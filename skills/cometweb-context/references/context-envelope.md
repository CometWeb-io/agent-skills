# ContextEnvelope v2

Minimalny kontrakt przekazywany do kolejnego skilla lub orkiestratora.

```json
{
  "schema": "cometweb.context/v2",
  "snapshot_id": "ctx-<timestamp-or-uuid>",
  "generated_at": "2026-09-07T00:00:00+02:00",
  "goal": "...",
  "mode": "targeted|standard|delta|full",
  "context_scope": "public_example|workspace_private|project_context",
  "project_ref": null,
  "profile": "product|portfolio|gtm|outreach|brand|meeting|weekly|claim-verification|custom",
  "baseline": {
    "status": "available|unavailable|not_requested",
    "ref": null
  },
  "sources": [
    {
      "source_id": "src-001",
      "project_ref": null,
      "source_type": "github|local-repo|vault|notion|crm|gmail|calendar|contacts|insight|website|social|file|other",
      "authority": "system_of_record|canonical|primary|secondary|fallback",
      "access": "live|local|connector|cached|fallback",
      "retrieved_at": "...",
      "effective_at": null,
      "freshness": "fresh|aging|stale|unknown",
      "sensitivity": "public|internal|confidential|restricted",
      "summary": "...",
      "evidence_ref": "..."
    }
  ],
  "facts": [
    {
      "fact_id": "f-001",
      "statement": "...",
      "source_ids": ["src-001"],
      "confidence": "high|medium|low",
      "sensitivity": "public|internal|confidential|restricted"
    }
  ],
  "deltas": [],
  "conflicts": [
    {
      "status": "unresolved_conflict|resolved",
      "basis": null
    }
  ],
  "gaps": [
    {
      "kind": "authority_gap",
      "missing_authority": "..."
    }
  ],
  "blocked_public_claims": [
    {
      "reason": "..."
    }
  ],
  "governance": {
    "first_principles": {
      "required": false,
      "status": "loaded|not_required|unavailable",
      "source_ref": null,
      "reason": null
    }
  },
  "handoff": {
    "recommended_next_skill": null,
    "dependencies": [],
    "constraints": []
  }
}
```

## Invariants

- `context_scope` rozdziela `public_example`, `workspace_private` i `project_context`; brak pola w starszym payloadzie oznacza `workspace_private`. Jawne `null` i nieznany zakres są błędem.
- `public_example` wymaga `public` dla każdego źródła i faktu, także źródeł bez referencji z faktów. `project_context` wymaga niepustego `project_ref` i identycznego `sources[].project_ref` dla każdego źródła.
- Kolejność sensitivity: `public` < `internal` < `confidential` < `restricted`. Fakt nie może obniżyć klasyfikacji żadnego wskazanego źródła; zewnętrzna koperta CW-AIP nie może obniżyć klasyfikacji źródeł ani faktów. Publiczna koperta wymaga jawnego `public_example`.
- Zakres i sensitivity sprawdzają zadeklarowane pola. Nie potwierdzają klasyfikacji treści, prawdziwości źródeł, uprawnień, anonimizacji tekstu ani zgody na public use. Sprawdź również goal, deltas/conflicts/gaps, governance i handoff przed publikacją.
- `facts` zawiera tylko fakty potrzebne do celu.
- Każdy `fact.source_ids[]` wskazuje istniejący `sources[].source_id`.
- `deltas` wymaga realnego baseline'u; bez niego nie twórz fikcyjnego porównania.
- `conflicts` zachowuje obie wersje i źródła. Każdy wpis ma `status` `unresolved_conflict` albo `resolved`; `resolved` wymaga niepustego `basis` (claim-specific authority, na której oparto rozstrzygnięcie).
- `gaps` obejmuje brak connectora, authority gap, nieweryfikowalny claim i brak wymaganej świeżości.
- `gaps[].kind` jest wolnym tekstem; `authority_gap` wymaga niepustego `missing_authority` i jest obowiązkowy, gdy źródło `system_of_record` ma `access` `cached` albo `fallback`.
- `blocked_public_claims` oznacza brak dopuszczenia do public use, nie automatycznie fałsz. Każdy wpis wymaga niepustego `reason`.
- `governance.first_principles` opisuje preflight, nie verdict. `required` jest boolean; `required: true` wyklucza `status: not_required`. `source_ref` i `reason` są informacyjne; walidator ich nie sprawdza.
- `facts[].statement` przy `sensitivity` `confidential` lub `restricted` ma najwyżej 800 znaków.
- `retrieved_at`, `effective_at` i `generated_at` to ISO-8601 ze strefą czasową; `retrieved_at` nie może być późniejsze niż `generated_at`.
- Niepuste `deltas` wymagają `baseline.status: available` z niepustym `ref`; tryb `delta` wymaga `available` albo `unavailable`.
- `handoff.dependencies` może zawierać ID wcześniejszych CW-AIP envelope'ów.

## Handoff

ContextEnvelope jest preflight dependency. Kolejny skill nadal wykonuje własne research/gates i nie może uznać
context factu za evidence admission tylko dlatego, że pojawił się w envelope.

## Wyjście skryptów

`python3 scripts/context_plan.py "<cel>" [--mode auto|targeted|standard|delta|full] --json`:

```text
profile: pierwszy dopasowany profil (lista jak w polu profile envelope'u)
context_scope: public_example|workspace_private|project_context (domyślnie workspace_private)
project_ref: referencja projektu w project_context; null w pozostałych zakresach
blocked_source_group_count: liczba grup wykluczonych w public_example; ich identyfikatory nie są ujawniane
mode: targeted|standard|delta|full (auto wybiera z treści celu)
source_groups[]: preferowane grupy źródeł profilu; vault-first-principles na początku, gdy decyzja jest materialna
governance:
  first_principles_required: boolean
  decision_log_required: boolean, równe first_principles_required
candidates[]: wszystkie dopasowane profile w kolejności reguł
ambiguous: true, gdy dopasowano więcej niż jeden profil
registry: references/source-registry.json
rule: minimal-authoritative-sources-first
```

Oba helpery przyjmują `--context-scope`. Planner dla `project_context` wymaga
`--project-ref`; źródła pobieraj wyłącznie dla wskazanego projektu. Tylko
`workspace_private` wczytuje nakładki `.local`. `public_example` ogranicza grupy
do publicznych kategorii; wykluczenie governance nie znosi jego wymagalności.

`python3 scripts/repo_snapshot.py [--root DIR] [--repo REL] [--include-paths] --json` (tylko odczyt):

```text
schema: cometweb.repo-snapshot/v2
context_scope: public_example|workspace_private|project_context
generated_at, observed_at: moment odczytu (UTC)
snapshot_ref: HEAD
root_source: argument|COMETWEB_ROOT|COMETWEB_CENTRUM|fallback
root_available: boolean
root: <redacted>, chyba że --include-paths
fallback: null albo use-current-github-connector, gdy root nie istnieje
repos[]:
  repo: ścieżka względna z repos.txt
  status: ok|invalid_path|missing|not_git|not_repo_root|error
  path: tylko z --include-paths
  branch, head_sha, last_commit_at, subject: dla status ok
  dirty_count, commits_7d, commits_30d: dla status ok
  error: przy status error; szczegół tylko z --include-paths
```

`public_example` zwraca `execution_status: NOT_RUN`, powód i pustą listę repo bez
odczytu filesystemu workspace, środowiskowego root ani rejestru. `root_available`
i `snapshot_ref` są wtedy `null`, a root `<redacted>`; opcje odczytu workspace są
odrzucane. `project_context` wymaga dokładnie jednego `--repo` i nie skanuje
rejestru całego workspace. Ukrycie ścieżki w prywatnym snapshot nie czyni go publicznym.

Migracja publicznych kopert: dodaj `context_scope: public_example` dopiero po
sprawdzeniu wszystkich pól, źródeł i faktów; przelicz payload hash. Stare prywatne
payloady pozostają zgodne, ale zmiana etykiety koperty na publiczną nie wystarcza.

## Zakres danych

Zakres danych jest niezależny od szerokości retrievalu.
- `public_example` — tylko jawnie publiczne źródła i fakty; bez lokalnych nakładek i odczytu repozytoriów workspace.
- `workspace_private` — domyślny prywatny preflight, z lokalnymi nakładkami.
- `project_context` — jeden jawny `project_ref`; źródła muszą deklarować tę samą referencję. Snapshot wymaga dokładnie jednego `--repo`.

To kontrole zadeklarowanych pól, nie automatyczna ocena prywatności tekstu ani zgoda na publikację.
