# Routing eval suite

Structured cases for cross-skill **implicit routing** before `SKILL.md` loads.

Each case in `suite.json`:

- `prompt` — user message
- `expected_primary_skill` — skill that should win
- `allowed_secondary_skills` — acceptable co-triggers
- `must_not_trigger` — skills that must not be primary
- `reason` — routing rationale for reviewers
- `lang` — optional, `en` (default) or `pl`; counts the case toward that
  language's coverage floor

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

Floors also apply per language (`LANGUAGE_FLOORS` in
`tooling/routing_coverage.py`): every active skill needs at least three Polish
cases that expect it and one Polish boundary case where a neighbouring skill
wins and it is forbidden. Write them as a Polish-speaking user would phrase the
request (mixed Polish/English terms included), not as translations of registry
examples. A prompt containing Polish letters must be tagged `"lang": "pl"`, so a
Polish case cannot silently miss the count.

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

## Negation

`registry/routing-policy.json` → `negation` keeps a routing signal from scoring
when the words it matches sit inside a negated clause, so "Do not review the
codebase, just fix the failing test" or "Nie rób przeglądu repo, tylko popraw
literówki" no longer route to the skill they turn down. The rule is
deterministic and bounded:

1. The normalized prompt is cut into clauses at `boundary`: punctuation
   (`. , ; : ! ? ( ) [ ]`), a spaced hyphen or dash, and contrast or
   subordinating words — `but`, `just`, `only`, `then`, `and`, `until`,
   `unless`, `before`, `after`, `if`, `when`, `while`, `tylko`, `jedynie`,
   `ale`, `lecz`, `potem`, `i`, `oraz`, `zanim`, `dopóki`, `aż`, `jeśli`,
   `gdy`, `kiedy`, `chyba że`, and so on. Polish `i` ("and") also matches the
   English pronoun "I" after casefolding; that can only shorten a scope.
2. In each clause the earliest `cues` match opens the negation, which runs to
   the end of that clause and never further than `max_scope_chars` (80).
   Cues are: a clause-initial prohibition (`do not`, `don't`, `never`, `skip`,
   `no`, `nie`, optionally after `please`/`proszę`); `don't want|need|have
   to`, `no need to`; `instead of`, `rather than`, `zamiast`; and Polish
   `nie` + a listed imperative or need verb (`nie rób`, `nie chcę`,
   `nie potrzebuję`, …) anywhere in the clause.
3. Negated text is blanked (offsets kept) before routing signals are matched,
   so a greedy signal such as `roast.*codebase` cannot start in a positive
   clause and finish in a negated one. A narrow-intent guard's `unless`
   exception is read from the same blanked text: "Don't humanize it, just fix
   typos" does not lift the `ai-humanize` guard.

What it deliberately does not do:

- A bare `not` is not a cue: "find what's not working" still scores.
- `without` and `bez` are not cues. They usually qualify a request ("close
  findings without regressions", "shipped without outcome evidence") rather
  than refuse one.
- Mid-clause `nie` with a verb outside the list ("czy strona nie działa")
  is not a cue.
- Explicit invocations (`$skill`, `use <skill-id>`, `explicit_patterns`),
  `_denied_by_name` and `denied_patterns` keep their own rules; negation
  only touches signals and guard exceptions.
- Scope ends at the clause: "Don't hold back: roast this repo", "Don't ship
  v3.1 until release readiness gives a GO verdict" and "Roast the repo, but
  don't touch the docs" still route to the requested skill.

Cue and boundary patterns go through the same safe-regex check as signals (no
nested quantifiers, 4096-character cap); `max_scope_chars` must be 1–400 and
there are at most 32 cues. `suite.json` (`negation-*`) and
`policy-suite.json` hold the positive and negated near-miss cases in English
and Polish.

## Multi-skill requests

`registry/routing-policy.json` → `sequence` routes a request that hands
different steps to different specialists — "audit the signup flow, then gate
release 2.5.0", "zweryfikuj claimy, a potem niech Rada oceni" — to the workflow
skill (`skill-orchestrator`), as the routing rules prescribe for multi-step
work. The rule:

1. Cuts the negation-masked prompt at `connector` matches: `then`,
   `afterwards`, `after that`, `once that is done`, `potem`, `następnie`,
   `a po nim/niej/tym`, `po czym`, `na tej/ich podstawie`, `w oparciu o`, `->`.
2. In each step, the single highest-scoring specialist with at least
   `min_step_score` (7) is that step's skill. An explicit-only skill such as
   the Council counts when its own signals name it ("then take it to the
   council", "niech Rada zdecyduje"); skills excluded by name or by a
   narrow-intent guard never count.
3. Two or more distinct step skills → `status: workflow`, primary
   `skill-orchestrator`, and the steps in `sequence`.

It does not fire when the router already chose the workflow skill or its
multi-agent alias, when the workflow skill is excluded ("without
skill-orchestrator"), or when the host passed an explicit invocation. A step in
a negated clause ("…, then do not run the release gate") is blanked before
scoring, and the same specialist in every step stays a single-skill route.

## Known gaps

`known-gaps.json` pins prompts the deterministic router misroutes today, with
the misroute it produces (`observed_primary_skill`, `observed_status`) and why
it is wrong. They do not count toward the floors. A gap that starts routing as
expected fails `--check` until it is moved into `suite.json`; a gap whose
misroute changes must be re-recorded. Fix routing signals, do not delete gaps
to make the check pass.

The `holdout-*` gaps are Polish and multi-skill prompts from the hash-split
holdout halves of the October 2026 routing pass. Signals were tuned only on the
tune halves, and these are the held-out prompts that still misroute; they are
recorded rather than tuned away so the measurement stays honest. Once someone
tunes on them they stop being a holdout: write fresh prompts to measure the
next change.

`--trigger-evals` replays the roaster skills' own `evals/trigger-evals.json`
through the same router. Those files were written for model-based triggering,
so the result is a deterministic-proxy discovery estimate, not a model result.
`--check` still holds the roasters to the recall, rejection and near-miss
floors in `TRIGGER_EVAL_FLOORS` (in `tooling/routing_coverage.py`), set just
under the measured numbers; raise a floor when routing improves, never lower
one to make a signal change pass.

## Confusion report

```bash
uv run python tooling/routing_coverage.py --confusion          # table
uv run python tooling/routing_coverage.py --confusion --json   # full rows
```

Replays every routing label the repository already holds — `suite.json`, each
skill's `evals/trigger-evals.json`, natural (not force-invoked) prompts in
`evals/real-host.json`, and registry trigger/negative examples — and lists the
expected-to-routed pairs, per-skill recall and false positives, and every
misroute. Each prompt falls in a stable `tune` or `holdout` half (by hash of the
normalized prompt). When tuning routing signals, read only the tune half's
failures and report the holdout half's numbers before and after, so a signal
that memorizes one phrasing shows up as a holdout that did not move. Known gaps
are not replayed here; `--check` already pins them.

## Adversarial cases

`adversarial-suite.json` runs through `tooling/run_policy_evals.py --suite` and
checks the instruction boundary in `registry/routing-policy.json` →
`untrusted_text`. Pasted content inside a prompt must not grant an explicit
invocation, unlock an explicit-only skill, or lift a denial. That covers
override phrases ("ignore previous instructions", "you are now", "zignoruj
poprzednie instrukcje"), quoted, fenced or blockquoted invocations, and
zero-width characters inside a denied skill name. The `adv-control-*` cases show
that legitimate invocations still route, including a request *about* injection
attacks. `tooling/tests/test_routing_adversarial.py` also removes each mechanism
in turn and checks that the attack cases then fail.
