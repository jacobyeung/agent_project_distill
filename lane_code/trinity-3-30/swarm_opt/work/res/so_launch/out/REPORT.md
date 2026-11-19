VERDICT: PARTIAL Four tested, opt-in S1 patches are packaged; reuse across logical runs and R2 caching remain unimplemented.

The largest measured startup cost is CPU preparation: **140.57 minutes in job 172660 and 145.27 minutes in job 171377**. The four patches add a verified prepared-input cache, bounded parallel frame hashing, a checkpoint verification memo within one allocation, and launch timing. Every switch defaults OFF. No production job, GPU test, production-sized benchmark, Git command, SSH connection, or input-tree edit ran.

The cache preserves the full configuration and native receipt bytes, including logical run paths. It can restore the same logical run into another physical pool directory when its source remains accessible and its frames are already present. A new logical run deliberately misses.

The supplied A and C' traces do not contain their full cache-key inputs, so this work does **not** establish a hit between those two jobs. An existing complete native journal already reuses preparation phases without this patch; a cache hit against that journal does not save the full cold preparation time.

All durations below distinguish measurements in the supplied logs from inferences and estimates. This work measured CPU fixture execution only. It did not measure a production speedup.

Source paths below are relative to the delivered `work/tree/`; unchanged trainer/R2 files also match `in/tree/work/tree_r1/`. The raw logs are `/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/r1_ops6/work/mon/last.txt` for 172660 and `/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/o/look1.out` for 171377. [Numbered excerpts](evidence/startup_log_excerpts.txt) retain their exact lines. [Machine-readable interval arithmetic](phase_timing.json) records timestamps and evidence labels. The supplied preparation mtimes and the first persisted C' step come from `PROMPT.md:9`; the two raw log excerpts do not contain all those internal mtimes.

| Phase | 172660 minutes | 171377 minutes | Evidence | Reads and writes | Pure function of named inputs? |
|---|---:|---:|---|---|---|
| Submission to wrapper | 2.27 | unavailable | Supplied submission time and measured wrapper start | Allocation availability; starts wrapper | No; scheduler and host state. |
| Wrapper to import stage | 0.17 | 0.03 | Measured timestamps | Staging inventory and export-session setup; wrapper log | No; filesystem/runtime state. |
| Import preflight | 1.22 | 0.60 | Measured; logs report 73 and 36 seconds | `job.sh`, `b/p0.sh`, `b/p0.py`: sealed kit, venv, trainer, neutral runtime record, NumPy/FLA overlays; writes import reports for p/t/u | Import acceptance depends on these identities and runtime; report timing is not pure. |
| Preflight PASS to first stage prep | 11.25 | 0.02 | Measured gap; cause unmeasured | `job.sh`: guard, `b/r8.py` checkpoint chooser, then `b/r.sh`; possible preparation/stage locks and kit copying | No; checkpoint inventory, locks and I/O state. |
| Model, store and archive staging before frames | 7.60 | 7.27 | Measured envelope | `b/c.sh`: venv/closure/trainer archives, base model, small metadata, receipt/database parts, extra archives, art assets; writes node-local union tree and stamps | Payloads are content-bound; execution and stamps depend on existing pool state. |
| Frame-bundle staging and verification | 23.87 | 23.35 | Measured envelope, including extraction | `b/c.sh:184`, `b/f2.py`, `b/s.py`: frame archives, shard inventories, f3–f14 manifests/store mapping; writes RGB files, import receipts and stamps | Verified bytes depend on manifest/archive pins; extraction time and whether work runs are not pure. |
| Init mirror | 0.25 | 0.25 | Measured envelope | `b/c.sh:217`: pinned init artifact and export member hashes; writes verified mirror | Payload yes; mirror location and completion marker depend on pool state. |
| Native CPU preparation, entire mode p | **140.57** | **145.27** | Measured launch-p to exit | `b/w.py:34`, `student_pilot/s1_admission.py:132`: input config, all stream receipts and dependencies below; writes native phase journals, prepared stores/config and frame inventory | Semantic selections are input-bound. Receipt bytes also contain UUID paths, timings, resources and resolved paths. |
| Within p: start to preparation result | 70.37 | approximately 73.20 | Inferred from supplied mtimes; A's completion time is approximate | Parent metadata/confusers, pointing/VQA rebuilds, routing materialization/composition, native preparation; writes `prepare_<uuid>/` | Same qualification as mode p. |
| Within p: result to mode-p exit | 70.20 | approximately 72.07 | Inferred residual, not an isolated frame measurement | `run.prepared`, retained-row traversal, frame existence checks, SQLite inventory/ref counts and fixed SHA samples; writes `frames_<uuid>/` and `data_receipt.json` | Acceptance is input-bound; timing, SQLite artifacts and paths need not be byte-deterministic. |
| Mode-p exit to second stage | 1.43 | 0.02 | Measured gap; cause unmeasured | Recursive wrapper return, checks, namespace/kit setup and possible locks | No. |
| Second stage prep | 2.37 | 2.13 | Measured envelope | Repeats staging entrypoints; `b/s.py` checks existing packages/files/rasters and frame shards; init mirror usually present | Acceptance is content-bound; execution depends on pool state. |
| Training launch to binding mirror | 10.93 | 9.10 | Measured timestamps; overlaps the beginning of the first optimizer step | Distributed startup, preparation authentication, processor/model/init loading, wrapping, optimizer creation/restoration, run binding; wrapper copies binding | No; includes hardware/runtime work and durable state. |
| First actual optimizer step | approximately 7.22 | 7.34 | C': supplied 433 seconds. A: raw metric 440.3–440.4 seconds | Native rows/RGB/masks, model and optimizer; updates parameters/state and writes all-rank first-step admission | No; hardware and state matter. |
| End-of-job slot copy, then destination verification | unavailable | 7.78 + 7.52 | Measured: 467 + 451 seconds for 113,540,341,760 bytes | External wrapper copies checkpoint to slot A, then verifies destination | Verified content is input-bound; elapsed time and publication state are not pure. |

