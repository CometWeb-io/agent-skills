# ContextEnvelope v2

Minimalny kontrakt przekazywany do kolejnego skilla lub orkiestratora.

```json
{
  "schema": "cometweb.context/v2",
  "snapshot_id": "ctx-<timestamp-or-uuid>",
  "generated_at": "2026-08-30T19:30:00Z",
  "goal": "...",
  "mode": "targeted|standard|delta|full",
  "profile": "product|gtm|outreach|brand|meeting|weekly|claim-verification|custom",
  "baseline": {
    "status": "available|unavailable|not_requested",
    "ref": null
  },
  "sources": [
    {
      "source_id": "...",
      "source_type": "github|local-repo|vault|notion|crm|gmail|calendar|insight|website|social|file|other",
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
      "source_ids": ["..."],
      "confidence": "high|medium|low",
      "sensitivity": "public|internal|confidential|restricted"
    }
  ],
  "deltas": [],
  "conflicts": [],
  "gaps": [],
  "blocked_public_claims": [],
  "handoff": {
    "recommended_next_skill": null,
    "dependencies": [],
    "constraints": []
  }
}
```

## Semantyka

- `facts` zawiera tylko fakty potrzebne do celu, nie dump wszystkich źródeł.
- `deltas` jest puste, jeśli baseline nie istnieje.
- `conflicts` zachowuje obie wersje i źródła.
- `gaps` obejmuje brak connectora, niepełny zakres, nieweryfikowalny claim i authority gap.
- `blocked_public_claims` nie oznacza, że claim jest fałszywy; oznacza, że nie spełnił gate'u do użycia publicznego.
- `handoff.dependencies` może zawierać ID wcześniejszych envelope'ów CW-AIP, jeśli skill działa w orkiestratorze.

## Handoff do Skill Orchestrator

Traktuj `ContextEnvelope` jako preflight dependency, a nie verdict. Kolejny skill może użyć go jako wejścia, ale musi nadal wykonać własne wymagane read/research/gates.

Przykłady:

- ContextEnvelope -> `repo-to-roadmap`: świeży stan repo/Insight/docs.
- ContextEnvelope -> `product-operator`: świeży kontekst operacyjny, ale operator sam odpowiada za priorytety.
- ContextEnvelope -> `ai-council`: tylko kontekst; materialne claimy mogą nadal wymagać Evidence Researcher.
- ContextEnvelope -> `cold-email`: kontekst prospekta; copy skill nadal odpowiada za treść i compliance.
