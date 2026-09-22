# Eval and portability audit

Check whether the package has:
- executable behavior cases, including fail-closed negatives;
- routing positives and negatives;
- tests for material guard branches;
- package-after-unzip validation;
- reproducible packaging where claimed;
- host metadata that does not overclaim runtime verification;
- no hidden dependency on repository-level files unless declared.

A runtime compatibility claim requires executed evidence from that host/configuration. Static metadata compatibility must be labeled as static only.
