# Competitive Intelligence Data Model

## Contents

1. Design principles
2. Directory model
3. Configuration schema
4. Snapshot schema
5. Evidence schema
6. Event schema
7. Pattern schema
8. Normalization rules
9. Versioning and migration

## 1. Design principles

Use append-only historical state. A snapshot is immutable after acceptance. `current.json` is a convenience pointer/copy of the latest accepted snapshot, never the only record.

Store observations separately from implications. Store source metadata with every material field or with a field-level evidence reference.

Prefer stable machine keys over prose headings so snapshots remain diffable.

## 2. Directory model

```text
.competitive-intelligence/
├── config.json
├── competitors/
│   └── <competitor-id>/
│       └── current.json
├── snapshots/
│   └── <competitor-id>/
│       └── <ISO8601-safe-timestamp>.json
├── events/
│   └── <YYYY-MM>.jsonl
├── reports/
│   └── <report-name>.md
└── raw/
    └── <competitor-id>/<timestamp>/
```

Raw evidence is optional and should be stored only when tool policy, copyright rules, and project policy allow it. Prefer source references and extracted facts over unnecessary bulk copying.

## 3. Configuration schema

Recommended `config.json`:

```json
{
  "schema_version": "1.0",
  "subject_product": {
    "name": "Our Product",
    "context_path": ".agents/product-marketing.md"
  },
  "competitors": [
    {
      "competitor_id": "acme",
      "name": "Acme",
      "tier": 1,
      "domains": ["acme.example"],
      "repos": [],
      "focus_areas": ["product", "pricing", "positioning"],
      "cadence": "weekly",
      "watch_urls": []
    }
  ],
  "sources": [
    {
      "source_id": "acme-pricing",
      "competitor_id": "acme",
      "kind": "web",
      "location": "https://acme.example/pricing",
      "signal_areas": ["pricing"],
      "critical": true,
      "cadence": "weekly",
      "status": "OK",
      "last_success_at": "2026-08-25T19:20:00Z"
    }
  ],
  "freshness_ttl_days": {
    "pricing": 7,
    "product": 14,
    "positioning": 14,
    "proof": 30,
    "discovery": 30,
    "company": 30,
    "tech_trust": 30
  }
}
```

TTL values are defaults, not universal truth. Tighten them for volatile, decision-critical signals and loosen them for slow-moving fields.

## 4. Snapshot schema

Required top-level keys:

```json
{
  "schema_version": "1.0",
  "competitor_id": "acme",
  "competitor_name": "Acme",
  "captured_at": "2026-08-25T19:30:00Z",
  "state": {},
  "evidence": []
}
```

Recommended `state` shape:

```json
{
  "positioning": {
    "headline": null,
    "value_proposition": null,
    "target_segments": [],
    "primary_use_cases": [],
    "category_language": []
  },
  "product": {
    "capabilities": [],
    "integrations": [],
    "platforms": [],
    "release_signals": []
  },
  "pricing": {
    "currency": null,
    "billing_model": null,
    "value_metric": null,
    "tiers": [],
    "trial": null,
    "free_plan": null
  },
  "proof": {
    "named_customers": [],
    "case_study_themes": [],
    "review_aggregates": []
  },
  "discovery": {
    "content_themes": [],
    "seo_metrics": {},
    "paid_media_signals": []
  },
  "company": {
    "funding": [],
    "leadership_changes": [],
    "hiring_signals": [],
    "geographies": []
  },
  "tech_trust": {
    "public_technologies": [],
    "security_claims": [],
    "compliance_claims": [],
    "status_signals": []
  }
}
```

Do not force unknown fields to empty strings. Use `null` for unknown scalar values and `[]` for known-empty collections only when the source actually supports that conclusion. When unsure whether a collection is exhaustive, store observed items and mark evidence coverage.

## 5. Evidence schema

Each evidence item should look like:

```json
{
  "evidence_id": "ev-20260825-001",
  "field_path": "state.pricing.tiers",
  "source": "https://acme.example/pricing",
  "source_class": "A_FIRST_PARTY",
  "observed_at": "2026-08-25T19:20:00Z",
  "last_verified_at": "2026-08-25T19:20:00Z",
  "direct": true,
  "supports": "Acme lists a Pro tier at 49 USD/month",
  "notes": null
}
```

Do not put long copyrighted source passages in evidence records. Store concise extracted facts and source pointers.

For authorized internal evidence, use a private source identifier/location appropriate to the connector or workspace. Do not copy private raw transcripts into public search queries or public skill artifacts.

Source collection health belongs in configuration/state metadata, not in the competitor's normalized `state`. A failed source must not create a removal delta.

## 6. Event schema

Events are append-only JSONL records:

```json
{
  "event_id": "evt-...",
  "event_key": "sha256:...",
  "competitor_id": "acme",
  "category": "PRICING_PACKAGING",
  "change_type": "MODIFIED",
  "field_path": "state.pricing.tiers",
  "before": {"name": "Pro", "monthly": 39},
  "after": {"name": "Pro", "monthly": 49},
  "factual_change": "Pro monthly list price increased from 39 to 49 USD.",
  "first_observed_at": "2026-08-25T19:20:00Z",
  "last_verified_at": "2026-08-25T19:20:00Z",
  "verification_state": "CONFIRMED",
  "materiality": {
    "score": 82,
    "severity": "CRITICAL"
  },
  "evidence_ids": ["ev-20260825-001"],
  "implication": "May change relative price positioning for the Pro segment.",
  "implication_confidence": 0.76,
  "disposition": "DEEP_DIVE",
  "status": "OPEN"
}
```

`event_key` identifies the same observed transition and is used for deduplication. `event_id` identifies the stored event record.

## 7. Pattern schema

Patterns aggregate accepted events and must not be presented as raw facts:

```json
{
  "pattern_id": "pat-enterprise-upmarket",
  "title": "Enterprise upmarket motion",
  "competitor_ids": ["acme"],
  "event_keys": ["sha256:...", "sha256:..."],
  "hypothesis": "Acme is shifting toward enterprise buyers.",
  "confidence": 0.72,
  "first_observed_at": "2026-07-01T00:00:00Z",
  "last_updated_at": "2026-08-25T00:00:00Z",
  "falsifier": "Enterprise-specific launches stop and SMB packaging becomes the dominant release focus."
}
```

## 8. Normalization rules

Normalize before diffing:

- Use canonical currency codes where known.
- Keep monthly and annual pricing separate; do not compare annual-per-month display price to true monthly billing without labeling it.
- Normalize feature names to stable capability IDs when possible, while retaining the competitor's wording as evidence metadata.
- Represent region/plan limitations explicitly.
- Separate `announced`, `beta/preview`, and `generally_available` states.
- Separate named customers from logo-wall observations if customer status is uncertain.
- Aggregate hiring by function/seniority/region rather than storing unnecessary personal records.
- Preserve exact source timestamps when available.

The kernel ignores obvious volatile metadata paths such as `captured_at`, `observed_at`, and `last_verified_at` by default. Do not rely on the ignore list to fix poor normalization.

## 9. Versioning and migration

Increment `schema_version` only for breaking semantic changes. A migration must never rewrite old snapshot files in place. Create a migrated copy with provenance that points to the original snapshot hash.
