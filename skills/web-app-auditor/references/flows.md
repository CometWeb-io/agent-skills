# Flows (critical paths)

A flow is a user job with a start, intermediate states, and a success definition.
The safety boundary is part of the flow contract.

## 1. Define the job

```text
JOB:       <what the persona is trying to accomplish>
START:     <known state>
SUCCESS:   <observable durable result>
FAILS:     <material failure/recovery paths>
MUTATION:  read-only | safe-test-only
```

If terminal success requires a prohibited real-world side effect, define the
safe test boundary and expect `incomplete` unless a controlled sandbox exists.

## 2. Happy path

At each policy-safe step record URL/route, carried data, displayed data, primary
action, and observed durable state.

Watch for silent changes in identity, amount, quantity, plan, recipient,
permission, tax, or other material facts.

## 3. Unhappy paths

Exercise only paths reachable without unsafe behavior:

- validation then correction
- back/cancel/edit/review
- refresh/deep link where the product expects restoration
- duplicate activation in a safe test environment
- session interruption using supported test mechanisms
- network/terminal failure only through mocks/sandbox/test controls

Do not demote real users, decline real cards, send real invites, delete real
records, or disconnect production integrations to manufacture a test.

## 4. Cross-step contradiction matrix

Track material facts across steps, e.g. amount, entity ID, recipient, status,
quantity, permissions. A terminal mismatch can be blocker only when actually
observed and materially consequential.

## 5. Recovery and idempotency

For policy-safe terminal actions verify:

- repeated activation does not create duplicate durable effects
- loading/progress prevents accidental duplicate action where needed
- success surface has a coherent next step
- returned list/detail reflects the resulting state

## 6. Multi-persona flows

Walk both sides only when you have authorized test personas/channels. An invite
cannot be declared delivered merely because the sender sees "success"; if real
message delivery cannot be safely verified, mark terminal delivery unproven.

## 7. Stop conditions

- product blocker makes later steps unreachable
- mutation policy blocks the next terminal action
- explicit scope boundary reached

Never invent coverage for steps beyond the stop condition.
