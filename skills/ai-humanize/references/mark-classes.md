# Provenance and mark classes

This file distinguishes mechanisms so the skill does not promise the wrong operation.

## 1. Text Unicode / edit artifacts

Examples: zero-width characters, bidi controls, exotic spaces, tag characters, private-use characters, mixed-script lookalikes.

**Bundled support:** `scripts/layer_a_clean.py`.

This class is deterministic and inspectable. The cleaner is intentionally conservative around Markdown code, emoji sequences, and script joiners.

## 2. Statistical / generative text watermarking

A generation-time algorithm changes token-selection probabilities using a key or pseudo-random function. The signal lives in token choices, not hidden Unicode metadata.

**Bundled support:** no detector and no remover. Deep rewriting can create an independently expressed version of the same content, but absence of a secret-key signal cannot be certified without an appropriate detector.

## 3. File/container provenance metadata

Examples: C2PA Content Credentials, EXIF/XMP, PDF or OOXML metadata.

**Bundled support:** none. Use file-format-specific tools available in the environment. Do not treat metadata removal as equivalent to removing an in-content watermark.

## 4. Pixel/audio/video watermarks and soft binding

The signal is embedded in image pixels, audio, or video rather than text/container metadata.

**Bundled support:** none. This skill does not modify media signals.

## 5. Model-side backdoors or training-time provenance

Signals produced by model training/fine-tuning or trigger behavior.

**Bundled support:** none. Out of scope.
