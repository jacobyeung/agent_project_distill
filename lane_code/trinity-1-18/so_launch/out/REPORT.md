VERDICT: DONE Build-21 patches 03, 04 and 02 apply with zero fuzz and pass OFF-identity, patch and native CPU checks; ten Gloo tests and one pool-fixture test remain for the lane.

## Build 21 port

The delivery is [patches_b21/manifest.json](patches_b21/manifest.json), in order **03, 04, 02**, against seal `b262e7a757d93e2485a523765916507b2bf3305fe3213cffca100007d19f2ce8` (936 files, measured and verified). Each patch applies independently and in that order with `patch --batch --fuzz=0 --no-backup-if-mismatch -p1`. The [handover](NOTE_FOR_TREE_REBUILD.md) has the exact commands and switch table. Every switch defaults OFF. **01 stays OFF**: it cannot hit in the production topology in a way that avoids native work; it is excluded from this delivery.

No hunk moved or failed. Build 21 preserves all five production files touched by these patches, so the three regenerated diffs are byte-identical to the reviewed build-20 diffs. The manifest pins build 21 rather than build 20. The recommended tree differs in exactly five production files and three added test scripts; no `.orig` or `.rej` files remain. Input bytes remain unchanged.

| Patch | Production hunks moved / failed | Bytes | SHA256 |
|---|---|---:|---|
| [03_checkpoint_verify_memo.diff](patches_b21/03_checkpoint_verify_memo.diff) | 0 / 0 | 13638 | `bf0ea4745a3e059fd0d0cdffc5fa7cd99ad646b7d70c7957df95f87b4f6c4e54` |
| [04_launch_phase_timing.diff](patches_b21/04_launch_phase_timing.diff) | 0 / 0 | 11751 | `c939f738090ac7ad78ce3aadf596ccbc5862945a1cd8fb55655f29141aa03120` |
| [02_parallel_frame_sha.diff](patches_b21/02_parallel_frame_sha.diff) | 0 / 0 | 6324 | `9f20e45be76d5ad356df185f6604c6e6ea822d6378286e1f8f3ed7df81158ea9` |

Started Thu Nov 19 10:36:04 UTC 2026 on `trinity-1-18`; deadline 11:51:04 UTC. This report was assembled at Thu Nov 19 10:44:04 UTC 2026. The artifact audit measured workspace size **841,561,605 bytes** and scratch free space **409,521,963,008 bytes**. No production speedup was measured. Patch 03's estimate is **about 4–5 min (inferred)** per resume launch; up to about 9 only if the page cache does not keep the checkpoint. Patch 04 saves no time directly; patch 02 needs an isolated warm-storage measurement.

## Exact build-21 commands and results

The five OFF checks ran first. They compare baseline and patched checkpoint/frame verdicts and fixture bytes, job and recursive-run command traces and stdout/stderr, and real `c.sh` stage output/steps bytes. The job and run checks cover successful dispatch and an exit-7 guard failure with switches unset and explicitly zero. The dedicated stage check runs OFF only. Its exact result is `Ran 5 tests in 2.809s`, `OK` ([output](tests/port21/off_identity.txt)).

```bash
source work/fix2_env.sh
export TMPDIR="$L/work/port21/tmp" TEST_TMP_ROOT="$L/work/port21/tmp" LANE_TEST_OUTPUT="$L/work/port21/tmp"
nice -n 10 "$PY" -I -s -B work/port21/check_off.py work/port21/recommended
nice -n 10 "$PY" -I -s -B work/port21/run_suites.py
nice -n 10 "$PY" -I -s -B work/port21/check_known_failures.py out/tests/port21
nice -n 10 "$PY" -I -s -B work/port21/audit_delivery.py
```

`PY=/scratch/jjyeung/envs/p1cpu/bin/python`. The runner sets CUDA empty, bytecode disabled, OMP/MKL/OpenBLAS threads to eight, tokenizer parallelism false, all test/cache paths inside this workspace, and `SO_NO_LOCAL_SOCKETS=1`. Torch tests set `torch.set_num_threads(8)` before test work. Tests execute serially under nice 10. Every log below contains the exact command, working directory, environment, stdout/stderr and exit code. [INDEX.md](tests/port21/INDEX.md) also links application and audit evidence.

