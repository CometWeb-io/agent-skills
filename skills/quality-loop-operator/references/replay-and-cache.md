# Replay and cache

Reuse a completed stage only when its content-addressed fingerprint exactly matches candidate, contract, policy, kernel/tool version and dependency hashes, and no invalidation tag applies. A replay whose hashes/tool versions drift is historical evidence, not proof that the current run is equivalent.
