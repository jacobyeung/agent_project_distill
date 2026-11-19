VERDICT: DONE The four round-10 fixes pass CPU verification; adoption still requires the pinned runtime and a zero-difference step-400 H100 gate.

| Quantity | Value | Evidence type |
|---|---:|---|
| Workspace tests | 147 passed | Measured; RESULTS.json and exact outputs below |
| Fresh-application tests | 66 passed | Measured; MANIFEST applied_cpu_suites |
| Round-10 regressions | 7 fail before; 7 pass after | Measured; round10_before.txt and round10.txt |
| Retained fail-before controls | 14 rerun | Measured; transcripts below |
| Original A4 reader base | 927 files unchanged | Measured; full inventory/hash comparison |
| Additive reader files | 42 | Measured; patches 01–03 |
| Prepared-path aliases | 7 | Read from the shared host table |
| Fixture sealed paths | 12 resolved | Measured; ten prepared-settings paths plus two gate receipt paths |
| Extraction fixture | 10,240 bytes; one open, one full read | Measured; no production archive throughput claim |
| Runtime archive parts | 13; 10,497,433,600 bytes | Read from A4 receipt; bytes not supplied |
| bwrap | 72,160 bytes | Read from A4 receipt; binary not supplied |
| Prepared asset archive | About 33 GB | Estimate from declared expanded inputs and tar headers |
| Largest suite child RSS | Unavailable | Full-suite runner stopped at final size assertion before recording RSS |
| Largest fresh-application child RSS | 298,569,728 bytes | Measured process resource counter |
| Guard benchmark peak RSS | 1,326,764,032 bytes | Measured process resource counter |
| Workspace at report generation | 2,915,860,288 unique-inode bytes | Measured; below 3,000,000,000 |

OFF reader source and output bytes remain unchanged. ON CPU fixtures preserve exact answers and traces. H100 equality, throughput and memory remain unmeasured. Zero answer/trace byte differences remain mandatory; score equality cannot authorize adoption.

The task started at **19:47:20 UTC on 2026-11-19** and is due at **20:47:20 UTC**. This report was generated at Thu Nov 19 20:07:51 UTC 2026. [out_round10](../out_round10/) preserves the reviewed delivery. Computation used nice 10, hidden CUDA and at most eight torch/OMP/MKL/OpenBLAS threads. No Git, SSH, SCP, Slurm operation, GPU, paid API, input-tree edit or file-deletion command ran. Network reads were limited to official library documentation.

Storage limitation: one sample during verification measured **3,041,057,187 bytes**, above the requested 3 GB cap. Completed immutable fixture files were shared only after byte-for-byte comparison; no paths were removed. [STORAGE10_FIXTURES.json](checks/STORAGE10_FIXTURES.json) and [STORAGE10_EXTRA.json](checks/STORAGE10_EXTRA.json) record the bounded sharing passes. All tests passed before the runner failed its final size assertion; finish_checks10.py verifies their outputs and the restored storage cap. Aggregate RSS for that runner is unavailable; fresh-application RSS is recorded separately. The final size is reported above. The fixture harness also shares known archive members after their real writes close.

## Review round 10: finding -> fix -> test

| Finding | Fix | Regression |
|---|---|---|
| MEDIUM 1: boot.py refuses -c | Ship `u0/u5.py`, pin it in MANIFEST/validate_kit and the built package's gate hashes, and invoke `[inputs['python'], '-B', '-I', kit+'/u0/u5.py', config]` inside A4's namespace. | The exact 443-byte boot rejects -c and runs the shipped preflight plus parent. Only the wrapper double changes its interpreter and physical boot pathname; boot.py stays byte-identical. CPU doubles supply version/CUDA imports. Public stage-kit preserves preflight bytes; mutation refuses. |
| MEDIUM 2: sealed paths have no aliases | One `host.ALIASES` table defines seven relative symlinks under logical/d. README generates PRIVATE_ALIASES from it, and host.stage creates them. The gate recursively checks every absolute sealed-settings path exists before the self-test. | A fixture executes authenticated host staging, seals settings, and resolves 12 absolute paths, including the ten prepared-settings paths and two gate receipt paths. Missing nested paths refuse before the self-test. |
| LOW 3: nested bwrap | When running under U0_ROOT, workers call the input wrapper directly, retaining J.environment. | Direct argv, HOME and OPENBLAS=1 assertions pass. Parent and preflight still enter J.namespace. |
| INFO: 4.tar read three times | Hash/count the one stream sent to tar; check its exit code and expected size/hash before aliases or successful staging records are published. README performs only metadata checks before extraction. | A 10,240-byte tar fixture is opened once and read once. A wrong hash refuses. README has no asset hash preread. |


## Wrapper bytes and pin comparison

| Supplied A4 member | Measured bytes | Measured SHA256 |
|---|---:|---|
| `v/boot.py` | 443 | `bce29ff7a0fe85d34d31a419d6ad1d0f9f333ef97b7a7fc2ce5ddcfb7da4536f` |
| `v/py` | 160 | `6fcf54ddf27fe5e2f755b8c3bacef8322486b5b292625847baa77d4fcc632416` |

Both hashes match the coordinator's supplied prefixes, and both sizes match the A4 archive listing. The preserved MANIFEST's `a4_member_pins` covers six package/operator files; it contains no v/py or v/boot.py SHA256. Therefore an independent full-hash match against prior wrapper-member pins cannot be claimed. [A4_WRAPPER_PINS10.json](checks/A4_WRAPPER_PINS10.json) records that distinction, the exact supplied bytes' hashes and the pinned a4.tar receipt. The regenerated MANIFEST carries this evidence under `a4_wrapper_member_pins`; the regression's embedded exact bytes match both supplied files. The production archive itself was not fetched or rehashed here.

The wrapper double preserves the `-I -B` interpreter flags and all boot.py bytes. It replaces the production interpreter with the required CPU interpreter and maps the boot pathname into the local fixture. The real boot still calls site.addsitedir with its production path. No production site overlay is claimed to have run: tiny CPU modules supply the preflight's CUDA/version imports. The test proves the script-path calling convention and confirms -c refusal.

## Staging and adoption contract

Follow [README](kit_parity50/README.md): apply patches 01–03 to the pinned full A4 source and 04–05 to its operator; build with `u0/a19.py --enable-extensions --manifest ... --extension-pins ...`; place, fill and obtain CPU proof. Run the private gate, seal, stage-kit and transfer before salloc. The host then stages runtime and data, runs the gate, and returns its receipt before submit/unpack.

The candidate binds **step 400 only**, read A/job **173060**, package **a15_cot_apdc76460c3a164**, artifact SHA256 **5083243cfedd2a389dfca579c5452e7d0c73b03a58e1cb7d204292ddd10e67cd**. It uses A4's 636-item schedule, one card, caches only, general/no-requeue. All-cache allowance is 12 GiB; processor-only is 4 GiB and needs its matching gate. The required device is exactly NVIDIA H100 80GB HBM3, 132 SMs, capability 9.0 and 79–86 billion bytes of memory.

`host.ALIASES` owns the names and targets. Under logical/d it creates `7.json -> binding.json`, `9.json -> ENVIRONMENT.json`, `a0 -> ../p/tree`, `a1.json -> p0/config.json`, `a2.pt -> k/sam3.pt`, `a3.json -> k/SAM3_RECEIPT.json`, and `a4 -> v/site`. README generates PRIVATE_ALIASES by importing that table. The a18/settings and pinned step-400 input audit found export, frames, selector-directory and SAM source-root paths already opaque at d/e, d/f, d/h and d/s. The decision input has no optional item-set path. Relative symlinks preserve resolved-path loader admission. Missing absolute sealed-settings paths fail before the guard self-test.

The host restores the authenticated package at logical/p and extracts 4.tar into root/sj/<logical>/d. It reads 4.tar once, hashing/counting the bounded stream sent to tar. A wrong hash, wrong byte count or tar failure prevents aliases and the successful staging record; the incomplete tree remains unusable. No wall-time or bandwidth saving was measured for the production archive.

The host starts the preflight and parent with `J.namespace(root) + [inputs['python'], '-B', '-I', script, config]`. The preflight is the pinned `u0/u5.py`. Workers under U0_ROOT invoke `[inputs['python'], '-B', '-I'] + args` directly. J.environment supplies HOME, TMPDIR and OPENBLAS=1; XDG/HF/Triton caches remain under the fresh opaque kit root. All workers authenticate assets, environment and kit bytes. Preflight hashes flow through stage-kit, package construction, gate validation, ue.json and submit admission.

## Runtime prerequisites and exact pins

All files below must be reachable at their exact Orchard paths. Their bytes are absent from the supplied mirror; this does not establish present-day Orchard reachability. [RUNTIME_PINS.json](kit_parity50/RUNTIME_PINS.json) copies A4's own runtime receipt. Its source SHA256 is `a62285317a774cee040ceb5817e7ad7a7e08e12ea412b8f416cfb97b5a1c12ee`. No alternate runtime is assumed.

| Group | Exact Orchard path | Bytes from receipt | SHA256 from receipt |
|---|---|---:|---|
| 0 | `/home/jjyeung/okit/p/d59945c1/4fe70504.00` | 900000000 | `273174ae1d1bc812a8843b3e2eec77e77b66b4a10d60c8871ea47529c395e2d7` |
| 0 | `/home/jjyeung/okit/p/d59945c1/4fe70504.01` | 721422080 | `c733222251bfa18ca823a719e025e3924fda21cffffc6f50cd19bb8ece4860a3` |
| 1 | `/home/jjyeung/okit/p/d59945c1/50011a59.00` | 900000000 | `a4ca7e645d1c4384bdb9506ef3e823e3964e18948f48cc627709f843744ea976` |
| 1 | `/home/jjyeung/okit/p/d59945c1/50011a59.01` | 900000000 | `beca0e524255eb310d978ec092bfab080f45e36e05ae99bfc2c3e6aeb0882e9a` |
| 1 | `/home/jjyeung/okit/p/d59945c1/50011a59.02` | 900000000 | `508e09bcce4652471a5f3115344c2ab2e2fde61cc3db17d872d45c37861087c1` |
| 1 | `/home/jjyeung/okit/p/d59945c1/50011a59.03` | 900000000 | `6f25823a68896cbf0dc87ae26a9e4d2fa25d57b1d52739c22ccad5c5d49214ef` |
| 1 | `/home/jjyeung/okit/p/d59945c1/50011a59.04` | 900000000 | `139fcc93fb1b36552564fceacf201127586c237d03f43b8e3c8e45d116f1be97` |
| 1 | `/project/community/jjyeung/bd8ae51c/p/d59945c1/50011a59.05` | 900000000 | `1cd72e6e222dbe15efab47d01adeca45aaecf3f62fcd52a6e72dd7786b307489` |
| 1 | `/project/community/jjyeung/bd8ae51c/p/d59945c1/50011a59.06` | 900000000 | `010b1302ce0ec32d1db758a4bf503e9cca4583e898ec868be4dc613694f50ed6` |
| 1 | `/project/community/jjyeung/bd8ae51c/p/d59945c1/50011a59.07` | 900000000 | `32687478f272e14632411099b316fdbb6b2d1587708ccd1893c4819a2511ba19` |
| 1 | `/project/community/jjyeung/bd8ae51c/p/d59945c1/50011a59.08` | 900000000 | `d571f17a5ed9e03514ec4553919cdebacb33fe037cad39d8f0aadb1cfafcb4fc` |
| 1 | `/project/community/jjyeung/bd8ae51c/p/d59945c1/50011a59.09` | 366728960 | `128dfaca7b744e0cf884b7caf1bc15080fab549b8e26107adb5a9b8d2b5a51a5` |
| 2 | `/project/community/jjyeung/bd8ae51c/p/d59945c1/371be2e2.00` | 409282560 | `4b11b4df5ebf8a20e5c73e5ae09f4f4695f79b44e0223254a8bbaad84127b6b3` |
| bwrap | `/project/community/jjyeung/cp4tk_rt/kit/bwrap` | 72160 | `e318903862396f96de3df57264e0158682b952fd3fb53ac23d876413e7b30f71` |

The helper reuses the unchanged runtime-group/bwrap block from A4 job.stage. S.copy_parts verifies parts before unpacking; S.room retains the 200 GiB free-space floor. Runtime expansion, H100 namespace execution and host disk peaks are unmeasured. Reserve about 33 GB for 4.tar as an estimate, plus extraction/runtime/source space. Only tiny archive fixtures were extracted here.

## Framework evidence and guard limits

CPU tests use **torch 2.11.0+cpu / transformers 5.12.1**. The pinned production receipt specifies **torch 2.13.0+cu130 / transformers 5.19.0**. [FRAMEWORK_EVIDENCE](FRAMEWORK_EVIDENCE.md) gives installed file:line citations and official documentation links for every framework behavior used. CUDA availability, version counters and default load_state_dict copying were rechecked against installed source and the official 2.11 pages in this round. Torch 2.13 can differ in counters, loading, inference tensors, dispatch and CUDA kernels; transformers 5.19 can differ in processor/model dispatch and returned containers.

Before readers, the production interpreter must detect add_, copy_ and load_state_dict mutations with the actual WeightGuard. Any miss or setup failure records failed ue.json and starts no workers; submit requires all three passing checks. This behavior passes on local torch 2.11 only. No production torch 2.13 result is claimed.

Weights must remain frozen. Calls check identities, pointers, versions, shapes/dtypes/devices and requires_grad; installation and type boundaries hash content. Persistent raw writes fail at a boundary. **Raw writes restored between boundaries remain undetected**; private tensor attributes and arbitrary non-tensor state also remain outside coverage. A hard kill can leave an unchecked journal. Cache budgets cover retained storage and transient cache copies, not model/caller memory.

The 50-item gate requires complete output schemas, every expected ID, useful hits for each enabled cache, unchanged ORIGINAL/OFF source hashes and zero semantic byte differences. Only clocks and declared audit/cache/memo telemetry are excluded; audit violations fail. Sequential shards establish equality, not parallel speed. No batching tolerance or multi-card A4 operator is offered; the array prototype remains approved=false. Scorers require successful unpack output after exit status 0; partial returns remain partial.

## Measured profile and forecast

The profile was recomputed from the supplied journals. These are existing step-200 GPU measurements, not new GPU runs. Exact recomputation output is in [profile_rerun.txt](checks/profile_rerun.txt); [profile.json](profile.json) records each source path and SHA256.

| Package/type | Items | Mean s/item | Median | p90 | Tokens/item: total / ordinary | Calls/item | G3T s/item | Factory load s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A4/camera_displacement | 150 | 9.553 | 7.641 | 15.357 | 164.05 / 124.05 | 1.00 | 2.000 | 0 (reused) |
| A4/camera_movement_direction | 150 | 9.045 | 8.963 | 9.604 | 203.61 / 163.60 | 1.00 | 0.055 | 0 (reused) |
| A4/camera_rotation | 150 | 5.088 | 5.008 | 5.266 | 89.93 / 79.02 | 1.00 | 0.103 | 0 (reused) |
| A4/object_abs_distance | 150 | 23.600 | 18.275 | 29.181 | 354.53 / 239.53 | 1.76 | 1.998 | 75.446 |
| A4/room_size_estimation | 36 | 3.667 | 3.642 | 3.856 | 65.25 / 65.25 | 0.00 | 0 (no call) | 0 (reused) |
| B5/room_size_estimation | 134 | 3.942 | 3.524 | 4.505 | 66.66 / 66.66 | 0.00 | 0 (no call) | 78.961 |

Total tokens include forced tool responses and budget tokens. Factory loading covers processor/model restore/setup, not deferred tower loading. A4 reuses one generator across five types. G3T timings cover lookup/restore or fresh execution; they do not measure SAM or total tower time. SAM has no independent timer.

A4 records 7,351.824 seconds from start to exit: 7,224.888 in items, 75.446 in loading, 1.729 in journal/control windows, and 49.761 outside type timers. B5 records 645.735 seconds, including 528.164 in items and 78.961 in loading. Residual wall time does not establish GPU idle time.

The distance profile retains one unexplained 648.397-second, 2,056-token item. There are 88 routed and 62 direct distance items. Source inspection implies 88 SAM encodes and 176 raw-name detections; those call counts are inferred. Camera items each serve one move/turn call; room items serve none.

A4 already records 461 G3T memo hits and 77 misses, retaining 128,553,354 payload bytes. This saving cannot be counted again. The new caches store video processor outputs, visual outputs and raw SAM values. They do not store question text, language/KV/recurrent state, own-depth scale, geometry or full tool responses.

**Estimate for what a19 builds:** the 636-item A4 schedule takes about **7,351.824 s (2 h 02 min 32 s; 11.559 s/item including fixed overhead)** if the supplied A4 throughput carries forward, with zero assumed cache saving. This does not measure the step-400 export. Target weights, cache guard/copy costs, actual reuse and staging can change it.

**Separate Package D estimate:** the 580-item distance read is a B5 fork with a 03:30 walltime and has **no ON route in a19**. Using 23.599762 s/item plus 75.446133 s loading and 49.761372 s overhead gives an estimate of **13,813.069 s (3 h 50 min)** on one card. Ideal two/four balanced-shard estimates are 6,969.138 / 3,547.173 s; they require an undelivered multi-card operator and exclude scene imbalance, staging, queues and preemption. The fixed 50-item reuse-heavy sample cannot establish these throughput estimates.








## Measured CPU guard overhead

These rerun CPU stubs contain bf16 2048×1024 parameters and 1024-element buffers. Their forward returns 32 elements without model-sized matrix work. Seven warm hits and three boundaries are timed per case. These measurements do not predict H100 speedup; [CACHE_COST3.json](checks/CACHE_COST3.json) holds raw samples.

| Parameters | Parameter/buffer tensors | Weight+buffer bytes | Full hash ms/call | Live guard ms/call | Install s | Boundary s |
|---:|---:|---:|---:|---:|---:|---:|
| 268435456 | 128/128 | 537133056 | 347.067 | 26.141 | 0.341 | 0.342 |
| 536870912 | 256/256 | 1074266112 | 706.850 | 53.070 | 0.681 | 0.696 |

## Patches and authentication

Base SHA256: `813fe4c57b2deed4bd731dd1e3493b6b0bed8d31e7bff92ff112cf5c9df823c3` across 927 files. Reader patches add 42 files without changing original reader bytes. Operator changes remain behind read_extensions, default OFF. All five patches apply with zero fuzz; base inventories and added hashes authenticate. MANIFEST pins payload, copied A4 files, bootstrap, operators, kit, operation files and wrapper evidence.

| Patch | Bytes | SHA256 |
|---|---:|---|
| [01_bounded_read_caches.diff](patches/01_bounded_read_caches.diff) | 90430 | `369af9663fbc1008f9ecf5a32c5067ba4a5f4cd31412f07db8263b13b23fd4c3` |
| [02_atomic_scene_shards.diff](patches/02_atomic_scene_shards.diff) | 218879 | `77b024654841f4537787e48c8b7a1087a8f84636ec0332a7dcbf2a11c2af3336` |
| [03_production_integration.diff](patches/03_production_integration.diff) | 271088 | `8ca34d1fb539dfc6294ce46dd888f0773e570a5792e83b5b4dfdd27b8e0f4830` |
| [04_operator_cache_bound.diff](patches/04_operator_cache_bound.diff) | 2723 | `0d3bdc2d943554cd525627466d2d71f30881884e76df95204ede6c1accdb9061` |
| [05_operator_return_and_proof.diff](patches/05_operator_return_and_proof.diff) | 6754 | `5369d7a7b2442a00a63bf318904a5e60ba972f6a6512500241c64019c77778cd` |

## What could go wrong and how we would notice

| Risk | Detection and response |
|---|---|
| Missing runtime, disk space, alias target or failed extraction | Part pins, space checks, tar status/stream hash and sealed-path existence checks refuse before reader work. |
| Actual H100 namespace/wrapper/overlay differs from the CPU fixture | Script preflight and environment pins refuse; only the real host gate establishes compatibility. |
| Torch 2.13 changes mutation behavior | Production self-test writes failed evidence and starts no readers. |
| Export, source, operator, preflight or environment differs | CPU, gate, worker and submit authentication refuses. |
| CUDA kernels or eager SAM loading change outputs | The zero-byte-difference gate refuses; matching aggregate scores do not suffice. |
| A worker fails before a final receipt | Nonzero exit stops the run; no ue.json means no return archive and submit cannot pass. The worker log remains only until allocation cleanup. |
| Hash mismatch during extraction | No successful stage record is published; extracted bytes remain untrusted and must not be executed. |
| Cache overhead dominates | Measure full-worker elapsed time and memory before crediting any speedup. |
| A raw write is restored between boundaries | Frozen ownership is required; the guard cannot detect that sequence. |

## Not done

No real H100 bwrap namespace, production interpreter/site overlay, torch 2.13 guard, GPU byte parity, throughput, GPU memory, large 4.tar extraction, transfer, submit or persistent requeue ran. Runtime files remain exact-path prerequisites. Tests use explicit namespace/runtime doubles and tiny assets. The boot bytes themselves did execute. Independent prior wrapper-member SHA256 pins were unavailable. CPU checks require no local OS sockets. Host argv screening and a receipt for arbitrary worker failure remain outside this fix set; current failures refuse adoption.

The review labels below remain because the dispatch explicitly requires finding/fix/test traceability. Other documentation states the current behavior.

## Review round 9: finding -> fix -> test

Authenticated A4 runtime staging, production guard self-tests, pre-allocation kit preparation, fresh tokens, J.environment and labelled logs pass. Preflight and parent enter the namespace; workers call its wrapper directly. All eleven preserved controls fail before and pass after.

## Review round 8: finding -> fix -> test

Symlink-preserving archive/real-loader admission, CPU-bound runtime versions, step-400-only build admission, resolved archive paths and retained tar diagnostics pass. The interpreter command is checked inside A4’s namespace. The preserved control reproduces 29 assertion failures.

## Review round 7: finding -> fix -> test

CPU-job asset staging, bounded fill waits, exact HBM3/132-SM admission, kit/input evidence and step-400 export binding pass. The preserved control reproduces ten assertion failures.

## Review round 6: finding -> fix -> test

Executable unpack, detached locked fill, complete cont_ops CPU assertions, copied-member pins and export/device admission pass. The preserved control reproduces 31 assertion failures.

## Review round 5: finding -> fix -> test

Batch wrapping, package/operator/extension authentication, executable operations, exact adoption profile, pool bound and unpack checks pass. The preserved control reproduces eleven assertion failures.

## Review round 4: finding -> fix -> test

The A4 builder retains export binding and compatible operation helpers. Preparation, rehearsal, bootstrap/action dispatch and return checks pass, including 636 stub reads. Both preserved controls reproduce their failures.

## Review round 3: finding -> fix -> test

Install/boundary hashing, fatal per-call identity/counter checks, processor-only mode, operator cache allowance/dispatch, base authentication, lock recovery and worker arguments pass. Preserved controls reproduce their failures.

## Review round 2: finding -> fix -> test

Entry isolation, path policy, bounded arrays, overlay pins, SAM capacity, deadline/lock/accounting and worker setup pass. The preserved control reproduces thirteen assertions and one expected CLI import error.

## Review round 1: finding -> fix -> test

Cache keys, strict parity schema/hits, unchanged OFF bytes, weight identity, writer-lock recovery, opacity and hard retained-memory accounting pass. The preserved control reproduces eight assertion failures.


## Exact commands and outputs

All commands run from this workspace through `bash work/cpu.sh`, which exports hidden CUDA, thread/cache limits and PYTHONDONTWRITEBYTECODE, then execs `nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B`. Fixture commands use work/run_fixture5.py to share identical local bytes after real writes. No production logic is replaced by that storage harness. Expected before-control failures are labelled; the development-only README assertion failure is retained in run_checks10_development.txt.

Command: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_read_cache.py`

Exact output ([checks/cache.txt](checks/cache.txt)):

```text
test_budget_eviction_oversize_and_process_reset (__main__.ReadCacheTests.test_budget_eviction_oversize_and_process_reset) ... ok
test_cache_enforces_serial_thread_ownership (__main__.ReadCacheTests.test_cache_enforces_serial_thread_ownership) ... ok
test_defaults_and_validation (__main__.ReadCacheTests.test_defaults_and_validation) ... ok
test_exact_storage_signed_zero_nan_bfloat_and_mutation (__main__.ReadCacheTests.test_exact_storage_signed_zero_nan_bfloat_and_mutation) ... ok
test_fifty_stub_reads_original_off_bytes_and_opt_in_cache_on (__main__.ReadCacheTests.test_fifty_stub_reads_original_off_bytes_and_opt_in_cache_on) ... ok
test_installed_transformers_tiny_vision_and_output_mutation (__main__.ReadCacheTests.test_installed_transformers_tiny_vision_and_output_mutation) ... ok
test_installed_transformers_video_packing_without_torchvision (__main__.ReadCacheTests.test_installed_transformers_video_packing_without_torchvision) ... ok
test_key_container_and_transient_memory_stay_within_hard_cache_bound (__main__.ReadCacheTests.test_key_container_and_transient_memory_stay_within_hard_cache_bound) ... ok
test_key_invalidates_pixels_metadata_kwargs_dtype_and_order (__main__.ReadCacheTests.test_key_invalidates_pixels_metadata_kwargs_dtype_and_order) ... ok
test_processor_keeps_question_out_and_metadata_in_key (__main__.ReadCacheTests.test_processor_keeps_question_out_and_metadata_in_key) ... ok
test_sam_caches_raw_values_but_recomputes_geometry (__main__.ReadCacheTests.test_sam_caches_raw_values_but_recomputes_geometry) ... ok
test_unaudited_container_constructors_bypass_without_snapshot (__main__.ReadCacheTests.test_unaudited_container_constructors_bypass_without_snapshot) ... ok
test_vision_child_hook_bypasses_cache (__main__.ReadCacheTests.test_vision_child_hook_bypasses_cache) ... ok
test_vision_execution_settings_and_live_options_invalidate (__main__.ReadCacheTests.test_vision_execution_settings_and_live_options_invalidate) ... ok
test_vision_returns_same_type_and_keeps_outer_hooks (__main__.ReadCacheTests.test_vision_returns_same_type_and_keeps_outer_hooks) ... ok

----------------------------------------------------------------------
Ran 15 tests in 2.420s

OK
```

Command: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_read_journal.py`

Exact output ([checks/journal.txt](checks/journal.txt)):

```text
test_duplicate_corruption_and_unowned_jsonl_fail (__main__.JournalTests.test_duplicate_corruption_and_unowned_jsonl_fail) ... ok
test_interrupted_pending_file_is_not_committed (__main__.JournalTests.test_interrupted_pending_file_is_not_committed) ... ok
test_scene_sets_disjoint_complete_stable_and_colocated (__main__.JournalTests.test_scene_sets_disjoint_complete_stable_and_colocated) ... ok
test_torn_utf8_projection_and_commit_before_projection (__main__.JournalTests.test_torn_utf8_projection_and_commit_before_projection) ... ok
test_deadline_after_environment_before_first_item_can_resume (__main__.RunnerTests.test_deadline_after_environment_before_first_item_can_resume) ... ok
test_deadline_before_environment_creates_no_unbound_projection (__main__.RunnerTests.test_deadline_before_environment_creates_no_unbound_projection) ... ok
test_deadline_recovery_keeps_writer_lock (__main__.RunnerTests.test_deadline_recovery_keeps_writer_lock) ... ok
test_default_path_rejects_torn_tail_and_has_no_commit_store (__main__.RunnerTests.test_default_path_rejects_torn_tail_and_has_no_commit_store) ... ok
test_public_journals_log_tokens_and_restore_identity_on_private_host (__main__.RunnerTests.test_public_journals_log_tokens_and_restore_identity_on_private_host) ... ok
test_reader_resume_committed_item_without_regeneration (__main__.RunnerTests.test_reader_resume_committed_item_without_regeneration) ... ok
test_semantic_comparison_preserves_calls_tokens_scores_and_signed_zero (__main__.RunnerTests.test_semantic_comparison_preserves_calls_tokens_scores_and_signed_zero) ... ok
test_shards_merge_byte_identical_to_single_and_reject_missing_duplicate (__main__.RunnerTests.test_shards_merge_byte_identical_to_single_and_reject_missing_duplicate) ... ok
test_type_journals_support_empty_scene_shards (__main__.RunnerTests.test_type_journals_support_empty_scene_shards) ... ok

----------------------------------------------------------------------
Ran 13 tests in 0.151s

OK
```

Command: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_off.py`

Exact output ([checks/off.txt](checks/off.txt)):

```text
test_every_output_byte_and_source_hash_matches_original (__main__.OffContractTests.test_every_output_byte_and_source_hash_matches_original) ... ok

----------------------------------------------------------------------
Ran 1 test in 4.674s

OK
```

Command: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_public.py`

Exact output ([checks/public.txt](checks/public.txt)):

```text
test_legacy_worker_log_context_manager_never_writes_raw_library_output (__main__.PublicTests.test_legacy_worker_log_context_manager_never_writes_raw_library_output) ... ok
test_library_wire_decoder_preserves_ordinary_json_and_hash_serialization (__main__.PublicTests.test_library_wire_decoder_preserves_ordinary_json_and_hash_serialization) ... ok
test_no_raw_id_map_is_published_and_nested_ids_roundtrip (__main__.PublicTests.test_no_raw_id_map_is_published_and_nested_ids_roundtrip) ... ok
test_private_restoration_is_rejected_outside_trinity_before_writing (__main__.PublicTests.test_private_restoration_is_rejected_outside_trinity_before_writing) ... ok
test_public_array_descriptor_has_opaque_paths_and_numeric_types (__main__.PublicTests.test_public_array_descriptor_has_opaque_paths_and_numeric_types) ... ok
test_settings_tokens_hide_every_name_and_reject_descriptive_paths (__main__.PublicTests.test_settings_tokens_hide_every_name_and_reject_descriptive_paths) ... ok
test_unstructured_library_logs_and_partial_lines_only_publish_tokens (__main__.PublicTests.test_unstructured_library_logs_and_partial_lines_only_publish_tokens) ... ok

----------------------------------------------------------------------
Ran 7 tests in 0.003s

OK
```

Command: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round1.py`

Exact output ([checks/round1.txt](checks/round1.txt)):

```text
test_f1_nested_mapping_boundaries_and_stale_processor (__main__.ReviewRegressions.test_f1_nested_mapping_boundaries_and_stale_processor) ... ok
test_f2_absent_hits_and_incomplete_trace_cannot_pass (__main__.ReviewRegressions.test_f2_absent_hits_and_incomplete_trace_cannot_pass) ... ok
test_f3_original_files_and_hash_tree_have_no_off_changes (__main__.ReviewRegressions.test_f3_original_files_and_hash_tree_have_no_off_changes) ... ok
test_f4_replaced_parameter_cannot_reuse_old_value (__main__.ReviewRegressions.test_f4_replaced_parameter_cannot_reuse_old_value) ... ok
test_f5_deadline_handler_does_not_repair_after_lock_unwinds (__main__.ReviewRegressions.test_f5_deadline_handler_does_not_repair_after_lock_unwinds) ... ok
test_f6_public_configuration_has_no_descriptive_paths (__main__.ReviewRegressions.test_f6_public_configuration_has_no_descriptive_paths) ... ok
test_f7_eviction_precedes_snapshot_allocation (__main__.ReviewRegressions.test_f7_eviction_precedes_snapshot_allocation) ... ok
test_f7_key_overhead_prevents_unbounded_retention (__main__.ReviewRegressions.test_f7_key_overhead_prevents_unbounded_retention) ... ok
test_deadline_recovery_keeps_writer_lock (round1_journal_tests.RunnerTests.test_deadline_recovery_keeps_writer_lock) ... ok
test_legacy_worker_log_context_manager_never_writes_raw_library_output (round1_public_tests.PublicTests.test_legacy_worker_log_context_manager_never_writes_raw_library_output) ... ok
test_library_wire_decoder_preserves_ordinary_json_and_hash_serialization (round1_public_tests.PublicTests.test_library_wire_decoder_preserves_ordinary_json_and_hash_serialization) ... ok
test_no_raw_id_map_is_published_and_nested_ids_roundtrip (round1_public_tests.PublicTests.test_no_raw_id_map_is_published_and_nested_ids_roundtrip) ... ok
test_private_restoration_is_rejected_outside_trinity_before_writing (round1_public_tests.PublicTests.test_private_restoration_is_rejected_outside_trinity_before_writing) ... ok
test_public_array_descriptor_has_opaque_paths_and_numeric_types (round1_public_tests.PublicTests.test_public_array_descriptor_has_opaque_paths_and_numeric_types) ... ok
test_settings_tokens_hide_every_name_and_reject_descriptive_paths (round1_public_tests.PublicTests.test_settings_tokens_hide_every_name_and_reject_descriptive_paths) ... ok
test_unstructured_library_logs_and_partial_lines_only_publish_tokens (round1_public_tests.PublicTests.test_unstructured_library_logs_and_partial_lines_only_publish_tokens) ... ok
test_every_output_byte_and_source_hash_matches_original (round1_off_tests.OffContractTests.test_every_output_byte_and_source_hash_matches_original) ... ok

----------------------------------------------------------------------
Ran 17 tests in 3.634s

OK
```

Command: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round2.py`

Exact output ([checks/round2.txt](checks/round2.txt)):

```text
test_f10_wrong_exception_is_not_accepted_and_lock_suite_runs (__main__.Round2Tests.test_f10_wrong_exception_is_not_accepted_and_lock_suite_runs) ... ok
test_f16_no_descriptive_environment_variable (__main__.Round2Tests.test_f16_no_descriptive_environment_variable) ... ok
test_f1_actual_isolated_script_plain_and_opaque (__main__.Round2Tests.test_f1_actual_isolated_script_plain_and_opaque) ... ok
test_f2_all_three_path_checks_accept_established_roots (__main__.Round2Tests.test_f2_all_three_path_checks_accept_established_roots) ... ok
test_f3_approved_argv_budget_script_and_retry (__main__.Round2Tests.test_f3_approved_argv_budget_script_and_retry) ... ok
test_f4_build_pins_on_overlay_and_off_package_bytes (__main__.Round2Tests.test_f4_build_pins_on_overlay_and_off_package_bytes) ... ok
test_f4_dispatch_uses_extension_entry_only_when_enabled (__main__.Round2Tests.test_f4_dispatch_uses_extension_entry_only_when_enabled) ... ok
test_f4_scene_summary_and_existing_return_envelope (__main__.Round2Tests.test_f4_scene_summary_and_existing_return_envelope) ... ok
test_f5_sam_default_capacity_and_raw_mutation_safety (__main__.Round2Tests.test_f5_sam_default_capacity_and_raw_mutation_safety) ... ok
test_f6_nonatomic_deadline_counts_under_lock (__main__.Round2Tests.test_f6_nonatomic_deadline_counts_under_lock) ... ok
test_f7_lock_wait_is_bounded_and_then_recovers (__main__.Round2Tests.test_f7_lock_wait_is_bounded_and_then_recovers) ... ok
test_f8_processor_bypass_is_counted (__main__.Round2Tests.test_f8_processor_bypass_is_counted) ... ok
test_f9_roots_and_manifest_checked_before_any_arm (__main__.Round2Tests.test_f9_roots_and_manifest_checked_before_any_arm) ... ok

----------------------------------------------------------------------
Ran 13 tests in 3.605s

OK
```

Command: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round3.py`

Exact output ([checks/round3.txt](checks/round3.txt)):

```text
test_f1_calls_never_hash_parameters_or_buffers (__main__.Round3Tests.test_f1_calls_never_hash_parameters_or_buffers) ... ok
test_f1_parameter_and_buffer_changes_are_fatal_and_latched (__main__.Round3Tests.test_f1_parameter_and_buffer_changes_are_fatal_and_latched) ... ok
test_f1_processor_only_overrides_model_switches (__main__.Round3Tests.test_f1_processor_only_overrides_model_switches) ... ok
test_f1_raw_storage_is_rejected_at_boundary (__main__.Round3Tests.test_f1_raw_storage_is_rejected_at_boundary) ... ok
test_f1_type_boundary_failure_blocks_resume_and_merge (__main__.Round3Tests.test_f1_type_boundary_failure_blocks_resume_and_merge) ... ok
test_f1_valid_boundary_allows_deadline_resume_and_public_merge (__main__.Round3Tests.test_f1_valid_boundary_allows_deadline_resume_and_public_merge) ... ok
test_f3_both_base_inventories_are_authenticated (__main__.Round3Tests.test_f3_both_base_inventories_are_authenticated) ... ok
test_f4_worker_uses_settings_argv_without_environment_side_effect (__main__.Round3Tests.test_f4_worker_uses_settings_argv_without_environment_side_effect) ... ok
test_f7_off_import_guard_covers_all_overlay_modules (__main__.Round3Tests.test_f7_off_import_guard_covers_all_overlay_modules) ... ok

----------------------------------------------------------------------
Ran 9 tests in 1.605s

OK
```

Command: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_operator_round3.py`

Exact output ([checks/operator3.txt](checks/operator3.txt)):

```text
test_f2_a12_payload_through_a4_actions_and_nested_return (__main__.OperatorTests.test_f2_a12_payload_through_a4_actions_and_nested_return) ... ok
test_f2_operator_memory_bound_includes_cache_only_when_enabled (__main__.OperatorTests.test_f2_operator_memory_bound_includes_cache_only_when_enabled) ... ok

----------------------------------------------------------------------
Ran 2 tests in 9.070s

OK
```

Command: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_lock_round3.py`

Exact output ([checks/lock3.txt](checks/lock3.txt)):

```text
test_deadline_recovery_keeps_writer_lock (lock_behavior.RunnerTests.test_deadline_recovery_keeps_writer_lock) ... ok
test_type_deadline_recovery_holds_writer_lock (__main__.TypeLockTests.test_type_deadline_recovery_holds_writer_lock) ... ok

----------------------------------------------------------------------
Ran 2 tests in 0.015s

OK
```

Command: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py`

Exact output ([checks/round4.txt](checks/round4.txt)):

```text
test_f1_bound_package_preserves_a4_contract_and_binding (__main__.Round4Tests.test_f1_bound_package_preserves_a4_contract_and_binding) ... ok
test_f2_bound_real_job_and_rehearsal_memory (__main__.Round4Tests.test_f2_bound_real_job_and_rehearsal_memory) ... ok
test_f3_cache_only_return_refuses_unverified_journals (__main__.Round4Tests.test_f3_cache_only_return_refuses_unverified_journals) ... ok
test_f9_off_builder_guard_and_processor_only (__main__.Round4Tests.test_f9_off_builder_guard_and_processor_only) ... ok

----------------------------------------------------------------------
Ran 4 tests in 21.333s

OK
{"output": "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/863e85df932841fdbf29df3113c5e263/verified-return", "complete": false, "status": "FAILED", "sha256": "f03449b9b94056d3c1918adf0aec15b62d0ffdcc077b3dcc91e35dd6a3a4b479"}
CPU bound-export fixture: /scratch/jjyeung/orch_n30/so_read/work/test-artifacts/863e85df932841fdbf29df3113c5e263
```

Command: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round5.py`

Exact output ([checks/round5.txt](checks/round5.txt)):

```text
test_f1_batch_wrapper_and_real_bundle_guard (__main__.Round5Tests.test_f1_batch_wrapper_and_real_bundle_guard) ... ok
test_f2_pins_refuse_before_copy (__main__.Round5Tests.test_f2_pins_refuse_before_copy) ... ok
test_f3_binding_derivation_and_operations (__main__.Round5Tests.test_f3_binding_derivation_and_operations) ... ok
test_f3_submit_pool_and_proof_refusals (__main__.Round5Tests.test_f3_submit_pool_and_proof_refusals) ... ok
test_f4_gate_pins_adopted_settings_and_profile (__main__.Round5Tests.test_f4_gate_pins_adopted_settings_and_profile) ... ok
test_f5_forecast_identifies_both_reads (__main__.Round5Tests.test_f5_forecast_identifies_both_reads) ... ok
test_f7_refused_unpack_not_scoreable (__main__.Round5Tests.test_f7_refused_unpack_not_scoreable) ... ok

----------------------------------------------------------------------
Ran 7 tests in 8.985s

OK
All CPU receipt checks passed
{"passed": true, "pool_bytes": 75000000}
All CPU receipt checks passed
```

Command: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py`

Exact output ([checks/round6.txt](checks/round6.txt)):

```text
test_f1_readme_unpack_subprocess (__main__.Round6Tests.test_f1_readme_unpack_subprocess) ... ok
test_f2_detached_locked_fill_exit_success_and_failure (__main__.Round6Tests.test_f2_detached_locked_fill_exit_success_and_failure) ... ok
test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks) ... ok
test_f4_every_copied_a4_member_pinned_before_output (__main__.Round6Tests.test_f4_every_copied_a4_member_pinned_before_output) ... ok
test_f5_checkpoint_binding_and_runtime_recheck (__main__.Round6Tests.test_f5_checkpoint_binding_and_runtime_recheck) ... ok
test_f5_production_device_is_required (__main__.Round6Tests.test_f5_production_device_is_required) ... ok
test_f5_runtime_asset_recheck (__main__.Round6Tests.test_f5_runtime_asset_recheck) ... ok
test_info_done_whitespace (__main__.Round6Tests.test_info_done_whitespace) ... ok
test_info_submit_requires_successful_bound_gpu_gate (__main__.Round6Tests.test_info_submit_requires_successful_bound_gpu_gate) ... ok

----------------------------------------------------------------------
Ran 9 tests in 25.434s

OK
README unpack command: exit 0; authenticated partial return accepted.
Detached fill: success=0, failure=17, duplicate launch refused.
```

Command: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round7.py`

Exact output ([checks/round7.txt](checks/round7.txt)):

```text
test_f1_archive_runs_inside_live_namespace_and_survives_it (__main__.Round7Tests.test_f1_archive_runs_inside_live_namespace_and_survives_it) ... ok
test_f2_fill_wait_missing_token_dead_pid_timeout_and_success (__main__.Round7Tests.test_f2_fill_wait_missing_token_dead_pid_timeout_and_success) ... ok
test_f3_exact_sxm_name_and_132_sms (__main__.Round7Tests.test_f3_exact_sxm_name_and_132_sms) ... ok
test_info_export_bytes_bound_to_cpu_inputs_before_gpu (__main__.Round7Tests.test_info_export_bytes_bound_to_cpu_inputs_before_gpu) ... ok
test_info_host_paths_allocation_and_input_evidence (__main__.Round7Tests.test_info_host_paths_allocation_and_input_evidence) ... ok
test_info_receipt_records_and_submit_checks_kit_comparator_sample (__main__.Round7Tests.test_info_receipt_records_and_submit_checks_kit_comparator_sample) ... ok
test_info_unpack_ignores_python_environment_and_keeps_sibling_import (__main__.Round7Tests.test_info_unpack_ignores_python_environment_and_keeps_sibling_import) ... ok
test_rebind_step400_only (__main__.Round7Tests.test_rebind_step400_only) ... ok

----------------------------------------------------------------------
Ran 8 tests in 5.556s

OK
Live namespace tar: regular file and symlink preserved; archive survives namespace loss; duplicate and OFF guarded.
Fill wait: missing token, dead worker, deadline and exit 17 refuse; exit 0 passes; production maximum 14400 seconds.
Only reviewed step-400 export passes; changed artifact and selectable-export API refuse.
```

Command: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py`

Exact output ([checks/round8.txt](checks/round8.txt)):

```text
test_f1_external_symlinks_refuse_before_archive (__main__.Round8Tests.test_f1_external_symlinks_refuse_before_archive) ... ok
test_f1_preserved_absolute_link_passes_real_artifact_and_load_native (__main__.Round8Tests.test_f1_preserved_absolute_link_passes_real_artifact_and_load_native) ... ok
test_f2_gate_authenticates_environment_before_gpu (__main__.Round8Tests.test_f2_gate_authenticates_environment_before_gpu) ... ok
test_f2_gpu_shell_preflight_executes_archived_interpreter (__main__.Round8Tests.test_f2_gpu_shell_preflight_executes_archived_interpreter) ... ok
test_f2_runtime_environment_and_receipt (__main__.Round8Tests.test_f2_runtime_environment_and_receipt) ... ok
test_f2_submit_checks_environment_versions_and_sha (__main__.Round8Tests.test_f2_submit_checks_environment_versions_and_sha) ... ok
test_f3_builder_refuses_other_export_before_reading_base (__main__.Round8Tests.test_f3_builder_refuses_other_export_before_reading_base) ... ok
test_f4_readme_archive_path_accepts_symlinked_parent (__main__.Round8Tests.test_f4_readme_archive_path_accepts_symlinked_parent) ... ok
test_info_gpu_commands_and_aliases (__main__.Round8Tests.test_info_gpu_commands_and_aliases) ... ok
test_info_tar_stderr_is_retained (__main__.Round8Tests.test_info_tar_stderr_is_retained) ... ok

----------------------------------------------------------------------
Ran 10 tests in 6.627s

OK
Absolute e/heads.pt symlink survives tar/extract; real Artifact.verify and load_native admission pass before model loading.
Preflight requires real A4 namespace argv; workers use the authenticated wrapper inside that namespace.
Runtime torch/transformers/CUDA and environment SHA256 are exact; changed versions, bytes and CPU build refuse.
```

Command: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round9.py`

Exact output ([checks/round9.txt](checks/round9.txt)):

```text
test_f1_actual_launch_calls_namespace_twice (__main__.Round9Tests.test_f1_actual_launch_calls_namespace_twice) ... ok
test_f1_all_commands_use_real_namespace_and_input_wrapper (__main__.Round9Tests.test_f1_all_commands_use_real_namespace_and_input_wrapper) ... ok
test_f1_authenticated_bootstrap_and_physical_asset_extraction (__main__.Round9Tests.test_f1_authenticated_bootstrap_and_physical_asset_extraction) ... ok
test_f1_runtime_staging_reuses_package_block_and_pins (__main__.Round9Tests.test_f1_runtime_staging_reuses_package_block_and_pins) ... ok
test_f2_failed_self_test_is_recorded_and_cannot_pass_receipt (__main__.Round9Tests.test_f2_failed_self_test_is_recorded_and_cannot_pass_receipt) ... ok
test_f2_main_records_failure_and_never_starts_workers (__main__.Round9Tests.test_f2_main_records_failure_and_never_starts_workers) ... ok
test_f2_real_guard_self_test_and_each_missed_operation (__main__.Round9Tests.test_f2_real_guard_self_test_and_each_missed_operation) ... ok
test_f2_submit_requires_all_three_guard_checks (__main__.Round9Tests.test_f2_submit_requires_all_three_guard_checks) ... ok
test_f3_staging_transfer_precedes_allocation_and_roots_extract (__main__.Round9Tests.test_f3_staging_transfer_precedes_allocation_and_roots_extract) ... ok
test_info_round7_logs_are_labelled (__main__.Round9Tests.test_info_round7_logs_are_labelled) ... ok
test_info_token_and_framework_gap_and_guard_limits (__main__.Round9Tests.test_info_token_and_framework_gap_and_guard_limits) ... ok

----------------------------------------------------------------------
Ran 11 tests in 4.464s

OK
Actual host launch calls preflight then parent with real namespace prefixes and the input wrapper.
Real J.namespace prefix and inputs[python] wrap preflight/parent; all three worker launch sites use the authenticated wrapper; J.environment retains HOME/TMPDIR/OPENBLAS=1.
Authenticated real A4 bootstrap stages fixture 4.tar to root/sj/<logical>/d with preserved wrapper/links and the complete pinned logical/p code tree; changed input proof refuses. Runtime I/O and bwrap execution are explicit doubles.
Package staging block extracts pinned fixture runtime; changed part hash refuses; 13 part pins plus bwrap match A4 receipts.
A missed mutation persists in failed ue.json; missing or failed guard evidence cannot produce passed=true.
Actual main writes failed ue.json and starts zero workers for a missed mutation or self-test setup exception.
Real frozen scratch module detects add_, copy_ and load_state_dict; each injected detection miss fails independently before workers.
Submit accepts complete guard evidence and rejects each missed mutation.
Gate/seal/stage-kit/transfer precede salloc; exact README host commands successfully extract kit and both source fixture archives.
Eight carried round-7 applied logs live only under checks/round7.
Fresh token derives kit paths; framework version gap and carried guard limits are explicit.
```

Command: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round10.py`

Exact output ([checks/round10.txt](checks/round10.txt)):

```text
test_f1_public_script_is_pinned_and_tampering_refuses (__main__.Round10Tests.test_f1_public_script_is_pinned_and_tampering_refuses) ... ok
test_f1_real_boot_refuses_c_and_runs_actual_preflight_script (__main__.Round10Tests.test_f1_real_boot_refuses_c_and_runs_actual_preflight_script) ... ok
test_f2_missing_nested_path_refuses_before_self_test (__main__.Round10Tests.test_f2_missing_nested_path_refuses_before_self_test) ... ok
test_f2_stage_resolves_every_sealed_path_with_one_alias_table (__main__.Round10Tests.test_f2_stage_resolves_every_sealed_path_with_one_alias_table) ... ok
test_f3_workers_are_direct_inside_namespace (__main__.Round10Tests.test_f3_workers_are_direct_inside_namespace) ... ok
test_f4_one_archive_read_hashes_extracted_bytes_and_refuses_bad_pin (__main__.Round10Tests.test_f4_one_archive_read_hashes_extracted_bytes_and_refuses_bad_pin) ... ok
test_f4_readme_has_no_asset_preread_and_generates_aliases (__main__.Round10Tests.test_f4_readme_has_no_asset_preread_and_generates_aliases) ... ok

----------------------------------------------------------------------
Ran 7 tests in 1.089s

OK
Public u0/u5.py preserves shipped bytes; validate_kit rejects its mutation.
Exact 443-byte boot refuses -c; host launches the shipped preflight and parent through the wrapper double. CUDA/version imports are explicit CPU stubs.
Nested missing absolute settings path refuses before the guard self-test; existing paths pass.
host.stage creates every shared alias; all 12 absolute settings paths seal and resolve, including code and site roots. Runtime and namespace execution are explicit doubles.
U0_ROOT workers call inputs[python] directly and retain J.environment; no nested bwrap.
Extraction reads all 10,240 archive bytes once, hashes the same stream, and refuses a changed hash before publishing staging success.
README generates PRIVATE_ALIASES from the host table and does not reread 4.tar before extraction.
```

Command: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/out/kit_parity50/test_compare.py`

Exact output ([checks/kit.txt](checks/kit.txt)):

```text
test_changed_answer_detected_even_when_score_unchanged (__main__.CompareTests.test_changed_answer_detected_even_when_score_unchanged) ... ok
test_each_enabled_cache_requires_hits (__main__.CompareTests.test_each_enabled_cache_requires_hits) ... ok
test_missing_duplicate_and_partial_tail_rejected (__main__.CompareTests.test_missing_duplicate_and_partial_tail_rejected) ... ok
test_public_wire_comparison_decodes_ids_without_publishing_a_reverse_map (__main__.CompareTests.test_public_wire_comparison_decodes_ids_without_publishing_a_reverse_map) ... ok
test_response_changes_are_detected (__main__.CompareTests.test_response_changes_are_detected) ... ok
test_scale_empty_fields_and_nested_served_responses_are_required (__main__.CompareTests.test_scale_empty_fields_and_nested_served_responses_are_required) ... ok
test_source_hash_gate_rejects_changed_or_missing_hashes (__main__.CompareTests.test_source_hash_gate_rejects_changed_or_missing_hashes) ... ok
test_telemetry_different_exact_trace_passes (__main__.CompareTests.test_telemetry_different_exact_trace_passes) ... ok
test_tokens_calls_heads_and_finish_each_detected (__main__.CompareTests.test_tokens_calls_heads_and_finish_each_detected) ... ok

----------------------------------------------------------------------
Ran 9 tests in 0.282s

OK
```

Command: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/out/kit_parity50/test_run.py`

Exact output ([checks/kit_launch.txt](checks/kit_launch.txt)):

```text
test_durable_scene_comparison_requires_explicit_on_arm (__main__.LaunchTests.test_durable_scene_comparison_requires_explicit_on_arm) ... ok
test_original_and_off_do_not_opt_in_to_journaling_or_sharding (__main__.LaunchTests.test_original_and_off_do_not_opt_in_to_journaling_or_sharding) ... ok
test_stage_kit_uses_opaque_names_token_metadata_and_authenticated_sample_bytes (__main__.LaunchTests.test_stage_kit_uses_opaque_names_token_metadata_and_authenticated_sample_bytes) ... ok

----------------------------------------------------------------------
Ran 3 tests in 0.052s

OK
```

Command: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/apply-round10/51ac61e502af4c98b8f65204e06cf2dd/src/u0/tests/test_off.py`

Exact output ([checks/applied_off.txt](checks/applied_off.txt)):

```text
test_every_output_byte_and_source_hash_matches_original (__main__.OffContractTests.test_every_output_byte_and_source_hash_matches_original) ... ok

----------------------------------------------------------------------
Ran 1 test in 4.640s

OK
```

Command: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/apply-round10/51ac61e502af4c98b8f65204e06cf2dd/src/u0/tests/test_round4.py`

Exact output ([checks/applied_round4.txt](checks/applied_round4.txt)):

```text
test_f1_bound_package_preserves_a4_contract_and_binding (__main__.Round4Tests.test_f1_bound_package_preserves_a4_contract_and_binding) ... ok
test_f2_bound_real_job_and_rehearsal_memory (__main__.Round4Tests.test_f2_bound_real_job_and_rehearsal_memory) ... ok
test_f3_cache_only_return_refuses_unverified_journals (__main__.Round4Tests.test_f3_cache_only_return_refuses_unverified_journals) ... ok
test_f9_off_builder_guard_and_processor_only (__main__.Round4Tests.test_f9_off_builder_guard_and_processor_only) ... ok

----------------------------------------------------------------------
Ran 4 tests in 20.145s

OK
{"output": "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/6e2134867b494bf29b789c266fbdfd2c/verified-return", "complete": false, "status": "FAILED", "sha256": "52e3867735496853227bc85531f9715ce83f18cdd95de67f01e54cb6cd6e65e2"}
CPU bound-export fixture: /scratch/jjyeung/orch_n30/so_read/work/test-artifacts/6e2134867b494bf29b789c266fbdfd2c
```

Command: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/apply-round10/51ac61e502af4c98b8f65204e06cf2dd/src/u0/tests/test_round5.py`

Exact output ([checks/applied_round5.txt](checks/applied_round5.txt)):

```text
test_f1_batch_wrapper_and_real_bundle_guard (__main__.Round5Tests.test_f1_batch_wrapper_and_real_bundle_guard) ... ok
test_f2_pins_refuse_before_copy (__main__.Round5Tests.test_f2_pins_refuse_before_copy) ... ok
test_f3_binding_derivation_and_operations (__main__.Round5Tests.test_f3_binding_derivation_and_operations) ... ok
test_f3_submit_pool_and_proof_refusals (__main__.Round5Tests.test_f3_submit_pool_and_proof_refusals) ... ok
test_f4_gate_pins_adopted_settings_and_profile (__main__.Round5Tests.test_f4_gate_pins_adopted_settings_and_profile) ... ok
test_f5_forecast_identifies_both_reads (__main__.Round5Tests.test_f5_forecast_identifies_both_reads) ... ok
test_f7_refused_unpack_not_scoreable (__main__.Round5Tests.test_f7_refused_unpack_not_scoreable) ... ok

----------------------------------------------------------------------
Ran 7 tests in 9.097s

OK
All CPU receipt checks passed
{"passed": true, "pool_bytes": 75000000}
All CPU receipt checks passed
```

Command: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/apply-round10/51ac61e502af4c98b8f65204e06cf2dd/src/u0/tests/test_round6.py`

Exact output ([checks/applied_round6.txt](checks/applied_round6.txt)):

```text
test_f1_readme_unpack_subprocess (__main__.Round6Tests.test_f1_readme_unpack_subprocess) ... ok
test_f2_detached_locked_fill_exit_success_and_failure (__main__.Round6Tests.test_f2_detached_locked_fill_exit_success_and_failure) ... ok
test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks) ... ok
test_f4_every_copied_a4_member_pinned_before_output (__main__.Round6Tests.test_f4_every_copied_a4_member_pinned_before_output) ... ok
test_f5_checkpoint_binding_and_runtime_recheck (__main__.Round6Tests.test_f5_checkpoint_binding_and_runtime_recheck) ... ok
test_f5_production_device_is_required (__main__.Round6Tests.test_f5_production_device_is_required) ... ok
test_f5_runtime_asset_recheck (__main__.Round6Tests.test_f5_runtime_asset_recheck) ... ok
test_info_done_whitespace (__main__.Round6Tests.test_info_done_whitespace) ... ok
test_info_submit_requires_successful_bound_gpu_gate (__main__.Round6Tests.test_info_submit_requires_successful_bound_gpu_gate) ... ok

----------------------------------------------------------------------
Ran 9 tests in 26.397s

OK
README unpack command: exit 0; authenticated partial return accepted.
Detached fill: success=0, failure=17, duplicate launch refused.
```

Command: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/apply-round10/51ac61e502af4c98b8f65204e06cf2dd/src/u0/tests/test_round7.py`

Exact output ([checks/applied_round7.txt](checks/applied_round7.txt)):

```text
test_f1_archive_runs_inside_live_namespace_and_survives_it (__main__.Round7Tests.test_f1_archive_runs_inside_live_namespace_and_survives_it) ... ok
test_f2_fill_wait_missing_token_dead_pid_timeout_and_success (__main__.Round7Tests.test_f2_fill_wait_missing_token_dead_pid_timeout_and_success) ... ok
test_f3_exact_sxm_name_and_132_sms (__main__.Round7Tests.test_f3_exact_sxm_name_and_132_sms) ... ok
test_info_export_bytes_bound_to_cpu_inputs_before_gpu (__main__.Round7Tests.test_info_export_bytes_bound_to_cpu_inputs_before_gpu) ... ok
test_info_host_paths_allocation_and_input_evidence (__main__.Round7Tests.test_info_host_paths_allocation_and_input_evidence) ... ok
test_info_receipt_records_and_submit_checks_kit_comparator_sample (__main__.Round7Tests.test_info_receipt_records_and_submit_checks_kit_comparator_sample) ... ok
test_info_unpack_ignores_python_environment_and_keeps_sibling_import (__main__.Round7Tests.test_info_unpack_ignores_python_environment_and_keeps_sibling_import) ... ok
test_rebind_step400_only (__main__.Round7Tests.test_rebind_step400_only) ... ok

----------------------------------------------------------------------
Ran 8 tests in 5.601s

OK
Live namespace tar: regular file and symlink preserved; archive survives namespace loss; duplicate and OFF guarded.
Fill wait: missing token, dead worker, deadline and exit 17 refuse; exit 0 passes; production maximum 14400 seconds.
Only reviewed step-400 export passes; changed artifact and selectable-export API refuse.
```

Command: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/apply-round10/51ac61e502af4c98b8f65204e06cf2dd/src/u0/tests/test_round8.py`

Exact output ([checks/applied_round8.txt](checks/applied_round8.txt)):

```text
test_f1_external_symlinks_refuse_before_archive (__main__.Round8Tests.test_f1_external_symlinks_refuse_before_archive) ... ok
test_f1_preserved_absolute_link_passes_real_artifact_and_load_native (__main__.Round8Tests.test_f1_preserved_absolute_link_passes_real_artifact_and_load_native) ... ok
test_f2_gate_authenticates_environment_before_gpu (__main__.Round8Tests.test_f2_gate_authenticates_environment_before_gpu) ... ok
test_f2_gpu_shell_preflight_executes_archived_interpreter (__main__.Round8Tests.test_f2_gpu_shell_preflight_executes_archived_interpreter) ... ok
test_f2_runtime_environment_and_receipt (__main__.Round8Tests.test_f2_runtime_environment_and_receipt) ... ok
test_f2_submit_checks_environment_versions_and_sha (__main__.Round8Tests.test_f2_submit_checks_environment_versions_and_sha) ... ok
test_f3_builder_refuses_other_export_before_reading_base (__main__.Round8Tests.test_f3_builder_refuses_other_export_before_reading_base) ... ok
test_f4_readme_archive_path_accepts_symlinked_parent (__main__.Round8Tests.test_f4_readme_archive_path_accepts_symlinked_parent) ... ok
test_info_gpu_commands_and_aliases (__main__.Round8Tests.test_info_gpu_commands_and_aliases) ... ok
test_info_tar_stderr_is_retained (__main__.Round8Tests.test_info_tar_stderr_is_retained) ... ok

----------------------------------------------------------------------
Ran 10 tests in 6.701s

OK
Absolute e/heads.pt symlink survives tar/extract; real Artifact.verify and load_native admission pass before model loading.
Preflight requires real A4 namespace argv; workers use the authenticated wrapper inside that namespace.
Runtime torch/transformers/CUDA and environment SHA256 are exact; changed versions, bytes and CPU build refuse.
```

Command: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/apply-round10/51ac61e502af4c98b8f65204e06cf2dd/src/u0/tests/test_round9.py`

Exact output ([checks/applied_round9.txt](checks/applied_round9.txt)):

```text
test_f1_actual_launch_calls_namespace_twice (__main__.Round9Tests.test_f1_actual_launch_calls_namespace_twice) ... ok
test_f1_all_commands_use_real_namespace_and_input_wrapper (__main__.Round9Tests.test_f1_all_commands_use_real_namespace_and_input_wrapper) ... ok
test_f1_authenticated_bootstrap_and_physical_asset_extraction (__main__.Round9Tests.test_f1_authenticated_bootstrap_and_physical_asset_extraction) ... ok
test_f1_runtime_staging_reuses_package_block_and_pins (__main__.Round9Tests.test_f1_runtime_staging_reuses_package_block_and_pins) ... ok
test_f2_failed_self_test_is_recorded_and_cannot_pass_receipt (__main__.Round9Tests.test_f2_failed_self_test_is_recorded_and_cannot_pass_receipt) ... ok
test_f2_main_records_failure_and_never_starts_workers (__main__.Round9Tests.test_f2_main_records_failure_and_never_starts_workers) ... ok
test_f2_real_guard_self_test_and_each_missed_operation (__main__.Round9Tests.test_f2_real_guard_self_test_and_each_missed_operation) ... ok
test_f2_submit_requires_all_three_guard_checks (__main__.Round9Tests.test_f2_submit_requires_all_three_guard_checks) ... ok
test_f3_staging_transfer_precedes_allocation_and_roots_extract (__main__.Round9Tests.test_f3_staging_transfer_precedes_allocation_and_roots_extract) ... ok
test_info_round7_logs_are_labelled (__main__.Round9Tests.test_info_round7_logs_are_labelled) ... ok
test_info_token_and_framework_gap_and_guard_limits (__main__.Round9Tests.test_info_token_and_framework_gap_and_guard_limits) ... ok

----------------------------------------------------------------------
Ran 11 tests in 4.560s

OK
Actual host launch calls preflight then parent with real namespace prefixes and the input wrapper.
Real J.namespace prefix and inputs[python] wrap preflight/parent; all three worker launch sites use the authenticated wrapper; J.environment retains HOME/TMPDIR/OPENBLAS=1.
Authenticated real A4 bootstrap stages fixture 4.tar to root/sj/<logical>/d with preserved wrapper/links and the complete pinned logical/p code tree; changed input proof refuses. Runtime I/O and bwrap execution are explicit doubles.
Package staging block extracts pinned fixture runtime; changed part hash refuses; 13 part pins plus bwrap match A4 receipts.
A missed mutation persists in failed ue.json; missing or failed guard evidence cannot produce passed=true.
Actual main writes failed ue.json and starts zero workers for a missed mutation or self-test setup exception.
Real frozen scratch module detects add_, copy_ and load_state_dict; each injected detection miss fails independently before workers.
Submit accepts complete guard evidence and rejects each missed mutation.
Gate/seal/stage-kit/transfer precede salloc; exact README host commands successfully extract kit and both source fixture archives.
Eight carried round-7 applied logs live only under checks/round7.
Fresh token derives kit paths; framework version gap and carried guard limits are explicit.
```

Command: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/apply-round10/51ac61e502af4c98b8f65204e06cf2dd/src/u0/tests/test_round10.py`

Exact output ([checks/applied_round10.txt](checks/applied_round10.txt)):

```text
test_f1_public_script_is_pinned_and_tampering_refuses (__main__.Round10Tests.test_f1_public_script_is_pinned_and_tampering_refuses) ... ok
test_f1_real_boot_refuses_c_and_runs_actual_preflight_script (__main__.Round10Tests.test_f1_real_boot_refuses_c_and_runs_actual_preflight_script) ... ok
test_f2_missing_nested_path_refuses_before_self_test (__main__.Round10Tests.test_f2_missing_nested_path_refuses_before_self_test) ... ok
test_f2_stage_resolves_every_sealed_path_with_one_alias_table (__main__.Round10Tests.test_f2_stage_resolves_every_sealed_path_with_one_alias_table) ... ok
test_f3_workers_are_direct_inside_namespace (__main__.Round10Tests.test_f3_workers_are_direct_inside_namespace) ... ok
test_f4_one_archive_read_hashes_extracted_bytes_and_refuses_bad_pin (__main__.Round10Tests.test_f4_one_archive_read_hashes_extracted_bytes_and_refuses_bad_pin) ... ok
test_f4_readme_has_no_asset_preread_and_generates_aliases (__main__.Round10Tests.test_f4_readme_has_no_asset_preread_and_generates_aliases) ... ok

----------------------------------------------------------------------
Ran 7 tests in 1.113s

OK
Public u0/u5.py preserves shipped bytes; validate_kit rejects its mutation.
Exact 443-byte boot refuses -c; host launches the shipped preflight and parent through the wrapper double. CUDA/version imports are explicit CPU stubs.
Nested missing absolute settings path refuses before the guard self-test; existing paths pass.
host.stage creates every shared alias; all 12 absolute settings paths seal and resolve, including code and site roots. Runtime and namespace execution are explicit doubles.
U0_ROOT workers call inputs[python] directly and retain J.environment; no nested bwrap.
Extraction reads all 10,240 archive bytes once, hashes the same stream, and refuses a changed hash before publishing staging success.
README generates PRIVATE_ALIASES from the host table and does not reread 4.tar before extraction.
```

Command: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/apply-round10/51ac61e502af4c98b8f65204e06cf2dd/src/u0/tests/test_compare.py`

Exact output ([checks/applied_compare.txt](checks/applied_compare.txt)):

```text
test_changed_answer_detected_even_when_score_unchanged (__main__.CompareTests.test_changed_answer_detected_even_when_score_unchanged) ... ok
test_each_enabled_cache_requires_hits (__main__.CompareTests.test_each_enabled_cache_requires_hits) ... ok
test_missing_duplicate_and_partial_tail_rejected (__main__.CompareTests.test_missing_duplicate_and_partial_tail_rejected) ... ok
test_public_wire_comparison_decodes_ids_without_publishing_a_reverse_map (__main__.CompareTests.test_public_wire_comparison_decodes_ids_without_publishing_a_reverse_map) ... ok
test_response_changes_are_detected (__main__.CompareTests.test_response_changes_are_detected) ... ok
test_scale_empty_fields_and_nested_served_responses_are_required (__main__.CompareTests.test_scale_empty_fields_and_nested_served_responses_are_required) ... ok
test_source_hash_gate_rejects_changed_or_missing_hashes (__main__.CompareTests.test_source_hash_gate_rejects_changed_or_missing_hashes) ... ok
test_telemetry_different_exact_trace_passes (__main__.CompareTests.test_telemetry_different_exact_trace_passes) ... ok
test_tokens_calls_heads_and_finish_each_detected (__main__.CompareTests.test_tokens_calls_heads_and_finish_each_detected) ... ok

----------------------------------------------------------------------
Ran 9 tests in 0.276s

OK
```

Command: `bash work/cpu.sh work/run_checks.py  # round1_before; exact environment/argv in runner`

Exact output ([checks/round1_before.txt](checks/round1_before.txt)):

```text
test_f1_nested_mapping_boundaries_and_stale_processor (__main__.ReviewRegressions.test_f1_nested_mapping_boundaries_and_stale_processor) ... FAIL
test_f2_absent_hits_and_incomplete_trace_cannot_pass (__main__.ReviewRegressions.test_f2_absent_hits_and_incomplete_trace_cannot_pass) ... FAIL
test_f3_original_files_and_hash_tree_have_no_off_changes (__main__.ReviewRegressions.test_f3_original_files_and_hash_tree_have_no_off_changes) ... FAIL
test_f4_replaced_parameter_cannot_reuse_old_value (__main__.ReviewRegressions.test_f4_replaced_parameter_cannot_reuse_old_value) ... FAIL
test_f5_deadline_handler_does_not_repair_after_lock_unwinds (__main__.ReviewRegressions.test_f5_deadline_handler_does_not_repair_after_lock_unwinds) ... FAIL
test_f6_public_configuration_has_no_descriptive_paths (__main__.ReviewRegressions.test_f6_public_configuration_has_no_descriptive_paths) ... FAIL
test_f7_eviction_precedes_snapshot_allocation (__main__.ReviewRegressions.test_f7_eviction_precedes_snapshot_allocation) ... FAIL
test_f7_key_overhead_prevents_unbounded_retention (__main__.ReviewRegressions.test_f7_key_overhead_prevents_unbounded_retention) ... FAIL

======================================================================
FAIL: test_f1_nested_mapping_boundaries_and_stale_processor (__main__.ReviewRegressions.test_f1_nested_mapping_boundaries_and_stale_processor)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round1.py", line 37, in test_f1_nested_mapping_boundaries_and_stale_processor
    self.assertNotEqual(C.digest(a),C.digest(b))
AssertionError: '195d5f5f2708b74c04d42a9245ed1c16e74695ec698c428a707d3180b25239d6' == '195d5f5f2708b74c04d42a9245ed1c16e74695ec698c428a707d3180b25239d6'

======================================================================
FAIL: test_f2_absent_hits_and_incomplete_trace_cannot_pass (__main__.ReviewRegressions.test_f2_absent_hits_and_incomplete_trace_cannot_pass)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round1.py", line 53, in test_f2_absent_hits_and_incomplete_trace_cannot_pass
    with self.assertRaisesRegex(ValueError,'^Missing required trace field: scale$'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f3_original_files_and_hash_tree_have_no_off_changes (__main__.ReviewRegressions.test_f3_original_files_and_hash_tree_have_no_off_changes)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round1.py", line 59, in test_f3_original_files_and_hash_tree_have_no_off_changes
    self.assertEqual((INPUT/rel).read_bytes(),(root/rel).read_bytes(),rel)
AssertionError: b'"""[10860 chars]n    hook = install_hook(model, CallHook(proce[3697 chars]en\n' != b'"""[10860 chars]n    from .read_cache import switches\n    cac[4848 chars]en\n' : b/e2e_reader/parity.py

======================================================================
FAIL: test_f4_replaced_parameter_cannot_reuse_old_value (__main__.ReviewRegressions.test_f4_replaced_parameter_cannot_reuse_old_value)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round1.py", line 73, in test_f4_replaced_parameter_cannot_reuse_old_value
    self.assertEqual(actual,9.)
AssertionError: 2.0 != 9.0

======================================================================
FAIL: test_f5_deadline_handler_does_not_repair_after_lock_unwinds (__main__.ReviewRegressions.test_f5_deadline_handler_does_not_repair_after_lock_unwinds)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round1.py", line 78, in test_f5_deadline_handler_does_not_repair_after_lock_unwinds
    self.assertNotIn('.recover()',handler)
AssertionError: '.recover()' unexpectedly found in ":\n                    if getattr(part,'atomic_journal',False):\n                        from .atomic_journal import AtomicJournal\n                        rows=AtomicJournal(root).recover()\n                    else:rows=read_records(root/'items.jsonl')\n                    from h1eval.items import load_manifest\n                    manifest=load_manifest(part.items)\n                    expected=len(select_types(manifest['items'],selected(manifest['items'],part.shard,getattr(part,'scene_shards',False)),kind,getattr(part,'atomic_journal',False)))\n                    result=dict(completed=len(rows),expected=expected,stopped=True)\n                    write_json(root/'SUMMARY.json',result)\n                    write_json(root/'progress.json',result)\n                    commit_record(steps,dict(event='deadline',type=kind,**result))\n"

======================================================================
FAIL: test_f6_public_configuration_has_no_descriptive_paths (__main__.ReviewRegressions.test_f6_public_configuration_has_no_descriptive_paths)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round1.py", line 86, in test_f6_public_configuration_has_no_descriptive_paths
    try:validate_config(cfg)
        ^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/a9.py", line 189, in validate_config
    raise ValueError('Public configuration requires opaque staged paths')
ValueError: Public configuration requires opaque staged paths

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round1.py", line 87, in test_f6_public_configuration_has_no_descriptive_paths
    except ValueError as error:self.fail(str(error))
                               ^^^^^^^^^^^^^^^^^^^^^
AssertionError: Public configuration requires opaque staged paths

======================================================================
FAIL: test_f7_eviction_precedes_snapshot_allocation (__main__.ReviewRegressions.test_f7_eviction_precedes_snapshot_allocation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round1.py", line 105, in test_f7_eviction_precedes_snapshot_allocation
    self.assertEqual(observed[0],0)
AssertionError: 30005 != 0

======================================================================
FAIL: test_f7_key_overhead_prevents_unbounded_retention (__main__.ReviewRegressions.test_f7_key_overhead_prevents_unbounded_retention)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round1.py", line 93, in test_f7_key_overhead_prevents_unbounded_retention
    self.assertEqual(len(cache.entries),0)
AssertionError: 1 != 0

----------------------------------------------------------------------
Ran 8 tests in 0.028s

FAILED (failures=8)
```

Command: `bash work/cpu.sh work/run_checks.py  # round2_before; exact environment/argv in runner`

Exact output ([checks/round2_before.txt](checks/round2_before.txt)):

```text
test_f10_wrong_exception_is_not_accepted_and_lock_suite_runs (__main__.Round2Tests.test_f10_wrong_exception_is_not_accepted_and_lock_suite_runs) ... FAIL
test_f16_no_descriptive_environment_variable (__main__.Round2Tests.test_f16_no_descriptive_environment_variable) ... FAIL
test_f1_actual_isolated_script_plain_and_opaque (__main__.Round2Tests.test_f1_actual_isolated_script_plain_and_opaque) ... 
  test_f1_actual_isolated_script_plain_and_opaque (__main__.Round2Tests.test_f1_actual_isolated_script_plain_and_opaque) (opaque=False) ... FAIL
  test_f1_actual_isolated_script_plain_and_opaque (__main__.Round2Tests.test_f1_actual_isolated_script_plain_and_opaque) (opaque=True) ... FAIL
test_f2_all_three_path_checks_accept_established_roots (__main__.Round2Tests.test_f2_all_three_path_checks_accept_established_roots) ... ERROR
test_f3_approved_argv_budget_script_and_retry (__main__.Round2Tests.test_f3_approved_argv_budget_script_and_retry) ... FAIL
test_f4_build_pins_on_overlay_and_off_package_bytes (__main__.Round2Tests.test_f4_build_pins_on_overlay_and_off_package_bytes) ... FAIL
test_f4_dispatch_uses_extension_entry_only_when_enabled (__main__.Round2Tests.test_f4_dispatch_uses_extension_entry_only_when_enabled) ... FAIL
test_f4_scene_summary_and_existing_return_envelope (__main__.Round2Tests.test_f4_scene_summary_and_existing_return_envelope) ... FAIL
test_f5_sam_default_capacity_and_raw_mutation_safety (__main__.Round2Tests.test_f5_sam_default_capacity_and_raw_mutation_safety) ... FAIL
test_f6_nonatomic_deadline_counts_under_lock (__main__.Round2Tests.test_f6_nonatomic_deadline_counts_under_lock) ... FAIL
test_f7_lock_wait_is_bounded_and_then_recovers (__main__.Round2Tests.test_f7_lock_wait_is_bounded_and_then_recovers) ... FAIL
test_f8_processor_bypass_is_counted (__main__.Round2Tests.test_f8_processor_bypass_is_counted) ... FAIL
test_f9_roots_and_manifest_checked_before_any_arm (__main__.Round2Tests.test_f9_roots_and_manifest_checked_before_any_arm) ... FAIL

======================================================================
ERROR: test_f2_all_three_path_checks_accept_established_roots (__main__.Round2Tests.test_f2_all_three_path_checks_accept_established_roots)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round2.py", line 75, in test_f2_all_three_path_checks_accept_established_roots
    boundary.seal_settings({'asset':path},root/'u0')
  File "/scratch/jjyeung/orch_n30/so_read/work/round2-before/src/u0/a9.py", line 49, in seal_settings
    validate_paths(settings)
  File "/scratch/jjyeung/orch_n30/so_read/work/round2-before/src/u0/a9.py", line 44, in validate_paths
    check(settings)
  File "/scratch/jjyeung/orch_n30/so_read/work/round2-before/src/u0/a9.py", line 39, in check
    for item in value.values():check(item)
                               ^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/round2-before/src/u0/a9.py", line 43, in check
    raise ValueError('Settings contain a non-opaque staged asset path')
ValueError: Settings contain a non-opaque staged asset path

======================================================================
FAIL: test_f10_wrong_exception_is_not_accepted_and_lock_suite_runs (__main__.Round2Tests.test_f10_wrong_exception_is_not_accepted_and_lock_suite_runs)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round2.py", line 295, in test_f10_wrong_exception_is_not_accepted_and_lock_suite_runs
    self.assertFalse(result.wasSuccessful(),'An unrelated ValueError was accepted')
AssertionError: True is not false : An unrelated ValueError was accepted

======================================================================
FAIL: test_f16_no_descriptive_environment_variable (__main__.Round2Tests.test_f16_no_descriptive_environment_variable)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round2.py", line 306, in test_f16_no_descriptive_environment_variable
    self.assertTrue("os.environ['H10_SETTINGS']" not in source,'Descriptive settings environment remains')
AssertionError: False is not true : Descriptive settings environment remains

======================================================================
FAIL: test_f1_actual_isolated_script_plain_and_opaque (__main__.Round2Tests.test_f1_actual_isolated_script_plain_and_opaque) (opaque=False)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round2.py", line 67, in test_f1_actual_isolated_script_plain_and_opaque
    self.assertEqual(result.returncode,0,result.stdout+result.stderr)
AssertionError: 1 != 0 : Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/859bc6c610894c079777e7446436cdfc/u0/a8.py", line 65, in <module>
    raise SystemExit(main())
                     ^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/859bc6c610894c079777e7446436cdfc/u0/a8.py", line 61, in main
    return launch(rest)
           ^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/859bc6c610894c079777e7446436cdfc/u0/a4.py", line 2, in main
    from a8 import source_hash
ModuleNotFoundError: No module named 'a8'


======================================================================
FAIL: test_f1_actual_isolated_script_plain_and_opaque (__main__.Round2Tests.test_f1_actual_isolated_script_plain_and_opaque) (opaque=True)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round2.py", line 67, in test_f1_actual_isolated_script_plain_and_opaque
    self.assertEqual(result.returncode,0,result.stdout+result.stderr)
AssertionError: 1 != 0 : Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/ca03b38d111749c0ba2a5d02410d0725/u0/a8.py", line 65, in <module>
    raise SystemExit(main())
                     ^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/ca03b38d111749c0ba2a5d02410d0725/u0/a8.py", line 56, in main
    from a9 import install_wire_decoder,PublicLog
ModuleNotFoundError: No module named 'a9'


======================================================================
FAIL: test_f3_approved_argv_budget_script_and_retry (__main__.Round2Tests.test_f3_approved_argv_budget_script_and_retry)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round2.py", line 89, in test_f3_approved_argv_budget_script_and_retry
    module=load('array_policy',require(self,'a15.py'))
                               ^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round2.py", line 43, in require
    path=E/name;test.assertTrue(path.is_file(),'Missing implementation: '+name)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: False is not true : Missing implementation: a15.py

======================================================================
FAIL: test_f4_build_pins_on_overlay_and_off_package_bytes (__main__.Round2Tests.test_f4_build_pins_on_overlay_and_off_package_bytes)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round2.py", line 116, in test_f4_build_pins_on_overlay_and_off_package_bytes
    builder=load('production_builder',require(self,'a12.py'))
                                      ^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round2.py", line 43, in require
    path=E/name;test.assertTrue(path.is_file(),'Missing implementation: '+name)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: False is not true : Missing implementation: a12.py

======================================================================
FAIL: test_f4_dispatch_uses_extension_entry_only_when_enabled (__main__.Round2Tests.test_f4_dispatch_uses_extension_entry_only_when_enabled)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round2.py", line 181, in test_f4_dispatch_uses_extension_entry_only_when_enabled
    entry=require(self,'a13.py')
          ^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round2.py", line 43, in require
    path=E/name;test.assertTrue(path.is_file(),'Missing implementation: '+name)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: False is not true : Missing implementation: a13.py

======================================================================
FAIL: test_f4_scene_summary_and_existing_return_envelope (__main__.Round2Tests.test_f4_scene_summary_and_existing_return_envelope)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round2.py", line 149, in test_f4_scene_summary_and_existing_return_envelope
    runner=load('production_runner',require(self,'a17.py'))
                                    ^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round2.py", line 43, in require
    path=E/name;test.assertTrue(path.is_file(),'Missing implementation: '+name)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: False is not true : Missing implementation: a17.py

======================================================================
FAIL: test_f5_sam_default_capacity_and_raw_mutation_safety (__main__.Round2Tests.test_f5_sam_default_capacity_and_raw_mutation_safety)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round2.py", line 208, in test_f5_sam_default_capacity_and_raw_mutation_safety
    self.assertTrue(hasattr(cache,'cache_bytes'),'Missing SAM capacity policy')
AssertionError: False is not true : Missing SAM capacity policy

======================================================================
FAIL: test_f6_nonatomic_deadline_counts_under_lock (__main__.Round2Tests.test_f6_nonatomic_deadline_counts_under_lock)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round2.py", line 246, in test_f6_nonatomic_deadline_counts_under_lock
    self.assertEqual(raised.exception.progress,dict(completed=1,expected=2,stopped=True,initialized=True))
AssertionError: {'completed': 0, 'expected': 2, 'stopped': True, 'initialized': False} != {'completed': 1, 'expected': 2, 'stopped': True, 'initialized': True}
- {'completed': 0, 'expected': 2, 'initialized': False, 'stopped': True}
?               ^                                ^^^^

+ {'completed': 1, 'expected': 2, 'initialized': True, 'stopped': True}
?               ^                                ^^^


======================================================================
FAIL: test_f7_lock_wait_is_bounded_and_then_recovers (__main__.Round2Tests.test_f7_lock_wait_is_bounded_and_then_recovers)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round2.py", line 251, in test_f7_lock_wait_is_bounded_and_then_recovers
    worker=load('array_lock',E/'a7.py');self.assertTrue(hasattr(worker,'acquire'),'Missing bounded lock wait')
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: False is not true : Missing bounded lock wait

======================================================================
FAIL: test_f8_processor_bypass_is_counted (__main__.Round2Tests.test_f8_processor_bypass_is_counted)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round2.py", line 268, in test_f8_processor_bypass_is_counted
    self.assertEqual(store.stats.get('processor',{}).get('bypasses'),2)
AssertionError: None != 2

======================================================================
FAIL: test_f9_roots_and_manifest_checked_before_any_arm (__main__.Round2Tests.test_f9_roots_and_manifest_checked_before_any_arm)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round2.py", line 273, in test_f9_roots_and_manifest_checked_before_any_arm
    self.assertTrue(hasattr(kit,'validate_roots'),'Missing independent root validation')
AssertionError: False is not true : Missing independent root validation

----------------------------------------------------------------------
Ran 13 tests in 0.164s

FAILED (failures=13, errors=1)
```

Command: `bash work/cpu.sh work/run_checks.py  # round3_before; exact environment/argv in runner`

Exact output ([checks/round3_before.txt](checks/round3_before.txt)):

```text
test_f1_calls_never_hash_parameters_or_buffers (__main__.Round3Tests.test_f1_calls_never_hash_parameters_or_buffers) ... FAIL
test_f1_parameter_and_buffer_changes_are_fatal_and_latched (__main__.Round3Tests.test_f1_parameter_and_buffer_changes_are_fatal_and_latched) ... FAIL
test_f1_processor_only_overrides_model_switches (__main__.Round3Tests.test_f1_processor_only_overrides_model_switches) ... FAIL
test_f1_raw_storage_is_rejected_at_boundary (__main__.Round3Tests.test_f1_raw_storage_is_rejected_at_boundary) ... FAIL
test_f1_type_boundary_failure_blocks_resume_and_merge (__main__.Round3Tests.test_f1_type_boundary_failure_blocks_resume_and_merge) ... FAIL
test_f1_valid_boundary_allows_deadline_resume_and_public_merge (__main__.Round3Tests.test_f1_valid_boundary_allows_deadline_resume_and_public_merge) ... FAIL
test_f3_both_base_inventories_are_authenticated (__main__.Round3Tests.test_f3_both_base_inventories_are_authenticated) ... FAIL
test_f4_worker_uses_settings_argv_without_environment_side_effect (__main__.Round3Tests.test_f4_worker_uses_settings_argv_without_environment_side_effect) ... ok
test_f7_off_import_guard_covers_all_overlay_modules (__main__.Round3Tests.test_f7_off_import_guard_covers_all_overlay_modules) ... 
  test_f7_off_import_guard_covers_all_overlay_modules (__main__.Round3Tests.test_f7_off_import_guard_covers_all_overlay_modules) (module=11) ... FAIL
  test_f7_off_import_guard_covers_all_overlay_modules (__main__.Round3Tests.test_f7_off_import_guard_covers_all_overlay_modules) (module=12) ... FAIL
  test_f7_off_import_guard_covers_all_overlay_modules (__main__.Round3Tests.test_f7_off_import_guard_covers_all_overlay_modules) (module=13) ... FAIL
  test_f7_off_import_guard_covers_all_overlay_modules (__main__.Round3Tests.test_f7_off_import_guard_covers_all_overlay_modules) (module=14) ... FAIL
  test_f7_off_import_guard_covers_all_overlay_modules (__main__.Round3Tests.test_f7_off_import_guard_covers_all_overlay_modules) (module=15) ... FAIL
  test_f7_off_import_guard_covers_all_overlay_modules (__main__.Round3Tests.test_f7_off_import_guard_covers_all_overlay_modules) (module=16) ... FAIL
  test_f7_off_import_guard_covers_all_overlay_modules (__main__.Round3Tests.test_f7_off_import_guard_covers_all_overlay_modules) (module=17) ... FAIL
  test_f7_off_import_guard_covers_all_overlay_modules (__main__.Round3Tests.test_f7_off_import_guard_covers_all_overlay_modules) (module=18) ... FAIL

======================================================================
FAIL: test_f1_calls_never_hash_parameters_or_buffers (__main__.Round3Tests.test_f1_calls_never_hash_parameters_or_buffers)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round3.py", line 53, in test_f1_calls_never_hash_parameters_or_buffers
    a=m(torch.ones(1,32));b=m(torch.ones(1,32))
      ^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/nn/modules/module.py", line 1779, in _wrapped_call_impl
    return self._call_impl(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/nn/modules/module.py", line 1790, in _call_impl
    return forward_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/round3-before-u0/a0.py", line 361, in forward
    try:key = digest((visual.config.to_dict(),module_identity(visual),args,kwargs))
                                              ^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/round3-before-u0/a0.py", line 329, in module_identity
    h.update(digest((name,id(tensor),tensor.data_ptr(),tensor_version(tensor),digest(tensor))).encode())
                                                                              ^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/unittest/mock.py", line 1139, in __call__
    return self._mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/unittest/mock.py", line 1143, in _mock_call
    return self._execute_mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/unittest/mock.py", line 1204, in _execute_mock_call
    result = effect(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round3.py", line 51, in checked
    def checked(v):visit(v);return original(v)
                   ^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round3.py", line 46, in visit
    if isinstance(v,torch.Tensor):self.assertNotIn(id(v),weights,'Per-call weight hashing')
                                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 140553963702464 unexpectedly found in {140553963702464, 140553963702784} : Per-call weight hashing

======================================================================
FAIL: test_f1_parameter_and_buffer_changes_are_fatal_and_latched (__main__.Round3Tests.test_f1_parameter_and_buffer_changes_are_fatal_and_latched)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round3.py", line 57, in test_f1_parameter_and_buffer_changes_are_fatal_and_latched
    self.assertTrue(hasattr(C,'ModelMutationError'),'Missing fatal weight guard')
AssertionError: False is not true : Missing fatal weight guard

======================================================================
FAIL: test_f1_processor_only_overrides_model_switches (__main__.Round3Tests.test_f1_processor_only_overrides_model_switches)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round3.py", line 92, in test_f1_processor_only_overrides_model_switches
    self.assertEqual(flags,dict(read_processor_cache='on',read_vision_cache='off',read_sam_cache='off'))
AssertionError: {'rea[15 chars]he': 'off', 'read_vision_cache': 'on', 'read_sam_cache': 'on'} != {'rea[15 chars]he': 'on', 'read_vision_cache': 'off', 'read_sam_cache': 'off'}
- {'read_processor_cache': 'off',
?                            ^^

+ {'read_processor_cache': 'on',
?                            ^

-  'read_sam_cache': 'on',
?                      ^

+  'read_sam_cache': 'off',
?                      ^^

-  'read_vision_cache': 'on'}
?                         ^

+  'read_vision_cache': 'off'}
?                         ^^


======================================================================
FAIL: test_f1_raw_storage_is_rejected_at_boundary (__main__.Round3Tests.test_f1_raw_storage_is_rejected_at_boundary)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round3.py", line 76, in test_f1_raw_storage_is_rejected_at_boundary
    self.assertTrue(hasattr(C.ReadCache,'weight_boundary'),'Missing boundary hashing')
AssertionError: False is not true : Missing boundary hashing

======================================================================
FAIL: test_f1_type_boundary_failure_blocks_resume_and_merge (__main__.Round3Tests.test_f1_type_boundary_failure_blocks_resume_and_merge)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round3.py", line 97, in test_f1_type_boundary_failure_blocks_resume_and_merge
    self.assertTrue(hasattr(C.ReadCache,'weight_boundary'),'Missing weight boundary')
AssertionError: False is not true : Missing weight boundary

======================================================================
FAIL: test_f1_valid_boundary_allows_deadline_resume_and_public_merge (__main__.Round3Tests.test_f1_valid_boundary_allows_deadline_resume_and_public_merge)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round3.py", line 129, in test_f1_valid_boundary_allows_deadline_resume_and_public_merge
    self.assertTrue(hasattr(C.ReadCache,'weight_boundary'),'Missing weight boundary')
AssertionError: False is not true : Missing weight boundary

======================================================================
FAIL: test_f3_both_base_inventories_are_authenticated (__main__.Round3Tests.test_f3_both_base_inventories_are_authenticated)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round3.py", line 173, in test_f3_both_base_inventories_are_authenticated
    with self.assertRaisesRegex(ValueError,'Base hash differs'):kit.validate_roots(cfg)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f7_off_import_guard_covers_all_overlay_modules (__main__.Round3Tests.test_f7_off_import_guard_covers_all_overlay_modules) (module=11)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round3.py", line 196, in test_f7_off_import_guard_covers_all_overlay_modules
    with self.subTest(module=i),self.assertRaisesRegex(AssertionError,'OFF attempted'):
                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: AssertionError not raised

======================================================================
FAIL: test_f7_off_import_guard_covers_all_overlay_modules (__main__.Round3Tests.test_f7_off_import_guard_covers_all_overlay_modules) (module=12)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round3.py", line 196, in test_f7_off_import_guard_covers_all_overlay_modules
    with self.subTest(module=i),self.assertRaisesRegex(AssertionError,'OFF attempted'):
                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: AssertionError not raised

======================================================================
FAIL: test_f7_off_import_guard_covers_all_overlay_modules (__main__.Round3Tests.test_f7_off_import_guard_covers_all_overlay_modules) (module=13)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round3.py", line 196, in test_f7_off_import_guard_covers_all_overlay_modules
    with self.subTest(module=i),self.assertRaisesRegex(AssertionError,'OFF attempted'):
                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: AssertionError not raised

======================================================================
FAIL: test_f7_off_import_guard_covers_all_overlay_modules (__main__.Round3Tests.test_f7_off_import_guard_covers_all_overlay_modules) (module=14)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round3.py", line 196, in test_f7_off_import_guard_covers_all_overlay_modules
    with self.subTest(module=i),self.assertRaisesRegex(AssertionError,'OFF attempted'):
                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: AssertionError not raised

======================================================================
FAIL: test_f7_off_import_guard_covers_all_overlay_modules (__main__.Round3Tests.test_f7_off_import_guard_covers_all_overlay_modules) (module=15)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round3.py", line 196, in test_f7_off_import_guard_covers_all_overlay_modules
    with self.subTest(module=i),self.assertRaisesRegex(AssertionError,'OFF attempted'):
                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: AssertionError not raised

======================================================================
FAIL: test_f7_off_import_guard_covers_all_overlay_modules (__main__.Round3Tests.test_f7_off_import_guard_covers_all_overlay_modules) (module=16)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round3.py", line 196, in test_f7_off_import_guard_covers_all_overlay_modules
    with self.subTest(module=i),self.assertRaisesRegex(AssertionError,'OFF attempted'):
                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: AssertionError not raised

======================================================================
FAIL: test_f7_off_import_guard_covers_all_overlay_modules (__main__.Round3Tests.test_f7_off_import_guard_covers_all_overlay_modules) (module=17)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round3.py", line 196, in test_f7_off_import_guard_covers_all_overlay_modules
    with self.subTest(module=i),self.assertRaisesRegex(AssertionError,'OFF attempted'):
                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: AssertionError not raised

======================================================================
FAIL: test_f7_off_import_guard_covers_all_overlay_modules (__main__.Round3Tests.test_f7_off_import_guard_covers_all_overlay_modules) (module=18)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round3.py", line 196, in test_f7_off_import_guard_covers_all_overlay_modules
    with self.subTest(module=i),self.assertRaisesRegex(AssertionError,'OFF attempted'):
                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: AssertionError not raised

----------------------------------------------------------------------
Ran 9 tests in 0.732s

FAILED (failures=15)
```

Command: `bash work/cpu.sh work/run_checks.py  # operator3_before; exact environment/argv in runner`

Exact output ([checks/operator3_before.txt](checks/operator3_before.txt)):

```text
test_f2_a12_payload_through_a4_actions_and_nested_return (__main__.OperatorTests.test_f2_a12_payload_through_a4_actions_and_nested_return) ... FAIL
test_f2_operator_memory_bound_includes_cache_only_when_enabled (__main__.OperatorTests.test_f2_operator_memory_bound_includes_cache_only_when_enabled) ... FAIL

======================================================================
FAIL: test_f2_a12_payload_through_a4_actions_and_nested_return (__main__.OperatorTests.test_f2_a12_payload_through_a4_actions_and_nested_return)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_operator_round3.py", line 235, in test_f2_a12_payload_through_a4_actions_and_nested_return
    self.assertEqual(result.returncode,0,result.stdout+result.stderr)
AssertionError: 1 != 0 : Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_operator_round3.py", line 243, in <module>
    if len(sys.argv)>1 and sys.argv[1]=='--child':child(Path(sys.argv[2]),int(sys.argv[3]))
                                                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_operator_round3.py", line 138, in child
    boot.main();main_job.assert_called_once_with(root)
    ^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/8ff6b15ac5a0457f86dd93df5638cceb/0.py", line 44, in main
    job.main(root)
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/unittest/mock.py", line 1139, in __call__
    return self._mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/unittest/mock.py", line 1143, in _mock_call
    return self._execute_mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/unittest/mock.py", line 1204, in _execute_mock_call
    result = effect(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_operator_round3.py", line 122, in run_job
    job.checked_run([sys.executable,'-I','-s','-B',str(root/'a/5.py'),str(cfgpath)])
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/8ff6b15ac5a0457f86dd93df5638cceb/0.py", line 18, in dispatch
    return original(argv,*args,**kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/unittest/mock.py", line 1139, in __call__
    return self._mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/unittest/mock.py", line 1143, in _mock_call
    return self._execute_mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/unittest/mock.py", line 1204, in _execute_mock_call
    result = effect(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_operator_round3.py", line 114, in dispatch
    try:operator.main()
        ^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/8ff6b15ac5a0457f86dd93df5638cceb/7.py", line 139, in main
    result=run(cfg['config'],cfg['end'],os.environ['CUDA_VISIBLE_DEVICES'].split(','))
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/unittest/mock.py", line 1139, in __call__
    return self._mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/unittest/mock.py", line 1143, in _mock_call
    return self._execute_mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/unittest/mock.py", line 1204, in _execute_mock_call
    result = effect(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_operator_round3.py", line 113, in <lambda>
    with patch.object(sys,'argv',argv[-2:]),patch.object(operator,'run',side_effect=lambda config,end,cards:actual_operator(config,end,['cpu-fixture'])):
                                                                                                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/8ff6b15ac5a0457f86dd93df5638cceb/7.py", line 87, in run
    result=(runner or execute)(cfg,cards,end,prefix=cfg['prefix'])
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/unittest/mock.py", line 1139, in __call__
    return self._mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/unittest/mock.py", line 1143, in _mock_call
    return self._execute_mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/unittest/mock.py", line 1204, in _execute_mock_call
    result = effect(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_operator_round3.py", line 82, in execute_sequence
    assert Path(launch.__file__).read_bytes()==(p/'u0/a4.py').read_bytes(),'Operator overlay not active'
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Operator overlay not active


======================================================================
FAIL: test_f2_operator_memory_bound_includes_cache_only_when_enabled (__main__.OperatorTests.test_f2_operator_memory_bound_includes_cache_only_when_enabled)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_operator_round3.py", line 161, in test_f2_operator_memory_bound_includes_cache_only_when_enabled
    self.assertIn('read_extensions',__import__('inspect').signature(operator.memory_bound).parameters,
AssertionError: 'read_extensions' not found in mappingproxy(OrderedDict({'captures': <Parameter "captures=(84,)">, 'allocation_bytes': <Parameter "allocation_bytes=214748364800">})) : Operator omits read cache memory

----------------------------------------------------------------------
Ran 2 tests in 8.005s

FAILED (failures=2)
```

Command: `bash work/cpu.sh work/run_checks.py  # lock3_before; exact environment/argv in runner`

Exact output ([checks/lock3_before.txt](checks/lock3_before.txt)):

```text
test_deadline_recovery_keeps_writer_lock (lock_behavior.RunnerTests.test_deadline_recovery_keeps_writer_lock) ... FAIL
test_type_deadline_recovery_holds_writer_lock (__main__.TypeLockTests.test_type_deadline_recovery_holds_writer_lock) ... FAIL

======================================================================
FAIL: test_deadline_recovery_keeps_writer_lock (lock_behavior.RunnerTests.test_deadline_recovery_keeps_writer_lock)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_read_journal.py", line 137, in test_deadline_recovery_keeps_writer_lock
    self.assertGreaterEqual(len(checks),2)
AssertionError: 1 not greater than or equal to 2

======================================================================
FAIL: test_type_deadline_recovery_holds_writer_lock (__main__.TypeLockTests.test_type_deadline_recovery_holds_writer_lock)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/review-before/src/h1eval/h10/launch.py", line 371, in run_types
    result=run(part,make_real=make_real,factory_options=factory_options,generators=generators)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/review-before/src/h1eval/h10/launch.py", line 324, in run
    commit_record(stream, row)
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/unittest/mock.py", line 1139, in __call__
    return self._mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/unittest/mock.py", line 1143, in _mock_call
    return self._execute_mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/unittest/mock.py", line 1204, in _execute_mock_call
    result = effect(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_lock_round3.py", line 30, in interrupted
    if Path(stream.name).name=='items.jsonl':raise fixtures.launch.ReadDeadline()
                                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
h1eval.h10.launch.ReadDeadline

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_lock_round3.py", line 33, in test_type_deadline_recovery_holds_writer_lock
    with self.assertRaises(fixtures.launch.ReadDeadline):fixtures.launch.run_types(args,make_real=self.make_real)
                                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/review-before/src/h1eval/h10/launch.py", line 375, in run_types
    rows=AtomicJournal(root).recover()
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_lock_round3.py", line 26, in checked
    with self.assertRaises(BlockingIOError):fcntl.flock(other,fcntl.LOCK_EX|fcntl.LOCK_NB)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: BlockingIOError not raised

----------------------------------------------------------------------
Ran 2 tests in 0.012s

FAILED (failures=2)
```

Command: `bash work/cpu.sh work/run_checks.py  # round4_before; exact environment/argv in runner`

Exact output ([checks/round4_before.txt](checks/round4_before.txt)):

```text
test_f1_bound_package_preserves_a4_contract_and_binding (__main__.Round4Tests.test_f1_bound_package_preserves_a4_contract_and_binding) ... FAIL
test_f2_bound_real_job_and_rehearsal_memory (__main__.Round4Tests.test_f2_bound_real_job_and_rehearsal_memory) ... FAIL
test_f3_cache_only_return_refuses_unverified_journals (__main__.Round4Tests.test_f3_cache_only_return_refuses_unverified_journals) ... 
  test_f3_cache_only_return_refuses_unverified_journals (__main__.Round4Tests.test_f3_cache_only_return_refuses_unverified_journals) (verified=False) ... FAIL
  test_f3_cache_only_return_refuses_unverified_journals (__main__.Round4Tests.test_f3_cache_only_return_refuses_unverified_journals) (verified=None) ... FAIL
  test_f3_cache_only_return_refuses_unverified_journals (__main__.Round4Tests.test_f3_cache_only_return_refuses_unverified_journals) (verified=0) ... FAIL
  test_f3_cache_only_return_refuses_unverified_journals (__main__.Round4Tests.test_f3_cache_only_return_refuses_unverified_journals) (verified=1) ... FAIL
  test_f3_cache_only_return_refuses_unverified_journals (__main__.Round4Tests.test_f3_cache_only_return_refuses_unverified_journals) (verified='true') ... FAIL
test_f9_off_builder_guard_and_processor_only (__main__.Round4Tests.test_f9_off_builder_guard_and_processor_only) ... skipped 'New route default and processor-only checks apply to delivered builder'

======================================================================
FAIL: test_f1_bound_package_preserves_a4_contract_and_binding (__main__.Round4Tests.test_f1_bound_package_preserves_a4_contract_and_binding)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 300, in test_f1_bound_package_preserves_a4_contract_and_binding
    self.assertEqual(cfg.get(key),old[key],key)
AssertionError: None != 'candidates_argmax' : stage1_select_rule

======================================================================
FAIL: test_f2_bound_real_job_and_rehearsal_memory (__main__.Round4Tests.test_f2_bound_real_job_and_rehearsal_memory)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 343, in test_f2_bound_real_job_and_rehearsal_memory
    self.assertEqual(result.returncode,0,str(root)+'\n'+result.stdout+result.stderr+logs+'\n'+'\n'.join(p.read_text() for p in (root/'job/sandbox/r').glob('FAILED.json')))
AssertionError: 1 != 0 : /scratch/jjyeung/orch_n30/so_read/work/test-artifacts/e444dd03f48c46edb6c7d0f886e0b15b
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 436, in <module>
    elif len(sys.argv)>1 and sys.argv[1]=='--control':control_child(Path(sys.argv[2]),Path(sys.argv[3]),sys.argv[4])
                                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 284, in control_child
    node.main()
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/e444dd03f48c46edb6c7d0f886e0b15b/built/package/a/5.py", line 147, in main
    raise ValueError('Prepared default settings differ')
ValueError: Prepared default settings differ
PASS action 0 rehearsal False



======================================================================
FAIL: test_f3_cache_only_return_refuses_unverified_journals (__main__.Round4Tests.test_f3_cache_only_return_refuses_unverified_journals) (verified=False)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 412, in test_f3_cache_only_return_refuses_unverified_journals
    with self.subTest(verified=value),self.assertRaisesRegex(ValueError,'Unverified weight journal'):validate()
                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f3_cache_only_return_refuses_unverified_journals (__main__.Round4Tests.test_f3_cache_only_return_refuses_unverified_journals) (verified=None)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 412, in test_f3_cache_only_return_refuses_unverified_journals
    with self.subTest(verified=value),self.assertRaisesRegex(ValueError,'Unverified weight journal'):validate()
                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f3_cache_only_return_refuses_unverified_journals (__main__.Round4Tests.test_f3_cache_only_return_refuses_unverified_journals) (verified=0)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 412, in test_f3_cache_only_return_refuses_unverified_journals
    with self.subTest(verified=value),self.assertRaisesRegex(ValueError,'Unverified weight journal'):validate()
                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f3_cache_only_return_refuses_unverified_journals (__main__.Round4Tests.test_f3_cache_only_return_refuses_unverified_journals) (verified=1)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 412, in test_f3_cache_only_return_refuses_unverified_journals
    with self.subTest(verified=value),self.assertRaisesRegex(ValueError,'Unverified weight journal'):validate()
                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f3_cache_only_return_refuses_unverified_journals (__main__.Round4Tests.test_f3_cache_only_return_refuses_unverified_journals) (verified='true')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 412, in test_f3_cache_only_return_refuses_unverified_journals
    with self.subTest(verified=value),self.assertRaisesRegex(ValueError,'Unverified weight journal'):validate()
                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 4 tests in 8.876s

FAILED (failures=7, skipped=1)
```

Command: `bash work/cpu.sh work/run_checks.py  # node4_before; exact environment/argv in runner`

Exact output ([checks/node4_before.txt](checks/node4_before.txt)):

```text
test_f2_bound_real_job_and_rehearsal_memory (__main__.Round4Tests.test_f2_bound_real_job_and_rehearsal_memory) ... FAIL

======================================================================
FAIL: test_f2_bound_real_job_and_rehearsal_memory (__main__.Round4Tests.test_f2_bound_real_job_and_rehearsal_memory)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 345, in test_f2_bound_real_job_and_rehearsal_memory
    self.assertEqual(proof['memory'].get('read_cache_bytes'),12*1024**3)
AssertionError: None != 12884901888

----------------------------------------------------------------------
Ran 1 test in 8.762s

FAILED (failures=1)
```

Command: `bash work/cpu.sh work/run_checks.py  # round5_before; exact environment/argv in runner`

Exact output ([checks/round5_before.txt](checks/round5_before.txt)):

```text
test_f1_batch_wrapper_and_real_bundle_guard (__main__.Round5Tests.test_f1_batch_wrapper_and_real_bundle_guard) ... FAIL
test_f2_pins_refuse_before_copy (__main__.Round5Tests.test_f2_pins_refuse_before_copy) ... 
  test_f2_pins_refuse_before_copy (__main__.Round5Tests.test_f2_pins_refuse_before_copy) (operator='tower_sequence.py') ... FAIL
  test_f2_pins_refuse_before_copy (__main__.Round5Tests.test_f2_pins_refuse_before_copy) (operator='unpack_return.py') ... FAIL
  test_f2_pins_refuse_before_copy (__main__.Round5Tests.test_f2_pins_refuse_before_copy) (operator='package/a/5.py') ... FAIL
  test_f2_pins_refuse_before_copy (__main__.Round5Tests.test_f2_pins_refuse_before_copy) (base='self-consistent') ... FAIL
  test_f2_pins_refuse_before_copy (__main__.Round5Tests.test_f2_pins_refuse_before_copy) (extension='changed') ... FAIL
test_f3_binding_derivation_and_operations (__main__.Round5Tests.test_f3_binding_derivation_and_operations) ... FAIL
test_f3_submit_pool_and_proof_refusals (__main__.Round5Tests.test_f3_submit_pool_and_proof_refusals) ... FAIL
test_f4_gate_pins_adopted_settings_and_profile (__main__.Round5Tests.test_f4_gate_pins_adopted_settings_and_profile) ... FAIL
test_f5_forecast_identifies_both_reads (__main__.Round5Tests.test_f5_forecast_identifies_both_reads) ... FAIL
test_f7_refused_unpack_not_scoreable (__main__.Round5Tests.test_f7_refused_unpack_not_scoreable) ... FAIL

======================================================================
FAIL: test_f1_batch_wrapper_and_real_bundle_guard (__main__.Round5Tests.test_f1_batch_wrapper_and_real_bundle_guard)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round5.py", line 66, in test_f1_batch_wrapper_and_real_bundle_guard
    self.assertIn('#SBATCH --exclude=orchard-community-2\n',batch)
AssertionError: '#SBATCH --exclude=orchard-community-2\n' not found in "#!/bin/bash\nset -euo pipefail\nexec /usr/bin/python3 -I -s -B - <<'A'\nimport hashlib,io,json,os,sys,tarfile\nfrom pathlib import Path,PurePosixPath\nj=os.environ.get('SLURM_JOB_ID','')\nif not j.isdigit():raise ValueError('Allocation required')\nb=bytes.fromhex('1f8b08000000000002ffed5aeb6fe3b811dfcffe2b74e907490e5791df89732ab0ddcdb55bdc3eb0d93da0300c4196685b1b5952453a8f2ef67fefcc907a5876b2298a5e51d444625b22391cce0c677e43d275be8a2c7df11f2d2e94b1ebd2b7bbffed0e8693eab77a3f9e4c062f0cf7c5ef50b64206050cf9e2ffb37ceb18c6491e3c245910f98b07c9c5c9d4180dce4793d19035ebc43ae88fc6507912b8ee7018f1f3413fb8702f78ff7c11f6cf8761df0d974b3e588c7bfde16419f607e7e7c3853be95d2cdc68723e192e06e3c1240cc7bd13453709d206d1913b5c5e2c7978310ec73c08076134ec0fc3e562391c0c07e7cbd1a2d75f8edcf1c578142d06e164783119bad1853b9ab88be1797f3150446576c353e271e1f6fa83e1683c39bf38e97cefbc389647d6a6933ffcc7c7787afd0f87bd717bfd0f47c7f5ffbb949393938f0517bcb8e5465e64d1369471961a41b48985805fcc00f9ace274c58c2049b230a0ea45b64d2301afd2c880dedb44c297dc16a903f43af126cf0a69ac03b14ee205c300c340c8cb38e14c3c88ceb2c836461e48ac3574e38ff0d8e97422be3436c10df7a358408b706d15592699911531301124f02be74520b342fb0e7bda31885e5684eba088fc75cf75c26cb3012e356968d831907045332856b7ac0b9f8275bb3777f803e9187f303ea4c9034c059c53c80db986ff2c7f99f05b9e34a75f12e2c525088de741a1dea338eeb2e2861702c5f660e4719af2c801d2f1d248784a23db7ff4fad4141f662ffbd3b9e7cd842c68aa67667036823569daacf9aa4761dab4e7c8a6112e571e3e3be89985b5d7ca2938786cc9efa565dbd82110a06189fd6666401a3661d09ea63533c32c5dc62b733e335be28566ad37d8677fc0bb22965c8d488c45db4d2e2ca0adc687d9436fdd6d42d3fba94d98666614412cb8f15b906cf95551648565fe094c2de151a57803f49caee045b094bc403917729b9b6a9e20516fd625c14e5ff6e70d194e9e102a7455e65bd9d94113e994ad4afd57061ba7161a1012f6d0922d307387b8e8cdedcb7cbb48e2f080c6dcc3fa0279143c5284cc3358955f7928cfd0a8b7692c1fcebe7e7de0db747596ddac27a67d6699416fe48799f483dc3c5583cd4c0a85e61cc869e5ebe5e828695b961a059990ab7f943c100200269c35bf8fe21517c091e7953477b1800972bb8be5dad06bdb010da56db2303ad6a37297a0bb8d11a7e5335a459a4963e3a4c1863ba44881042db3b198cf4c7b0ae629e374cb773ac50207b56cd099613a8e899449648a9eede4486fba6f505f52112cb91166115756937b4a1db979a6fa5ee6d899a7d2d9dc447161a907e17d2eb69cf1fb58483fbba12750aeb67d25399883036a2c609111771b2557a556b009f47a4e9ca2422cb7618c60bff6be232b3dd8d76cf13c2fd75a525e7bd175d0c767cb1d532c15169c8567af3f7e396c925aea16754743009b8accb9110b03c540ee8cea9c159796b9a035ebafb6c8ab6e6c3fd618445b3cf882ff7dcbd3903fd1bc3240745e8fdb64599afd006cee74aac1274ca2d1304ef3ad14d81445578ba6741507a9effbcc434eb3d54dcd7dc33759f160b26fdf6d2db940c40226ef7986b98cef79e4af0612a9e45c980747d724e6aa3f8c1bf21c3dbc8f15fe06427ac235c59909c41e11d12e19116ca07f20b605df807efc02b41317a55a7e0912c19f4165194b512bd23eb0167fd926890156074e9d8737e05821852804ca196cdea1972082629b7a075041ab096b43034584bc33b6b7c15d831dfb3e2e71dff73cd3f7b1d2f7cda972e1ff8769c2e4bf8eff7b93e178b087ff27ee11ffff4ef8ff4309accad545915ade65b070b324901c313e840a0af61064b39437c07013f113d28730c764bce14c038e27e0fea72fbf5e5d7b9619820789231849f8009a36c1bdc9ecceeb0f5fde7f86dadec865cdff012cecebd77fb97a039d3d0ba2e8c066f0e9d2678f3efbf43984c045f82ce2222ce21ca62820948737c18a135a53606e16c5a104bcb7f10033ddf1c264e033b9f066660a3335114342871e04a8046018389a847b873816c12df7b3bbd48fc0ffae3df291ac7692545aded93321a6b0475cb6a7bdf55efd2d2fe2e5831f47d064de1e413ee4d875c04016accf8673c02b39f00d78720c929b2b89081e00a4f609b958a81a768b4ef919c91475213c405086c01000468a010d5441954d08f19347231c08019fa0951147106500db3623c01e778a779570714be52ccf60f9c3a737579f18682c4be330483a06c458aed0b5a201117c2b21ee035abe145c02d45c892644da695a3680c6fb18493552c12f23950589691fc4a0a55a8cb29d41d8c32c6120ef731fe9f3c269194085f8342708b1c930ca179ddd47abfcc1ca28aea02b715cd6c1c4f6cc1ca011823e58f2b4500f4c639bdea468f207fa22e085190aafb9fa4a21ea5588022f35efd1324460e655ad9a288d29685655aac7ba1ad7411bfe56ea6d0334b08602964f8f9163f3885126004be0caf34aef0253f883f1d7eb0fef21b103402b6116c62abee520714c3b17093712307fdc2fc02d9454aa5d00f49eb829b2e10ad508c8ffab5936ccaa912897d5361a606369a2a59e01a89201f89ae0eced9babf79fdf7efe9b02a3acead5d18627bc6fdf3b347ecc704ea83a9e0223307b6ed12c699f83f2d4166d9284798629498c30375c673025ef5bb75b99cf21139922d5c3c603ed775ca239ddf389ddeeb71b45e1664e7cdf20cb7b28d664e6e34ef04065057abf8338c851e90caf9aadcebc2ff71da19a374a60a7aed5ffd3d5ab377e4b1d64c0dd6ea915b22d0f14a1c5571965e9882c3d146d916805cee2398a5c3db1d22f4dcb44d166b5ffa197c8b25d4a14a212189c8f0d55ad5231bd2d356b33039495e53ea6a7cd56d5d4ae3f7ff868d634050c06a99cdad632a794029b102d8181990e98a0690a99f846c74c93e210bc20e73b934abbe44b94c1a8faf9bc1ee75fb3adba1bcc650331384ecd69efdc7599a9e27afdb20f2fbbdd5d97a845ffbd53c100ad0015630abee6412150478f47194839525e94de18f7288a2c614a50880ac4f32253bd785b91ed52edac42902fd774b85ca104757b07ec722368e3c9901ed172e234e2f716ede96909cfdcb9b62f648fb6e43ab45126bc06ab1619af22ec411b86bd3dc9889ee756fe92c41d48f8b58cd358acfdc583d72703d6bb4c486c861f9a15f3e54b3216fbb40769b13698279b2b53d2edc99c9e6caea6a99b33d3f99a4126d714c0d3cce1845ed25a502470411c86067b4ba4a6dbc60a87c629972d0eb38b1c0e5bb8e751d00587503be37f6f9c9a5f456eb6e7665184e0c97ed8b0e97da1cfd3111e66f03401da7d454b77823ce769a46c517b4f85679bfa6464bbb4335b8135c5e72ed4a5e87d750f03236ae1e0040d2560cc6740c4865c43585fad699b1f464b0c324e4364e10d976a6753c8edc2b8e3f16a2d318ad372c63d58c0fdd2d940c37225abed60d580f82c2baee13be1ef830d87dc2a44e4acde4bf40a7b50af82766410184112b5f689e10a8881c436d09c3c039d6cc05a9456b6f8ca222e61860cbc57c4563c038b2d201051ca926e93a44c56c86718d0c1a13afcb8c427ece7e1073d4571b04a3321e31081c5250e59aa08aad19ea87d6b8a164acec7d1bc24d82ca2c0e806539aae23792a0036ce7a0eeb3bace7bace9ccc92644d227480304cc0520270aef1eb430a11c7f7718ebe0fa807be6db6d31ae5c4cccfa8be3f0f3e9b4c4700ca1abcf7e042747bcb6ca0ea523cceb2c0fda010209e6c751df495a0d4138e820b2af16b6bb6903a48fd360e312bccb73f4ee744b019f8646a9e66df66ca3001a0560a389475e2875df1e32843551cd024eb758baa02c7afb44bfdf6eb1465b5d8ee3da5a07ff02213569f8dce6d86bb649e09b662d349910e936aa5ea28b94df57a6760132a4630151549ea2c4c80450f37031cfc78461485274c67f83d0fb798673e3b1bc5c335620032cd1e1e0960e6422f60ae07b34e4a8560a42094c983dad410225ea5e01eb09f69ff283063fa7db90ce2645b282bd3619a20accbc8743027442158f61f3d90d14b4428c8dd73634c95604f176079371d75f65783c5ca777a96162410d7d2b3310c6aada07e6016cbf85ef952f55b05473d9b677adf6e57b5a7851b2f75ef99a9050139a3167e59011a03f720a186d65229b0bd7e977a862a25ab414f4af20481a253673a7fb9831685f28c58ada740fccc4ca4807149854e3d7ce441466615353f787c5113008a4a1630f82149d464aa5f75b849abeabad6f3523af4d96e0088eaecf699bc200ff64e306beff254c30549d2a473804c296ffdad335efa04b7b3dad0c196965fb5e9f298755e7f79f7eed5a732e1d173abcf45f50b7d2a4a47013e5d15b0ba0c16550e8dc09cacf321b39bd709d4d9990738bddb73fbc36e77c0887b1f700b440c6821f4769a7aadd21cd5c94583d0a753ad3ed3fdc6d4142dd96ad7d12985daed90a505bb3f7bed663f7bbd71c92459e29e63799b82778ed596a9413db524d4a5099360c92f78b26340ac52b81c5cd0d408c03543b035c643230734432649db6a03bc2d0008a73056050026c7b8423c62103f482c47d002f9645000b55bbc7bb0c8209e2e01284a4d4c1142a0b3040de83aa08b040da55fc43710a03c6b3cec5e9c8e87a7833efc75473dfa3b1df54efb76f7bc83a3f95a951eb43f55c2e877d075a393f751af77c030f780921655b5aa779654691029a340a97494761b23b4ec9e9ae5c956f8203350329e4ca95e567a3ab09fe809f8109a6ea3157fb4c7e9de044ef78da4e192ea8d9572227891a0ba2100f3a4b33c6fff18ef871061977775165709c8658f1dcee9458223699654177f0bfeac406db528e70f720d3ca0d1acabd37fbfa961ad5d56cbbba41c66790cdc0c5a24f784a8b9de7b8fa777be520b3568bb831d47b53b46b76b7d33dbba31f796fb77159e767c82c14142c6b7ef768b249e5496ce74cf56ccf9cf7becb5fdacddd9f17a79912d9a5bd4272727afe98453251b328853ed00c82b1002867568607207190d7a20a5617cb87ef58e4e599e8986febd2dec7a43f8b15db5f94fa5a11ebe5c01d606dc346fecd0ae75b529d7d15bde6ab7b2b56bded2577d7a4c37485a1be3b5c6ab5d985afd0cef92c093401010e45ea3aada11b771784c7969634ab7af6b1d02da78bc416603e1a362bd7264cd20459b637b510706a71049306d372a7635b91f06de0a16bebb7af7a10ac01a893502a0c65478ee7e483b1f2b952a9df0fb90f348907b2cc314dd95b0f700ffee4da7d60db4bd3b4f3b767599ebd396e5cec6407d23663675e7ea0a5c7e662ef42d2df8290bcecb2774ae682bcdeb6acf3099c3976e80f6d6a52b37caa682f3d280f076dc6d20295fd23f2d9ee25e7f756af28355080349f016e802422e84ba04d339fcfaa0e04496dc72cbd65790ec72dae564f5cea4cae19fe711768cab75dfafb6b14f577fb97af5e9fad5af9575559ba0cd3e25f03fa0091d947c7d0bc49eee7ac31d2ad59dbb6a4b2413d52aa1ccb2d99cd1138072f8990987a7b77191a533f3f59737affcdfde5ebffdd3af57fe9babdfdebebeba066e449ec4c00f2315ab6570fd2024df5cddc3fbdee1bc45ad71fb7849e4588ee5588ee5588ee5588ee5588ee5588ee5588ee5588ee5588ee5588ee5588ee5588ee5588ee5588ee558fef7ca3f017de49de300500000')\nr=Path('/tmp')/('a'+j+'ab0123456789')\nr.mkdir(mode=0o700)\nwith tarfile.open(fileobj=io.BytesIO(b)) as a:\n    for e in a:\n        n=PurePosixPath(e.name)\n        if n.is_absolute() or '..' in n.parts or not e.isfile():raise ValueError('Unsafe input')\n        p=r/e.name;p.parent.mkdir(parents=True,exist_ok=True)\n        with a.extractfile(e) as i,p.open('xb') as o:o.write(i.read())\nos.chdir(r)\nos.execv(sys.executable,[sys.executable,'-I','-s','-B',str(r/'0.py'),str(r)])\nA\n"

======================================================================
FAIL: test_f2_pins_refuse_before_copy (__main__.Round5Tests.test_f2_pins_refuse_before_copy) (operator='tower_sequence.py')
----------------------------------------------------------------------
ReachedCopy: Unpinned input reached copy/build

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round5.py", line 105, in test_f2_pins_refuse_before_copy
    with self.assertRaisesRegex(ValueError,'operator pin'):attempt()
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: "operator pin" does not match "Unpinned input reached copy/build"

======================================================================
FAIL: test_f2_pins_refuse_before_copy (__main__.Round5Tests.test_f2_pins_refuse_before_copy) (operator='unpack_return.py')
----------------------------------------------------------------------
ReachedCopy: Unpinned input reached copy/build

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round5.py", line 105, in test_f2_pins_refuse_before_copy
    with self.assertRaisesRegex(ValueError,'operator pin'):attempt()
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: "operator pin" does not match "Unpinned input reached copy/build"

======================================================================
FAIL: test_f2_pins_refuse_before_copy (__main__.Round5Tests.test_f2_pins_refuse_before_copy) (operator='package/a/5.py')
----------------------------------------------------------------------
ReachedCopy: Unpinned input reached copy/build

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round5.py", line 105, in test_f2_pins_refuse_before_copy
    with self.assertRaisesRegex(ValueError,'operator pin'):attempt()
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: "operator pin" does not match "Unpinned input reached copy/build"

======================================================================
FAIL: test_f2_pins_refuse_before_copy (__main__.Round5Tests.test_f2_pins_refuse_before_copy) (base='self-consistent')
----------------------------------------------------------------------
ReachedCopy: Unpinned input reached copy/build

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round5.py", line 117, in test_f2_pins_refuse_before_copy
    with self.subTest(base='self-consistent'),self.assertRaisesRegex(ValueError,'reviewed A4 payload'):attempt()
                                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: "reviewed A4 payload" does not match "Unpinned input reached copy/build"

======================================================================
FAIL: test_f2_pins_refuse_before_copy (__main__.Round5Tests.test_f2_pins_refuse_before_copy) (extension='changed')
----------------------------------------------------------------------
ReachedCopy: Unpinned input reached copy/build

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round5.py", line 125, in test_f2_pins_refuse_before_copy
    with self.subTest(extension='changed'),self.assertRaisesRegex(ValueError,'Extension inventory'):attempt(source=source)
                                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: "Extension inventory" does not match "Unpinned input reached copy/build"

======================================================================
FAIL: test_f3_binding_derivation_and_operations (__main__.Round5Tests.test_f3_binding_derivation_and_operations)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round5.py", line 138, in test_f3_binding_derivation_and_operations
    helper=self.helpers();root=fresh();binding=copy.deepcopy(self.binding)
           ^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round5.py", line 61, in helpers
    self.assertTrue((E/'a20.py').is_file(),'Missing executable binding/operation/gate helper')
AssertionError: False is not true : Missing executable binding/operation/gate helper

======================================================================
FAIL: test_f3_submit_pool_and_proof_refusals (__main__.Round5Tests.test_f3_submit_pool_and_proof_refusals)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round5.py", line 169, in test_f3_submit_pool_and_proof_refusals
    helper=self.helpers();root=fresh();package=root/'package';(package/'a/c').mkdir(parents=True)
           ^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round5.py", line 61, in helpers
    self.assertTrue((E/'a20.py').is_file(),'Missing executable binding/operation/gate helper')
AssertionError: False is not true : Missing executable binding/operation/gate helper

======================================================================
FAIL: test_f4_gate_pins_adopted_settings_and_profile (__main__.Round5Tests.test_f4_gate_pins_adopted_settings_and_profile)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round5.py", line 199, in test_f4_gate_pins_adopted_settings_and_profile
    self.assertTrue(hasattr(kit,'validate_profile'),'GPU gate accepts an unbound read profile')
AssertionError: False is not true : GPU gate accepts an unbound read profile

======================================================================
FAIL: test_f5_forecast_identifies_both_reads (__main__.Round5Tests.test_f5_forecast_identifies_both_reads)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round5.py", line 227, in test_f5_forecast_identifies_both_reads
    self.assertIn('Package D',text);self.assertIn('636-item',text)
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'Package D' not found in 'VERDICT: DONE The round-4 fixes pass CPU verification; adopt only after the GPU byte gate.\n\nMeasured: **95 workspace tests and 14 fresh-application tests pass**. Five patches apply exactly; original reader files and complete OFF output bytes remain unchanged. The backup is out_round4/. The CPU fixture completes 636 synthetic reads with five verified ordinary journals through real A4 preparation, rehearsal, bootstrap and job.main.\n\nMeasured existing distance time is **23.60 s/item**. Estimated 580-item elapsed time, crediting no cache saving, is **3 h 50 min** on one card. Ideal two/four-shard estimates are **1 h 56 min / 59 min**, excluding staging, queues, preemption and scene imbalance; they require an undelivered multi-card operator. Measured CPU guard/cache overhead on a 268M-parameter bf16 stub is **25.9 ms/call**. This is not a GPU saving.\n\n## Review round 4: finding -> fix -> test\n\n| Finding | Fix and test |\n|---|---|\n| 1. Incomplete step-600 package | a19 uses A4 build_r1-style post-processing, preserving 8.py, run keys and admission. It requires the reviewed target export/whole-archive binding and seals the fill helper. Wrong binding/receipt checks fail; the documented old build fails before. |\n| 2. Adoption profile not exercised | Real job.main constructs actions 0/1 from packaged 9.json. Real 7.py rehearsal produces MEMORY.json with 12 GiB cache allowance. Stub workers produce five verified ordinary journals. The old CPU-proof helper fails the allowance test. |\n| 3. Unchecked cache-only return | ON unpack rejects non-true WEIGHTS receipts. Invalid-value regressions fail before/pass after; real authenticated partial-return unpack rejects an unchecked journal. |\n| 9. README nits | Commands use explicit delivery/source roots; kit pin is A4-only; README states what bootstrap admission actually checks. |\n\n**Step 600: one card, caches only, general/no-requeue.** Apply 01–03 to a full A4/src copy and 04–05 to an A4 operator copy. Define the local roots using [README](kit_parity50/README.md), then build:\n\n```bash\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a19.py" \\\n  --enable-extensions --base-operator "$LOCAL/a4" --source-root "$EXT_SOURCE" \\\n  --export-binding "$STEP600_BINDING" --token "$PACKAGE_TOKEN" --out "$LOCAL/step600"\n```\n\nThe required binding includes target run/step/object/preparation identities and archive_bytes/archive_sha256. The CPU task has no real step-600 export; its test binding is synthetic. The generic a12 operator build is refused. Add --processor-only for the 4 GiB processor cache; otherwise the cache allowance is 12 GiB. Both disable atomic journals and sharding. A4\'s fixed schedule remains 636 items; changing it requires a separately reviewed operator/proof.\n\nUse the generated fill helper, regenerate CPU proof through package/a/5.py, and retain the generated tower_sequence.py beside unpack_return.py. Exact fill/proof commands are in README. Require read_cache_bytes in MEMORY/CPU.json, along with payload/plan/inputs/operator binding and fits=true. The unchanged 0.py admission does not independently require that field. Cache-only returns retain ordinary journals; ON unpack refuses unchecked weights even on partial returns.\n\nBefore adoption, require **zero answer/trace byte differences**, useful cache hits, net worker_wall_seconds savings, and full-process host/GPU/envelope headroom. ON\'s eager SAM construction and boundary hashing need the GPU gate. The sample overstates reuse. Keep models frozen; persistent raw writes fail at boundaries, while restored-between-boundary writes are unsupported. Hard kills can require fresh journals. Validate persistent-storage requeue before any preempt/sharded use. Stage source trees as archives and run the kit with --public. No launch ran; preserve step-400 deliveries.\n\nExact commands, outputs, citations and limits: [REPORT](REPORT.md). Patch/base pins: [MANIFEST](patches/MANIFEST.json).\n'

======================================================================
FAIL: test_f7_refused_unpack_not_scoreable (__main__.Round5Tests.test_f7_refused_unpack_not_scoreable)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round5.py", line 234, in test_f7_refused_unpack_not_scoreable
    self.assertIn('refused unpack leaves',text.lower())
AssertionError: 'refused unpack leaves' not found in 'verdict: done the round-4 fixes pass cpu verification; adopt only after the gpu byte gate.\n\nmeasured: **95 workspace tests and 14 fresh-application tests pass**. five patches apply exactly; original reader files and complete off output bytes remain unchanged. the backup is out_round4/. the cpu fixture completes 636 synthetic reads with five verified ordinary journals through real a4 preparation, rehearsal, bootstrap and job.main.\n\nmeasured existing distance time is **23.60 s/item**. estimated 580-item elapsed time, crediting no cache saving, is **3 h 50 min** on one card. ideal two/four-shard estimates are **1 h 56 min / 59 min**, excluding staging, queues, preemption and scene imbalance; they require an undelivered multi-card operator. measured cpu guard/cache overhead on a 268m-parameter bf16 stub is **25.9 ms/call**. this is not a gpu saving.\n\n## review round 4: finding -> fix -> test\n\n| finding | fix and test |\n|---|---|\n| 1. incomplete step-600 package | a19 uses a4 build_r1-style post-processing, preserving 8.py, run keys and admission. it requires the reviewed target export/whole-archive binding and seals the fill helper. wrong binding/receipt checks fail; the documented old build fails before. |\n| 2. adoption profile not exercised | real job.main constructs actions 0/1 from packaged 9.json. real 7.py rehearsal produces memory.json with 12 gib cache allowance. stub workers produce five verified ordinary journals. the old cpu-proof helper fails the allowance test. |\n| 3. unchecked cache-only return | on unpack rejects non-true weights receipts. invalid-value regressions fail before/pass after; real authenticated partial-return unpack rejects an unchecked journal. |\n| 9. readme nits | commands use explicit delivery/source roots; kit pin is a4-only; readme states what bootstrap admission actually checks. |\n\n**step 600: one card, caches only, general/no-requeue.** apply 01–03 to a full a4/src copy and 04–05 to an a4 operator copy. define the local roots using [readme](kit_parity50/readme.md), then build:\n\n```bash\ncuda_visible_devices= nice -n 10 "$read_python" -i -s -b "$ext_source/u0/a19.py" \\\n  --enable-extensions --base-operator "$local/a4" --source-root "$ext_source" \\\n  --export-binding "$step600_binding" --token "$package_token" --out "$local/step600"\n```\n\nthe required binding includes target run/step/object/preparation identities and archive_bytes/archive_sha256. the cpu task has no real step-600 export; its test binding is synthetic. the generic a12 operator build is refused. add --processor-only for the 4 gib processor cache; otherwise the cache allowance is 12 gib. both disable atomic journals and sharding. a4\'s fixed schedule remains 636 items; changing it requires a separately reviewed operator/proof.\n\nuse the generated fill helper, regenerate cpu proof through package/a/5.py, and retain the generated tower_sequence.py beside unpack_return.py. exact fill/proof commands are in readme. require read_cache_bytes in memory/cpu.json, along with payload/plan/inputs/operator binding and fits=true. the unchanged 0.py admission does not independently require that field. cache-only returns retain ordinary journals; on unpack refuses unchecked weights even on partial returns.\n\nbefore adoption, require **zero answer/trace byte differences**, useful cache hits, net worker_wall_seconds savings, and full-process host/gpu/envelope headroom. on\'s eager sam construction and boundary hashing need the gpu gate. the sample overstates reuse. keep models frozen; persistent raw writes fail at boundaries, while restored-between-boundary writes are unsupported. hard kills can require fresh journals. validate persistent-storage requeue before any preempt/sharded use. stage source trees as archives and run the kit with --public. no launch ran; preserve step-400 deliveries.\n\nexact commands, outputs, citations and limits: [report](report.md). patch/base pins: [manifest](patches/manifest.json).\n'

----------------------------------------------------------------------
Ran 7 tests in 4.635s

FAILED (failures=11)
```

Command: `bash work/cpu.sh work/run_checks.py  # round6_before; exact environment/argv in runner`

Exact output ([checks/round6_before.txt](checks/round6_before.txt)):

```text
test_f1_readme_unpack_subprocess (__main__.Round6Tests.test_f1_readme_unpack_subprocess) ... FAIL
test_f2_detached_locked_fill_exit_success_and_failure (__main__.Round6Tests.test_f2_detached_locked_fill_exit_success_and_failure) ... FAIL
test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks) ... 
  test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks) (field='bundle_guard.batch_sha256') ... FAIL
  test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks) (field='bundle_guard.path') ... FAIL
  test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks) (field='entry_sequence.events') ... FAIL
  test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks) (field='entry_sequence.guard_target_sha256') ... FAIL
  test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks) (field='entry_sequence.requested_argv') ... FAIL
  test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks) (field='entry_sequence.dispatched_argv') ... FAIL
  test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks) (field='entry_sequence.batch_sha256') ... FAIL
  test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks) (field='memory.perception_memo_modules') ... FAIL
  test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks) (field='memory.sam_measurement_required') ... FAIL
test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks) ... FAIL
test_f4_every_copied_a4_member_pinned_before_output (__main__.Round6Tests.test_f4_every_copied_a4_member_pinned_before_output) ... 
  test_f4_every_copied_a4_member_pinned_before_output (__main__.Round6Tests.test_f4_every_copied_a4_member_pinned_before_output) (member='package/BATCH.sh') ... FAIL
  test_f4_every_copied_a4_member_pinned_before_output (__main__.Round6Tests.test_f4_every_copied_a4_member_pinned_before_output) (member='package/3.py') ... FAIL
  test_f4_every_copied_a4_member_pinned_before_output (__main__.Round6Tests.test_f4_every_copied_a4_member_pinned_before_output) (member='package/a/0.json') ... FAIL
  test_f4_every_copied_a4_member_pinned_before_output (__main__.Round6Tests.test_f4_every_copied_a4_member_pinned_before_output) (member='package/a/4.py') ... FAIL
  test_f4_every_copied_a4_member_pinned_before_output (__main__.Round6Tests.test_f4_every_copied_a4_member_pinned_before_output) (member='package/a/7.py') ... FAIL
  test_f4_every_copied_a4_member_pinned_before_output (__main__.Round6Tests.test_f4_every_copied_a4_member_pinned_before_output) (member='fetch_return.py') ... FAIL
test_f4_every_copied_a4_member_pinned_before_output (__main__.Round6Tests.test_f4_every_copied_a4_member_pinned_before_output) ... FAIL
test_f5_checkpoint_binding_and_runtime_recheck (__main__.Round6Tests.test_f5_checkpoint_binding_and_runtime_recheck) ... 
  test_f5_checkpoint_binding_and_runtime_recheck (__main__.Round6Tests.test_f5_checkpoint_binding_and_runtime_recheck) (asset='RESTORE.json') ... FAIL
  test_f5_checkpoint_binding_and_runtime_recheck (__main__.Round6Tests.test_f5_checkpoint_binding_and_runtime_recheck) (asset='binding.json') ... FAIL
test_f5_checkpoint_binding_and_runtime_recheck (__main__.Round6Tests.test_f5_checkpoint_binding_and_runtime_recheck) ... FAIL
test_f5_production_device_is_required (__main__.Round6Tests.test_f5_production_device_is_required) ... FAIL
test_f5_runtime_asset_recheck (__main__.Round6Tests.test_f5_runtime_asset_recheck) ... FAIL
test_info_done_whitespace (__main__.Round6Tests.test_info_done_whitespace) ... FAIL
test_info_submit_requires_successful_bound_gpu_gate (__main__.Round6Tests.test_info_submit_requires_successful_bound_gpu_gate) ... 
  test_info_submit_requires_successful_bound_gpu_gate (__main__.Round6Tests.test_info_submit_requires_successful_bound_gpu_gate) (field='passed') ... FAIL
  test_info_submit_requires_successful_bound_gpu_gate (__main__.Round6Tests.test_info_submit_requires_successful_bound_gpu_gate) (field='adoption_plan_sha256') ... FAIL
  test_info_submit_requires_successful_bound_gpu_gate (__main__.Round6Tests.test_info_submit_requires_successful_bound_gpu_gate) (field='required_device_type') ... FAIL
  test_info_submit_requires_successful_bound_gpu_gate (__main__.Round6Tests.test_info_submit_requires_successful_bound_gpu_gate) (field='adoption_assets') ... FAIL
  test_info_submit_requires_successful_bound_gpu_gate (__main__.Round6Tests.test_info_submit_requires_successful_bound_gpu_gate) (field='adoption_profile') ... FAIL
test_info_submit_requires_successful_bound_gpu_gate (__main__.Round6Tests.test_info_submit_requires_successful_bound_gpu_gate) ... FAIL

======================================================================
FAIL: test_f1_readme_unpack_subprocess (__main__.Round6Tests.test_f1_readme_unpack_subprocess)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 127, in test_f1_readme_unpack_subprocess
    self.assertEqual(result.returncode,0,result.stderr)
AssertionError: 1 != 0 : Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/91efe6b635734728826dccdd488ba246/step600/unpack_return.py", line 3, in <module>
    from fetch_return import digest as file_digest, validate_exit
ModuleNotFoundError: No module named 'fetch_return'


======================================================================
FAIL: test_f2_detached_locked_fill_exit_success_and_failure (__main__.Round6Tests.test_f2_detached_locked_fill_exit_success_and_failure)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 139, in test_f2_detached_locked_fill_exit_success_and_failure
    self.assertIn('nohup bash',text,'Pull/fill still runs in the foreground')
AssertionError: 'nohup bash' not found in '#!/bin/bash\nset -euo pipefail\numask 077\nD=$(cd -- "$(dirname -- "$0")" && pwd)\nP=/project/community/jjyeung/okh7/a15_cot_apab0123456789\nexport TZ=UTC CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud CLOUDSDK_CORE_DISABLE_PROMPTS=1\nE=$P/a/e\ntest ! -e "$E"\nmkdir -m 700 "$E"\nOBJECT=q8/8865619b/673bc60f_m600.tar\ncp /project/community/jjyeung/okh7/abcdef/5 "$E/5"\ntest "$(cat "$E/5")" = \'q8/8865619b/673bc60f_m600.tar 4 2222222222222222222222222222222222222222222222222222222222222222\'\ncp /project/community/jjyeung/okh7/abcdef/7 "$E/7"\ntest "$(sha256sum "$E/7" | cut -d\' \' -f1)" = 3b0051c4a9cc661d02019a645165fc3e23d658d2f24a6fd6fd86ec7877ba4fc1\ncp /project/community/jjyeung/okh7/abcdef/8 "$E/8"\ntest "$(sha256sum "$E/8" | cut -d\' \' -f1)" = 4c0dd9d6e4535a2945ed58754c1cdd5e9a316067be35f2e8440caa9a80e1c915\ncp /project/community/jjyeung/okh7/abcdef/9 "$E/9"\ntest "$(sha256sum "$E/9" | cut -d\' \' -f1)" = 7f654d2f0ae9f06083f2fc8fd793512c154b4d01ce8632fb733d4191205af770\nfor i in 0 1 2 3; do\n  test ! -e "$E/$i"\n  gsutil -o Boto:num_retries=0 -o Boto:metadata_service_num_attempts=1 -o GSUtil:parallel_process_count=1 -o GSUtil:parallel_thread_count=1 -o GSUtil:sliced_object_download_threshold=0 -o GSUtil:sliced_object_download_max_components=1 -q cp "gs://cmu-gpucloud-jjyeung/$OBJECT.part0$i-of-04" "$E/$i.partial"\n  mv "$E/$i.partial" "$E/$i"\ndone\n/usr/bin/python3 -I -s -B "$P/a/4.py" --parts "$E/0" "$E/1" "$E/2" "$E/3" --done "$E/5" --object "$OBJECT" --config "$E/7" --receipt "$E/8" --data-receipt "$E/9" --lineage SFT --step 600 --out "$P/a/export.json" --prep-tar "$P/a/6" --base-inputs "$P/a/0.json" --inputs-out "$P/a/1.json"\nPREP=$(sha256sum "$P/a/6" | cut -d\' \' -f1)\n/usr/bin/python3 -I -s -B "$D/d.py" "$P/a/1.json" "$P/a/0.json" "$PREP" > "$P/a/dry.json"\n(cd "$P" && CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 04:30:00)\n/usr/bin/python3 -I -s -B "$D/d2.py" "$P" "$P/a/w2" > "$P/a/dry2.json"\nprintf \'%s\\n\' 0 > "$P/a/1.txt"\n' : Pull/fill still runs in the foreground

======================================================================
FAIL: test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks) (field='bundle_guard.batch_sha256')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 179, in test_f3_full_cont_ops_receipt_checks
    self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'Unbound CPU receipt field: '+key)
AssertionError: 0 == 0 : Unbound CPU receipt field: batch_sha256

======================================================================
FAIL: test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks) (field='bundle_guard.path')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 179, in test_f3_full_cont_ops_receipt_checks
    self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'Unbound CPU receipt field: '+key)
AssertionError: 0 == 0 : Unbound CPU receipt field: path

======================================================================
FAIL: test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks) (field='entry_sequence.events')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 179, in test_f3_full_cont_ops_receipt_checks
    self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'Unbound CPU receipt field: '+key)
AssertionError: 0 == 0 : Unbound CPU receipt field: events

======================================================================
FAIL: test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks) (field='entry_sequence.guard_target_sha256')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 179, in test_f3_full_cont_ops_receipt_checks
    self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'Unbound CPU receipt field: '+key)
AssertionError: 0 == 0 : Unbound CPU receipt field: guard_target_sha256

======================================================================
FAIL: test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks) (field='entry_sequence.requested_argv')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 179, in test_f3_full_cont_ops_receipt_checks
    self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'Unbound CPU receipt field: '+key)
AssertionError: 0 == 0 : Unbound CPU receipt field: requested_argv

======================================================================
FAIL: test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks) (field='entry_sequence.dispatched_argv')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 179, in test_f3_full_cont_ops_receipt_checks
    self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'Unbound CPU receipt field: '+key)
AssertionError: 0 == 0 : Unbound CPU receipt field: dispatched_argv

======================================================================
FAIL: test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks) (field='entry_sequence.batch_sha256')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 179, in test_f3_full_cont_ops_receipt_checks
    self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'Unbound CPU receipt field: '+key)
AssertionError: 0 == 0 : Unbound CPU receipt field: batch_sha256

======================================================================
FAIL: test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks) (field='memory.perception_memo_modules')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 179, in test_f3_full_cont_ops_receipt_checks
    self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'Unbound CPU receipt field: '+key)
AssertionError: 0 == 0 : Unbound CPU receipt field: perception_memo_modules

======================================================================
FAIL: test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks) (field='memory.sam_measurement_required')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 179, in test_f3_full_cont_ops_receipt_checks
    self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'Unbound CPU receipt field: '+key)
AssertionError: 0 == 0 : Unbound CPU receipt field: sam_measurement_required

======================================================================
FAIL: test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 181, in test_f3_full_cont_ops_receipt_checks
    self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'MEMORY.json differs')
AssertionError: 0 == 0 : MEMORY.json differs

======================================================================
FAIL: test_f4_every_copied_a4_member_pinned_before_output (__main__.Round6Tests.test_f4_every_copied_a4_member_pinned_before_output) (member='package/BATCH.sh')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 194, in test_f4_every_copied_a4_member_pinned_before_output
    with self.assertRaisesRegex(ValueError,'A4 member pin|A4 batch pin'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f4_every_copied_a4_member_pinned_before_output (__main__.Round6Tests.test_f4_every_copied_a4_member_pinned_before_output) (member='package/3.py')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 194, in test_f4_every_copied_a4_member_pinned_before_output
    with self.assertRaisesRegex(ValueError,'A4 member pin|A4 batch pin'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f4_every_copied_a4_member_pinned_before_output (__main__.Round6Tests.test_f4_every_copied_a4_member_pinned_before_output) (member='package/a/0.json')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 194, in test_f4_every_copied_a4_member_pinned_before_output
    with self.assertRaisesRegex(ValueError,'A4 member pin|A4 batch pin'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f4_every_copied_a4_member_pinned_before_output (__main__.Round6Tests.test_f4_every_copied_a4_member_pinned_before_output) (member='package/a/4.py')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 194, in test_f4_every_copied_a4_member_pinned_before_output
    with self.assertRaisesRegex(ValueError,'A4 member pin|A4 batch pin'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f4_every_copied_a4_member_pinned_before_output (__main__.Round6Tests.test_f4_every_copied_a4_member_pinned_before_output) (member='package/a/7.py')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 194, in test_f4_every_copied_a4_member_pinned_before_output
    with self.assertRaisesRegex(ValueError,'A4 member pin|A4 batch pin'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f4_every_copied_a4_member_pinned_before_output (__main__.Round6Tests.test_f4_every_copied_a4_member_pinned_before_output) (member='fetch_return.py')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 194, in test_f4_every_copied_a4_member_pinned_before_output
    with self.assertRaisesRegex(ValueError,'A4 member pin|A4 batch pin'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f4_every_copied_a4_member_pinned_before_output (__main__.Round6Tests.test_f4_every_copied_a4_member_pinned_before_output)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 202, in test_f4_every_copied_a4_member_pinned_before_output
    with self.assertRaisesRegex(ValueError,'bootstrap pin'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f5_checkpoint_binding_and_runtime_recheck (__main__.Round6Tests.test_f5_checkpoint_binding_and_runtime_recheck) (asset='RESTORE.json')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 222, in test_f5_checkpoint_binding_and_runtime_recheck
    with self.assertRaises(ValueError):selected_gate(self.helper,args)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f5_checkpoint_binding_and_runtime_recheck (__main__.Round6Tests.test_f5_checkpoint_binding_and_runtime_recheck) (asset='binding.json')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 222, in test_f5_checkpoint_binding_and_runtime_recheck
    with self.assertRaises(ValueError):selected_gate(self.helper,args)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f5_checkpoint_binding_and_runtime_recheck (__main__.Round6Tests.test_f5_checkpoint_binding_and_runtime_recheck)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 225, in test_f5_checkpoint_binding_and_runtime_recheck
    with self.assertRaisesRegex(ValueError,'export identity|export pin'):selected_gate(self.helper,args)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f5_production_device_is_required (__main__.Round6Tests.test_f5_production_device_is_required)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 239, in test_f5_production_device_is_required
    self.assertTrue(hasattr(self.kit,'validate_device'),'GPU name is recorded but never required')
AssertionError: False is not true : GPU name is recorded but never required

======================================================================
FAIL: test_f5_runtime_asset_recheck (__main__.Round6Tests.test_f5_runtime_asset_recheck)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 229, in test_f5_runtime_asset_recheck
    self.assertTrue(hasattr(self.kit,'validate_assets'),'Gate lacks runtime asset authentication')
AssertionError: False is not true : Gate lacks runtime asset authentication

======================================================================
FAIL: test_info_done_whitespace (__main__.Round6Tests.test_info_done_whitespace)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 251, in test_info_done_whitespace
    self.assertNotIn('test "$(cat "$E/5")" =',text,'Whitespace-only receipt changes still refuse')
AssertionError: 'test "$(cat "$E/5")" =' unexpectedly found in '#!/bin/bash\nset -euo pipefail\numask 077\nD=$(cd -- "$(dirname -- "$0")" && pwd)\nP=/project/community/jjyeung/okh7/a15_cot_apab0123456789\nexport TZ=UTC CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud CLOUDSDK_CORE_DISABLE_PROMPTS=1\nE=$P/a/e\ntest ! -e "$E"\nmkdir -m 700 "$E"\nOBJECT=q8/8865619b/673bc60f_m600.tar\ncp /project/community/jjyeung/okh7/abcdef/5 "$E/5"\ntest "$(cat "$E/5")" = \'q8/8865619b/673bc60f_m600.tar 4 2222222222222222222222222222222222222222222222222222222222222222\'\ncp /project/community/jjyeung/okh7/abcdef/7 "$E/7"\ntest "$(sha256sum "$E/7" | cut -d\' \' -f1)" = 3b0051c4a9cc661d02019a645165fc3e23d658d2f24a6fd6fd86ec7877ba4fc1\ncp /project/community/jjyeung/okh7/abcdef/8 "$E/8"\ntest "$(sha256sum "$E/8" | cut -d\' \' -f1)" = 4c0dd9d6e4535a2945ed58754c1cdd5e9a316067be35f2e8440caa9a80e1c915\ncp /project/community/jjyeung/okh7/abcdef/9 "$E/9"\ntest "$(sha256sum "$E/9" | cut -d\' \' -f1)" = 7f654d2f0ae9f06083f2fc8fd793512c154b4d01ce8632fb733d4191205af770\nfor i in 0 1 2 3; do\n  test ! -e "$E/$i"\n  gsutil -o Boto:num_retries=0 -o Boto:metadata_service_num_attempts=1 -o GSUtil:parallel_process_count=1 -o GSUtil:parallel_thread_count=1 -o GSUtil:sliced_object_download_threshold=0 -o GSUtil:sliced_object_download_max_components=1 -q cp "gs://cmu-gpucloud-jjyeung/$OBJECT.part0$i-of-04" "$E/$i.partial"\n  mv "$E/$i.partial" "$E/$i"\ndone\n/usr/bin/python3 -I -s -B "$P/a/4.py" --parts "$E/0" "$E/1" "$E/2" "$E/3" --done "$E/5" --object "$OBJECT" --config "$E/7" --receipt "$E/8" --data-receipt "$E/9" --lineage SFT --step 600 --out "$P/a/export.json" --prep-tar "$P/a/6" --base-inputs "$P/a/0.json" --inputs-out "$P/a/1.json"\nPREP=$(sha256sum "$P/a/6" | cut -d\' \' -f1)\n/usr/bin/python3 -I -s -B "$D/d.py" "$P/a/1.json" "$P/a/0.json" "$PREP" > "$P/a/dry.json"\n(cd "$P" && CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 04:30:00)\n/usr/bin/python3 -I -s -B "$D/d2.py" "$P" "$P/a/w2" > "$P/a/dry2.json"\nprintf \'%s\\n\' 0 > "$P/a/1.txt"\n' : Whitespace-only receipt changes still refuse

======================================================================
FAIL: test_info_submit_requires_successful_bound_gpu_gate (__main__.Round6Tests.test_info_submit_requires_successful_bound_gpu_gate) (field='passed')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 268, in test_info_submit_requires_successful_bound_gpu_gate
    with self.subTest(field=key):self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'GPU evidence ignored')
                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 0 == 0 : GPU evidence ignored

======================================================================
FAIL: test_info_submit_requires_successful_bound_gpu_gate (__main__.Round6Tests.test_info_submit_requires_successful_bound_gpu_gate) (field='adoption_plan_sha256')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 268, in test_info_submit_requires_successful_bound_gpu_gate
    with self.subTest(field=key):self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'GPU evidence ignored')
                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 0 == 0 : GPU evidence ignored

======================================================================
FAIL: test_info_submit_requires_successful_bound_gpu_gate (__main__.Round6Tests.test_info_submit_requires_successful_bound_gpu_gate) (field='required_device_type')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 268, in test_info_submit_requires_successful_bound_gpu_gate
    with self.subTest(field=key):self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'GPU evidence ignored')
                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 0 == 0 : GPU evidence ignored

======================================================================
FAIL: test_info_submit_requires_successful_bound_gpu_gate (__main__.Round6Tests.test_info_submit_requires_successful_bound_gpu_gate) (field='adoption_assets')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 268, in test_info_submit_requires_successful_bound_gpu_gate
    with self.subTest(field=key):self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'GPU evidence ignored')
                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 0 == 0 : GPU evidence ignored

======================================================================
FAIL: test_info_submit_requires_successful_bound_gpu_gate (__main__.Round6Tests.test_info_submit_requires_successful_bound_gpu_gate) (field='adoption_profile')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 268, in test_info_submit_requires_successful_bound_gpu_gate
    with self.subTest(field=key):self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'GPU evidence ignored')
                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 0 == 0 : GPU evidence ignored

======================================================================
FAIL: test_info_submit_requires_successful_bound_gpu_gate (__main__.Round6Tests.test_info_submit_requires_successful_bound_gpu_gate)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 270, in test_info_submit_requires_successful_bound_gpu_gate
    self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0)
AssertionError: 0 == 0

----------------------------------------------------------------------
Ran 9 tests in 35.729s

FAILED (failures=31)
```

Command: `bash work/cpu.sh work/run_checks.py  # round7_before; exact environment/argv in runner`

Exact output ([checks/round7_before.txt](checks/round7_before.txt)):

```text
test_f1_archive_runs_inside_live_namespace_and_survives_it (__main__.Round7Tests.test_f1_archive_runs_inside_live_namespace_and_survives_it) ... FAIL
test_f2_fill_wait_missing_token_dead_pid_timeout_and_success (__main__.Round7Tests.test_f2_fill_wait_missing_token_dead_pid_timeout_and_success) ... FAIL
test_f3_exact_sxm_name_and_132_sms (__main__.Round7Tests.test_f3_exact_sxm_name_and_132_sms) ... 
  test_f3_exact_sxm_name_and_132_sms (__main__.Round7Tests.test_f3_exact_sxm_name_and_132_sms) (name='NVIDIA H100 PCIe', sms=114) ... FAIL
  test_f3_exact_sxm_name_and_132_sms (__main__.Round7Tests.test_f3_exact_sxm_name_and_132_sms) (name='NVIDIA H100 80GB HBM3', sms=114) ... FAIL
  test_f3_exact_sxm_name_and_132_sms (__main__.Round7Tests.test_f3_exact_sxm_name_and_132_sms) (name='NVIDIA H100 PCIe', sms=132) ... FAIL
test_info_export_bytes_bound_to_cpu_inputs_before_gpu (__main__.Round7Tests.test_info_export_bytes_bound_to_cpu_inputs_before_gpu) ... FAIL
test_info_host_paths_allocation_and_input_evidence (__main__.Round7Tests.test_info_host_paths_allocation_and_input_evidence) ... FAIL
test_info_receipt_records_and_submit_checks_kit_comparator_sample (__main__.Round7Tests.test_info_receipt_records_and_submit_checks_kit_comparator_sample) ... FAIL
test_info_unpack_ignores_python_environment_and_keeps_sibling_import (__main__.Round7Tests.test_info_unpack_ignores_python_environment_and_keeps_sibling_import) ... FAIL
test_rebind_step400_only (__main__.Round7Tests.test_rebind_step400_only) ... FAIL

======================================================================
FAIL: test_f1_archive_runs_inside_live_namespace_and_survives_it (__main__.Round7Tests.test_f1_archive_runs_inside_live_namespace_and_survives_it)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round7.py", line 39, in test_f1_archive_runs_inside_live_namespace_and_survives_it
    self.assertTrue(hasattr(self.node,'stage_gate_assets'),'CPU proof does not stage the assets while its namespace exists')
AssertionError: False is not true : CPU proof does not stage the assets while its namespace exists

======================================================================
FAIL: test_f2_fill_wait_missing_token_dead_pid_timeout_and_success (__main__.Round7Tests.test_f2_fill_wait_missing_token_dead_pid_timeout_and_success)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round7.py", line 69, in test_f2_fill_wait_missing_token_dead_pid_timeout_and_success
    self.assertIn('# BEGIN FILL_WAIT',text,'Fill wait has no bounded executable block')
AssertionError: '# BEGIN FILL_WAIT' not found in 'The GPU kit is unrun. It requires zero answer/trace byte differences. Its 50 items cover ten items per type and twelve captures; this reuse-heavy sample does not predict full-read throughput.\n\nUse the full **A4/src** base pinned by `BASE_PIN.json`. The reader patches also apply to the inspected B5 source subset, but this kit does not authenticate a B5 base. Apply patches 01–03 to a separate source copy. They add `u0/`; all original reader files remain byte-identical. Apply 04–05 to a separate A4 operator copy, outside `src`.\n\nThe ordinary entrypoint stays OFF and imports no extension. `u0/a8.py --enable-extensions` explicitly selects the extensions; individual cache settings then default OFF. The ON environment records an extension source hash. Rebuild payload and artifact pins before deployment.\n\n## Local preparation\n\nThese commands use paths supplied by the operator; they do not depend on the author\'s `work/` directory. Set `DELIVERY` to the delivered `out/`, `A4_BASE` to the full supplied A4 directory on local scratch, `LOCAL` to a fresh local scratch directory, and `READ_PYTHON` to the approved Python executable. Both source roots and all outputs must stay on local scratch. The package contains code, not model/data archives.\n\n```bash\n: "${DELIVERY:?Absolute path to delivered out directory}"\n: "${A4_BASE:?Absolute path to the full pinned A4 directory on local scratch}"\n: "${LOCAL:?Fresh local scratch directory}"\n: "${READ_PYTHON:?Approved Python executable}"\nexport PYTHONDONTWRITEBYTECODE=1 TOKENIZERS_PARALLELISM=false\nexport OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8\nexport XDG_CACHE_HOME="$LOCAL/cache" HF_HOME="$LOCAL/cache/hf" TRITON_CACHE_DIR="$LOCAL/cache/triton"\nmkdir -p "$LOCAL/source" "$LOCAL/a4"\nnice -n 10 tar -cf - -C "$A4_BASE/src" . | nice -n 10 tar -xf - -C "$LOCAL/source"\nnice -n 10 tar -cf - -C "$A4_BASE" package tower_sequence.py fetch_return.py unpack_return.py |\n  nice -n 10 tar -xf - -C "$LOCAL/a4"\nnice -n 10 patch --batch --fuzz=0 -p1 -d "$LOCAL/source" < "$DELIVERY/patches/01_bounded_read_caches.diff"\nnice -n 10 patch --batch --fuzz=0 -p1 -d "$LOCAL/source" < "$DELIVERY/patches/02_atomic_scene_shards.diff"\nnice -n 10 patch --batch --fuzz=0 -p1 -d "$LOCAL/source" < "$DELIVERY/patches/03_production_integration.diff"\nnice -n 10 patch --batch --fuzz=0 -p1 -d "$LOCAL/a4" < "$DELIVERY/patches/04_operator_cache_bound.diff"\nnice -n 10 patch --batch --fuzz=0 -p1 -d "$LOCAL/a4" < "$DELIVERY/patches/05_operator_return_and_proof.diff"\nEXT_SOURCE="$LOCAL/source"\n```\n\nKeep the private kit, original manifests and reverse maps on Trinity. Stage each source tree as one archive and extract it only on node-local scratch. Both parity source roots must remain pristine: no build outputs, extra files or symlinks. Public paths, submission names, configuration and logs must use opaque tokens. Never transfer private reverse maps to Orchard.\n\n## Step-600 binding, build and operations\n\nThe candidate uses **A4\'s 636-item schedule, one card, caches only, general/no-requeue**. A4\'s export admission, submit helper and run settings remain intact. `a19` requires the reviewed payload hash `4498fca72a8e4b476b38f097ffdf3ff88b5aa20fc036bd196b18a5706e9fe46d`, the patched operator hashes, all copied A4 members, the base BATCH.sh and decoded bootstrap pins from MANIFEST, the exact extension inventory and the four original alias bases. It authenticates them before copying. Its batch uses cont_ops\' exact `build_r10.wrap_batch`: excluded node, EXIT log return and USR1 forwarding.\n\nThe owner supplies a **reviewed step-600 target template** in cont_ops\' `bind400_partial.json` schema: target run, step, member_directory, lineage, object, preparation_sha256, `done` and `prep_paths`. `done` and `prep_paths` are paths on Orchard; preparation_sha256 holds hashes, not paths. Use authenticated local copies of that target\'s artifact.json, whole-tar `.done` receipt and three preparation files. The helper fills configuration/archive fields from those files and checks target run/member/step and preparation hashes. Do not edit a step-200/400 receipt to manufacture step-600 evidence. No real target receipt was supplied to this CPU task.\n\n```bash\n: "${TARGET_TEMPLATE:?Reviewed target template, including Orchard done and prep_paths}"\n: "${TARGET_ARTIFACT:?Authenticated local artifact.json from target export}"\n: "${TARGET_DONE:?Authenticated local whole-tar done receipt}"\n: "${TARGET_CONFIG:?Authenticated local preparation config.json}"\n: "${TARGET_RECEIPT:?Authenticated local preparation s1_receipt.json}"\n: "${TARGET_DATA_RECEIPT:?Authenticated local data_receipt.json}"\nSTEP600_BINDING="$LOCAL/binding600.json"\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a20.py" --enable-extensions binding \\\n  --template "$TARGET_TEMPLATE" --artifact "$TARGET_ARTIFACT" --done "$TARGET_DONE" \\\n  --config "$TARGET_CONFIG" --receipt "$TARGET_RECEIPT" --data-receipt "$TARGET_DATA_RECEIPT" \\\n  --out "$STEP600_BINDING"\n: "${PACKAGE_TOKEN:?Fresh 11-16 hex characters starting with a-f}"\nPROFILE_ARGS=()  # All three caches, 12 GiB. For processor-only: PROFILE_ARGS=(--processor-only)\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a19.py" \\\n  --enable-extensions --base-operator "$LOCAL/a4" --source-root "$EXT_SOURCE" \\\n  --manifest "$DELIVERY/patches/MANIFEST.json" --extension-pins "$DELIVERY/kit_parity50/EXTENSION_PINS.json" \\\n  --export-binding "$STEP600_BINDING" --token "$PACKAGE_TOKEN" --out "$LOCAL/step600" "${PROFILE_ARGS[@]}"\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a20.py" --enable-extensions operations \\\n  --operator "$LOCAL/step600" --binding "$STEP600_BINDING" --dry-root "$DELIVERY/operations" --out "$LOCAL/ops"\nnice -n 10 tar -czf "$LOCAL/0.tgz" -C "$LOCAL/ops" .\nnice -n 10 sha256sum "$LOCAL/0.tgz"\n```\n\n`step600` retains the exact local source/operator/unpacker. `ops/1.tgz` is the package delivery, with `ops/SHA256`; the outer archive carries it and five inert scripts. The commands below are **owner operations on Orchard, unrun here**. Transfer the single outer archive through the owner\'s existing authorized transport. Set `OPS_ARCHIVE` to its received opaque path, `OPS_SHA256` to the printed local hash, and `D` to a fresh opaque operation directory. These are transport endpoints, not generated receipt values.\n\n```bash\n: "${OPS_ARCHIVE:?Received outer archive on Orchard}"\n: "${OPS_SHA256:?Printed local SHA256 of that archive}"\n: "${D:?Fresh opaque operation directory on Orchard}"\nprintf \'%s  %s\\n\' "$OPS_SHA256" "$OPS_ARCHIVE" | sha256sum -c -\ntest ! -e "$D"\nmkdir -m 700 "$D"\ntar -xzf "$OPS_ARCHIVE" -C "$D"\nbash "$D/o_place.sh"\nbash "$D/o_pull_fill.sh"\nP=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}\n# Detached worker: inspect completion no more than once per minute.\nwhile test ! -f "$P/a/1.txt"; do sleep 60; done\ntest "$(cat "$P/a/1.txt")" = 0\nbash "$D/o_cpu.sh"\n```\n\n`o_place.sh` verifies the inner archive and places it at `$P=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}`. `o_pull_fill.sh` acquires the permanent attempt lock `$P/a/0.lock`, launches one detached nohup worker, and returns its PID in `$P/a/0.txt`. The worker logs to `$P/a/0.log` and writes its exit status to `$P/a/1.txt` on success or failure. A duplicate launch refuses; a failed or interrupted attempt requires a fresh package/token, never an automatic retry. The worker copies the reviewed `done` and `prep_paths` files to `$P/a/e/{5,7,8,9}`, authenticates their pins (the `.done` receipt uses whitespace-separated fields), fetches export parts `0..3` once with retries disabled, fills through `a/4.py`, and runs cont_ops\' verbatim `dryres2.py` and `dry2.py`. A failed transfer stops; the scripts do not retry it.\n\n`o_cpu.sh` requests the A4 CPU allocation explicitly: preempt, eight CPUs, 200G, four hours, no GPU, no requeue, and the excluded nodes. The **CPU allocation** is separate from the intended **general GPU read**. Wait for the CPU job to finish successfully. Preserve `$P/a/c/CPU.json`, `MEMORY.json` and the exact `SETTINGS.json` emitted by A4 prepare. Bring these small files back as one archive through the authorized transport to `$LOCAL/step600/proof/` before the parity preparation below. The proof emits exact restore, artifact-binding, manifest and export-pin receipts. These small files authenticate staging; they do not contain model weights. The proof binds payload/plan/inputs/operator, must pass bundle/entry checks and contain `memory.read_cache_bytes=12884901888` (4294967296 for processor-only), `basis=fixed_g3t_shapes`, and `fits=true`.\n\nArchive the CPU evidence on Orchard after its successful completion, using the package token printed by the build:\n\n```bash\nP=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}\ntar -czf "$D/2.tgz" -C "$P/a/c" CPU.json MEMORY.json SETTINGS.json RESTORE.json binding.json manifest.json EXPORT_PIN.json\nsha256sum "$D/2.tgz"\n```\n\nAfter authorized transport, authenticate and extract that archive on local scratch:\n\n```bash\n: "${PROOF_ARCHIVE:?Received CPU-evidence archive on local scratch}"\n: "${PROOF_SHA256:?Printed Orchard SHA256 of the CPU-evidence archive}"\nprintf \'%s  %s\\n\' "$PROOF_SHA256" "$PROOF_ARCHIVE" | nice -n 10 sha256sum -c -\nmkdir "$LOCAL/step600/proof"\nnice -n 10 tar -xzf "$PROOF_ARCHIVE" -C "$LOCAL/step600/proof"\n```\n\nAfter the zero-difference GPU parity gate passes, transfer its token-only `ue.json` through the authorized transport as one archive, preserving the SHA256 printed on the GPU host. The authorized owner authenticates that archive and installs the receipt before submission:\n\n```bash\n: "${GATE_ARCHIVE:?Received archive containing ue.json}"\n: "${GATE_SHA256:?SHA256 printed on the GPU host}"\nprintf \'%s  %s\\n\' "$GATE_SHA256" "$GATE_ARCHIVE" | sha256sum -c -\nmkdir "$D/g"\ntar -xf "$GATE_ARCHIVE" -C "$D/g"\nP=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}\ntest ! -e "$P/a/g.json"\ncp "$D/g/ue.json" "$P/a/g.json"\n```\n\nThen run:\n\n```bash\nbash "$D/o_sub.sh"\n# After the GPU job finishes:\nbash "$D/o_fetch.sh"\nP=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}\ntar -czf "$D/3.tgz" -C "$P/a/f" 0.tgz EXIT.json\nsha256sum "$D/3.tgz"\n```\n\n`o_sub.sh` embeds cont_ops’ A4 CPU-receipt assertions verbatim, including batch/dispatch/guard pins and MEMORY.json equality, then checks cache memory and the successful GPU receipt at `$P/a/g.json`, requires both dry checks to pass, requires an empty general queue, and refuses a return pool over **75,000,000 bytes** (including errors/symlinks). It then runs `3.py check` and one `3.py submit --gpus 1 --time 04:30:00`, saving the job ID. The GPU receipt must match the CPU restore/binding pins, filled export pin, adopted plan/profile and H100 80 GB requirement. The unchanged bootstrap itself does not require the cache-memory field; this submit preflight does. `o_fetch.sh` derives the authenticated return token and fetches `$P/a/f/{0.tgz,EXIT.json}`.\n\nTransfer `$D/3.tgz` through the authorized transport, preserving the local operator directory. Authenticate, extract and unpack it locally:\n\n```bash\n: "${RETURN_ARCHIVE:?Received fetched-return archive on local scratch}"\n: "${RETURN_SHA256:?Printed Orchard SHA256 of the fetched-return archive}"\nprintf \'%s  %s\\n\' "$RETURN_SHA256" "$RETURN_ARCHIVE" | nice -n 10 sha256sum -c -\nmkdir "$LOCAL/step600/f"\nnice -n 10 tar -xzf "$RETURN_ARCHIVE" -C "$LOCAL/step600/f"\n(cd "$LOCAL/step600" && CUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -s -B ./unpack_return.py \\\n  --archive "$LOCAL/step600/f/0.tgz" --exit "$LOCAL/step600/f/EXIT.json" \\\n  --out "$LOCAL/step600/ret" > "$LOCAL/step600/unpack-success.json" && \\\n  test -s "$LOCAL/step600/unpack-success.json")\n```\n\nA refused unpack leaves its extracted tree behind. Scorers must consume only unpack\'s **success output after exit status 0**, never a directory merely because it exists; the command\'s `&&` chain enforces that handoff. A successful partial return still has `complete=false` and must not be scored as complete. The ON unpacker refuses any existing weight receipt whose verified value is not JSON true. Processor-only journals need no weight receipt. OFF behavior remains unchanged. Whole-archive identity follows A4\'s design: fill checks the sealed whole-tar constants; job/unpack admission compare against inputs.archives[0].\n\n**Forecasts:** Package D is the 580-item distance read (B5 fork, 03:30 walltime); it has **no ON route** in a19. Its one-card **estimate** is 13,813.069 s (3 h 50 min), using the measured 23.600 s/item and crediting no cache saving. The **636-item** A4 read that a19 actually builds has an **estimate** of **7,351.824 s (2 h 02 min 32 s; 11.559 s/item)**, obtained by carrying forward the supplied A4 total, with zero assumed saving. Target weights, cache costs and staging/queue delays can change it; neither forecast is a step-600 measurement.\n\n## GPU parity staging and acceptance\n\nThe gate must seal **A4 prepare\'s actual output plus the operator\'s per-read overrides** for the package being adopted. Do not supply an unrelated PRIVATE_SETTINGS.json. `a20 gate` checks the prepared bytes and exact RESTORE.json/artifact-binding bytes against CPU.json’s READY pins, checks export identity against the adopted step binding, and checks payload, plan and operator bindings. Every GPU worker rechecks those asset bytes and the artifact manifest before reading; changing paths cannot substitute another checkpoint. It applies the authenticated operator descriptor and derives `enable_caches`, `read_cache_bytes` and the full adoption profile: candidates_argmax, memo on, g3t, empty verify IDs, save_own_depth=false, and the exact cache switches. Both the parent driver and every worker refuse a different profile. Processor-only adoption is explicitly gated with slots `[0]` and 4 GiB; all-cache adoption uses `[0,1,2]` and 12 GiB.\n\nStage the exact retained CPU data on the intended GPU host; preserve the CPU logical directory so pinned manifests and restore paths stay unchanged. Do not rebuild RESTORE.json or the manifest for a different checkpoint. The following **owner-only, unrun staging commands** create one data archive on the CPU proof’s compute node. `CPU.json.root` is node-local, so run there while that directory remains available. The archive can be large; use the owner’s approved storage/transport plan.\n\n```bash\nP=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}\n/usr/bin/python3 -I -s -B - "$P" <<\'PY\'\nimport json,subprocess,sys,tarfile\nfrom pathlib import Path\np=Path(sys.argv[1]);root=Path(json.loads((p/\'a/c/CPU.json\').read_text())[\'root\'])\nwith tarfile.open(p/\'0.tgz\') as archive:cfg=json.load(archive.extractfile(\'9.json\'))\nsys.path.insert(0,str(root/\'bootstrap\'))\nfrom orchard_h10.common import template\n_,J,_,_,_=template()\nsubprocess.run(J.namespace(root)+[\'/bin/tar\',\'-chf\',str(root/\'4.tar\'),\'-C\',cfg[\'logical\']+\'/d\',\'.\'],check=True)\nprint(root/\'4.tar\')\nsubprocess.run([\'sha256sum\',str(root/\'4.tar\')],check=True)\nPY\n```\n\nTransfer that single archive through approved transport. On the assigned GPU host, extract it under the package’s exact opaque logical root, and stage the package payload there for the manifest’s code roots. `P` refers to the same filled package in the registered Orchard namespace. These commands refuse an existing destination:\n\n```bash\n: "${ASSET_ARCHIVE:?Received CPU data archive}"\n: "${ASSET_SHA256:?Printed CPU archive SHA256}"\nprintf \'%s  %s\\n\' "$ASSET_SHA256" "$ASSET_ARCHIVE" | sha256sum -c -\nGPU_LOGICAL=$(/usr/bin/python3 -I -s -B - "$P/0.tgz" <<\'PY\'\nimport json,sys,tarfile\nwith tarfile.open(sys.argv[1]) as archive:print(json.load(archive.extractfile(\'9.json\'))[\'logical\'])\nPY\n)\ntest ! -e "$GPU_LOGICAL"\nmkdir -p "$GPU_LOGICAL/d" "$GPU_LOGICAL/p"\ntar -xf "$ASSET_ARCHIVE" -C "$GPU_LOGICAL/d"\ntar -xzf "$P/0.tgz" -C "$GPU_LOGICAL/p"\ntest ! -e "$GPU_LOGICAL/d/7.json"\ncp "$GPU_LOGICAL/d/binding.json" "$GPU_LOGICAL/d/7.json"\n```\n\nCreate a private neutral configuration from `config.example.json` with separate authenticated A4 original/patched source roots. Set `export=$GPU_LOGICAL/d/e`, `export_pin=$GPU_LOGICAL/d/6.json`, and `artifact_manifest=$GPU_LOGICAL/d/7.json`. The last file is a byte-identical neutral alias for the CPU binding. Include that exact `binding.json` to `7.json` mapping in `PRIVATE_ALIASES.json`; map the other private prepared asset paths to staged opaque aliases of those same files. Keep private settings and reverse maps on Trinity. The following commands use files under `$LOCAL`:\n\n```bash\n: "${PRIVATE_CONFIG_TEMPLATE:?Private neutral GPU configuration with staged asset paths}"\n: "${PRIVATE_ALIASES:?Private JSON mapping preparation paths to staged opaque paths}"\nPRIVATE_SETTINGS="$LOCAL/PRIVATE_SETTINGS.json"\nPRIVATE_CONFIG="$LOCAL/PRIVATE_NEUTRAL_CONFIG.json"\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a20.py" --enable-extensions gate \\\n  --operator "$LOCAL/step600" --prepared "$LOCAL/step600/proof/SETTINGS.json" \\\n  --proof "$LOCAL/step600/proof/CPU.json" --config "$PRIVATE_CONFIG_TEMPLATE" \\\n  --asset-receipts "$LOCAL/step600/proof" \\\n  --settings-out "$PRIVATE_SETTINGS" --config-out "$PRIVATE_CONFIG"\n```\n\n```bash\nmkdir -p "$LOCAL/public"\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a11.py" seal \\\n  --source-root "$EXT_SOURCE" --input "$PRIVATE_SETTINGS" --aliases "$PRIVATE_ALIASES" \\\n  --out "$LOCAL/public/u3"\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a11.py" stage-kit \\\n  --source-root "$EXT_SOURCE" --input "$DELIVERY/kit_parity50" \\\n  --config "$PRIVATE_CONFIG" --out "$LOCAL/public/u0"\n```\n\nThe staged `u3.json` pins every extension; `u4.json` authenticates both full 927-file base inventories. The driver rejects changed bases, equal original/patched roots, and an original root containing extensions. It authenticates the sealed sample bytes and the logical sample pin. Transfer only the staged directory through the approved transport under an opaque root.\n\nOn an assigned **H100 80 GB** GPU, run the acceptance command below; it is **unrun here**. Preserve that allocation\'s actual `CUDA_VISIBLE_DEVICES`.\n\n```bash\nnice -n 10 "$READ_PYTHON" -I -s -B /scratch/jjyeung/ab0123456789/u0/u0.py \\\n  /scratch/jjyeung/ab0123456789/u0/u2.json --out /scratch/jjyeung/ab0123456789/u9 \\\n  --enable-gpu --public --repeat-baseline --shards 4\n```\n\nEvery arm starts a fresh process. ORIGINAL/OFF/OFF_REPEAT use ordinary journals and modulo shards. ON tests caches; ON_JOURNAL and sequential whole-scene shards test separate journal/shard features. Sequential shards establish equality, not parallel speed. Public logs tokenize item/native/room identities and arbitrary stdout/stderr. No reverse map is written on Orchard.\n\nAcceptance requires all 50 expected IDs, complete production output schemas, nonempty text/tokens/heads, scale even when null, every served response and forced-token count, matching call counters, and **zero semantic byte differences**. ORIGINAL/OFF must also retain every production source hash. Each enabled cache must report its memory bound and useful hits; SAM needs both feature and detection hits. Empty or all-miss runs fail. Only clocks and explicit audit/cache/memo telemetry are excluded from semantic comparison; audit violations fail. There is no answer/trace tolerance.\n\nEach RUN.json records the adopted package plan, read profile, asset pins, required device type, actual device, cache slots and budget. The worker checks CUDA device properties before model loading and refuses a different GPU family, compute capability or memory class. `ue.json` is written only after all comparisons finish and records whether they all passed; failed or missing receipts cannot authorize submit. Archive it with `tar -cf "$LOCAL/5.tar" -C /scratch/jjyeung/ab0123456789/u9 ue.json` and print `sha256sum "$LOCAL/5.tar"` for the authenticated return transport. Judge net time from `RUN.json`\'s `worker_wall_seconds`, which includes install/boundary hashing and eager SAM loading. Per-item timing alone cannot establish savings. ON constructs SAM outside inference mode to obtain tracked parameters; that changes loading time and potentially RNG use. The GPU byte gate must clear it. The sample overrepresents clip reuse: its ten distance items share one clip, while A4 has 150 distance items across 60 clips (review finding 7).\n\nThe cache cap covers retained cache storage and transient copies, not model/caller working memory. Measure full-process host/GPU peaks. Models must remain frozen: calls check parameter/buffer identities, pointers and counters; install/type boundaries hash content. Persistent raw writes fail at a boundary. Raw writes restored between boundaries, private tensor attributes and arbitrary non-tensor state are outside this guard\'s coverage. Graceful stops verify journals; a hard kill can leave an unchecked journal that requires fresh output.\n\nOutput directories u0–u5 represent ORIGINAL/OFF/OFF_REPEAT/ON/ON_JOURNAL/SHARDED. Reports u6–ua compare arms; ub.json checks merge equality; uc/ud contain canonical single/sharded returns. Restore on Trinity with the private inputs:\n\n```bash\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a11.py" restore \\\n  --source-root "$EXT_SOURCE" --input PRIVATE_RETURN --out "$LOCAL/restored" \\\n  --private-source "$DELIVERY/kit_parity50/sample50.json" \\\n  --private-source "$PRIVATE_CONFIG" --private-source "$PRIVATE_SETTINGS"\n```\n\nRestoration authenticates committed rows before rebuilding private IDs/checksums. Merge with the original manifest through the explicit extension entrypoint. The canonical answer/trace archive must match exactly; transport-envelope clocks remain variable.\n\n## Array validation\n\nNo multi-card A4 operator is delivered. The array helper is a separate inert prototype. Its example has `approved=false`: two one-hour shards, at most two attempts, four GPU-hours total. Approval must bind the exact partition, shards, time and attempts, with no more than five allocated GPU-hours over all attempts. Before any sharded/preempt adoption, validate real persistent-storage preemption/requeue.\n\n```bash\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a15.py" PRIVATE_ARRAY_CONFIG.json \\\n  --enable-array --token ab0123456789 --out "$LOCAL/array-plan" \\\n  --python /scratch/jjyeung/ab0123456789/u1 --source /scratch/jjyeung/ab0123456789/u2 \\\n  --staged-config /project/community/jjyeung/okh7/a15_cot_apab0123456789/u3.json\n```\n\nThis writes commands without running them. Exit 75 requests bounded requeue; other errors remain failures. Lock waits stop after 60 seconds, and the attempt limit forbids more work. Public paths must use approved roots and pass the forbidden-word screen; name checks do not establish storage permissions or capacity.\n\nNo delivered CPU suite or single-GPU kit requires a local OS socket. StageOneSocket is a Python callback. Real restore, bwrap isolation, remote transport, GPU parity/performance/memory and persistent requeue remain unrun.\n\n## Review round 6: finding -> fix -> test\n\n| Finding | Fix | Regression |\n|---|---|---|\n| 1. Unpack import fails | Run `-s -B` from the operator directory. | Execute the README command as a subprocess on an authenticated fixture return. |\n| 2. Foreground pull/fill | Detached nohup worker, permanent attempt lock, PID/log and exit file; no retries. | Success 0 and failure 17 both report completion; duplicate launch refuses. |\n| 3. Weak submit receipt | Embed every cont_ops A4 CPU assertion, then enforce cache and pool checks. | Batch/guard/action/argv/events/memory tampering and a resealed stale batch fail. |\n| 4. Unpinned copied members | Pin all A4 copied members, base batch and decoded bootstrap before output. | Mutations of each additional member and bootstrap pin refuse before writing. |\n| 5. Unbound checkpoint/device | READY restore/binding pins and export identity bind step-600 assets; workers recheck assets and require H100 80 GB. | Changed receipts, wrong step, changed staged files and non-production GPU properties fail. |\n| INFO: receipt whitespace | Compare the three whitespace-separated fields. | Tabs/newlines pass; extra fields fail. |\n| INFO: manual GPU handoff | Submit requires the successful token-only GPU receipt for the same plan/profile/assets/device. | Failed, absent, stale or mismatched evidence refuses. |\n\nThe binding retains Orchard `done`/`prep_paths` as authenticated operation metadata; admission still checks its fixed identity keys. Persistent raw writes remain boundary-checked; restored-between-boundary raw writes remain unsupported and require frozen model ownership. These informational limits do not change reader behavior.\n' : Fill wait has no bounded executable block

======================================================================
FAIL: test_f3_exact_sxm_name_and_132_sms (__main__.Round7Tests.test_f3_exact_sxm_name_and_132_sms) (name='NVIDIA H100 PCIe', sms=114)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round7.py", line 95, in test_f3_exact_sxm_name_and_132_sms
    with self.subTest(name=name,sms=sms),self.assertRaises(ValueError):check(name,sms)
                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f3_exact_sxm_name_and_132_sms (__main__.Round7Tests.test_f3_exact_sxm_name_and_132_sms) (name='NVIDIA H100 80GB HBM3', sms=114)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round7.py", line 95, in test_f3_exact_sxm_name_and_132_sms
    with self.subTest(name=name,sms=sms),self.assertRaises(ValueError):check(name,sms)
                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f3_exact_sxm_name_and_132_sms (__main__.Round7Tests.test_f3_exact_sxm_name_and_132_sms) (name='NVIDIA H100 PCIe', sms=132)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round7.py", line 95, in test_f3_exact_sxm_name_and_132_sms
    with self.subTest(name=name,sms=sms),self.assertRaises(ValueError):check(name,sms)
                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_info_export_bytes_bound_to_cpu_inputs_before_gpu (__main__.Round7Tests.test_info_export_bytes_bound_to_cpu_inputs_before_gpu)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round7.py", line 116, in test_info_export_bytes_bound_to_cpu_inputs_before_gpu
    with self.assertRaisesRegex(ValueError,'export pin|export bytes'):self.helper.gate(*args,**kwargs)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_info_host_paths_allocation_and_input_evidence (__main__.Round7Tests.test_info_host_paths_allocation_and_input_evidence)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round7.py", line 155, in test_info_host_paths_allocation_and_input_evidence
    self.assertNotIn('$LOCAL/5.tar',text)
AssertionError: '$LOCAL/5.tar' unexpectedly found in 'The GPU kit is unrun. It requires zero answer/trace byte differences. Its 50 items cover ten items per type and twelve captures; this reuse-heavy sample does not predict full-read throughput.\n\nUse the full **A4/src** base pinned by `BASE_PIN.json`. The reader patches also apply to the inspected B5 source subset, but this kit does not authenticate a B5 base. Apply patches 01–03 to a separate source copy. They add `u0/`; all original reader files remain byte-identical. Apply 04–05 to a separate A4 operator copy, outside `src`.\n\nThe ordinary entrypoint stays OFF and imports no extension. `u0/a8.py --enable-extensions` explicitly selects the extensions; individual cache settings then default OFF. The ON environment records an extension source hash. Rebuild payload and artifact pins before deployment.\n\n## Local preparation\n\nThese commands use paths supplied by the operator; they do not depend on the author\'s `work/` directory. Set `DELIVERY` to the delivered `out/`, `A4_BASE` to the full supplied A4 directory on local scratch, `LOCAL` to a fresh local scratch directory, and `READ_PYTHON` to the approved Python executable. Both source roots and all outputs must stay on local scratch. The package contains code, not model/data archives.\n\n```bash\n: "${DELIVERY:?Absolute path to delivered out directory}"\n: "${A4_BASE:?Absolute path to the full pinned A4 directory on local scratch}"\n: "${LOCAL:?Fresh local scratch directory}"\n: "${READ_PYTHON:?Approved Python executable}"\nexport PYTHONDONTWRITEBYTECODE=1 TOKENIZERS_PARALLELISM=false\nexport OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8\nexport XDG_CACHE_HOME="$LOCAL/cache" HF_HOME="$LOCAL/cache/hf" TRITON_CACHE_DIR="$LOCAL/cache/triton"\nmkdir -p "$LOCAL/source" "$LOCAL/a4"\nnice -n 10 tar -cf - -C "$A4_BASE/src" . | nice -n 10 tar -xf - -C "$LOCAL/source"\nnice -n 10 tar -cf - -C "$A4_BASE" package tower_sequence.py fetch_return.py unpack_return.py |\n  nice -n 10 tar -xf - -C "$LOCAL/a4"\nnice -n 10 patch --batch --fuzz=0 -p1 -d "$LOCAL/source" < "$DELIVERY/patches/01_bounded_read_caches.diff"\nnice -n 10 patch --batch --fuzz=0 -p1 -d "$LOCAL/source" < "$DELIVERY/patches/02_atomic_scene_shards.diff"\nnice -n 10 patch --batch --fuzz=0 -p1 -d "$LOCAL/source" < "$DELIVERY/patches/03_production_integration.diff"\nnice -n 10 patch --batch --fuzz=0 -p1 -d "$LOCAL/a4" < "$DELIVERY/patches/04_operator_cache_bound.diff"\nnice -n 10 patch --batch --fuzz=0 -p1 -d "$LOCAL/a4" < "$DELIVERY/patches/05_operator_return_and_proof.diff"\nEXT_SOURCE="$LOCAL/source"\n```\n\nKeep the private kit, original manifests and reverse maps on Trinity. Stage each source tree as one archive and extract it only on node-local scratch. Both parity source roots must remain pristine: no build outputs, extra files or symlinks. Public paths, submission names, configuration and logs must use opaque tokens. Never transfer private reverse maps to Orchard.\n\n## Step-600 binding, build and operations\n\nThe candidate uses **A4\'s 636-item schedule, one card, caches only, general/no-requeue**. A4\'s export admission, submit helper and run settings remain intact. `a19` requires the reviewed payload hash `4498fca72a8e4b476b38f097ffdf3ff88b5aa20fc036bd196b18a5706e9fe46d`, the patched operator hashes, all copied A4 members, the base BATCH.sh and decoded bootstrap pins from MANIFEST, the exact extension inventory and the four original alias bases. It authenticates them before copying. Its batch uses cont_ops\' exact `build_r10.wrap_batch`: excluded node, EXIT log return and USR1 forwarding.\n\nThe owner supplies a **reviewed step-600 target template** in cont_ops\' `bind400_partial.json` schema: target run, step, member_directory, lineage, object, preparation_sha256, `done` and `prep_paths`. `done` and `prep_paths` are paths on Orchard; preparation_sha256 holds hashes, not paths. Use authenticated local copies of that target\'s artifact.json, whole-tar `.done` receipt and three preparation files. The helper fills configuration/archive fields from those files and checks target run/member/step and preparation hashes. Do not edit a step-200/400 receipt to manufacture step-600 evidence. No real target receipt was supplied to this CPU task.\n\n```bash\n: "${TARGET_TEMPLATE:?Reviewed target template, including Orchard done and prep_paths}"\n: "${TARGET_ARTIFACT:?Authenticated local artifact.json from target export}"\n: "${TARGET_DONE:?Authenticated local whole-tar done receipt}"\n: "${TARGET_CONFIG:?Authenticated local preparation config.json}"\n: "${TARGET_RECEIPT:?Authenticated local preparation s1_receipt.json}"\n: "${TARGET_DATA_RECEIPT:?Authenticated local data_receipt.json}"\nSTEP600_BINDING="$LOCAL/binding600.json"\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a20.py" --enable-extensions binding \\\n  --template "$TARGET_TEMPLATE" --artifact "$TARGET_ARTIFACT" --done "$TARGET_DONE" \\\n  --config "$TARGET_CONFIG" --receipt "$TARGET_RECEIPT" --data-receipt "$TARGET_DATA_RECEIPT" \\\n  --out "$STEP600_BINDING"\n: "${PACKAGE_TOKEN:?Fresh 11-16 hex characters starting with a-f}"\nPROFILE_ARGS=()  # All three caches, 12 GiB. For processor-only: PROFILE_ARGS=(--processor-only)\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a19.py" \\\n  --enable-extensions --base-operator "$LOCAL/a4" --source-root "$EXT_SOURCE" \\\n  --manifest "$DELIVERY/patches/MANIFEST.json" --extension-pins "$DELIVERY/kit_parity50/EXTENSION_PINS.json" \\\n  --export-binding "$STEP600_BINDING" --token "$PACKAGE_TOKEN" --out "$LOCAL/step600" "${PROFILE_ARGS[@]}"\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a20.py" --enable-extensions operations \\\n  --operator "$LOCAL/step600" --binding "$STEP600_BINDING" --dry-root "$DELIVERY/operations" --out "$LOCAL/ops"\nnice -n 10 tar -czf "$LOCAL/0.tgz" -C "$LOCAL/ops" .\nnice -n 10 sha256sum "$LOCAL/0.tgz"\n```\n\n`step600` retains the exact local source/operator/unpacker. `ops/1.tgz` is the package delivery, with `ops/SHA256`; the outer archive carries it and five inert scripts. The commands below are **owner operations on Orchard, unrun here**. Transfer the single outer archive through the owner\'s existing authorized transport. Set `OPS_ARCHIVE` to its received opaque path, `OPS_SHA256` to the printed local hash, and `D` to a fresh opaque operation directory. These are transport endpoints, not generated receipt values.\n\n```bash\n: "${OPS_ARCHIVE:?Received outer archive on Orchard}"\n: "${OPS_SHA256:?Printed local SHA256 of that archive}"\n: "${D:?Fresh opaque operation directory on Orchard}"\nprintf \'%s  %s\\n\' "$OPS_SHA256" "$OPS_ARCHIVE" | sha256sum -c -\ntest ! -e "$D"\nmkdir -m 700 "$D"\ntar -xzf "$OPS_ARCHIVE" -C "$D"\nbash "$D/o_place.sh"\nbash "$D/o_pull_fill.sh"\nP=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}\n# Detached worker: inspect completion no more than once per minute.\nwhile test ! -f "$P/a/1.txt"; do sleep 60; done\ntest "$(cat "$P/a/1.txt")" = 0\nbash "$D/o_cpu.sh"\n```\n\n`o_place.sh` verifies the inner archive and places it at `$P=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}`. `o_pull_fill.sh` acquires the permanent attempt lock `$P/a/0.lock`, launches one detached nohup worker, and returns its PID in `$P/a/0.txt`. The worker logs to `$P/a/0.log` and writes its exit status to `$P/a/1.txt` on success or failure. A duplicate launch refuses; a failed or interrupted attempt requires a fresh package/token, never an automatic retry. The worker copies the reviewed `done` and `prep_paths` files to `$P/a/e/{5,7,8,9}`, authenticates their pins (the `.done` receipt uses whitespace-separated fields), fetches export parts `0..3` once with retries disabled, fills through `a/4.py`, and runs cont_ops\' verbatim `dryres2.py` and `dry2.py`. A failed transfer stops; the scripts do not retry it.\n\n`o_cpu.sh` requests the A4 CPU allocation explicitly: preempt, eight CPUs, 200G, four hours, no GPU, no requeue, and the excluded nodes. The **CPU allocation** is separate from the intended **general GPU read**. Wait for the CPU job to finish successfully. Preserve `$P/a/c/CPU.json`, `MEMORY.json` and the exact `SETTINGS.json` emitted by A4 prepare. Bring these small files back as one archive through the authorized transport to `$LOCAL/step600/proof/` before the parity preparation below. The proof emits exact restore, artifact-binding, manifest and export-pin receipts. These small files authenticate staging; they do not contain model weights. The proof binds payload/plan/inputs/operator, must pass bundle/entry checks and contain `memory.read_cache_bytes=12884901888` (4294967296 for processor-only), `basis=fixed_g3t_shapes`, and `fits=true`.\n\nArchive the CPU evidence on Orchard after its successful completion, using the package token printed by the build:\n\n```bash\nP=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}\ntar -czf "$D/2.tgz" -C "$P/a/c" CPU.json MEMORY.json SETTINGS.json RESTORE.json binding.json manifest.json EXPORT_PIN.json\nsha256sum "$D/2.tgz"\n```\n\nAfter authorized transport, authenticate and extract that archive on local scratch:\n\n```bash\n: "${PROOF_ARCHIVE:?Received CPU-evidence archive on local scratch}"\n: "${PROOF_SHA256:?Printed Orchard SHA256 of the CPU-evidence archive}"\nprintf \'%s  %s\\n\' "$PROOF_SHA256" "$PROOF_ARCHIVE" | nice -n 10 sha256sum -c -\nmkdir "$LOCAL/step600/proof"\nnice -n 10 tar -xzf "$PROOF_ARCHIVE" -C "$LOCAL/step600/proof"\n```\n\nAfter the zero-difference GPU parity gate passes, transfer its token-only `ue.json` through the authorized transport as one archive, preserving the SHA256 printed on the GPU host. The authorized owner authenticates that archive and installs the receipt before submission:\n\n```bash\n: "${GATE_ARCHIVE:?Received archive containing ue.json}"\n: "${GATE_SHA256:?SHA256 printed on the GPU host}"\nprintf \'%s  %s\\n\' "$GATE_SHA256" "$GATE_ARCHIVE" | sha256sum -c -\nmkdir "$D/g"\ntar -xf "$GATE_ARCHIVE" -C "$D/g"\nP=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}\ntest ! -e "$P/a/g.json"\ncp "$D/g/ue.json" "$P/a/g.json"\n```\n\nThen run:\n\n```bash\nbash "$D/o_sub.sh"\n# After the GPU job finishes:\nbash "$D/o_fetch.sh"\nP=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}\ntar -czf "$D/3.tgz" -C "$P/a/f" 0.tgz EXIT.json\nsha256sum "$D/3.tgz"\n```\n\n`o_sub.sh` embeds cont_ops’ A4 CPU-receipt assertions verbatim, including batch/dispatch/guard pins and MEMORY.json equality, then checks cache memory and the successful GPU receipt at `$P/a/g.json`, requires both dry checks to pass, requires an empty general queue, and refuses a return pool over **75,000,000 bytes** (including errors/symlinks). It then runs `3.py check` and one `3.py submit --gpus 1 --time 04:30:00`, saving the job ID. The GPU receipt must match the CPU restore/binding pins, filled export pin, adopted plan/profile and H100 80 GB requirement. The unchanged bootstrap itself does not require the cache-memory field; this submit preflight does. `o_fetch.sh` derives the authenticated return token and fetches `$P/a/f/{0.tgz,EXIT.json}`.\n\nTransfer `$D/3.tgz` through the authorized transport, preserving the local operator directory. Authenticate, extract and unpack it locally:\n\n```bash\n: "${RETURN_ARCHIVE:?Received fetched-return archive on local scratch}"\n: "${RETURN_SHA256:?Printed Orchard SHA256 of the fetched-return archive}"\nprintf \'%s  %s\\n\' "$RETURN_SHA256" "$RETURN_ARCHIVE" | nice -n 10 sha256sum -c -\nmkdir "$LOCAL/step600/f"\nnice -n 10 tar -xzf "$RETURN_ARCHIVE" -C "$LOCAL/step600/f"\n(cd "$LOCAL/step600" && CUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -s -B ./unpack_return.py \\\n  --archive "$LOCAL/step600/f/0.tgz" --exit "$LOCAL/step600/f/EXIT.json" \\\n  --out "$LOCAL/step600/ret" > "$LOCAL/step600/unpack-success.json" && \\\n  test -s "$LOCAL/step600/unpack-success.json")\n```\n\nA refused unpack leaves its extracted tree behind. Scorers must consume only unpack\'s **success output after exit status 0**, never a directory merely because it exists; the command\'s `&&` chain enforces that handoff. A successful partial return still has `complete=false` and must not be scored as complete. The ON unpacker refuses any existing weight receipt whose verified value is not JSON true. Processor-only journals need no weight receipt. OFF behavior remains unchanged. Whole-archive identity follows A4\'s design: fill checks the sealed whole-tar constants; job/unpack admission compare against inputs.archives[0].\n\n**Forecasts:** Package D is the 580-item distance read (B5 fork, 03:30 walltime); it has **no ON route** in a19. Its one-card **estimate** is 13,813.069 s (3 h 50 min), using the measured 23.600 s/item and crediting no cache saving. The **636-item** A4 read that a19 actually builds has an **estimate** of **7,351.824 s (2 h 02 min 32 s; 11.559 s/item)**, obtained by carrying forward the supplied A4 total, with zero assumed saving. Target weights, cache costs and staging/queue delays can change it; neither forecast is a step-600 measurement.\n\n## GPU parity staging and acceptance\n\nThe gate must seal **A4 prepare\'s actual output plus the operator\'s per-read overrides** for the package being adopted. Do not supply an unrelated PRIVATE_SETTINGS.json. `a20 gate` checks the prepared bytes and exact RESTORE.json/artifact-binding bytes against CPU.json’s READY pins, checks export identity against the adopted step binding, and checks payload, plan and operator bindings. Every GPU worker rechecks those asset bytes and the artifact manifest before reading; changing paths cannot substitute another checkpoint. It applies the authenticated operator descriptor and derives `enable_caches`, `read_cache_bytes` and the full adoption profile: candidates_argmax, memo on, g3t, empty verify IDs, save_own_depth=false, and the exact cache switches. Both the parent driver and every worker refuse a different profile. Processor-only adoption is explicitly gated with slots `[0]` and 4 GiB; all-cache adoption uses `[0,1,2]` and 12 GiB.\n\nStage the exact retained CPU data on the intended GPU host; preserve the CPU logical directory so pinned manifests and restore paths stay unchanged. Do not rebuild RESTORE.json or the manifest for a different checkpoint. The following **owner-only, unrun staging commands** create one data archive on the CPU proof’s compute node. `CPU.json.root` is node-local, so run there while that directory remains available. The archive can be large; use the owner’s approved storage/transport plan.\n\n```bash\nP=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}\n/usr/bin/python3 -I -s -B - "$P" <<\'PY\'\nimport json,subprocess,sys,tarfile\nfrom pathlib import Path\np=Path(sys.argv[1]);root=Path(json.loads((p/\'a/c/CPU.json\').read_text())[\'root\'])\nwith tarfile.open(p/\'0.tgz\') as archive:cfg=json.load(archive.extractfile(\'9.json\'))\nsys.path.insert(0,str(root/\'bootstrap\'))\nfrom orchard_h10.common import template\n_,J,_,_,_=template()\nsubprocess.run(J.namespace(root)+[\'/bin/tar\',\'-chf\',str(root/\'4.tar\'),\'-C\',cfg[\'logical\']+\'/d\',\'.\'],check=True)\nprint(root/\'4.tar\')\nsubprocess.run([\'sha256sum\',str(root/\'4.tar\')],check=True)\nPY\n```\n\nTransfer that single archive through approved transport. On the assigned GPU host, extract it under the package’s exact opaque logical root, and stage the package payload there for the manifest’s code roots. `P` refers to the same filled package in the registered Orchard namespace. These commands refuse an existing destination:\n\n```bash\n: "${ASSET_ARCHIVE:?Received CPU data archive}"\n: "${ASSET_SHA256:?Printed CPU archive SHA256}"\nprintf \'%s  %s\\n\' "$ASSET_SHA256" "$ASSET_ARCHIVE" | sha256sum -c -\nGPU_LOGICAL=$(/usr/bin/python3 -I -s -B - "$P/0.tgz" <<\'PY\'\nimport json,sys,tarfile\nwith tarfile.open(sys.argv[1]) as archive:print(json.load(archive.extractfile(\'9.json\'))[\'logical\'])\nPY\n)\ntest ! -e "$GPU_LOGICAL"\nmkdir -p "$GPU_LOGICAL/d" "$GPU_LOGICAL/p"\ntar -xf "$ASSET_ARCHIVE" -C "$GPU_LOGICAL/d"\ntar -xzf "$P/0.tgz" -C "$GPU_LOGICAL/p"\ntest ! -e "$GPU_LOGICAL/d/7.json"\ncp "$GPU_LOGICAL/d/binding.json" "$GPU_LOGICAL/d/7.json"\n```\n\nCreate a private neutral configuration from `config.example.json` with separate authenticated A4 original/patched source roots. Set `export=$GPU_LOGICAL/d/e`, `export_pin=$GPU_LOGICAL/d/6.json`, and `artifact_manifest=$GPU_LOGICAL/d/7.json`. The last file is a byte-identical neutral alias for the CPU binding. Include that exact `binding.json` to `7.json` mapping in `PRIVATE_ALIASES.json`; map the other private prepared asset paths to staged opaque aliases of those same files. Keep private settings and reverse maps on Trinity. The following commands use files under `$LOCAL`:\n\n```bash\n: "${PRIVATE_CONFIG_TEMPLATE:?Private neutral GPU configuration with staged asset paths}"\n: "${PRIVATE_ALIASES:?Private JSON mapping preparation paths to staged opaque paths}"\nPRIVATE_SETTINGS="$LOCAL/PRIVATE_SETTINGS.json"\nPRIVATE_CONFIG="$LOCAL/PRIVATE_NEUTRAL_CONFIG.json"\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a20.py" --enable-extensions gate \\\n  --operator "$LOCAL/step600" --prepared "$LOCAL/step600/proof/SETTINGS.json" \\\n  --proof "$LOCAL/step600/proof/CPU.json" --config "$PRIVATE_CONFIG_TEMPLATE" \\\n  --asset-receipts "$LOCAL/step600/proof" \\\n  --settings-out "$PRIVATE_SETTINGS" --config-out "$PRIVATE_CONFIG"\n```\n\n```bash\nmkdir -p "$LOCAL/public"\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a11.py" seal \\\n  --source-root "$EXT_SOURCE" --input "$PRIVATE_SETTINGS" --aliases "$PRIVATE_ALIASES" \\\n  --out "$LOCAL/public/u3"\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a11.py" stage-kit \\\n  --source-root "$EXT_SOURCE" --input "$DELIVERY/kit_parity50" \\\n  --config "$PRIVATE_CONFIG" --out "$LOCAL/public/u0"\n```\n\nThe staged `u3.json` pins every extension; `u4.json` authenticates both full 927-file base inventories. The driver rejects changed bases, equal original/patched roots, and an original root containing extensions. It authenticates the sealed sample bytes and the logical sample pin. Transfer only the staged directory through the approved transport under an opaque root.\n\nOn an assigned **H100 80 GB** GPU, run the acceptance command below; it is **unrun here**. Preserve that allocation\'s actual `CUDA_VISIBLE_DEVICES`.\n\n```bash\nnice -n 10 "$READ_PYTHON" -I -s -B /scratch/jjyeung/ab0123456789/u0/u0.py \\\n  /scratch/jjyeung/ab0123456789/u0/u2.json --out /scratch/jjyeung/ab0123456789/u9 \\\n  --enable-gpu --public --repeat-baseline --shards 4\n```\n\nEvery arm starts a fresh process. ORIGINAL/OFF/OFF_REPEAT use ordinary journals and modulo shards. ON tests caches; ON_JOURNAL and sequential whole-scene shards test separate journal/shard features. Sequential shards establish equality, not parallel speed. Public logs tokenize item/native/room identities and arbitrary stdout/stderr. No reverse map is written on Orchard.\n\nAcceptance requires all 50 expected IDs, complete production output schemas, nonempty text/tokens/heads, scale even when null, every served response and forced-token count, matching call counters, and **zero semantic byte differences**. ORIGINAL/OFF must also retain every production source hash. Each enabled cache must report its memory bound and useful hits; SAM needs both feature and detection hits. Empty or all-miss runs fail. Only clocks and explicit audit/cache/memo telemetry are excluded from semantic comparison; audit violations fail. There is no answer/trace tolerance.\n\nEach RUN.json records the adopted package plan, read profile, asset pins, required device type, actual device, cache slots and budget. The worker checks CUDA device properties before model loading and refuses a different GPU family, compute capability or memory class. `ue.json` is written only after all comparisons finish and records whether they all passed; failed or missing receipts cannot authorize submit. Archive it with `tar -cf "$LOCAL/5.tar" -C /scratch/jjyeung/ab0123456789/u9 ue.json` and print `sha256sum "$LOCAL/5.tar"` for the authenticated return transport. Judge net time from `RUN.json`\'s `worker_wall_seconds`, which includes install/boundary hashing and eager SAM loading. Per-item timing alone cannot establish savings. ON constructs SAM outside inference mode to obtain tracked parameters; that changes loading time and potentially RNG use. The GPU byte gate must clear it. The sample overrepresents clip reuse: its ten distance items share one clip, while A4 has 150 distance items across 60 clips (review finding 7).\n\nThe cache cap covers retained cache storage and transient copies, not model/caller working memory. Measure full-process host/GPU peaks. Models must remain frozen: calls check parameter/buffer identities, pointers and counters; install/type boundaries hash content. Persistent raw writes fail at a boundary. Raw writes restored between boundaries, private tensor attributes and arbitrary non-tensor state are outside this guard\'s coverage. Graceful stops verify journals; a hard kill can leave an unchecked journal that requires fresh output.\n\nOutput directories u0–u5 represent ORIGINAL/OFF/OFF_REPEAT/ON/ON_JOURNAL/SHARDED. Reports u6–ua compare arms; ub.json checks merge equality; uc/ud contain canonical single/sharded returns. Restore on Trinity with the private inputs:\n\n```bash\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a11.py" restore \\\n  --source-root "$EXT_SOURCE" --input PRIVATE_RETURN --out "$LOCAL/restored" \\\n  --private-source "$DELIVERY/kit_parity50/sample50.json" \\\n  --private-source "$PRIVATE_CONFIG" --private-source "$PRIVATE_SETTINGS"\n```\n\nRestoration authenticates committed rows before rebuilding private IDs/checksums. Merge with the original manifest through the explicit extension entrypoint. The canonical answer/trace archive must match exactly; transport-envelope clocks remain variable.\n\n## Array validation\n\nNo multi-card A4 operator is delivered. The array helper is a separate inert prototype. Its example has `approved=false`: two one-hour shards, at most two attempts, four GPU-hours total. Approval must bind the exact partition, shards, time and attempts, with no more than five allocated GPU-hours over all attempts. Before any sharded/preempt adoption, validate real persistent-storage preemption/requeue.\n\n```bash\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a15.py" PRIVATE_ARRAY_CONFIG.json \\\n  --enable-array --token ab0123456789 --out "$LOCAL/array-plan" \\\n  --python /scratch/jjyeung/ab0123456789/u1 --source /scratch/jjyeung/ab0123456789/u2 \\\n  --staged-config /project/community/jjyeung/okh7/a15_cot_apab0123456789/u3.json\n```\n\nThis writes commands without running them. Exit 75 requests bounded requeue; other errors remain failures. Lock waits stop after 60 seconds, and the attempt limit forbids more work. Public paths must use approved roots and pass the forbidden-word screen; name checks do not establish storage permissions or capacity.\n\nNo delivered CPU suite or single-GPU kit requires a local OS socket. StageOneSocket is a Python callback. Real restore, bwrap isolation, remote transport, GPU parity/performance/memory and persistent requeue remain unrun.\n\n## Review round 6: finding -> fix -> test\n\n| Finding | Fix | Regression |\n|---|---|---|\n| 1. Unpack import fails | Run `-s -B` from the operator directory. | Execute the README command as a subprocess on an authenticated fixture return. |\n| 2. Foreground pull/fill | Detached nohup worker, permanent attempt lock, PID/log and exit file; no retries. | Success 0 and failure 17 both report completion; duplicate launch refuses. |\n| 3. Weak submit receipt | Embed every cont_ops A4 CPU assertion, then enforce cache and pool checks. | Batch/guard/action/argv/events/memory tampering and a resealed stale batch fail. |\n| 4. Unpinned copied members | Pin all A4 copied members, base batch and decoded bootstrap before output. | Mutations of each additional member and bootstrap pin refuse before writing. |\n| 5. Unbound checkpoint/device | READY restore/binding pins and export identity bind step-600 assets; workers recheck assets and require H100 80 GB. | Changed receipts, wrong step, changed staged files and non-production GPU properties fail. |\n| INFO: receipt whitespace | Compare the three whitespace-separated fields. | Tabs/newlines pass; extra fields fail. |\n| INFO: manual GPU handoff | Submit requires the successful token-only GPU receipt for the same plan/profile/assets/device. | Failed, absent, stale or mismatched evidence refuses. |\n\nThe binding retains Orchard `done`/`prep_paths` as authenticated operation metadata; admission still checks its fixed identity keys. Persistent raw writes remain boundary-checked; restored-between-boundary raw writes remain unsupported and require frozen model ownership. These informational limits do not change reader behavior.\n'

======================================================================
FAIL: test_info_receipt_records_and_submit_checks_kit_comparator_sample (__main__.Round7Tests.test_info_receipt_records_and_submit_checks_kit_comparator_sample)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round7.py", line 119, in test_info_receipt_records_and_submit_checks_kit_comparator_sample
    self.assertTrue(hasattr(self.kit,'kit_hashes'),'Receipt omits executing kit/comparator/sample bytes')
AssertionError: False is not true : Receipt omits executing kit/comparator/sample bytes

======================================================================
FAIL: test_info_unpack_ignores_python_environment_and_keeps_sibling_import (__main__.Round7Tests.test_info_unpack_ignores_python_environment_and_keeps_sibling_import)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round7.py", line 143, in test_info_unpack_ignores_python_environment_and_keeps_sibling_import
    self.assertIn(' -s -E -B ./unpack_return.py',block)
AssertionError: ' -s -E -B ./unpack_return.py' not found in ': "${RETURN_ARCHIVE:?Received fetched-return archive on local scratch}"\n: "${RETURN_SHA256:?Printed Orchard SHA256 of the fetched-return archive}"\nprintf \'%s  %s\\n\' "$RETURN_SHA256" "$RETURN_ARCHIVE" | nice -n 10 sha256sum -c -\nmkdir "$LOCAL/step600/f"\nnice -n 10 tar -xzf "$RETURN_ARCHIVE" -C "$LOCAL/step600/f"\n(cd "$LOCAL/step600" && CUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -s -B ./unpack_return.py \\\n  --archive "$LOCAL/step600/f/0.tgz" --exit "$LOCAL/step600/f/EXIT.json" \\\n  --out "$LOCAL/step600/ret" > "$LOCAL/step600/unpack-success.json" && \\\n  test -s "$LOCAL/step600/unpack-success.json")'

======================================================================
FAIL: test_rebind_step400_only (__main__.Round7Tests.test_rebind_step400_only)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round7.py", line 163, in test_rebind_step400_only
    self.assertIn('bound_export',inspect.signature(self.helper.gate).parameters,'Gate lacks reviewed export binding')
AssertionError: 'bound_export' not found in mappingproxy(OrderedDict({'operator': <Parameter "operator">, 'prepared': <Parameter "prepared">, 'proof': <Parameter "proof">, 'config_template': <Parameter "config_template">, 'settings_out': <Parameter "settings_out">, 'config_out': <Parameter "config_out">, 'asset_receipts': <Parameter "asset_receipts=None">})) : Gate lacks reviewed export binding

----------------------------------------------------------------------
Ran 8 tests in 2.520s

FAILED (failures=10)
```

Command: `bash work/cpu.sh work/run_checks.py  # round8_before; exact environment/argv in runner`

Exact output ([checks/round8_before.txt](checks/round8_before.txt)):

```text
test_f1_external_symlinks_refuse_before_archive (__main__.Round8Tests.test_f1_external_symlinks_refuse_before_archive) ... 
  test_f1_external_symlinks_refuse_before_archive (__main__.Round8Tests.test_f1_external_symlinks_refuse_before_archive) (kind='absolute') ... FAIL
  test_f1_external_symlinks_refuse_before_archive (__main__.Round8Tests.test_f1_external_symlinks_refuse_before_archive) (kind='relative') ... FAIL
  test_f1_external_symlinks_refuse_before_archive (__main__.Round8Tests.test_f1_external_symlinks_refuse_before_archive) (kind='directory') ... FAIL
  test_f1_external_symlinks_refuse_before_archive (__main__.Round8Tests.test_f1_external_symlinks_refuse_before_archive) (kind='chain') ... FAIL
  test_f1_external_symlinks_refuse_before_archive (__main__.Round8Tests.test_f1_external_symlinks_refuse_before_archive) (kind='dangling') ... FAIL
  test_f1_external_symlinks_refuse_before_archive (__main__.Round8Tests.test_f1_external_symlinks_refuse_before_archive) (kind='cycle') ... FAIL
test_f1_preserved_absolute_link_passes_real_artifact_and_load_native (__main__.Round8Tests.test_f1_preserved_absolute_link_passes_real_artifact_and_load_native) ... FAIL
test_f2_gate_authenticates_environment_before_gpu (__main__.Round8Tests.test_f2_gate_authenticates_environment_before_gpu) ... FAIL
test_f2_gpu_shell_preflight_executes_archived_interpreter (__main__.Round8Tests.test_f2_gpu_shell_preflight_executes_archived_interpreter) ... FAIL
test_f2_runtime_environment_and_receipt (__main__.Round8Tests.test_f2_runtime_environment_and_receipt) ... FAIL
test_f2_submit_checks_environment_versions_and_sha (__main__.Round8Tests.test_f2_submit_checks_environment_versions_and_sha) ... 
  test_f2_submit_checks_environment_versions_and_sha (__main__.Round8Tests.test_f2_submit_checks_environment_versions_and_sha) (field='sha256') ... FAIL
  test_f2_submit_checks_environment_versions_and_sha (__main__.Round8Tests.test_f2_submit_checks_environment_versions_and_sha) (field='torch') ... FAIL
  test_f2_submit_checks_environment_versions_and_sha (__main__.Round8Tests.test_f2_submit_checks_environment_versions_and_sha) (field='transformers') ... FAIL
  test_f2_submit_checks_environment_versions_and_sha (__main__.Round8Tests.test_f2_submit_checks_environment_versions_and_sha) (field='cuda') ... FAIL
test_f3_builder_refuses_other_export_before_reading_base (__main__.Round8Tests.test_f3_builder_refuses_other_export_before_reading_base) ... 
  test_f3_builder_refuses_other_export_before_reading_base (__main__.Round8Tests.test_f3_builder_refuses_other_export_before_reading_base) (field='step') ... FAIL
  test_f3_builder_refuses_other_export_before_reading_base (__main__.Round8Tests.test_f3_builder_refuses_other_export_before_reading_base) (field='run') ... FAIL
  test_f3_builder_refuses_other_export_before_reading_base (__main__.Round8Tests.test_f3_builder_refuses_other_export_before_reading_base) (field='member_directory') ... FAIL
  test_f3_builder_refuses_other_export_before_reading_base (__main__.Round8Tests.test_f3_builder_refuses_other_export_before_reading_base) (field='lineage') ... FAIL
  test_f3_builder_refuses_other_export_before_reading_base (__main__.Round8Tests.test_f3_builder_refuses_other_export_before_reading_base) (field='object') ... FAIL
  test_f3_builder_refuses_other_export_before_reading_base (__main__.Round8Tests.test_f3_builder_refuses_other_export_before_reading_base) (field='config_sha256') ... FAIL
  test_f3_builder_refuses_other_export_before_reading_base (__main__.Round8Tests.test_f3_builder_refuses_other_export_before_reading_base) (field='archive_sha256') ... FAIL
  test_f3_builder_refuses_other_export_before_reading_base (__main__.Round8Tests.test_f3_builder_refuses_other_export_before_reading_base) (field='archive_bytes') ... FAIL
  test_f3_builder_refuses_other_export_before_reading_base (__main__.Round8Tests.test_f3_builder_refuses_other_export_before_reading_base) (field='base_identity') ... FAIL
  test_f3_builder_refuses_other_export_before_reading_base (__main__.Round8Tests.test_f3_builder_refuses_other_export_before_reading_base) (field='frame_layout') ... FAIL
  test_f3_builder_refuses_other_export_before_reading_base (__main__.Round8Tests.test_f3_builder_refuses_other_export_before_reading_base) (field='preparation_sha256') ... FAIL
test_f3_builder_refuses_other_export_before_reading_base (__main__.Round8Tests.test_f3_builder_refuses_other_export_before_reading_base) ... FAIL
test_f4_readme_archive_path_accepts_symlinked_parent (__main__.Round8Tests.test_f4_readme_archive_path_accepts_symlinked_parent) ... FAIL
test_info_gpu_commands_and_aliases (__main__.Round8Tests.test_info_gpu_commands_and_aliases) ... FAIL
test_info_tar_stderr_is_retained (__main__.Round8Tests.test_info_tar_stderr_is_retained) ... FAIL

======================================================================
FAIL: test_f1_external_symlinks_refuse_before_archive (__main__.Round8Tests.test_f1_external_symlinks_refuse_before_archive) (kind='absolute')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 89, in test_f1_external_symlinks_refuse_before_archive
    else:self.fail('Archive accepted escaping symlink: '+kind)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Archive accepted escaping symlink: absolute

======================================================================
FAIL: test_f1_external_symlinks_refuse_before_archive (__main__.Round8Tests.test_f1_external_symlinks_refuse_before_archive) (kind='relative')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 89, in test_f1_external_symlinks_refuse_before_archive
    else:self.fail('Archive accepted escaping symlink: '+kind)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Archive accepted escaping symlink: relative

======================================================================
FAIL: test_f1_external_symlinks_refuse_before_archive (__main__.Round8Tests.test_f1_external_symlinks_refuse_before_archive) (kind='directory')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 89, in test_f1_external_symlinks_refuse_before_archive
    else:self.fail('Archive accepted escaping symlink: '+kind)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Archive accepted escaping symlink: directory

======================================================================
FAIL: test_f1_external_symlinks_refuse_before_archive (__main__.Round8Tests.test_f1_external_symlinks_refuse_before_archive) (kind='chain')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 89, in test_f1_external_symlinks_refuse_before_archive
    else:self.fail('Archive accepted escaping symlink: '+kind)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Archive accepted escaping symlink: chain

======================================================================
FAIL: test_f1_external_symlinks_refuse_before_archive (__main__.Round8Tests.test_f1_external_symlinks_refuse_before_archive) (kind='dangling')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 91, in test_f1_external_symlinks_refuse_before_archive
    self.assertTrue(err.exists(),'Symlink refusal diagnostic is missing')
AssertionError: False is not true : Symlink refusal diagnostic is missing

======================================================================
FAIL: test_f1_external_symlinks_refuse_before_archive (__main__.Round8Tests.test_f1_external_symlinks_refuse_before_archive) (kind='cycle')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 91, in test_f1_external_symlinks_refuse_before_archive
    self.assertTrue(err.exists(),'Symlink refusal diagnostic is missing')
AssertionError: False is not true : Symlink refusal diagnostic is missing

======================================================================
FAIL: test_f1_preserved_absolute_link_passes_real_artifact_and_load_native (__main__.Round8Tests.test_f1_preserved_absolute_link_passes_real_artifact_and_load_native)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 68, in test_f1_preserved_absolute_link_passes_real_artifact_and_load_native
    with self.assertRaises(PassedAdmission):parity.load_native(e,settings={'config':str(d/'config.json')},artifact=artifact)
                                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/src/b/e2e_reader/parity.py", line 131, in load_native
    raise ValueError('restore input missing from artifact: ' + str(p))
ValueError: restore input missing from artifact: /scratch/jjyeung/orch_n30/so_read/work/test-artifacts/2d729d1684444e008487ceb4c5e46dab/logical/d/e/heads.pt

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 69, in test_f1_preserved_absolute_link_passes_real_artifact_and_load_native
    except ValueError as error:self.fail('Real load_native rejected extracted link: '+str(error))
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Real load_native rejected extracted link: restore input missing from artifact: /scratch/jjyeung/orch_n30/so_read/work/test-artifacts/2d729d1684444e008487ceb4c5e46dab/logical/d/e/heads.pt

======================================================================
FAIL: test_f2_gate_authenticates_environment_before_gpu (__main__.Round8Tests.test_f2_gate_authenticates_environment_before_gpu)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 142, in test_f2_gate_authenticates_environment_before_gpu
    self.assertIn('environment',inspect.getsource(self.helper.gate),'Gate omits CPU environment receipt binding')
AssertionError: 'environment' not found in "def gate(operator, prepared, proof, config_template, settings_out, config_out, asset_receipts=None, bound_export=None):\n    package, public, cfg = package_config(operator)\n    receipt = read(proof); raw = Path(prepared).read_bytes()\n    if (receipt.get('passed') is not True or receipt['plan'] != public['plan_sha256']\n            or receipt['payload'] != public['payload_sha256'] or receipt['ready']['settings'] != sha(raw)\n            or receipt['operator_sha256'] != sha((package/'a/6.py').read_bytes())):\n        raise ValueError('Prepared settings proof differs from adopted package')\n    settings = json.loads(raw)\n    spec = importlib.util.spec_from_file_location('adopted_operator', package/'a/6.py')\n    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)\n    descriptor, = module.descriptors(str(package))\n    for key in PROFILE_KEYS[:5]:settings[key] = descriptor[key]\n    expected = {key:cfg[key] for key in PROFILE_KEYS}\n    if {key:settings.get(key) for key in PROFILE_KEYS} != expected:\n        raise ValueError('Prepared/adopted read profile differs')\n    slots = [i for i,name in enumerate(('processor','vision','sam')) if settings['read_'+name+'_cache']=='on']\n    config = read(config_template)\n    paths = (dict(restore=Path(asset_receipts)/'RESTORE.json',binding=Path(asset_receipts)/'binding.json',\n                  export_pin=Path(asset_receipts)/'EXPORT_PIN.json') if asset_receipts else\n             dict(restore=Path(config['export'])/'RESTORE.json',binding=Path(config['artifact_manifest']),\n                  export_pin=Path(config['export_pin'])))\n    assets = {key:sha(path.read_bytes()) for key,path in paths.items()}\n    inputs_path = Path(asset_receipts)/'1.json' if asset_receipts else package/'a/1.json'\n    if sha(inputs_path.read_bytes()) != receipt['inputs']:\n        raise ValueError('Gate input evidence differs from CPU proof')\n    export_pin = read(inputs_path)['export_pin']\n    if (export_pin['path'] != 'a/export.json' or assets['export_pin'] != export_pin['sha256']\n            or paths['export_pin'].stat().st_size != export_pin['bytes']):\n        raise ValueError('Staged export pin bytes differ from CPU inputs')\n    if any(assets[key] != receipt['ready'][key] for key in ('restore','binding')):\n        raise ValueError('Staged assets differ from CPU READY pins')\n    identity = read(paths['export_pin']); binding = cfg['export_binding']\n    if any(identity.get(key) != binding[key] for key in\n           ('run','step','member_directory','lineage','object','config_sha256','archive_sha256')) or any(\n            identity.get('preparation',{}).get(key,{}).get('sha256') != digest\n            for key,digest in binding['preparation_sha256'].items()):\n        raise ValueError('Staged export identity differs from adopted step binding')\n    selected = read(bound_export) if bound_export else DEFAULT_BOUND_EXPORT\n    if identity != selected:\n        raise ValueError('Staged export differs from selected export (default: reviewed step 400)')\n    config.update(enable_caches=slots, read_cache_bytes=settings['read_cache_bytes'],\n                  adoption_profile=expected, adoption_plan_sha256=public['plan_sha256'],\n                  adoption_kit=cfg['gate_kit_sha256'],\n                  adoption_assets=assets, required_device_type='H100_80GB')\n    write(settings_out, settings); write(config_out, config)\n    return config\n" : Gate omits CPU environment receipt binding

======================================================================
FAIL: test_f2_gpu_shell_preflight_executes_archived_interpreter (__main__.Round8Tests.test_f2_gpu_shell_preflight_executes_archived_interpreter)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 128, in test_f2_gpu_shell_preflight_executes_archived_interpreter
    self.assertTrue(host_path.is_file(),'Preflight lacks A4 namespace launcher')
AssertionError: False is not true : Preflight lacks A4 namespace launcher

======================================================================
FAIL: test_f2_runtime_environment_and_receipt (__main__.Round8Tests.test_f2_runtime_environment_and_receipt)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 103, in test_f2_runtime_environment_and_receipt
    self.assertTrue(hasattr(self.kit,'validate_environment'),'GPU environment lacks a preflight')
AssertionError: False is not true : GPU environment lacks a preflight

======================================================================
FAIL: test_f2_submit_checks_environment_versions_and_sha (__main__.Round8Tests.test_f2_submit_checks_environment_versions_and_sha) (field='sha256')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 164, in test_f2_submit_checks_environment_versions_and_sha
    with self.subTest(field=field):self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'Submit ignored '+field)
                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 0 == 0 : Submit ignored sha256

======================================================================
FAIL: test_f2_submit_checks_environment_versions_and_sha (__main__.Round8Tests.test_f2_submit_checks_environment_versions_and_sha) (field='torch')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 164, in test_f2_submit_checks_environment_versions_and_sha
    with self.subTest(field=field):self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'Submit ignored '+field)
                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 0 == 0 : Submit ignored torch

======================================================================
FAIL: test_f2_submit_checks_environment_versions_and_sha (__main__.Round8Tests.test_f2_submit_checks_environment_versions_and_sha) (field='transformers')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 164, in test_f2_submit_checks_environment_versions_and_sha
    with self.subTest(field=field):self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'Submit ignored '+field)
                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 0 == 0 : Submit ignored transformers

======================================================================
FAIL: test_f2_submit_checks_environment_versions_and_sha (__main__.Round8Tests.test_f2_submit_checks_environment_versions_and_sha) (field='cuda')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 164, in test_f2_submit_checks_environment_versions_and_sha
    with self.subTest(field=field):self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'Submit ignored '+field)
                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 0 == 0 : Submit ignored cuda

======================================================================
FAIL: test_f3_builder_refuses_other_export_before_reading_base (__main__.Round8Tests.test_f3_builder_refuses_other_export_before_reading_base) (field='step')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 180, in test_f3_builder_refuses_other_export_before_reading_base
    self.builder.build(root/'absent-base',SRC,root/'binding.json',root/'output','ab0123456789',enable_extensions=True)
  File "/scratch/jjyeung/orch_n30/so_read/work/round8-before-u0/a19.py", line 152, in build
    original = (base/'package/0.tgz').read_bytes()
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/pathlib.py", line 1019, in read_bytes
    with self.open(mode='rb') as f:
         ^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py", line 26, in open_path
    stream=original_open(path,mode,*args,**kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/pathlib.py", line 1013, in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/db739ea6dfc44361b4dcf89e9d7dbecc/absent-base/package/0.tgz'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 181, in test_f3_builder_refuses_other_export_before_reading_base
    except FileNotFoundError:self.fail('Builder read the base before rejecting another export: '+key)
                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Builder read the base before rejecting another export: step

======================================================================
FAIL: test_f3_builder_refuses_other_export_before_reading_base (__main__.Round8Tests.test_f3_builder_refuses_other_export_before_reading_base) (field='run')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 180, in test_f3_builder_refuses_other_export_before_reading_base
    self.builder.build(root/'absent-base',SRC,root/'binding.json',root/'output','ab0123456789',enable_extensions=True)
  File "/scratch/jjyeung/orch_n30/so_read/work/round8-before-u0/a19.py", line 152, in build
    original = (base/'package/0.tgz').read_bytes()
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/pathlib.py", line 1019, in read_bytes
    with self.open(mode='rb') as f:
         ^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py", line 26, in open_path
    stream=original_open(path,mode,*args,**kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/pathlib.py", line 1013, in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/92058b94d42e47c99b37b2c66f27004a/absent-base/package/0.tgz'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 181, in test_f3_builder_refuses_other_export_before_reading_base
    except FileNotFoundError:self.fail('Builder read the base before rejecting another export: '+key)
                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Builder read the base before rejecting another export: run

======================================================================
FAIL: test_f3_builder_refuses_other_export_before_reading_base (__main__.Round8Tests.test_f3_builder_refuses_other_export_before_reading_base) (field='member_directory')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 180, in test_f3_builder_refuses_other_export_before_reading_base
    self.builder.build(root/'absent-base',SRC,root/'binding.json',root/'output','ab0123456789',enable_extensions=True)
  File "/scratch/jjyeung/orch_n30/so_read/work/round8-before-u0/a19.py", line 152, in build
    original = (base/'package/0.tgz').read_bytes()
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/pathlib.py", line 1019, in read_bytes
    with self.open(mode='rb') as f:
         ^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py", line 26, in open_path
    stream=original_open(path,mode,*args,**kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/pathlib.py", line 1013, in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/d42e4a933b3f4cbca822f7ed394e54c4/absent-base/package/0.tgz'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 181, in test_f3_builder_refuses_other_export_before_reading_base
    except FileNotFoundError:self.fail('Builder read the base before rejecting another export: '+key)
                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Builder read the base before rejecting another export: member_directory

======================================================================
FAIL: test_f3_builder_refuses_other_export_before_reading_base (__main__.Round8Tests.test_f3_builder_refuses_other_export_before_reading_base) (field='lineage')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 180, in test_f3_builder_refuses_other_export_before_reading_base
    self.builder.build(root/'absent-base',SRC,root/'binding.json',root/'output','ab0123456789',enable_extensions=True)
  File "/scratch/jjyeung/orch_n30/so_read/work/round8-before-u0/a19.py", line 152, in build
    original = (base/'package/0.tgz').read_bytes()
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/pathlib.py", line 1019, in read_bytes
    with self.open(mode='rb') as f:
         ^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py", line 26, in open_path
    stream=original_open(path,mode,*args,**kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/pathlib.py", line 1013, in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/04c33c8087c0403e86284acbaf5370fe/absent-base/package/0.tgz'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 181, in test_f3_builder_refuses_other_export_before_reading_base
    except FileNotFoundError:self.fail('Builder read the base before rejecting another export: '+key)
                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Builder read the base before rejecting another export: lineage

======================================================================
FAIL: test_f3_builder_refuses_other_export_before_reading_base (__main__.Round8Tests.test_f3_builder_refuses_other_export_before_reading_base) (field='object')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 180, in test_f3_builder_refuses_other_export_before_reading_base
    self.builder.build(root/'absent-base',SRC,root/'binding.json',root/'output','ab0123456789',enable_extensions=True)
  File "/scratch/jjyeung/orch_n30/so_read/work/round8-before-u0/a19.py", line 152, in build
    original = (base/'package/0.tgz').read_bytes()
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/pathlib.py", line 1019, in read_bytes
    with self.open(mode='rb') as f:
         ^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py", line 26, in open_path
    stream=original_open(path,mode,*args,**kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/pathlib.py", line 1013, in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/7d9e166d3b794dae874190d04d6c880f/absent-base/package/0.tgz'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 181, in test_f3_builder_refuses_other_export_before_reading_base
    except FileNotFoundError:self.fail('Builder read the base before rejecting another export: '+key)
                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Builder read the base before rejecting another export: object

======================================================================
FAIL: test_f3_builder_refuses_other_export_before_reading_base (__main__.Round8Tests.test_f3_builder_refuses_other_export_before_reading_base) (field='config_sha256')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 180, in test_f3_builder_refuses_other_export_before_reading_base
    self.builder.build(root/'absent-base',SRC,root/'binding.json',root/'output','ab0123456789',enable_extensions=True)
  File "/scratch/jjyeung/orch_n30/so_read/work/round8-before-u0/a19.py", line 152, in build
    original = (base/'package/0.tgz').read_bytes()
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/pathlib.py", line 1019, in read_bytes
    with self.open(mode='rb') as f:
         ^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py", line 26, in open_path
    stream=original_open(path,mode,*args,**kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/pathlib.py", line 1013, in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/7904254e26f040f08af168aecf269967/absent-base/package/0.tgz'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 181, in test_f3_builder_refuses_other_export_before_reading_base
    except FileNotFoundError:self.fail('Builder read the base before rejecting another export: '+key)
                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Builder read the base before rejecting another export: config_sha256

======================================================================
FAIL: test_f3_builder_refuses_other_export_before_reading_base (__main__.Round8Tests.test_f3_builder_refuses_other_export_before_reading_base) (field='archive_sha256')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 180, in test_f3_builder_refuses_other_export_before_reading_base
    self.builder.build(root/'absent-base',SRC,root/'binding.json',root/'output','ab0123456789',enable_extensions=True)
  File "/scratch/jjyeung/orch_n30/so_read/work/round8-before-u0/a19.py", line 152, in build
    original = (base/'package/0.tgz').read_bytes()
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/pathlib.py", line 1019, in read_bytes
    with self.open(mode='rb') as f:
         ^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py", line 26, in open_path
    stream=original_open(path,mode,*args,**kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/pathlib.py", line 1013, in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/0c238a8df42142878b69571ff687638b/absent-base/package/0.tgz'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 181, in test_f3_builder_refuses_other_export_before_reading_base
    except FileNotFoundError:self.fail('Builder read the base before rejecting another export: '+key)
                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Builder read the base before rejecting another export: archive_sha256

======================================================================
FAIL: test_f3_builder_refuses_other_export_before_reading_base (__main__.Round8Tests.test_f3_builder_refuses_other_export_before_reading_base) (field='archive_bytes')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 180, in test_f3_builder_refuses_other_export_before_reading_base
    self.builder.build(root/'absent-base',SRC,root/'binding.json',root/'output','ab0123456789',enable_extensions=True)
  File "/scratch/jjyeung/orch_n30/so_read/work/round8-before-u0/a19.py", line 152, in build
    original = (base/'package/0.tgz').read_bytes()
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/pathlib.py", line 1019, in read_bytes
    with self.open(mode='rb') as f:
         ^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py", line 26, in open_path
    stream=original_open(path,mode,*args,**kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/pathlib.py", line 1013, in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/9241fc5ab3f74ee091f1450706dae9a8/absent-base/package/0.tgz'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 181, in test_f3_builder_refuses_other_export_before_reading_base
    except FileNotFoundError:self.fail('Builder read the base before rejecting another export: '+key)
                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Builder read the base before rejecting another export: archive_bytes

======================================================================
FAIL: test_f3_builder_refuses_other_export_before_reading_base (__main__.Round8Tests.test_f3_builder_refuses_other_export_before_reading_base) (field='base_identity')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 180, in test_f3_builder_refuses_other_export_before_reading_base
    self.builder.build(root/'absent-base',SRC,root/'binding.json',root/'output','ab0123456789',enable_extensions=True)
  File "/scratch/jjyeung/orch_n30/so_read/work/round8-before-u0/a19.py", line 152, in build
    original = (base/'package/0.tgz').read_bytes()
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/pathlib.py", line 1019, in read_bytes
    with self.open(mode='rb') as f:
         ^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py", line 26, in open_path
    stream=original_open(path,mode,*args,**kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/pathlib.py", line 1013, in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/e6bd03ec2e0a4278b970350cd0d4ccb2/absent-base/package/0.tgz'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 181, in test_f3_builder_refuses_other_export_before_reading_base
    except FileNotFoundError:self.fail('Builder read the base before rejecting another export: '+key)
                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Builder read the base before rejecting another export: base_identity

======================================================================
FAIL: test_f3_builder_refuses_other_export_before_reading_base (__main__.Round8Tests.test_f3_builder_refuses_other_export_before_reading_base) (field='frame_layout')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 180, in test_f3_builder_refuses_other_export_before_reading_base
    self.builder.build(root/'absent-base',SRC,root/'binding.json',root/'output','ab0123456789',enable_extensions=True)
  File "/scratch/jjyeung/orch_n30/so_read/work/round8-before-u0/a19.py", line 152, in build
    original = (base/'package/0.tgz').read_bytes()
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/pathlib.py", line 1019, in read_bytes
    with self.open(mode='rb') as f:
         ^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py", line 26, in open_path
    stream=original_open(path,mode,*args,**kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/pathlib.py", line 1013, in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/fd36bc83a56e45eeb12d9dba4758940f/absent-base/package/0.tgz'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 181, in test_f3_builder_refuses_other_export_before_reading_base
    except FileNotFoundError:self.fail('Builder read the base before rejecting another export: '+key)
                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Builder read the base before rejecting another export: frame_layout

======================================================================
FAIL: test_f3_builder_refuses_other_export_before_reading_base (__main__.Round8Tests.test_f3_builder_refuses_other_export_before_reading_base) (field='preparation_sha256')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 180, in test_f3_builder_refuses_other_export_before_reading_base
    self.builder.build(root/'absent-base',SRC,root/'binding.json',root/'output','ab0123456789',enable_extensions=True)
  File "/scratch/jjyeung/orch_n30/so_read/work/round8-before-u0/a19.py", line 152, in build
    original = (base/'package/0.tgz').read_bytes()
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/pathlib.py", line 1019, in read_bytes
    with self.open(mode='rb') as f:
         ^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py", line 26, in open_path
    stream=original_open(path,mode,*args,**kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/pathlib.py", line 1013, in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/f2b3d0572eb44459addf0a0f5a246504/absent-base/package/0.tgz'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 181, in test_f3_builder_refuses_other_export_before_reading_base
    except FileNotFoundError:self.fail('Builder read the base before rejecting another export: '+key)
                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Builder read the base before rejecting another export: preparation_sha256

======================================================================
FAIL: test_f3_builder_refuses_other_export_before_reading_base (__main__.Round8Tests.test_f3_builder_refuses_other_export_before_reading_base)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 183, in test_f3_builder_refuses_other_export_before_reading_base
    self.assertNotIn('--bound-export',(OUT/'kit_parity50/README.md').read_text())
AssertionError: '--bound-export' unexpectedly found in 'The GPU kit is unrun. It requires zero answer/trace byte differences. Its 50 items cover ten items per type and twelve captures; this reuse-heavy sample does not predict full-read throughput.\n\nUse the full **A4/src** base pinned by `BASE_PIN.json`. The reader patches also apply to the inspected B5 source subset, but this kit does not authenticate a B5 base. Apply patches 01–03 to a separate source copy. They add `u0/`; all original reader files remain byte-identical. Apply 04–05 to a separate A4 operator copy, outside `src`.\n\nThe ordinary entrypoint stays OFF and imports no extension. `u0/a8.py --enable-extensions` explicitly selects the extensions; individual cache settings then default OFF. The ON environment records an extension source hash. Rebuild payload and artifact pins before deployment.\n\n## Local preparation\n\nThese commands use paths supplied by the operator; they do not depend on the author\'s `work/` directory. Set `DELIVERY` to the delivered `out/`, `A4_BASE` to the full supplied A4 directory on local scratch, `LOCAL` to a fresh local scratch directory, and `READ_PYTHON` to the approved Python executable. Both source roots and all outputs must stay on local scratch. The package contains code, not model/data archives.\n\n```bash\nset -euo pipefail\n: "${DELIVERY:?Absolute path to delivered out directory}"\n: "${A4_BASE:?Absolute path to the full pinned A4 directory on local scratch}"\n: "${LOCAL:?Fresh local scratch directory}"\n: "${READ_PYTHON:?Approved Python executable}"\nexport PYTHONDONTWRITEBYTECODE=1 TOKENIZERS_PARALLELISM=false\nexport OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8\nexport XDG_CACHE_HOME="$LOCAL/cache" HF_HOME="$LOCAL/cache/hf" TRITON_CACHE_DIR="$LOCAL/cache/triton"\nmkdir -p "$LOCAL/source" "$LOCAL/a4"\nnice -n 10 tar -cf - -C "$A4_BASE/src" . | nice -n 10 tar -xf - -C "$LOCAL/source"\nnice -n 10 tar -cf - -C "$A4_BASE" package tower_sequence.py fetch_return.py unpack_return.py |\n  nice -n 10 tar -xf - -C "$LOCAL/a4"\nnice -n 10 patch --batch --fuzz=0 -p1 -d "$LOCAL/source" < "$DELIVERY/patches/01_bounded_read_caches.diff"\nnice -n 10 patch --batch --fuzz=0 -p1 -d "$LOCAL/source" < "$DELIVERY/patches/02_atomic_scene_shards.diff"\nnice -n 10 patch --batch --fuzz=0 -p1 -d "$LOCAL/source" < "$DELIVERY/patches/03_production_integration.diff"\nnice -n 10 patch --batch --fuzz=0 -p1 -d "$LOCAL/a4" < "$DELIVERY/patches/04_operator_cache_bound.diff"\nnice -n 10 patch --batch --fuzz=0 -p1 -d "$LOCAL/a4" < "$DELIVERY/patches/05_operator_return_and_proof.diff"\nEXT_SOURCE="$LOCAL/source"\n```\n\nKeep the private kit, original manifests and reverse maps on Trinity. Stage each source tree as one archive and extract it only on node-local scratch. Both parity source roots must remain pristine: no build outputs, extra files or symlinks. Public paths, submission names, configuration and logs must use opaque tokens. Never transfer private reverse maps to Orchard.\n\n## Bound export, build and operations\n\nThe candidate uses **A4\'s 636-item schedule, one card, caches only, general/no-requeue**. A4\'s export admission, submit helper and run settings remain intact. `a19` requires the reviewed payload hash `4498fca72a8e4b476b38f097ffdf3ff88b5aa20fc036bd196b18a5706e9fe46d`, the patched operator hashes, all copied A4 members, the base BATCH.sh and decoded bootstrap pins from MANIFEST, the exact extension inventory and the four original alias bases. It authenticates them before copying. Its batch uses cont_ops\' exact `build_r10.wrap_batch`: excluded node, EXIT log return and USR1 forwarding.\n\nThe gate defaults to **step 400**, read A of job **173060**, source package **a15_cot_apdc76460c3a164**. Its artifact SHA256 is **5083243cfedd2a389dfca579c5452e7d0c73b03a58e1cb7d204292ddd10e67cd**. `operations/BOUND_EXPORT.json` preserves the supplied export pin. `operations/binding.default.json` combines that identity, the four archive-part sizes in the supplied `a/1.json`, and the reviewed `bind400_partial.json` operation paths. `DEFAULT_EXPORT_PROVENANCE.json` records all source hashes. These are authenticated metadata; production weights were not restored here.\n\n`BOUND_EXPORT` selects the gate\'s exact reviewed export.json; `EXPORT_BINDING` selects the matching build/fill binding. For another reviewed export, including step 600, supply both parameters. The gate refuses a package whose export differs from the selected pin. A fresh package token identifies the ON build; it does not reuse the source package\'s token.\n\n```bash\nset -euo pipefail\nBOUND_EXPORT=${BOUND_EXPORT:-"$DELIVERY/operations/BOUND_EXPORT.json"}\nEXPORT_BINDING=${EXPORT_BINDING:-"$DELIVERY/operations/binding.default.json"}\n: "${PACKAGE_TOKEN:?Fresh 11-16 hex characters starting with a-f}"\nPROFILE_ARGS=()  # All three caches, 12 GiB. For processor-only: PROFILE_ARGS=(--processor-only)\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a19.py" \\\n  --enable-extensions --base-operator "$LOCAL/a4" --source-root "$EXT_SOURCE" \\\n  --manifest "$DELIVERY/patches/MANIFEST.json" --extension-pins "$DELIVERY/kit_parity50/EXTENSION_PINS.json" \\\n  --export-binding "$EXPORT_BINDING" --token "$PACKAGE_TOKEN" --out "$LOCAL/adopted" "${PROFILE_ARGS[@]}"\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a20.py" --enable-extensions operations \\\n  --operator "$LOCAL/adopted" --binding "$EXPORT_BINDING" --dry-root "$DELIVERY/operations" --out "$LOCAL/ops"\nnice -n 10 tar -czf "$LOCAL/0.tgz" -C "$LOCAL/ops" .\nnice -n 10 sha256sum "$LOCAL/0.tgz"\n```\n\nFor a different target, derive `EXPORT_BINDING` from its reviewed template and authenticated local receipts before the build block above, and set `BOUND_EXPORT` to that target\'s reviewed export.json:\n\n```bash\nset -euo pipefail\n: "${TARGET_TEMPLATE:?Reviewed target template, including Orchard done and prep_paths}"\n: "${TARGET_ARTIFACT:?Authenticated local artifact.json}"\n: "${TARGET_DONE:?Authenticated local whole-tar done receipt}"\n: "${TARGET_CONFIG:?Authenticated preparation config.json}"\n: "${TARGET_RECEIPT:?Authenticated preparation receipt}"\n: "${TARGET_DATA_RECEIPT:?Authenticated data receipt}"\n: "${EXPORT_BINDING:?Fresh output binding path for the selected target}"\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a20.py" --enable-extensions binding \\\n  --template "$TARGET_TEMPLATE" --artifact "$TARGET_ARTIFACT" --done "$TARGET_DONE" \\\n  --config "$TARGET_CONFIG" --receipt "$TARGET_RECEIPT" --data-receipt "$TARGET_DATA_RECEIPT" \\\n  --out "$EXPORT_BINDING"\n```\n\n`adopted` retains the exact local source/operator/unpacker. `ops/1.tgz` is the package delivery, with `ops/SHA256`; the outer archive carries it and five inert scripts. The commands below are **owner operations on Orchard, unrun here**. Transfer the single outer archive through the owner\'s existing authorized transport. Set `OPS_ARCHIVE` to its received opaque path, `OPS_SHA256` to the printed local hash, and `D` to a fresh opaque operation directory. These are transport endpoints, not generated receipt values.\n\n```bash\nset -euo pipefail\n: "${OPS_ARCHIVE:?Received outer archive on Orchard}"\n: "${OPS_SHA256:?Printed local SHA256 of that archive}"\n: "${D:?Fresh opaque operation directory on Orchard}"\n: "${PACKAGE_TOKEN:?Copy the fresh build token to this Orchard shell}"\nprintf \'%s  %s\\n\' "$OPS_SHA256" "$OPS_ARCHIVE" | sha256sum -c -\ntest ! -e "$D"\nmkdir -m 700 "$D"\ntar -xzf "$OPS_ARCHIVE" -C "$D"\nbash "$D/o_place.sh"\nbash "$D/o_pull_fill.sh"\n# BEGIN FILL_WAIT\n: "${PACKAGE_TOKEN:?Copy the fresh build token to this Orchard shell}"\nP=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}\nFILL_MAX_SECONDS=${FILL_MAX_SECONDS:-14400}\n[[ "$FILL_MAX_SECONDS" =~ ^[0-9]+$ ]] && (( FILL_MAX_SECONDS >= 1 && FILL_MAX_SECONDS <= 14400 )) || exit 1\nFILL_DEADLINE=$((SECONDS + FILL_MAX_SECONDS))\nwhile test ! -f "$P/a/1.txt"; do\n  FILL_PID=$(cat "$P/a/0.txt") || exit 1\n  [[ "$FILL_PID" =~ ^[1-9][0-9]*$ ]] || exit 1\n  if ! kill -0 "$FILL_PID" 2>/dev/null && test ! -f "$P/a/1.txt"; then\n    echo \'Fill worker is gone without an exit receipt\' >&2; exit 1\n  fi\n  if (( SECONDS >= FILL_DEADLINE )); then\n    echo \'Fill wait exceeded its maximum\' >&2; exit 1\n  fi\n  FILL_REMAIN=$((FILL_DEADLINE - SECONDS))\n  sleep "$(( FILL_REMAIN < 60 ? FILL_REMAIN : 60 ))"\ndone\ntest "$(cat "$P/a/1.txt")" = 0\n# END FILL_WAIT\nbash "$D/o_cpu.sh"\n```\n\n`o_place.sh` verifies the inner archive and places it at `$P=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}`. `o_pull_fill.sh` acquires the permanent attempt lock `$P/a/0.lock`, launches one detached nohup worker, and returns its PID in `$P/a/0.txt`. The worker logs to `$P/a/0.log` and writes its exit status to `$P/a/1.txt` on success or failure. Run the wait on the same host that launched the detached worker. It checks at most once per minute, refuses a vanished PID without `1.txt`, and stops after at most 14,400 seconds (four hours). A duplicate launch refuses; a failed or interrupted attempt requires a fresh package/token, never an automatic retry. The worker copies the reviewed `done` and `prep_paths` files to `$P/a/e/{5,7,8,9}`, authenticates their pins (the `.done` receipt uses whitespace-separated fields), fetches export parts `0..3` once with retries disabled, fills through `a/4.py`, and runs cont_ops\' verbatim `dryres2.py` and `dry2.py`. A failed transfer stops; the scripts do not retry it.\n\n`o_cpu.sh` requests the A4 CPU allocation explicitly: preempt, eight CPUs, 200G, four hours, no GPU, no requeue, and the excluded nodes. The **CPU allocation** is separate from the intended **general GPU read**. Wait for the CPU job to finish successfully. Preserve `$P/a/c/CPU.json`, `MEMORY.json` and the exact `SETTINGS.json` emitted by A4 prepare. Bring these small files back as one archive through the authorized transport to `$LOCAL/adopted/proof/` before the parity preparation below. Before writing CPU.json, the ON proof streams `logical/d` through its live `J.namespace(root)` to the named shared staging path `$P/a/4.tar`, outside the capped return pool. It dereferences symlinks and records `gate_assets.path`, `logical`, `sha256` and `bytes` in CPU.json. The output file is opened outside bwrap and tar writes to that descriptor. This uses the same preparation/READY as the proof, without a second staging job. A tar failure leaves no successful CPU.json and is not retried. The proof also emits exact `a/1.json`, restore, artifact-binding, manifest and export-pin receipts. These small files authenticate staging; they do not contain model weights. The proof binds payload/plan/inputs/operator, must pass bundle/entry checks and contain `memory.read_cache_bytes=12884901888` (4294967296 for processor-only), `basis=fixed_g3t_shapes`, and `fits=true`.\n\nArchive the CPU evidence on Orchard after its successful completion, using the package token printed by the build:\n\n```bash\nset -euo pipefail\nP=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}\ntar -czf "$D/2.tgz" -C "$P/a/c" CPU.json MEMORY.json SETTINGS.json RESTORE.json binding.json manifest.json EXPORT_PIN.json 1.json\nsha256sum "$D/2.tgz"\n```\n\nAfter authorized transport, authenticate and extract that archive on local scratch:\n\n```bash\nset -euo pipefail\n: "${PROOF_ARCHIVE:?Received CPU-evidence archive on local scratch}"\n: "${PROOF_SHA256:?Printed Orchard SHA256 of the CPU-evidence archive}"\nprintf \'%s  %s\\n\' "$PROOF_SHA256" "$PROOF_ARCHIVE" | nice -n 10 sha256sum -c -\nmkdir "$LOCAL/adopted/proof"\nnice -n 10 tar -xzf "$PROOF_ARCHIVE" -C "$LOCAL/adopted/proof"\n```\n\nAfter the zero-difference GPU parity gate passes, transfer its token-only `ue.json` through the authorized transport as one archive, preserving the SHA256 printed on the GPU host. The authorized owner authenticates that archive and installs the receipt before submission:\n\n```bash\nset -euo pipefail\n: "${GATE_ARCHIVE:?Received archive containing ue.json}"\n: "${GATE_SHA256:?SHA256 printed on the GPU host}"\nprintf \'%s  %s\\n\' "$GATE_SHA256" "$GATE_ARCHIVE" | sha256sum -c -\nmkdir "$D/g"\ntar -xf "$GATE_ARCHIVE" -C "$D/g"\nP=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}\ntest ! -e "$P/a/g.json"\ncp "$D/g/ue.json" "$P/a/g.json"\n```\n\nThen run:\n\n```bash\nset -euo pipefail\nbash "$D/o_sub.sh"\n# After the GPU job finishes:\nbash "$D/o_fetch.sh"\nP=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}\ntar -czf "$D/3.tgz" -C "$P/a/f" 0.tgz EXIT.json\nsha256sum "$D/3.tgz"\n```\n\n`o_sub.sh` embeds cont_ops’ A4 CPU-receipt assertions verbatim, including batch/dispatch/guard pins and MEMORY.json equality, then checks cache memory and the successful GPU receipt at `$P/a/g.json`, requires both dry checks to pass, requires an empty general queue, and refuses a return pool over **75,000,000 bytes** (including errors/symlinks). It then runs `3.py check` and one `3.py submit --gpus 1 --time 04:30:00`, saving the job ID. The GPU receipt must match the CPU restore/binding pins, filled export pin, adopted plan/profile and H100 80 GB requirement. The unchanged bootstrap itself does not require the cache-memory field; this submit preflight does. `o_fetch.sh` derives the authenticated return token and fetches `$P/a/f/{0.tgz,EXIT.json}`.\n\nTransfer `$D/3.tgz` through the authorized transport, preserving the local operator directory. Authenticate, extract and unpack it locally:\n\n```bash\nset -euo pipefail\n: "${RETURN_ARCHIVE:?Received fetched-return archive on local scratch}"\n: "${RETURN_SHA256:?Printed Orchard SHA256 of the fetched-return archive}"\nprintf \'%s  %s\\n\' "$RETURN_SHA256" "$RETURN_ARCHIVE" | nice -n 10 sha256sum -c -\nmkdir "$LOCAL/adopted/f"\nnice -n 10 tar -xzf "$RETURN_ARCHIVE" -C "$LOCAL/adopted/f"\n(cd "$LOCAL/adopted" && CUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -s -E -B ./unpack_return.py \\\n  --archive "$LOCAL/adopted/f/0.tgz" --exit "$LOCAL/adopted/f/EXIT.json" \\\n  --out "$LOCAL/adopted/ret" > "$LOCAL/adopted/unpack-success.json" && \\\n  test -s "$LOCAL/adopted/unpack-success.json")\n```\n\nA refused unpack leaves its extracted tree behind. Scorers must consume only unpack\'s **success output after exit status 0**, never a directory merely because it exists; the command\'s `&&` chain enforces that handoff. A successful partial return still has `complete=false` and must not be scored as complete. The ON unpacker refuses any existing weight receipt whose verified value is not JSON true. Processor-only journals need no weight receipt. OFF behavior remains unchanged. Whole-archive identity follows A4\'s design: fill checks the sealed whole-tar constants; job/unpack admission compare against inputs.archives[0].\n\n**Forecasts:** Package D is the 580-item distance read (B5 fork, 03:30 walltime); it has **no ON route** in a19. Its one-card **estimate** is 13,813.069 s (3 h 50 min), using the measured 23.600 s/item and crediting no cache saving. The **636-item** A4 read that a19 actually builds has an **estimate** of **7,351.824 s (2 h 02 min 32 s; 11.559 s/item)**, obtained by carrying forward the supplied A4 total, with zero assumed saving. Target weights, cache costs and staging/queue delays can change it; neither forecast measures the selected export.\n\n## GPU parity staging and acceptance\n\nThe gate must seal **A4 prepare\'s actual output plus the operator\'s per-read overrides** for the package being adopted. Do not supply an unrelated PRIVATE_SETTINGS.json. `a20 gate` checks the prepared bytes and exact RESTORE.json/artifact-binding bytes against CPU.json’s READY pins, checks export identity against the adopted step binding, checks the export-pin hash and byte count against the exact `a/1.json` bytes authenticated by CPU.json, and checks payload, plan and operator bindings. The selected export defaults to the pinned step-400 export; `--bound-export` explicitly changes it. Every GPU worker rechecks those asset bytes and the artifact manifest before reading; changing paths cannot substitute another checkpoint. It applies the authenticated operator descriptor and derives `enable_caches`, `read_cache_bytes` and the full adoption profile: candidates_argmax, memo on, g3t, empty verify IDs, save_own_depth=false, and the exact cache switches. Both the parent driver and every worker refuse a different profile. Processor-only adoption is explicitly gated with slots `[0]` and 4 GiB; all-cache adoption uses `[0,1,2]` and 12 GiB.\n\nThe **owner-only commands below are unrun here**. The shared asset archive already exists when CPU.json appears; never try to reopen the CPU job\'s private `/tmp`. Reserve storage for the archive before running `o_cpu.sh`. Its size is recorded by the job; no production archive size was measured here.\n\nAllocate the gate on Orchard, then enter its compute task. This is one non-requeued H100 job, eight CPUs, 200G and a five-hour maximum. Preserve its actual `CUDA_VISIBLE_DEVICES`; the Python guard requires exactly `NVIDIA H100 80GB HBM3`, 132 SMs, capability 9.0 and the 80 GB memory class.\n\n```bash\nset -euo pipefail\nsalloc --account=mt01 --partition=general --nodes=1 --ntasks=1 --cpus-per-task=8 \\\n  --mem=200G --gres=gpu:1 --time=05:00:00 --no-requeue \\\n  --exclude=orchard-community-2 --job-name=ab0123456789 \\\n  srun --ntasks=1 --pty bash --noprofile --norc\n```\n\nOn that H100 host, `/scratch/jjyeung` must **physically exist and be writable** outside bwrap. A4 creates `/scratch` only inside its namespace; it does not satisfy this host requirement. The operator must provision the host path before the gate. The exact logical root (currently `/scratch/jjyeung/b01ec87a6f29b`) must be absent so extraction cannot overlay another run. Preserve it so manifests and restore paths remain valid. Provision the separate opaque kit/source directories there too. Stage the source trees and public kit as single authenticated archives; keep private inputs and reverse maps on Trinity.\n\nThe shared path `$P/a/4.tar` is visible directly on Orchard. If approved transport copies it, set `ASSET_ARCHIVE` to that received path; CPU.json still supplies the expected hash and bytes. Run inside the allocation:\n\n```bash\nset -euo pipefail\n: "${PACKAGE_TOKEN:?Fresh package token from the build}"\nP=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}\nASSET_ARCHIVE=${ASSET_ARCHIVE:-"$P/a/4.tar"}\nGPU_LOGICAL=$(/usr/bin/python3 -I -s -B - "$P" "$ASSET_ARCHIVE" <<\'PYASSET\'\nimport hashlib,json,sys,tarfile\nfrom pathlib import Path\np=Path(sys.argv[1]);archive=Path(sys.argv[2]);proof=json.loads((p/\'a/c/CPU.json\').read_text())\nassert proof[\'passed\'] is True\nwith tarfile.open(p/\'0.tgz\') as t:cfg=json.load(t.extractfile(\'9.json\'))\nasset=proof[\'gate_assets\'];assert asset[\'logical\']==cfg[\'logical\']\nassert asset[\'path\']==str(p/\'a/4.tar\') and archive.stat().st_size==asset[\'bytes\']\nh=hashlib.sha256()\nwith archive.open(\'rb\') as stream:\n    for chunk in iter(lambda:stream.read(1024**2),b\'\'):h.update(chunk)\nassert h.hexdigest()==asset[\'sha256\']\nprint(cfg[\'logical\'])\nPYASSET\n)\ntest -d /scratch/jjyeung && test -w /scratch/jjyeung\ntest ! -e "$GPU_LOGICAL"\nmkdir -p "$GPU_LOGICAL/d" "$GPU_LOGICAL/p"\ntar -xf "$ASSET_ARCHIVE" -C "$GPU_LOGICAL/d"\ntar -xzf "$P/0.tgz" -C "$GPU_LOGICAL/p"\ntest ! -e "$GPU_LOGICAL/d/7.json"\ncp "$GPU_LOGICAL/d/binding.json" "$GPU_LOGICAL/d/7.json"\n```\n\nCreate a private neutral configuration from `config.example.json` with separate authenticated A4 original/patched source roots. Set `export=$GPU_LOGICAL/d/e`, `export_pin=$GPU_LOGICAL/d/6.json`, and `artifact_manifest=$GPU_LOGICAL/d/7.json`. The last file is a byte-identical neutral alias for the CPU binding. Include that exact `binding.json` to `7.json` mapping in `PRIVATE_ALIASES.json`; map the other private prepared asset paths to staged opaque aliases of those same files. Keep private settings and reverse maps on Trinity. The following commands use files under `$LOCAL`:\n\n```bash\nset -euo pipefail\n: "${PRIVATE_CONFIG_TEMPLATE:?Private neutral GPU configuration with staged asset paths}"\n: "${PRIVATE_ALIASES:?Private JSON mapping preparation paths to staged opaque paths}"\nPRIVATE_SETTINGS="$LOCAL/PRIVATE_SETTINGS.json"\nPRIVATE_CONFIG="$LOCAL/PRIVATE_NEUTRAL_CONFIG.json"\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a20.py" --enable-extensions gate \\\n  --operator "$LOCAL/adopted" --prepared "$LOCAL/adopted/proof/SETTINGS.json" \\\n  --proof "$LOCAL/adopted/proof/CPU.json" --config "$PRIVATE_CONFIG_TEMPLATE" \\\n  --asset-receipts "$LOCAL/adopted/proof" --bound-export "$BOUND_EXPORT" \\\n  --settings-out "$PRIVATE_SETTINGS" --config-out "$PRIVATE_CONFIG"\n```\n\n```bash\nset -euo pipefail\nmkdir -p "$LOCAL/public"\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a11.py" seal \\\n  --source-root "$EXT_SOURCE" --input "$PRIVATE_SETTINGS" --aliases "$PRIVATE_ALIASES" \\\n  --out "$LOCAL/public/u3"\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a11.py" stage-kit \\\n  --source-root "$EXT_SOURCE" --input "$DELIVERY/kit_parity50" \\\n  --config "$PRIVATE_CONFIG" --out "$LOCAL/public/u0"\n```\n\nThe package embeds the driver/comparator SHA256 and the deterministically sealed sample SHA256 from MANIFEST `kit_files`. The driver and every worker authenticate those executing bytes, and `ue.json` carries them to SUBMIT_CHECK. The staged `u3.json` pins every extension; `u4.json` authenticates both full 927-file base inventories. The driver rejects changed bases, equal original/patched roots, and an original root containing extensions. It authenticates the sealed sample bytes and the logical sample pin. Transfer only the staged directory through the approved transport under an opaque root.\n\nOn an assigned **H100 80 GB** GPU, run the acceptance command below; it is **unrun here**. Preserve that allocation\'s actual `CUDA_VISIBLE_DEVICES`.\n\n```bash\nset -euo pipefail\nnice -n 10 "$READ_PYTHON" -I -s -B /scratch/jjyeung/ab0123456789/u0/u0.py \\\n  /scratch/jjyeung/ab0123456789/u0/u2.json --out /scratch/jjyeung/ab0123456789/u9 \\\n  --enable-gpu --public --repeat-baseline --shards 4\n```\n\nEvery arm starts a fresh process. ORIGINAL/OFF/OFF_REPEAT use ordinary journals and modulo shards. ON tests caches; ON_JOURNAL and sequential whole-scene shards test separate journal/shard features. Sequential shards establish equality, not parallel speed. Public logs tokenize item/native/room identities and arbitrary stdout/stderr. No reverse map is written on Orchard.\n\nAcceptance requires all 50 expected IDs, complete production output schemas, nonempty text/tokens/heads, scale even when null, every served response and forced-token count, matching call counters, and **zero semantic byte differences**. ORIGINAL/OFF must also retain every production source hash. Each enabled cache must report its memory bound and useful hits; SAM needs both feature and detection hits. Empty or all-miss runs fail. Only clocks and explicit audit/cache/memo telemetry are excluded from semantic comparison; audit violations fail. There is no answer/trace tolerance.\n\nEach RUN.json records the adopted package plan, read profile, asset pins, required device type, actual device, cache slots and budget. The worker checks CUDA device properties before model loading and refuses a different exact name, SM count, compute capability or memory class. `ue.json` is written only after all comparisons finish and records whether they all passed; failed or missing receipts cannot authorize submit. On the H100 host, archive it with `tar -cf /scratch/jjyeung/ab0123456789/5.tar -C /scratch/jjyeung/ab0123456789/u9 ue.json` and print `sha256sum /scratch/jjyeung/ab0123456789/5.tar` for authenticated return transport. Judge net time from `RUN.json`\'s `worker_wall_seconds`, which includes install/boundary hashing and eager SAM loading. Per-item timing alone cannot establish savings. ON constructs SAM outside inference mode to obtain tracked parameters; that changes loading time and potentially RNG use. The GPU byte gate must clear it. The sample overrepresents clip reuse: its ten distance items share one clip, while A4 has 150 distance items across 60 clips (review finding 7).\n\nThe cache cap covers retained cache storage and transient copies, not model/caller working memory. Measure full-process host/GPU peaks. Models must remain frozen: calls check parameter/buffer identities, pointers and counters; install/type boundaries hash content. Persistent raw writes fail at a boundary. Raw writes restored between boundaries, private tensor attributes and arbitrary non-tensor state are outside this guard\'s coverage. Graceful stops verify journals; a hard kill can leave an unchecked journal that requires fresh output.\n\nOutput directories u0–u5 represent ORIGINAL/OFF/OFF_REPEAT/ON/ON_JOURNAL/SHARDED. Reports u6–ua compare arms; ub.json checks merge equality; uc/ud contain canonical single/sharded returns. Restore on Trinity with the private inputs:\n\n```bash\nset -euo pipefail\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a11.py" restore \\\n  --source-root "$EXT_SOURCE" --input PRIVATE_RETURN --out "$LOCAL/restored" \\\n  --private-source "$DELIVERY/kit_parity50/sample50.json" \\\n  --private-source "$PRIVATE_CONFIG" --private-source "$PRIVATE_SETTINGS"\n```\n\nRestoration authenticates committed rows before rebuilding private IDs/checksums. Merge with the original manifest through the explicit extension entrypoint. The canonical answer/trace archive must match exactly; transport-envelope clocks remain variable.\n\n## Array validation\n\nNo multi-card A4 operator is delivered. The array helper is a separate inert prototype. Its example has `approved=false`: two one-hour shards, at most two attempts, four GPU-hours total. Approval must bind the exact partition, shards, time and attempts, with no more than five allocated GPU-hours over all attempts. Before any sharded/preempt adoption, validate real persistent-storage preemption/requeue.\n\n```bash\nset -euo pipefail\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a15.py" PRIVATE_ARRAY_CONFIG.json \\\n  --enable-array --token ab0123456789 --out "$LOCAL/array-plan" \\\n  --python /scratch/jjyeung/ab0123456789/u1 --source /scratch/jjyeung/ab0123456789/u2 \\\n  --staged-config /project/community/jjyeung/okh7/a15_cot_apab0123456789/u3.json\n```\n\nThis writes commands without running them. Exit 75 requests bounded requeue; other errors remain failures. Lock waits stop after 60 seconds, and the attempt limit forbids more work. Public paths must use approved roots and pass the forbidden-word screen; name checks do not establish storage permissions or capacity.\n\nNo delivered CPU suite or single-GPU kit requires a local OS socket. StageOneSocket is a Python callback. Real restore, bwrap isolation, remote transport, GPU parity/performance/memory and persistent requeue remain unrun.\n\n## Review round 7: finding -> fix -> test\n\n| Finding | Fix | Regression |\n|---|---|---|\n| 1. Private root disappears | Archive inside CPU proof to `$P/a/4.tar` before CPU.json; record hash/bytes. | Real fixture tar runs through a namespace wrapper, survives loss of the root, and the CPU operator fixture executes staging. |\n| 2. Fill wait hangs | Guard PACKAGE_TOKEN, check PID and cap wait at four hours. | Missing token, dead PID, timeout and failed exit refuse; success passes. |\n| 3. PCIe accepted | Require exact HBM3 name and 132 SMs. | SXM stub passes; PCIe and wrong-SM stubs refuse. |\n| 4. Evidence/host nits | Bind executing kit/comparator/sample; include a/1.json; unpack with -s -E -B; use an H100-local archive path. | Mutated pins refuse, environment-polluted unpack succeeds, allocation/evidence blocks are checked. |\n| 5. Decision export | Default to the supplied step-400 export; require an explicit parameter for other exports. | Step 400 passes by default; synthetic step 600 passes only when selected; wrong artifact refuses. |\n\nFrozen weights remain required. Persistent raw writes are boundary-checked; writes restored between boundaries remain outside the guard. GPU byte equality and performance remain unrun.\n'

======================================================================
FAIL: test_f4_readme_archive_path_accepts_symlinked_parent (__main__.Round8Tests.test_f4_readme_archive_path_accepts_symlinked_parent)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 194, in test_f4_readme_archive_path_accepts_symlinked_parent
    self.assertEqual(result.returncode,0,result.stderr)
AssertionError: 1 != 0 : Traceback (most recent call last):
  File "<stdin>", line 7, in <module>
AssertionError


======================================================================
FAIL: test_info_gpu_commands_and_aliases (__main__.Round8Tests.test_info_gpu_commands_and_aliases)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 199, in test_info_gpu_commands_and_aliases
    self.assertIn("inputs['python']",text)
AssertionError: "inputs['python']" not found in 'The GPU kit is unrun. It requires zero answer/trace byte differences. Its 50 items cover ten items per type and twelve captures; this reuse-heavy sample does not predict full-read throughput.\n\nUse the full **A4/src** base pinned by `BASE_PIN.json`. The reader patches also apply to the inspected B5 source subset, but this kit does not authenticate a B5 base. Apply patches 01–03 to a separate source copy. They add `u0/`; all original reader files remain byte-identical. Apply 04–05 to a separate A4 operator copy, outside `src`.\n\nThe ordinary entrypoint stays OFF and imports no extension. `u0/a8.py --enable-extensions` explicitly selects the extensions; individual cache settings then default OFF. The ON environment records an extension source hash. Rebuild payload and artifact pins before deployment.\n\n## Local preparation\n\nThese commands use paths supplied by the operator; they do not depend on the author\'s `work/` directory. Set `DELIVERY` to the delivered `out/`, `A4_BASE` to the full supplied A4 directory on local scratch, `LOCAL` to a fresh local scratch directory, and `READ_PYTHON` to the approved Python executable. Both source roots and all outputs must stay on local scratch. The package contains code, not model/data archives.\n\n```bash\nset -euo pipefail\n: "${DELIVERY:?Absolute path to delivered out directory}"\n: "${A4_BASE:?Absolute path to the full pinned A4 directory on local scratch}"\n: "${LOCAL:?Fresh local scratch directory}"\n: "${READ_PYTHON:?Approved Python executable}"\nexport PYTHONDONTWRITEBYTECODE=1 TOKENIZERS_PARALLELISM=false\nexport OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8\nexport XDG_CACHE_HOME="$LOCAL/cache" HF_HOME="$LOCAL/cache/hf" TRITON_CACHE_DIR="$LOCAL/cache/triton"\nmkdir -p "$LOCAL/source" "$LOCAL/a4"\nnice -n 10 tar -cf - -C "$A4_BASE/src" . | nice -n 10 tar -xf - -C "$LOCAL/source"\nnice -n 10 tar -cf - -C "$A4_BASE" package tower_sequence.py fetch_return.py unpack_return.py |\n  nice -n 10 tar -xf - -C "$LOCAL/a4"\nnice -n 10 patch --batch --fuzz=0 -p1 -d "$LOCAL/source" < "$DELIVERY/patches/01_bounded_read_caches.diff"\nnice -n 10 patch --batch --fuzz=0 -p1 -d "$LOCAL/source" < "$DELIVERY/patches/02_atomic_scene_shards.diff"\nnice -n 10 patch --batch --fuzz=0 -p1 -d "$LOCAL/source" < "$DELIVERY/patches/03_production_integration.diff"\nnice -n 10 patch --batch --fuzz=0 -p1 -d "$LOCAL/a4" < "$DELIVERY/patches/04_operator_cache_bound.diff"\nnice -n 10 patch --batch --fuzz=0 -p1 -d "$LOCAL/a4" < "$DELIVERY/patches/05_operator_return_and_proof.diff"\nEXT_SOURCE="$LOCAL/source"\n```\n\nKeep the private kit, original manifests and reverse maps on Trinity. Stage each source tree as one archive and extract it only on node-local scratch. Both parity source roots must remain pristine: no build outputs, extra files or symlinks. Public paths, submission names, configuration and logs must use opaque tokens. Never transfer private reverse maps to Orchard.\n\n## Bound export, build and operations\n\nThe candidate uses **A4\'s 636-item schedule, one card, caches only, general/no-requeue**. A4\'s export admission, submit helper and run settings remain intact. `a19` requires the reviewed payload hash `4498fca72a8e4b476b38f097ffdf3ff88b5aa20fc036bd196b18a5706e9fe46d`, the patched operator hashes, all copied A4 members, the base BATCH.sh and decoded bootstrap pins from MANIFEST, the exact extension inventory and the four original alias bases. It authenticates them before copying. Its batch uses cont_ops\' exact `build_r10.wrap_batch`: excluded node, EXIT log return and USR1 forwarding.\n\nThe gate defaults to **step 400**, read A of job **173060**, source package **a15_cot_apdc76460c3a164**. Its artifact SHA256 is **5083243cfedd2a389dfca579c5452e7d0c73b03a58e1cb7d204292ddd10e67cd**. `operations/BOUND_EXPORT.json` preserves the supplied export pin. `operations/binding.default.json` combines that identity, the four archive-part sizes in the supplied `a/1.json`, and the reviewed `bind400_partial.json` operation paths. `DEFAULT_EXPORT_PROVENANCE.json` records all source hashes. These are authenticated metadata; production weights were not restored here.\n\n`BOUND_EXPORT` selects the gate\'s exact reviewed export.json; `EXPORT_BINDING` selects the matching build/fill binding. For another reviewed export, including step 600, supply both parameters. The gate refuses a package whose export differs from the selected pin. A fresh package token identifies the ON build; it does not reuse the source package\'s token.\n\n```bash\nset -euo pipefail\nBOUND_EXPORT=${BOUND_EXPORT:-"$DELIVERY/operations/BOUND_EXPORT.json"}\nEXPORT_BINDING=${EXPORT_BINDING:-"$DELIVERY/operations/binding.default.json"}\n: "${PACKAGE_TOKEN:?Fresh 11-16 hex characters starting with a-f}"\nPROFILE_ARGS=()  # All three caches, 12 GiB. For processor-only: PROFILE_ARGS=(--processor-only)\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a19.py" \\\n  --enable-extensions --base-operator "$LOCAL/a4" --source-root "$EXT_SOURCE" \\\n  --manifest "$DELIVERY/patches/MANIFEST.json" --extension-pins "$DELIVERY/kit_parity50/EXTENSION_PINS.json" \\\n  --export-binding "$EXPORT_BINDING" --token "$PACKAGE_TOKEN" --out "$LOCAL/adopted" "${PROFILE_ARGS[@]}"\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a20.py" --enable-extensions operations \\\n  --operator "$LOCAL/adopted" --binding "$EXPORT_BINDING" --dry-root "$DELIVERY/operations" --out "$LOCAL/ops"\nnice -n 10 tar -czf "$LOCAL/0.tgz" -C "$LOCAL/ops" .\nnice -n 10 sha256sum "$LOCAL/0.tgz"\n```\n\nFor a different target, derive `EXPORT_BINDING` from its reviewed template and authenticated local receipts before the build block above, and set `BOUND_EXPORT` to that target\'s reviewed export.json:\n\n```bash\nset -euo pipefail\n: "${TARGET_TEMPLATE:?Reviewed target template, including Orchard done and prep_paths}"\n: "${TARGET_ARTIFACT:?Authenticated local artifact.json}"\n: "${TARGET_DONE:?Authenticated local whole-tar done receipt}"\n: "${TARGET_CONFIG:?Authenticated preparation config.json}"\n: "${TARGET_RECEIPT:?Authenticated preparation receipt}"\n: "${TARGET_DATA_RECEIPT:?Authenticated data receipt}"\n: "${EXPORT_BINDING:?Fresh output binding path for the selected target}"\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a20.py" --enable-extensions binding \\\n  --template "$TARGET_TEMPLATE" --artifact "$TARGET_ARTIFACT" --done "$TARGET_DONE" \\\n  --config "$TARGET_CONFIG" --receipt "$TARGET_RECEIPT" --data-receipt "$TARGET_DATA_RECEIPT" \\\n  --out "$EXPORT_BINDING"\n```\n\n`adopted` retains the exact local source/operator/unpacker. `ops/1.tgz` is the package delivery, with `ops/SHA256`; the outer archive carries it and five inert scripts. The commands below are **owner operations on Orchard, unrun here**. Transfer the single outer archive through the owner\'s existing authorized transport. Set `OPS_ARCHIVE` to its received opaque path, `OPS_SHA256` to the printed local hash, and `D` to a fresh opaque operation directory. These are transport endpoints, not generated receipt values.\n\n```bash\nset -euo pipefail\n: "${OPS_ARCHIVE:?Received outer archive on Orchard}"\n: "${OPS_SHA256:?Printed local SHA256 of that archive}"\n: "${D:?Fresh opaque operation directory on Orchard}"\n: "${PACKAGE_TOKEN:?Copy the fresh build token to this Orchard shell}"\nprintf \'%s  %s\\n\' "$OPS_SHA256" "$OPS_ARCHIVE" | sha256sum -c -\ntest ! -e "$D"\nmkdir -m 700 "$D"\ntar -xzf "$OPS_ARCHIVE" -C "$D"\nbash "$D/o_place.sh"\nbash "$D/o_pull_fill.sh"\n# BEGIN FILL_WAIT\n: "${PACKAGE_TOKEN:?Copy the fresh build token to this Orchard shell}"\nP=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}\nFILL_MAX_SECONDS=${FILL_MAX_SECONDS:-14400}\n[[ "$FILL_MAX_SECONDS" =~ ^[0-9]+$ ]] && (( FILL_MAX_SECONDS >= 1 && FILL_MAX_SECONDS <= 14400 )) || exit 1\nFILL_DEADLINE=$((SECONDS + FILL_MAX_SECONDS))\nwhile test ! -f "$P/a/1.txt"; do\n  FILL_PID=$(cat "$P/a/0.txt") || exit 1\n  [[ "$FILL_PID" =~ ^[1-9][0-9]*$ ]] || exit 1\n  if ! kill -0 "$FILL_PID" 2>/dev/null && test ! -f "$P/a/1.txt"; then\n    echo \'Fill worker is gone without an exit receipt\' >&2; exit 1\n  fi\n  if (( SECONDS >= FILL_DEADLINE )); then\n    echo \'Fill wait exceeded its maximum\' >&2; exit 1\n  fi\n  FILL_REMAIN=$((FILL_DEADLINE - SECONDS))\n  sleep "$(( FILL_REMAIN < 60 ? FILL_REMAIN : 60 ))"\ndone\ntest "$(cat "$P/a/1.txt")" = 0\n# END FILL_WAIT\nbash "$D/o_cpu.sh"\n```\n\n`o_place.sh` verifies the inner archive and places it at `$P=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}`. `o_pull_fill.sh` acquires the permanent attempt lock `$P/a/0.lock`, launches one detached nohup worker, and returns its PID in `$P/a/0.txt`. The worker logs to `$P/a/0.log` and writes its exit status to `$P/a/1.txt` on success or failure. Run the wait on the same host that launched the detached worker. It checks at most once per minute, refuses a vanished PID without `1.txt`, and stops after at most 14,400 seconds (four hours). A duplicate launch refuses; a failed or interrupted attempt requires a fresh package/token, never an automatic retry. The worker copies the reviewed `done` and `prep_paths` files to `$P/a/e/{5,7,8,9}`, authenticates their pins (the `.done` receipt uses whitespace-separated fields), fetches export parts `0..3` once with retries disabled, fills through `a/4.py`, and runs cont_ops\' verbatim `dryres2.py` and `dry2.py`. A failed transfer stops; the scripts do not retry it.\n\n`o_cpu.sh` requests the A4 CPU allocation explicitly: preempt, eight CPUs, 200G, four hours, no GPU, no requeue, and the excluded nodes. The **CPU allocation** is separate from the intended **general GPU read**. Wait for the CPU job to finish successfully. Preserve `$P/a/c/CPU.json`, `MEMORY.json` and the exact `SETTINGS.json` emitted by A4 prepare. Bring these small files back as one archive through the authorized transport to `$LOCAL/adopted/proof/` before the parity preparation below. Before writing CPU.json, the ON proof streams `logical/d` through its live `J.namespace(root)` to the named shared staging path `$P/a/4.tar`, outside the capped return pool. It dereferences symlinks and records `gate_assets.path`, `logical`, `sha256` and `bytes` in CPU.json. The output file is opened outside bwrap and tar writes to that descriptor. This uses the same preparation/READY as the proof, without a second staging job. A tar failure leaves no successful CPU.json and is not retried. The proof also emits exact `a/1.json`, restore, artifact-binding, manifest and export-pin receipts. These small files authenticate staging; they do not contain model weights. The proof binds payload/plan/inputs/operator, must pass bundle/entry checks and contain `memory.read_cache_bytes=12884901888` (4294967296 for processor-only), `basis=fixed_g3t_shapes`, and `fits=true`.\n\nArchive the CPU evidence on Orchard after its successful completion, using the package token printed by the build:\n\n```bash\nset -euo pipefail\nP=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}\ntar -czf "$D/2.tgz" -C "$P/a/c" CPU.json MEMORY.json SETTINGS.json RESTORE.json binding.json manifest.json EXPORT_PIN.json 1.json\nsha256sum "$D/2.tgz"\n```\n\nAfter authorized transport, authenticate and extract that archive on local scratch:\n\n```bash\nset -euo pipefail\n: "${PROOF_ARCHIVE:?Received CPU-evidence archive on local scratch}"\n: "${PROOF_SHA256:?Printed Orchard SHA256 of the CPU-evidence archive}"\nprintf \'%s  %s\\n\' "$PROOF_SHA256" "$PROOF_ARCHIVE" | nice -n 10 sha256sum -c -\nmkdir "$LOCAL/adopted/proof"\nnice -n 10 tar -xzf "$PROOF_ARCHIVE" -C "$LOCAL/adopted/proof"\n```\n\nAfter the zero-difference GPU parity gate passes, transfer its token-only `ue.json` through the authorized transport as one archive, preserving the SHA256 printed on the GPU host. The authorized owner authenticates that archive and installs the receipt before submission:\n\n```bash\nset -euo pipefail\n: "${GATE_ARCHIVE:?Received archive containing ue.json}"\n: "${GATE_SHA256:?SHA256 printed on the GPU host}"\nprintf \'%s  %s\\n\' "$GATE_SHA256" "$GATE_ARCHIVE" | sha256sum -c -\nmkdir "$D/g"\ntar -xf "$GATE_ARCHIVE" -C "$D/g"\nP=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}\ntest ! -e "$P/a/g.json"\ncp "$D/g/ue.json" "$P/a/g.json"\n```\n\nThen run:\n\n```bash\nset -euo pipefail\nbash "$D/o_sub.sh"\n# After the GPU job finishes:\nbash "$D/o_fetch.sh"\nP=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}\ntar -czf "$D/3.tgz" -C "$P/a/f" 0.tgz EXIT.json\nsha256sum "$D/3.tgz"\n```\n\n`o_sub.sh` embeds cont_ops’ A4 CPU-receipt assertions verbatim, including batch/dispatch/guard pins and MEMORY.json equality, then checks cache memory and the successful GPU receipt at `$P/a/g.json`, requires both dry checks to pass, requires an empty general queue, and refuses a return pool over **75,000,000 bytes** (including errors/symlinks). It then runs `3.py check` and one `3.py submit --gpus 1 --time 04:30:00`, saving the job ID. The GPU receipt must match the CPU restore/binding pins, filled export pin, adopted plan/profile and H100 80 GB requirement. The unchanged bootstrap itself does not require the cache-memory field; this submit preflight does. `o_fetch.sh` derives the authenticated return token and fetches `$P/a/f/{0.tgz,EXIT.json}`.\n\nTransfer `$D/3.tgz` through the authorized transport, preserving the local operator directory. Authenticate, extract and unpack it locally:\n\n```bash\nset -euo pipefail\n: "${RETURN_ARCHIVE:?Received fetched-return archive on local scratch}"\n: "${RETURN_SHA256:?Printed Orchard SHA256 of the fetched-return archive}"\nprintf \'%s  %s\\n\' "$RETURN_SHA256" "$RETURN_ARCHIVE" | nice -n 10 sha256sum -c -\nmkdir "$LOCAL/adopted/f"\nnice -n 10 tar -xzf "$RETURN_ARCHIVE" -C "$LOCAL/adopted/f"\n(cd "$LOCAL/adopted" && CUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -s -E -B ./unpack_return.py \\\n  --archive "$LOCAL/adopted/f/0.tgz" --exit "$LOCAL/adopted/f/EXIT.json" \\\n  --out "$LOCAL/adopted/ret" > "$LOCAL/adopted/unpack-success.json" && \\\n  test -s "$LOCAL/adopted/unpack-success.json")\n```\n\nA refused unpack leaves its extracted tree behind. Scorers must consume only unpack\'s **success output after exit status 0**, never a directory merely because it exists; the command\'s `&&` chain enforces that handoff. A successful partial return still has `complete=false` and must not be scored as complete. The ON unpacker refuses any existing weight receipt whose verified value is not JSON true. Processor-only journals need no weight receipt. OFF behavior remains unchanged. Whole-archive identity follows A4\'s design: fill checks the sealed whole-tar constants; job/unpack admission compare against inputs.archives[0].\n\n**Forecasts:** Package D is the 580-item distance read (B5 fork, 03:30 walltime); it has **no ON route** in a19. Its one-card **estimate** is 13,813.069 s (3 h 50 min), using the measured 23.600 s/item and crediting no cache saving. The **636-item** A4 read that a19 actually builds has an **estimate** of **7,351.824 s (2 h 02 min 32 s; 11.559 s/item)**, obtained by carrying forward the supplied A4 total, with zero assumed saving. Target weights, cache costs and staging/queue delays can change it; neither forecast measures the selected export.\n\n## GPU parity staging and acceptance\n\nThe gate must seal **A4 prepare\'s actual output plus the operator\'s per-read overrides** for the package being adopted. Do not supply an unrelated PRIVATE_SETTINGS.json. `a20 gate` checks the prepared bytes and exact RESTORE.json/artifact-binding bytes against CPU.json’s READY pins, checks export identity against the adopted step binding, checks the export-pin hash and byte count against the exact `a/1.json` bytes authenticated by CPU.json, and checks payload, plan and operator bindings. The selected export defaults to the pinned step-400 export; `--bound-export` explicitly changes it. Every GPU worker rechecks those asset bytes and the artifact manifest before reading; changing paths cannot substitute another checkpoint. It applies the authenticated operator descriptor and derives `enable_caches`, `read_cache_bytes` and the full adoption profile: candidates_argmax, memo on, g3t, empty verify IDs, save_own_depth=false, and the exact cache switches. Both the parent driver and every worker refuse a different profile. Processor-only adoption is explicitly gated with slots `[0]` and 4 GiB; all-cache adoption uses `[0,1,2]` and 12 GiB.\n\nThe **owner-only commands below are unrun here**. The shared asset archive already exists when CPU.json appears; never try to reopen the CPU job\'s private `/tmp`. Reserve storage for the archive before running `o_cpu.sh`. Its size is recorded by the job; no production archive size was measured here.\n\nAllocate the gate on Orchard, then enter its compute task. This is one non-requeued H100 job, eight CPUs, 200G and a five-hour maximum. Preserve its actual `CUDA_VISIBLE_DEVICES`; the Python guard requires exactly `NVIDIA H100 80GB HBM3`, 132 SMs, capability 9.0 and the 80 GB memory class.\n\n```bash\nset -euo pipefail\nsalloc --account=mt01 --partition=general --nodes=1 --ntasks=1 --cpus-per-task=8 \\\n  --mem=200G --gres=gpu:1 --time=05:00:00 --no-requeue \\\n  --exclude=orchard-community-2 --job-name=ab0123456789 \\\n  srun --ntasks=1 --pty bash --noprofile --norc\n```\n\nOn that H100 host, `/scratch/jjyeung` must **physically exist and be writable** outside bwrap. A4 creates `/scratch` only inside its namespace; it does not satisfy this host requirement. The operator must provision the host path before the gate. The exact logical root (currently `/scratch/jjyeung/b01ec87a6f29b`) must be absent so extraction cannot overlay another run. Preserve it so manifests and restore paths remain valid. Provision the separate opaque kit/source directories there too. Stage the source trees and public kit as single authenticated archives; keep private inputs and reverse maps on Trinity.\n\nThe shared path `$P/a/4.tar` is visible directly on Orchard. If approved transport copies it, set `ASSET_ARCHIVE` to that received path; CPU.json still supplies the expected hash and bytes. Run inside the allocation:\n\n```bash\nset -euo pipefail\n: "${PACKAGE_TOKEN:?Fresh package token from the build}"\nP=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}\nASSET_ARCHIVE=${ASSET_ARCHIVE:-"$P/a/4.tar"}\nGPU_LOGICAL=$(/usr/bin/python3 -I -s -B - "$P" "$ASSET_ARCHIVE" <<\'PYASSET\'\nimport hashlib,json,sys,tarfile\nfrom pathlib import Path\np=Path(sys.argv[1]);archive=Path(sys.argv[2]);proof=json.loads((p/\'a/c/CPU.json\').read_text())\nassert proof[\'passed\'] is True\nwith tarfile.open(p/\'0.tgz\') as t:cfg=json.load(t.extractfile(\'9.json\'))\nasset=proof[\'gate_assets\'];assert asset[\'logical\']==cfg[\'logical\']\nassert asset[\'path\']==str(p/\'a/4.tar\') and archive.stat().st_size==asset[\'bytes\']\nh=hashlib.sha256()\nwith archive.open(\'rb\') as stream:\n    for chunk in iter(lambda:stream.read(1024**2),b\'\'):h.update(chunk)\nassert h.hexdigest()==asset[\'sha256\']\nprint(cfg[\'logical\'])\nPYASSET\n)\ntest -d /scratch/jjyeung && test -w /scratch/jjyeung\ntest ! -e "$GPU_LOGICAL"\nmkdir -p "$GPU_LOGICAL/d" "$GPU_LOGICAL/p"\ntar -xf "$ASSET_ARCHIVE" -C "$GPU_LOGICAL/d"\ntar -xzf "$P/0.tgz" -C "$GPU_LOGICAL/p"\ntest ! -e "$GPU_LOGICAL/d/7.json"\ncp "$GPU_LOGICAL/d/binding.json" "$GPU_LOGICAL/d/7.json"\n```\n\nCreate a private neutral configuration from `config.example.json` with separate authenticated A4 original/patched source roots. Set `export=$GPU_LOGICAL/d/e`, `export_pin=$GPU_LOGICAL/d/6.json`, and `artifact_manifest=$GPU_LOGICAL/d/7.json`. The last file is a byte-identical neutral alias for the CPU binding. Include that exact `binding.json` to `7.json` mapping in `PRIVATE_ALIASES.json`; map the other private prepared asset paths to staged opaque aliases of those same files. Keep private settings and reverse maps on Trinity. The following commands use files under `$LOCAL`:\n\n```bash\nset -euo pipefail\n: "${PRIVATE_CONFIG_TEMPLATE:?Private neutral GPU configuration with staged asset paths}"\n: "${PRIVATE_ALIASES:?Private JSON mapping preparation paths to staged opaque paths}"\nPRIVATE_SETTINGS="$LOCAL/PRIVATE_SETTINGS.json"\nPRIVATE_CONFIG="$LOCAL/PRIVATE_NEUTRAL_CONFIG.json"\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a20.py" --enable-extensions gate \\\n  --operator "$LOCAL/adopted" --prepared "$LOCAL/adopted/proof/SETTINGS.json" \\\n  --proof "$LOCAL/adopted/proof/CPU.json" --config "$PRIVATE_CONFIG_TEMPLATE" \\\n  --asset-receipts "$LOCAL/adopted/proof" --bound-export "$BOUND_EXPORT" \\\n  --settings-out "$PRIVATE_SETTINGS" --config-out "$PRIVATE_CONFIG"\n```\n\n```bash\nset -euo pipefail\nmkdir -p "$LOCAL/public"\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a11.py" seal \\\n  --source-root "$EXT_SOURCE" --input "$PRIVATE_SETTINGS" --aliases "$PRIVATE_ALIASES" \\\n  --out "$LOCAL/public/u3"\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a11.py" stage-kit \\\n  --source-root "$EXT_SOURCE" --input "$DELIVERY/kit_parity50" \\\n  --config "$PRIVATE_CONFIG" --out "$LOCAL/public/u0"\n```\n\nThe package embeds the driver/comparator SHA256 and the deterministically sealed sample SHA256 from MANIFEST `kit_files`. The driver and every worker authenticate those executing bytes, and `ue.json` carries them to SUBMIT_CHECK. The staged `u3.json` pins every extension; `u4.json` authenticates both full 927-file base inventories. The driver rejects changed bases, equal original/patched roots, and an original root containing extensions. It authenticates the sealed sample bytes and the logical sample pin. Transfer only the staged directory through the approved transport under an opaque root.\n\nOn an assigned **H100 80 GB** GPU, run the acceptance command below; it is **unrun here**. Preserve that allocation\'s actual `CUDA_VISIBLE_DEVICES`.\n\n```bash\nset -euo pipefail\nnice -n 10 "$READ_PYTHON" -I -s -B /scratch/jjyeung/ab0123456789/u0/u0.py \\\n  /scratch/jjyeung/ab0123456789/u0/u2.json --out /scratch/jjyeung/ab0123456789/u9 \\\n  --enable-gpu --public --repeat-baseline --shards 4\n```\n\nEvery arm starts a fresh process. ORIGINAL/OFF/OFF_REPEAT use ordinary journals and modulo shards. ON tests caches; ON_JOURNAL and sequential whole-scene shards test separate journal/shard features. Sequential shards establish equality, not parallel speed. Public logs tokenize item/native/room identities and arbitrary stdout/stderr. No reverse map is written on Orchard.\n\nAcceptance requires all 50 expected IDs, complete production output schemas, nonempty text/tokens/heads, scale even when null, every served response and forced-token count, matching call counters, and **zero semantic byte differences**. ORIGINAL/OFF must also retain every production source hash. Each enabled cache must report its memory bound and useful hits; SAM needs both feature and detection hits. Empty or all-miss runs fail. Only clocks and explicit audit/cache/memo telemetry are excluded from semantic comparison; audit violations fail. There is no answer/trace tolerance.\n\nEach RUN.json records the adopted package plan, read profile, asset pins, required device type, actual device, cache slots and budget. The worker checks CUDA device properties before model loading and refuses a different exact name, SM count, compute capability or memory class. `ue.json` is written only after all comparisons finish and records whether they all passed; failed or missing receipts cannot authorize submit. On the H100 host, archive it with `tar -cf /scratch/jjyeung/ab0123456789/5.tar -C /scratch/jjyeung/ab0123456789/u9 ue.json` and print `sha256sum /scratch/jjyeung/ab0123456789/5.tar` for authenticated return transport. Judge net time from `RUN.json`\'s `worker_wall_seconds`, which includes install/boundary hashing and eager SAM loading. Per-item timing alone cannot establish savings. ON constructs SAM outside inference mode to obtain tracked parameters; that changes loading time and potentially RNG use. The GPU byte gate must clear it. The sample overrepresents clip reuse: its ten distance items share one clip, while A4 has 150 distance items across 60 clips (review finding 7).\n\nThe cache cap covers retained cache storage and transient copies, not model/caller working memory. Measure full-process host/GPU peaks. Models must remain frozen: calls check parameter/buffer identities, pointers and counters; install/type boundaries hash content. Persistent raw writes fail at a boundary. Raw writes restored between boundaries, private tensor attributes and arbitrary non-tensor state are outside this guard\'s coverage. Graceful stops verify journals; a hard kill can leave an unchecked journal that requires fresh output.\n\nOutput directories u0–u5 represent ORIGINAL/OFF/OFF_REPEAT/ON/ON_JOURNAL/SHARDED. Reports u6–ua compare arms; ub.json checks merge equality; uc/ud contain canonical single/sharded returns. Restore on Trinity with the private inputs:\n\n```bash\nset -euo pipefail\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a11.py" restore \\\n  --source-root "$EXT_SOURCE" --input PRIVATE_RETURN --out "$LOCAL/restored" \\\n  --private-source "$DELIVERY/kit_parity50/sample50.json" \\\n  --private-source "$PRIVATE_CONFIG" --private-source "$PRIVATE_SETTINGS"\n```\n\nRestoration authenticates committed rows before rebuilding private IDs/checksums. Merge with the original manifest through the explicit extension entrypoint. The canonical answer/trace archive must match exactly; transport-envelope clocks remain variable.\n\n## Array validation\n\nNo multi-card A4 operator is delivered. The array helper is a separate inert prototype. Its example has `approved=false`: two one-hour shards, at most two attempts, four GPU-hours total. Approval must bind the exact partition, shards, time and attempts, with no more than five allocated GPU-hours over all attempts. Before any sharded/preempt adoption, validate real persistent-storage preemption/requeue.\n\n```bash\nset -euo pipefail\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a15.py" PRIVATE_ARRAY_CONFIG.json \\\n  --enable-array --token ab0123456789 --out "$LOCAL/array-plan" \\\n  --python /scratch/jjyeung/ab0123456789/u1 --source /scratch/jjyeung/ab0123456789/u2 \\\n  --staged-config /project/community/jjyeung/okh7/a15_cot_apab0123456789/u3.json\n```\n\nThis writes commands without running them. Exit 75 requests bounded requeue; other errors remain failures. Lock waits stop after 60 seconds, and the attempt limit forbids more work. Public paths must use approved roots and pass the forbidden-word screen; name checks do not establish storage permissions or capacity.\n\nNo delivered CPU suite or single-GPU kit requires a local OS socket. StageOneSocket is a Python callback. Real restore, bwrap isolation, remote transport, GPU parity/performance/memory and persistent requeue remain unrun.\n\n## Review round 7: finding -> fix -> test\n\n| Finding | Fix | Regression |\n|---|---|---|\n| 1. Private root disappears | Archive inside CPU proof to `$P/a/4.tar` before CPU.json; record hash/bytes. | Real fixture tar runs through a namespace wrapper, survives loss of the root, and the CPU operator fixture executes staging. |\n| 2. Fill wait hangs | Guard PACKAGE_TOKEN, check PID and cap wait at four hours. | Missing token, dead PID, timeout and failed exit refuse; success passes. |\n| 3. PCIe accepted | Require exact HBM3 name and 132 SMs. | SXM stub passes; PCIe and wrong-SM stubs refuse. |\n| 4. Evidence/host nits | Bind executing kit/comparator/sample; include a/1.json; unpack with -s -E -B; use an H100-local archive path. | Mutated pins refuse, environment-polluted unpack succeeds, allocation/evidence blocks are checked. |\n| 5. Decision export | Default to the supplied step-400 export; require an explicit parameter for other exports. | Step 400 passes by default; synthetic step 600 passes only when selected; wrong artifact refuses. |\n\nFrozen weights remain required. Persistent raw writes are boundary-checked; writes restored between boundaries remain outside the guard. GPU byte equality and performance remain unrun.\n'

======================================================================
FAIL: test_info_tar_stderr_is_retained (__main__.Round8Tests.test_info_tar_stderr_is_retained)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 99, in test_info_tar_stderr_is_retained
    err=root/'results/4.err';self.assertTrue(err.exists(),'Tar stderr was discarded')
                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: False is not true : Tar stderr was discarded

----------------------------------------------------------------------
Ran 10 tests in 3.997s

FAILED (failures=29)
```

Command: `bash work/cpu.sh work/run_checks.py  # round9_before; exact environment/argv in runner`

Exact output ([checks/round9_before.txt](checks/round9_before.txt)):

```text
test_f1_actual_launch_calls_namespace_twice (__main__.Round9Tests.test_f1_actual_launch_calls_namespace_twice) ... FAIL
test_f1_all_commands_use_real_namespace_and_input_wrapper (__main__.Round9Tests.test_f1_all_commands_use_real_namespace_and_input_wrapper) ... FAIL
test_f1_authenticated_bootstrap_and_physical_asset_extraction (__main__.Round9Tests.test_f1_authenticated_bootstrap_and_physical_asset_extraction) ... FAIL
test_f1_runtime_staging_reuses_package_block_and_pins (__main__.Round9Tests.test_f1_runtime_staging_reuses_package_block_and_pins) ... FAIL
test_f2_failed_self_test_is_recorded_and_cannot_pass_receipt (__main__.Round9Tests.test_f2_failed_self_test_is_recorded_and_cannot_pass_receipt) ... FAIL
test_f2_main_records_failure_and_never_starts_workers (__main__.Round9Tests.test_f2_main_records_failure_and_never_starts_workers) ... FAIL
test_f2_real_guard_self_test_and_each_missed_operation (__main__.Round9Tests.test_f2_real_guard_self_test_and_each_missed_operation) ... FAIL
test_f2_submit_requires_all_three_guard_checks (__main__.Round9Tests.test_f2_submit_requires_all_three_guard_checks) ... FAIL
test_f3_staging_transfer_precedes_allocation_and_roots_extract (__main__.Round9Tests.test_f3_staging_transfer_precedes_allocation_and_roots_extract) ... FAIL
test_info_round7_logs_are_labelled (__main__.Round9Tests.test_info_round7_logs_are_labelled) ... FAIL
test_info_token_and_framework_gap_and_guard_limits (__main__.Round9Tests.test_info_token_and_framework_gap_and_guard_limits) ... FAIL

======================================================================
FAIL: test_f1_actual_launch_calls_namespace_twice (__main__.Round9Tests.test_f1_actual_launch_calls_namespace_twice)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round9.py", line 91, in test_f1_actual_launch_calls_namespace_twice
    host=self.host()
         ^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round9.py", line 34, in host
    self.assertTrue(path.is_file(),'Missing namespace host launcher')
AssertionError: False is not true : Missing namespace host launcher

======================================================================
FAIL: test_f1_all_commands_use_real_namespace_and_input_wrapper (__main__.Round9Tests.test_f1_all_commands_use_real_namespace_and_input_wrapper)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round9.py", line 38, in test_f1_all_commands_use_real_namespace_and_input_wrapper
    host=self.host()
         ^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round9.py", line 34, in host
    self.assertTrue(path.is_file(),'Missing namespace host launcher')
AssertionError: False is not true : Missing namespace host launcher

======================================================================
FAIL: test_f1_authenticated_bootstrap_and_physical_asset_extraction (__main__.Round9Tests.test_f1_authenticated_bootstrap_and_physical_asset_extraction)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round9.py", line 111, in test_f1_authenticated_bootstrap_and_physical_asset_extraction
    host=self.host()
         ^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round9.py", line 34, in host
    self.assertTrue(path.is_file(),'Missing namespace host launcher')
AssertionError: False is not true : Missing namespace host launcher

======================================================================
FAIL: test_f1_runtime_staging_reuses_package_block_and_pins (__main__.Round9Tests.test_f1_runtime_staging_reuses_package_block_and_pins)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round9.py", line 62, in test_f1_runtime_staging_reuses_package_block_and_pins
    host=self.host()
         ^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round9.py", line 34, in host
    self.assertTrue(path.is_file(),'Missing namespace host launcher')
AssertionError: False is not true : Missing namespace host launcher

======================================================================
FAIL: test_f2_failed_self_test_is_recorded_and_cannot_pass_receipt (__main__.Round9Tests.test_f2_failed_self_test_is_recorded_and_cannot_pass_receipt)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round9.py", line 177, in test_f2_failed_self_test_is_recorded_and_cannot_pass_receipt
    self.assertIn('guard_self_test',inspect.signature(self.kit.write_gate_receipt).parameters,'Receipt omits self-test')
AssertionError: 'guard_self_test' not found in mappingproxy(OrderedDict({'out': <Parameter "out">, 'cfg': <Parameter "cfg">, 'passed': <Parameter "passed">})) : Receipt omits self-test

======================================================================
FAIL: test_f2_main_records_failure_and_never_starts_workers (__main__.Round9Tests.test_f2_main_records_failure_and_never_starts_workers)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round9.py", line 190, in test_f2_main_records_failure_and_never_starts_workers
    self.assertTrue(hasattr(self.kit,'guard_self_test'),'Missing production self-test')
AssertionError: False is not true : Missing production self-test

======================================================================
FAIL: test_f2_real_guard_self_test_and_each_missed_operation (__main__.Round9Tests.test_f2_real_guard_self_test_and_each_missed_operation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round9.py", line 156, in test_f2_real_guard_self_test_and_each_missed_operation
    self.assertTrue(hasattr(self.kit,'guard_self_test'),'Missing production guard self-test')
AssertionError: False is not true : Missing production guard self-test

======================================================================
FAIL: test_f2_submit_requires_all_three_guard_checks (__main__.Round9Tests.test_f2_submit_requires_all_three_guard_checks)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round9.py", line 223, in test_f2_submit_requires_all_three_guard_checks
    self.assertIn("gate.get('guard_self_test')",helper.SUBMIT_CHECK,'Submit omits guard evidence')
AssertionError: "gate.get('guard_self_test')" not found in "import hashlib,json,os,sys,tarfile\nfrom pathlib import Path\np=Path(sys.argv[1]);pool=Path(sys.argv[2]);h=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()\npub=json.loads((p/'0.json').read_text());proof=json.loads((p/'a/c/CPU.json').read_text())\nwith tarfile.open(p/'0.tgz') as t:cfg=json.load(t.extractfile('9.json'))\nif h(p/'0.tgz')!=pub['payload_sha256']:raise ValueError('Payload differs')\nfor key in ('passed','entry_sequence_passed','bundle_guard_passed'):\n if proof.get(key) is not True:raise ValueError('CPU receipt failed: '+key)\nif (proof['plan']!=pub['plan_sha256'] or proof['payload']!=pub['payload_sha256'] or proof['inputs']!=h(p/'a/1.json') or proof['operator_sha256']!=h(p/'a/6.py')):raise ValueError('CPU receipt binding differs')\nmemory=proof['memory']\nif memory.get('fits') is not True or memory.get('basis')!='fixed_g3t_shapes' or memory.get('read_cache_bytes')!=cfg['read_cache_bytes']:raise ValueError('CPU memory proof differs')\nimport hashlib,json,sys,tarfile\nfrom pathlib import Path\np=Path(sys.argv[1]);c=json.loads((p/'a/c/CPU.json').read_text());v=json.loads((p/'0.json').read_text())\nsha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()\nassert c['passed'] is True and c['bundle_guard_passed'] is True and c['entry_sequence_passed'] is True\nassert c['payload']==v['payload_sha256'] and c['plan']==v['plan_sha256']\nassert c['operator_sha256']==sha(p/'a/6.py') and c['inputs']==sha(p/'a/1.json')\ng=c['bundle_guard']\nassert g['passed'] is True and g['path']=='7.py' and g['guard_target']=='6.py' and g['action']=='test'\nassert g['operator_sha256']==sha(p/'a/6.py') and g['batch_sha256']==sha(p/'BATCH.sh')\ne=c['entry_sequence'];root=Path(c['root'])\nassert e['passed'] is True and e['entry_sequence_passed'] is True\nassert e['events']==['guard_installed','write_test','operator_dispatch']\nassert e['operator_sha256_before']==e['operator_sha256_after']==c['operator_sha256']\nassert e['path']=='7.py' and e['guard_target']=='6.py' and e['action']=='test'\nassert e['operator_sha256']==c['operator_sha256'] and e['batch_sha256']==sha(p/'BATCH.sh')\nassert e['pool']==str(root/'wpool') and e['token']==v['token']\nw=e['write_test']\nassert type(w['bytes']) is int and w['bytes']==4*1024**2\nassert isinstance(w['sha256'],str) and len(w['sha256'])==64 and all(ch in '0123456789abcdef' for ch in w['sha256'])\nwith tarfile.open(p/'0.tgz') as archive:\n    guard_sha=hashlib.sha256(archive.extractfile('orchard_h10/vendor/return_io.py').read()).hexdigest()\nassert e['guard_target_sha256']==guard_sha\nassert {k:v for k,v in e.items() if k!='entry_sequence_passed'}==g\nassert e['requested_argv'][-2:]==[str(root/'a/5.py'),str(root/'a/1.json')]\nassert e['dispatched_argv']==e['requested_argv'][:-2]+[str(root/'7.py'),str(root/'a/1.json')]\nm=c['memory']\nassert m==json.loads((p/'a/c/MEMORY.json').read_text())\nassert m['fits'] is True and m['basis']=='fixed_g3t_shapes'\nassert m['perception_memo_modules']==['g3t'] and m['sam_measurement_required'] is False\nprint('All CPU receipt checks passed')\nfor name in ('dry.json','dry2.json'):\n if json.loads((p/'a'/name).read_text()).get('passed') is not True:raise ValueError('Dry check failed')\nif not pool.is_dir() or pool.is_symlink():raise ValueError('Return pool missing or linked')\ntotal=0\ndef fail(error):raise error\nfor base,dirs,files in os.walk(str(pool),followlinks=False,onerror=fail):\n for name in dirs+files:\n  f=Path(base)/name\n  if f.is_symlink():raise ValueError('Unexpected pool symlink')\n for name in files:\n  total+=(Path(base)/name).stat().st_size\n  if total>75000000:raise ValueError('Return pool exceeds 75 MB')\ndef decode(v):\n if isinstance(v,str):return bytes.fromhex(v[1:]).decode() if v.startswith('u') else (_ for _ in ()).throw(ValueError('Invalid gate token'))\n if isinstance(v,dict):return {decode(k):decode(x) for k,x in v.items()}\n if isinstance(v,list):return [decode(x) for x in v]\n return v\ngate=decode(json.loads((p/'a/g.json').read_text())['u0'])\nkeys=('stage1_select_rule','perception_memo','perception_memo_modules','perception_memo_verify_ids','save_own_depth','read_processor_only','read_processor_cache','read_vision_cache','read_sam_cache','read_cache_bytes')\nexpected={k:cfg[k] for k in keys}\nif (gate.get('passed') is not True or gate.get('adoption_plan_sha256')!=pub['plan_sha256'] or gate.get('required_device_type')!='H100_80GB' or json.dumps(gate.get('adoption_profile'),sort_keys=True)!=json.dumps(expected,sort_keys=True)):raise ValueError('GPU gate differs from adopted plan/profile/device')\nassets=dict(restore=proof['ready']['restore'],binding=proof['ready']['binding'],export_pin=h(p/'a/export.json'))\nif gate.get('adoption_assets')!=assets:raise ValueError('GPU gate assets differ from CPU proof')\nif gate.get('adoption_kit')!=cfg['gate_kit_sha256']:raise ValueError('GPU gate kit/comparator/sample differ from MANIFEST pins')\nenvironment=json.loads((p/'a/c/ENVIRONMENT.json').read_text())\nenvironment_sha=h(p/'a/c/ENVIRONMENT.json')\nif environment_sha!=proof['ready']['environment']:raise ValueError('CPU environment receipt differs')\nexpected_environment=dict(sha256=environment_sha,torch=environment['versions']['torch'],transformers=environment['versions']['transformers'],cuda=environment['cuda'])\nif gate.get('adoption_environment')!=expected_environment:raise ValueError('GPU gate environment versions/hash differ')\nprint(json.dumps(dict(passed=True,pool_bytes=total)))\n" : Submit omits guard evidence

======================================================================
FAIL: test_f3_staging_transfer_precedes_allocation_and_roots_extract (__main__.Round9Tests.test_f3_staging_transfer_precedes_allocation_and_roots_extract)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round9.py", line 241, in test_f3_staging_transfer_precedes_allocation_and_roots_extract
    self.assertLess(text.index(marker),allocation,marker)
AssertionError: 19997 not less than 16512 : --enable-extensions gate

======================================================================
FAIL: test_info_round7_logs_are_labelled (__main__.Round9Tests.test_info_round7_logs_are_labelled)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round9.py", line 283, in test_info_round7_logs_are_labelled
    self.assertTrue((OUT/'checks/round7'/('applied_'+name+'.txt')).is_file(),name)
AssertionError: False is not true : lock_round3

======================================================================
FAIL: test_info_token_and_framework_gap_and_guard_limits (__main__.Round9Tests.test_info_token_and_framework_gap_and_guard_limits)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round9.py", line 271, in test_info_token_and_framework_gap_and_guard_limits
    self.assertIn('GPU_KIT="/scratch/jjyeung/${GATE_TOKEN}"',text)
AssertionError: 'GPU_KIT="/scratch/jjyeung/${GATE_TOKEN}"' not found in 'The GPU kit is unrun. It requires zero answer/trace byte differences. Its 50 items cover ten items per type and twelve captures; this reuse-heavy sample does not predict full-read throughput.\n\nUse the full **A4/src** base pinned by `BASE_PIN.json`. The reader patches also apply to the inspected B5 source subset, but this kit does not authenticate a B5 base. Apply patches 01–03 to a separate source copy. They add `u0/`; all original reader files remain byte-identical. Apply 04–05 to a separate A4 operator copy, outside `src`.\n\nThe ordinary entrypoint stays OFF and imports no extension. `u0/a8.py --enable-extensions` explicitly selects the extensions; individual cache settings then default OFF. The ON environment records an extension source hash. Rebuild payload and artifact pins before deployment.\n\n## Local preparation\n\nThese commands use paths supplied by the operator; they do not depend on the author\'s `work/` directory. Set `DELIVERY` to the delivered `out/`, `A4_BASE` to the full supplied A4 directory on local scratch, `LOCAL` to a fresh local scratch directory, and `READ_PYTHON` to the approved Python executable. Both source roots and all outputs must stay on local scratch. The package contains code, not model/data archives.\n\n```bash\nset -euo pipefail\n: "${DELIVERY:?Absolute path to delivered out directory}"\n: "${A4_BASE:?Absolute path to the full pinned A4 directory on local scratch}"\n: "${LOCAL:?Fresh local scratch directory}"\n: "${READ_PYTHON:?Approved Python executable}"\nexport PYTHONDONTWRITEBYTECODE=1 TOKENIZERS_PARALLELISM=false\nexport OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8\nexport XDG_CACHE_HOME="$LOCAL/cache" HF_HOME="$LOCAL/cache/hf" TRITON_CACHE_DIR="$LOCAL/cache/triton"\nmkdir -p "$LOCAL/source" "$LOCAL/a4"\nnice -n 10 tar -cf - -C "$A4_BASE/src" . | nice -n 10 tar -xf - -C "$LOCAL/source"\nnice -n 10 tar -cf - -C "$A4_BASE" package tower_sequence.py fetch_return.py unpack_return.py |\n  nice -n 10 tar -xf - -C "$LOCAL/a4"\nnice -n 10 patch --batch --fuzz=0 -p1 -d "$LOCAL/source" < "$DELIVERY/patches/01_bounded_read_caches.diff"\nnice -n 10 patch --batch --fuzz=0 -p1 -d "$LOCAL/source" < "$DELIVERY/patches/02_atomic_scene_shards.diff"\nnice -n 10 patch --batch --fuzz=0 -p1 -d "$LOCAL/source" < "$DELIVERY/patches/03_production_integration.diff"\nnice -n 10 patch --batch --fuzz=0 -p1 -d "$LOCAL/a4" < "$DELIVERY/patches/04_operator_cache_bound.diff"\nnice -n 10 patch --batch --fuzz=0 -p1 -d "$LOCAL/a4" < "$DELIVERY/patches/05_operator_return_and_proof.diff"\nEXT_SOURCE="$LOCAL/source"\n```\n\nKeep the private kit, original manifests and reverse maps on Trinity. Stage each source tree as one archive and extract it only on node-local scratch. Both parity source roots must remain pristine: no build outputs, extra files or symlinks. Public paths, submission names, configuration and logs must use opaque tokens. Never transfer private reverse maps to Orchard.\n\n## Bound export, build and operations\n\nThe candidate uses **A4\'s 636-item schedule, one card, caches only, general/no-requeue**. A4\'s export admission, submit helper and run settings remain intact. `a19` requires the reviewed payload hash `4498fca72a8e4b476b38f097ffdf3ff88b5aa20fc036bd196b18a5706e9fe46d`, the patched operator hashes, all copied A4 members, the base BATCH.sh and decoded bootstrap pins from MANIFEST, the exact extension inventory and the four original alias bases. It authenticates them before copying. Its batch uses cont_ops\' exact `build_r10.wrap_batch`: excluded node, EXIT log return and USR1 forwarding.\n\nThe kit binds **step 400 only**, read A of job **173060**, source package **a15_cot_apdc76460c3a164**. Its artifact SHA256 is **5083243cfedd2a389dfca579c5452e7d0c73b03a58e1cb7d204292ddd10e67cd**. `operations/BOUND_EXPORT.json` preserves the supplied export pin. `operations/binding.default.json` combines that identity, the four archive-part sizes in the supplied `a/1.json`, and the reviewed `bind400_partial.json` operation paths. `DEFAULT_EXPORT_PROVENANCE.json` records all source hashes. These are authenticated metadata; production weights were not restored here.\n\n`a19 build` checks the reviewed step-400 identity and preparation hashes before reading or copying the base. No other export can authorize adoption. A fresh package token identifies the ON build; it does not reuse the source package\'s token.\n\n```bash\nset -euo pipefail\nEXPORT_BINDING="$DELIVERY/operations/binding.default.json"\n: "${PACKAGE_TOKEN:?Fresh 11-16 hex characters starting with a-f}"\nPROFILE_ARGS=()  # All three caches, 12 GiB. For processor-only: PROFILE_ARGS=(--processor-only)\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a19.py" \\\n  --enable-extensions --base-operator "$LOCAL/a4" --source-root "$EXT_SOURCE" \\\n  --manifest "$DELIVERY/patches/MANIFEST.json" --extension-pins "$DELIVERY/kit_parity50/EXTENSION_PINS.json" \\\n  --export-binding "$EXPORT_BINDING" --token "$PACKAGE_TOKEN" --out "$LOCAL/adopted" "${PROFILE_ARGS[@]}"\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a20.py" --enable-extensions operations \\\n  --operator "$LOCAL/adopted" --binding "$EXPORT_BINDING" --dry-root "$DELIVERY/operations" --out "$LOCAL/ops"\nnice -n 10 tar -czf "$LOCAL/0.tgz" -C "$LOCAL/ops" .\nnice -n 10 sha256sum "$LOCAL/0.tgz"\n```\n\n`adopted` retains the exact local source/operator/unpacker. `ops/1.tgz` is the package delivery, with `ops/SHA256`; the outer archive carries it and five inert scripts. The commands below are **owner operations on Orchard, unrun here**. Transfer the single outer archive through the owner\'s existing authorized transport. Set `OPS_ARCHIVE` to its received opaque path, `OPS_SHA256` to the printed local hash, and `D` to a fresh opaque operation directory. These are transport endpoints, not generated receipt values.\n\n```bash\nset -euo pipefail\n: "${OPS_ARCHIVE:?Received outer archive on Orchard}"\n: "${OPS_SHA256:?Printed local SHA256 of that archive}"\n: "${D:?Fresh opaque operation directory on Orchard}"\n: "${PACKAGE_TOKEN:?Copy the fresh build token to this Orchard shell}"\nprintf \'%s  %s\\n\' "$OPS_SHA256" "$OPS_ARCHIVE" | sha256sum -c -\ntest ! -e "$D"\nmkdir -m 700 "$D"\ntar -xzf "$OPS_ARCHIVE" -C "$D"\nbash "$D/o_place.sh"\nbash "$D/o_pull_fill.sh"\n# BEGIN FILL_WAIT\n: "${PACKAGE_TOKEN:?Copy the fresh build token to this Orchard shell}"\nP=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}\nFILL_MAX_SECONDS=${FILL_MAX_SECONDS:-14400}\n[[ "$FILL_MAX_SECONDS" =~ ^[0-9]+$ ]] && (( FILL_MAX_SECONDS >= 1 && FILL_MAX_SECONDS <= 14400 )) || exit 1\nFILL_DEADLINE=$((SECONDS + FILL_MAX_SECONDS))\nwhile test ! -f "$P/a/1.txt"; do\n  FILL_PID=$(cat "$P/a/0.txt") || exit 1\n  [[ "$FILL_PID" =~ ^[1-9][0-9]*$ ]] || exit 1\n  if ! kill -0 "$FILL_PID" 2>/dev/null && test ! -f "$P/a/1.txt"; then\n    echo \'Fill worker is gone without an exit receipt\' >&2; exit 1\n  fi\n  if (( SECONDS >= FILL_DEADLINE )); then\n    echo \'Fill wait exceeded its maximum\' >&2; exit 1\n  fi\n  FILL_REMAIN=$((FILL_DEADLINE - SECONDS))\n  sleep "$(( FILL_REMAIN < 60 ? FILL_REMAIN : 60 ))"\ndone\ntest "$(cat "$P/a/1.txt")" = 0\n# END FILL_WAIT\nbash "$D/o_cpu.sh"\n```\n\n`o_place.sh` verifies the inner archive and places it at `$P=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}`. `o_pull_fill.sh` acquires the permanent attempt lock `$P/a/0.lock`, launches one detached nohup worker, and returns its PID in `$P/a/0.txt`. The worker logs to `$P/a/0.log` and writes its exit status to `$P/a/1.txt` on success or failure. Run the wait on the same host that launched the detached worker. It checks at most once per minute, refuses a vanished PID without `1.txt`, and stops after at most 14,400 seconds (four hours). A duplicate launch refuses; a failed or interrupted attempt requires a fresh package/token, never an automatic retry. The worker copies the reviewed `done` and `prep_paths` files to `$P/a/e/{5,7,8,9}`, authenticates their pins (the `.done` receipt uses whitespace-separated fields), fetches export parts `0..3` once with retries disabled, fills through `a/4.py`, and runs cont_ops\' verbatim `dryres2.py` and `dry2.py`. A failed transfer stops; the scripts do not retry it.\n\n`o_cpu.sh` requests the A4 CPU allocation explicitly: preempt, eight CPUs, 200G, four hours, no GPU, no requeue, and the excluded nodes. The **CPU allocation** is separate from the intended **general GPU read**. Wait for the CPU job to finish successfully. Preserve `$P/a/c/CPU.json`, `MEMORY.json` and the exact `SETTINGS.json` emitted by A4 prepare. Bring these small files back as one archive through the authorized transport to `$LOCAL/adopted/proof/` before the parity preparation below. Before writing CPU.json, the ON proof streams `logical/d` through its live `J.namespace(root)` to the named shared staging path `$P/a/4.tar`, outside the capped return pool. It refuses any symlink whose resolved target leaves `logical/d` (including directory links, chains, dangling links and cycles), preserves admitted links with `tar -cf - -C <logical>/d .`, and records `gate_assets.path`, `logical`, `sha256` and `bytes` in CPU.json. The output file is opened outside bwrap and tar writes to that descriptor. This uses the same preparation/READY as the proof, without a second staging job. Validation and tar run in the same live namespace. Tar stderr goes to `results/4.err`. A tar failure leaves no successful CPU.json and is not retried. The proof also emits exact `a/1.json`, restore, artifact-binding, manifest, export-pin and ENVIRONMENT.json receipts. ON prepare adds the compiled CUDA version to ENVIRONMENT.json and its SHA256 to READY. These small files authenticate staging; they do not contain model weights. The proof binds payload/plan/inputs/operator, must pass bundle/entry checks and contain `memory.read_cache_bytes=12884901888` (4294967296 for processor-only), `basis=fixed_g3t_shapes`, and `fits=true`.\n\nArchive the CPU evidence on Orchard after its successful completion, using the package token printed by the build:\n\n```bash\nset -euo pipefail\nP=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}\ntar -czf "$D/2.tgz" -C "$P/a/c" CPU.json MEMORY.json SETTINGS.json RESTORE.json binding.json manifest.json EXPORT_PIN.json 1.json ENVIRONMENT.json\nsha256sum "$D/2.tgz"\n```\n\nAfter authorized transport, authenticate and extract that archive on local scratch:\n\n```bash\nset -euo pipefail\n: "${PROOF_ARCHIVE:?Received CPU-evidence archive on local scratch}"\n: "${PROOF_SHA256:?Printed Orchard SHA256 of the CPU-evidence archive}"\nprintf \'%s  %s\\n\' "$PROOF_SHA256" "$PROOF_ARCHIVE" | nice -n 10 sha256sum -c -\nmkdir "$LOCAL/adopted/proof"\nnice -n 10 tar -xzf "$PROOF_ARCHIVE" -C "$LOCAL/adopted/proof"\n```\n\nAfter the zero-difference GPU parity gate passes, transfer its token-only `ue.json` through the authorized transport as one archive, preserving the SHA256 printed on the GPU host. The authorized owner authenticates that archive and installs the receipt before submission:\n\n```bash\nset -euo pipefail\n: "${GATE_ARCHIVE:?Received archive containing ue.json}"\n: "${GATE_SHA256:?SHA256 printed on the GPU host}"\nprintf \'%s  %s\\n\' "$GATE_SHA256" "$GATE_ARCHIVE" | sha256sum -c -\nmkdir "$D/g"\ntar -xf "$GATE_ARCHIVE" -C "$D/g"\nP=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}\ntest ! -e "$P/a/g.json"\ncp "$D/g/ue.json" "$P/a/g.json"\n```\n\nThen run:\n\n```bash\nset -euo pipefail\nbash "$D/o_sub.sh"\n# After the GPU job finishes:\nbash "$D/o_fetch.sh"\nP=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}\ntar -czf "$D/3.tgz" -C "$P/a/f" 0.tgz EXIT.json\nsha256sum "$D/3.tgz"\n```\n\n`o_sub.sh` embeds cont_ops’ A4 CPU-receipt assertions verbatim, including batch/dispatch/guard pins and MEMORY.json equality, then checks cache memory and the successful GPU receipt at `$P/a/g.json`, requires both dry checks to pass, requires an empty general queue, and refuses a return pool over **75,000,000 bytes** (including errors/symlinks). It then runs `3.py check` and one `3.py submit --gpus 1 --time 04:30:00`, saving the job ID. The GPU receipt must match the CPU restore/binding pins, filled export pin, adopted plan/profile and H100 80 GB requirement. The unchanged bootstrap itself does not require the cache-memory field; this submit preflight does. `o_fetch.sh` derives the authenticated return token and fetches `$P/a/f/{0.tgz,EXIT.json}`.\n\nTransfer `$D/3.tgz` through the authorized transport, preserving the local operator directory. Authenticate, extract and unpack it locally:\n\n```bash\nset -euo pipefail\n: "${RETURN_ARCHIVE:?Received fetched-return archive on local scratch}"\n: "${RETURN_SHA256:?Printed Orchard SHA256 of the fetched-return archive}"\nprintf \'%s  %s\\n\' "$RETURN_SHA256" "$RETURN_ARCHIVE" | nice -n 10 sha256sum -c -\nmkdir "$LOCAL/adopted/f"\nnice -n 10 tar -xzf "$RETURN_ARCHIVE" -C "$LOCAL/adopted/f"\n(cd "$LOCAL/adopted" && CUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -s -E -B ./unpack_return.py \\\n  --archive "$LOCAL/adopted/f/0.tgz" --exit "$LOCAL/adopted/f/EXIT.json" \\\n  --out "$LOCAL/adopted/ret" > "$LOCAL/adopted/unpack-success.json" && \\\n  test -s "$LOCAL/adopted/unpack-success.json")\n```\n\nA refused unpack leaves its extracted tree behind. Scorers must consume only unpack\'s **success output after exit status 0**, never a directory merely because it exists; the command\'s `&&` chain enforces that handoff. A successful partial return still has `complete=false` and must not be scored as complete. The ON unpacker refuses any existing weight receipt whose verified value is not JSON true. Processor-only journals need no weight receipt. OFF behavior remains unchanged. Whole-archive identity follows A4\'s design: fill checks the sealed whole-tar constants; job/unpack admission compare against inputs.archives[0].\n\n**Forecasts:** Package D is the 580-item distance read (B5 fork, 03:30 walltime); it has **no ON route** in a19. Its one-card **estimate** is 13,813.069 s (3 h 50 min), using the measured 23.600 s/item and crediting no cache saving. The **636-item** A4 read that a19 actually builds has an **estimate** of **7,351.824 s (2 h 02 min 32 s; 11.559 s/item)**, obtained by carrying forward the supplied A4 total, with zero assumed saving. Target weights, cache costs and staging/queue delays can change it; neither forecast measures the selected export.\n\n## GPU parity staging and acceptance\n\nThe gate must seal **A4 prepare\'s actual output plus the operator\'s per-read overrides** for the package being adopted. Do not supply an unrelated PRIVATE_SETTINGS.json. `a20 gate` checks the prepared bytes and exact RESTORE.json/artifact-binding bytes against CPU.json’s READY pins, checks export identity against the adopted step binding, checks the export-pin hash and byte count against the exact `a/1.json` bytes authenticated by CPU.json, and checks payload, plan and operator bindings. The complete export must equal the supplied step-400 pin. The gate also authenticates ENVIRONMENT.json against CPU READY; submit compares its hash and torch/transformers/CUDA versions with ue.json. Every GPU worker rechecks those asset bytes and the artifact manifest before reading; changing paths cannot substitute another checkpoint. It applies the authenticated operator descriptor and derives `enable_caches`, `read_cache_bytes` and the full adoption profile: candidates_argmax, memo on, g3t, empty verify IDs, save_own_depth=false, and the exact cache switches. Both the parent driver and every worker refuse a different profile. Processor-only adoption is explicitly gated with slots `[0]` and 4 GiB; all-cache adoption uses `[0,1,2]` and 12 GiB.\n\nThe **owner-only commands below are unrun here**. The shared asset archive already exists when CPU.json appears; never try to reopen the CPU job\'s private `/tmp`. Reserve storage for the archive before running `o_cpu.sh`: **about 33 GB, estimated**, from about 32.6 GB of expanded inputs plus tar headers. Preserving symlinks avoids duplicated shards and heads. Reserve separate space for extraction, sources and runtime outputs. The job records actual bytes; no production archive size was measured here.\n\nAllocate the gate on Orchard, then enter its compute task. This is one non-requeued H100 job, eight CPUs, 200G and a five-hour maximum. Preserve its actual `CUDA_VISIBLE_DEVICES`; the Python guard requires exactly `NVIDIA H100 80GB HBM3`, 132 SMs, capability 9.0 and the 80 GB memory class.\n\n```bash\nset -euo pipefail\nGATE_TOKEN=$(/usr/bin/python3 -I -s -B -c \'import secrets;print(secrets.token_hex(6))\')\nsalloc --account=mt01 --partition=general --nodes=1 --ntasks=1 --cpus-per-task=8 \\\n  --mem=200G --gres=gpu:1 --time=05:00:00 --no-requeue \\\n  --exclude=orchard-community-2 --job-name="a15_cot_ap${GATE_TOKEN}" \\\n  srun --ntasks=1 --pty bash --noprofile --norc\n```\n\nOn that H100 host, `/scratch/jjyeung` must **physically exist and be writable** outside bwrap. A4 creates `/scratch` only inside its namespace; it does not satisfy this host requirement. The operator must provision the host path before the gate. The exact logical root (currently `/scratch/jjyeung/b01ec87a6f29b`) must be absent so extraction cannot overlay another run. Preserve it so manifests and restore paths remain valid. Provision the separate opaque kit/source directories there too. Stage the source trees and public kit as single authenticated archives; keep private inputs and reverse maps on Trinity.\n\nThe shared path `$P/a/4.tar` is visible directly on Orchard. If approved transport copies it, set `ASSET_ARCHIVE` to that received path; CPU.json still supplies the expected hash and bytes. Run inside the allocation:\n\n```bash\nset -euo pipefail\n: "${PACKAGE_TOKEN:?Fresh package token from the build}"\nP=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}\nASSET_ARCHIVE=${ASSET_ARCHIVE:-"$P/a/4.tar"}\nGPU_LOGICAL=$(/usr/bin/python3 -I -s -B - "$P" "$ASSET_ARCHIVE" <<\'PYASSET\'\nimport hashlib,json,sys,tarfile\nfrom pathlib import Path\np=Path(sys.argv[1]);archive=Path(sys.argv[2]);proof=json.loads((p/\'a/c/CPU.json\').read_text())\nassert proof[\'passed\'] is True\nwith tarfile.open(p/\'0.tgz\') as t:cfg=json.load(t.extractfile(\'9.json\'))\nasset=proof[\'gate_assets\'];assert asset[\'logical\']==cfg[\'logical\']\nassert Path(asset[\'path\']).resolve()==(p/\'a/4.tar\').resolve() and archive.stat().st_size==asset[\'bytes\']\nh=hashlib.sha256()\nwith archive.open(\'rb\') as stream:\n    for chunk in iter(lambda:stream.read(1024**2),b\'\'):h.update(chunk)\nassert h.hexdigest()==asset[\'sha256\']\nprint(cfg[\'logical\'])\nPYASSET\n)\ntest -d /scratch/jjyeung && test -w /scratch/jjyeung\ntest ! -e "$GPU_LOGICAL"\nmkdir -p "$GPU_LOGICAL/d" "$GPU_LOGICAL/p"\ntar -xf "$ASSET_ARCHIVE" -C "$GPU_LOGICAL/d"\ntar -xzf "$P/0.tgz" -C "$GPU_LOGICAL/p"\ntest ! -e "$GPU_LOGICAL/d/7.json"\nln -s binding.json "$GPU_LOGICAL/d/7.json"\ntest ! -e "$GPU_LOGICAL/d/9.json"\nln -s ENVIRONMENT.json "$GPU_LOGICAL/d/9.json"\n```\n\nCreate a private neutral configuration from `config.example.json` with separate authenticated A4 original/patched source roots. Set `export=$GPU_LOGICAL/d/e`, `export_pin=$GPU_LOGICAL/d/6.json`, and `artifact_manifest=$GPU_LOGICAL/d/7.json`. Set `environment_receipt=$GPU_LOGICAL/d/9.json`. The neutral binding and environment aliases must be symlinks, as created above. Include that exact `binding.json` to `7.json` mapping in `PRIVATE_ALIASES.json`; map the other private prepared asset paths to staged opaque aliases of those same files. These aliases must be symlinks so `resolve()` reaches the manifest allow-list target; copies are rejected. Keep private settings and reverse maps on Trinity. The following commands use files under `$LOCAL`:\n\n```bash\nset -euo pipefail\n: "${PRIVATE_CONFIG_TEMPLATE:?Private neutral GPU configuration with staged asset paths}"\n: "${PRIVATE_ALIASES:?Private JSON mapping preparation paths to staged opaque paths}"\nPRIVATE_SETTINGS="$LOCAL/PRIVATE_SETTINGS.json"\nPRIVATE_CONFIG="$LOCAL/PRIVATE_NEUTRAL_CONFIG.json"\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a20.py" --enable-extensions gate \\\n  --operator "$LOCAL/adopted" --prepared "$LOCAL/adopted/proof/SETTINGS.json" \\\n  --proof "$LOCAL/adopted/proof/CPU.json" --config "$PRIVATE_CONFIG_TEMPLATE" \\\n  --asset-receipts "$LOCAL/adopted/proof" \\\n  --settings-out "$PRIVATE_SETTINGS" --config-out "$PRIVATE_CONFIG"\n```\n\n```bash\nset -euo pipefail\nmkdir -p "$LOCAL/public"\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a11.py" seal \\\n  --source-root "$EXT_SOURCE" --input "$PRIVATE_SETTINGS" --aliases "$PRIVATE_ALIASES" \\\n  --out "$LOCAL/public/u3"\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a11.py" stage-kit \\\n  --source-root "$EXT_SOURCE" --input "$DELIVERY/kit_parity50" \\\n  --config "$PRIVATE_CONFIG" --out "$LOCAL/public/u0"\n```\n\nThe package embeds the driver/comparator SHA256 and the deterministically sealed sample SHA256 from MANIFEST `kit_files`. The driver and every worker authenticate those executing bytes, and `ue.json` carries them to SUBMIT_CHECK. The staged `u3.json` pins every extension; `u4.json` authenticates both full 927-file base inventories. The driver rejects changed bases, equal original/patched roots, and an original root containing extensions. It authenticates the sealed sample bytes and the logical sample pin. Transfer only the staged directory through the approved transport under an opaque root.\n\nOn an assigned **H100 80 GB** GPU, run the acceptance command below; it is **unrun here**. Preserve that allocation\'s actual `CUDA_VISIBLE_DEVICES`.\n\n```bash\nset -euo pipefail\n# BEGIN GPU_ENVIRONMENT\n: "${GPU_LOGICAL:?Exact logical root extracted above}"\nGPU_KIT=/scratch/jjyeung/ab0123456789\nREAD_PYTHON="$GPU_LOGICAL/d/v/py"\nexport XDG_CACHE_HOME="$GPU_KIT/u6" HF_HOME="$GPU_KIT/u6/u0" TRITON_CACHE_DIR="$GPU_KIT/u6/u1"\nexport HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1\nexport PYTHONDONTWRITEBYTECODE=1 TOKENIZERS_PARALLELISM=false\nexport OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8\nmkdir -p "$XDG_CACHE_HOME" "$HF_HOME" "$TRITON_CACHE_DIR"\nnice -n 10 "$READ_PYTHON" -I -s -B - "$GPU_LOGICAL/d/ENVIRONMENT.json" <<\'PYENV\'\nimport json,sys,torch,transformers\nfrom pathlib import Path\ntorch.set_num_threads(8)\nenvironment=json.loads(Path(sys.argv[1]).read_text())\nactual=dict(torch=torch.__version__,transformers=transformers.__version__,cuda=torch.version.cuda)\nexpected=dict(torch=environment[\'versions\'][\'torch\'],transformers=environment[\'versions\'][\'transformers\'],cuda=environment[\'cuda\'])\nif actual!=expected or not actual[\'cuda\'] or not torch.cuda.is_available():\n    raise ValueError(\'GPU interpreter/environment preflight failed\')\nprint(\'Environment preflight passed\')\nPYENV\n# END GPU_ENVIRONMENT\nnice -n 10 "$READ_PYTHON" -I -s -B /scratch/jjyeung/ab0123456789/u0/u0.py \\\n  /scratch/jjyeung/ab0123456789/u0/u2.json --out /scratch/jjyeung/ab0123456789/u9 \\\n  --enable-gpu --public --repeat-baseline --shards 4\n```\n\nThe preflight runs the archived production interpreter outside bwrap and fails before the gate if it cannot start, lacks dependencies/CUDA, or differs from ENVIRONMENT.json. No substitute interpreter is accepted. The gate parent, every worker and receipt writer independently compare the recorded versions and SHA256. Cache roots are explicit under the opaque kit root, matching A4\'s XDG/HF pattern with an explicit Triton root.\n\nEvery arm starts a fresh process. ORIGINAL/OFF/OFF_REPEAT use ordinary journals and modulo shards. ON tests caches; ON_JOURNAL and sequential whole-scene shards test separate journal/shard features. Sequential shards establish equality, not parallel speed. Public logs tokenize item/native/room identities and arbitrary stdout/stderr. No reverse map is written on Orchard.\n\nAcceptance requires all 50 expected IDs, complete production output schemas, nonempty text/tokens/heads, scale even when null, every served response and forced-token count, matching call counters, and **zero semantic byte differences**. ORIGINAL/OFF must also retain every production source hash. Each enabled cache must report its memory bound and useful hits; SAM needs both feature and detection hits. Empty or all-miss runs fail. Only clocks and explicit audit/cache/memo telemetry are excluded from semantic comparison; audit violations fail. There is no answer/trace tolerance.\n\nEach RUN.json and ue.json record the checked torch/transformers/CUDA versions and ENVIRONMENT.json SHA256. Each RUN.json also records the adopted package plan, read profile, asset pins, required device type, actual device, cache slots and budget. The worker checks CUDA device properties before model loading and refuses a different exact name, SM count, compute capability or memory class. `ue.json` is written only after all comparisons finish and records whether they all passed; failed or missing receipts cannot authorize submit. On the H100 host, archive it with `tar -cf /scratch/jjyeung/ab0123456789/5.tar -C /scratch/jjyeung/ab0123456789/u9 ue.json` and print `sha256sum /scratch/jjyeung/ab0123456789/5.tar` for authenticated return transport. Judge net time from `RUN.json`\'s `worker_wall_seconds`, which includes install/boundary hashing and eager SAM loading. Per-item timing alone cannot establish savings. ON constructs SAM outside inference mode to obtain tracked parameters; that changes loading time and potentially RNG use. The GPU byte gate must clear it. The sample overrepresents clip reuse: its ten distance items share one clip, while A4 has 150 distance items across 60 clips (review finding 7).\n\nThe cache cap covers retained cache storage and transient copies, not model/caller working memory. Measure full-process host/GPU peaks. Models must remain frozen: calls check parameter/buffer identities, pointers and counters; install/type boundaries hash content. Persistent raw writes fail at a boundary. Raw writes restored between boundaries, private tensor attributes and arbitrary non-tensor state are outside this guard\'s coverage. Graceful stops verify journals; a hard kill can leave an unchecked journal that requires fresh output.\n\nOutput directories u0–u5 represent ORIGINAL/OFF/OFF_REPEAT/ON/ON_JOURNAL/SHARDED. Reports u6–ua compare arms; ub.json checks merge equality; uc/ud contain canonical single/sharded returns. Restore on Trinity with the private inputs:\n\n```bash\nset -euo pipefail\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a11.py" restore \\\n  --source-root "$EXT_SOURCE" --input PRIVATE_RETURN --out "$LOCAL/restored" \\\n  --private-source "$DELIVERY/kit_parity50/sample50.json" \\\n  --private-source "$PRIVATE_CONFIG" --private-source "$PRIVATE_SETTINGS"\n```\n\nRestoration authenticates committed rows before rebuilding private IDs/checksums. Merge with the original manifest through the explicit extension entrypoint. The canonical answer/trace archive must match exactly; transport-envelope clocks remain variable.\n\n## Array validation\n\nNo multi-card A4 operator is delivered. The array helper is a separate inert prototype. Its example has `approved=false`: two one-hour shards, at most two attempts, four GPU-hours total. Approval must bind the exact partition, shards, time and attempts, with no more than five allocated GPU-hours over all attempts. Before any sharded/preempt adoption, validate real persistent-storage preemption/requeue.\n\n```bash\nset -euo pipefail\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a15.py" PRIVATE_ARRAY_CONFIG.json \\\n  --enable-array --token ab0123456789 --out "$LOCAL/array-plan" \\\n  --python /scratch/jjyeung/ab0123456789/u1 --source /scratch/jjyeung/ab0123456789/u2 \\\n  --staged-config /project/community/jjyeung/okh7/a15_cot_apab0123456789/u3.json\n```\n\nThis writes commands without running them. Exit 75 requests bounded requeue; other errors remain failures. Lock waits stop after 60 seconds, and the attempt limit forbids more work. Public paths must use approved roots and pass the forbidden-word screen; name checks do not establish storage permissions or capacity.\n\nNo delivered CPU suite or single-GPU kit requires a local OS socket. StageOneSocket is a Python callback. Real restore, bwrap isolation, remote transport, GPU parity/performance/memory and persistent requeue remain unrun.\n\n## Review round 7: finding -> fix -> test\n\n| Finding | Fix | Regression |\n|---|---|---|\n| 1. Private root disappears | Archive inside CPU proof to `$P/a/4.tar` before CPU.json; record hash/bytes. | Real fixture tar runs through a namespace wrapper, survives loss of the root, and the CPU operator fixture executes staging. |\n| 2. Fill wait hangs | Guard PACKAGE_TOKEN, check PID and cap wait at four hours. | Missing token, dead PID, timeout and failed exit refuse; success passes. |\n| 3. PCIe accepted | Require exact HBM3 name and 132 SMs. | SXM stub passes; PCIe and wrong-SM stubs refuse. |\n| 4. Evidence/host nits | Bind executing kit/comparator/sample; include a/1.json; unpack with -s -E -B; use an H100-local archive path. | Mutated pins refuse, environment-polluted unpack succeeds, allocation/evidence blocks are checked. |\n| 5. Decision export | Bind only the supplied step-400 export at build and gate. | Other identities refuse before the builder reads the base; wrong artifact refuses at the gate. |\n\nFrozen weights remain required. Persistent raw writes are boundary-checked; writes restored between boundaries remain outside the guard. GPU byte equality and performance remain unrun.\n\n## Review round 8: finding -> fix -> test\n\n| Finding | Fix | Regression |\n|---|---|---|\n| 1. Archive breaks loader admission | Preserve in-tree symlinks; refuse escaping targets before tar; estimated archive is about 33 GB. | Extract an absolute heads link and run real Artifact.verify/load_native admission; reject external, chained, directory, dangling and cyclic links. |\n| 2. Environment unspecified | Use archived d/v/py; preflight versions/CUDA; pin ENVIRONMENT.json through READY, gate and submit; set opaque cache roots. | Changed versions/hash and CPU build refuse; synthetic matching versions pass; submit rejects each changed field. |\n| 3. Other export checked late | Builder admits only reviewed step-400 identity/preparation. | Eleven identity/preparation mutations refuse before reading the base. |\n| 4. Unresolved package path | Resolve both archive-path operands. | README validation executes through a symlinked package parent. |\n| 5. Handoff details | Aliases are symlinks; retain tar stderr; generate a fresh a15_cot_ap job token. | Error text survives; commands and alias instructions are checked. |\n'

----------------------------------------------------------------------
Ran 11 tests in 0.016s

FAILED (failures=11)
```

Command: `bash work/cpu.sh work/run_checks.py  # round10_before; exact environment/argv in runner`

Exact output ([checks/round10_before.txt](checks/round10_before.txt)):

```text
test_f1_public_script_is_pinned_and_tampering_refuses (__main__.Round10Tests.test_f1_public_script_is_pinned_and_tampering_refuses) ... FAIL
test_f1_real_boot_refuses_c_and_runs_actual_preflight_script (__main__.Round10Tests.test_f1_real_boot_refuses_c_and_runs_actual_preflight_script) ... FAIL
test_f2_missing_nested_path_refuses_before_self_test (__main__.Round10Tests.test_f2_missing_nested_path_refuses_before_self_test) ... FAIL
test_f2_stage_resolves_every_sealed_path_with_one_alias_table (__main__.Round10Tests.test_f2_stage_resolves_every_sealed_path_with_one_alias_table) ... FAIL
test_f3_workers_are_direct_inside_namespace (__main__.Round10Tests.test_f3_workers_are_direct_inside_namespace) ... FAIL
test_f4_one_archive_read_hashes_extracted_bytes_and_refuses_bad_pin (__main__.Round10Tests.test_f4_one_archive_read_hashes_extracted_bytes_and_refuses_bad_pin) ... FAIL
test_f4_readme_has_no_asset_preread_and_generates_aliases (__main__.Round10Tests.test_f4_readme_has_no_asset_preread_and_generates_aliases) ... FAIL

======================================================================
FAIL: test_f1_public_script_is_pinned_and_tampering_refuses (__main__.Round10Tests.test_f1_public_script_is_pinned_and_tampering_refuses)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round10.py", line 80, in test_f1_public_script_is_pinned_and_tampering_refuses
    self.assertIn('u5.py',self.kit.kit_hashes(),'Missing executable preflight hash')
AssertionError: 'u5.py' not found in {'run.py': '2cb5917beef275402eceb92cc45efe4cc1625d6124b35196f02461057453bbf1', 'compare.py': '73858354fe8d366880873246e6256393ea2b27d5979af4e128e93c569a92f50e', 'sample50.json': '6a7885b6ea579d5e4a647ac408e79bec500e18cce574409b0a30c921a41e8707', 'host.py': 'afbcd84afd2ca8fe7278080f3d76d8f671b421a5f42df6278399730e1099155c'} : Missing executable preflight hash

======================================================================
FAIL: test_f1_real_boot_refuses_c_and_runs_actual_preflight_script (__main__.Round10Tests.test_f1_real_boot_refuses_c_and_runs_actual_preflight_script)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round10.py", line 48, in test_f1_real_boot_refuses_c_and_runs_actual_preflight_script
    self.assertTrue((OUT/'kit_parity50/u5.py').is_file(),'Preflight must be a shipped script')
AssertionError: False is not true : Preflight must be a shipped script

======================================================================
FAIL: test_f2_missing_nested_path_refuses_before_self_test (__main__.Round10Tests.test_f2_missing_nested_path_refuses_before_self_test)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round10.py", line 142, in test_f2_missing_nested_path_refuses_before_self_test
    self.assertTrue(hasattr(self.kit,'validate_existing_paths'),'Missing pre-self-test path admission')
AssertionError: False is not true : Missing pre-self-test path admission

======================================================================
FAIL: test_f2_stage_resolves_every_sealed_path_with_one_alias_table (__main__.Round10Tests.test_f2_stage_resolves_every_sealed_path_with_one_alias_table)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round10.py", line 111, in test_f2_stage_resolves_every_sealed_path_with_one_alias_table
    self.assertTrue(hasattr(self.host,'ALIASES'),'Missing shared prepared-path aliases')
AssertionError: False is not true : Missing shared prepared-path aliases

======================================================================
FAIL: test_f3_workers_are_direct_inside_namespace (__main__.Round10Tests.test_f3_workers_are_direct_inside_namespace)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round10.py", line 157, in test_f3_workers_are_direct_inside_namespace
    self.assertEqual(self.kit.worker_command(['u0.py','u2.json']),[inputs['python'],'-B','-I','u0.py','u2.json'])
AssertionError: Lists differ: ['/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/eb69[1339 chars]son'] != ['/scratch/jjyeung/b01ec87a6f29b/d/v/py', '-B', '-I', 'u0.py', 'u2.json']

First differing element 0:
'/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/eb69[30 chars]wrap'
'/scratch/jjyeung/b01ec87a6f29b/d/v/py'

First list contains 57 additional elements.
First extra element 5:
'usr/bin'

Diff is 1666 characters long. Set self.maxDiff to None to see it.

======================================================================
FAIL: test_f4_one_archive_read_hashes_extracted_bytes_and_refuses_bad_pin (__main__.Round10Tests.test_f4_one_archive_read_hashes_extracted_bytes_and_refuses_bad_pin)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round10.py", line 162, in test_f4_one_archive_read_hashes_extracted_bytes_and_refuses_bad_pin
    self.assertTrue(hasattr(self.host,'extract_assets'),'Missing one-pass extraction/hash')
AssertionError: False is not true : Missing one-pass extraction/hash

======================================================================
FAIL: test_f4_readme_has_no_asset_preread_and_generates_aliases (__main__.Round10Tests.test_f4_readme_has_no_asset_preread_and_generates_aliases)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round10.py", line 189, in test_f4_readme_has_no_asset_preread_and_generates_aliases
    self.assertNotIn("archive.open('rb')",block,'README rehashes the archive before staging')
AssertionError: "archive.open('rb')" unexpectedly found in "\nimport hashlib,json,sys,tarfile\nfrom pathlib import Path\np=Path(sys.argv[1]);archive=Path(sys.argv[2]);proof=json.loads((p/'a/c/CPU.json').read_text())\nassert proof['passed'] is True\nwith tarfile.open(p/'0.tgz') as t:cfg=json.load(t.extractfile('9.json'))\nasset=proof['gate_assets'];assert asset['logical']==cfg['logical']\nassert Path(asset['path']).resolve()==(p/'a/4.tar').resolve() and archive.stat().st_size==asset['bytes']\nh=hashlib.sha256()\nwith archive.open('rb') as stream:\n    for chunk in iter(lambda:stream.read(1024**2),b''):h.update(chunk)\nassert h.hexdigest()==asset['sha256']\nprint(cfg['logical'])" : README rehashes the archive before staging

----------------------------------------------------------------------
Ran 7 tests in 0.056s

FAILED (failures=7)
```

Command: `bash work/cpu.sh work/run_checks.py  # f16_behavior_before; exact environment/argv in runner`

Exact output ([checks/f16_behavior_before.txt](checks/f16_behavior_before.txt)):

```text
test_f4_worker_uses_settings_argv_without_environment_side_effect (__main__.Round3Tests.test_f4_worker_uses_settings_argv_without_environment_side_effect) ... FAIL

======================================================================
FAIL: test_f4_worker_uses_settings_argv_without_environment_side_effect (__main__.Round3Tests.test_f4_worker_uses_settings_argv_without_environment_side_effect)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round3.py", line 189, in test_f4_worker_uses_settings_argv_without_environment_side_effect
    self.assertNotIn('H10_SETTINGS',kit.os.environ)
AssertionError: 'H10_SETTINGS' unexpectedly found in {'CUDA_VISIBLE_DEVICES': 'fixture', 'H10_SETTINGS': '/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/572dfae5ed094fb5a1ae6797d90e270e/u0.json'}

----------------------------------------------------------------------
Ran 1 test in 0.724s

FAILED (failures=1)
```

Command: `bash work/cpu.sh work/run_checks.py`

Exact output ([checks/run_checks10.txt](checks/run_checks10.txt)):

```text
cache: OK
journal: OK
off: OK
public: OK
round1: OK
round2: OK
round3: OK
operator3: OK
lock3: OK
round4: CPU bound-export fixture: /scratch/jjyeung/orch_n30/so_read/work/test-artifacts/863e85df932841fdbf29df3113c5e263
round5: All CPU receipt checks passed
round6: Detached fill: success=0, failure=17, duplicate launch refused.
round7: Only reviewed step-400 export passes; changed artifact and selectable-export API refuse.
round8: Runtime torch/transformers/CUDA and environment SHA256 are exact; changed versions, bytes and CPU build refuse.
round9: Fresh token derives kit paths; framework version gap and carried guard limits are explicit.
round10: README generates PRIVATE_ALIASES from the host table and does not reread 4.tar before extraction.
kit: OK
kit_launch: OK
PASS: all 8 round-1 regressions fail against the round-1 reviewed implementation.
PASS: all 13 round-2 regressions fail against the round-2 reviewed implementation (14 failures including both CLI variants).
PASS: round3_before reproduces FAILED (failures=15).
PASS: operator3_before reproduces FAILED (failures=2).
PASS: lock3_before reproduces FAILED (failures=2).
PASS: round5_before reproduces FAILED (failures=11).
PASS: round6_before reproduces FAILED (failures=31).
PASS: round7_before reproduces FAILED (failures=10).
PASS: round10_before reproduces FAILED (failures=7).
PASS: round9_before reproduces FAILED (failures=11).
PASS: round8_before reproduces FAILED (failures=29).
PASS: round4_before reproduces FAILED (failures=7, skipped=1).
PASS: node4_before reproduces FAILED (failures=1).
PASS: f16_behavior_before reproduces FAILED (failures=1).
PASS: Python syntax, shell syntax, and default-off execution guards.
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/run_checks.py", line 106, in <module>
    assert report['workspace_bytes']<3_000_000_000
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError
```

Command: `bash work/cpu.sh work/run_fixture5.py work/build_patches.py`

Exact output ([checks/build_patches10.txt](checks/build_patches10.txt)):

```text
PASS: 3 additive reader diffs (42 files) plus 2 default-OFF A4 operator diffs; zero-fuzz application; unchanged original reader hash trees.
PASS: OFF, round-4/5/6/7/8/9/10 integration and comparator suites pass from the fresh applied A4 tree; both complete 927-file base inventories authenticate.
Applied verification root: /scratch/jjyeung/orch_n30/so_read/work/apply-round10/51ac61e502af4c98b8f65204e06cf2dd
```

Command: `bash work/cpu.sh work/finish_checks10.py`

Exact output ([checks/finish_checks10.txt](checks/finish_checks10.txt)):

```text
PASS: 147 tests in 18 workspace suites; all 14 fail-before controls reproduced; syntax and default-OFF checks passed.
PASS: workspace 2871926607 bytes < 3,000,000,000 after sharing identical completed fixtures; all paths/bytes retained.
LIMITATION: the driver exited 1 at its final storage assertion; its aggregate child RSS was not recorded.
```

Command: `bash work/cpu.sh work/gate_integration10.py`

Exact output ([checks/gate_integration10.txt](checks/gate_integration10.txt)):

```text
PASS: actual CPU fixture environment refuses before synthetic GPU receipt serialization.
All CPU receipt checks passed
{"passed": true, "pool_bytes": 0}
PASS: CPU helper produced the archive before CPU.json; its recorded hash/bytes and exact a/1.json match.
PASS: archive reconstructs READY-identical assets after the fixture private data path becomes unavailable.
PASS: public stage-kit bytes match MANIFEST-derived pins; changed driver, comparator, host helper, preflight and sealed sample each refuse.
PASS: exact CPU evidence feeds gate and full submit assertions; only reviewed step400 passes; synthetic environment evidence binds submit.
PASS: failed synthetic GPU receipt refuses; no GPU evidence was measured or submitted.
{"archive_bytes": 20480, "archive_sha256": "27e8ecf815e4f101bd03e9abdc5ce30b68648a9dad41eef7592aa7587e64c539", "assets": {"binding": "0a7c30028271d544e1bfdc2e51cf98ec39ba888c3b9d1d78b93269f43d34351d", "export_pin": "3ecf348301576174e3322b7105b6c3cab87606ef906226dab7cdb6073d651a5e", "restore": "44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a"}, "environment": {"cuda": "12.9", "sha256": "437dd3df35eac78affdb22dacee5045ea803d23f451d95fa4590fb321782af6d", "torch": "2.11.0+cpu", "transformers": "5.12.1"}, "kit": {"compare.py": "73858354fe8d366880873246e6256393ea2b27d5979af4e128e93c569a92f50e", "host.py": "d9bf99ecb646222b5f8767810937bf639a3b61bebd92455fcf0466d461af1712", "run.py": "e5640351a50e476f2b849a2af515b5ac12d8d759bfc376035c93d4b1075a31e4", "sample50.json": "1fdb65050f933d8578c849fbaa1010515ed07ad959234afd2d90cefdd946531b", "u5.py": "f44916b089adc4ce8a045aa752676ee404868292282fa0eb3ae3e02689d63501"}, "plan": "6913bbc74315d6b20305f99a793cadfd40cca772bc6f23f61f47b23ac74b4f6c", "required_device_type": "H100_80GB"}
```

Command: `bash work/cpu.sh work/docs_check10.py`

Exact output ([checks/docs10.txt](checks/docs10.txt)):

```text
PASS: 13 README shell blocks parse; archive-validation heredoc parses as Python 3.6; host paths and allocation documented.
PASS: cont_ops CPU assertion block remains verbatim; submit and operator helpers parse as Python 3.6.
PASS: installed device-property declarations and official 2.11 documentation recorded; no CUDA query executed.
PASS: step-400-only handoff, symlink archive, version preflight, retained stderr and 33 GB estimate documented.
PASS: namespace host bootstrap parses and runs --help under actual /usr/bin/python3 3.6.8; no runtime staging or GPU executed.
PASS: private gate, seal, stage-kit and archive transfer precede allocation; exact host extraction and namespaced wrapper commands are present.
PASS: exact receipt-handoff shell preserves failed ue.json outside private /tmp and still exits nonzero; only the GPU launch is replaced by false.
PASS: PRIVATE_ALIASES uses the staging table; pinned script preflight and one-pass archive extraction are documented.
PASS: exact README PYALIASES example executes and emits all seven mappings from the host table.
```

Command: `bash work/cpu.sh work/verify_archive_command8.py`

Exact output ([checks/archive_command10.txt](checks/archive_command10.txt)):

```text
PASS: link-validation/tar argv passes the real production opaque-command guard; namespace script parses as Python 3.6.
```

Command: `bash work/cpu.sh work/profile.py`

Exact output ([checks/profile_rerun.txt](checks/profile_rerun.txt)):

```text
package,type,items,seconds_mean,seconds_median,seconds_p90,tokens_mean,chosen_tokens_mean,calls_mean,g3t_seconds_mean,prefill_seconds_mean,factory_load_seconds,memo_hits,memo_misses
A4,object_abs_distance,150,23.599762386313476,18.275352681001095,29.181164655301444,354.52666666666664,239.52666666666667,1.76,1.9979346477866784,0.7367918526601474,75.44613318200209,45,43
A4,camera_displacement,150,9.553418849733328,7.640535711499979,15.356754048199218,164.05333333333334,124.05333333333333,1,2.00042000095343,0.5960202045065671,5.23999915458262e-07,117,33
A4,camera_rotation,150,5.088042348260205,5.008183966501747,5.266059609701188,89.93333333333334,79.02,1,0.10294739982023506,0.5878986225467573,5.270012479741126e-07,149,1
A4,camera_movement_direction,150,9.04453233268665,8.96309851549995,9.604166692998842,203.60666666666665,163.6,1,0.054859042846558924,0.6688661366800565,5.660003807861358e-07,150,0
A4,room_size_estimation,36,3.6673470785834876,3.641862107999259,3.8561768934996508,65.25,65.25,0,,0.570126933693953,1.5570003597531468e-06,0,0
B5,room_size_estimation,134,3.9415213698808493,3.523957444002008,4.505284694300644,66.66417910447761,66.66417910447761,0,,0.7769587752761131,78.96129892199679,0,0

A4 wall 7351.824172258377 outside timers 49.7613715433763
object_abs_distance timings {'g3t_s': 1.9979, 'prefill_s': 0.7368, 'total_s': 22.7406} families {'ground': 176, 'gap': 88} outer-core 0.8592 unattributed 0.5086 rooms 46 memo {'hits': 45, 'misses': 43, 'held_bytes': 71767526, 'requested': 'on', 'events': 0}
camera_displacement timings {'g3t_s': 2.0004, 'prefill_s': 0.596, 'total_s': 8.6717} families {'move': 150} outer-core 0.8817 unattributed 0.3302 rooms 36 memo {'hits': 117, 'misses': 33, 'held_bytes': 126883032, 'requested': 'on', 'events': 0}
camera_rotation timings {'g3t_s': 0.1029, 'prefill_s': 0.5879, 'total_s': 4.2036} families {'turn': 150} outer-core 0.8844 unattributed 0.3192 rooms 34 memo {'hits': 149, 'misses': 1, 'held_bytes': 128553354, 'requested': 'on', 'events': 0}
camera_movement_direction timings {'g3t_s': 0.0549, 'prefill_s': 0.6689, 'total_s': 8.1506} families {'move': 150} outer-core 0.894 unattributed 0.4929 rooms 36 memo {'hits': 150, 'misses': 0, 'held_bytes': 128553354, 'requested': 'on', 'events': 0}
room_size_estimation timings {'prefill_s': 0.5701, 'total_s': 2.7924} families {} outer-core 0.875 unattributed 0.0779 rooms 9 memo {'hits': 0, 'misses': 0, 'held_bytes': 128553354, 'requested': 'on', 'events': 0}
B5 wall 645.7347497940063 outside timers 33.016660970002704
room_size_estimation timings {'prefill_s': 0.777, 'total_s': 3.2551} families {} outer-core 0.6864 unattributed 5.5929 rooms 107 memo {'hits': 0, 'misses': 0, 'held_bytes': 0, 'requested': 'on', 'events': 0}
```

Command: `bash work/cpu.sh work/torch_versions3.py`

Exact output ([checks/torch_versions3.txt](checks/torch_versions3.txt)):

```text
{
  "events": [
    {
      "after": {
        "data_ptr": 118613056,
        "object_id": 140714125370192,
        "version": 1
      },
      "before": {
        "data_ptr": 118613056,
        "object_id": 140714125370192,
        "version": 0
      },
      "object_changed": false,
      "operation": "parameter.add_",
      "pointer_changed": false,
      "version_changed": true
    },
    {
      "after": {
        "data_ptr": 118623552,
        "object_id": 140714125370512,
        "version": 1
      },
      "before": {
        "data_ptr": 118623552,
        "object_id": 140714125370512,
        "version": 0
      },
      "object_changed": false,
      "operation": "detach().add_",
      "pointer_changed": false,
      "version_changed": true
    },
    {
      "after": {
        "data_ptr": 118624192,
        "object_id": 140714125370192,
        "version": 0
      },
      "before": {
        "data_ptr": 118624192,
        "object_id": 140714125370192,
        "version": 0
      },
      "object_changed": false,
      "operation": "parameter.data.add_",
      "pointer_changed": false,
      "version_changed": false
    },
    {
      "after": {
        "data_ptr": 118626816,
        "object_id": 140714125370512,
        "version": 0
      },
      "before": {
        "data_ptr": 118624576,
        "object_id": 140714125370512,
        "version": 0
      },
      "object_changed": false,
      "operation": "parameter.data assignment to cloned storage",
      "pointer_changed": true,
      "version_changed": false
    },
    {
      "after": {
        "data_ptr": 118627136,
        "object_id": 140714125370192,
        "version": 0
      },
      "before": {
        "data_ptr": 118627136,
        "object_id": 140714125370192,
        "version": 0
      },
      "object_changed": false,
      "operation": "parameter.data assignment to same storage",
      "pointer_changed": false,
      "version_changed": false
    },
    {
      "after": {
        "data_ptr": 118627328,
        "object_id": 140714125370512,
        "version": 0
      },
      "before": {
        "data_ptr": 118627328,
        "object_id": 140714125370512,
        "version": 0
      },
      "object_changed": false,
      "operation": "numpy raw storage write",
      "pointer_changed": false,
      "version_changed": false
    },
    {
      "after": {
        "data_ptr": 118627392,
        "object_id": 140714125370192,
        "version": 1
      },
      "before": {
        "data_ptr": 118627392,
        "object_id": 140714125370192,
        "version": 0
      },
      "object_changed": false,
      "operation": "SGD.step foreach=False",
      "pointer_changed": false,
      "version_changed": true
    },
    {
      "error": "Inference tensors do not track version counter.",
      "operation": "inference tensor _version"
    }
  ],
  "sources": {
    "/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/autograd/graph.py": "05470e880f0f293b31f59d4670eea1eeca14139bfc07ebfea8ee2ce3a5f4d8d7",
    "/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/include/c10/core/TensorImpl.h": "f0fc518750b2316da0e7baf8bf9de619d260948168552666028e1e300026d65f",
    "/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/include/torch/csrc/autograd/VariableTypeUtils.h": "3786bb26eb90dcee698387405efab2e8ed9cf4d23dd79e9c3b1a04f756379caa",
    "/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/optim/sgd.py": "8c97f1289923574f2a4ad7ff2fb758ea6e66e1be658d039a9a3bae10a1222a28"
  },
  "threads": 8,
  "torch": "2.11.0+cpu"
}
```

Command: `bash work/cpu.sh work/benchmark_round3.py`

Exact output ([checks/cache_cost3.txt](checks/cache_cost3.txt)):

```text
{
  "cases": [
    {
      "after_install_seconds": 0.34134596725925803,
      "after_per_call": {
        "max_seconds": 0.0279176221229136,
        "median_seconds": 0.026140545960515738,
        "min_seconds": 0.025956018827855587,
        "seconds": [
          0.02613494824618101,
          0.025956018827855587,
          0.02612791722640395,
          0.026140545960515738,
          0.02781710121780634,
          0.027858904097229242,
          0.0279176221229136
        ]
      },
      "before_install_seconds": 3.742612898349762e-05,
      "before_per_call": {
        "max_seconds": 0.45441452227532864,
        "median_seconds": 0.34706722013652325,
        "min_seconds": 0.33688052790239453,
        "seconds": [
          0.4315689289942384,
          0.35284700989723206,
          0.34706722013652325,
          0.33984962198883295,
          0.45441452227532864,
          0.33688052790239453,
          0.33892159909009933
        ]
      },
      "blocks": 128,
      "boundary": {
        "max_seconds": 0.34542193077504635,
        "median_seconds": 0.34177112486213446,
        "min_seconds": 0.33813909627497196,
        "seconds": [
          0.34542193077504635,
          0.33813909627497196,
          0.34177112486213446
        ]
      },
      "buffer_shape": [
        1024
      ],
      "buffer_tensors": 128,
      "dtype": "bfloat16",
      "median_speed_ratio": 13.276969067928214,
      "parameter_count": 268435456,
      "parameter_shape": [
        2048,
        1024
      ],
      "parameter_tensors": 128,
      "weight_and_buffer_bytes": 537133056
    },
    {
      "after_install_seconds": 0.6812121528200805,
      "after_per_call": {
        "max_seconds": 0.058478849940001965,
        "median_seconds": 0.05306965531781316,
        "min_seconds": 0.052297207061201334,
        "seconds": [
          0.05306965531781316,
          0.05288917385041714,
          0.053603915963321924,
          0.058478849940001965,
          0.057326571084558964,
          0.052297207061201334,
          0.052625448908656836
        ]
      },
      "before_install_seconds": 3.863777965307236e-05,
      "before_per_call": {
        "max_seconds": 0.8509081923402846,
        "median_seconds": 0.706850215792656,
        "min_seconds": 0.6787665546871722,
        "seconds": [
          0.8509081923402846,
          0.7424496323801577,
          0.6801157887093723,
          0.7036504759453237,
          0.706850215792656,
          0.6787665546871722,
          0.7180621158331633
        ]
      },
      "blocks": 256,
      "boundary": {
        "max_seconds": 0.7659496073611081,
        "median_seconds": 0.6957047251053154,
        "min_seconds": 0.6868291697464883,
        "seconds": [
          0.6957047251053154,
          0.6868291697464883,
          0.7659496073611081
        ]
      },
      "buffer_shape": [
        1024
      ],
      "buffer_tensors": 256,
      "dtype": "bfloat16",
      "median_speed_ratio": 13.31929162832526,
      "parameter_count": 536870912,
      "parameter_shape": [
        2048,
        1024
      ],
      "parameter_tensors": 256,
      "weight_and_buffer_bytes": 1074266112
    }
  ],
  "cuda_visible_devices": "",
  "kind": "measured CPU stub cache-hit overhead, not GPU speedup",
  "max_rss_bytes": 1326764032,
  "nice": 19,
  "threads": 8,
  "torch": "2.11.0+cpu"
}
```
