# Safety and mutation policy

The audit must not damage the product, spend money, contact real people, expose
sensitive data, or change access merely to improve coverage.

## 1. Classify the environment

Use one of:

- `production` — real users/data/business effects
- `staging` — non-production but may still integrate with real services
- `test` — controlled test environment/data
- `local` — local/dev instance
- `unknown` — cannot establish safely

If uncertain, use `unknown`. A hostname containing `staging`, `dev`, or `test`
is a clue, not proof that all downstream side effects are sandboxed.

## 2. Default mutation policy

| Environment | Default |
|---|---|
| production | `read-only` |
| unknown | `read-only` |
| staging | `safe-test-only` |
| test | `safe-test-only` |
| local | `safe-test-only` |

`safe-test-only` means: use disposable/test entities, avoid external real-world
side effects, verify the result, and clean up when practical.

Do not lower this policy merely because a control is in scope.

## 3. Always inspect, do not always execute

You may inspect labels, focus, disabled state, confirmation copy, and reachable
previews without committing a mutation. When execution is blocked by policy,
record `policy-blocked` and what was safely verified.

Never execute these solely for coverage unless the user has explicitly asked
for that exact action in an authorized sandbox and the side effect is controlled:

- real payment, purchase, subscription, refund, transfer, or paid API action
- send email/SMS/push/invite/message to a real recipient
- publish/deploy/go-live/post publicly
- delete or irreversibly overwrite real data
- change roles, permissions, ownership, auth/security controls, secrets, keys
- trigger production webhooks/integrations with external consequences
- export/download unnecessary sensitive datasets
- create large volumes, spam, load, or denial-of-service conditions

For production/unknown, remain read-only even if the user broadly says
"click everything". Ask for/use a staging/test environment for mutation tests.

## 4. Safe test mutation recipe

When `safe-test-only` allows a mutation:

1. Confirm the entity is disposable/test data.
2. Record the known pre-state.
3. Perform one controlled action.
4. Verify durable state, not only toast/animation.
5. Re-read list/detail/aggregate counts affected by the action.
6. Undo/delete/restore the test entity when safe and useful.
7. Verify cleanup.

If cleanup is impossible or uncertainty appears, stop mutating and downgrade to
read-only.

## 5. Adversarial testing boundary

This skill is product QA, not a pentest. Do not bypass authentication, brute
force, exploit injection, enumerate secrets, fuzz destructive endpoints, alter
authorization, or attempt privilege escalation merely because a form exists.
Security-relevant observations visible during normal use may be reported as
product findings; active offensive testing requires explicit authorization and
the appropriate security workflow.

## 6. Privacy and evidence hygiene

Evidence should prove the finding with the minimum sensitive content.

- Redact auth tokens, session IDs, API keys, passwords, payment card data,
  private keys, secrets, and unnecessary personal identifiers.
- Crop screenshots to the relevant region when practical.
- Do not paste private/raw user data into public web search.
- Prefer synthetic/test identities in reports and examples.
- Do not retain a secret in a finding title, filename, or evidence ID.

If redaction would destroy the proof, describe the value generically and keep
only the minimal protected evidence available to the authorized user.

## 7. Coverage accounting

A policy-blocked control is not "untested by accident". Record:

```text
control: Delete production account
status:  policy-blocked
verified: label + confirmation dialog + cancel path
not executed: irreversible production deletion
```

A completed audit may still be `ship` with policy-blocked actions only when the
selected audit objective did not require proving those terminal side effects.
If the terminal side effect is essential to the job (for example payment), use
`incomplete` and recommend a sandbox reproduction.
