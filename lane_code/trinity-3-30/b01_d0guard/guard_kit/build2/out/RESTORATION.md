# Candidate restoration

The supplied closure passes metadata admission (`CLOSURE_ADMISSION.json`) and the unchanged C8r `prepared` and `check_init_spec` functions (`RESTORATION_TEST.json`). The per-file supplied inventory also matches (`CLOSURE_FILES_AUDIT.json`). The local path adapter resolves original logical pins to read-only supplied files; it preserves their contents and digest checks.

`guard_kit/closure.py` checks the selected artifact step, exact exported artifact bytes, original input-config pin, trainer-computed prepared config identity, preparation pin, binding, source-tree identity, run/source seals, baseline initialization, trained-group membership and initial-to-final hash chain. The job repeats this check against the extracted export and runs `guard_backend.authenticate_candidate` before candidate preparation.

`read_runtime.prepared` verifies the production data receipt, preparation and architecture fields, frozen route policy, scene exclusions, actual trainer source tree/archive, and source-seal bindings. `runtime.check_init_spec` verifies the evaluator's trained groups. Model restoration then retains the unchanged trained-tensor loader and native parity code. Local metadata tests do not execute that model restoration.

The real metadata fixture is pinned in `candidate_m50/CLOSURE.json`. The wrong-config, foreign-step, changed-chain and non-byte-equal-artifact tests are in `G2_TESTS.json`. Production steps require their own freshly fetched closure and `.done`; the metadata fixture cannot authorize them.

The reviewed export stager and checker files are byte-identical (`SOURCE_IDENTITY.json`). `stage_candidate.py` adapts only the checker's subprocess namespace and output bind to C8r; it still requests full shard hashing and exact tensor inventory checks. This integration has not executed on Orchard.

The tiny rehearsal artifacts change only the file digests at `heads.sha256` and `full_weights.sha256` (`rehearsal/whole/sandbox/fixture/PREPARATION.json`). Their complete tensor checks pass (`rehearsal/whole/TENSOR_CHECKS.json`), but the CPU model boundary does not load them or validate the retained trained-group fingerprints against tiny tensors. Actual candidate weights, GPU restoration, prompt parity and token identity remain unchecked.
