# Tool authority v5

Council może analizować szeroko, ale side effects wymagają jawnej klasy authority.

Przed akcją zewnętrzną uruchom `tool-authority`.

## Klasy

- `T0` — read-only / lokalne obliczenie,
- `T1` — bezpieczna wewnętrzna zmiana odwracalna,
- `T2` — external/public side effect lub wysłanie komunikacji,
- `T3` — financial, destructive, credential-sensitive lub high-risk data action,
- `T4` — nieodwracalna akcja wysokiego ryzyka / wielkiej stawki.

T2+ powinno być jawne w reasoning/planie. T3/T4 wymagają human approval. Nie używaj faktu, że Council ma `GO`, jako substytutu autoryzacji do działania.
