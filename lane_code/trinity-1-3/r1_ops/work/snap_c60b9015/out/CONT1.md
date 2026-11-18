LOCAL_CHECKS_PENDING_HEAVY_TEST. C resumes A at absolute step 200 and stops at 600. The launch gate accepts only a completed PASS CPU proof and separate written GO. No canary is needed.

| Identity | Value |
|---|---|
| Config identity | `6594f46cdc16168514aca26a6ce38285907adfc6ece0b75d8e10428ea0b2fe74` |
| Config file SHA256 | `2152828974490944a1713f5a539e87211f80179f0b5f9254ea9966fc65788733` |
| Run key | `05b8ac69` |
| Job name | `a15_cot_ap05b8ac69` |
| Bundle | `/project/community/jjyeung/okh7/i_7f1589c1` |
| Kit | `/project/community/jjyeung/okh7/x_7f1589c1` |
| Persistent slots | `/project/community/jjyeung/okh7/r/05b8ac69` |
| Archive | `p_c60b9015.tar` |
| Archive SHA256 | `c60b901594843989b909cb785a5fdc9ad544ea0fdec8d78c63bf173e4f6e136c` |
| Proof script | `p_05b8ac69.sh` (general or bootstrap, CPU only; 48 CPUs, 800 GB, four hours) |
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

The deriver seals `b/` and every code subdirectory at `0500` after inventory generation and evidence validation. Isolated job-prefix imports cannot create bytecode in the kit. The resume chooser explicitly includes its sealed code directory so `python -I` can import the donor verifier. `tk_nx` uses `rsync --chmod=D700` to create private node-local directories at `0700`. `b/z.py` refuses in-place redeployment of a sealed kit. Operators must derive a fresh kit; changing permissions to redeploy is unsupported.

The CPU proof accepts `general` and `bootstrap`. Seal with `p.py --partition bootstrap` and submit the packaged proof script with `sbatch -p bootstrap`; the selected partition must match the authority. The default script selects `general`. Both use 48 CPUs, 800 GB, no GPUs and `04:00:00`. The kit authorization lists the two proof partitions and `advanced`; training stays on `advanced` with four GPUs and `24:00:00`. These partition fields do not grant submission GO.

The CPU proof retains A's admission, namespace, loader-audit and fix-11 environment setup. It additionally exercises the actual slot extraction and pointer verifier against a four-rank fixture. PASS requires `checks.resume_pointer.status=PASS`; the launch gate refuses CANARY. The proof fixture does not attest a future real A slot, which is verified at runtime.

Validation: 82 packet tests pass on this build. The 1.79 GB full-store regression awaits the required heavy-I/O authorization; all other tests ran. `tools/run_local_checks.py` checks deterministic packaging, two equal kit derivations, production-form evidence, four-rank D0 optimizer identity, native unit regeneration, CPU first batch and fix-11 shell replay. Five mode/partition regressions verify `0500` code directories, isolated cold and donor prefix execution without bytecode, inventory preservation, real `tk_nx` copies with the proof directory-mode checker, sealed-kit redeploy refusal, and both partition authorities. The native continuation test checks bit-exact parameters, Adam state, RNG, LR and rows for 206 uninterrupted updates versus 200 plus six resumed updates, with single-rank collectives mocked. Production RGB and other absent populations remain fixture boundaries.

Reviewer checks: verify the archived deriver seals all code directories, `tk_nx` copies them at `0700`, the isolated prefix preserves inventory, and the selected proof partition matches both authority and submission. Verify training still selects advanced and inspect the A launch-to-effective-config authentication chain, slot extraction and checksum checks, native restore adapter, new-output binding, row-population equality, independent writable namespaces, PASS-only gate, fix-11 replay, 24-hour limits and exact archive/derived-kit inventory. Confirm the real step-200 slot exists with full optimizer state. Independently scan the new runtime/proof text and seal the final deployed kit. Confirm the operator's written boundary GO and normal monitoring rules before submission.

Local tests do not prove Orchard namespaces, filesystem capacity, real A checkpoint availability, GPU/FSDP bit-exactness, production RGB admission, full routing regeneration or throughput. Regenerated database or population hashes may differ in production; C then refuses and needs investigation. No Orchard access, SSH, Git, GPU launch, external write, mirror or independent review occurred. The brief confines this task to local CPU work; `out/REVIEW_REQUEST.json` is the local handoff. `out/proof/CONT2_RESEAL.json` is a fixture seal, not production approval. `out/CONT2.diff` compares the C1 baseline with this packet, including derived kit bytes and directory modes. `out/CONT2_STORAGE.json` records new local storage. No cleanup was attempted.
