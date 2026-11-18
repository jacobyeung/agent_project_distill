BUILT_FOR_INDEPENDENT_REVIEW. C resumes A at absolute step 200 and stops at 600. The launch gate accepts a completed PASS CPU proof or the pinned canary exception, with separate identity-bound GO.

| Identity | Value |
|---|---|
| Config identity | `6594f46cdc16168514aca26a6ce38285907adfc6ece0b75d8e10428ea0b2fe74` |
| Config file SHA256 | `2152828974490944a1713f5a539e87211f80179f0b5f9254ea9966fc65788733` |
| Run key | `05b8ac69` |
| Job name | `a15_cot_ap05b8ac69` |
| Bundle | `/project/community/jjyeung/okh7/i_7f1589c1` |
| Kit | `/project/community/jjyeung/okh7/x_7f1589c1` |
| Persistent slots | `/project/community/jjyeung/okh7/r/05b8ac69` |
| Archive | `p_08f3a7b2.tar` |
| Archive SHA256 | `08f3a7b2ef2e1923ba77b464afcedbbe668a77a1915b4c32c0a815044ff7d9fd` |
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

`production_go_granted` is false and `production_go_required_separately` is true. The resource authority grants no launch GO. The submitter requires a completed PASS proof or the pinned canary exception, plus separate identity-bound `go.json`. The proof sealer validates the complete authority, permits general/bootstrap, and pins `k/4.json` alongside the runtime. Certification and proof sealing do not modify any file in `k/`.

The CPU proof authenticates the trainer with the same `v.tree(record_pin, TRAINER, commit)` call as `b/w.py`, then inserts `TRAINER` at the front of `sys.path` before importing `student_pilot.loader_audit.main`. `tk_pythonpath p` retains its existing composition. The config, trainer archive, training wrapper, run, bundle and kit identities remain unchanged.

The post-admission audit found no further production defects. The rehearsal also rejects empty staged-root arguments and records namespace failures separately from trainer/import failures. The local shell fixture places `student_pilot` only in the sealed epoch tree. This test arrangement detects the missing import path instead of masking it with a package under `b/`. Its relocated Python launcher preserves the permitted CPU virtual environment and its dependencies.

| Post-admission boundary | Verification and result |
|---|---|
| Runtime record and trainer | The shell checks the staged record SHA. The heredoc reads `k/0.json`; `v.tree` checks its record pin, schema, commit, complete file inventory and tree digest before import. A changed trainer refuses before executing it. |
| Environment and Python path | The real `c.sh` establishes `TRAINER`, runtime record aliases, closure, optional NumPy overlay, CPU visibility and private cache paths. The fixture tests both overlay branches with no trainer on the initial PYTHONPATH. |
| Run directory | `TK_RUNS_DIR=$NR`; the inner namespace binds `$NR` to `$X/runs`. `d.effective` reads the authenticated preparation from that logical run path. |
| Audit writes and mounts | The real loader writes `inputs/l.json` and `inputs/a.json` inside a real local bubblewrap namespace. Trainer and staged inputs remain read-only; runs and the proof job directory are writable. The outer proof maps the same run to its physical work directory. |
| Data authentication | The replay executes the real `d.effective`, pinned preparation reads, SQLite population scan, sampler, disk plan, routing selection and required-family checks on synthetic prepared data. No loader or validator body is mocked. |
| Report pins | The loader pins `l.json` in `a.json`. The outer proof requires the original config identity and checks the physical `l.json` SHA before merging checks. Changed identities and loader bytes refuse. |
| Check aggregation | The outer proof adds the resume fixture, audit checks and directory-mode check. Missing reports, missing required checks and failed checks refuse. The additional staged-binary inventory is retained. |
| Status and return code | A loader exception or failed prepared-data verification cannot produce PASS. Negative tests cover execution failure, verification failure, missing audit, wrong pin, wrong identity, failed check, missing required check, failed resume fixture and nonprivate directory. |
| Resume fixture | The unchanged verifier extracts a four-rank fixture slot and checks the exact step-200 pointer, binding and shard pins. The final proof requires `resume_pointer=PASS`; this fixture does not attest a future real A slot. |

