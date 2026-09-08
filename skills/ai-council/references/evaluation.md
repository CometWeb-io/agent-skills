# Evaluation and champion/challenger v5

## Golden Decision Suite

Utrzymuj poprzednie przypadki oraz temporal/living-decision cases:

- stale legal source,
- superseded regulation,
- draft vs final guidance,
- rule not yet effective,
- old competitor price,
- internal metric not verified in system of record,
- vendor/repo version mismatch,
- security advisory published after snapshot,
- current source contradicts Decision Memory,
- syndicated breaking news,
- correct minority under correlated consensus,
- triggered watch dependency,
- portfolio capacity conflict,
- human approval required for high-authority action.

## Invariants

- high irreversible risk never FAST,
- FAST adviser_count = 3,
- framework count respects budget,
- unknown independence cannot inflate coverage,
- blind round cannot read Decision Memory,
- gatekeeper BLOCK cannot be majority-overridden,
- low-confidence GO/NO-GO downgrade,
- TEST is complete,
- unresolved mandatory gate prevents stop,
- material stale/unknown/superseded/not-yet-effective evidence cannot support unconditional verdict,
- current law/security claims require decision-specific live verification,
- internal metric requires current system-of-record verification,
- Source Registry entry alone is never evidence,
- immutable snapshot never changes during revalidation,
- high-materiality dependency change can produce REOPEN,
- T3/T4 actions require human approval.

## Champion/challenger

Porównuj frozen identical inputs. Mierz benefits: assumptions, risks, evidence gaps, temporal correctness, contradiction coverage, minority preservation, gate quality, forecast calibration, test quality. Mierz costs: latency, token/tool cost, refresh cost.

Promuj challengera dopiero po powtarzalnej przewadze bez regresji invariants. Real outcomes i forecast calibration mają pierwszeństwo przed synthetic preference.
