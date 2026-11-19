BUILT_FOR_INDEPENDENT_REVIEW. C resumes A at absolute step 200 and stops at 600. The launch gate accepts only a completed PASS CPU proof and separate written GO. No canary is needed.

| Identity | Value |
|---|---|
| Config identity | `6594f46cdc16168514aca26a6ce38285907adfc6ece0b75d8e10428ea0b2fe74` |
| Config file SHA256 | `2152828974490944a1713f5a539e87211f80179f0b5f9254ea9966fc65788733` |
| Run key | `05b8ac69` |
| Job name | `a15_cot_ap05b8ac69` |
| Bundle | `/project/community/jjyeung/okh7/i_7f1589c1` |
| Kit | `/project/community/jjyeung/okh7/x_7f1589c1` |
| Persistent slots | `/project/community/jjyeung/okh7/r/05b8ac69` |
| Archive | `p_fcc9a6f3.tar` |
| Archive SHA256 | `fcc9a6f333735d5b9b73ed6c56d21e41d00a683b10f46b00a2efff744d34f329` |
| Proof script | `p_05b8ac69.sh` (general, CPU only) |
| Training time limit | `24:00:00` (advanced, four GPUs) |

The estimate is `(400 × 0.153 + 11) / 4 = 18.05` wall hours. The 24-hour allocation leaves 5.95 hours for restore, exports and variation. The existing trainer budget remains 86,400 seconds with a 3,600-second stop reserve. The wrapper's GCS fallback deadline also uses 86,400 seconds.

The complete config delta from frozen A is below. Tree, code archive, stores, REMOVE lists, selection, units, reader pins, S2=true, S1=false, both max_own probabilities, 1,000-step LR horizon, seed, row offset and default cells are equal to A.

| Field | A | C |
|---|---|---|
| continuation | `null` | `{"config": "fac0705214fdecb53561c633d7d94642cd469b50b662c5de81f09d11891d115f", "root": "/project/community/jjyeung/okh7/r/673bc60f", "rows": "exact", "run": "673bc60f", "schema": "c0-v1", "step": 200}` |
| h1.stop_after_step | `200` | `600` |
| milestones | `[100, 200]` | `[400, 600]` |
| output | `"/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/runs/673bc60f"` | `"/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/runs/05b8ac69"` |
| preparation_output | `"/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/f/673bc60f"` | `"/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/f/05b8ac69"` |
| recipe.milestones | `[100, 200]` | `[400, 600]` |

`configs/cont1_cells.json` exposes every family's requested cents. `tools/build_cont1.py --cells FILE` puts those values directly into `type_mix.streams.<stream>.cells`, which the unchanged sampler consumes. A changed parameter set produces a distinct identity; it needs new admission, proof and GO. Unit allowlists and row/store pins remain explicit existing config parameters. This sealed C enforces identical admitted populations at its default boundary. The explicit `continuation.rows=rebind` config mode permits an intentional change to newly admitted cells and input pins. `--mix FILE` also accepts the existing unit allowlist and mix policy. The builder selects rebind mode when the requested mix changes; a source-pin rebind still needs matching store, selection and packaging records. Rebind mode preserves optimizer and absolute step, while rebuilding the requested sampler at that step; it does not claim equality with A's draws.

The bundle and kit tokens differ from A; `record_key=69d2930d` retains A's immutable data-record paths. All new writable run, slot, log, export-session and bundle/kit paths use C's opaque token. A's `r/673bc60f` is read only. Existing packet archives are checksum-verified and retained.

`b/c0.py` is the sealed runtime bridge. The wrapper first restores any C slot through its inherited A/B restore path. For the first C leg, `job.sh` verifies A's run marker, binding mirror and digest, selects only a verified step-200 A/B record, checks its archive size and SHA256, safely streams its regular members into C's private `d/`, and verifies the pinned `complete.json` plus every shard, replicated payload and rank RNG file. It retains A's checkpoint and binding bytes unchanged. The donor pointer records A's run, launch identity, exact step, archive digest and manifest digest.

