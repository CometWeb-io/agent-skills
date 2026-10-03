# Kernel inputs and outputs

`scripts/ci_kernel.py` reads snapshot files (`--snapshot`, `--old`, `--new`) and event
objects (`--event-json`, inline or `@file.json`) and prints JSON. The machine-checked
contract is `references/contract.json`; this page lists the keys the kernel reads. The
wider recommended shapes are in `data-model.md`; keys listed there but not here are stored
and hashed but never interpreted by the kernel.

## Snapshot (hash, validate-snapshot, diff, accept-snapshot)

```text
schema_version     required
competitor_id      required, lowercase slug
competitor_name    required
captured_at        required, ISO 8601 with timezone
state              required object; the only part diff compares (free-form content)
evidence[]         required array
  evidence_id      unique; missing warns, duplicate is an error
  source           missing warns
  last_verified_at missing warns
  field_path       not read
  source_class     not read
  observed_at      not read
  direct           not read
  supports         not read
  notes            not read
```

`validate-snapshot` returns `valid`, `errors` and `warnings` and exits 2 when invalid.
`diff` returns `change_count` and `changes`; each change has `change_type` (ADDED, REMOVED,
MODIFIED), `field_path`, `before`, `after`, `category` and `event_key`. Paths ending in
captured_at, generated_at, observed_at, last_verified_at, scan_id, snapshot_hash, hash or
source_accessed_at are ignored. `hash` returns `snapshot_hash` and `state_hash`.

## Materiality (score)

```text
relevance          0..1, default 0
magnitude          0..1, default 0
confidence         0..1, default 0 (the "evidence confidence" anchor)
novelty            0..1, default 0
persistence        0..1, default 0
competitor_tier    1, 2 or 3, default 1; anything else is an error
```

Returns `score` 0..100, `severity` (CRITICAL, HIGH, MEDIUM, LOW, NOISE) and `tier_factor`.

## Event (event-key, append-event)

```text
competitor_id          required for append-event
category               required for append-event; see the taxonomy, not checked
field_path             required for append-event
before                 any JSON value
after                  any JSON value
event_key              computed from the five keys above when absent
event_id               computed when absent
first_observed_at      falls back to last_verified_at, then to now
last_verified_at
verification_state     CONFIRMED, LIKELY, UNVERIFIED, DISPUTED, RETRACTED; not checked
materiality            the score output object; not checked
disposition            IGNORE, WATCH, VERIFY, TEST, RESPOND, ESCALATE; not checked
status                 free-form workflow status; not checked
implication
implication_confidence
change_type            stored, not read
factual_change         stored, not read
evidence_ids           stored, not read
```

`category` takes PRODUCT_CAPABILITY, PRICING_PACKAGING, POSITIONING_MESSAGING,
CUSTOMER_PROOF, DISCOVERY_GTM, COMPANY_ORG, TECH_TRUST, SALES_MOTION, MARKET_SIGNAL or
OTHER. The kernel does not check `category`, `verification_state`, `disposition` or
`status`: they feed `event_key` and the revision signature, so a typo creates a new key
or a spurious revision instead of an error. `append-event` returns `appended`,
`duplicate`, `event_id` and `event_key`; an event whose `event_key` exists with the same
`verification_state`, `materiality`, `disposition`, `status`, `implication` and
`implication_confidence` is a duplicate.

## Freshness

`freshness --last-verified-at --ttl-days [--as-of]` returns `status` (CURRENT,
NEAR_EXPIRY, STALE, UNKNOWN), `age_days` and `ttl_days`. Any command that fails prints
`{"error": ...}` and exits 2.
