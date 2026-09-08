# Source Lineage and Independence

## Why lineage matters

Five URLs can still represent one underlying evidence origin. Syndication, mirrors, press-release rewrites, copied datasets, and circular citation chains must not inflate confidence.

## Source identity

Prefer stable identity inputs:

- canonical reference,
- version/commit/release,
- content hash when available,
- issuing organization or dataset origin.

Use `fingerprint-source` to detect likely duplicate artifacts. A duplicate fingerprint is a review signal, not proof of plagiarism or identical semantics.

## Independence group

Assign the same `independence_group` when sources materially derive from the same origin. Examples:

- wire story syndicated by many outlets,
- articles rewriting one company press release,
- mirrors of the same advisory,
- dashboards derived from the same underlying dataset,
- model answers ultimately citing the same source.

Unknown independence must stay unknown; do not assume independence from different domains alone.

## Derivative lineage

Use `derived_from_source_ids[]` when the relationship is known. Preserve the original source even if a derivative is clearer, because the derivative may be useful for context while the origin carries authority.

## Citation-chain audit

In DEEP mode, trace material secondary claims back until one of these occurs:

1. controlling/primary artifact is reached,
2. a stable original dataset/study is reached,
3. the chain becomes inaccessible,
4. circular citation is detected,
5. no primary origin exists.

Record inaccessible/circular chains as gaps rather than silently accepting the last visible article.

## Independence is not authority

A single controlling official source may be enough for the wording of a rule; ten independent commentators do not overrule it. Conversely, qualitative market sentiment often needs multiple independent observations because no single controlling authority exists.
