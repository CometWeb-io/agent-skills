# Bounded user pilot: one workflow

This is a feedback contract for testing an **experimental** package, not a claim of qualification. It suits developers and small product teams who already use an AI coding agent for web-app QA.

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

To submit **sanitized public** feedback, [open a GitHub issue](https://github.com/CometWeb-io/agent-skills/issues/new) and describe the task, observed result and friction without attaching private artifacts. Do not open a public issue for sensitive feedback; retain it privately until a mutually agreed private channel exists.

Avoid sending customer records, private source code, credentials or unrestricted tool transcripts. Permission to receive feedback is not permission to publish or quote it.
