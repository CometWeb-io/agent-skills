# Bounded user pilot: one workflow

This is an invitation and feedback contract for testing an **experimental** package, not a claim of qualification. First audience: developers and small product teams already using an AI coding agent for web-app QA.

## What to test

1. Pick one **disposable** application/task you can safely inspect and modify, or use the [synthetic QA example](../examples/qa-repair-retest/README.md).
2. Run the same task with your normal host, model and tools **without** the skill.
3. Install only the needed package, repeat under matched conditions and document any differences.
4. Report observed outcome and friction. You may report a failure. There is no requirement to publish private project files.

Use [START-HERE.md](START-HERE.md) for the walkthrough and [PROVE-IT.md](PROVE-IT.md) for meaningful comparisons.

## Private pilot feedback form

Copy this into your own private note or issue; remove secrets before sharing it publicly.

```text
Date / timezone:
Agent host + version / model:
Skill(s) + pinned source commit:
Task and predeclared acceptance check:
What worked without the skill:
What worked with the skill:
What changed in tools, permissions, retries or setup:
Observed final result (pass / fail / not assessed):
Time, tokens and costs (unknown is valid):
Wrong assumptions, unwanted actions or false success claims:
Would you use it for a second task? Why or why not?
One change that would make it worth keeping:
May this feedback be quoted publicly? (default: NO)
```

Avoid sending customer records, private source code, credentials or unrestricted tool transcripts. Permission to receive feedback is not permission to publish or quote it.

## What counts as adoption?

- **Visit:** a person opens the project page; only use this if measured by a permitted source.
- **Install:** a package gets installed; CLI telemetry is an imperfect proxy, not an individual identity.
- **Activation:** a distinct developer completes the first demo/task and can show the expected result.
- **Retained use:** the same consenting developer voluntarily uses it again on another task.
- **Qualified evidence:** an independently reviewed comparison with matched conditions and documented outcome.

Do not call install count, GitHub stars or a passing test an activation. Do not infer retention from one interview. Never manufacture testimonials.

## Pilot decision after an initial cohort

Record the full denominator: invited, accepted, attempted, activated, returned and explicitly declined. Separate setup failure from task failure. Log objections and the task context behind them.

- If people cannot finish the first task, repair onboarding before distributing more broadly.
- If they finish but do not prefer the skill, compare it against the native control and investigate unnecessary overhead.
- If they return for a second task and describe a specific improvement, expand only that validated use case.
- If the benefit is unproven, retain the experimental label and do not publish improvement percentages.
