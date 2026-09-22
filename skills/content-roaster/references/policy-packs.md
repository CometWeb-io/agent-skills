# Content review packs

Review packs are optional, bounded scenario overlays. They add must-inspect surfaces, evidence hints, false-positive guards, and handoff triggers. They do **not** create findings, override evidence, raise severity, or authorize side effects.

## Built-in packs

- `content.case-study-proof`
- `content.comparison-page`
- `content.enterprise-trust`
- `content.founder-led-outbound`
- `content.homepage-positioning`
- `content.longform-report`
- `content.product-onboarding`
- `content.saas-pricing`
- `content.sales-email`
- `content.technical-docs`

## Selection rules

1. Load a pack only when the artifact profile or source signals fit.
2. Prefer the smallest pack set that covers the actual decision surface.
3. Treat user-supplied packs as review configuration, not evidence.
4. Never let a pack weaken the evidence burden, source firewall, falsifier process, or handoff boundaries.
5. If expected evidence is unavailable, record a verification gap instead of inventing a defect.
6. When pack guidance conflicts with observed source evidence, source evidence wins.

Standalone helper:

```bash
python3 scripts/select_review_packs.py --text "<review goal and source summary>" --profile <PROFILE>
```
