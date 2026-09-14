# Local workflow: plan -> validated brief -> snapshot

All paths below are relative to the skill directory. Runtime uses only the Python
standard library; it does not require the monorepo tooling directory or an API key.
Read and redact input before use: reports contain the supplied evidence summaries.
Do not paste secrets or unnecessary personal information into those summaries.

## Inspect without writing

```bash
python3 scripts/operator_kernel.py plan --input-json examples/plan.synthetic.json
python3 scripts/prepare_brief.py --input examples/plan.synthetic.json --language pl
python3 scripts/self_check.py
```

The shipped example is deliberately synthetic. Replace it with a sourced plan input:
`target`, `goal`, `horizon`, timezone-aware `as_of`, `coverage`, `state_items`, and
`candidates`. Candidates contain action/why_now/done_when/confidence/evidence,
action_type, scoring dimensions and depends_on. Unknown coverage stays unavailable.
Explicit critical_gap_open and material_current_evidence_block are binding signals.
Do not use a fabricated high evidence_strength to overcome missing source proof.

## Save a new analysis packet

```bash
python3 scripts/prepare_brief.py --input /private/plan-input.json --output /private/new-brief --language pl
```

The parent must exist and the output directory must not. No old file is overwritten.
The command validates first, then saves brief.md, operator-plan.json,
operator-report.json, operator-snapshot.json, validation.json and BRIEF-MANIFEST.json.
Every candidate survives in the machine report even if it is not shortlisted. NEXT
cannot precede its prerequisites. STOP and readiness-held work are not executed.

A non-ready but structurally valid brief is useful: it states why implementation
must wait and which independent checks may proceed. Exit 0 means artifact generation,
not authorization, READY, validated application behavior, or successful installation.
Exit 2 means invalid input/baseline/output; no completed artifact is claimed.

## Repeat

```bash
python3 scripts/prepare_brief.py --input /private/new-input.json --previous /private/old-brief/operator-snapshot.json --output /private/newer-brief
```

This adds delta.json. It does not invent a baseline for a new project. A malformed
snapshot fails. Changed scope and unverified removed blockers remain explicit.
The input hash and artifact hashes track content consistency, not source authorship.
The brief renderer escapes supplied HTML/Markdown; raw values are retained in JSON.

## Capability limits

self_check validates only bundled resources and selected deterministic scenarios.
pytest runs the larger developer suite. Neither runs a model or queries GitHub,
Notion, a browser or a production application. A tool-free host must perform a
bounded manual analysis and report the unavailable checks instead of inventing them.
