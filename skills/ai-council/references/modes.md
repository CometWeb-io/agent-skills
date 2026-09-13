# Council modes v4

Tryb kontroluje koszt deliberacji, nie prestiż problemu. `mode_budget()` jest źródłem prawdy.

Alias produktowy w `SKILL.md`: `LIGHT` ≈ `FAST`, `STANDARD`, `DEEP`.

## FAST / LIGHT

Dla małej, odwracalnej decyzji o niskim ryzyku.

- Decision Contract + 2–3 perspektywy + evidence sanity + key risks.
- Verdict: `GO` / `TEST` / `DEFER` (bez forecasting, portfolio, living-decision machinery).
- 3 advisers.
- Do 1 specialist.
- Budżet orientacyjny 2 gatekeepers; wszystkie wymagane bramki pozostają w planie.
- Maks. 1 framework.
- Maks. 1 live web query.
- Maks. 1 analogia.
- Premortem/counterfactual/minority sentinel nieobowiązkowe.
- Red Team i Evidence Judge nadal obowiązują w wersji skróconej.

## STANDARD

Domyślny tryb dla średniej wartości/niepewności.

- Do 5 advisers.
- Do 3 specialists.
- Budżet orientacyjny 4 gatekeepers; bez usuwania wymaganych bramek.
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
- Budżet orientacyjny 6 gatekeepers; bez usuwania wymaganych bramek.
- Do 3 frameworków.
- Do 5 live web queries.
- Do 3 analogii.
- Premortem, Minority Sentinel, counterfactual i Process Auditor obowiązkowe.

Gatekeeperów nie usuwaj tylko po to, aby zmieścić ich w budżecie adviserów. Binding risk surface ma pierwszeństwo przed dodatkowym adviserem.

## Kernel 5.0.1

`LIGHT` jest dokładnym aliasem `FAST`; literówki w nazwie trybu są błędem. `route` nie obcina listy wymaganych gatekeeperów. Gdy jest ich więcej niż orientacyjny budżet, zwraca `gatekeeper_budget_exceeded: true`. Wtedy podnieś profil lub opisz koszt dodatkowych kontroli; nie rezygnuj z bramki dla zachowania limitu. Kernel nie uruchamia ekspertów ani nie automatyzuje takiej eskalacji.

Do końcowego `gate` przekaż pełną listę `roles.gatekeepers` jako `--required-gates-json`. Sam słownik statusów nie ujawnia brakujących ról. [Przykład CLI](kernel-admission.md).