The two within-p rows partition the mode-p row; do not add them again. Binding-mirror timestamps overlap optimizer execution, so do not add the mirror interval to the full step duration. C' submission to its first persisted step is **208.73 minutes**, calculated from the supplied 22:18:18Z and 01:47:02Z timestamps. Its mode-p interval accounts for about 67% of that total.

The 23-minute frame envelope is not a measurement of SHA256 alone. Cold staging also reads/extracts archives. On a stamped bundle, `tk_stage_bundle` can print “verified” without reading the frames again. On the second staging pass, the delay before the f3 completion line can include earlier work in `s.py`; that line does not isolate f3 hashing. `Stage.run(..., frames=False)` still processes packages, files and raster directories (`b/s.py:176`), so merely selecting the existing `reuse` stage mode would not remove all repeated I/O.

The preparation dependency audit covers the S1 in-job path. Each row shows how the cache key binds the input, including transitive pins. A pin means an expected SHA256, not a promise that a mutable external file still has those bytes. Native source/training checks remain responsible for external files they subsequently read.

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
| All frame bytes reused by the cache, fN manifests, store mapping and archives | `b/pc.py:273`; native frame audit | `frame_manifests` plus entire `k/0.json` as `staging`. Publication requires every retained logical frame in the native SQLite inventory to be covered. Noncanonical/uncovered frames decline publication. Every reused RGB file is SHA256-checked. |
| Trainer source, source seal/archive, wrapper and staging implementation, venv/overlays and packaged authorities | `run.authenticate`; `b/a.py`; `b/pc.py.Context` | Preparation code identity contains commit, trainer archive, config code pin and SHA256 of every kit `b/` file. Entire deployment identity also includes venv/closure/overlay pins. |
| Preparation environment and logical-to-physical frame mapping | `b/c.sh:382`; `orchard_paths`; native admission request | Pass-through rehearsal/frame-host/local-node/CPU-count/snapshot/hash-seed values enter `environment`. `tk_env`'s fixed mount, student ID, frame mapping, init mirror and CPU settings are bound by its wrapper hash. Contract frame roots are also keyed. |

The cache key is SHA256 of canonical JSON containing schema, the exact config-file pin, store receipts, full parsed config, frame manifests, preparation code identity, complete staging identity, admission contract and the pass-through environment. Even a formatting-only config-file change misses, because native admission binds that file's SHA256.

`launch.run_directory` is the physical destination; it is intentionally outside the key. `cfg.output`, the logical admission directory and config pins remain inside it. A change in preparation code therefore misses even when the stores and user settings match. A forged same-key receipt with different code components is also refused.

On an eligible mode-p launch, the wrapper takes a per-run lock that remains held through training, stages required runtime/store metadata, and tries restore before ordinary frame-bundle staging. Restore locks the key, authenticates the index/producer receipt, hashes every prepared file and each already-staged frame, and checks complete destination files.

A missing target is copied into a private directory; the copy stream and destination are hashed before rename. Publication records only complete prepare/frames phases and their local JSON-pin closure. It verifies that all native retained frames occur in its fully hashed manifests. A receipt is fsynced before the atomic index update.

Separate runs can build concurrently; publishers/readers serialize the final key operation. Two jobs for one run serialize through the wrapper lock, including recursive preparation. Local CPU tests cover these locks; a shared index also requires its filesystem to honor flock and atomic rename.

Missing index/source, a purged pool, partial output, changed key/code or corrupted payload causes a miss and the native path runs. A malformed cache directory never supplies training authorization. A corrupt/partial target is preserved under a refusal name; corrupt frames and their relevant staging receipts/stamps are preserved under refusal names so ordinary staging can restore them.

A complete native journal from another generation is retained, because a checkpoint may pin its UUID paths. That case uses native validation rather than substituting a new preparation generation. Cache refusal due to an unpinned config variant can occur before a key/report exists; the wrapper logs a miss and runs native preparation.

Each cache hit writes `o/<job>.prepared-cache.json`: schema, job, HIT status, key and components, source job, source/target prepared paths, source/target frame paths, producer-receipt path/SHA, verified file/frame counts and verification seconds. The producer receipt contains **every prepared relative path, byte count and SHA256, plus every frame relative path, byte count and SHA256**. A BUILT report points to that receipt.

Native preparation receipts remain byte-identical and continue to report their producer's resource measurements; current reuse time belongs to the new cache report. GPU admission and each allocation's actual all-rank first optimizer step remain mandatory.

R2 uses another path: `launch_r2/staging.py` authenticates/stages a plan, and `launch_r2/host.py:251` executes packet checks, scene rebuilding, full materialization, native preparation, CPU encoding/dry-run and real-row metadata proofs. `launch_r2/entry.py:8` can reuse an explicitly pinned reviewed host receipt, but checks packet/source/config identities, reached source-statement obligations, every rank/stream and its checklist receipts.

