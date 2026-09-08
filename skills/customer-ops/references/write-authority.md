# Write Authority and Mutation Safety

## Contents

1. Purpose
2. Action classes
3. Approval rules
4. Preflight checklist
5. Idempotency and retries
6. Bulk changes
7. Sensitive publication
8. Post-write verification
9. Failure handling

## 1. Purpose

Customer Ops often has enough context to *recommend* an action before it has authority to
perform it. Separate analysis from mutation so the skill does not send, close, refund,
publish, or alter operational truth merely because the next step seems obvious.

Follow the host product/tool's own confirmation and safety requirements in addition to this
skill. This reference never expands tool authority.

## 2. Action classes

Use the highest applicable class.

### `R0 — READ / ANALYZE`

Examples:

- search/read support threads,
- read CRM/account/billing facts,
- inspect GitHub issues/PRs,
- read incident docs,
- calculate/rank from already authorized data,
- produce drafts/proposals.

No external mutation.

### `W1 — REVERSIBLE INTERNAL METADATA`

Examples:

- add/remove a non-sensitive support tag,
- assign/reassign an internal owner,
- update an internal case field,
- add an approved label to a GitHub issue.

Require explicit user intent to mutate the system. Inspect existing conventions first.

### `W2 — OPERATIONAL WORK ARTIFACT`

Examples:

- create/update GitHub issue,
- create/update internal incident/task record,
- add substantive engineering/internal comment,
- update CRM case/risk notes.

Require explicit user intent and preflight. Dedupe/idempotency checks are mandatory where
retries can create duplicates.

### `W3 — CUSTOMER/PUBLIC COMMUNICATION OR CLOSURE`

Examples:

- send/reply to a customer,
- publish status/incident communication,
- close a customer case,
- tell a customer a fix is deployed/resolved,
- communicate a contractual/SLA interpretation.

Require explicit user intent plus factual/source verification. Do not manufacture ETA,
root cause, scope, eligibility, or promises.

### `W4 — FINANCIAL / DESTRUCTIVE / SENSITIVE DISCLOSURE`

Examples:

- issue refund/credit,
- delete/archive material records,
- reveal security/privacy incident details,
- make a legal/regulatory commitment,
- publish highly sensitive customer information.

Require explicit human authorization and the applicable policy/specialist gate. If the
host environment has a higher-risk authority mechanism, use it.

## 3. Approval rules

- The user's request to **analyze, triage, investigate, review, summarize, recommend, or
  prepare** does not authorize a write.
- The user's request to **create, update, send, reply, close, assign, tag, refund, publish,
  or delete** can authorize the named mutation if target and required fields are resolved.
- Do not broaden a specific write into adjacent writes. "Create the GitHub issue" does not
  also authorize emailing the customer or changing CRM state.
- A previous turn's approval does not automatically authorize a materially different
  target/content/action.
- When the target is ambiguous and connector reads can resolve it safely, read first. Ask
  only if the ambiguity cannot be resolved from available authoritative data.

Without write authority, return the exact proposal under `Needs approval`.

## 4. Preflight checklist

Before `W1+`, verify:

```text
intent            user actually requested this mutation
target            correct account/contact/thread/repo/issue/page
source truth      material facts re-checked/current enough
content           no unsupported ETA/root cause/scope/eligibility claim
privacy           minimum necessary data; no secrets/unnecessary PII
conventions       repo/support/CRM conventions inspected where relevant
idempotency       existing artifact/action checked when duplication is possible
side effects      financial/destructive/public consequences understood
scope             exact records/actions bounded
```

For customer/public messages also verify:

- recipient/channel,
- latest customer ask/context,
- latest incident/case state,
- commitments created by the message,
- no conflicting canonical incident communication.

## 5. Idempotency and retries

Agent/tool retries can duplicate work. Before creation actions:

- search for an existing GitHub issue/problem cluster/task using stable identifiers and
  symptom context;
- inspect whether the customer reply already exists in the thread when tool state makes
  that possible;
- use stable case/cluster IDs in internal artifacts;
- capture returned external IDs immediately.

After a write failure/timeout, do **not** blindly retry creation. Read/search first to
establish whether the first action succeeded.

For updates, re-read if concurrent changes can materially affect correctness.

## 6. Bulk changes

For multi-record writes, prepare a mutation manifest:

```text
action_id
target system
object id
action
old value/state (if available)
new value/state
reason/source
risk class
```

Rules:

- Do not silently expand a sampled analysis into writes on the full population.
- Preserve per-record traceability.
- Stop/flag if a target no longer matches the preflight assumption.
- Do not overwrite unrelated fields when the connector action replaces a full field set.
- Report partial success/failure record by record.

## 7. Sensitive publication

Before moving data from a restricted source into GitHub/shared docs/status/public comms,
classify the payload:

- `PUBLIC`
- `INTERNAL`
- `CUSTOMER_CONFIDENTIAL`
- `RESTRICTED` (secrets, credentials, highly sensitive/legal/security material)

Default publication rules:

| From | To | Rule |
|---|---|---|
| support/CRM | public GitHub | use internal IDs + minimum symptom context; no raw PII |
| support/CRM | private GitHub | still minimize; private does not mean unrestricted |
| support | broad incident channel | only operational facts needed by the audience |
| restricted security/privacy evidence | ordinary GitHub/support comment | do not copy; link to approved restricted location |
| internal incident doc | customer/status update | facts only; remove hypotheses/internal details |

Use the kernel `privacy-scan` as a **best-effort preflight**, never as proof that content is
safe or compliant.

## 8. Post-write verification

After a successful write, verify when possible:

- returned object ID/URL,
- resulting state/labels/assignee/body,
- sent message appears in the correct thread,
- case/CRM field actually changed,
- incident update is on the intended record/channel.

Report:

```text
performed action
target
external id/url
verified state
anything not verified
```

A tool success response is evidence of the API action, not automatically evidence that a
customer problem is solved.

## 9. Failure handling

If a mutation fails:

- preserve the error without exposing secrets,
- do not claim the change occurred,
- do not downgrade the case state based on the intended mutation,
- avoid duplicate retries,
- return the safest next step.

If only some bulk mutations succeed, report a partial outcome and exact successful/failed
object IDs.
