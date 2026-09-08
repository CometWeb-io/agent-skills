# Council modes v4

Tryb kontroluje koszt deliberacji, nie prestiż problemu. `mode_budget()` jest źródłem prawdy.

Alias produktowy w `SKILL.md`: `LIGHT` ≈ `FAST`, `STANDARD`, `DEEP`.

## FAST / LIGHT

Dla małej, odwracalnej decyzji o niskim ryzyku.

- Decision Contract + 2–3 perspektywy + evidence sanity + key risks.
- Verdict: `GO` / `TEST` / `DEFER` (bez forecasting, portfolio, living-decision machinery).
- 3 advisers.
- Do 1 specialist.
- Do 2 gatekeepers, jeśli risk surface ich wymaga.
- Maks. 1 framework.
- Maks. 1 live web query.
- Maks. 1 analogia.
- Premortem/counterfactual/minority sentinel nieobowiązkowe.
- Red Team i Evidence Judge nadal obowiązują w wersji skróconej.

## STANDARD

Domyślny tryb dla średniej wartości/niepewności.

- Do 5 advisers.
- Do 3 specialists.
- Do 4 gatekeepers.
- Do 3 frameworków.
- Do 2 live web queries.
- Do 3 analogii.
- Premortem obowiązkowy.
- Minority Sentinel obowiązkowy.
- Counterfactual: gdy confidence < required, podejrzanie wysoki consensus albo materialny dissent.

## DEEP

Dla wysokiego lock-in, dużego downside, złożonej regulacji lub wielu systemowych zależności.

- Do 7 advisers.
- Do 5 specialists.
- Do 6 gatekeepers.
- Do 3 frameworków.
- Do 5 live web queries.
- Do 3 analogii.
- Premortem, Minority Sentinel, counterfactual i Process Auditor obowiązkowe.

Gatekeeperów nie usuwaj tylko po to, aby zmieścić ich w budżecie adviserów. Binding risk surface ma pierwszeństwo przed dodatkowym adviserem.
