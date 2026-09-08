# Experiment Engine v4

`TEST` jest kontraktem decyzyjnym, nie sugestią "spróbujmy".

Wymagaj:

- hypothesis,
- primary metric,
- baseline,
- pass threshold,
- fail threshold,
- minimum detectable effect, jeśli sensowny,
- duration,
- budget,
- sample / observation unit,
- guardrails,
- kill criteria,
- decision rule: GO / NO-GO / otherwise DEFER,
- Evidence Gap Addressed,
- Assumption Key, jeśli test rozstrzyga konkretne założenie,
- owner,
- review date.

Przed rekomendacją testu rozważ Value of Information. Tani test może być lepszy od dalszej debaty; drogi test o małej szansie zmiany decyzji może nie mieć sensu.

Po wyniku aktualizuj Status, Outcome, Result i bounded Learning. Powiązane założenie przechodzi do `Validated`, `Rejected` lub pozostaje `Testing`.
