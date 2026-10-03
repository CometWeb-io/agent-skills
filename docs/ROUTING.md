# How routing works

A host picks a skill by reading each skill's `description`; that is a model
decision and this repository cannot run it. What the repository can check is
whether the registry's claims about each skill hold together. For that,
[`tooling/route_skill.py`](../tooling/route_skill.py) routes a prompt
deterministically from two files:

- `registry/skills.json`: each skill's `routing_signals` (`[weight, regex]`
  pairs), `explicit_only` and `alias_of`;
- `registry/routing-policy.json`: the admission rules below.

Every result carries `"mode": "deterministic_proxy"` and
`"runtime_acceptance": "not_assessed"`. It is not a model evaluation and not a
permission boundary. Pass it the user's instruction only, never retrieved
document text.

```bash
uv run python tooling/route_skill.py 'Click through the checkout and find UX bugs, then decide if release 2.5.0 is ready to ship'
```

## The steps, in order

1. **Normalize.** Casefold, strip accents (`ł` becomes `l`), and drop invisible
   format characters such as zero-width spaces, so a hidden character cannot
   split a skill name.
2. **Set aside untrusted text.** Fenced code, blockquote lines and text in
   double or typographic quotes are someone else's words. So is everything
   from the first override cue ("ignore previous instructions", "you are
   now", "zignoruj poprzednie instrukcje") to the end of the prompt. Neither
   can invoke a skill or score a signal (`untrusted_text`).
3. **Read invocations.** `$skill-id` or `@skill-id`, "use / run / invoke / load
   *skill-id*", and the skill's `explicit_patterns` invoke it. They are read
   from the user's own text only.
4. **Read denials.** "don't use *skill-id*", "without *skill-id*", "bez
   *skill-id*" and the skill's `denied_patterns` exclude it. Denials are read
   from the whole prompt, quotes included, so pasted text can never lift one.
   Excluding a skill also excludes its aliases.
5. **Hold back explicit-only skills.** A skill with `explicit_only: true`
   (the Council) is blocked unless step 3 invoked it.
6. **Apply narrow-intent guards.** When a guard's `when` matches and its
   `unless` does not, the skill is blocked as `outside_declared_scope`:
   "fix typos" alone is not a request for `ai-humanize`
   (`narrow_intent_guards`).
7. **Score signals.** Each remaining skill sums the weights of its signals that
   match. Text inside a negated clause is blanked first, so "Don't review the
   codebase, just fix the test" does not score the reviewer (`negation`).
8. **Choose.** Invoked skills win over scores. Otherwise the top score wins,
   but if a different specialist is within one point of it the result is
   `ambiguous` rather than a silent pick (`ties`). Two or more invoked skills
   make a workflow handled by the workflow skill (`workflow_skill`).
9. **Detect sequences.** A prompt cut at "then", "potem", "->" and similar
   connectors whose steps are won by different specialists routes to the
   workflow skill, with the steps listed in `sequence` (`sequence`).

The result reports `status` (`single_skill`, `workflow`, `ambiguous` or
`no_skill`), `primary_skill`, `candidates`, `scores`, the reason each skill was
`blocked`, and `override_suspected`.

## Policy blocks

| Block | What it holds |
| --- | --- |
| `explicit_patterns` | Per skill, extra phrasings that count as invoking it ("przepuść przez Radę"). |
| `denied_patterns` | Per skill, extra phrasings that exclude it. |
| `narrow_intent_guards` | Per skill, a `when` / `unless` pair that keeps a narrow request away from a broad skill. |
| `negation` | Negation `cues`, the clause `boundary`, and `max_scope_chars` (1–400) for how far a negation reaches. |
| `sequence` | The step `connector` and `min_step_score`, the score a specialist needs to own a step. |
| `untrusted_text` | The `override_cues` after which nothing counts as the user's instruction. |
| `ties` | The outcome of a near-tie between specialists: `ambiguous`. |
| `workflow_skill` | The skill that runs multi-step work: `skill-orchestrator`. |

Every pattern, in the policy and in the registry, passes the same safety check:
at most 4,096 characters and no nested quantifiers, so a prompt cannot make a
pattern backtrack for minutes.

## Known gaps

- Hosts do not run this router. A green routing suite shows the registry is
  self-consistent, not that a model will pick the same skill.
- [`evals/routing/known-gaps.json`](../evals/routing/known-gaps.json) lists
  prompts the router misroutes today, with the misroute pinned; a gap that
  starts routing correctly fails the check until it is moved into the suite.
- A bare "not", "without" and "bez" are not negation cues, because they usually
  qualify a request ("ship without regressions") rather than refuse one.
- Only double and typographic quotes mark quoted text; single quotes do not.
- Override cues exist for English and Polish only.
- A sequence needs a connector word. With "then", the checkout example above
  is a two-step workflow; with "and" it routes to `release-readiness` alone,
  because the release gate outscores the auditor and no step boundary is seen,
  so the click-through step is dropped.
- The router always returns `ambiguous` on a near-tie; `ties` records that
  outcome but is not read, so changing it changes nothing.

## Adding a case

1. Reproduce the route: `uv run python tooling/route_skill.py '<prompt>'`.
2. Add the prompt to `evals/routing/suite.json` with the skill that should win
   and the ones that must not (`"lang": "pl"` for Polish). Instruction-boundary
   attacks go in `adversarial-suite.json`; a misroute you are not fixing now goes
   in `known-gaps.json`.
3. Fix the cause, not the case. Signals for skills listed in `OVERRIDES` in
   `tooling/sync_skill_registry.py` are edited there and written with
   `uv run python tooling/sync_skill_registry.py --apply`; other skills' signals
   are edited in `registry/skills.json`. Policy changes go in
   `registry/routing-policy.json`.
4. Run `uv run python tooling/check_all.py --fast`. It runs the routing suite,
   the coverage floors, the policy and adversarial suites, and the known-gap
   check. Before and after a signal change, compare the holdout half in
   `uv run python tooling/routing_coverage.py --confusion`.

Case fields, coverage floors, the full negation and sequence rules, and the
holdout method are in [`evals/routing/README.md`](../evals/routing/README.md).
