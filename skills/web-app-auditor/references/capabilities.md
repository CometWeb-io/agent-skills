# Capability profiles

Do not pretend the host has tools it does not expose. Capability determines the
proof bar, not the ambition of the prose.

## Profiles

| Profile | Available | Strongest valid claims |
|---|---|---|
| `hybrid` | interactive browser + source | observed interaction + source-assisted root cause |
| `browser` | interactive browser | observed interaction, state, visual/data claims |
| `screenshot` | one or more rendered images | static visual/text/data claims visible in images |
| `source` | source/repo, no browser | deterministic static facts; interaction effects are inferred |
| `fetch-only` | HTML/text/HTTP fetch, no rendered browser | markup/text/response facts only |

A host may also expose optional diagnostics: screenshots, console, network,
DOM inspection, filesystem, code execution. Record only those actually present.

## Confidence mapping

- `high` — directly observed/measured in the relevant execution surface.
- `medium` — deterministic static/source evidence supports the claim, but the
  user-facing interaction was not executed.
- `low` — hypothesis or incomplete reproduction; use `needs-repro`.

A source-only proof of a hardcoded wrong displayed price can be `medium` if the
render path is deterministic. A source-only claim that a modal "will not open"
is normally `needs-repro` unless the code makes the failure mechanically certain.

## Capability gates

### No interactive browser

Do not say `clicked`, `tested keyboard`, `submitted`, `navigated`, `network
failed`, or `persisted` unless another tool directly proves it. Interaction-heavy
`page`, `area`, `crawl`, and `flow` audits at `standard`/`forensic` depth must
end `incomplete` unless the user explicitly requested a static-only audit.

### Screenshot-only

You may confirm visible overlap, hierarchy, clipping, inconsistent labels,
visible arithmetic, and other image-grounded facts. You cannot confirm hidden
states, focus order, hover, keyboard, submit, persistence, route behavior, or
network side effects.

### Source-only

Use source to locate likely surfaces and deterministic contradictions. Label
user-facing consequences as inferred. Do not convert lint/code-style findings
into product defects.

### No console/network

Do not infer request status from a toast or spinner. Report only the durable UI
state you can observe.

### No code execution/filesystem

Do not claim `scripts/validate_report.py` ran. Perform a manual consistency
check and state `validator: not run — capability unavailable`.

## Capability upgrade

If a stronger tool becomes available during the task, upgrade the profile and
reproduce the highest-impact `needs-repro` items first. Do not silently rewrite
old inferred evidence as observed evidence.
