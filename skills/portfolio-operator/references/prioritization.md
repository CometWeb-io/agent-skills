# Prioritization and capacity

## Gates before scoring

Evaluate in this order:

1. overdue/near `hard_external` commitments;
2. safety/legal/financial/compliance obligations with current-horizon consequences;
3. confirmed blockers of the primary goal;
4. prerequisites for 1-3;
5. revenue/trust-critical work tied to current evidence;
6. fixed-date research/submission obligations;
7. strategic work aligned to the primary goal;
8. optional improvements.

A numeric score may order items within a class. It must not override a hard gate.

## MUST DO test

An item belongs in `MUST DO` only if at least one is true:

- evidenced hard external commitment in the active horizon;
- evidenced hard internal commitment/gate in the active horizon;
- confirmed blocker of the active portfolio goal;
- dependency necessary to satisfy one of the above.

If none is true, use `NOW`, `WAITING`, `NEXT`, or `PAUSE / DROP`.

## Future gates

A condition that matters later but does not block the active horizon is `WAITING/NEXT`.

Example: self-serve billing work may be a future gate while a free design-partner validation sprint is active. Do not call it a current blocker unless the active goal changes.

## Capacity

If the user supplies reliable available hours, use them cautiously. Otherwise:

- one primary focus stream;
- at most two secondary focus streams;
- relative effort classes only;
- maintenance for non-focus projects;
- explicit `PAUSE / DROP` for work that should not receive capacity.

Never manufacture a 40-hour week, percentages, or exact day allocation from no source.

## Conflict detection

Surface `CAPACITY CONFLICTS` when, for example:

- two large hard commitments share the same or overlapping fixed deadline;
- a new external promise collides with a previously accepted commitment;
- the active horizon contains more hard work than the known/relative capacity can plausibly hold;
- one project requires primary-focus status while another already has an immovable primary commitment;
- exact capacity is unknown and three or more substantial (`M/L/XL`) current-horizon hard commitments compete across distinct projects/domains.

Do not resolve a consequential conflict by silently dropping one commitment. If the trade-off is material, delegate a decision.

## Focus allocation

After commitments/gates:

- `PRIMARY_FOCUS`: the stream that receives most discretionary attention;
- `SECONDARY_FOCUS`: up to two bounded streams that can progress without undermining the primary;
- `MAINTENANCE`: only necessary upkeep;
- `WAITING/PAUSED`: no active capacity beyond monitoring.

Do not distribute small tasks across every active project just to make the plan look balanced.