| Tree / script | Exact output summary | Full command and output |
|---|---|---|
| `03_checkpoint_verify_memo.test_checkpoint_verify_memo` | `Ran 10 tests in 0.292s`; `OK` | [log](tests/port21/03_checkpoint_verify_memo.test_checkpoint_verify_memo.txt) |
| `04_launch_phase_timing.test_launch_phase_timing` | `Ran 7 tests in 1.642s`; `OK` | [log](tests/port21/04_launch_phase_timing.test_launch_phase_timing.txt) |
| `02_parallel_frame_sha.test_parallel_frame_sha` | `Ran 7 tests in 0.044s`; `OK` | [log](tests/port21/02_parallel_frame_sha.test_parallel_frame_sha.txt) |
| `01_diagnostic.test_prepared_input_cache` | `Ran 33 tests in 1.077s`; `OK` | [log](tests/port21/01_diagnostic.test_prepared_input_cache.txt) |
| `01_diagnostic.test_prepared_cache_wrapper` | `Ran 9 tests in 4.381s`; `OK` | [log](tests/port21/01_diagnostic.test_prepared_cache_wrapper.txt) |
| `recommended.test_checkpoint_verify_memo` | `Ran 10 tests in 0.268s`; `OK` | [log](tests/port21/recommended.test_checkpoint_verify_memo.txt) |
| `recommended.test_launch_phase_timing` | `Ran 7 tests in 1.536s`; `OK` | [log](tests/port21/recommended.test_launch_phase_timing.txt) |
| `recommended.test_parallel_frame_sha` | `Ran 7 tests in 0.046s`; `OK` | [log](tests/port21/recommended.test_parallel_frame_sha.txt) |
| `combined_diagnostic.test_checkpoint_verify_memo` | `Ran 10 tests in 0.285s`; `OK` | [log](tests/port21/combined_diagnostic.test_checkpoint_verify_memo.txt) |
| `combined_diagnostic.test_launch_phase_timing` | `Ran 7 tests in 1.469s`; `OK` | [log](tests/port21/combined_diagnostic.test_launch_phase_timing.txt) |
| `combined_diagnostic.test_parallel_frame_sha` | `Ran 7 tests in 0.044s`; `OK` | [log](tests/port21/combined_diagnostic.test_parallel_frame_sha.txt) |
| `combined_diagnostic.test_prepared_input_cache` | `Ran 33 tests in 1.065s`; `OK` | [log](tests/port21/combined_diagnostic.test_prepared_input_cache.txt) |
| `combined_diagnostic.test_prepared_cache_wrapper` | `Ran 9 tests in 3.665s`; `OK` | [log](tests/port21/combined_diagnostic.test_prepared_cache_wrapper.txt) |
| `native_baseline` | `Ran 86 tests in 2.783s`; `OK (skipped=11)` | [log](tests/port21/native_baseline.txt) |
| `native_recommended` | `Ran 86 tests in 2.909s`; `OK (skipped=11)` | [log](tests/port21/native_recommended.txt) |
| `native_combined_diagnostic` | `Ran 86 tests in 2.819s`; `OK (skipped=11)` | [log](tests/port21/native_combined_diagnostic.txt) |
| `native_recommended_on` | `Ran 86 tests in 2.886s`; `OK (skipped=11)` | [log](tests/port21/native_recommended_on.txt) |
| `extra_probes` | `Ran 5 tests in 0.128s`; `OK` | [log](tests/port21/extra_probes.txt) |

The delivered set has **24 patch tests + 86 native tests: 99 pass, 11 skip**. The diagnostic combined tree also applies the unchanged patch 01 solely to rerun its two scripts: **66 patch tests + 86 native tests: 141 pass, 11 skip**. Patch 01's tests do not establish a production cache benefit. The five OFF comparisons and five extra probes pass separately. Repeated baseline/ON/standalone runs are shown individually rather than counted as new test coverage.

