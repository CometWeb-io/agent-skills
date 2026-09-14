# ContextEnvelope v2

Minimalny kontrakt przekazywany do kolejnego skilla lub orkiestratora.

```json
{
  "schema": "cometweb.context/v2",
  "snapshot_id": "ctx-<timestamp-or-uuid>",
  "generated_at": "2026-09-07T00:00:00+02:00",
  "goal": "...",
  "mode": "targeted|standard|delta|full",
  "profile": "product|portfolio|gtm|outreach|brand|meeting|weekly|claim-verification|custom",
  "baseline": {
    "status": "available|unavailable|not_requested",
    "ref": null
  },
  "sources": [
    {
      "source_id": "src-001",
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
  "conflicts": [],
  "gaps": [],
  "blocked_public_claims": [],
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

- `facts` zawiera tylko fakty potrzebne do celu.
- Każdy `fact.source_ids[]` wskazuje istniejący `sources[].source_id`.
- `deltas` wymaga realnego baseline'u; bez niego nie twórz fikcyjnego porównania.
- `conflicts` zachowuje obie wersje i źródła.
- `gaps` obejmuje brak connectora, authority gap, nieweryfikowalny claim i brak wymaganej świeżości.
- `blocked_public_claims` oznacza brak dopuszczenia do public use, nie automatycznie fałsz.
- `governance.first_principles` opisuje preflight, nie verdict.
- `handoff.dependencies` może zawierać ID wcześniejszych CW-AIP envelope'ów.

## Handoff

ContextEnvelope jest preflight dependency. Kolejny skill nadal wykonuje własne research/gates i nie może uznać
context factu za evidence admission tylko dlatego, że pojawił się w envelope.
