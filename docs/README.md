# Documentation index

Each topic has one home; other documents link to it instead of repeating it.
Read the sections in order the first time. Files marked *generated* are
written by a tool and fail CI when edited by hand.

## Start

| Document | What it covers |
| --- | --- |
| [`../README.md`](../README.md) | What the skills are, the quickstart and the skill catalog. |
| [`TARGET.md`](TARGET.md) | What this repository is, and what it is not. |
| [`media/README.md`](media/README.md) | The overview diagram used by the README. |
| [`../THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md) | Attribution and provenance for adapted third-party patterns. |

## Using skills per host

| Document | What it covers |
| --- | --- |
| [`../INSTALL.md`](../INSTALL.md) | Installers for Claude Code, Cursor, Codex, Qwen Code, Qoder and Lingma; plugin marketplaces; dry run, upgrade and uninstall. |
| [`OPENAI-MARKETPLACE.md`](OPENAI-MARKETPLACE.md) | Importing the repository as a ChatGPT or Codex workspace marketplace. |
| [`ROUTING.md`](ROUTING.md) | How a prompt is matched to a skill, the routing policy blocks, known gaps and how to add a case. |
| [`generated-compatibility-matrix.md`](generated-compatibility-matrix.md) | *Generated.* Declared support per skill and host. |
| [`../extras/AGENTS.snippet.md`](../extras/AGENTS.snippet.md) | *Generated.* The routing block to paste into a project's `AGENTS.md` or `CLAUDE.md`. |

## Writing a skill

| Document | What it covers |
| --- | --- |
| [`../CONTRIBUTING.md`](../CONTRIBUTING.md) | The check flow, adding a skill step by step, the quality bar, and which files are generated. |
| [`TOOLING.md`](TOOLING.md) | Every script under `tooling/`: what it does, which gate runs it, what it reads and writes. |
| [`QUALITY-SUITE-INTEGRATION.md`](QUALITY-SUITE-INTEGRATION.md) | How imported skill bundles join the one skill tree and registry. |
| [`VOCABULARY.md`](VOCABULARY.md) | Verdicts, severities, confidence, freshness, gate and run statuses and envelope kinds across every skill, and why they differ. |
| [`../AGENTS.md`](../AGENTS.md) | Standing repository rules for coding agents (in Polish). |
| [`../CODE_OF_CONDUCT.md`](../CODE_OF_CONDUCT.md) | How contributors are expected to behave. |

## Evaluating

| Document | What it covers |
| --- | --- |
| [`SKILL-QUALITY-OPERATIONS.md`](SKILL-QUALITY-OPERATIONS.md) | What CI proves, and how repository evidence is kept apart from runtime claims. |
| [`../evals/routing/README.md`](../evals/routing/README.md) | Routing case files, coverage floors, negation and sequence rules, holdout tuning. |
| [`CONTRACT-TRACE-AND-SKILL-EVALS.md`](CONTRACT-TRACE-AND-SKILL-EVALS.md) | Contract tracing and reviewed skill comparisons with a model. |
| [`OUTPUT-GRADING.md`](OUTPUT-GRADING.md) | Grading a skill's actual output against its output contract, offline, with golden good and broken cases. |
| [`REAL-HOST-EVALS.md`](REAL-HOST-EVALS.md) | Running the skills in a real host CLI under budget caps, grading the transcripts, and comparing with and without the plugin. |
| [`LOCAL-VALIDATION.md`](LOCAL-VALIDATION.md) | A recorded run of every gate without GitHub Actions (in Polish). |
| [`generated-eval-strength.md`](generated-eval-strength.md) | *Generated* by `tooling/eval_strength.py`. How many guards each harness pins. |
| [`generated-context-budget.md`](generated-context-budget.md) | *Generated* by `tooling/context_budget.py`. What each skill costs a host in context. |
| [`generated-skills-table.md`](generated-skills-table.md) | *Generated.* Version, tier and lifecycle per skill. |

## Protocol (CW-AIP)

| Document | What it covers |
| --- | --- |
| [`../protocol/cw-aip-v2/README.md`](../protocol/cw-aip-v2/README.md) | The current envelope format for handoffs between skills. |
| [`../protocol/cw-aip-v1/cw-interchange-v1.md`](../protocol/cw-aip-v1/cw-interchange-v1.md) | v1, still valid for skills that have not migrated; its schemas sit beside it. |
| [`WHYKIT-INTEGRATION.md`](WHYKIT-INTEGRATION.md) | Turning final evidence and decision envelopes into unreviewed WhyKit drafts. |

## Security

| Document | What it covers |
| --- | --- |
| [`../SECURITY.md`](../SECURITY.md) | Reporting a vulnerability, and what the leak gate does and does not promise. |
| [`SIGNED-COMMITS.md`](SIGNED-COMMITS.md) | Enabling commit signing before the ruleset requires it. |

## Releasing

| Document | What it covers |
| --- | --- |
| [`../CONTRIBUTING.md#plugin-version`](../CONTRIBUTING.md#plugin-version) | When the plugin version must change, and how the shipped set is recorded. |
| [`../CONTRIBUTING.md#releases`](../CONTRIBUTING.md#releases) | Cutting a release: the tag, the local packaging rehearsal, the SBOM and verifying attestations. |
| [`../CHANGELOG.md`](../CHANGELOG.md) | What changed in each plugin release. |
| [`acceptance/longform-publisher-1.0.0.md`](acceptance/longform-publisher-1.0.0.md) | A recorded real-world acceptance of one skill release. |

## Publication standards

In Polish; they record decisions made on 2026-09-12 and bind the
`ebook-publisher` and `longform-publisher` skills.

| Document | What it covers |
| --- | --- |
| [`EDITORIAL_VISUAL_STANDARD.md`](EDITORIAL_VISUAL_STANDARD.md) | Brand marks, typography, colour tokens, status labels. |
| [`COMETWEB-EBOOK-DESIGN-RULES.md`](COMETWEB-EBOOK-DESIGN-RULES.md) | Layout rules for covers, before/after views and status pills. |
| [`../profiles/cometweb/PROFILE.md`](../profiles/cometweb/PROFILE.md) | The project overlay that applies these standards to CometWeb publications. |

## Other generated files

Written by `tooling/generate_adapters.py` from `registry/skills.json`; change the
registry and regenerate with `uv run python tooling/check_all.py --fix --fast`.

- `generated-cursor-routing.mdc`, the Cursor routing rule, and its compact
  fallback [`../extras/cursor-routing.mdc`](../extras/cursor-routing.mdc)
- each skill's `agents/openai.yaml` interface block
- the routing rule the Cursor plugin ships,
  [`../rules/cometweb-agent-skills.mdc`](../rules/cometweb-agent-skills.mdc)
- the skill list in the `description` of `.claude-plugin/plugin.json`, and
  `.cursor-plugin/plugin.json` as that manifest restricted to the keys Cursor
  documents (`cursor.plugin_format` in `registry/hosts.json`)
- the [skill catalog](../README.md#skill-catalog) and every skill count in
  `README.md`
