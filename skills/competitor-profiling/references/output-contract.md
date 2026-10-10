# Output contract

A source-backed initial baseline, not a finding of factual truth. The validator
checks structure, temporal consistency and readiness; it does not fetch sources.

Required root fields: `summary` (non-empty text), `status` (`complete`, `partial`,
`blocked`), `not_verified` (list of non-empty strings), `profile`, and
`competitive_intelligence_handoff`.

`profile` requires `subject`, `scope`, `as_of`, non-empty `sources` and `claims`,
`sections`, `contradictions` and `gaps`. ISO dates mean UTC midnight; timestamps
must include a timezone. Every `observed_at` must be at or before `as_of`.

Sources have unique `id`, non-empty `kind`, `locator`, and `observed_at`.
Claims have unique `id`, non-empty `text`, `state` (`OBSERVED`, `INFERRED`,
`HYPOTHESIS`, `UNKNOWN`), and non-empty `source_ids` referencing existing sources.

`sections` has exactly `company`, `icp`, `positioning`, `product`, `pricing`,
`proof`, and `discovery`. Each is an object with non-empty `summary` and
non-empty `claim_ids` referencing profile claims. A section name or "covered"
label alone cannot establish coverage. A partial dossier can record unknowns
with a supporting source locator and describe its gaps without inventing facts.

Complete profiles also require non-empty `section_support` in every section.
Each entry has `claim_id` from that section's `claim_ids`, `source_id` from that
claim's `source_ids`, and a non-empty `rationale` explaining how that source
supports the section. A claim can support multiple sections with explicit
bindings. Supplied support is a structural mapping, never proof of source truth.
`assess` reports `coverage_status: SUPPORT_MAPPED|NOT_ASSESSED` and always
`factual_verification: not_assessed`; it does not fetch or independently review sources.

`complete` requires empty `not_verified`, `contradictions`, and `gaps`, and no
`UNKNOWN` or `HYPOTHESIS` claims. It describes completion of the declared scope,
not independent factual verification or authority for a side effect.

The handoff contains non-empty `baseline_id` and `source_profile_status`
(`BOOTSTRAP`, `PARTIAL`, `READY`). `READY` requires a valid complete profile and
`profile_sha256` equal to `scripts/output_contract.py:profile_hash(profile)`:
SHA-256 of canonical UTF-8 JSON (sorted keys, compact separators, no NaN), with
`sha256:` prefix. The digest binds the snapshot, not the truth of its contents.
A first baseline never invents a prior delta; consumers must validate their
own monitoring snapshot before acceptance.
