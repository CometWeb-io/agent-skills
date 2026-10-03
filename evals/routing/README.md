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

The fifteen `holdout-*` gaps from the first Polish and multi-skill pass (October
2026) now route correctly and live in `suite.json` under their old IDs. They
were fixed with general signals during the round-4 pass, so they are tuned-on
prompts now, not a holdout. The two `r4b-skill-orchestrator-*` gaps are
multi-step requests whose later step names its target only by pronoun ("then
roast it") or uses "roadmap" as a verb; no specialist reaches
`min_step_score` there, so the sequence rule sees one step.

`--trigger-evals` replays the roaster skills' own `evals/trigger-evals.json`
through the same router. Those files were written for model-based triggering,
so the result is a deterministic-proxy discovery estimate, not a model result.
`--check` still holds the roasters to the recall, rejection and near-miss
floors in `TRIGGER_EVAL_FLOORS` (in `tooling/routing_coverage.py`), set just
under the measured numbers; raise a floor when routing improves, never lower
one to make a signal change pass.

## Frozen holdout

`holdout.json` is the honest number. Every other routing set here has been read
while signals were edited, so its pass rate flatters the router; the October 2026
confusion report's "holdout" half routed 308/308 while 144 freshly written
prompts routed 93/144.

```bash
uv run python tooling/routing_holdout.py --check   # integrity (a check_all gate)
uv run python tooling/routing_holdout.py           # aggregate accuracy
```

The protocol:

1. The prompts were written before their author read the routing signals:
   positives for every active skill, near-misses (a neighbouring skill or no
   skill must win, and the tempting one is forbidden) and plain no-skill
   requests, in English and Polish.
2. The file is pinned by sha256 in `holdout.lock.json`. Any edit, whitespace
   included, fails `--check` until `holdout_version` is bumped and
   `--record` pins the new hash. `--record` will not give a recorded version a
   second hash.
3. Never tune on it. The tool prints aggregates (overall, per kind, per
   language) and never which prompts failed; do not write one that does. Tune on
   `suite.json`, the known gaps and fresh prompts of your own, then read the
   holdout once and append the result with `--log "<label>"`. The measurement log
   in the lock is append-only.
4. No holdout prompt may appear, after normalization, in `suite.json`,
   `known-gaps.json`, the canonical, policy or adversarial suites, or a registry
   example. Near-duplicates (token overlap ≥ 0.8) may not grow past
   `max_near_duplicates` in the lock (1, a no-skill prompt that happened to
   resemble an older suite case).
5. When the holdout has been read too often to mean anything, or a prompt
   leaked, write a new version with fresh prompts rather than editing this one.

A case passes when the primary skill equals `expected_primary_skill` and no
`must_not_trigger` skill is primary or a candidate, the same rule
`run_routing_evals.py` applies.

| Holdout 1.0.0 (144 cases) | Baseline | After round 4 |
| --- | ---: | ---: |
| Overall | 93 (64.6%) | 112 (77.8%) |
| Positive (100) | 60 | 76 |
| Near-miss (26) | 15 | 18 |
| No skill (18) | 18 | 18 |
| English (100) | 58 | 73 |
| Polish (44) | 35 | 39 |

The round-4 column is the second of two reads, both in the lock's log. The
first (113/144) came before two signal changes that pinned policy tests
forced: "take it to the council" is not an explicit Council invocation, and a
roadmap-plus-this-week prompt stays ambiguous. Neither change used holdout
results.

Round 4 tuned on 214 fresh prompts in three batches, each routed before any
signal it motivated was written. Measured that way, the gain on unseen prompts
was smaller than on the batch being tuned: the second batch routed 38/68 on the original router
and 42/68 on the first round's signals, the third 22/44 and 28/44 on the
signals written before it. Expect the next unseen set to land nearer those
numbers than the 100% the tuned sets now show.

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
