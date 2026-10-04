# Output contract

A result is an evidence-backed baseline object. `scripts/output_contract.py`
enforces it and `evals/cases.json` pins each rule.

| Field | Type | Meaning |
| --- | --- | --- |
| `summary` | non-empty string | What was done, in one or two sentences |
| `status` | `complete`, `partial` or `blocked` | How far the work got |

The result also requires `profile` and `competitive_intelligence_handoff`.
The profile requires `subject`, `as_of`, `scope`, non-empty `sources` and
`claims`, exact sections `company`, `icp`, `positioning`, `product`, `pricing`,
`proof`, and `discovery`, plus `contradictions` and `gaps`.
| `not_verified` | list of strings | What was not checked; empty only when nothing was left |

A `complete` result with a non-empty `not_verified` is contradictory and is
rejected.

The output does **not** assert anything beyond what was checked. A consumer that
mistakes a heuristic for a verdict is the failure mode worth preventing here.

Source and claim rows use `id`; source rows also use `kind`, `locator`, and
`observed_at`, while claim rows use `text`, `state`, and `source_ids`. The
handoff uses
`baseline_id` and `source_profile_status`, whose values are `BOOTSTRAP`,
`PARTIAL`, or `READY`; it never invents a prior delta.