KIT_DIFF compares the final archive with `snap_6a5c7d00`:

| Archive member | Before SHA256 | After SHA256 | Change |
|---|---|---|---|
| `p_05b8ac69.sh` | `4a304bfd2042c618ddb2bad4e33faaf429ba290480c2bde282149c10af9042db` | `0c065ddefb77dcfe864a3bb3d1f343d3b421d601ba34a0a71abfca43e88c31a5` | Verify trainer before audit import; isolated proof-tail rehearsal. |
| `s.sh` | `5f15c65f0cc1355330314300fe1f269accc642b953eccf7f42bde3851cd500f6` | `83d209076ba2d7502e4dc0dad0770e7509b46e48af8b72da0c71f061050c23dc` | Pinned C canary exception; unchanged PASS branch. |
| `sums.txt` | `ab08a74aef06e152804e5deedbc2ee8664d9a6bdd46974c68179bd33876a070f` | `1d2270924ef7a7397d8fcf9ecd61811b8bfce954929acb5288d4119a4f5e97ae` | Pin the changed script bytes. |

Validation: all 112 packet tests pass, including all three tests in `tests/test_fix10.py`, its full-store division regression, 17 C canary gate tests and five audit/rehearsal tests. `tools/run_local_checks.py --share-fixture-bytes` passes deterministic packaging, two equal kit derivations, production-form evidence, four-rank D0 optimizer identity, native unit regeneration, CPU first batch and the full test suite. The new coverage includes a changed-trainer refusal, real loader success and failure inside bubblewrap, and nine outer-proof failure cases. `out/proof/CONT4_LOADER_REPLAY.json` pins the real loader reports. A separate native outer-bubblewrap check passes and is recorded in `out/proof/CONT4_OUTER_NAMESPACE.json`. `out/proof/CONT4_RESEAL.json` records successful general/bootstrap fixture seals with unchanged kit inventory.


The binding ORCH ruling is `events/r1_ops/20261118T0842Z_ORCH_RULING_C_canary_and_general_order.md`, SHA256 `31f5e70ca014a370913115e124290805744e5947790e8d2463e5b0225130aa89`. It authorizes the boundary canary subject to its ordering, real step-200 checkpoint/population checks and kill rules; this packet does not replace those conditions.

The C canary gate requires `canary=true`, `ADMISSION_JOB=172180`, and `PROOF_JOB` equal to the new bundle's `job.id`. It authenticates admission receipt SHA256 `ed9aad679a1d9dd6302970dcb82d02d5b92fd6f3a53aede6bf219fca405f8d21` and log SHA256 `0658f1614ad94ff6141b66ba1523b37d2ea60d28c074929ac6e6f2307b1d58a3`. All five admission checks must PASS; the resume pointer must be the step-200 A fixture. The receipt's config/contract, old manifest and current staged hashes must match. The pinned log must show exactly one `exit rc=0`. The new proof must be PENDING or RUNNING under `a15_cot_ap05b8ac69` on general; held PENDING is accepted. The gate exclusively creates `KH/o/<PROOF_JOB>.canary.json` after kit validation. It marks gate acceptance, not successful training allocation.

`ADMISSION_KIT` accepts exactly `/project/community/jjyeung/okh7/x_7f1589c1` (the default) or `/project/community/jjyeung/okh7/x_7f1589c1.f172180`. Retain the old receipt, log, manifest and authenticated config/staging files together. If deriving the new kit changes its manifest, use the moved-aside old kit as ADMISSION_KIT; the current-kit location works only while its receipt-authenticated manifest and files remain intact. Moving the old kit aside and deriving the new kit at its original name preserves the unchanged bundle/kit identities. PASS mode does not consult admission evidence or write a canary marker.

