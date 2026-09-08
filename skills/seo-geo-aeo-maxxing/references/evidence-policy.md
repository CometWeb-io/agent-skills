# Evidence and confidence policy

Use evidence before inference. Separate platform rules from target-site state.

## Evidence classes

| Class | Meaning | Typical evidence | Max action confidence |
|---|---|---|---:|
| `E1_FIRST_PARTY_LIVE` | Current platform rule/product documentation | Search Central, OpenAI Help, BWT product docs | 5/5 |
| `E2_SITE_DIRECT` | Direct artifact from the audited property | HTML, robots, headers, sitemap, rendered DOM | 5/5 |
| `E3_REPRODUCIBLE_TEST` | Repeatable target-specific test | browser fetch, URL test, rich-result test | 4/5 |
| `E4_CONNECTED_DATA` | Connected target/property data | GSC, BWT, GA4, RUM, crawl/log dataset | 4/5 |
| `E5_SECONDARY_RESEARCH` | Credible industry/research evidence | benchmark/correlation study | 3/5 |
| `E6_HEURISTIC` | Practitioner heuristic | emerging formatting/content tactic | 2/5 |
| `E7_EXPERIMENTAL` | Speculative or unverified tactic | unsupported special file/behavior | 1/5 |

`E1_FIRST_PARTY_LIVE` defines a platform control or documented behavior; it does not prove the
audited property is configured correctly. A scored target-site verdict therefore also needs at least
one target-specific `E2`, `E3`, or `E4` artifact. The scoring script enforces this.

## Evidence object contract

For `PASS`, `WEAK`, and `FAIL`, use a non-empty list:

```json
"evidence": [
  {
    "class": "E2_SITE_DIRECT",
    "artifact": "robots.txt contains User-agent: OAI-SearchBot with no matching Disallow for /docs/",
    "source": "https://example.com/robots.txt"
  }
]
```

`artifact` must name what was actually observed. A generic sentence such as `SEO looks good` is not
evidence. `source` is optional when the artifact is a connected dataset or local crawl record.

## Claim labels

Use as needed:

- `CONFIRMED`: current first-party platform documentation/product data;
- `OBSERVED`: target-specific direct or connected evidence;
- `INFERRED`: plausible explanation not directly proven;
- `EXPERIMENTAL`: emerging relationship/tactic not established as a requirement;
- `UNVERIFIED`: current first-party evidence could not be refreshed.

## Verdict discipline

- `FAIL`: requirement/quality condition clearly not met.
- `WEAK`: partial, inconsistent, or materially compromised.
- `PASS`: condition clearly satisfied for the stated scope.
- `NOT_ASSESSED`: evidence needed to decide is unavailable.
- `N/A`: the check genuinely does not apply.

Do not use `FAIL` because a page fails a preferred template. Do not use `PASS` from generic platform
documentation without target evidence.

## N/A anti-gaming rule

Checks marked `never` in the registry cannot be `N/A`. Surface checks may be `N/A` only when that
surface is explicitly out of scope. Conditional checks require both a reason and target-specific
`applicability_evidence` showing why the condition does not apply. If applicability is uncertain,
use `NOT_ASSESSED`.

## Distribution evidence

For sampled template checks, `distribution` may encode observed pass/weak/fail counts. The score is
then derived from the distribution rather than a coarse single verdict. Preserve sample size and do
not extrapolate beyond the sampled/template evidence.

## Sitewide-claim rule

A page sample can support a page-level finding or a template hypothesis. Use sitewide language only
when direct template logic, crawl-wide data, connected index data, or equivalent evidence supports
it. State sample size whenever it matters.

## Correlation policy

Secondary studies can motivate experiments; they cannot become hard gates unless the platform also
publishes the relevant requirement. Write `correlates with` or `test`, not `causes citations`.

## Evidence quality grade

The scoring engine reports evidence quality/grade to describe how strong the audit's evidence base
is. It is not a probability of ranking, citation, or future performance.
