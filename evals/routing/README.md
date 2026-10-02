# Routing eval suite

Structured cases for cross-skill **implicit routing** before `SKILL.md` loads.

Each case in `suite.json`:

- `prompt` — user message
- `expected_primary_skill` — skill that should win
- `allowed_secondary_skills` — acceptable co-triggers
- `must_not_trigger` — skills that must not be primary
- `reason` — routing rationale for reviewers

CI validates schema and coverage (including the Product Operator / Repo to
Roadmap / Release Readiness collision set). LLM routing accuracy is measured
operator-side by replaying prompts against your host's skill picker.

## Coverage floors and hollow cases

```bash
uv run python tooling/routing_coverage.py            # per-skill table
uv run python tooling/routing_coverage.py --check    # what the test suite enforces
uv run python tooling/routing_coverage.py --trigger-evals   # plus skill-local trigger evals
```

Every active skill needs at least three cases that expect it and two that
forbid it in `must_not_trigger`. One positive case only shows the router can
reach a skill; the negatives show its neighbours are told "not this one".
The table splits negatives into *boundary* cases (another skill should win) and
*out-of-scope* cases (no skill should).

`--check` also rejects cases that make a green run say less than it seems:
duplicate IDs, prompts that are identical after case/accent/punctuation
normalization, skill IDs the registry does not know (a typo in
`must_not_trigger` would otherwise check nothing), a skill both expected and
forbidden, and prompts copied from a registry `trigger_examples` /
`negative_trigger_examples` entry. Registry examples are already routed by
`tooling/tests/test_registry_self_consistency.py`; paraphrase instead of
copying. Near-duplicates (token overlap ≥ 0.8) are listed but not failed.

`canonical-suite.json` is deliberately built from registry examples and is not
held to the copy rule; `policy-suite.json` is a policy-admission contract run
against both a synthetic and the real registry.

## Known gaps

`known-gaps.json` pins prompts the deterministic router misroutes today, with
the misroute it produces (`observed_primary_skill`, `observed_status`) and why
it is wrong. They do not count toward the floors. A gap that starts routing as
expected fails `--check` until it is moved into `suite.json`; a gap whose
misroute changes must be re-recorded. Fix routing signals, do not delete gaps
to make the check pass.

`--trigger-evals` replays the roaster skills' own `evals/trigger-evals.json`
through the same router. Those files were written for model-based triggering,
so the result is a deterministic-proxy discovery estimate, not a model result.
`--check` still holds the roasters to the recall, rejection and near-miss
floors in `TRIGGER_EVAL_FLOORS` (in `tooling/routing_coverage.py`), set just
under the measured numbers; raise a floor when routing improves, never lower
one to make a signal change pass.
