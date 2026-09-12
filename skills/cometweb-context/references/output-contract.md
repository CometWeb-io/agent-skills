# User-facing output contract

The full ContextEnvelope is the machine contract. The user-facing response is a compressed view.

## DIRECT_USER

Default when the user invokes CometWeb Context directly.

- targeted: <=120 words normally
- standard/delta: <=220 words normally
- full: <=320 words normally
- show only material facts, conflicts/gaps, and one next action
- never include raw ContextEnvelope JSON unless explicitly requested
- retrieval scope must not control response length

### Full refresh example

Input: `Zrób pełny refresh całego CometWeb.`

Good output shape:

```text
Stan: implementacja wyprzedziła governance; 3 konflikty wymagają reconciliation.

Najważniejsze:
- Pricing live != binding decision.
- CometPen działa operacyjnie mimo starego paused status.
- Lens jest implemented/release-prep, ale publication-gated.

Problemy / niepewności:
- brak świeżego CRM SoR; nie wnioskuj o pipeline.

Co dalej:
- Product Operator: zaktualizować canonical state i ułożyć BLOCKER / VERIFY NOW / NOW.
```

Do not append the full ContextEnvelope.

## DOWNSTREAM

When another skill/agent consumes the context:

1. Build and validate the complete ContextEnvelope.
2. Pass the full machine structure downstream.
3. Show the user only a short handoff summary.

## DEBUG / EXPLICIT_DETAIL

Only on explicit request may the skill render full sources, evidence map, or raw ContextEnvelope.