The proof's `--rehearsal STAGED_ROOT` switch reuses the production tail and both namespaces, with fresh writable run/job paths and a read-only existing staged root. It performs `tk_env`, `tk_pythonpath p`, the trainer-tree verification, native imports, a pinned VQA descriptor read and a read-only SQLite schema query. The native loader starts and reaches `d.effective`; only a FileNotFoundError for the exact absent `data_receipt.json` is expected. Other exceptions fail. It does not stage archives, run admission, restore a checkpoint or certify populations. The rehearsal job name is `a15_cot_ap05b8ac6a`, which the canary queue predicate refuses. Receipts are `<job>.rehearsal.json` and logs are `<job>.rehearsal.log`; terminal status is exclusively REHEARSAL_OK or REHEARSAL_FAIL and cannot satisfy the launch gate. Each step is reported; the first uncompleted step fails when execution fails.

The operator must first retain the staged root on `orchard-community-0` and reseal the final certified kit for general into `BUN/a4.json`. Seal the deployed authority with `/usr/bin/python3 -I -B /project/community/jjyeung/okh7/i_7f1589c1/p.py --kit /project/community/jjyeung/okh7/x_7f1589c1 --bundle /project/community/jjyeung/okh7/i_7f1589c1 --binding /project/community/jjyeung/okh7/i_7f1589c1/BINDING.json --partition general --out /project/community/jjyeung/okh7/i_7f1589c1/a4.json`. The sealer exclusively creates this path; choose a fresh authority filename if it already exists and use the same filename in sbatch.

Run this exact argv after the general-slot ordering permits the short rehearsal:

```bash
sbatch --partition=general --nodelist=orchard-community-0 --nodes=1 --ntasks=1 --cpus-per-task=4 --mem=32G --time=00:30:00 --gres=gpu:0 --job-name=a15_cot_ap05b8ac6a --no-requeue --output=/project/community/jjyeung/okh7/x_7f1589c1/o/%j.rehearsal.out --error=/project/community/jjyeung/okh7/x_7f1589c1/o/%j.rehearsal.err /project/community/jjyeung/okh7/i_7f1589c1/p_05b8ac69.sh /project/community/jjyeung/okh7/i_7f1589c1/a4.json --rehearsal /tmp/jjyeung/p_05b8ac69_172180/tmp/jjyeung/a_05b8ac69/root
```

The root is from the pinned 172180 receipt and is node-local. A missing root produces REHEARSAL_FAIL; do not restage or rerun admission under this switch. `out/proof/CONT4_REHEARSAL.json` records the local native-loader boundary test. The operator must inspect the Orchard rehearsal before submitting the full proof, then follow the ruling's held-proof/general ordering and real A step-200 checkpoint/population checks. A rehearsal job must never be written to the bundle's `job.id` as the parallel full proof. The canary gate checks for a rehearsal receipt and refuses it.

Reviewer checks: verify the archive SHA256, `KIT_DIFF4.md` and `CONT4.diff` against `snap_6a5c7d00`. Review the fixed two-path admission allowlist, byte pins, five checks, staged-input equality, general queue predicate, exclusive canary marker, distinct rehearsal name and non-PASS receipts. Confirm the PASS branch and training sbatch argv remain byte-identical. The proof script, launch gate and checksum file change in the archive. Compare the generated heredoc's tree check and import order with `b/w.py`; inspect the real loader replay and the negative cases. Reseal the proof against the final deployed bundle and certified kit, run the production CPU proof and verify every required check plus its receipt pins. The delta review must cover these final proof and gate bytes before deployment. The PASS branch retains every predicate. The canary branch requires the pinned admission evidence, an active new proof and identity-bound GO under the written ORCH ruling.

Local evidence does not certify Orchard's namespace configuration, production prepared rows, filesystem capacity, full routing regeneration, the real A checkpoint or GPU/FSDP behavior. The local replay uses synthetic SQLite rows and preparation receipts with the byte-identical sealed trainer; it executes the actual nested kit namespace, and a native outer-namespace fixture verifies that the retained staged root is read-only while the fresh run is writable. C continues from A's full step-200 optimizer checkpoint to step 600; the resume fixture is not a substitute for runtime donor verification.

No SSH, Orchard access, Git, GPU launch, external write or independent review occurred. `out/REVIEW_REQUEST.json` is the local handoff. The general/bootstrap proof seals are local fixtures, not production approval. All existing packet archives remain checksum-identical. `CONT4.diff` covers local code, tests, reports and derived kit differences from `snap_6a5c7d00`. No cleanup was attempted.
