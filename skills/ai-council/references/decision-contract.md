# Decision Contract v3

Znormalizuj każdą deliberację przed routingiem.

## Wymagane pole

- `question` — decyzja w jednym zdaniu.

## Pola canonical

- `decision_type`: `binary | option_selection | resource_allocation | sequencing | market_entry | pricing | build_vs_buy | launch | partnership | hiring | m_and_a | shutdown | product_investment`.
- `objective`.
- `options[]` i `status_quo`.
- `constraints[]`.
- `time_horizon`.
- `success_metric`.
- `financial_impact 0–1`.
- `strategic_impact 0–1`.
- `uncertainty 0–1`.
- `reversibility`.
- `cost_of_delay 0–1`.
- `cost_of_false_positive 0–1`.
- `cost_of_false_negative 0–1`.
- `known_facts[]`, `known_unknowns[]`.
- `stakeholders[]`.
- `execution_dependencies[]`.
- `jurisdictions[]`.
- `risk_surfaces[]`.

Nie wymyślaj nieznanych wartości. Heurystyki kernela są routingiem, nie faktami. Jawny kontekst użytkownika ma pierwszeństwo.

## Typ werdyktu

`GO | NO-GO | TEST | DEFER` pozostaje governance verdict. Dla decyzji niebinarnych dodaj:

- `recommended_option`,
- `option_ranking`,
- `allocation`,
- `sequence`,

gdy mają zastosowanie.
