# Contributing

Thanks for improving CometWeb Agent Skills. This repo optimizes for **evidence-backed,
tested skills** — not prompt volume.

## What belongs here

- Deterministic scripts, validators, kernels
- Tests and eval fixtures (routing, golden cases)
- SKILL.md + references scoped to one skill
- CI-safe changes (run `./scripts/run_all_checks.sh`)

## What does not belong here

- GTM / promotion playbooks, outreach calendars, “how to get stars” guides
- Council or product **strategy memos** meant for internal GTM (use `private-workspace/`)
- Secrets, Notion UUIDs, customer data
- Bulk-generated skills without tests

See [`AGENTS.md`](AGENTS.md) for the full public-vs-private split.

## Before a PR

```bash
./scripts/public-safety-check.sh
python3 scripts/validate_skills.py
python3 scripts/run_routing_evals.py
./scripts/run_all_tests.sh
```

Before tagging a release, also run the history pass:

```bash
./scripts/public-safety-check.sh --history
```

It applies the same leak rules to every commit ever made, not just the working
tree. It is not part of CI, because a file removed from `HEAD` stays in history
until someone rewrites it — so this check reports the known 2026-08-26 incident
and will keep doing so until that rewrite happens.

## Skill quality bar (vs typical prompt repos)

| Expectation | CometWeb bar |
| --- | --- |
| SKILL.md only | + scripts and/or schemas where claims are enforceable |
| No tests | pytest or unittest for kernels/validators |
| Vague routing | Explicit negatives in description + routing eval case |
| Silent handoffs | CW-AIP envelope fields in output contracts |

## Adding a routing eval case

Edit `evals/routing/suite.json` and update `scripts/run_routing_evals.py` signals if needed.

## Releases

Maintainers: `./scripts/package-releases.sh vX.Y.Z` then GitHub Release with `dist/*.zip`.
