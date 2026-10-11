# Displayed calculation checks

Use `scripts/check_calculations.py` for ratios, calculated quantities and conservative
uncertainty endpoints actually displayed in a manuscript or PDF. Copy the displayed
decimals and units from that artifact, not from the helper's recommended result. Retain
the operands/source calculation in the QA evidence; express its exact result as an
integer numerator/denominator. A percent already scaled to 100 has that factor in its
numerator. `1/3 ratio` and `100/3 %` are different inputs; no unit conversion is implicit.

Run from the skill directory:

```bash
python scripts/check_calculations.py /path/to/calculations.json
python -m unittest discover -s tests -p 'test_calculations.py' -v
```

Minimal input, with no optional fields:

```json
{
  "schema": "cometweb.ebook-calculations/v1",
  "calculations": [
    {
      "id": "ratio-1",
      "mode": "nearest_half_even",
      "value": {
        "exact": {"numerator": 1, "denominator": 3, "unit": "ratio"},
        "displayed": {"value": "0.33", "precision": 2, "unit": "ratio"}
      }
    },
    {
      "id": "range-1",
      "mode": "conservative_bounds",
      "lower": {
        "exact": {"numerator": 1, "denominator": 3, "unit": "kg CO2e"},
        "displayed": {"value": "0.33", "precision": 2, "unit": "kg CO2e"}
      },
      "upper": {
        "exact": {"numerator": 2, "denominator": 3, "unit": "kg CO2e"},
        "displayed": {"value": "0.67", "precision": 2, "unit": "kg CO2e"}
      }
    }
  ]
}
```

`calculations` must be nonempty, with unique IDs (letters/digits/underscore/hyphen).
`nearest_half_even` is ordinary nearest rounding, with exact ties to the even final digit:
`1/8` becomes `0.12` at precision 2; `3/8` becomes `0.38`. It need not round outward.
`conservative_bounds` requires both `lower` and `upper`: floor the lower endpoint and
ceil the upper endpoint at their shared displayed precision. Negative endpoints also
round toward negative/positive infinity, rather than toward/away from zero. For example,
`[-2/3, -1/3]` becomes `[-0.67, -0.33]`. Exact endpoints remain unchanged.

`exact` contains integer numerator/denominator (booleans, floats and strings are invalid),
each with at most 1000 decimal digits; denominator must be nonzero. Negative denominators
are supported and the original expression is retained. `displayed.value` is a finite
plain decimal string, with dot separator, no exponent, whitespace or leading zeros.
Precision is an integer from 0 through 100. The number of displayed fractional digits
must match it. Units are nonempty strings without surrounding whitespace and must match
exactly; both bounds require the same exact unit and displayed precision. Unknown fields,
unknown modes, duplicate JSON keys, non-finite constants and reversed exact bounds are
input errors. Input is a regular UTF-8 JSON file, limited to 4 MiB; directories, FIFOs and
device files are rejected. Symlinks to regular files are supported. The helper reads input and writes only
its JSON result to stdout.

Exit 0 / `CALCULATIONS_MATCH`: every supplied display matches. Exit 1 / `BLOCKED`:
valid records contain wrong rounding, precision, unit or reversed displayed bounds.
Exit 2 / `INPUT_ERROR`: malformed, unsupported or unreadable input; command-line usage
errors use argparse's stderr. Results contain `calculations`, `blockers` (code/detail),
the unchanged `exact` expression, a `reduced` fraction, each `expected` decimal and
endpoint `matches` flags. This
checks the canonical rounding at that precision, not merely any wider enclosing interval.
The output `limits` states the helper's qualification boundary.

After changing a calculation, wording, unit or displayed precision, rerun against the
new artifact and save the input/result with `examples_and_numbers` QA evidence. Publication
fingerprints still bind the manuscript/PDF through `ebook_check.py`; this standalone
result does not mark a publication review complete.

Limits: no arbitrary expression evaluation, manuscript/PDF extraction, automatic discovery
of omitted calculations, verification of source operands, dimensional analysis, uncertainty
model validation or publication authority. Rational arithmetic avoids binary float and
finite decimal-context errors; a passing result proves only the supplied comparison.
