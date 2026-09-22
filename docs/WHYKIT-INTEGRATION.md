# Exporting CW-AIP v2 handoffs to WhyKit

`tooling/whykit_draft.py` turns a finalized CW-AIP v2 `EvidenceEnvelope` or
`DecisionEnvelope` into a human-readable WhyKit Markdown draft. The adapter lives
in this producer repository; WhyKit does not depend on CometWeb's protocol.

The command is intentionally narrow:

- it validates the full envelope, typed payload, and canonical payload hash;
- it rejects duplicate JSON keys and non-JSON constants such as `NaN`;
- it rejects `payload_hash: pending` and unsupported envelope types;
- it always emits `status: draft` and `human_reviewed: false`;
- it never allocates WhyKit evidence or decision IDs;
- it writes to stdout unless `--output` is given;
- it refuses to overwrite an existing output file;
- it never updates a vault index, evidence register, or decision log.

Producer-controlled prose is escaped and rendered as quoted data. A heading,
HTML fragment, list, link, or code fence inside an envelope cannot become
adapter-authored Markdown structure.

## Evidence draft

```bash
python3 tooling/whykit_draft.py evidence-envelope.json \
  --owner "Research lead" \
  --output reports/release-readiness-2026-09-19.md
```

WhyKit requires report filenames to end in `YYYY-MM-DD`. The converter does not
rename an explicitly supplied path. Use `--source-id E-NNN` only after the
corresponding source has a populated row in the target vault's evidence
register:

```bash
python3 tooling/whykit_draft.py evidence-envelope.json \
  --owner "Research lead" \
  --source-id E-018 \
  --output reports/release-readiness-2026-09-19.md
```

CW-AIP source IDs such as `S-1` and evidence-pack IDs are preserved in the body
and provenance. They are not silently relabelled as WhyKit `E-NNN` IDs.

## Decision draft

A decision record needs identifiers that belong to the target vault, so they
must be supplied explicitly:

```bash
python3 tooling/whykit_draft.py decision-envelope.json \
  --owner "Product lead" \
  --decision-id D-041 \
  --review-by 2027-03-19 \
  --source-id E-018 \
  --payload-ref "file:///reviewed/decision-envelope.json" \
  --output 06-decisions/d-041-release-candidate.md
```

The output remains a proposal regardless of the producer's `GO`, `NO_GO`,
`TEST`, or `DEFER` verdict. A person must review the prose, confirm the evidence
mapping, add the record to the decision log, and approve it through the normal
WhyKit workflow.

Decision `profile` and `human_approval` values are retained in `provenance`.
Use `--payload-ref` when the producer keeps a durable machine-readable record;
the Markdown intentionally does not mirror every producer-specific field.

## Safe review sequence

1. Generate to stdout or an explicit draft path.
2. Inspect the Markdown and provenance block.
3. Populate and verify every referenced `E-NNN` row.
4. Link the note from the appropriate map or log.
5. Run `whykit lint --strict` in the target vault.
6. Set `human_reviewed: true` and advance the status only after human review.

The converter has no runtime dependency beyond Python's standard library and
does not add another GitHub Actions workflow.
