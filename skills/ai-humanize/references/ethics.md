# Intended use and reporting boundaries

This skill is for editing text the user is allowed to process. Its bundled deterministic tooling operates only on text/Markdown hygiene and rewrite invariants.

## Appropriate use

- improve clarity, rhythm, tone, and naturalness;
- remove generic model-writing habits from the user's own or authorized drafts;
- preserve facts while substantially re-expressing prose;
- clean suspicious invisible Unicode or copy/paste artifacts in text/Markdown;
- research how text provenance mechanisms behave, with accurate uncertainty;
- compare rewrite strategies without treating a style heuristic as an authorship detector.

## Misleading claims to avoid

Do not claim that:

- a rewrite proves human authorship;
- a style catalog can determine whether AI wrote a passage;
- Unicode cleanup removes a statistical generation watermark;
- a missing detector signal proves that no provenance mechanism is present;
- rewriting guarantees compliance with an academic, platform, contractual, or disclosure policy.

If the user's context has a disclosure rule, preserve their agency while avoiding false certification. The skill can edit text; it cannot certify authorship history.

## Provenance reporting

Separate three different things:

1. **Deterministic text hygiene** — what `layer_a_clean.py` actually removed/replaced.
2. **Rewrite fidelity** — what `rewrite_guard.py` and semantic review can verify about preserved content.
3. **Provider/detector evidence** — results from an appropriate, actually executed provenance detector or first-party provider documentation.

Never collapse these into one claim such as “clean,” “human,” or “undetectable.”

## File/media scope

C2PA, EXIF/XMP, PDF/OOXML metadata, image/audio/video watermarks, soft binding, and training-time/model-side provenance are not bundled capabilities of this skill. Use the appropriate external tooling when the environment supports it, and report those operations separately from text rewriting.
