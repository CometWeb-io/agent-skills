# Documentation index

Nine documents live here and almost nothing linked to them. This index says what
each one is for, and which files are written by a tool rather than by a person.

## Repository direction

| Document | What it covers |
| --- | --- |
| [`TARGET.md`](TARGET.md) | What this repository is, and what it is not. Start here. |
| [`SKILL-QUALITY-OPERATIONS.md`](SKILL-QUALITY-OPERATIONS.md) | How deterministic repository evidence is kept separate from runtime claims. |
| [`CONTRACT-TRACE-AND-SKILL-EVALS.md`](CONTRACT-TRACE-AND-SKILL-EVALS.md) | Contract tracing and how reviewed skill comparisons are run. |

## Working locally

| Document | What it covers |
| --- | --- |
| [`LOCAL-VALIDATION.md`](LOCAL-VALIDATION.md) | Running the full gate without GitHub Actions. |
| [`../CONTRIBUTING.md`](../CONTRIBUTING.md) | The commands to run before a pull request, and the quality bar. |
| [`../SECURITY.md`](../SECURITY.md) | Reporting a vulnerability, and what the leak gate does and does not promise. |

## Publication and visual standards

Both are in Polish and record decisions made on 2026-09-12. They bind the
`ebook-publisher` and `longform-publisher` skills.

| Document | What it covers |
| --- | --- |
| [`EDITORIAL_VISUAL_STANDARD.md`](EDITORIAL_VISUAL_STANDARD.md) | Brand marks, typography, colour tokens, status labels. |
| [`COMETWEB-EBOOK-DESIGN-RULES.md`](COMETWEB-EBOOK-DESIGN-RULES.md) | Layout rules for covers, before/after views and status pills. |

## Release records

| Document | What it covers |
| --- | --- |
| [`RELEASE-READINESS-CANDIDATE-1.1.md`](RELEASE-READINESS-CANDIDATE-1.1.md) | Notes for the release-readiness 1.1.0 candidate. |
| [`acceptance/`](acceptance/) | Per-release acceptance records. |

## Generated — do not hand-edit

`tooling/generate_adapters.py` writes these from `registry/skills.json`. Editing
them directly is pointless: `generate_adapters.py --check` fails in CI the moment
they differ from what the registry produces. Change the registry and regenerate.

- [`generated-context-budget.md`](generated-context-budget.md) — written by `tooling/context_budget.py`
- [`generated-eval-strength.md`](generated-eval-strength.md) — written by `tooling/eval_strength.py`
- [`generated-skills-table.md`](generated-skills-table.md)
- [`generated-compatibility-matrix.md`](generated-compatibility-matrix.md)
- `generated-cursor-routing.mdc`
