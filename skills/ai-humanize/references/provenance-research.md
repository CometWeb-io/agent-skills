# Provenance-aware text rewriting

Status snapshot: **2026-08-25**.

Provider deployment changes quickly. Treat this file as a dated research note. If a current provider claim affects the user's decision and web access exists, verify the provider's latest first-party documentation before asserting it.

## Canonical status table

| Provider / surface | Snapshot status | What can safely be said |
|---|---|---|
| Anthropic / supported Claude text surfaces | `confirmed_or_rollout` | Anthropic has publicly described model-level statistical text marking based on SynthID-Text principles. Product/model coverage can change, so verify current rollout details before making a surface-specific claim. |
| Google Gemini app / web text | `confirmed` | Google DeepMind states that SynthID Text is used for text generated in the Gemini app/web experience. |
| Gemini API text | `not_documented_as_watermarked` | A Google AI Developers Forum staff response dated 2026-08-05 states that generated API text is not SynthID-watermarked and native text watermarking is not planned at that time. Re-check if this matters. |
| OpenAI ordinary text responses | `not_publicly_verified` | OpenAI Verify currently supports OpenAI provenance checks for images and audio. OpenAI says its goal is to expand provenance signals to text, which is not the same as confirmation that ordinary text responses currently carry a supported public signal. |
| DeepSeek hosted text | `unknown_surface` | Public labeling rules do not by themselves establish a keyed statistical text watermark. |
| Qwen / Alibaba hosted text | `unknown_surface` | Public AIGC detection or media watermark features do not prove a keyed watermark on ordinary text generation. |
| Self-hosted open-weight model | `controlled_only_if_audited` | The operator controls the inference stack, but a watermark logits processor can still be enabled. Audit the actual generation config. |

Do not convert `unknown_surface`, `not_publicly_verified`, or `not_documented_as_watermarked` into a universal claim that no provenance signal exists.

## First-party sources used for this snapshot

- Anthropic Claude marking overview: https://www.anthropic.com/news/claude-text-watermark
- Google DeepMind SynthID overview: https://deepmind.google/models/synthid/
- Google SynthID Text developer documentation: https://ai.google.dev/responsible/docs/safeguards/synthid
- Gemini API staff statement (2026-08-05): https://discuss.ai.google.dev/t/does-gemini-api-text-output-carry-synthid-watermarking-gemini-2-5-flash-lite-gemini-3-1-flash-lite-eu-ai-act-art-50-2/177241/2
- OpenAI Verify: https://openai.com/research/verify/
- OpenAI provenance help: https://help.openai.com/en/articles/8912793
- OpenAI provenance update: https://openai.com/index/advancing-content-provenance/

## What this skill can verify

For text, the bundled deterministic pieces can verify only their own operations:

- `layer_a_clean.py` can report removed/replaced Unicode characters;
- `rewrite_guard.py` can report extractable invariant drift.

They cannot verify whether a provider's secret statistical watermark is present or absent.

Use provenance result states only when an appropriate detector actually ran:

- `detected`
- `not_detected`
- `abstain`
- `unavailable`

Never turn `not_detected` into `human-written`.

## Why deep rewriting is different from synonym swapping

A statistical text watermark is tied to generation-time token choices. Cosmetic substitutions can preserve substantial source structure. Deep mode instead reconstructs the prose from a semantic map and changes sentence segmentation, clause hierarchy, paragraph boundaries, safe information order, and lexical realization.

That is an editorial technique, not a guaranteed watermark-removal technique. Robustness varies by watermark family, detector, text length, entropy, transformation strength, and the model used for rewriting.

## Experimental confound: the rewrite model can add its own signal

A provenance experiment must separate three questions:

1. Did the source provider's signal survive the transformation?
2. Did the rewrite provider add a new signal?
3. Did the rewrite preserve the source meaning?

A generic AI detector cannot answer all three. For controlled research, record the source surface, rewrite surface, exact models when known, sampler configuration when controlled, transformation mode, detector/key identity, and semantic-fidelity checks.

## Operational rule

When a user asks to humanize or deeply re-express text:

- perform the editorial task;
- preserve facts and protected spans;
- do not invent mistakes, anecdotes, citations, metrics, or personal experiences;
- state provenance limits only when relevant;
- never promise undetectability or removal of an unsupported signal.
