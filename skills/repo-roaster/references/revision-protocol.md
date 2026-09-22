# Revision and re-review protocol

Use this protocol for `DELTA`, `REVISION`, or `RECHECK` modes.

## 1. Pin both evidence states

Record base and head artifact/ref identifiers in `comparison`. Populate `source_manifest` for both sides where available. If a source is moving or unhashed, state that limitation.

## 2. Preserve finding identity

Match prior findings using `finding_key`. If a key changed because the code/content/claim moved or was renamed, list the prior key in `finding_aliases`. Never create a new key solely to make an unresolved issue look new.

## 3. Re-run the old test before judging the new text/code

For every prior finding:

1. recover the original observation and verification contract;
2. inspect the exact changed surface;
3. rerun the original success condition where possible;
4. rerun the Defender pass for new counterevidence;
5. classify the finding.

Every resolution-ledger row must also record `verification_status` (`PASSED`, `PARTIAL`, `FAILED`, or `NOT_RUN`) and `change_basis` (`ARTIFACT_CHANGED`, `SCOPE_CHANGED`, `JUDGMENT_CORRECTED`, `MIXED`, or `UNKNOWN`). `RESOLVED` requires `verification_status=PASSED`; `NOT_ASSESSABLE` requires `NOT_RUN`.

Statuses:

- `RESOLVED` — original failure mode no longer reproduces and the success condition is met;
- `PARTIAL` — some symptoms changed but the underlying failure remains or verification is incomplete;
- `OPEN` — failure remains materially unchanged;
- `REGRESSED` — the issue became worse or reappeared after an apparent fix;
- `NOT_ASSESSABLE` — evidence needed to resolve the prior finding is unavailable.

## 4. Distinguish evidence drift from reviewer drift

A changed conclusion may come from changed artifact evidence, a larger reviewed scope, or a corrected prior judgment. Record which changed. Do not pretend the artifact improved when only the reviewer learned more.

## 5. Scan the repair surface for regressions

After resolving old findings, inspect changed areas for new failures introduced by the repair. Link new findings to the changed surface rather than assuming causality without evidence.

## 6. Preserve scope limits

A re-review of a patch is not a complete re-review of the whole artifact. State unchanged areas that were not re-inspected.

## 7. Resolution is evidence, not prose

A rebuttal, comment, changelog entry, or "fixed" label is not closure. Closure requires evidence satisfying the original verification contract or a justified replacement contract.
