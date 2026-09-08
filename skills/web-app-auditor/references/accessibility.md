# Accessibility

Measure what the available tools support. Do not claim formal conformance from a
partial keyboard pass or visual guess.

## 1. Keyboard and focus

When an interactive browser is available:

- tab order follows a usable logical order
- focus is visible on operable controls
- no keyboard trap except intentional/modal trapping with a valid escape path
- buttons, links, menus, tabs, dialogs, comboboxes use appropriate keyboard
  behavior for their implemented pattern
- the primary in-scope job is operable without a pointer when that is an
  applicable requirement

Severity follows demonstrated user impact. Inability to complete a primary job
by keyboard can be major/blocker depending on scope and affected users, but do
not auto-promote because of geography or an assumed regulatory context.

## 2. Names, roles, states

- controls have an accessible name appropriate to purpose
- native semantics are preferred; do not demand redundant ARIA
- `aria-expanded`, `aria-selected`, `aria-checked`, `aria-invalid`, `aria-busy`
  agree with actual/visual state when used
- icon-only primary/destructive actions without an accessible name are material
  findings when verified

## 3. Structure

Check heading and landmark structure for comprehension/navigation, not stylistic
purity.

- page has a meaningful top-level heading structure
- heading levels communicate hierarchy; do not file "multiple H1" solely as a
  defect without demonstrated semantic/navigation harm or an applicable rule
- landmarks are useful and distinguish repeated regions
- data tables expose header relationships needed to understand cells

## 4. Contrast, zoom, reflow

- measure contrast when tooling exists; do not invent ratios
- do not rely on color alone for material status/error communication
- zoom/reflow keeps the primary job readable and operable
- horizontal scrolling may be legitimate for genuinely wide data regions; page
  clipping that hides the job is a finding

## 5. Images, media, motion

- informative images have useful alternatives when required
- decorative images are ignored appropriately
- critical text is not available only as inaccessible image text
- motion that can cause material distraction/vestibular issues respects relevant
  reduced-motion expectations where applicable

## 6. Forms

- labels are programmatically associated when needed
- errors are discoverable and associated with the affected field/context
- required state is not communicated only by color
- focus/error recovery supports completion

## 7. Evidence basis

Use `Expected basis: accessibility-standard` only when you can identify and
measure an applicable criterion/pattern. Otherwise use `platform-convention` or
`heuristic` and calibrate severity accordingly.

Do not dump raw automated scanner output as findings. Deduplicate by user impact
and manually verify high-severity items where possible.
