# Word-range check

When a word bound is requested, save only the final reader-facing body in a UTF-8
file. Keep separate claim ledgers, source maps, change notes and provenance notes
outside that file. The helper reads exactly the selected file; it never guesses
which sections belong to the artifact.

```bash
python scripts/word_range.py body.md --min-words 450 --max-words 550
```

Replace the example bounds with the requested nonnegative integers. Bounds are
inclusive; either bound may be omitted, and the minimum cannot exceed the maximum.
Fix an out-of-range body with useful, supported prose and rerun before delivery.
For rewrites, preserve meaning and protected spans. Surface a conflict with
evidence or fidelity rather than padding or dropping required information. If
execution is unavailable, disclose that the deterministic check was not run.

## Counting and output

The count is `len(text.split())` on the raw UTF-8 file: every nonempty token
separated by Python Unicode whitespace counts once. NBSP, tabs and newlines are
separators; zero-width space is not. There is no normalization, Markdown/HTML
rendering or linguistic segmentation. Markdown markers, code, citations and URLs
count when they form whitespace-delimited tokens. Hyphens and apostrophes do not
split a token; unspaced CJK text counts as one token. A different counting rule
explicitly requested by the user takes precedence; report that this helper does
not implement it rather than silently substituting this convention.

The CLI prints JSON with `verdict`, `word_count`, `min_words`, `max_words` and
`checked_bounds`. With requested bounds, `PASS` exits 0 and `FAIL` exits 1.
Without bounds, `COUNTED` exits 0 with `checked_bounds: false`; no length constraint
is imposed and other skill checks remain unchanged. Invalid arguments/bounds,
non-regular or unreadable files and malformed UTF-8 produce `ERROR`, an `error`
message, a null `word_count`, `checked_bounds: false`, and exit 2. Missing bounds
are null. Regular-file symlinks are readable. The helper never writes the body.

This verifies only the chosen counting convention and bounds, not semantic
fidelity, factual truth, editorial quality, or release readiness.
