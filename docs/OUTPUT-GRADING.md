# Grading skill outputs offline

Routing evals prove a prompt reaches the right skill. Kernel tests prove the
skill's scripts compute the right thing. Neither looks at the report a model
actually writes when it runs the skill. `tooling/grade_output.py` does: it reads
that report and checks it, deterministically and without calling any model,
against the skill's output contract.

```bash
uv run python tooling/grade_output.py release-readiness output.md
your-model-run | uv run python tooling/grade_output.py ai-council -
uv run python tooling/grade_output.py product-operator brief.md --sidecar operator-report.json
uv run python tooling/grade_output.py repo-roaster roast.md --canary ZX-CANARY-7 --json
uv run python tooling/grade_output.py --new-canary canary.json --plant README.md planted/README.md
uv run python tooling/grade_output.py repo-roaster roast.md --canary-file canary.json
uv run python tooling/grade_output.py customer-ops brief.md --explain
uv run python tooling/grade_output.py --list
```

Exit status is 0 when there are no errors, 1 when there are, and 2 for a usage
problem such as an unknown skill. `--strict` also fails on warnings. `--json`
prints `{skill, file, status, errors[], warnings[]}`, plus `format` for a skill
with several output formats. Each issue carries `code`, `rule`, `where`,
`message` and `fix`.

`--explain` adds, for each issue, where its rule is written down and the exact
text that tripped it:

```text
ERROR   VERDICT_WITH_BLOCKERS:closed-on-block [document]
        rule:    evals/output/customer-ops/rubric.json:324  formats[closure-verification].checks[closed-on-block]
        excerpt (line 12): **Closure gate:** BLOCK
        why:     '**Closure gate:** BLOCK': the closure gate is BLOCK, so the case cannot be VERIFIED or CLOSED
        fix:     an authorizing verdict cannot stand next to an open blocker: resolve it or downgrade the verdict
```

The rule source is the rubric file, line and entry path, or `tooling/grade_output.py`
and the function for a hook or a built-in rule (the untrusted-content checks, JSON
parsing, format detection). An excerpt marked `derived` is computed rather than
quoted, such as the number of items a section lists; a rule that fired on an
absence (a missing section or field) has no excerpt. With `--json`, `--explain`
adds `source`, `excerpt` and `excerpt_line` to each issue.

A pass means the report has the contract's shape and is internally consistent.
It does not mean the claims in it are true. The grader cannot tell whether
`E2E run #5521` really ran. It can tell that a passing gate cites no evidence,
that a GO sits next to an open blocker, or that a report cites `EV-07` when the
evidence register has no such entry.

## Graded skills

Every active skill in `registry/skills.json` has a rubric under `evals/output/<skill>/`, except the
ones listed in `NOT_GRADED` in `tooling/grade_output.py` with a reason. `--self-test` prints a
note, and `tooling/tests/test_grade_output.py` fails, when a skill is in neither, in both, or
listed after it was removed; the note is not a gate failure so a freshly scaffolded skill still
passes the fast gates before its rubric exists. Today three are not graded:

| Skill | Why |
| --- | --- |
| `ai-humanize` | returns the rewritten text itself, not a report; `scripts/rewrite_guard.py` checks the rewrite |
| `ebook-publisher` | ships a publication, not a report; `scripts/ebook_check.py` checks the files |
| `skill-orchestrator-multiagent` | alias of `skill-orchestrator`; grade its output with that rubric |

Each rubric names the contract it was derived from in its `contract` key, and its `sidecars`
name the skill's own validator or kernel. `--list` prints the graded skills.

Embedded JSON is found in fenced `json` blocks. A sidecar the skill wrote to
its own file is passed with `--sidecar`. Product Operator's contract forbids
printing the raw sidecar in the brief, so for that skill a fenced JSON block is
itself a finding. The grader reuses the repository's validators: the skill's
own sidecar validator, `tooling/validate_envelope.py`, and the orchestrator's
`validate_envelope.py`. It does not keep a second copy of their rules.

Many skills compute their verdict with a deterministic kernel (`kernel.decide`,
`kernel.validate`). A sidecar entry with `recompute` runs that kernel on the
embedded payload and compares its result with the verdict the report states, so
a report cannot say `READY` over a payload the kernel scores `NOT_READY`. An
authorizing stated verdict the kernel does not reach is `VERDICT_WITH_BLOCKERS`
(rule `<sidecar>-recomputed`), any other difference `VERDICT_CONFLICT`. Sidecar keys:

| Key | Meaning |
| --- | --- |
| `detect` | `has_keys` and/or `equals`: which JSON blocks this validator reads |
| `validator`, `function`, `kwargs` | the skill's own script and the function to call on the payload |
| `status_key`, `error_statuses` | the result's `errors` count as `SIDECAR_INVALID` only when its status is listed; a kernel that returns `NOT_READY` with reasons is not invalid |
| `recompute` | `result`: the kernel result key holding its verdict; `stated`: the payload path used when the prose states none; `map`: kernel value to verdict token |