`r1_population.bind_prepared` also binds final reader offsets and sampling identities when invoked; it is not an extra timed phase proven by the supplied S1 trace. `student_pilot/startup_receipt.py` belongs to the separate frozen-DDP startup path and is not invoked by S1's mode-p branch. These receipts cannot be replaced with an S1 journal.

R2's `r2_real_proof.prove` also reads `sealed_meta_dir/REAL_ROW_INPUTS.json` by path, so a complete R2 cache must pin that index and its dependencies. No R2 production cache patch is delivered.

The expected savings below are **estimates**, conditional on the named workload. Baseline durations are measured where stated; a maximum removable envelope is not a measured speedup. The changes overlap, so the rows must not be summed. Patch 02 affects `f2.py`, not the cache's own mandatory file/frame hashing.

| Change | Measured baseline/evidence | Expected seconds or minutes saved | Safety and practical limit |
|---|---|---|---|
| 01: prepared-input cache | Cold native p is 140.57–145.27 min | **Estimated 120 min planning allowance** for restoring an absent same-logical-run target from an intact producer with warm local frames. Formula: cold p minus source hashing, optional verified copying and complete RGB hashing; 120 min assumes about 20–25 min for those checks. Their production cost is unmeasured. **Estimated 0 min** of rebuild saving for an already complete native journal, a key miss or a new logical run; overhead can make net saving negative. The actual A-to-C' key was not replayed. | Every reused file is SHA256-checked; source remains required. Cold frames rebuild. The 20–25 min verification allowance is a planning assumption, not a transfer benchmark or lower bound. First publication adds full hashing overhead. |
| 02: parallel frame SHA | Cold staging/frame envelope is 23.35–23.87 min; hashing is not isolated | **Estimated 0–17.5 min** for a comparable 23.35-min envelope with four workers. 17.5 min is the ideal 75% ceiling only if all the time were parallelizable hashing; extraction and saturated storage lower it. Negative net saving is possible under contention. | Default serial function remains intact. Enabled mode hashes every byte with at most eight workers, default four; it bounds pending tasks and preserves path/manifest/digest rejection. Do not enable on Trinity NFS data. |
| 03: checkpoint verification memo | Chooser hashes all payloads of each complete checkpoint; the external slot's 451-s verify is a different operation | **Estimated 0 s** on the supplied job.sh's single chooser call. For an actual duplicate same-allocation call, saving equals one full payload verification minus metadata checks; using 451 s only as a rough transfer-rate proxy gives **approximately 7.5 min per 113.5-GB repeat**, not a measurement of this chooser. | First verification and every new allocation still hash payloads. Job/start/host/path/binding/validator and device/inode/size/mtime/ctime bind the memo. Persistent slot checks remain unchanged. |
| 04: phase/lock timing | C' quiet gap is 675 s; A's is 1 s | **Estimated 0 s directly**; exposes whether preflight, launch guard, chooser or stage-lock wait owns the delay. | Logs to the existing steps file; mode chooser stdout and failure status are preserved. A 113.5-GB checkpoint read is a plausible explanation for the gap, not a trace-proven cause. |
| Second staging bypass, not built | 142 s in C', 128 s in A | **Estimated 0 s delivered; at most 2.13–2.37 min** if a later proof removes the entire envelope. | The existing reuse stage still rechecks files/rasters. Skipping the stage wholesale would require a receipt for the full staged closure and protection from another kit replacing shared inputs. |
| First-step warmup change, not built | A first step 440.3–440.4 s vs step 200 at 133.14 s; data 34.5–34.7 s vs 32.20 s | **Estimated 0 s delivered; approximately 300–307 s is the observed excess**, not proven removable time. | Warmup must preserve RNG, sampler order, optimizer state and actual first-step admission. No full-model GPU evidence authorizes changing this path. |
| Slot-copy verification change, not built | Write 467 s, verify 451 s for 113,540,341,760 B | **Estimated 0 s delivered; 7.52 min is the entire measured verification envelope**. | The copying wrapper is outside the input tree. A source/copy-stream hash does not verify durable destination bytes, so removing the destination read would weaken the supplied persistence guarantee. |

For the first-step hypothesis, the installed torch 2.11 implementation provides two mechanisms, not an attribution of the observed 300 seconds. `torch/optim/adamw.py:21` inherits Adam; `torch/optim/adam.py:162` initializes missing state, including moment tensors at lines 178 and 182, from `step` at line 238. FSDP's `torch/distributed/fsdp/_runtime_utils.py:112` initializes lazily and its root pre-forward invokes that path at line 521.

