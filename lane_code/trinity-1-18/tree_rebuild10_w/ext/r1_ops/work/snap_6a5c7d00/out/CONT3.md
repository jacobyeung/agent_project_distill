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
| Archive | `p_6a5c7d00.tar` |
| Archive SHA256 | `6a5c7d009a19cb5bac690b864f2be68bb5cebc29649923c93da36328d0f96888` |
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

The derived `k/4.json` seals modes `["p","t","u"]`, `new_gpus={"p":0,"t":4,"u":4}`, top-level partition `advanced`, wall limit `86400`, one node, arm `0`, GPU cap `4`, one parallel job and `resume="latest"`. Its per-mode resources authorize `p` on `general` or `bootstrap` with zero GPUs and 14,400 seconds; `t` and `u` require `advanced`, four GPUs and 86,400 seconds. Proof and training request 48 CPUs and 800 GB. C's verified donor and later checkpoint restores enter `u`; the inherited cold-entry resource envelope also carries `t`, while C's restore bridge still refuses training without a continuation checkpoint.

The deriver binds these resource fields before generating `SHA256SUMS.txt`. It preserves the supplied evidence identity, revision, admission contract and expiry. Both `b/g.py` and `b/i.py` validate the exact authority and allocation. The sealed entry sets `TK_ALLOCATION_MODE` before preflight and recursive admission: CPU preparation inside a training job uses that training allocation's limits. A standalone proof uses the zero-GPU proof limits. The runtime checks a supplied `SLURM_TIMELIMIT`; the sealed launch slot, job and wrapper pin the training wall limit even where Slurm omits that variable.

`production_go_granted` is false and `production_go_required_separately` is true. The resource authority grants no launch GO. The submitter still requires a completed PASS CPU proof and separate identity-bound `go.json`. The proof sealer validates the complete authority, permits general/bootstrap, and pins `k/4.json` alongside the runtime. Certification and proof sealing do not modify any file in `k/`.

The CPU proof retains A's admission, namespace, loader-audit and fix-11 environment setup. It additionally exercises the actual slot extraction and pointer verifier against a four-rank fixture. PASS requires `checks.resume_pointer.status=PASS`; the launch gate refuses CANARY. The proof fixture does not attest a future real A slot, which is verified at runtime.

Validation: all 88 packet tests pass, including all three tests from `tests/test_fix10.py` and its full-store division regression. `tools/run_local_checks.py` passes deterministic packaging, two equal kit derivations, production-form evidence, four-rank D0 optimizer identity, native unit regeneration, CPU first batch and fix-11 shell replay. Five C3 tests exercise the real `g.check`, `i.authorize` and `x.ready` on fixture records: proof on both CPU partitions, both training modes, nested admission, sealed fields, and refusal of wrong modes, GPU counts, partitions, nodes and wall limits. Only native data admission and persistent slot selection are mocked in that resource matrix. Existing prefix tests execute the real metadata preflight, isolated gate and resume imports, then verify `a.py`, unchanged inventory, no bytecode and `0500` code directories. The native continuation test checks exact parameters, Adam state, RNG, LR and rows for 206 uninterrupted updates versus 200 plus six resumed updates, with single-rank collectives mocked.

Reviewer checks: verify the archive SHA256 and `CONT3.diff` against `snap_c60b9015`; inspect `d.py`, `r4.py`, the derived `k/4.json`, `b/g.py`, `b/i.py`, the job prefix and recursive admission path. Check all per-mode limits, `resume="latest"`, the 24-hour launch slot and wrapper, separate written GO, and the proof seal's authority hash. Derive and certify a fresh final kit with real evidence; never patch a certified `k/4.json`. Confirm the real step-200 A slot contains the full optimizer state, the continuation authentication chain and row populations match, and the deployed manifest survives prefix execution without bytecode. Run the production CPU proof on the selected CPU partition and obtain the operator's written boundary GO before submission.

Local tests do not prove Orchard namespaces, filesystem capacity, real A checkpoint availability, GPU/FSDP bit-exactness, production RGB admission, full routing regeneration or throughput. Regenerated database or population hashes may differ in production; C then refuses and needs investigation. No Orchard access, SSH, Git, GPU launch, external write, mirror or independent review occurred. The brief confines this task to local CPU work; `out/REVIEW_REQUEST.json` is the local handoff. `out/proof/CONT3_RESEAL.json` records fixture seals, not production approval. `out/CONT3.diff` compares the frozen `snap_c60b9015` packet with this packet, including derived kit bytes and directory modes. All existing packet archives remain checksum-identical. No cleanup was attempted.