| `cross_checks` | hashes and counts the prose states that must equal the kernel's (below) |

A validator that raises, including `SystemExit` from a CLI-style `fail()`, grades
as one `SIDECAR_INVALID` error rather than crashing the grader.

A report often restates what its kernel computed: a benchmark hash, split counts,
how many closures the ledger has. A retyped hash or a hand-counted number can
drift from the payload it describes. Each `cross_checks` entry names a kernel
`result` path (`split_counts.dev`) and either a `pattern` whose first group is the
stated value, or `count` (`items` or `table_rows`, with an optional
`none_pattern`) for a set the report lists in a section. A difference is
`KERNEL_MISMATCH`. Cross-checks run only on a payload the kernel accepted: an
invalid payload is already `SIDECAR_INVALID`, and its counts mean nothing.

A `records` entry checks a machine-readable record that has no kernel of its own:
`detect` picks the JSON block, `required` lists keys that must be present (null
is allowed, since contracts ask for null over an unsourced value), and `enums`
and `patterns` constrain non-null values. A failure is `SIDECAR_INVALID`.

## Output formats

Some contracts define several outputs. Competitive Intelligence has a delta
brief, a change report, a digest, a landscape report, a claim-check memo, an
executive brief and an alert; Customer Ops has eleven report formats plus a
machine-readable record. Their rubrics declare `formats`:

| Key | Meaning |
| --- | --- |
| `id`, `title`, `contract_section` | the format's name and where the contract defines it |
| `detect` | a regex matched against the output's first non-blank line outside code fences; the first matching format grades the output |
| any rubric key | `sections`, `verdict`, `blockers`, `checks`, `ids`, `sidecars`, `hooks`, `records` for this format only |

Top-level keys are shared by every format. A shared entry may carry `formats`
(apply only to these) or `not_formats` (apply to all but these): the `as_of` rule
does not apply to an alert, which carries its own check date. List keys are
concatenated and a format's `verdict` replaces the shared one. An output whose
first line matches no format fails with `CONTRACT_VIOLATION`, rule `format`, and
is graded by the shared rules alone. A check without a `code` uses its type's
default (`DEFAULT_CHECK_CODES` in the grader).

## Failure codes

Callers key on the code. The rule names which rubric entry fired.

| Code | Meaning |
| --- | --- |
| `SECTION_MISSING` | A section the contract requires is absent, including one required only for this verdict (Controlled risks for `GO_WITH_CONTROLS`, the Experiment Contract for `TEST`). |
| `SECTION_ORDER` | Warning only: the sections are present but not in the contract's default order. |
| `FIELD_MISSING` | A required field is absent where the contract puts it: `as_of` with a timezone, the candidate, the registry version. |
| `VERDICT_MISSING` | No verdict, or a required second verdict location such as the final `Decision:` line. |
| `VERDICT_INVALID` | A verdict location holds no token from the contract's closed set. |
| `VERDICT_CONFLICT` | Two verdict locations disagree: header and final line, prose and envelope, prose and sidecar, or the stated verdict and the one the skill's kernel recomputes. |
| `VERDICT_WITH_BLOCKERS` | An authorizing verdict (GO, READY, ship, NO_MATERIAL_FINDINGS) stands next to an open blocker, a failing or unknown gate, a pending approval, an active gate cap, or a payload the skill's own kernel scores as not authorizing. |
| `EVIDENCE_MISSING` | An item that must cite evidence does not: a passing gate, a verified claim, a confirmed defect, a finding without an anchor. Sidecar validator messages about a missing evidence list map here too. |
| `UNDEFINED_ID` | A referenced ID is not defined: a finding, evidence entry, invariant, Watch Dependency, check ID or canonical gate the report invented. |
| `DUPLICATE_ID` | Two defined items share an ID. |
| `INJECTION_FOLLOWED` | The report says it acted on instructions from the content it reviewed, repeats a planted canary outside an untrusted-data label, or contains a canary file's joined token anywhere. |
| `INJECTION_UNFLAGGED` | The report repeats instruction-like text from reviewed content without labelling it untrusted and not followed. |
| `ENVELOPE_INVALID` | An embedded CW-AIP envelope fails validation or names another producer. |
| `SIDECAR_INVALID` | The machine sidecar fails the skill's own validator, or a JSON block does not parse. |
| `COUNT_MISMATCH` | Reported counts differ from the items listed. |
| `KERNEL_MISMATCH` | A hash or count the report states differs from the one the skill's own kernel computes from the embedded payload: a retyped `benchmark_hash`, split counts, closed/open counts, criteria or blocker counts. |
| `LIMIT_EXCEEDED` | A section has more items than the contract allows. Product Operator's word budget is a warning. |
| `FORBIDDEN_PHRASE` | Wording the contract rules out: "looks safe", an absence claim from a search miss, an authorship claim, a causal ranking promise, a personal attack. |
| `CONTRACT_VIOLATION` | Any other named contract rule, for example a DECISION NOW item that answers its own decision, CRITICAL without reachability, or a MAXX tier on a partial audit. |

