# Human escalation and expert evidence v5

## Kiedy eskalować

Eskaluj, gdy:

- gate = `COUNSEL_REQUIRED`,
- decyzja przekracza zdefiniowaną human approval authority,
- materialny legal/security/finance/medical/scientific problem nie może być wiarygodnie rozstrzygnięty dostępnymi źródłami,
- konsekwencja błędu jest wysoka i kwalifikowana opinia ma dodatni Value of Information.

## Handoff packet

Użyj `handoff` i wygeneruj bounded packet zawierający:

- decision i jurisdiction/domain,
- frozen known facts,
- dokładne pytanie do eksperta,
- material uncertainty,
- relewantne primary sources,
- alternatywne interpretacje,
- konsekwencję biznesową,
- deadline,
- co zmieni verdict.

Human response zapisuj jako `HUMAN_EXPERT_EVIDENCE` z zakresem, datą i validity. Nie traktuj jej jako wiecznej prawdy poza zakresem opinii.
