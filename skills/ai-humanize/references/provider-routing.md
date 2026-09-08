# Provider routing for provenance-aware text work

Status snapshot: **2026-08-25**. Read `provenance-research.md` first.

## Architectural rule

A writing skill can control planning, editing, and the text it asks a model to produce. It cannot disable a watermark applied inside a provider's sampler or serving stack.

Therefore treat a rewrite generated on a provider surface as **new generation**. Even if the original provider's token sequence is fully replaced, the rewrite surface may add its own provenance signal.

## Routing by objective

### Ordinary editorial rewrite

Choose the model/runtime that gives the best semantic fidelity and writing quality. Do not route merely to chase an unverified detector score.

### Provenance-sensitive rewrite

Use deep mode and preserve invariants. If current provider status matters, verify it live. Report only what is known about the specific surface rather than generalizing from a provider brand.

### Controlled watermark experiment

Use an inference environment whose generation configuration is known and auditable. Record:

- source provider/product surface;
- source model/version when known;
- rewrite provider/product surface;
- rewrite model/version;
- whether watermark/logits processors are controlled and audited;
- rewrite mode;
- detector name/version/key identity when applicable;
- detector result;
- semantic-fidelity review.

A controlled environment does not prove that the output is universally unwatermarked. It only removes one experimental unknown.

## Reporting vocabulary

Detector result:

- `detected`
- `not_detected`
- `abstain`
- `unavailable`

Provider deployment status:

- `confirmed`
- `confirmed_or_rollout`
- `not_documented_as_watermarked`
- `not_publicly_verified`
- `unknown_surface`
- `controlled_only_if_audited`

Avoid `clean`, `undetectable`, `human-written`, and `watermark_removed` unless a specific tool and evidence justify a narrower technical statement.
