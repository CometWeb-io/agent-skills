# Audit modes and depth

Mode defines *what* is audited. Depth defines *how exhaustively*.

## Depth contract

| Depth | Coverage bar | Sampling |
|---|---|---|
| `recon` | inventory + primary safe interactions + obvious high-impact contradictions | allowed; state what was skipped |
| `standard` | all primary actions, all unique interaction/state patterns, all high-risk claims, every form/state class, representative repeated instances | allowed only for repeated low-risk instances; record the rule |
| `forensic` | exhaust all in-scope activatable instances and material claims until IN is exhausted or policy/environment blocks them | no sampling |

Default: `standard`.

Use `forensic` for explicit requests such as "every button", "dokladnie",
"dogłębnie", "forensic", "exhaustive". Do not silently turn `standard` into
forensic because the interface is small.

### Standard sampling rule

Test 100% of:

- primary/terminal actions that are policy-safe
- unique control types/behavior variants
- destructive/high-risk controls up to the safe pre-commit boundary
- forms and validation classes
- high-risk claims: money, identity, permission, quota, terminal status
- screens/templates explicitly named by the user

For repeated homogeneous rows/cards/controls, test a representative set that
covers state variants (e.g. active/inactive, paid/unpaid, long/short content),
not every identical instance. Record the sample and why it is representative.

## `page`

One route/screen plus its owned modals/drawers/popovers. Do not follow global
navigation into another feature.

- recon: inventory + primary controls
- standard: unique controls/states + representative repeated rows
- forensic: every in-scope control instance, tab, menu, row action, state

## `area`

A bounded feature/job slice such as Billing, Users, Settings.

Map entry points/screens/return paths. Check cross-screen state for repeated
entities. Shared chrome counts only when it belongs to the area.

## `crawl`

Bounded multi-page IA/navigation audit.

- <=15 unique templates: cover each template once + named/key instances
- larger: all primary nav/footer destinations + one representative of each
  template + user-named pages

Forensic crawl may expand beyond this only when the user explicitly requests
exhaustive page-instance coverage and the scope remains finite. If the requested
forensic population is effectively unbounded/huge, do not silently sample and
call it forensic: define a finite boundary when possible, otherwise finish as
`incomplete` with the unexhausted population stated.

## `flow`

A start, steps, and success definition (signup, checkout, invite, export).

Walk happy path and relevant unhappy paths only to the mutation boundary allowed
by `safety-and-mutations.md`. If terminal success cannot be tested safely, mark
it policy-blocked and use `incomplete` when terminal proof is essential.

## `data`

Integrity-first. Build the contradiction matrix and recalculate material
aggregates. UI/UX findings are incidental unless they hide or misrepresent data.
Safe mutation/re-read is optional and governed by environment policy.

## `visual`

UI/UX primary. Verify hierarchy, affordance, legibility, responsive behavior,
copy/labels, state communication. Do not manufacture a full data audit unless a
material contradiction is discovered.

A screenshot-only visual audit can be complete for the static objective if the
user explicitly asked for static visual review; interaction claims remain out.

## `regression`

Requires baseline evidence: previous report, screenshots, or explicit old
behavior. Re-run prior findings as `fixed | still-open | regressed`; then run a
thin standard pass on the same scope for collateral damage.

## `a11y`

Accessibility-first. Test supported keyboard/semantics/contrast/zoom patterns.
Do not claim formal conformance unless the required criteria and tooling were
actually measured.

## Combining intent

"Przeklikaj billing i sprawdz liczby" = `area` mode with data-integrity bar,
not two separate audits. Keep one scope card and one report.
