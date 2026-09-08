# Legal & Regulatory Gate

Legal jest jurisdiction-aware gatekeeperem, nie prawnikiem-personą i nie głosem większościowym.

## Router

Najpierw uruchom `legal`, aby określić:

- jurysdykcje,
- relewantne domeny prawa,
- materialność,
- wymagane aktualne źródła,
- czy potrzebna jest kwalifikowana ocena człowieka.

Domeny obejmują m.in.:

- commercial/contracts,
- privacy/data protection,
- AI regulation,
- IP/copyright/licensing,
- consumer/advertising,
- employment,
- competition/antitrust,
- corporate/M&A,
- cross-border,
- sector regulation.

## Evidence

Dla aktualnego prawa/regulacji preferuj źródła pierwotne: tekst aktu, regulator, sąd/organ, oficjalne wytyczne. Materiały kancelarii/komentarze mogą objaśniać, ale nie zastępują primary source dla materialnego claimu.

Nie przechowuj w kernelu statycznego wniosku typu "prawo zawsze wymaga X". Router ma wykryć potrzebę sprawdzenia; aktualny stan prawny pobierz live.

## Gate output

- `NOT_REQUIRED`.
- `CLEAR`.
- `CLEAR_WITH_CONTROLS` — wskaż konkretne controls/conditions.
- `COUNSEL_REQUIRED` — wskaż pytanie do rozstrzygnięcia i dlaczego jest materialne.
- `BLOCK` — wskaż binding constraint i źródło.

Chairman nie może przegłosować `BLOCK`. `COUNSEL_REQUIRED` nie jest "ostrożnościowym NO-GO" — to DEFER do rozstrzygnięcia.

## Rozdział odpowiedzialności

Legal: obowiązki prawne i regulacyjne.
Privacy: data lifecycle i prywatność.
Security: adversarial/technical risk.
Responsible AI: materialne harms/rights/fairness szersze niż minimalna zgodność prawna.
