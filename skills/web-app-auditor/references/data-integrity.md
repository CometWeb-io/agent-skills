# Data integrity

A qualified auditor treats every number as a claim about the world. Claims
must agree with each other and with arithmetic.

## 1. Contradiction matrix (mandatory on data; material on page/area)

Record every appearance of each material/repeated fact selected by the depth
contract. `standard` verifies all high-risk facts and representative repeated
low-risk facts; `forensic` records every in-scope material fact:

```text
FACT          | A (nav) | B (table) | C (detail) | D (toast) | E (URL)
--------------|---------|-----------|------------|-----------|--------
invoice count | 4       | 3 rows    | —          | —         | —
invoice id    | —       | INV-1042  | INV-1042   | INV-1042  | 1042
status        | —       | paid      | open       | "opłacono"| —
amount        | —       | 2900 PLN  | 2900 PLN   | 29 USD    | —
customer      | M.Nowak | Acme GmbH | Maria Nowak| —         | —
```

A disagreement becomes a finding only when the compared cells are expected to
represent the same fact/context. First rule out legitimate differences such as
filtered vs global count, net vs gross, timezone, or intentionally different
status scope. Duplicate IDs, impossible dates, and unexplained unit mismatches
remain strong defect candidates.

Do this for: counts, totals, subtotals, taxes, discounts, percents, dates,
times, timezones, names, emails, ids, statuses, roles, quantities, units,
plan names, remaining quotas, "last updated", filter result lengths.

## 2. Recalculate (do the math yourself)

- **Sum** line items. Compare to subtotal, tax, total, amount due.
- **Percent**: `part / whole`, watch 0, 100, rounding (0.5, 1.005).
- **Tax**: stated rate × net = tax? Gross − net = tax?
- **Discount**: stacked vs sequential. Coupon vs line vs order.
- **Pagination**: `from–to of total` vs rows on this page vs pages available.
- **Badges**: nav/tab badge vs list length vs filtered length vs server total.
- **Filters**: active filter chips vs query vs result count vs empty state.
- **Charts**: legend/value vs table vs axis. A pie that does not sum to 100%.
- **Delta**: "vs last period +12%" — compute from the two displayed numbers.
- **Remaining quota**: `used + remaining = limit`? Progress bar width ≈ used/limit?

If the UI hides the inputs to a total, say `needs-repro` unless you can
derive them from other screens.

## 3. Common contradiction patterns

| Lie | Example |
|---|---|
| Count mismatch | Badge 4, table 3, footer "z 3" |
| Arithmetic | Lines 10+15=30 |
| Unit mismatch | Header USD, line PLN, no FX |
| Rounding | 33.335% shown as 33% and 34% in two places |
| Stale | Delete succeeds, row remains until refresh |
| Optimistic fiction | Toggle flips, then snaps back, no error |
| Identity collision | Two rows share INV-1042; two names for one user |
| Impossible value | 31.02.2026, −1 items, 140% progress |
| Timezone/clock | "2 hours ago" vs timestamp yesterday; UTC shown as local |
| Locale | `1,234.56` vs `1 234,56` mixed; month/day swapped |
| Status vs action | Status "paid", button "Pay now" still there |
| Permission fiction | UI shows "admin", API 403s the admin action |
| Empty vs zero vs null | "0 results" as a ghost row; blank vs "—" vs 0 |
| Off-by-one | Page size 10, "1–10 of 9"; index 0 shown to users |
| Truncation as wrong value | 99+ hiding 120; "…" eating the amount |
| Copy vs data | Button "Usuń 3 pliki" with 2 selected |

## 4. Safe mutation then re-read

Only after `safety-and-mutations.md` allows the action, perform a controlled
mutation on disposable/test data. Never pay, delete production data, send real
messages, or change real permissions solely to validate data integrity.

After an allowed create / update / delete / move / filter / sort action:

1. Read the same entity on the current screen.
2. Navigate away and back (or refresh) and read again.
3. If a list and a detail exist, check both.
4. If a badge/count exists, check it.
5. If an undo path exists, test it when safe and re-read.
6. Clean up/restore the test entity when practical and verify cleanup.

If the terminal mutation is policy-blocked, verify only the pre-commit state and
record the outcome as unproven. A UI that only looks right until refresh is
still wrong when that stale behavior is actually observed.

## 5. Money, dates, ids — extra care

Money:

- Currency symbol agrees with ISO code and locale.
- Net / gross / tax labeled. Never infer which.
- Recurring prices: monthly vs yearly vs "billed annually".
- Trial, prorate, credits. If shown, they must enter the total.

Dates:

- Parse displayed dates. Reject impossible calendars.
- Relative + absolute should refer to the same instant.
- Expiry at 00:00 vs end-of-day — if it matters, file it.

Ids:

- Unique where they must be unique.
- Detail URL id matches the record.
- Truncated ids still unambiguous, or shown in full on copy.

## 6. Confidence

| How you know | Confidence |
|---|---|
| Recalculated from numbers on the same screen | high |
| Compared two screens you opened | high |
| Compared UI to API/network payload you saw | high |
| Compared observed UI to deterministic source/data contract | high if both were actually observed |
| Guessed from naming | do not file — or `needs-repro` |

Never "the total looks off" without the arithmetic in Evidence.
