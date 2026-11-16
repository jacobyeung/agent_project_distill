# Host input staging order

`launch_r2.host.execute_packet` currently calls `input_paths` before physical `stage_inputs`. A fresh kit can therefore refuse a required `u/` input before it stages that input. This must be repaired after the active legacy run ends, before sealing or kit construction.

The default repair loads and verifies the kit configuration first for full-host execution, records the runtime check, and runs physical staging plus post-staging verification within the item 2 receipt action. It then resolves packet inputs and proceeds with the existing synthetic-input, pose-pin, configuration and transport guards. Preserve early refusal for already-readable synthetic packet inputs, so bounded fixture calls do not attempt real runtime startup. Validate newly staged inputs again before transport.

Add a `Checklist.stage_inputs` action that authenticates the plan, invokes the real staging function, then calls `staged`. Prove it with tiny real archive/payload bytes and a failing entry; a staging failure must leave an item 2 refusing receipt. Prove orchestration order through the real full-host path up to the sealed-pose refusal, substituting only the runtime identity bytes. Never grant fixture pose pins production admission or construct a full store.

After the source change, rerun the native host proofs and refresh coverage because host.py's old hash-matched hits no longer count. Replace line-number-dependent host coverage classification with the new precise ranges and missing-input reasons; do not mask locally exercisable new staging branches.

The system-interpreter/bootstrap launcher already emits a hashed E01 refusal if it cannot reach the venv. Document that early failure output separately from the runtime checklist receipt, which exists only after the venv starts.
