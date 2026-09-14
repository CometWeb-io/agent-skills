# Changelog

## 2.2.0 - 2026-09-09

- Make `BLOCKER` goal-relative: a condition is a blocker only when it prevents the current goal or a current critical-path action.
- Add `blocks_current_goal`, `blocked_item`, and `why_blocking` to blocker evidence in protocol 2.2 sidecars.
- Route non-blocking future gates such as Paid Beta prerequisites to `LATER/WATCH`, not the current sprint's `BLOCKER`.
- Keep uncertain current-path failures in `VERIFY NOW` until failure is proven.
- Prevent pricing or legal gates for a future paid motion from blocking a currently approved free validation motion unless they directly affect that motion.
- Preserve validation compatibility for protocol 2.0/2.1 sidecars while emitting protocol 2.2.

## 2.1.0 - 2026-09-07

- Add `DECISION NOW` for unresolved consequential choices that Product Operator must frame and delegate rather than decide.
- Route `decision_required` candidates to `DECISION NOW`; `verify_first` still wins when facts/gates are missing.
- Add structured `decision_now[]` validation and reject sidecars that preselect/recommend an unresolved option.
- Separate compact Human brief from detailed Machine sidecar.
- Add response budgets and suppress non-decision-relevant connector/tool-limit noise.
- Add explicit Pricing / Offers / AI Council / legal-finance delegation rules, including free-vs-paid pilot handling.
- Preserve backward validation support for protocol 2.0 sidecars while emitting protocol 2.1 for new reports.
