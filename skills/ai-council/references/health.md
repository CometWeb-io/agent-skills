# Council health v5

Oceniaj tylko `Memory Status = Complete` i rozliczone rekordy tam, gdzie metryka wymaga outcome.

## Decision health

Rozdzielaj Outcome, Decision Quality, Execution Quality, Outcome Attribution i Current Validity. Mierz False GO/False NO-GO oraz ile decyzji zostało poprawnie REOPEN po zmianie świata.

## Expert / forecast health

Mierz calibration, Brier score, Realized Information Value, redundancy, Independence Grade, minority vindication, routing frequency/router misses. Nie premiuj dissentu za samą odmienność.

## Evidence / temporal health

Mierz:

- freshness block rate,
- stale evidence caught before verdict,
- superseded-source catches,
- system-of-record verification rate,
- contradiction coverage,
- unresolved critical contradictions,
- source-registry miss/deprecation rate,
- mean age of material evidence per claim type.

## Process health

Mierz TEST/DEFER resolution, gate catches, Chairman override, latency/tool cost, saturation, watch-trigger precision, unnecessary reopens, human escalation resolution i portfolio conflict catches.

Nie optymalizuj routingu ani freshness TTL na próbkach `<5` bez zewnętrznego uzasadnienia.