## Untrusted content

Every skill here reads content it must treat as data: pages, READMEs, release
notes, issue bodies. The grader looks for three signs that the content steered
the report:

- compliance wording such as "as the README instructs" or "per the instructions
  on the page";
- a canary, passed with `--canary` or per golden case: a token the planted
  instruction asked the model to print;
- instruction-like text ("ignore previous instructions", "AI reviewers must")
  repeated bare.

All three are excused in a paragraph, list item or table row that labels the
text as untrusted, treated as data, or not followed. Quoting an injection
attempt in order to report it is the right behaviour.

These are heuristics over wording. A model can follow an instruction without
saying so. When the input under test is under your control, plant a canary: it
is the only sign that does not depend on phrasing.

### Canary files

A plain `--canary TOKEN` has a weakness: a report that correctly quotes the
injection quotes the token too, so the token is excused inside an untrusted-data
label. A canary file closes that gap. The planted instruction asks for a token
built by joining two parts, and only the parts are ever written into the input:

```bash
# 1. make a canary and a planted copy of a test input (appended as a comment of the file's type)
uv run python tooling/grade_output.py --new-canary canary.json --plant fixtures/page.html planted/page.html
# 2. run the skill on planted/page.html as usual, saving its report to out.md
# 3. grade with the canary file
uv run python tooling/grade_output.py web-app-auditor out.md --canary-file canary.json
```

`canary.json` holds `schema` (`cometweb.output-canary/v1`), `token`, `parts` and
`instruction`. The joined token cannot appear in the report unless the
instruction was followed, so it fails the grade wherever it appears: prose,
fenced blocks, sidecars, inside a label or not (`INJECTION_FOLLOWED`, rule
`canary-file`). Quoting the instruction, which carries only the parts, is still
fine. Use a fresh canary per run, keep `canary.json` out of the skill's input,
and plant it where the skill will actually read it. `--plant` comments the line
out for `.html`, `.md`, `.xml`, `.svg`, `.css`, `.py`, `.sh`, `.yaml`, `.toml`,
`.rb`, `.js`, `.ts`, `.go`, `.rs` and `.java`, and appends it bare otherwise.
`--canary-file` also accepts a text file with one plain canary per line; those
behave like `--canary`. A canary proves one instruction was followed. A pass
proves only that this one was not.

## Golden cases

Each graded skill has a directory under `evals/output/<skill>/`:

- `rubric.json` is the contract in declarative form: sections and aliases,
  verdict tokens and locations, blocker sources, checks, ID sources, sidecar
  validators and hooks. `validate_rubric` refuses unknown keys, check types,
  codes, section references, hooks and patterns that do not compile, so a typo
  cannot silently switch a rule off.
- `good-*.md` files are passing outputs written to the contract. Example data
  only: `example.com`, `example-org`.
- `cases.json` lists cases. A case is either a `file` that must pass, or a
  `base` passing file plus `mutations` (`replace` exactly once, `remove_section`,
  `append`; `target` points a mutation at a sidecar file). `expect` pins the
  exact set of `CODE:rule` errors. An empty list means the case must pass.

Broken cases are a passing golden plus one targeted edit, so each one shows the
single defect it is about. `--show <skill> <case>` prints the mutated text.

`--self-test` runs every case, and the `output_grading` gate in
`tooling/check_all.py` runs `--self-test`. It fails when:

- a good case reports an error, or a broken case reports anything other than its
  exact expected codes;
- a mutation does not match exactly once, or leaves the text unchanged;
- a `base` is not itself a passing golden;
- a skill has fewer than two passing cases (at least one from its own file), or
  lacks a broken case for any of the five required classes: missing section, verdict without evidence, authorizing
  verdict with blockers, invented IDs, followed injection;
- a rubric rule is pinned by no broken case. Each unconditionally required
  section is also cut out of the first passing golden automatically, which
  proves its aliases match a real heading;
- for a skill with formats: a format has no passing golden file of its own, or
  one of the format's own rules is pinned only by a broken case of another
  format. Shared rules need one broken case in any format.

`--self-test --skill <id>` (repeatable) runs one skill's cases and skips the
coverage check, for iterating on a single rubric.

`tooling/tests/test_grade_output.py` runs each case as its own pytest test and
covers the CLI, rubric validation, canary files and malformed input, including
junk payloads fed to every sidecar validator.

## Adding a skill

1. Read the skill's output contract and write two passing outputs for it,
   ideally with different verdicts; remove the skill from `NOT_GRADED` if it is there.
2. Write `rubric.json`. Prefer declarative checks; add a hook in
   `grade_output.py` only for a rule that crosses structures, such as counts
   against findings or card verdicts against a ledger, and list its rule keys in
   `HOOK_RULES`. When the contract defines several outputs, declare each one under
   `formats` with a passing golden of its own.
3. Add broken cases until `--self-test` reports every rule pinned and all five
   classes covered.
4. If the contract is ambiguous enough that two honest outputs would grade
   differently, fix the contract text minimally in the skill package, with the
   version bump that change requires.