These files live under `/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/`. See the official [AdamW documentation](https://docs.pytorch.org/docs/2.11/generated/torch.optim.AdamW.html) and [FSDP documentation](https://docs.pytorch.org/docs/2.11/fsdp.html). The A data-time difference is only about 2.4 seconds, so the available metrics do not support blaming the full excess on row loading. A GPU phase trace is still needed.

Tests set `torch.set_num_threads(8)` before test tensor work. The installed `torch/_torch_docs.py:9817` documents its intra-op CPU scope and initialization requirement; the official [thread-setting documentation](https://docs.pytorch.org/docs/2.11/generated/torch.set_num_threads.html) agrees. The runner also hides CUDA and caps OMP/MKL/OpenBLAS. These changes rely on file hashes, locks and the existing training contract; they do not change a torch optimizer, model or distributed algorithm.

The main failure modes and their signals are explicit:

- **Stale or purged cached output:** file/SHA/closure failure produces MISS and native work; inspect the new job's cache JSON and steps log. A source purge can race with copying; the verified copy must finish before the target is renamed.
- **A preparation input omitted from the key:** the full config, pinned dependency closure, wrapper/trainer/runtime identities and strict MDG/REMOVE admission reduce this risk. A future reader that opens an unpinned path or reads a new environment value still requires an audit. Compare cold/hit prepared rows, source seals and first-step results during deployment; this delivery does not claim a general cache for arbitrary future producer code.
- **Existing preparation/checkpoint generation:** a complete native journal is retained. If a corrupt or missing generation cannot match a retained checkpoint, resume can still refuse; the cache does not authorize a cold restart over it.
- **Concurrent mutation:** prepared source and completed checkpoints must remain immutable. Hashing catches observed changes, and wrapper/key locks cover cooperating jobs. These are private operator-owned caches, not signed receipts from an untrusted writer. A privileged writer or unsupported concurrent mutation after verification is outside that model.
- **Pool growth:** incomplete copies, refused artifacts and historical receipts are preserved. The cache performs no deletion or automatic garbage collection; monitor the pool's capacity and let its owner manage retention.
- **Performance regression:** initial publication hashes full outputs/RGB, warm-journal hits can be slower than native reuse, and frame hashing can saturate storage. Use verification seconds, counts and phase timestamps before enabling broadly.

Five failures in the native `test_s1_in_job_gate` fixture reproduce on the untouched input: four failed assertions and one error, all caused by its MDG configuration lacking a corresponding MDG stream. Its success fixture also omits VQA, which the current gate expects. The patches do not edit that module or the training gate.

The normal selected regression run excludes this stale module and covers 51 tests; the optional expanded 57-test run records the same five failures on the input and patched tree. A new cache-specific fixture with consistent native bindings successfully traverses the real training gate before and after restore. This is CPU fixture evidence, not a full production preparation rehearsal.

The saved build decisions remain in `work/STATUS.md`: full config/logical-path identity, byte-preserved native provenance, SHA256 for all prepared/frame reuse and S1-only integration. A failing real-`tk_env` test justified correcting the environment key so fixed wrapper values do not change its restore/publication identity. A failing MDG path-admission test justified refusing unpinned MDG variants. A failing formatting-only config test justified adding its exact file pin.

Exact before/after evidence lives in `out/tests/07_environment_key_*`, `out/tests/08_mdg_key_*` and `out/tests/16_raw_config_pin_*`. This decision evidence is retained to satisfy the requested audit of test-justified changes; no saved decision to preserve configuration/provenance was relaxed.

Remaining work is reuse across logical runs with a native provenance design, an R2 host-receipt adapter with a full dependency audit, production-scale timing and the unbuilt launch changes listed above. The stale native gate fixture also remains unchanged. [The hand-over note](NOTE_FOR_TREE_REBUILD.md) gives the apply order and deployment checks after N's first proof.

Final patch verification completed before the 08:45Z deadline. Report assembled at 2026-11-19T07:31:07Z.

Each patch applied independently to a fresh build-20 copy, and the complete set applied in numeric order with `patch --batch --fuzz=0 -p1`. No fuzz or offset was needed. The packaging check confirms that only the eleven declared production/test paths differ from the input tree. The manifest contains exact patch bytes, SHA256, base-file hashes and the application method.

| Patch | Bytes | Default-OFF switch | Independent test results and exact log |
|---|---:|---|---|
| [01_prepared_input_cache.diff](patches/01_prepared_input_cache.diff) | 58222 | `TK_PREPARED_INPUT_CACHE` | 24 + 6 passed; [exact output](tests/20261119T072417Z/01_prepared_input_cache.diff.txt) |
| [02_parallel_frame_sha.diff](patches/02_parallel_frame_sha.diff) | 6324 | `TK_PARALLEL_FRAME_SHA` | 7 passed; [exact output](tests/20261119T072417Z/02_parallel_frame_sha.diff.txt) |
| [03_checkpoint_verify_memo.diff](patches/03_checkpoint_verify_memo.diff) | 10812 | `TK_CHECKPOINT_VERIFY_MEMO` | 9 passed; [exact output](tests/20261119T072417Z/03_checkpoint_verify_memo.diff.txt) |
| [04_launch_phase_timing.diff](patches/04_launch_phase_timing.diff) | 5015 | `TK_LAUNCH_TIMING` | 3 passed; [exact output](tests/20261119T072417Z/04_launch_phase_timing.diff.txt) |

The final combined run passes **49 new tests and 51 selected native regressions (100 tests)**. It includes key-component misses, exact config-file pin changes, same-key/different-code refusal, corruption, missing/partial/purged sources, concurrent publishers/consumers, real wrapper serialization, native training-gate acceptance and provenance preservation. The default-OFF paths, frame rejection cases, checkpoint invalidation and timing exit/stdout behavior are covered.

The actual outer verification command was:

```bash
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/verify_delivery.py
```

The runner sets `TEST_TMP_ROOT`, `TMPDIR` and `LANE_TEST_OUTPUT` to its new owned scratch directory. Child commands inherit nice level 10 and the CPU/CUDA limits. To run the included patch tests on a rebuilt source tree, use the same environment with each command below, after setting those three fixture paths:

| Test command from the source root | Exact independent result |
|---|---|
| `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B tests/test_prepared_input_cache.py -v` | `Ran 24 tests in 0.676s`; `OK` |
| `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B tests/test_prepared_cache_wrapper.py -v` | `Ran 6 tests in 1.508s`; `OK` |
| `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B tests/test_parallel_frame_sha.py -v` | `Ran 7 tests in 0.042s`; `OK` |
| `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B tests/test_checkpoint_verify_memo.py -v` | `Ran 9 tests in 0.037s`; `OK` |
| `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B tests/test_launch_phase_timing.py -v` | `Ran 3 tests in 0.248s`; `OK` |

The following block is the **unedited combined application and test output**, including exact commands and exit codes. The standalone logs linked above retain the independent applications and their own exact timings.

```text
$ date -u
Thu Nov 19 07:24:27 UTC 2026
EXIT: 0
$ patch --batch --fuzz=0 -p1 -i /scratch/jjyeung/orch_n30/so_launch/out/patches/01_prepared_input_cache.diff
patching file launch_s1/b/c.sh
patching file launch_s1/b/r.sh
patching file launch_s1/b/pc.py
patching file tests/test_prepared_input_cache.py
patching file tests/test_prepared_cache_wrapper.py
EXIT: 0
$ patch --batch --fuzz=0 -p1 -i /scratch/jjyeung/orch_n30/so_launch/out/patches/02_parallel_frame_sha.diff
patching file launch_s1/b/f2.py
patching file tests/test_parallel_frame_sha.py
EXIT: 0
$ patch --batch --fuzz=0 -p1 -i /scratch/jjyeung/orch_n30/so_launch/out/patches/03_checkpoint_verify_memo.diff
patching file launch_s1/b/r8.py
patching file tests/test_checkpoint_verify_memo.py
EXIT: 0
$ patch --batch --fuzz=0 -p1 -i /scratch/jjyeung/orch_n30/so_launch/out/patches/04_launch_phase_timing.diff
patching file launch_s1/job.sh
patching file launch_s1/b/c.sh
patching file tests/test_launch_phase_timing.py
EXIT: 0
$ /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_launch/work/verify_20261119T072417Z/combined/tests/test_prepared_input_cache.py -v
test_an_existing_complete_journal_survives_a_cache_miss (__main__.PreparedCacheTests.test_an_existing_complete_journal_survives_a_cache_miss) ... ok
test_another_complete_generation_does_not_replace_native_journal (__main__.PreparedCacheTests.test_another_complete_generation_does_not_replace_native_journal) ... ok
test_cold_rebuild_after_miss_can_publish_and_hit (__main__.PreparedCacheTests.test_cold_rebuild_after_miss_can_publish_and_hit) ... ok
test_concurrent_consumers_keep_complete_target_and_training_evidence (__main__.PreparedCacheTests.test_concurrent_consumers_keep_complete_target_and_training_evidence) ... ok
test_corrupt_or_missing_frames_force_ordinary_restaging (__main__.PreparedCacheTests.test_corrupt_or_missing_frames_force_ordinary_restaging) ... ok
test_corrupt_prepared_file_misses_and_quarantines_target (__main__.PreparedCacheTests.test_corrupt_prepared_file_misses_and_quarantines_target) ... ok
test_default_off_cli_has_no_side_effects (__main__.PreparedCacheTests.test_default_off_cli_has_no_side_effects) ... ok
test_each_key_component_changed_alone_misses (__main__.PreparedCacheTests.test_each_key_component_changed_alone_misses) ... ok
test_hit_verifies_and_preserves_native_journal (__main__.PreparedCacheTests.test_hit_verifies_and_preserves_native_journal) ... ok
test_new_logical_run_cannot_reuse_a_native_configuration_seal (__main__.PreparedCacheTests.test_new_logical_run_cannot_reuse_a_native_configuration_seal) ... ok
test_partial_index_is_a_miss (__main__.PreparedCacheTests.test_partial_index_is_a_miss) ... ok
test_partial_prepared_directory_is_never_published (__main__.PreparedCacheTests.test_partial_prepared_directory_is_never_published) ... ok
test_partial_published_directory_misses (__main__.PreparedCacheTests.test_partial_published_directory_misses) ... ok
test_purged_pool_source_misses (__main__.PreparedCacheTests.test_purged_pool_source_misses) ... ok
test_real_config_init_and_code_changes_miss (__main__.PreparedCacheTests.test_real_config_init_and_code_changes_miss) ... ok
test_real_wrapper_environment_has_same_restore_and_seal_key (__main__.PreparedCacheTests.test_real_wrapper_environment_has_same_restore_and_seal_key) ... ok
test_restored_receipts_pass_the_native_training_gate_without_rebinding (__main__.PreparedCacheTests.test_restored_receipts_pass_the_native_training_gate_without_rebinding) ... ok
test_same_key_different_code_in_receipt_is_refused (__main__.PreparedCacheTests.test_same_key_different_code_in_receipt_is_refused) ... ok
test_same_parsed_config_with_different_file_pin_misses (__main__.PreparedCacheTests.test_same_parsed_config_with_different_file_pin_misses) ... ok
test_symlink_and_path_traversal_refused (__main__.PreparedCacheTests.test_symlink_and_path_traversal_refused) ... ok
test_two_concurrent_publishers_commit_complete_receipts (__main__.PreparedCacheTests.test_two_concurrent_publishers_commit_complete_receipts) ... ok
test_uncovered_retained_frame_refuses_publication (__main__.PreparedCacheTests.test_uncovered_retained_frame_refuses_publication) ... ok
test_unpinned_mdg_paths_cannot_form_a_cache_key (__main__.PreparedCacheTests.test_unpinned_mdg_paths_cannot_form_a_cache_key) ... ok
test_unpinned_remove_path_cannot_form_a_cache_key (__main__.PreparedCacheTests.test_unpinned_remove_path_cannot_form_a_cache_key) ... ok

----------------------------------------------------------------------
Ran 24 tests in 0.647s

OK
EXIT: 0
$ /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_launch/work/verify_20261119T072417Z/combined/tests/test_prepared_cache_wrapper.py -v
test_default_off_uses_native_path_and_writes_no_cache (__main__.PreparedWrapperTests.test_default_off_uses_native_path_and_writes_no_cache) ... ok
test_failed_native_preparation_is_not_published (__main__.PreparedWrapperTests.test_failed_native_preparation_is_not_published) ... ok
test_hit_reuses_verified_phases_without_launching_native_builder (__main__.PreparedWrapperTests.test_hit_reuses_verified_phases_without_launching_native_builder) ... ok
test_miss_runs_native_builder_then_publishes (__main__.PreparedWrapperTests.test_miss_runs_native_builder_then_publishes) ... ok
test_recursive_resume_inherits_lock_and_still_launches_training (__main__.PreparedWrapperTests.test_recursive_resume_inherits_lock_and_still_launches_training) ... ok
test_two_jobs_for_one_run_serialize_native_preparation (__main__.PreparedWrapperTests.test_two_jobs_for_one_run_serialize_native_preparation) ... ok

----------------------------------------------------------------------
Ran 6 tests in 1.503s

OK
EXIT: 0
$ /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_launch/work/verify_20261119T072417Z/combined/tests/test_parallel_frame_sha.py -v
test_default_does_not_construct_a_thread_pool (__main__.FrameHashTests.test_default_does_not_construct_a_thread_pool) ... ok
test_duplicate_and_wrong_path_refuse_both_modes (__main__.FrameHashTests.test_duplicate_and_wrong_path_refuse_both_modes) ... ok
test_late_corrupt_file_refuses_both_modes (__main__.FrameHashTests.test_late_corrupt_file_refuses_both_modes) ... ok
test_manifest_digest_refuses (__main__.FrameHashTests.test_manifest_digest_refuses) ... ok
test_missing_and_symlinked_files_refuse (__main__.FrameHashTests.test_missing_and_symlinked_files_refuse) ... ok
test_parallel_and_default_counts_match (__main__.FrameHashTests.test_parallel_and_default_counts_match) ... ok
test_worker_cap (__main__.FrameHashTests.test_worker_cap) ... ok

----------------------------------------------------------------------
Ran 7 tests in 0.041s

OK
EXIT: 0
$ /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_launch/work/verify_20261119T072417Z/combined/tests/test_checkpoint_verify_memo.py -v
test_another_job_or_allocation_clock_rehashes (__main__.CheckpointMemoTests.test_another_job_or_allocation_clock_rehashes) ... ok
test_corrupt_memo_falls_back_to_full_hash (__main__.CheckpointMemoTests.test_corrupt_memo_falls_back_to_full_hash) ... ok
test_default_off_rehashes_and_writes_no_memo (__main__.CheckpointMemoTests.test_default_off_rehashes_and_writes_no_memo) ... ok
test_inode_replacement_even_with_same_size_and_mtime_refuses (__main__.CheckpointMemoTests.test_inode_replacement_even_with_same_size_and_mtime_refuses) ... ok
test_marker_or_binding_change_cannot_hit (__main__.CheckpointMemoTests.test_marker_or_binding_change_cannot_hit) ... ok
test_missing_allocation_identity_disables_memo (__main__.CheckpointMemoTests.test_missing_allocation_identity_disables_memo) ... ok
test_only_first_same_job_check_reads_payloads (__main__.CheckpointMemoTests.test_only_first_same_job_check_reads_payloads) ... ok
test_purged_payload_refuses_resume (__main__.CheckpointMemoTests.test_purged_payload_refuses_resume) ... ok
test_same_size_corruption_with_restored_mtime_refuses (__main__.CheckpointMemoTests.test_same_size_corruption_with_restored_mtime_refuses) ... ok

----------------------------------------------------------------------
Ran 9 tests in 0.037s

OK
EXIT: 0
$ /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_launch/work/verify_20261119T072417Z/combined/tests/test_launch_phase_timing.py -v
test_default_path_runs_same_commands_and_produces_no_timing (__main__.LaunchTimingTests.test_default_path_runs_same_commands_and_produces_no_timing) ... ok
test_enabled_logs_boundaries_without_polluting_mode_stdout (__main__.LaunchTimingTests.test_enabled_logs_boundaries_without_polluting_mode_stdout) ... ok
test_failed_guard_preserves_exit_status_and_stops_dispatch (__main__.LaunchTimingTests.test_failed_guard_preserves_exit_status_and_stops_dispatch) ... ok

----------------------------------------------------------------------
Ran 3 tests in 0.252s

OK
EXIT: 0
$ /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_launch/work/run_native_regression.py /scratch/jjyeung/orch_n30/so_launch/work/verify_20261119T072417Z/combined
test_all_retained_frames_exist_and_fixed_sample_is_authenticated (tests.test_s1_admission.OrchardAdmissionTests.test_all_retained_frames_exist_and_fixed_sample_is_authenticated) ... ok
test_changed_sample_and_conflicting_frame_hashes_fail_closed (tests.test_s1_admission.OrchardAdmissionTests.test_changed_sample_and_conflicting_frame_hashes_fail_closed) ... ok
test_legacy_dataset_aliases_use_the_label_list_identity (tests.test_s1_admission.OrchardAdmissionTests.test_legacy_dataset_aliases_use_the_label_list_identity) ... ok
test_missing_retained_frame_fails_closed (tests.test_s1_admission.OrchardAdmissionTests.test_missing_retained_frame_fails_closed) ... ok
test_native_sql_stream_rebuild_iterator_is_read_only (tests.test_s1_admission.OrchardAdmissionTests.test_native_sql_stream_rebuild_iterator_is_read_only) ... ok
test_removed_rows_do_not_enter_the_rgb_denominator (tests.test_s1_admission.OrchardAdmissionTests.test_removed_rows_do_not_enter_the_rgb_denominator) ... ok
test_changed_rank_payload_is_rejected (tests.test_s1_first_batch_progress.FirstBatchProgressTests.test_changed_rank_payload_is_rejected) ... ok
test_completed_preparation_phase_is_not_rebuilt (tests.test_s1_first_batch_progress.FirstBatchProgressTests.test_completed_preparation_phase_is_not_rebuilt) ... ok
test_completed_rank_is_authenticated_and_reused (tests.test_s1_first_batch_progress.FirstBatchProgressTests.test_completed_rank_is_authenticated_and_reused) ... ok
test_failed_phase_never_publishes_completion (tests.test_s1_first_batch_progress.FirstBatchProgressTests.test_failed_phase_never_publishes_completion) ... ok
test_foreign_binding_cannot_reuse_a_rank (tests.test_s1_first_batch_progress.FirstBatchProgressTests.test_foreign_binding_cannot_reuse_a_rank) ... ok
test_partial_duplicate_nonfinite_and_wrong_row_do_not_complete (tests.test_s1_first_batch_progress.FirstBatchProgressTests.test_partial_duplicate_nonfinite_and_wrong_row_do_not_complete) ... ok
test_destination_traversal_and_symlinks_are_rejected (tests.test_s1_staging.PinnedStagingTests.test_destination_traversal_and_symlinks_are_rejected) ... ok
test_files_and_each_raster_are_bound_without_deleting_sources (tests.test_s1_staging.PinnedStagingTests.test_files_and_each_raster_are_bound_without_deleting_sources) ... ok
test_member_hash_is_checked_during_streaming (tests.test_s1_staging.PinnedStagingTests.test_member_hash_is_checked_during_streaming) ... ok
test_parent_traversal_and_links_are_rejected (tests.test_s1_staging.PinnedStagingTests.test_parent_traversal_and_links_are_rejected) ... ok
test_payload_package_verifies_members_and_retains_duplicate_role_pins (tests.test_s1_staging.PinnedStagingTests.test_payload_package_verifies_members_and_retains_duplicate_role_pins) ... ok
test_streamed_archive_and_cached_sample_are_verified (tests.test_s1_staging.PinnedStagingTests.test_streamed_archive_and_cached_sample_are_verified) ... ok
test_symbolic_link_member_is_rejected (tests.test_s1_staging.PinnedStagingTests.test_symbolic_link_member_is_rejected) ... ok
test_wrong_full_archive_digest_never_creates_completion_marker (tests.test_s1_staging.PinnedStagingTests.test_wrong_full_archive_digest_never_creates_completion_marker) ... ok
test_export_retains_training_and_export_configuration_seals (tests.test_s1_source_seal.SourceSealTests.test_export_retains_training_and_export_configuration_seals) ... ok
test_links_are_not_source_files (tests.test_s1_source_seal.SourceSealTests.test_links_are_not_source_files) ... ok
test_mutated_source_and_archive_are_rejected (tests.test_s1_source_seal.SourceSealTests.test_mutated_source_and_archive_are_rejected) ... ok
test_rehashed_foreign_archive_does_not_prove_the_tree (tests.test_s1_source_seal.SourceSealTests.test_rehashed_foreign_archive_does_not_prove_the_tree) ... ok
test_seal_binds_tree_archive_and_configuration_without_a_git_sha (tests.test_s1_source_seal.SourceSealTests.test_seal_binds_tree_archive_and_configuration_without_a_git_sha) ... ok
test_directory_manifest_cannot_escape_its_root (tests.test_s1_mdg_inputs.MDGInputTests.test_directory_manifest_cannot_escape_its_root) ... ok
test_frame_manifest_uses_resized_not_original_hashes (tests.test_s1_mdg_inputs.MDGInputTests.test_frame_manifest_uses_resized_not_original_hashes) ... ok
test_initialization_binds_both_metadata_and_weight_bytes (tests.test_s1_mdg_inputs.MDGInputTests.test_initialization_binds_both_metadata_and_weight_bytes) ... ok
test_resized_frame_root_does_not_change_legacy_rgb_mapping (tests.test_s1_mdg_inputs.MDGInputTests.test_resized_frame_root_does_not_change_legacy_rgb_mapping) ... ok
test_two_clip_sources_are_pinned_without_concatenation (tests.test_s1_mdg_inputs.MDGInputTests.test_two_clip_sources_are_pinned_without_concatenation) ... ok
test_each_rank_must_forward_every_stream_without_substitution (tests.test_s1_first_step.NativeFirstStepTests.test_each_rank_must_forward_every_stream_without_substitution) ... ok
test_failed_first_step_cannot_checkpoint_or_export (tests.test_s1_first_step.NativeFirstStepTests.test_failed_first_step_cannot_checkpoint_or_export) ... ok
test_microstep_multiplicity_must_match_the_recipe (tests.test_s1_first_step.NativeFirstStepTests.test_microstep_multiplicity_must_match_the_recipe) ... ok
test_missing_rank_and_nonfinite_values_are_rejected (tests.test_s1_first_step.NativeFirstStepTests.test_missing_rank_and_nonfinite_values_are_rejected) ... ok
test_resume_allocation_checks_its_first_actual_optimizer_step (tests.test_s1_first_step.NativeFirstStepTests.test_resume_allocation_checks_its_first_actual_optimizer_step) ... ok
test_changed_binding_mirror_refuses (tests.test_s1_persistent_resume.PersistentResumeTests.test_changed_binding_mirror_refuses) ... ok
test_corrupt_restored_payload_refuses (tests.test_s1_persistent_resume.PersistentResumeTests.test_corrupt_restored_payload_refuses) ... ok
test_first_job_claims_marker_and_may_start (tests.test_s1_persistent_resume.PersistentResumeTests.test_first_job_claims_marker_and_may_start) ... ok
test_foreign_run_marker_refuses (tests.test_s1_persistent_resume.PersistentResumeTests.test_foreign_run_marker_refuses) ... ok
test_missing_slurm_identity_refuses_persistent_mode (tests.test_s1_persistent_resume.PersistentResumeTests.test_missing_slurm_identity_refuses_persistent_mode) ... ok
test_new_job_with_prior_marker_refuses_cold_start (tests.test_s1_persistent_resume.PersistentResumeTests.test_new_job_with_prior_marker_refuses_cold_start) ... ok
test_restored_native_state_and_verified_slot_resume (tests.test_s1_persistent_resume.PersistentResumeTests.test_restored_native_state_and_verified_slot_resume) ... ok
test_stale_local_checkpoint_refuses (tests.test_s1_persistent_resume.PersistentResumeTests.test_stale_local_checkpoint_refuses) ... ok
test_unmarked_persistent_binding_refuses_a_new_first_leg (tests.test_s1_persistent_resume.PersistentResumeTests.test_unmarked_persistent_binding_refuses_a_new_first_leg) ... ok
test_unverified_slot_does_not_admit_a_later_job (tests.test_s1_persistent_resume.PersistentResumeTests.test_unverified_slot_does_not_admit_a_later_job) ... ok
test_valid_but_foreign_binding_mirror_refuses (tests.test_s1_persistent_resume.PersistentResumeTests.test_valid_but_foreign_binding_mirror_refuses) ... ok
test_verified_slot_without_restored_state_refuses (tests.test_s1_persistent_resume.PersistentResumeTests.test_verified_slot_without_restored_state_refuses) ... ok
test_new_run_chooses_training (tests.test_s1_launch_kit.LaunchKitTests.test_new_run_chooses_training) ... ok
test_job_entry_preserves_wrapper_allocation_clock (tests.test_s1_launch_kit.LaunchKitTests.test_job_entry_preserves_wrapper_allocation_clock) ... ok
test_parseable_but_incomplete_checkpoint_never_restarts_cold (tests.test_s1_launch_kit.LaunchKitTests.test_parseable_but_incomplete_checkpoint_never_restarts_cold) ... ok
test_resume_requires_matching_binding_and_complete_payload_inventory (tests.test_s1_launch_kit.LaunchKitTests.test_resume_requires_matching_binding_and_complete_payload_inventory) ... ok

----------------------------------------------------------------------
Ran 51 tests in 0.977s

OK
EXIT: 0
$ date -u
Thu Nov 19 07:24:38 UTC 2026
EXIT: 0
```

The optional expanded check retains the input fixture failure rather than modifying its assertions. Its command and complete output are in [the input log](tests/20261119T072417Z/known_native_failures_input.txt) and [the patched log](tests/20261119T072417Z/known_native_failures_patched.txt). Both runs contain 57 tests and exit 1, with the same four failures and one error. The comparison command was:

```bash
nice -n 10 env CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/verify_known_failures.py /scratch/jjyeung/orch_n30/so_launch/out/tests/20261119T072417Z
```

Its exact output is:

```text
PASS: the same five native admission-fixture failures reproduce on input and patched trees
ERROR: test_reviewed_derivation_loads_from_a_restaged_host_directory (tests.test_s1_in_job_gate.InJobGateTests.test_reviewed_derivation_loads_from_a_restaged_host_directory)
FAIL: test_changed_proof_payload_and_foreign_parent_are_rejected (tests.test_s1_in_job_gate.InJobGateTests.test_changed_proof_payload_and_foreign_parent_are_rejected)
FAIL: test_fixture_evidence_does_not_authorize_real_training (tests.test_s1_in_job_gate.InJobGateTests.test_fixture_evidence_does_not_authorize_real_training)
FAIL: test_scene_coverage_cannot_be_omitted_or_rebound (tests.test_s1_in_job_gate.InJobGateTests.test_scene_coverage_cannot_be_omitted_or_rebound)
FAIL: test_self_consistent_unreviewed_configuration_change_is_rejected (tests.test_s1_in_job_gate.InJobGateTests.test_self_consistent_unreviewed_configuration_change_is_rejected)
```
