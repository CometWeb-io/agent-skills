# Policy lock and evidence floor

When a run carries a frozen policy, verify the pack/revision/hash before issuing a verdict. If the active policy defines a minimum gate evidence grade, each required PASS gate must meet it. A gate can be structurally PASS yet inadmissible for READY when its evidence grade is below the policy floor.