The additional native admission-fixture comparison reproduces the same four failures and one error on baseline and patched build 21. Both 92-test attempts exit 1; the comparison exits 0. Exact outputs: [baseline](tests/port21/known_native_failures_input.txt), [patched](tests/port21/known_native_failures_patched.txt), [matching identities](tests/port21/known_failure_comparison.txt). These fixture failures remain outside the supported 86-test gate; they are not counted as passes.

The retained [OFF harness error](tests/port21/off_identity.harness_error.txt) records two Python indentation errors in extracted fixture methods. The corrected harness passes before any ON suite runs. No production code changed to address these errors.

## Lane tests and remaining work

Sockets are unavailable by dispatch; this run does not attempt them. The native runner explicitly skips the whole `tests.test_s1_checkpoint_buffers.CheckpointBufferTests` class because its `setUpClass` starts a real TCP/Gloo process group. The lane still needs these ten tests:

- `test_buffers_are_rank_private`
- `test_checkpoint_restore_preserves_running_statistics`
- `test_default_stall_budget_covers_native_startup`
- `test_disk_headroom_is_checked_before_any_checkpoint_payload`
- `test_export_disk_guard_precedes_publication_and_payloads`
- `test_legacy_shard_cannot_initialize_mutable_buffers`
- `test_startup_stop_exports_with_optimizer_and_shared_leg_budget`
- `test_two_hour_plan_counts_early_signal_and_weight_exports`
- `test_whole_leg_budget_counts_measured_states_and_exports`
- `test_whole_leg_guard_does_not_admit_space_for_only_one_state`

The eleventh skip is `tests.test_s1_launch_kit.LaunchKitTests.test_packaged_templates_validate_but_do_not_authorize_execution`: its authenticated pool selection is not staged. With sockets and the authenticated fixtures available, rerun the same gate without the sandbox skip:

```bash
SO_NO_LOCAL_SOCKETS=0 nice -n 10 "$PY" -I -s -B "$L/work/run_native_regression.py" "$L/work/port21/recommended"
```

READY names `work/base/tree_b01ce449`, `work/build15/inputs` and `work/build_n1/inputs` for the lane's separate focused suites. The exact read-only source paths are recorded and linked under `work/port21/fixtures/work` ([mapping](tests/port21/fixture_links.json)). The bounded 86-test native gate does not consume those links. This run does not claim to reproduce READY's separate 112-test proof.

The lane must rebuild/rescan and reseal the kit, run its socket/pool tests and preserve all native training gates before launch. No Orchard job, GPU validation or production launch timing ran here. The Orchard complete-journal reuse-floor measurement in [MEASURE_NATIVE_REUSE.md](MEASURE_NATIVE_REUSE.md) remains unrun; the separate cross-run store implementation, two-node checks and admission review are outside this port. These pending production checks do not change the completed build-21 port result.

## Risks and detection

Patch 03 assumes completed checkpoints remain immutable under cooperating writers. Stat metadata is not authentication against a same-user forger or a guarantee of immediate timestamps for arbitrary mmap writes. The extra probes force rehashing after chmod, refuse writes during hashing and disable hits under symlinked parents. Check `.checkpoint-verification/<job>.events.jsonl`; missing events mean no demonstrated memo benefit. Native loaders still verify SHA256 before loading shards, replicated data and RNG (`work/port21/baseline/student_pilot/full_ft.py:563,603,618`; `carrier_c1_run.py:2069`).

Patch 02 hashes every byte, caps workers at eight and pending work at twice the worker count; storage contention can make it slower. Fault and bounded-work probes pass. Measure f2 alone before enabling it. Patch 04 writes timing only; missing or unwritable logs cannot abort a launch. OFF behavior is verified on synthetic fixtures, not a full Orchard run. The five native admission-fixture failures require fixture repair and a lane rerun, not relaxed production checks.

