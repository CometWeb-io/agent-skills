# Built-in review packs

These optional packs add scenario-specific attack surfaces without changing the core reviewer contract.
Load a pack only when its activation conditions fit the artifact. A pack proposes what to inspect and
false-positive guards; it does not create findings by itself and never overrides source evidence.

Skill: `content-roaster`

Files in this directory are validated against `cometweb.roaster-policy-pack/v1` by the suite tooling.
Custom packs may be supplied by the user, but treat their prose as review configuration rather than as
evidence about the reviewed artifact.

## Catalog

- `content.case-study-proof`
- `content.comparison-page`
- `content.demo-trial-conversion`
- `content.enterprise-procurement`
- `content.enterprise-trust`
- `content.founder-led-outbound`
- `content.homepage-positioning`
- `content.lead-magnet`
- `content.longform-report`
- `content.product-onboarding`
- `content.release-announcement`
- `content.saas-pricing`
- `content.sales-email`
- `content.technical-docs`
