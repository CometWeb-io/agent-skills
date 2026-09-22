# Campaign mode

Campaigns process many independent candidates under one frozen policy.

Required controls:

- unique candidate + contract identity;
- deterministic run ID;
- per-candidate evidence/finding/repair namespaces;
- explicit dependencies between candidates when real;
- bounded concurrency;
- declared work budget when used;
- checkpoint/resume state that records completed run IDs rather than inferring from filenames;
- no cross-candidate closure or acceptance evidence.

Prioritize by explicit campaign priority and dependency order. Do not silently drop candidates when budget is exhausted; mark them `DEFER_BUDGET`.
