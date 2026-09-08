# Responsive and viewports

Defaults: `1280x800` and `390x844`. Add a tablet width when the user/surface
makes it relevant. Do not claim "all devices" from two emulated widths.

## 1. Inspect at relevant viewports

- page-level horizontal overflow that hides the primary job
- primary action reachability and sticky-layer collisions
- text/numbers/signs/IDs do not clip into a different meaning
- tables have an intentional narrow-screen strategy
- touch interaction does not depend exclusively on hover
- images/video preserve meaningful content and aspect
- fixed/sticky elements do not hide fields/CTAs when keyboard/viewport changes

## 2. Local scrolling can be valid

Wide tables, code, timelines, and carousels may scroll in their own region.
File a defect when the behavior prevents/obscures the job, not merely because
`scrollWidth > clientWidth` exists somewhere.

## 3. Pointer vs touch

If the browser supports touch emulation, actually test tap/no-hover behavior.
If not, do not promote an imagined hover trap to a confirmed finding.

## 4. Target size

Use measured applicable accessibility criteria when claiming a standards-based
defect. Otherwise treat target-size recommendations as heuristics and severity
by demonstrated difficulty/error risk.

## 5. Density and product context

A dense desktop-admin table on 390 is not automatically major. Severity depends
on whether mobile/touch use is part of the expected user job and whether the
primary task remains operable. If mobile applicability is unknown, mark the
assumption or recommendation rather than inventing a major defect.
