# Customer Communication and Sensitive-Data Safety

## Contents

1. Communication truth contract
2. Message structure
3. Troubleshooting and workarounds
4. ETA and commitments
5. Sensitive data
6. Credits/refunds/concessions
7. Security/privacy/legal escalations
8. Tone
9. Pre-send checklist

## 1. Communication truth contract

Every support/incident message should distinguish:

1. **What we know** — confirmed/reported facts at the right certainty.
2. **What we are doing** — action actually underway/owned.
3. **What the customer can do** — verified workaround/diagnostic if any.
4. **What happens next** — real checkpoint/condition; no invented promise.

Do not let a desire to reassure the customer weaken factual precision.

## 2. Message structure

For a routine operational reply, prefer:

```text
Acknowledge concrete impact/question.
State current verified status in 1-2 sentences.
Give one next step/workaround if known.
Give the next real checkpoint or say there is no confirmed ETA yet.
```

Avoid dumping internal triage, speculative root cause, team chatter, or irrelevant technical
detail.

### Status language

Use evidence-calibrated wording:

- `We can reproduce...` only after reproduction.
- `We are investigating...` only if work is actually active/owned.
- `A fix is deployed...` only after deployment evidence.
- `This is resolved...` only when the intended audience's definition is satisfied; customer
  case closure still requires verification.

## 3. Troubleshooting and workarounds

Label a step correctly:

- `diagnostic step` — tests a hypothesis;
- `temporary workaround` — avoids the symptom with known limitations;
- `resolution` — durable remedy supported by evidence.

Only recommend a workaround that is:

- relevant to the symptom,
- safe for customer data/account state,
- tested/documented enough for the context,
- reversible where possible.

If uncertain, say it is an unverified diagnostic rather than a fix.

## 4. ETA and commitments

Never invent an ETA. If no confirmed engineering/incident ETA exists, say so and use a real
next update checkpoint only when one is actually committed.

Any customer-facing statement such as:

- "by tomorrow",
- "within two hours",
- "we will refund after X",
- "this will ship in version Y",

creates or changes a commitment and must be tracked.

After a missed commitment, do not repair trust with a new speculative promise. Establish
what is actually known, owner, and next realistic checkpoint.

## 5. Sensitive data

Before sending/publishing/copying content, minimize:

- credentials/secrets/tokens/cookies/auth headers,
- payment card/banking details,
- private URLs containing tokens,
- unnecessary customer names/emails/phone numbers,
- proprietary datasets/content not needed for the task,
- contract/pricing details irrelevant to the recipient,
- security exploit detail outside restricted channels.

Use internal case/account IDs where possible.

Private GitHub/internal chat is not automatically an unrestricted data destination.

## 6. Credits, refunds, concessions

Do not promise or apply:

- service credit,
- refund,
- discount,
- free extension,
- custom SLA/remedy,

unless the user explicitly authorizes the action and the relevant policy/amount/eligibility
is known or the appropriate approval workflow is completed.

A customer asking for a refund is evidence of dissatisfaction/financial request, not
automatic eligibility.

## 7. Security/privacy/legal escalations

If a message contains or alleges:

- unauthorized access,
- secret exposure,
- personal/confidential data exposure,
- data loss/corruption,
- formal legal demand/threat,
- regulatory request,
- fraud/material financial harm,

preserve evidence, limit distribution, and route to the specialist gate. Do not improvise
legal breach-notification conclusions or technical exploitation steps in ordinary support.

Customer-facing messaging should be coordinated with the authorized specialist/incident
owner where required.

## 8. Tone

Use concise transactional language:

- acknowledge concrete impact without performative empathy,
- use the customer's terminology when accurate,
- avoid blame,
- avoid marketing copy in incident/support messages,
- avoid over-apologizing in place of information/action,
- provide one clear next step/checkpoint.

For a serious incident, clarity and consistency matter more than sounding reassuring.

## 9. Pre-send checklist

Before `send/reply/publish` verify:

```text
recipient/channel correct
latest customer ask read
current case/incident state verified
facts sourced and certainty calibrated
root cause/ETA not invented
workaround safe and current
message does not conflict with canonical incident comms
new commitments identified/trackable
unnecessary PII/secrets removed
requested send/publish authority present
```

After sending, record the communication source ID/time and any new commitment.
