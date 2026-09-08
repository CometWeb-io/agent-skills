# Layer A demo

## Input (with invisible characters)
Hello​ world with‌ soft­hyphen and а (Cyrillic lookalike)

## After `python scripts/layer_a_clean.py --aggressive-homoglyphs`
Hello world with softhyphen and a (Cyrillic lookalike)

Removed: ZERO WIDTH SPACE, ZERO WIDTH NON-JOINER, SOFT HYPHEN, exotic space, Cyrillic а → a.