No Git, SSH, Slurm, GPU, paid API, production job, file deletion or external write ran. All source copies and test outputs remain in this workspace; READY fixture targets remain read-only. No other agent's work was stopped.

## Framework evidence

The installed Torch version is `2.11.0+cpu` (`/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/version.py:4`). CPU intra-op thread control and its required placement before test work are documented at `torch/_torch_docs.py:9814–9824` in that installation and in the [official PyTorch 2.11 set_num_threads documentation](https://docs.pytorch.org/docs/2.11/generated/torch.set_num_threads.html).

The skipped fixture opens a local socket and calls `init_process_group('gloo', init_method='tcp://…')` (`work/port21/baseline/tests/test_s1_checkpoint_buffers.py:28–35`). Installed `torch/distributed/rendezvous.py:190–207,210–237` constructs its TCPStore. The [official TCP initialization documentation](https://docs.pytorch.org/docs/2.11/distributed.html#tcp-initialization) describes the network rendezvous. No socket-dependent test is counted as passed.

## Measured phases and preparation inputs

Mode p measured **140.57 minutes in job 172660** and **145.27 minutes in job 171377**. The [interval arithmetic](phase_timing.json) retains timestamps and evidence labels; [numbered log excerpts](evidence/startup_log_excerpts.txt) retain the raw evidence. The source logs are `/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/r1_ops6/work/mon/last.txt` and `/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/o/look1.out`. Preparation mtimes and C' step duration also use the supplied `PROMPT.md`. Measured envelopes overlap where stated and must not be added blindly. Table source paths refer to the input tree; trainer code is unchanged.

| Phase | 172660 minutes | 171377 minutes | Evidence | Reads and writes | Pure function of named inputs? |
|---|---:|---:|---|---|---|
| Submission to wrapper | 2.27 | unavailable | Supplied submission time and measured wrapper start | Allocation availability; starts wrapper | No; scheduler and host state. |
| Wrapper to import stage | 0.17 | 0.03 | Measured timestamps | Staging inventory and export-session setup; wrapper log | No; filesystem/runtime state. |
| Import preflight | 1.22 | 0.60 | Measured; logs report 73 and 36 seconds | `job.sh`, `b/p0.sh`, `b/p0.py`: sealed kit, venv, trainer, neutral runtime record, NumPy/FLA overlays; writes import reports for p/t/u | Import acceptance depends on these identities and runtime; report timing is not pure. |
| Preflight PASS to first stage prep | 11.25 | 0.02 | Measured gap; hashing attribution inferred | Three full checkpoint checks through the guard, chooser and recursive preparation guard | No; checkpoint inventory, locks and I/O state. |
| Model, store and archive staging before frames | 7.60 | 7.27 | Measured envelope | `b/c.sh`: venv/closure/trainer archives, base model, small metadata, receipt/database parts, extra archives, art assets; writes node-local union tree and stamps | Payloads are content-bound; execution and stamps depend on existing pool state. |
| Frame-bundle staging and verification | 23.87 | 23.35 | Measured envelope, including extraction | `b/c.sh:184`, `b/f2.py`, `b/s.py`: frame archives, shard inventories, f3–f14 manifests/store mapping; writes RGB files, import receipts and stamps | Verified bytes depend on manifest/archive pins; extraction time and whether work runs are not pure. |
| Init mirror | 0.25 | 0.25 | Measured envelope | `b/c.sh:217`: pinned init artifact and export member hashes; writes verified mirror | Payload yes; mirror location and completion marker depend on pool state. |
| Native CPU preparation, entire mode p | **140.57** | **145.27** | Measured launch-p to exit | `b/w.py:34`, `student_pilot/s1_admission.py:132`: input config, all stream receipts and dependencies below; writes native phase journals, prepared stores/config and frame inventory | Semantic selections are input-bound. Receipt bytes also contain UUID paths, timings, resources and resolved paths. |
| Within p: start to preparation result | 70.37 | approximately 73.20 | Inferred from supplied mtimes; A's completion time is approximate | Parent metadata/confusers, pointing/VQA rebuilds, routing materialization/composition, native preparation; writes `prepare_<uuid>/` | Same qualification as mode p. |
| Within p: result to mode-p exit | 70.20 | approximately 72.07 | Inferred residual, not an isolated frame measurement | `run.prepared`, retained-row traversal, frame existence checks, SQLite inventory/ref counts and fixed SHA samples; writes `frames_<uuid>/` and `data_receipt.json` | Acceptance is input-bound; timing, SQLite artifacts and paths need not be byte-deterministic. |
| Mode-p exit to second stage | 1.43 | 0.02 | Measured gap; hashing attribution inferred | Parent resume guard performs the fourth full checkpoint check | No. |
| Second stage prep | 2.37 | 2.13 | Measured envelope | Repeats staging entrypoints; `b/s.py` checks existing packages/files/rasters and frame shards; init mirror usually present | Acceptance is content-bound; execution depends on pool state. |
| Training launch to binding mirror | 10.93 | 9.10 | Measured timestamps; overlaps the beginning of the first optimizer step | Distributed startup, preparation authentication, processor/model/init loading, wrapping, optimizer creation/restoration, run binding; wrapper copies binding | No; includes hardware/runtime work and durable state. |
| First actual optimizer step | approximately 7.22 | 7.34 | C': supplied 433 seconds. A: raw metric 440.3–440.4 seconds | Native rows/RGB/masks, model and optimizer; updates parameters/state and writes all-rank first-step admission | No; hardware and state matter. |
| End-of-job slot copy, then destination verification | unavailable | 7.78 + 7.52 | Measured: 467 + 451 seconds for 113,540,341,760 bytes | External wrapper copies checkpoint to slot A, then verifies destination | Verified content is input-bound; elapsed time and publication state are not pure. |

Patch 01's key contains the exact input config-file pin, the complete parsed config, stream receipts, all frame manifests, complete staging identity, trainer/wrapper/code identity, admission contract and relevant environment. It retains run paths deliberately; it is not a portable native preparation identity. The following audit explains coverage for this version, not a future general cache guarantee.

| Preparation input or dependency | Reader | Key coverage and admission limit |
|---|---|---|
| Original configuration and every setting, including output/preparation paths, recipe, seed, world size, frame layout/markers, pixel/sequence settings, route table, filters and optional feature blocks | `s1_admission.admit`; `carrier_c1_run.validate/prepare` | Entire parsed configuration is `preparation_config`; its launch pin is checked before forming the key. No field is excluded to improve hit rate. |
| Pose, pointing, VQA, routing and optional MDG source receipts | `s1_admission.py:181`; `carrier_c1_run.py:482` | `store_receipts=cfg.streams`, also contained in the full configuration. |
| Original SQLite rows/targets, divisions and parent-division ancestry, source memberships, pose mix sources and clip/dense plans | `carrier_c1_data.build_stream`; `c1_pose_mix.prepare`; `r1_routing.compose_native` | Their SHA pins occur in the source receipts or in config. Hashing the parent receipt binds its nested expected hashes; a changed valid child requires a changed parent/key. Prepared local copies also enter the published file inventory. |
| Pointing GT raster bytes and raster key, per-row geometry and shape/quality rules | `carrier_c1_data.py:513`; `ground_target_filter`; `build_stream` | Raster SHA/key are in pinned database rows; thresholds/filters are in config or the sealed preparation implementation. |
| REMOVE lists and defect restrictions | `row_removals.Removals`; pointing/VQA/routing preparation | Config contains each path, SHA and restriction. Path-only REMOVE lists are refused by the cache and use native preparation. |
| Dev/benchmark/pose/report exclusions, held-out QIDs/sources, scene-coverage reference and source mapping | `s1_exclusions.Exclusions/apply`; `carrier_c1_run.prepare` | Config pins/values and receipt ancestry bind every authority. Packaged reserve-scene data such as `r0_scenes.json` belongs to the trainer archive identity. |
| Routing selection/manifest, eligible packed/row sources and selection indices, source exclusions, relocation catalog, candidate manifest | `s1_routing.py:202`; `s1_pool_relocate.relocate`; `s1_pool.selected_rows` | `cfg.s1_routing` and its pinned selection/manifest closure. Catalog destinations are also included, even when bytes match. |
| Routing frame map/plan, FPS authority and frame counts; source-row scene/FPS metadata | `s1_routing.Frames`, legacy routing database traversal | Config pins bind map, plan and optional FPS authority; legacy database pins bind source metadata. |
| Base-model manifest, architecture and tokenizer/processor metadata/files | `mdg_parent.bind`; `s1_routing`; `carrier_c1_run.prepare` | Pose-source receipt points to the base manifest, whose file hashes bind metadata. `staging` also contains model/runtime archive identities. |
| Parent init artifact, full-weight manifest/index, selected embedding shard, parent heads and MDG init weights | `mdg_parent.py:23`; `carrier_c1_run.validate_init` | Config init pin plus artifact/export nested pins; current staging/init identity also enters the key. The no-MDG branch reads metadata without loading parent weight payloads. |
| MDG clips and optional clip-source manifest, scene identity map, raster/frame manifests, per-clip raster hashes, vocabulary, confusers, stem weights, exclusions and init metadata/weights | `stageb_mdg.inputs/prepare`; `mdg_inputs`; `mdg_parent.bind` | Full MDG block and transitive manifests/payload pins. Cache admission requires pinned file inputs, `{root, manifest}` directories and pinned init members. Mutable path-only variants are refused. Literal exclusion lists are already part of config. |
| Optional validation rows/slice, depth-init metadata and paired-layout partner pins | `carrier_c1_run.prepare_validation/prepare`; `carrier_c1_data.layout_inputs` | Config pins and pinned row/receipt closure. |
| R1 registry/evidence, row-source catalog and membership, mixture/sampling bindings and hand-over/persisted-file mapping when used through S1 | `r1_training`; `r1_components`; `r1_routing`; `r1_handover` | Entire optional config blocks and their pinned nested records. This does not adapt `launch_r2`'s separate host-preparation receipt. |
| All frame bytes reused by the cache, fN manifests, store mapping and archives | `b/pc.py`; native frame audit | `frame_manifests` plus entire `k/0.json` as `staging`. Publication requires every retained logical frame in the native SQLite inventory to be covered. Noncanonical/uncovered frames decline publication. Every reused RGB file is SHA256-checked. |
| Trainer source, source seal/archive, wrapper and staging implementation, venv/overlays and packaged authorities | `run.authenticate`; `b/a.py`; `b/pc.py.Context` | Preparation code identity contains commit, trainer archive, config code pin and SHA256 of every kit `b/` file. Entire deployment identity also includes venv/closure/overlay pins. |
| Preparation environment and logical-to-physical frame mapping | `b/c.sh:382`; `orchard_paths`; native admission request | Only pass-through rehearsal, CPU-count and hash-seed values enter `environment`; the removed names are not read on this preparation path. `tk_env`'s fixed mount, student ID, frame mapping, init mirror and CPU settings are bound by its wrapper hash. Contract frame roots are also keyed. |

Cache metadata uses a key and per-component SHA256 digests; full components remain in memory for key construction. Schema v2 refuses v1 cache entries. Native prepared/config files remain byte-preserved.

The native preparation path also has mutable journal state. Its `request.json` binds config/source/CPU/frame roots; `PhaseJournal` reuses completed phases, and admission refuses another request. A MISS leaves the destination intact, including a partial or foreign-config journal. Destination quarantine occurs only after a candidate copy fully verifies and immediately before its installation. A failed final rename restores the native destination. A report-write or uncertain-install error exits with a non-MISS status. Cached RGB corruption still invalidates the affected frame files/stamps through the existing staging repair path; it does not rename the native journal.

A verified synthetic copy preserves native receipt bytes. The hit report records source job, paths, key/components, producer receipt pin and verified file/frame counts. A valid destination from another preparation generation remains native because retained checkpoints may bind its UUID paths. None of these checks grants training authorization or replaces actual all-rank first-step admission.

## Launch wins, in priority order

| Patch or candidate | Evidence | Expected saving and limit |
|---|---|---|
| **03: same-allocation checkpoint verification memo** | Four `complete()` calls each hash the 113.5-GB checkpoint. C' has measured 675-s and 86-s guard envelopes. | **Estimate: about 4–5 min (inferred); up to about 9 only if the page cache does not keep the checkpoint**. The memo removes three repeated payload reads. The first check and every new allocation still hash fully. |
| **04: phase and lock timing** | Existing logs combine several guards and waits. | Estimate: zero minutes directly. Boundaries in `job.sh` and both recursive/parent `r.sh` guards separate these costs. Logging failure cannot abort a job. |
| **02: parallel frame SHA, optional** | Already-covered f2-only checks take a measured 1–19 s in C' (`last.txt:218–224,232–239`). The 23-minute cold envelope includes extraction. | No useful measured saving yet. Estimate: seconds on the supplied warm checks; storage contention can make it slower. Measure f2 alone on a warm Orchard node before enabling. Four workers by default, capped at eight, at most twice that many pending tasks, and all bytes still hash. |
| **01: prepared-input cache — OFF** | Same node-local source/destination; different-node source absent; new-run key differs. | Estimate: zero minutes or worse. Misses add full publication hashing; same-path hits add hashes to native reuse and hold the stage lock during restore. |
| Second-stage bypass, not built | Measured 142 s in C', 128 s in A. | Estimate: at most 2.13–2.37 min if a future proof removes the whole stage. Shared inputs and full staging closure still need verification. |
| First-step change, not built | A's first step takes 440.3–440.4 s vs 133.14 s at step 200. | About 300–307 s is observed excess, not a demonstrated removable cost. No GPU trace supports changing RNG, sampler, optimizer or admission behavior. |
| Slot-copy destination verification, not built | Measured 467-s write and 451-s verify for 113,540,341,760 B. | The entire verification envelope is 7.52 min; no delivered saving. The external copier is outside this source tree, and destination durability checks remain required. |

The four checkpoint checks explain the **11-minute gap** as an inference supported by code and logs. In the input tree, they run through:

1. `job.sh:16`: `g.py p` → `persistent_launch()` → `r8.main()` → `complete()`.
2. `job.sh:18`: the direct `r8.py` chooser → `complete()`.
3. `b/r.sh:40` in the **recursive** p child: `g.py p` → the same verifier.
4. `b/r.sh:40` in the **parent** u leg: `g.py u` → the same verifier.

C' spent **675 s** between preflight PASS and first stage prep, covering three checks, and **86 s** between p exit and second stage prep, covering one. A had no checkpoint and one second in each gap (`look1.out:280–281,347–348`). The node reports 1842 GiB RAM (`last.txt:163`), which makes page-cache retention plausible but does not measure cache residency. Subtracting that one-second baseline gives an inferred warm pass of about 85 s. Removing three warm passes saves about 255 s, or **about 4–5 min (inferred); up to about 9 only if the page cache does not keep the checkpoint**. The conditional upper estimate is 2 × (675 / 3) + 86 = 536 s, assuming the first pass is at least as slow as each later pass. It is not a throughput measurement.

Set `TK_LAUNCH_TIMING=1` on the **first resume** job and retain the four guard envelopes and `.checkpoint-verification/<job>.events.jsonl`. The four-process CPU regression exercises real `g.py.persistent_launch` and the direct chooser; it records `[false, true, true, true]` memo hits and refuses a subsequently corrupted payload. Its tiny fixtures do not measure checkpoint throughput.

Patch 03 binds a memo to job ID, allocation start, host, checkpoint path, binding and validator SHA. It checks marker SHA and dev/inode/size/mtime_ns/ctime_ns for the marker and every payload. New jobs, clock changes, inode replacement, restored-mtime writes, marker/binding changes, purge and malformed memo force full verification or refusal. This assumes cooperating writers keep completed checkpoints immutable; it does not authenticate against a same-user forger or prove immediate ctime updates for arbitrary mmap writes.

## Review round 2: finding -> fix -> test

| Finding | Fix | Regression evidence |
|---|---|---|
| 1 MEDIUM: unsupported adoption saving | Budget only the prepare half; explicitly retain node-local frame audit and the unmeasured complete-journal floor. | Planning/design contract fails on the reviewed text and passes now. [Native measurement procedure](MEASURE_NATIVE_REUSE.md) is delivered but **not run**: no Orchard access or production journal is authorized here. |
| 2 MEDIUM: missing Orchard data channel and identity work | Specify external GCS session issuance, candidate verification/root publication, login-node read-only cache, zero-write job staging, content-derived phase names and exact config/preparation binding; re-estimate effort. | Transport/identity design contract fails before and passes after. This checks design requirements, not a store implementation. |
| 3 LOW: unsupported memo range | Infer three warm passes from the 86-s envelope and 1-s no-checkpoint baseline; state the conditional 536-s upper estimate. | Report/note contract fails before and passes after; four-process guard/chooser regression passes. Production timing remains pending. |
| 4 LOW: real stage-lock timing untested | Execute whole real `c.sh` under `bash -euo pipefail`, with only staging dependencies stubbed. | Coverage contract fails on the reviewed tests and passes now. Prep/preflight ON emit exactly two lock lines and exit 0; OFF output equals input byte for byte. The implementation already worked; the defect was coverage. |
| 5 LOW: offset hunks leave inventory-visible backups | Apply with `--no-backup-if-mismatch` in the note, manifest and verifier. | The documented all-four application leaves `.orig` files before; the same order leaves no `.orig` or `.rej` after. Fresh standalone, recommended and combined trees pass. |
| 6 LOW: inherited `TK_PC_LOCK_HELD=1` skips lock | Export `TK_PC_LOCK_HELD="$$"`; a child accepts it only when it equals `$PPID`. Keep `flock -w 600 7 || exit 75`. | Inherited `1` bypasses contention before; t/u with unset, `1` or stale-PID markers exit 75 after. Recursive and symlink-parent runs still succeed; concurrent preparation remains serialized. |
| 7 LOW: full config copies and method-bearing refusal | Store only key/component digests; compare them on restore. Use generic optional-input errors and catch context refusal before restore starts. | Two new tests fail before and pass after: a method-bearing valid config publishes/restores without copying its fields, changed component digest refuses, and the CLI safely misses without method text or traceback. |

Exact before/after outputs and commands are indexed in [review_round2/INDEX.md](tests/review_round2/INDEX.md). The full final suites include every earlier behavior regression. Documentation and coverage contracts are explicitly distinguished from runtime failures.

## Review round 1: finding -> fix -> test

| Finding | Current invariant and rerun evidence |
|---|---|
| 1 | 01 OFF; production-path/design contract and same-path/purge tests pass. |
| 2 | MISS leaves partial/foreign journals untouched; native reuse/refusal, copy/install failure and report-error tests pass. |
| 3 | 03 first; all four real guard/chooser calls pass with one full verification. |
| 4 | Parent-bound lock marker and 600-s request; symlink, duplicate t/u and concurrent-job tests pass. |
| 5 | Whole real `c.sh` HIT/MISS/error/missing-root matrix passes. |
| 6 | Missing/unwritable timing logs cannot abort; recursive/parent guard events and exit-7 behavior pass. |
| 7 | Full launch-kit, production-import and checkpoint-buffer modules are selected; explicit environment skips appear below. |
| 8 | Unused environment names do not change the key; written cache metadata uses generic component names and digests. |


The requested review-round mappings and the harness-error disclosure are retained as audit evidence; these are deliberate exceptions to the no-archaeology writing rule.