A's checkpoint binds its admitted effective configuration. The bridge reconstructs that configuration from the frozen A template and authenticated admission/preparation pins, requires its identity to equal the checkpoint binding, and checks the sealed trainer revision. In C's default exact mode, it compares C's regenerated stream counts, database/indices hashes, mix populations, effective quotas and policy before restoring. A mismatched population or source refuses.

`b/r8.py` returns mode `u` for the verified donor and initializes only C's persistent marker. `b/w.py` installs the bridge only for a continuation config in mode `u`. The first native restore receives A's original binding and restores parameters, Adam state, buffers, trained-group state and RNG. The native loop receives start_step=200; it computes LR and row plans from absolute step 201. The first new output binding belongs to C. Later C checkpoints use the inherited native resume path. Empty or malformed optimizer state refuses before an update. The sealed trainer tree is byte-identical to A.

H1's `C1_INIT_LOCAL` path loads the pinned m544 full-weight/head export before optimizer construction. That warm start alone cannot preserve Adam or absolute step. C retains that initialization for compatibility, then restores A's full checkpoint. A's GCS `m200` and `mstop*` objects are weight exports, not substitutes for the verified slot. If A uses its separate GCS slot fallback, an operator must restore and verify a normal A/B slot before C can start; C does not fetch network objects.

The CPU proof retains A's admission, namespace, loader-audit and fix-11 environment setup. It additionally exercises the actual slot extraction and pointer verifier against a four-rank fixture. PASS requires `checks.resume_pointer.status=PASS`; the launch gate refuses CANARY. The proof fixture does not attest a future real A slot, which is verified at runtime.

Validation: 78 unique packet tests have passing results. The initial full run executed 77 tests; its single stale generated-diff failure is covered by the final 35-test recheck. `CONT1_TEST_LEDGER.json` records each result and both logs. Passing tests of unchanged code, including the 1.79 GB division fixture and historical A CANARY gate, are retained to respect the scratch cap. The runner checks deterministic archives, two byte-equal fixture kit derivations, production-form review/staging/archive evidence, four-rank D0 OFF optimizer identity, native unit regeneration, the CPU first batch and fix-11 nounset replay. Large immutable local fixture files share hardlinks; source snapshots remain untouched. The continuation tests compare default step-201–600 plans, check wrong run/step/config/checksums and missing optimizer state, exercise the adapter and resume chooser, and execute the PASS-only gate. The native small-model test compares 206 uninterrupted updates with 200 plus six resumed updates: parameters, Adam state, RNG, LR and rows are bit-exact. It uses native shard serialization/restore with mocked single-rank collectives. Other sampler populations are synthetic; the VQA check also uses the real local admitted population.

Reviewer checks: inspect the A launch-to-effective-config authentication chain, slot extraction and checksum checks, native restore adapter, new-output binding, row-population equality, independent writable namespaces, PASS-only gate, fix-11 replay, 24-hour limits and exact archive/derived-kit inventory. Confirm the real step-200 slot exists with full optimizer state. Independently scan the new runtime/proof text and seal the final deployed kit. Confirm the operator's written boundary GO and normal monitoring rules before submission.

Local tests do not prove Orchard namespaces, filesystem capacity, real A checkpoint availability, GPU/FSDP bit-exactness, production RGB admission, full routing regeneration or throughput. Regenerated database or population hashes may differ in production; C then refuses and needs investigation. No Orchard access, SSH, Git, GPU launch, external write, mirror or independent review occurred. The brief confines this task to local CPU work; `out/REVIEW_REQUEST.json` is the local handoff. `out/proof/CONT1_RESEAL.json` is a fixture seal, not production approval. The explicit snapshot comparison in this report identifies the requested authority baseline. `out/CONT1_STORAGE.json` records a conservative 2.88 GB of changed local storage, counting immutable hardlinks once. The workspace also contains substantial inherited artifacts; no cleanup was attempted.
