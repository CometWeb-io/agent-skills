# UI / UX

Audit the interface as a tool for a user job, not as a design-fashion review.
Separate defects/usability risks from recommendations.

## 1. First-glance orientation

Ask whether a new user can determine, when the screen's job requires it:

1. where they are
2. what the main object/job is
3. what action or next step matters
4. current material status
5. whether the state is loading, empty, failed, or complete

Failure is not automatically `major`. Demonstrate the resulting user friction,
wrong action, inability to find the path, or misleading state.

## 2. Hierarchy and scan path

- titles/headings match the actual job and object
- primary/secondary/destructive actions are distinguishable when competing
- important table fields remain discoverable/readable
- overlap/cutoff/truncation does not change material meaning
- density supports the task rather than hiding the key value/action

Spacing preference, card-vs-list taste, and "modernity" are recommendations
unless they cause a concrete usability problem.

## 3. Affordance and semantics

- interactive controls look/behave operably
- non-interactive surfaces do not misleadingly mimic controls
- links navigate; buttons act; semantic mismatch matters when it breaks browser
  behavior, keyboard use, or user expectation
- current nav/tab state is clear when navigation depends on it

A tooltip is not a substitute for an accessible name. A visible text label is
not mandatory for every icon if purpose remains clear and accessible.

## 4. Copy and labels

- labels describe the actual outcome
- error copy supports recovery
- the same state/entity uses consistent terminology
- truncation/localization does not change amounts, signs, IDs, or meaning
- mixed language is a defect only when it is inconsistent with product intent or
  materially harms comprehension; otherwise recommendation/nit

## 5. Feedback and persistence

- action receives prompt acknowledgement appropriate to latency
- long work exposes progress/state rather than appearing frozen
- durable result, not a transient toast, is the source of truth
- failures preserve user work when possible and explain recovery
- undo, if offered, must restore the relevant state

Exact latency thresholds are heuristics unless measured against a requirement.
Do not file "no skeleton after 1.0s" as an automatic defect.

## 6. Navigation and recovery

- back/return paths preserve material state when users reasonably rely on it, or
  resets are explicit and acceptable
- deep links work when the product exposes/shareability semantics require them
- modals/overlays do not create surprising history behavior
- missing/error routes provide a usable way out

URL persistence for filters/tabs is a platform/product choice unless the state is
intended to be shareable/restorable. Use `heuristic` when no stronger basis
exists.

## 7. Real visual defects

Examples:

- overlap/cutoff that hides content/action
- layout shift causing mis-taps
- page-level overflow hiding the primary job
- broken/stretching media that obscures information
- sticky layers covering terminal controls
- focus indicator absent when keyboard focus cannot otherwise be located

Assign severity from impact, not from category.

## 8. Consistency

Consistency matters when divergence creates uncertainty, errors, or extra work.
One legacy radius is usually recommendation/nit; two incompatible destructive
confirmation patterns in the same flow can be materially worse.
