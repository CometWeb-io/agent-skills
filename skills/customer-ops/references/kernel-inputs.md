# Kernel inputs and outputs

`scripts/customer_ops_kernel.py <command> --json '<object>'` (or `--json @file.json`, or
`--json -` for stdin) reads one JSON object and prints one JSON object. The machine-checked
contract is `references/contract.json`; this page is the human-readable field list. Keys
the kernel does not read are ignored, so a misspelled key silently becomes "absent": use
these names exactly. Ordinal dimensions are integers; booleans must be JSON `true`/`false`.
Datetimes are ISO 8601 with a timezone offset.

## priority-assess (alias score-case)

```text
impact                  0..4 required
urgency                 0..4 required
breadth                 0..4 required
recurrence              0..4 required
workaround              0..4 required (4 = no viable workaround)
customer_risk           0..4, default 0
strategic_value         0..4, default 0
contractual_deadline    bool
executive_escalation    bool
security_signal         bool, specialist gate
privacy_signal          bool, specialist gate
security_privacy_signal bool, specialist gate
data_loss_signal        bool, specialist gate
legal_signal            bool, specialist gate
fraud_signal            bool, specialist gate
material_financial_harm_signal  bool, specialist gate
```

Returns `operational_priority` and `base_priority` (P0..P3), `rank_score`,
`priority_reasons`, `account_escalation` (STANDARD, EXPEDITED, EXECUTIVE),
`incident_candidate`, `specialist_gate_required` and `specialist_gates`.

## churn-risk

```text
cancel_intent           0..3 required
support_pain            0..3 required
usage_decline           0..3 required
billing_risk            0..3 required
relationship_risk       0..3 required
renewal_pressure        0..3 required
competitive_pressure    0..3 required
direct_evidence_count   0..100, default 0
independent_source_count  0..100, default 0
evidence_current        bool, default true
evidence_conflicted     bool, default false
```

Returns `risk_level` (LOW, MEDIUM, HIGH, CRITICAL), `expressed_exit_intent`,
`time_pressure`, `evidence_grade`, and `strongest_drivers` rows of `driver` and `level`.

## incident-severity

```text
impact                  0..4 required
breadth                 0..4 required
workaround              0..4 required
critical_function       bool
confirmed_data_loss     bool
confirmed_security_incident  bool, specialist gate
confirmed_privacy_incident   bool, specialist gate
legal_signal            bool, specialist gate
material_financial_harm bool, specialist gate
```

Returns `customer_impact_severity` (SEV1, SEV2, SEV3, NOT_INCIDENT) and
`declaration_recommended`.

## deadline-status (alias sla-status)

```text
native_status           provider status; paused, hit, met, fulfilled, completed, missed, breached, overdue, fixed are recognized, anything else is non-terminal
paused                  bool
now                     required unless a recognized native_status or paused is given
due_at                  authoritative deadline that already reflects the provider clock
warning_minutes         >= 0, default 0
clock_mode              set to continuous to opt in to the fallback below
start_at                continuous clock only
target_minutes          continuous clock only, > 0
pause_minutes           continuous clock only, >= 0
```

`start_at` + `target_minutes` without `clock_mode` returns UNKNOWN on purpose.

## dedupe-key and dedupe-pair

```text
symptom
component
environment
trigger
error_signature
left                    dedupe-pair only: object with the five keys above
right                   dedupe-pair only: object with the five keys above
```

Both return candidates only (`dedupe_key`; or `similarity` with LIKELY_SAME_CANDIDATE,
REVIEW, DISTINCT_CANDIDATE); never auto-merge.

## commitment-status

```text
state                   OPEN, DUE_SOON, OVERDUE, FULFILLED, RENEGOTIATED, CANCELLED; default OPEN
due_at                  explicit due time
checkpoint_at           used when due_at is absent
now                     required with due_at or checkpoint_at
warning_minutes         >= 0, default 240
```

A terminal `state` is returned as is. Any other value returns UNKNOWN with the accepted
list instead of running the clock, so a misspelled terminal state is never reported as
OVERDUE.

## transition

```text
entity                  case, incident, handoff, commitment, exposure, cluster
from_state
to_state
```

Returns `allowed` and `allowed_next_states` for the default state machine.

## case-gate

`stage` is one of TRIAGED, GITHUB_READY, RESOLVED, VERIFIED, CLOSED, CUSTOMER_SEND.

```text
source_id, case_type, customer_symptom, owner_class, next_action      TRIAGED, all required
expected_behavior, actual_behavior, reproduction_state                GITHUB_READY, required
verification_criteria, dedupe_search_status, privacy_preflight_status  GITHUB_READY, required
repo_conventions_status   GITHUB_READY; unknown or partial warns
known_secret_or_restricted_data  GITHUB_READY bool; true blocks
resolution_summary        RESOLVED, required
remedy_ref                RESOLVED; this or customer_answered is required
customer_answered         RESOLVED bool
verification_method, verification_evidence, verified_at              VERIFIED, required
verification_passed       VERIFIED; must be true
verified                  CLOSED; true, or an approved unverified close
allow_unverified_close    CLOSED bool
unverified_close_reason   CLOSED; required with allow_unverified_close
customer_followup_status  CLOSED; sent, confirmed, waived, not_required
open_commitments_count    CLOSED, default 0; above 0 blocks without a reason
open_commitments_exception_reason  CLOSED
open_critical_handoffs_count  CLOSED, default 0; above 0 warns
message                   CUSTOMER_SEND, required
recipient_resolved        CUSTOMER_SEND; must be true
facts_current             CUSTOMER_SEND; must be true
write_authorized          CUSTOMER_SEND; must be true
canonical_incident_comms_conflict  CUSTOMER_SEND; true blocks
```

`privacy_preflight_status: blocked` blocks GITHUB_READY and CUSTOMER_SEND; a
`dedupe_search_status` other than done or unavailable warns; a `reproduction_state` of
reported-only, not-reproduced or unknown warns; an `owner_class` of unknown warns.
Returns `status` PASS, WARN or BLOCK with `missing_fields`, `blockers` and `warnings`.

## privacy-scan

```text
text                    string to scan
```

Returns `status` FINDINGS or NO_OBVIOUS_FINDINGS and `redacted_text`; best effort only.

## Status values

`status` across commands: PASS, WARN, BLOCK (case-gate); OK, AT_RISK, BREACHED, MET,
PAUSED, FIXED, UNKNOWN (deadline-status); OPEN, DUE_SOON, OVERDUE, FULFILLED,
RENEGOTIATED, CANCELLED, UNKNOWN (commitment-status); FINDINGS, NO_OBVIOUS_FINDINGS
(privacy-scan). An invalid payload exits 2 with `{"status": "error", "error": ...}`.
