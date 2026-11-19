VERDICT: DONE All requested round-7 fixes pass CPU verification; production adoption still requires the selected-export H100 byte-parity gate.

**Measured validation:** 119 workspace tests and 38 fresh-application tests pass. The eight round-7 tests produce ten expected assertion failures on the reviewed implementation and pass on the delivered implementation. All eleven retained before-fix controls reran. Five diffs apply with zero fuzz. All original reader files and original/OFF output bytes remain unchanged; ON CPU fixtures retain exact answers and traces. GPU byte equality remains unmeasured and mandatory.

**Default export, read from supplied pins:** step **400**, read A/job **173060**, source package **a15_cot_apdc76460c3a164**, artifact SHA256 **5083243cfedd2a389dfca579c5452e7d0c73b03a58e1cb7d204292ddd10e67cd**. The gate's `--bound-export` parameter selects a different reviewed export.json. The default compares the complete supplied export identity, including artifact, head, full-weight and preparation pins. The builder accepts positive reviewed steps; the gate requires the selected identity. The synthetic step-600 fixture passes only with an explicit selection.

**Measured resources:** the suite's largest child-process RSS was 399,781,888 bytes; the separate guard benchmark peaked at 1,337,815,040 bytes. The workspace measured 2,855,759,441 unique-inode bytes at report generation, below 3,000,000,000. The suite recorded 2,975,305,259 bytes before completed-fixture sharing. [STORAGE7.json](checks/STORAGE7.json) records 163,241,740 identical bytes shared across 5,721 completed pre-task fixture paths; each replacement preserved bytes and path. No workspace-cap violation was observed.

**Estimates:** the supplied A4 timing supports **7,351.824 s for its 636-item schedule**, with zero credited cache saving. The separate **Package D** estimate is **13,813.069 s for 580 distance items**; a19 has **no ON route** for Package D. Neither estimate measures the selected export on a GPU.

Work started at **16:27:18 UTC on 2026-11-19**; the deadline is **17:42:18 UTC**. This report was generated at Thu Nov 19 16:49:51 UTC 2026. [out_round7](../out_round7/) preserves the entire reviewed delivery. CPU tests used torch 2.11.0+cpu, transformers 5.12.1, eight torch threads, CUDA hidden and `nice -n 10` (the benchmark observed effective nice 19). No Git, SSH, scheduler action, GPU execution, paid API, input-tree edit or deletion command ran. Network access read only official PyTorch documentation.

## Review round 7: finding -> fix -> test


| Finding | Fix | Regression |
|---|---|---|
| 1. Private root disappears | Archive inside CPU proof to `$P/a/4.tar` before CPU.json; record hash/bytes. | Real fixture tar runs through a namespace wrapper, survives loss of the root, and the CPU operator fixture executes staging. |
| 2. Fill wait hangs | Guard PACKAGE_TOKEN, check PID and cap wait at four hours. | Missing token, dead PID, timeout and failed exit refuse; success passes. |
| 3. PCIe accepted | Require exact HBM3 name and 132 SMs. | SXM stub passes; PCIe and wrong-SM stubs refuse. |
| 4. Evidence/host nits | Bind executing kit/comparator/sample; include a/1.json; unpack with -s -E -B; use an H100-local archive path. | Mutated pins refuse, environment-polluted unpack succeeds, allocation/evidence blocks are checked. |
| 5. Decision export | Default to the supplied step-400 export; require an explicit parameter for other exports. | Step 400 passes by default; synthetic step 600 passes only when selected; wrong artifact refuses. |

Frozen weights remain required. Persistent raw writes are boundary-checked; writes restored between boundaries remain outside the guard. GPU byte equality and performance remain unrun.


## Staging and adoption contract

The selected implementation archives assets **inside the existing CPU-proof job**. This uses its already-prepared files and READY receipt, so a separate staging job cannot diverge from the CPU proof. When `read_extensions is True`, `a/5.py` opens the named shared staging path **`$P/a/4.tar`** with exclusive creation outside bwrap and runs `tar -chf - -C logical/d .` through **`J.namespace(root)`**, streaming to that descriptor. Tar dereferences symlinks. The helper flushes/fsyncs the file, hashes it in 1 MiB chunks, and records its path, logical root, SHA256 and byte count in CPU.json. CPU.json is written only after tar succeeds. OFF does not call the helper or create an archive.

The archive lives in the package's shared staging area, outside the 75 MB return pool. Reserve capacity before the CPU job. A failed staging attempt leaves an incomplete archive and no successful CPU.json; a new attempt needs inspection and a fresh package token. The CPU job also copies exact a/1.json into the evidence directory. The gate verifies that file against CPU.json.inputs and verifies EXPORT_PIN.json against its export_pin.sha256 and bytes before GPU work.

**Measured fixture staging:** the real A4 CPU helper emitted a **20,480-byte fixture archive** before CPU.json. The integration check made the original fixture data path unavailable, extracted the archive, and recovered READY-identical assets. Its model/storage/namespace inputs are synthetic; 20,480 bytes is not a production-size estimate. No real large archive was created here.

On the H100 host, **`/scratch/jjyeung` must physically exist and be writable outside bwrap**. The package's exact logical root must be absent before extraction; currently it is `/scratch/jjyeung/b01ec87a6f29b`. A4's namespace-only `/scratch` creation cannot satisfy this host requirement. The [README](kit_parity50/README.md) supplies the owner-only `salloc ... srun` command for one GPU, eight CPUs, 200G, five hours, general/no-requeue, plus CPU-bound archive verification and extraction. Preserve the allocation's actual CUDA_VISIBLE_DEVICES. Device checks require exactly **NVIDIA H100 80GB HBM3**, **132 SMs**, capability **9.0**, and **79–86 billion bytes** of device memory. PCIe, wrong-SM, NVL, MIG and other device types refuse.

Follow the README for patch application, `u0/a19.py --enable-extensions --manifest ... --extension-pins ...`, matching EXPORT_BINDING/BOUND_EXPORT selection, generated operations, placement, detached fill, CPU proof, GPU gate, receipt handoff, submit and unpack. The delivered `operations/binding.default.json` derives its identity from the supplied export pin, its archive byte count from the four a/1.json part sizes, and its operation paths/base identity/frame layout from the reviewed bind400_partial.json. [DEFAULT_EXPORT_PROVENANCE.json](operations/DEFAULT_EXPORT_PROVENANCE.json) pins all four supplied files and the template. This is metadata verification, not a new restore of step-400 weights.

The fill wait requires PACKAGE_TOKEN, checks the PID from 0.txt on the launch host when 1.txt is absent, and has a **14,400-second maximum**. It polls at most once per minute and shortens its final sleep to the remaining deadline. A missing PID, exited worker without a receipt, timeout or nonzero exit receipt fails; it never retries a killed attempt.

The package embeds driver/comparator SHA256 values and the deterministically sealed sample SHA256 derived from MANIFEST kit_files. The driver, workers and receipt writer check their actual bytes. The token-only ue.json carries those hashes, and SUBMIT_CHECK compares them with the immutable package's MANIFEST-derived pins. The public-kit integration changes each staged file in turn and confirms refusal. It also confirms that a failed synthetic receipt cannot authorize submit. Receipt serialization in CPU tests is explicitly synthetic and does not certify a GPU run.

Submit retains cont_ops' CPU assertions verbatim, including batch/dispatch/guard pins and MEMORY.json equality. It also requires the cache allowance, both dry checks, an empty general queue, the bounded return pool, and a successful gate for the same plan/profile/assets/device/kit. The original loader still verifies all pinned checkpoint components before model loading. Every gate worker rechecks staged receipt bytes and the manifest hash.

A refused unpack leaves its extracted tree behind. Scorers require **success output after exit status 0**, and complete=false remains partial. The command uses **-s -E -B** from the operator directory: sibling imports work while PYTHONPATH/PYTHONHOME are ignored. GPU receipt transport uses an explicit H100-host archive path.

## Equality and mutation limits

The ordinary reader imports no extension and parses no new settings. The OFF fixture compares complete output files/stdout, including source hashes and controlled timing fields, against the original without exclusions. [OFF_BYTES.json](checks/OFF_BYTES.json) records the byte proof. The operator memory/return additions are guarded by read_extensions, whose default is OFF.

The 50-item CPU fixture compares original/OFF/processor+vision/processor-only answers and traces exactly with stub generation. Separate SAM fixtures check cached values, geometry recomputation and mutation rejection. Production adoption requires the unrun ORIGINAL/OFF/OFF_REPEAT/ON/journal/sharded GPU gates, useful hits in every enabled cache, and **zero answer/trace byte differences**. Only clocks and explicit telemetry are excluded; equal scores cannot hide changed answers. No batching implementation or numeric tolerance is delivered.

Calls check every parameter/buffer identity, pointer and version. Full hashes run at installation and type boundaries. Persistent .data/NumPy/raw-storage writes fail at boundaries; a raw write restored before the next boundary can evade detection. Private tensor attributes and arbitrary non-tensor module state are outside the guard's coverage. Models must remain frozen. A hard worker death can leave WEIGHTS.json false; graceful stops validate it. Processor-only runs install no weight guard.

ON eagerly constructs SAM outside inference mode; OFF constructs it lazily inside inference mode. This changes load timing and potentially RNG use. Only the GPU byte gate can clear the difference. Per-item timing omits installation and boundary costs; judge net performance using RUN.json worker_wall_seconds. The sample overstates reuse: its ten distance items share one clip, while A4 has 150 distance items over 60 clips (review finding 7). No production saving is credited.




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

**Estimate for what a19 builds:** the 636-item A4 schedule takes about **7,351.824 s (2 h 02 min 32 s; 11.559 s/item including fixed overhead)** if the supplied A4 throughput carries forward, with zero assumed cache saving. This does not measure the selected export. Target weights, cache guard/copy costs, actual reuse and staging can change it.

**Separate Package D estimate:** the 580-item distance read is a B5 fork with a 03:30 walltime and has **no ON route in a19**. Using 23.599762 s/item plus 75.446133 s loading and 49.761372 s overhead gives an estimate of **13,813.069 s (3 h 50 min)** on one card. Ideal two/four balanced-shard estimates are 6,969.138 / 3,547.173 s; they require an undelivered multi-card operator and exclude scene imbalance, staging, queues and preemption. The fixed 50-item reuse-heavy sample cannot establish these throughput estimates.




## Measured CPU guard overhead

Each stub uses bf16 parameters shaped 2048×1024 and a 1024-element buffer per module. Its forward returns a 32-element tensor without model-sized matrix work. Each implementation runs one miss and a warm hit, then seven timed hits; boundary cost is the median of three hashes. These measurements compare per-call full hashing with the delivered boundary/live-metadata guard on CPU. They do not measure GPU speedup. Exact samples are in [CACHE_COST3.json](checks/CACHE_COST3.json).

| Parameters | Parameter/buffer tensors | Weight+buffer bytes | Full hashing ms/call | Delivered guard ms/call | Install s | Boundary s |
|---:|---:|---:|---:|---:|---:|---:|
| 268435456 | 128/128 | 537133056 | 403.580 | 27.168 | 0.343 | 0.351 |
| 536870912 | 256/256 | 1074266112 | 796.500 | 55.204 | 0.742 | 0.778 |

## Framework evidence

[FRAMEWORK_EVIDENCE.md](FRAMEWORK_EVIDENCE.md) cites the installed torch/transformers source for every retained framework assumption. The device guard uses [torch/cuda/__init__.py:673](/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/cuda/__init__.py:673), which initializes CUDA, validates the index and returns native properties. [torch/_C/__init__.pyi:12448](/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/_C/__init__.pyi:12448) declares name, capability, SM count and memory; multi_processor_count appears at line 12452. The official [PyTorch 2.11 device-properties documentation](https://docs.pytorch.org/docs/2.11/generated/torch.cuda.get_device_properties.html) was reread on 2026-11-19. [SOURCE_EVIDENCE7.json](checks/SOURCE_EVIDENCE7.json) pins the installed files and cont_ops assertion source. [TORCH_VERSIONS3.json](checks/TORCH_VERSIONS3.json) contains the rerun mutation-counter probes. Device tests use stubs; no local CUDA query ran.

## Patches and authentication

The A4 base is `813fe4c57b2deed4bd731dd1e3493b6b0bed8d31e7bff92ff112cf5c9df823c3` over **927 files**. The reviewed A4 payload is `4498fca72a8e4b476b38f097ffdf3ff88b5aa20fc036bd196b18a5706e9fe46d` (5252958 bytes). B5 base archive: `ac2e259025d6a821aa5eb13e236f0635bd970313859086fc2f3ce3276647f2f0`. B5 checks establish patch applicability; the GPU kit authenticates A4.

| Patch | Bytes | SHA256 |
|---|---:|---|
| [01_bounded_read_caches.diff](patches/01_bounded_read_caches.diff) | 90430 | `369af9663fbc1008f9ecf5a32c5067ba4a5f4cd31412f07db8263b13b23fd4c3` |
| [02_atomic_scene_shards.diff](patches/02_atomic_scene_shards.diff) | 218841 | `5f76cf79e29471138161e476daf3920ec2bcbf751586fc47528fbd7388530cfa` |
| [03_production_integration.diff](patches/03_production_integration.diff) | 209517 | `1836061b44430b5a19a7b68a44a33e9a62b9f395c1a67fd96ca8a6d214c872b5` |
| [04_operator_cache_bound.diff](patches/04_operator_cache_bound.diff) | 2723 | `0d3bdc2d943554cd525627466d2d71f30881884e76df95204ede6c1accdb9061` |
| [05_operator_return_and_proof.diff](patches/05_operator_return_and_proof.diff) | 5843 | `79426b74d74493bc0cb6fa3d0fdb3f511f67b61a2ad2fec62b235e74dc5a598b` |

Reader patches add **37 files** under u0/, including regression tests; all original reader bytes remain unchanged. Operator patches remain behind read_extensions. Fresh applied OFF/round-4/5/6/7/comparator suites pass. MANIFEST pins the complete original inventories, additional copied A4 members, base batch/decoded bootstrap, patched operators, extensions, kit, default-export provenance and operation files. The 85 original files in the development source copy and all 927 originals in the fresh applied tree match their input hashes.

## What could go wrong and how we would notice

| Risk | Detection and response |
|---|---|
| Archive staging fails, storage fills or a namespace disappears too early | checked_run fails before CPU.json; preserve the failed attempt for inspection and use a fresh token. |
| H100 host lacks the logical directory's writable parent | Explicit host checks fail before extraction; provision the path before gate work. |
| Fill dies without an exit receipt or PID is reused | PID check catches the missing worker; the four-hour deadline bounds even a reused PID. |
| Wrong export or changed filled pin | Exact CPU input/READY checks and selected-export identity refuse before GPU execution; runtime component hashes check actual weights. |
| Stale or changed driver/comparator/sample | Runtime hashes and submit's package-bound expected hashes refuse. |
| Different H100 variant | Exact name, 132 SMs, capability and memory checks refuse before model loading. |
| Changed input/operator/batch or incomplete CPU proof | Builder pins and the full cont_ops submit assertion block refuse. |
| GPU kernels or eager SAM alter answer/trace bytes | Zero-difference gate fails; equal aggregate scores cannot waive it. |
| Cache cost erases savings or whole-process memory exceeds the cache cap | Compare full worker wall time and actual host/GPU peaks; the cache cap excludes model/caller working memory. |
| A raw write is restored between boundaries | Frozen ownership remains required; this sequence is outside the guard. |
| A refused/partial return is scored | Require unpack success output and inspect complete status. |

## Not done

No production GPU parity, throughput, peak-memory measurement, scheduler allocation, large pull/staging archive, real bwrap isolation/restore, transport, upload, submit, return publication or persistent-storage requeue ran. No numeric tolerance, batching or multi-card A4 operator is delivered. The array prototype remains approved=false. CPU suites need no local OS sockets. The H100 host path and production interpreter/storage capacity are owner-side preconditions, not verified here.

## Review round 6: finding -> fix -> test

The documented unpack subprocess runs; detached fill retains its lock/PID/log/exit status; submit embeds every cont_ops CPU assertion; copied A4 members, batch and bootstrap are pinned; CPU receipts bind checkpoint assets. The round-6 suite passes and its reviewed-snapshot control still produces 31 expected assertion failures. The round-7 gate uses the selected export parameter and exact SXM admission described above.

## Review round 5: finding -> fix -> test

The built batch equals cont_ops wrap_batch and passes the real bundle guard. Builder tests refuse changed payload/operators/extensions before output. Operation, profile, pool, forecast and unpack-success tests pass. The reviewed-snapshot control reproduces eleven expected failures.

## Review round 4: finding -> fix -> test

The A4 builder retains run keys, binding, fill admission and compatible helpers. The real CPU fixture executes preparation, rehearsal, bootstrap, job/action dispatch and all 636 stub reads in five verified ordinary journals. Return tests reject invalid weight receipts and retain OFF behavior. Its explicit alternate-export fixture uses step 600; this is not the default decision export. Both the reviewed route and original CPU-helper controls reproduce their expected failures.

### Review round 1: finding -> fix -> test

Typed keys, complete parity schemas, original/OFF provenance, frozen identity, lock-held recovery, opaque transport and bounded storage pass their regressions; all eight baseline regressions fail as expected.

### Review round 2: finding -> fix -> test

Isolated entry, path policy, bounded array attempts, pinned overlays, SAM capacity, deadline counts, lock waits, accounting, source-root checks and worker setup pass. The baseline reproduces thirteen assertions plus the expected CLI import error.

### Review round 3: finding -> fix -> test

Install/type-boundary hashes and cheap fatal live guards, processor-only mode, operator memory/overlay dispatch, full-base authentication, lock/worker behavior and OFF import checks pass. The generic operator test checks its nested atomic merge; the A4 adoption fixture checks the cache-only single-card profile. All baseline controls reproduce.

These named review sections are retained because the binding prompts explicitly request them. Test-output names containing step600 identify synthetic alternate-export fixtures, not an operational default.

## Commands and exact outputs

Commands ran from `/scratch/jjyeung/orch_n30/so_read`. `work/cpu.sh` exports CUDA_VISIBLE_DEVICES="", OMP/MKL/OPENBLAS threads=8, TOKENIZERS_PARALLELISM=false, PYTHONDONTWRITEBYTECODE=1 and scratch caches, then executes the approved Python with `nice -n 10 -I -s -B`. Child processes inherit those limits. The documented unpack command intentionally uses -s -E -B for its sibling import. Fixture storage shares immutable bytes and detaches shared files before edits.

Test commands additionally set READ_INPUT_SRC=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/A4/src and READ_TEST_TMP=/scratch/jjyeung/orch_n30/so_read/work/test-artifacts. Applied suites also set READ_OPERATOR_SOURCE and READ_OPERATOR4_SOURCE under `/scratch/jjyeung/orch_n30/so_read/work/apply-round7/29851255c3074802ac1047736a9d9e9a/operator`. All outputs below are literal; before-fix failures are expected controls. No cluster kill or automatic relaunch occurred.

```bash
bash work/cpu.sh work/run_checks.py
```

Exact output:

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
round4: CPU step-600 fixture: /scratch/jjyeung/orch_n30/so_read/work/test-artifacts/d78d62f3657442ceae64ee6ac71ae14d
round5: All CPU receipt checks passed
round6: Detached fill: success=0, failure=17, duplicate launch refused.
round7: Default step-400 artifact is pinned; explicit step-600 passes; default-on-600 and wrong artifact refuse.
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
PASS: round4_before reproduces FAILED (failures=7, skipped=1).
PASS: node4_before reproduces FAILED (failures=1).
PASS: f16_behavior_before reproduces FAILED (failures=1).
PASS: Python syntax, shell syntax, and default-off execution guards.
{"cuda_visible_devices": "", "max_child_rss_bytes": 399781888, "torch": "2.11.0+cpu", "torch_threads": 8, "transformers": "5.12.1", "workspace_bytes": 2975305259}
```

```bash
bash work/cpu.sh work/run_fixture5.py work/build_patches.py
```

Exact output:

```text
PASS: 3 additive reader diffs (37 files) plus 2 default-OFF A4 operator diffs; zero-fuzz application; unchanged original reader hash trees.
PASS: OFF, round-4/5/6/7 integration and comparator suites pass from the fresh applied A4 tree; both complete 927-file base inventories authenticate.
Applied verification root: /scratch/jjyeung/orch_n30/so_read/work/apply-round7/29851255c3074802ac1047736a9d9e9a
```

```bash
bash work/cpu.sh work/gate_integration7.py
```

Exact output:

```text
All CPU receipt checks passed
{"passed": true, "pool_bytes": 0}
PASS: CPU helper produced the archive before CPU.json; its recorded hash/bytes and exact a/1.json match.
PASS: archive reconstructs READY-identical assets after the fixture private data path becomes unavailable.
PASS: public stage-kit bytes match MANIFEST-derived pins; changed driver, comparator and sealed sample each refuse.
PASS: exact CPU evidence feeds gate and full submit assertions; default400 refuses synthetic600, explicit selection passes.
PASS: failed synthetic GPU receipt refuses; no GPU evidence was measured or submitted.
{"archive_bytes": 20480, "archive_sha256": "67b355dbc9370d3ce58b638ac2c15fd91359b4c9cff8610231b4ec7671e0bc8f", "assets": {"binding": "21397fddb5e9a40597ca7ae5824494d6656b68591f35f705287bfce770f8dd7a", "export_pin": "094d8d36773012097318172d96befb844805aae9e4a785e65a4f9454d2c7ec9e", "restore": "44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a"}, "kit": {"compare.py": "73858354fe8d366880873246e6256393ea2b27d5979af4e128e93c569a92f50e", "run.py": "c175e55c9090b33c219a5aef58b8b21b10b1238084abd59342eab7b7f5b5ad84", "sample50.json": "1fdb65050f933d8578c849fbaa1010515ed07ad959234afd2d90cefdd946531b"}, "plan": "f829c4521af353c4a848def6573dbef734f2dc2313ffe8a03b963597431684c5", "required_device_type": "H100_80GB"}
```

```bash
bash work/cpu.sh work/profile.py
```

Exact output:

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

```bash
bash work/cpu.sh work/torch_versions3.py
```

Exact output:

```text
{
  "events": [
    {
      "after": {
        "data_ptr": 113228928,
        "object_id": 140261195899728,
        "version": 1
      },
      "before": {
        "data_ptr": 113228928,
        "object_id": 140261195899728,
        "version": 0
      },
      "object_changed": false,
      "operation": "parameter.add_",
      "pointer_changed": false,
      "version_changed": true
    },
    {
      "after": {
        "data_ptr": 113239424,
        "object_id": 140261195900048,
        "version": 1
      },
      "before": {
        "data_ptr": 113239424,
        "object_id": 140261195900048,
        "version": 0
      },
      "object_changed": false,
      "operation": "detach().add_",
      "pointer_changed": false,
      "version_changed": true
    },
    {
      "after": {
        "data_ptr": 113240128,
        "object_id": 140261195899728,
        "version": 0
      },
      "before": {
        "data_ptr": 113240128,
        "object_id": 140261195899728,
        "version": 0
      },
      "object_changed": false,
      "operation": "parameter.data.add_",
      "pointer_changed": false,
      "version_changed": false
    },
    {
      "after": {
        "data_ptr": 113242752,
        "object_id": 140261195900048,
        "version": 0
      },
      "before": {
        "data_ptr": 113240640,
        "object_id": 140261195900048,
        "version": 0
      },
      "object_changed": false,
      "operation": "parameter.data assignment to cloned storage",
      "pointer_changed": true,
      "version_changed": false
    },
    {
      "after": {
        "data_ptr": 113243136,
        "object_id": 140261195899728,
        "version": 0
      },
      "before": {
        "data_ptr": 113243136,
        "object_id": 140261195899728,
        "version": 0
      },
      "object_changed": false,
      "operation": "parameter.data assignment to same storage",
      "pointer_changed": false,
      "version_changed": false
    },
    {
      "after": {
        "data_ptr": 113243264,
        "object_id": 140261195900048,
        "version": 0
      },
      "before": {
        "data_ptr": 113243264,
        "object_id": 140261195900048,
        "version": 0
      },
      "object_changed": false,
      "operation": "numpy raw storage write",
      "pointer_changed": false,
      "version_changed": false
    },
    {
      "after": {
        "data_ptr": 113243456,
        "object_id": 140261195899728,
        "version": 1
      },
      "before": {
        "data_ptr": 113243456,
        "object_id": 140261195899728,
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

```bash
bash work/cpu.sh work/benchmark_round3.py
```

Exact output:

```text
{
  "cases": [
    {
      "after_install_seconds": 0.342553183902055,
      "after_per_call": {
        "max_seconds": 0.02751278318464756,
        "median_seconds": 0.02716766484081745,
        "min_seconds": 0.02685382403433323,
        "seconds": [
          0.02685382403433323,
          0.026951179839670658,
          0.027089558076113462,
          0.02718622237443924,
          0.02729942323639989,
          0.02716766484081745,
          0.02751278318464756
        ]
      },
      "before_install_seconds": 4.2974017560482025e-05,
      "before_per_call": {
        "max_seconds": 0.5149778532795608,
        "median_seconds": 0.40357976080849767,
        "min_seconds": 0.3581583430059254,
        "seconds": [
          0.460304566193372,
          0.36115757236257195,
          0.38943942822515965,
          0.4926336333155632,
          0.40357976080849767,
          0.3581583430059254,
          0.5149778532795608
        ]
      },
      "blocks": 128,
      "boundary": {
        "max_seconds": 0.3531409460119903,
        "median_seconds": 0.35146467201411724,
        "min_seconds": 0.3442889880388975,
        "seconds": [
          0.35146467201411724,
          0.3442889880388975,
          0.3531409460119903
        ]
      },
      "buffer_shape": [
        1024
      ],
      "buffer_tensors": 128,
      "dtype": "bfloat16",
      "median_speed_ratio": 14.85515089990908,
      "parameter_count": 268435456,
      "parameter_shape": [
        2048,
        1024
      ],
      "parameter_tensors": 128,
      "weight_and_buffer_bytes": 537133056
    },
    {
      "after_install_seconds": 0.7423426792956889,
      "after_per_call": {
        "max_seconds": 0.05567771429196,
        "median_seconds": 0.05520420288667083,
        "min_seconds": 0.05339152365922928,
        "seconds": [
          0.055284484289586544,
          0.05520420288667083,
          0.05567771429196,
          0.05525902472436428,
          0.053932304959744215,
          0.05339152365922928,
          0.053717562928795815
        ]
      },
      "before_install_seconds": 3.7375837564468384e-05,
      "before_per_call": {
        "max_seconds": 1.1242351457476616,
        "median_seconds": 0.7965004621073604,
        "min_seconds": 0.6924755121581256,
        "seconds": [
          0.6924755121581256,
          0.7965004621073604,
          0.7191511681303382,
          1.1242351457476616,
          0.740694236010313,
          0.8977804249152541,
          0.8292495901696384
        ]
      },
      "blocks": 256,
      "boundary": {
        "max_seconds": 0.8296124143525958,
        "median_seconds": 0.7776896841824055,
        "min_seconds": 0.7716436041519046,
        "seconds": [
          0.8296124143525958,
          0.7776896841824055,
          0.7716436041519046
        ]
      },
      "buffer_shape": [
        1024
      ],
      "buffer_tensors": 256,
      "dtype": "bfloat16",
      "median_speed_ratio": 14.428257640863013,
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
  "max_rss_bytes": 1337815040,
  "nice": 19,
  "threads": 8,
  "torch": "2.11.0+cpu"
}
```

```bash
bash work/cpu.sh work/docs_check7.py
```

Exact output:

```text
PASS: 16 README shell blocks parse; archive-validation heredoc parses as Python 3.6; host paths and allocation documented.
PASS: cont_ops CPU assertion block remains verbatim; submit and operator helpers parse as Python 3.6.
PASS: installed device-property declarations and official 2.11 documentation recorded; no CUDA query executed.
```

```bash
bash work/cpu.sh work/share_storage7.py
```

Exact output:

```text
{"changed_files": 5721, "paths_preserved": true, "read_bytes": 208576544, "scope": "completed pre-task fixtures only; every replacement checked byte-for-byte", "unique_bytes_shared": 163241740, "workspace_bytes": 2812067270}
```

The patch-application subprocess output from build_patches.py is retained verbatim:

```text
patching file u0/a0.py
patching file u0/a1.py
patching file u0/a2.py
patching file u0/a3.py
patching file u0/tests/test_read_cache.py
patching file u0/tests/test_off.py
patching file u0/a4.py
patching file u0/a5.py
patching file u0/a6.py
patching file u0/a7.py
patching file u0/a8.py
patching file u0/a9.py
patching file u0/a10.py
patching file u0/a11.py
patching file u0/tests/test_read_journal.py
patching file u0/tests/test_public.py
patching file u0/tests/test_round1.py
patching file u0/tests/test_compare.py
patching file u0/tests/u0.json
patching file u0/tests/u1.json
patching file u0/a12.py
patching file u0/a13.py
patching file u0/a14.py
patching file u0/a15.py
patching file u0/a16.py
patching file u0/a17.py
patching file u0/a18.py
patching file u0/a19.py
patching file u0/a20.py
patching file u0/tests/test_round2.py
patching file u0/tests/test_round3.py
patching file u0/tests/test_operator_round3.py
patching file u0/tests/test_lock_round3.py
patching file u0/tests/test_round4.py
patching file u0/tests/test_round5.py
patching file u0/tests/test_round6.py
patching file u0/tests/test_round7.py
patching file u0/a0.py
patching file u0/a1.py
patching file u0/a2.py
patching file u0/a3.py
patching file u0/tests/test_read_cache.py
patching file u0/tests/test_off.py
patching file u0/a4.py
patching file u0/a5.py
patching file u0/a6.py
patching file u0/a7.py
patching file u0/a8.py
patching file u0/a9.py
patching file u0/a10.py
patching file u0/a11.py
patching file u0/tests/test_read_journal.py
patching file u0/tests/test_public.py
patching file u0/tests/test_round1.py
patching file u0/tests/test_compare.py
patching file u0/tests/u0.json
patching file u0/tests/u1.json
patching file u0/a12.py
patching file u0/a13.py
patching file u0/a14.py
patching file u0/a15.py
patching file u0/a16.py
patching file u0/a17.py
patching file u0/a18.py
patching file u0/a19.py
patching file u0/a20.py
patching file u0/tests/test_round2.py
patching file u0/tests/test_round3.py
patching file u0/tests/test_operator_round3.py
patching file u0/tests/test_lock_round3.py
patching file u0/tests/test_round4.py
patching file u0/tests/test_round5.py
patching file u0/tests/test_round6.py
patching file u0/tests/test_round7.py
patching file tower_sequence.py
patching file unpack_return.py
patching file package/a/5.py
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_read_cache.py
```

Exact output:

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
Ran 15 tests in 2.892s

OK
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_read_journal.py
```

Exact output:

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
Ran 13 tests in 0.142s

OK
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_off.py
```

Exact output:

```text
test_every_output_byte_and_source_hash_matches_original (__main__.OffContractTests.test_every_output_byte_and_source_hash_matches_original) ... ok

----------------------------------------------------------------------
Ran 1 test in 5.725s

OK
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_public.py
```

Exact output:

```text
test_legacy_worker_log_context_manager_never_writes_raw_library_output (__main__.PublicTests.test_legacy_worker_log_context_manager_never_writes_raw_library_output) ... ok
test_library_wire_decoder_preserves_ordinary_json_and_hash_serialization (__main__.PublicTests.test_library_wire_decoder_preserves_ordinary_json_and_hash_serialization) ... ok
test_no_raw_id_map_is_published_and_nested_ids_roundtrip (__main__.PublicTests.test_no_raw_id_map_is_published_and_nested_ids_roundtrip) ... ok
test_private_restoration_is_rejected_outside_trinity_before_writing (__main__.PublicTests.test_private_restoration_is_rejected_outside_trinity_before_writing) ... ok
test_public_array_descriptor_has_opaque_paths_and_numeric_types (__main__.PublicTests.test_public_array_descriptor_has_opaque_paths_and_numeric_types) ... ok
test_settings_tokens_hide_every_name_and_reject_descriptive_paths (__main__.PublicTests.test_settings_tokens_hide_every_name_and_reject_descriptive_paths) ... ok
test_unstructured_library_logs_and_partial_lines_only_publish_tokens (__main__.PublicTests.test_unstructured_library_logs_and_partial_lines_only_publish_tokens) ... ok

----------------------------------------------------------------------
Ran 7 tests in 0.004s

OK
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round1.py
```

Exact output:

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
Ran 17 tests in 4.400s

OK
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round2.py
```

Exact output:

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
Ran 13 tests in 3.872s

OK
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round3.py
```

Exact output:

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
Ran 9 tests in 1.923s

OK
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_operator_round3.py
```

Exact output:

```text
test_f2_a12_payload_through_a4_actions_and_nested_return (__main__.OperatorTests.test_f2_a12_payload_through_a4_actions_and_nested_return) ... ok
test_f2_operator_memory_bound_includes_cache_only_when_enabled (__main__.OperatorTests.test_f2_operator_memory_bound_includes_cache_only_when_enabled) ... ok

----------------------------------------------------------------------
Ran 2 tests in 10.134s

OK
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_lock_round3.py
```

Exact output:

```text
test_deadline_recovery_keeps_writer_lock (lock_behavior.RunnerTests.test_deadline_recovery_keeps_writer_lock) ... ok
test_type_deadline_recovery_holds_writer_lock (__main__.TypeLockTests.test_type_deadline_recovery_holds_writer_lock) ... ok

----------------------------------------------------------------------
Ran 2 tests in 0.021s

OK
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py
```

Exact output:

```text
test_f1_step600_package_preserves_a4_contract_and_binding (__main__.Round4Tests.test_f1_step600_package_preserves_a4_contract_and_binding) ... ok
test_f2_step600_real_job_and_rehearsal_memory (__main__.Round4Tests.test_f2_step600_real_job_and_rehearsal_memory) ... ok
test_f3_cache_only_return_refuses_unverified_journals (__main__.Round4Tests.test_f3_cache_only_return_refuses_unverified_journals) ... ok
test_f9_off_builder_guard_and_processor_only (__main__.Round4Tests.test_f9_off_builder_guard_and_processor_only) ... ok

----------------------------------------------------------------------
Ran 4 tests in 23.365s

OK
{"output": "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/d78d62f3657442ceae64ee6ac71ae14d/verified-return", "complete": false, "status": "FAILED", "sha256": "e7ef3d7b5e9017bea6fccbca98e9b7eb5347d4b4e301dff67d70ed8d93589daa"}
CPU step-600 fixture: /scratch/jjyeung/orch_n30/so_read/work/test-artifacts/d78d62f3657442ceae64ee6ac71ae14d
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round5.py
```

Exact output:

```text
test_f1_batch_wrapper_and_real_bundle_guard (__main__.Round5Tests.test_f1_batch_wrapper_and_real_bundle_guard) ... ok
test_f2_pins_refuse_before_copy (__main__.Round5Tests.test_f2_pins_refuse_before_copy) ... ok
test_f3_binding_derivation_and_operations (__main__.Round5Tests.test_f3_binding_derivation_and_operations) ... ok
test_f3_submit_pool_and_proof_refusals (__main__.Round5Tests.test_f3_submit_pool_and_proof_refusals) ... ok
test_f4_gate_pins_adopted_settings_and_profile (__main__.Round5Tests.test_f4_gate_pins_adopted_settings_and_profile) ... ok
test_f5_forecast_identifies_both_reads (__main__.Round5Tests.test_f5_forecast_identifies_both_reads) ... ok
test_f7_refused_unpack_not_scoreable (__main__.Round5Tests.test_f7_refused_unpack_not_scoreable) ... ok

----------------------------------------------------------------------
Ran 7 tests in 9.970s

OK
All CPU receipt checks passed
{"passed": true, "pool_bytes": 75000000}
All CPU receipt checks passed
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py
```

Exact output:

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
Ran 9 tests in 29.955s

OK
README unpack command: exit 0; authenticated partial return accepted.
Detached fill: success=0, failure=17, duplicate launch refused.
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round7.py
```

Exact output:

```text
test_f1_archive_runs_inside_live_namespace_and_survives_it (__main__.Round7Tests.test_f1_archive_runs_inside_live_namespace_and_survives_it) ... ok
test_f2_fill_wait_missing_token_dead_pid_timeout_and_success (__main__.Round7Tests.test_f2_fill_wait_missing_token_dead_pid_timeout_and_success) ... ok
test_f3_exact_sxm_name_and_132_sms (__main__.Round7Tests.test_f3_exact_sxm_name_and_132_sms) ... ok
test_info_export_bytes_bound_to_cpu_inputs_before_gpu (__main__.Round7Tests.test_info_export_bytes_bound_to_cpu_inputs_before_gpu) ... ok
test_info_host_paths_allocation_and_input_evidence (__main__.Round7Tests.test_info_host_paths_allocation_and_input_evidence) ... ok
test_info_receipt_records_and_submit_checks_kit_comparator_sample (__main__.Round7Tests.test_info_receipt_records_and_submit_checks_kit_comparator_sample) ... ok
test_info_unpack_ignores_python_environment_and_keeps_sibling_import (__main__.Round7Tests.test_info_unpack_ignores_python_environment_and_keeps_sibling_import) ... ok
test_rebind_default400_and_explicit600 (__main__.Round7Tests.test_rebind_default400_and_explicit600) ... ok

----------------------------------------------------------------------
Ran 8 tests in 8.578s

OK
Live namespace tar: regular file and dereferenced link preserved; archive survives namespace loss; duplicate and OFF guarded.
Fill wait: missing token, dead worker, deadline and exit 17 refuse; exit 0 passes; production maximum 14400 seconds.
Default step-400 artifact is pinned; explicit step-600 passes; default-on-600 and wrong artifact refuse.
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/out/kit_parity50/test_compare.py
```

Exact output:

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

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/out/kit_parity50/test_run.py
```

Exact output:

```text
test_durable_scene_comparison_requires_explicit_on_arm (__main__.LaunchTests.test_durable_scene_comparison_requires_explicit_on_arm) ... ok
test_original_and_off_do_not_opt_in_to_journaling_or_sharding (__main__.LaunchTests.test_original_and_off_do_not_opt_in_to_journaling_or_sharding) ... ok
test_stage_kit_uses_opaque_names_token_metadata_and_authenticated_sample_bytes (__main__.LaunchTests.test_stage_kit_uses_opaque_names_token_metadata_and_authenticated_sample_bytes) ... ok

----------------------------------------------------------------------
Ran 3 tests in 0.061s

OK
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/apply-round7/29851255c3074802ac1047736a9d9e9a/src/u0/tests/test_off.py
```

Exact output:

```text
test_every_output_byte_and_source_hash_matches_original (__main__.OffContractTests.test_every_output_byte_and_source_hash_matches_original) ... ok

----------------------------------------------------------------------
Ran 1 test in 4.956s

OK
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/apply-round7/29851255c3074802ac1047736a9d9e9a/src/u0/tests/test_round4.py
```

Exact output:

```text
test_f1_step600_package_preserves_a4_contract_and_binding (__main__.Round4Tests.test_f1_step600_package_preserves_a4_contract_and_binding) ... ok
test_f2_step600_real_job_and_rehearsal_memory (__main__.Round4Tests.test_f2_step600_real_job_and_rehearsal_memory) ... ok
test_f3_cache_only_return_refuses_unverified_journals (__main__.Round4Tests.test_f3_cache_only_return_refuses_unverified_journals) ... ok
test_f9_off_builder_guard_and_processor_only (__main__.Round4Tests.test_f9_off_builder_guard_and_processor_only) ... ok

----------------------------------------------------------------------
Ran 4 tests in 22.256s

OK
{"output": "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/7e42e6400b6a4b0c8821772699c9dfae/verified-return", "complete": false, "status": "FAILED", "sha256": "f42d58e86206a8eb8ef4653870f0dd4a8eb08c0c702f40ea56900b9368a70f6c"}
CPU step-600 fixture: /scratch/jjyeung/orch_n30/so_read/work/test-artifacts/7e42e6400b6a4b0c8821772699c9dfae
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/apply-round7/29851255c3074802ac1047736a9d9e9a/src/u0/tests/test_round5.py
```

Exact output:

```text
test_f1_batch_wrapper_and_real_bundle_guard (__main__.Round5Tests.test_f1_batch_wrapper_and_real_bundle_guard) ... ok
test_f2_pins_refuse_before_copy (__main__.Round5Tests.test_f2_pins_refuse_before_copy) ... ok
test_f3_binding_derivation_and_operations (__main__.Round5Tests.test_f3_binding_derivation_and_operations) ... ok
test_f3_submit_pool_and_proof_refusals (__main__.Round5Tests.test_f3_submit_pool_and_proof_refusals) ... ok
test_f4_gate_pins_adopted_settings_and_profile (__main__.Round5Tests.test_f4_gate_pins_adopted_settings_and_profile) ... ok
test_f5_forecast_identifies_both_reads (__main__.Round5Tests.test_f5_forecast_identifies_both_reads) ... ok
test_f7_refused_unpack_not_scoreable (__main__.Round5Tests.test_f7_refused_unpack_not_scoreable) ... ok

----------------------------------------------------------------------
Ran 7 tests in 10.121s

OK
All CPU receipt checks passed
{"passed": true, "pool_bytes": 75000000}
All CPU receipt checks passed
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/apply-round7/29851255c3074802ac1047736a9d9e9a/src/u0/tests/test_round6.py
```

Exact output:

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
Ran 9 tests in 29.944s

OK
README unpack command: exit 0; authenticated partial return accepted.
Detached fill: success=0, failure=17, duplicate launch refused.
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/apply-round7/29851255c3074802ac1047736a9d9e9a/src/u0/tests/test_round7.py
```

Exact output:

```text
test_f1_archive_runs_inside_live_namespace_and_survives_it (__main__.Round7Tests.test_f1_archive_runs_inside_live_namespace_and_survives_it) ... ok
test_f2_fill_wait_missing_token_dead_pid_timeout_and_success (__main__.Round7Tests.test_f2_fill_wait_missing_token_dead_pid_timeout_and_success) ... ok
test_f3_exact_sxm_name_and_132_sms (__main__.Round7Tests.test_f3_exact_sxm_name_and_132_sms) ... ok
test_info_export_bytes_bound_to_cpu_inputs_before_gpu (__main__.Round7Tests.test_info_export_bytes_bound_to_cpu_inputs_before_gpu) ... ok
test_info_host_paths_allocation_and_input_evidence (__main__.Round7Tests.test_info_host_paths_allocation_and_input_evidence) ... ok
test_info_receipt_records_and_submit_checks_kit_comparator_sample (__main__.Round7Tests.test_info_receipt_records_and_submit_checks_kit_comparator_sample) ... ok
test_info_unpack_ignores_python_environment_and_keeps_sibling_import (__main__.Round7Tests.test_info_unpack_ignores_python_environment_and_keeps_sibling_import) ... ok
test_rebind_default400_and_explicit600 (__main__.Round7Tests.test_rebind_default400_and_explicit600) ... ok

----------------------------------------------------------------------
Ran 8 tests in 8.637s

OK
Live namespace tar: regular file and dereferenced link preserved; archive survives namespace loss; duplicate and OFF guarded.
Fill wait: missing token, dead worker, deadline and exit 17 refuse; exit 0 passes; production maximum 14400 seconds.
Default step-400 artifact is pinned; explicit step-600 passes; default-on-600 and wrong artifact refuse.
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/apply-round7/29851255c3074802ac1047736a9d9e9a/src/u0/tests/test_compare.py
```

Exact output:

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
Ran 9 tests in 0.306s

OK
```

```bash
READ_REVIEW_BEFORE=1 bash work/cpu.sh work/run_fixture5.py work/src/u0/tests/test_round1.py
```

Exact output:

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
Ran 8 tests in 0.016s

FAILED (failures=8)
```

```bash
READ_ROUND2_BEFORE=1 bash work/cpu.sh work/run_fixture5.py work/src/u0/tests/test_round2.py
```

Exact output:

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
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/a429414872004e938ba4526cdc5d63e2/u0/a8.py", line 65, in <module>
    raise SystemExit(main())
                     ^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/a429414872004e938ba4526cdc5d63e2/u0/a8.py", line 61, in main
    return launch(rest)
           ^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/a429414872004e938ba4526cdc5d63e2/u0/a4.py", line 2, in main
    from a8 import source_hash
ModuleNotFoundError: No module named 'a8'


======================================================================
FAIL: test_f1_actual_isolated_script_plain_and_opaque (__main__.Round2Tests.test_f1_actual_isolated_script_plain_and_opaque) (opaque=True)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round2.py", line 67, in test_f1_actual_isolated_script_plain_and_opaque
    self.assertEqual(result.returncode,0,result.stdout+result.stderr)
AssertionError: 1 != 0 : Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/c41d2b737ba6459794fe46729c0dc801/u0/a8.py", line 65, in <module>
    raise SystemExit(main())
                     ^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/c41d2b737ba6459794fe46729c0dc801/u0/a8.py", line 56, in main
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
Ran 13 tests in 0.183s

FAILED (failures=13, errors=1)
```

```bash
READ_ROUND3_BEFORE=1 bash work/cpu.sh work/run_fixture5.py work/src/u0/tests/test_round3.py
```

Exact output:

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
AssertionError: 140371491997088 unexpectedly found in {140371491997088, 140371491997408} : Per-call weight hashing

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
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round3.py", line 195, in test_f7_off_import_guard_covers_all_overlay_modules
    with self.subTest(module=i),self.assertRaisesRegex(AssertionError,'OFF attempted'):
                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: AssertionError not raised

======================================================================
FAIL: test_f7_off_import_guard_covers_all_overlay_modules (__main__.Round3Tests.test_f7_off_import_guard_covers_all_overlay_modules) (module=12)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round3.py", line 195, in test_f7_off_import_guard_covers_all_overlay_modules
    with self.subTest(module=i),self.assertRaisesRegex(AssertionError,'OFF attempted'):
                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: AssertionError not raised

======================================================================
FAIL: test_f7_off_import_guard_covers_all_overlay_modules (__main__.Round3Tests.test_f7_off_import_guard_covers_all_overlay_modules) (module=13)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round3.py", line 195, in test_f7_off_import_guard_covers_all_overlay_modules
    with self.subTest(module=i),self.assertRaisesRegex(AssertionError,'OFF attempted'):
                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: AssertionError not raised

======================================================================
FAIL: test_f7_off_import_guard_covers_all_overlay_modules (__main__.Round3Tests.test_f7_off_import_guard_covers_all_overlay_modules) (module=14)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round3.py", line 195, in test_f7_off_import_guard_covers_all_overlay_modules
    with self.subTest(module=i),self.assertRaisesRegex(AssertionError,'OFF attempted'):
                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: AssertionError not raised

======================================================================
FAIL: test_f7_off_import_guard_covers_all_overlay_modules (__main__.Round3Tests.test_f7_off_import_guard_covers_all_overlay_modules) (module=15)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round3.py", line 195, in test_f7_off_import_guard_covers_all_overlay_modules
    with self.subTest(module=i),self.assertRaisesRegex(AssertionError,'OFF attempted'):
                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: AssertionError not raised

======================================================================
FAIL: test_f7_off_import_guard_covers_all_overlay_modules (__main__.Round3Tests.test_f7_off_import_guard_covers_all_overlay_modules) (module=16)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round3.py", line 195, in test_f7_off_import_guard_covers_all_overlay_modules
    with self.subTest(module=i),self.assertRaisesRegex(AssertionError,'OFF attempted'):
                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: AssertionError not raised

======================================================================
FAIL: test_f7_off_import_guard_covers_all_overlay_modules (__main__.Round3Tests.test_f7_off_import_guard_covers_all_overlay_modules) (module=17)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round3.py", line 195, in test_f7_off_import_guard_covers_all_overlay_modules
    with self.subTest(module=i),self.assertRaisesRegex(AssertionError,'OFF attempted'):
                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: AssertionError not raised

======================================================================
FAIL: test_f7_off_import_guard_covers_all_overlay_modules (__main__.Round3Tests.test_f7_off_import_guard_covers_all_overlay_modules) (module=18)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round3.py", line 195, in test_f7_off_import_guard_covers_all_overlay_modules
    with self.subTest(module=i),self.assertRaisesRegex(AssertionError,'OFF attempted'):
                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: AssertionError not raised

----------------------------------------------------------------------
Ran 9 tests in 0.791s

FAILED (failures=15)
```

```bash
READ_ROUND3_BEFORE=1 bash work/cpu.sh work/run_fixture5.py work/src/u0/tests/test_operator_round3.py
```

Exact output:

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
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/6481c7c6a76a4c55a0fc4331be71c481/0.py", line 44, in main
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
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/6481c7c6a76a4c55a0fc4331be71c481/0.py", line 18, in dispatch
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
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/6481c7c6a76a4c55a0fc4331be71c481/7.py", line 139, in main
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
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/6481c7c6a76a4c55a0fc4331be71c481/7.py", line 87, in run
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
Ran 2 tests in 9.352s

FAILED (failures=2)
```

```bash
READ_LOCK_BEFORE=1 bash work/cpu.sh work/run_fixture5.py work/src/u0/tests/test_lock_round3.py
```

Exact output:

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
Ran 2 tests in 0.014s

FAILED (failures=2)
```

```bash
READ_ROUND4_BEFORE=1 bash work/cpu.sh work/run_fixture5.py work/src/u0/tests/test_round4.py
```

Exact output:

```text
test_f1_step600_package_preserves_a4_contract_and_binding (__main__.Round4Tests.test_f1_step600_package_preserves_a4_contract_and_binding) ... FAIL
test_f2_step600_real_job_and_rehearsal_memory (__main__.Round4Tests.test_f2_step600_real_job_and_rehearsal_memory) ... FAIL
test_f3_cache_only_return_refuses_unverified_journals (__main__.Round4Tests.test_f3_cache_only_return_refuses_unverified_journals) ... 
  test_f3_cache_only_return_refuses_unverified_journals (__main__.Round4Tests.test_f3_cache_only_return_refuses_unverified_journals) (verified=False) ... FAIL
  test_f3_cache_only_return_refuses_unverified_journals (__main__.Round4Tests.test_f3_cache_only_return_refuses_unverified_journals) (verified=None) ... FAIL
  test_f3_cache_only_return_refuses_unverified_journals (__main__.Round4Tests.test_f3_cache_only_return_refuses_unverified_journals) (verified=0) ... FAIL
  test_f3_cache_only_return_refuses_unverified_journals (__main__.Round4Tests.test_f3_cache_only_return_refuses_unverified_journals) (verified=1) ... FAIL
  test_f3_cache_only_return_refuses_unverified_journals (__main__.Round4Tests.test_f3_cache_only_return_refuses_unverified_journals) (verified='true') ... FAIL
test_f9_off_builder_guard_and_processor_only (__main__.Round4Tests.test_f9_off_builder_guard_and_processor_only) ... skipped 'New route default and processor-only checks apply to delivered builder'

======================================================================
FAIL: test_f1_step600_package_preserves_a4_contract_and_binding (__main__.Round4Tests.test_f1_step600_package_preserves_a4_contract_and_binding)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 292, in test_f1_step600_package_preserves_a4_contract_and_binding
    self.assertEqual(cfg.get(key),old[key],key)
AssertionError: None != 'candidates_argmax' : stage1_select_rule

======================================================================
FAIL: test_f2_step600_real_job_and_rehearsal_memory (__main__.Round4Tests.test_f2_step600_real_job_and_rehearsal_memory)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 335, in test_f2_step600_real_job_and_rehearsal_memory
    self.assertEqual(result.returncode,0,str(root)+'\n'+result.stdout+result.stderr+logs+'\n'+'\n'.join(p.read_text() for p in (root/'job/sandbox/r').glob('FAILED.json')))
AssertionError: 1 != 0 : /scratch/jjyeung/orch_n30/so_read/work/test-artifacts/ca2a72dd5ba747b3b71ba47da8432941
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 428, in <module>
    elif len(sys.argv)>1 and sys.argv[1]=='--control':control_child(Path(sys.argv[2]),Path(sys.argv[3]),sys.argv[4])
                                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 276, in control_child
    node.main()
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/ca2a72dd5ba747b3b71ba47da8432941/built/package/a/5.py", line 147, in main
    raise ValueError('Prepared default settings differ')
ValueError: Prepared default settings differ
PASS action 0 rehearsal False



======================================================================
FAIL: test_f3_cache_only_return_refuses_unverified_journals (__main__.Round4Tests.test_f3_cache_only_return_refuses_unverified_journals) (verified=False)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 404, in test_f3_cache_only_return_refuses_unverified_journals
    with self.subTest(verified=value),self.assertRaisesRegex(ValueError,'Unverified weight journal'):validate()
                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f3_cache_only_return_refuses_unverified_journals (__main__.Round4Tests.test_f3_cache_only_return_refuses_unverified_journals) (verified=None)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 404, in test_f3_cache_only_return_refuses_unverified_journals
    with self.subTest(verified=value),self.assertRaisesRegex(ValueError,'Unverified weight journal'):validate()
                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f3_cache_only_return_refuses_unverified_journals (__main__.Round4Tests.test_f3_cache_only_return_refuses_unverified_journals) (verified=0)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 404, in test_f3_cache_only_return_refuses_unverified_journals
    with self.subTest(verified=value),self.assertRaisesRegex(ValueError,'Unverified weight journal'):validate()
                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f3_cache_only_return_refuses_unverified_journals (__main__.Round4Tests.test_f3_cache_only_return_refuses_unverified_journals) (verified=1)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 404, in test_f3_cache_only_return_refuses_unverified_journals
    with self.subTest(verified=value),self.assertRaisesRegex(ValueError,'Unverified weight journal'):validate()
                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f3_cache_only_return_refuses_unverified_journals (__main__.Round4Tests.test_f3_cache_only_return_refuses_unverified_journals) (verified='true')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 404, in test_f3_cache_only_return_refuses_unverified_journals
    with self.subTest(verified=value),self.assertRaisesRegex(ValueError,'Unverified weight journal'):validate()
                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 4 tests in 9.906s

FAILED (failures=7, skipped=1)
```

```bash
READ_ROUND5_BEFORE=1 bash work/cpu.sh work/run_fixture5.py work/src/u0/tests/test_round5.py
```

Exact output:

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
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round5.py", line 63, in test_f1_batch_wrapper_and_real_bundle_guard
    self.assertIn('#SBATCH --exclude=orchard-community-2\n',batch)
AssertionError: '#SBATCH --exclude=orchard-community-2\n' not found in "#!/bin/bash\nset -euo pipefail\nexec /usr/bin/python3 -I -s -B - <<'A'\nimport hashlib,io,json,os,sys,tarfile\nfrom pathlib import Path,PurePosixPath\nj=os.environ.get('SLURM_JOB_ID','')\nif not j.isdigit():raise ValueError('Allocation required')\nb=bytes.fromhex('1f8b08000000000002ffed5ae96fdb4616cf67fd15acfb81a43ca1a9c3922d9705d2c4dd66d11c8893020b412046e448624c915c0ee5a341fef77defcdf010253b5e14ed62510d125ae4ccbc79f3cedf1caef359a6c9b33fb5b85046ae4b7fddddbfee6038ae7eabefa3f178f0cc709ffd0565230b9ec390cffe9ee54bc7308e327e1fa73cf4e7f785904713e374303a3f1b8d59b34eae78ff74049547e3f3333e9f0783fe80bb61af1f04e7ee78713a10bdf3452f1c9f05a7433ee6e3f385180ccffabc370f5d310e43310c837e7f7e361e1d29ba314f1a44c5e9d9409cf5463df77c18f24178da1f9dbba7bdd13c14e1201c2c7a231ecc83fec00d8783053c46e3fe9043cbf3e162b180a7225aa4d72241727ceef6fa83e1e9687c767ed4f9da7976280ff8a693ddffe9633ceeffc3616fd4f6ffe1e9c1ffff92727474f43e1752e437c2c8f234dc04459426060fd79194f08b19209f65942c99c1e3380d3855cfd34d124af8948406f4dec405fc293679e200bd4eb4ced2bc30565caee268ce30c13010f2228a0593f7b2b3c8d3b591f1026b0dddf83dbc763a9d502c8c35bf167e18496811acac3c4d0b66a479044cf0187e6522e7459aebd8614f3a06d14bf360c5f3d05ff55c2748d76be0529386861d0309573479bebc615d784ad6ed5edfe20fa4637c6fbc4be27b980a04a74018c50afea7d9f358dc88b839fd9290c82f406822e3b9fa8ee2b84df36b914b14dbbd91454922420748470b2316098d6cffe8f5a929be4c9ff72733cf9bca22a7a99e98fce4147cd2b459f3538fd2b469cf904d23582c3d7c7730324b6ba795930b88d885b82b2cdbc60e5c82860bec37353969d884417b9ad6d40cd264112dcdd9d46c89179ab5be609fdd016ff3a8106a44622cdcac3369016d353ecc1e7aeb6e639ade776dc2343323e79114c66f3cde88cb3c4f73cbfc094c2d1661a57803f49c2ce1035f14224739e7c52633d53c41a2deb44b829d3cefcf1a321c3f2254e8aaccb7b2b3bd26d2295b95faaf0c364a2c342024eca1255b60e60e71d19bd917d9661e47c11e8db9fbf505f2c845a8089927e0959f45509ca0516f92a8b83ff9fcf95e6c92e5497abd1a9bf68965f2dea91fa485cf33f3580d363529159a3320a795afddd151d2b62c350a32512c7f2f792004004c382b7117464b218123cf2b696e630113e4761b152b43fbb6031a4ada646174ac47e52e40776b234aca77b48a242d8cb593f0b570489112095a66c3994f4c7b02e65944c9466c758a240e6ad9a033c3741c132993c8143ddbc990de64d7a03e25922f8411a4a1505693794a1d9979a2fa5e64d8592485b3be0ea3dc522fd2fb986f041377912cfcf49ade40b9daf695e4600e0ea831072723eed64aae4aad601318f59c284185586ec318c17eeddd405646b0cfe9fc6951aee5525edbe93a18e3d3c59629960ae327c1c9cbf79ff69ba496ba45ddd110c0a642736644d240315038a33a67290acb9c93cffacb0df2aa1bdb0f3506d1e6f7be14ffde8824108f34af0c1083d7c3365996663f009b5b9d6af0099368348c926c53486c8aa2ab4553868abdd47763e6bea0d9eaa6e6be16eb34bf37d997afb6961c979184c97b9e612ea23b11facb4181543221cdbda36b1233d51fc60d448611dec70a7f0d293d169ae2d404620f88689b8ce46be8cfe526176bd08f9f8376a2bc54cbcf3c96e209541651216b45da7b7cf1e74d1c1b607510d445700d8175b180e48972069b77e8238820df24de1e54d06ac2dad04011a1e88ced6d08d760c7be8f2eeefb9e67fa3e56fabe395121fc6fb84c18ffcff17f6f3c1c0d76f0ffd83de0ffbf08ffbf2b8155e95d94a98bdb141c378d792110e343aaa0640f49364d44030c37113f217d4873ac88d68269c0f108dcfff0e9d7cb2bcf32038820510823491f40d39adf99cceebc7cf7e9ed47a8ed9dbaacf97f008e7df5f297cb57d0d9b3208b0e6c064f979e3d7af6e93984c445f82c1432c8a30ca628219507d77c2908ad2930370da3a000bcb7f60033dd8adc64103385f4a666023335114342871e24a8186018049a5878fb3896fc46f8e96de287107f571ec5485607492aade8ec999053d80321dbd3d17aa7fe46e4d1e2de8f4268326b8f50dc67d875c04016accf8633c02b19f00d787204929b298948c10152fb845c2c540dbbc1a0fc84c51475213c405086c0100046ca010d5441954d08f19d4723ec49011fa0951185906500db3633c00e778a77b5e012965ab33c81e5771f5e5d7e60a0b13489021e770cc8b142a16b450332f8a680bc0f68f9428a02a0e6523621d256d3b20134dec548aa914a7e29a98cc7a6bd1783966a31ca7606610fb38481a22f7ca42f72a7650015e2d39c20c426c3283f74b65fadf2072bb3b882aec471590713db3173804608fac0e5c951f74c63935c2768f27bfa22e085194aafe97da510b517a2c04bcd7be48608ccbcaa5513a53105cdaa4af55a57a31fb4e16fa5de3640036bc8c17d7a8c029b478c320958023dcf2ba30b4ce17be39f57efdec2c20e006d01b33096d18d0089e3b2731e0b2306f3c7fd02dc42490ab50b80d1133745d642a11a09ebff6a960db36a2c94cb6a1b0db0e19a68a92700aa0a0eb1869fbc7e75f9f6e3eb8fff52609455bd3adaf0a4f7e56b87c68f18ce095527126004662f2c9a25ed73d03ab5459b24619ee0922442981bac529892f7a5dbadcc679f894c90ea7ee381f65b21d19cecc4c46ef7cbb5a2703d23beaf91e51d146b32f3e120b8a7b202bd5f411c14a8f40aaf9aad5e795fec0642356f94c0565dabff87cb17affc963ac880bbdd522b645b1e28428baf32ca3210597a28da22d10a9c463314b97a63655c9a940b459bd5f1873e22cb762951c84a60703e3654b54ac5f4b5d4accd0c50569af9b83c6db6aaa676f5f1dd7bb3a629613058caa96d2d73424b6013b2253030d50913344d2913bfe89c69521e820f147ca785d22ec5126530aa7e36abc7f9ef6cabee067359430e8e1273d23b735d66aabc5e7fecc3c76e773b246ad17fed5430402b40e5985cac04cf25eae8e12c034b8e44e46534c63d8a3c8d991214a202f9b4cc543b6f2bb35da89d5548f2a54f078b254a50b777c02ed792369e8cc2235a4e9484e2cea23d3d2de1a93bd3f685ecd1965c8736caa4d760d522e355843d68c3b0b75730a2e7b955bc2471f3027e2da224922b7f7eeff5c980f52e13129be243b3623e7f4ec6621ff76059ac0de6d1e6ca94747b32a7479bab69eae6cc743ea7b0926b0ae071e67042cfc91714097488fdd060c7456aba6dacb06f9cd26d71986de4b0dfc23d8f922e04843a18ffb1716a7e15b9e94e9845114224fb66c366f4853e8f677898c1e30468f7152ddde159269250d9a28e9e0acf36f5c9c8766967b6026b8acf6da84bd9fbf20e0646d42220081a4ac0b89e01111bc50ad2fa7245dbfc305a6c90711a320dae45a1763665b1991bb7225aae0acce2e4ceb8070bb8bf70d6d0b0f464b51dac1a109f65c515fc8dc55bbe16b0b60a1039abef0546851da857413b3208cc20b1f27d62b8026220b13534a7c840271be08b8595ce3fb35014304306d12b644b9182c5e6908868c9926ce2b85cac50cc30a0834375f8b8c037ece7e183dec2882f9354165180c0e202872c5504d5684fd4be35450b25e7e3685eccd7f3901b5d3ea1e93a854824c0c669cf617d87f55cd799915992ac49840e108609584a00ce15fe799740c6f17d9ca3ef03ea81bf36db6a8d7262e64754df3f061f4da63300ad1abcb71042747bcb6ca0ea523cce22c7fda000205ed1ea3ae82b41a9371c051d2af66b6bb6903a48fd260a7055986dbebd9c937c3df0c9d43ccdbecd94610240ad14b06fd5890fbbe2c75186aa38a049d67e8baa82c0afb44bfd76eb1465e56c779e52d0ef224fa5d567a76736c35d32cf045bb1e9a448a749e5a93a4b6e12edef0c6c42e508a6b222499d0531b0e8e16680838f27645178c3e58cb813c106d7994f5e8de2e11a31002bcd1e1e09e0ca853ec05cf7ae3a69290423f1a088efd5a68694d13281f080fd4cfb5b891997df170b1ec59b5c59994ed304615d46a6836b42148265ffe8818c9e234241ee9e9a63aa05f6640e9677dd51677f3558ac62a767694102712d3d1bd3a0d60aea0766b188ee542c55bf5572d4b37962f4ed76557b72dc68a17b4f4d2d0858336ae19715a031080f05d4902f9502dbe977a167a8966435e849489e20500cea4caf5f6ea145ae222356eb29103f531329605e52a9530f1f7ab022b3f29a1f3cbea8090045250b187c9f246a32d5af3add2455755deb79091dfa6cd60044f5eaf689bc200ff656326beff254c3f1386ed2d943a694b7feab57bcf484b0b35cd3c196965fb5e9f290755e7d7af3e6c58772c1a3e7569f8bea0ffa54948e027cba2a6075193855068dc09cacb321b39bd709d4d9990738bddb73fbc36e77c0887b1f700b640c6821f5769afaac9639aa938b06a14fa75a7d26bb8da9295ab2d5aea3530ab5db519416ecfee0b59bfde0f546259364893b81e57502d139525ba606f5d4925097264c82253fe3c98e01b94ae17208411383436886646b8c86460668864c92b6d506785b00104e6e2c73004c8e718978c4207e905886a005d6933c076a3778f7609e423e5d00502c3431450881ce0234a0eb802e1234947e11df4082f2acd1b07b7e3c1a1e0ffaf0af7bdaa37fc7a7bde3bedd3debe068be56a507ed8f9530fa1d0cdd18e47dd4eb2d302c3ca0a4455579f5964b950691304a944a4749b73142cbeea959166fa40f320325e3c994ea6525c703fb919e800fa1e9265c8a077b1cef4ce078d7481a21a9de582927821709aa1b02304f3acbf3768ff1be0911b67957677195805cf6d0e19c76121c49b3a4baf81b8867396aab4539bb2f56c0031acdaa3afdf79b1ad6da65b5bc4bca419a45c0cda0457247889aeb9def787ae72bb550837638d80a54db6374bbd617b3ad1b73c7ddbfaaf4b415130c011232be7cb55b24f1a4b20ca63bb662ce7ed861af1d67edce56d4cbf274dedca23e3a3a7a49279c6ab151f028d10180a2022160f043031777b0a2c108a4348c2f572fded029cb13d1d01fdbc2ae37841fda559b7d571aeafecb15606dc04df3c60eed5a579b721dbde5ad762b5bbbe62d7dd5a7c77483a4b5315e6bbcda85a9d5cff02e09bc4904013cf31a55d58eb88dc3e3929736a674fbbad621a08dc71b6436903e2ad6ab40d64c52b439b6937560704a9104d3b6b3625793fb66e2ad60e19bcb37efaa04ac915823016a4c85e7eefbb4f3be52a9d289b80b84082585c7324dd15d097b07f06fdf746add40dbb9f3b4655717993e6d596c6d0cd43762a61377a6aec06527e65cdfd2829f452e44f986c1156da5795ded0926b3ffd20dd0deb874e546d9143f2b0d086fc7ddf082d64bfaa72512dcebaf4e4dbee185305001d102434020a45497603afb3fef159c4ce31b61d9fa0a925d4ebb9cacde99546bf8a745842de36addf7ab6decc3e52f972f3e5cbdf8b5b2ae6a13b4d9a704fe7b34a19392af6f81d893ed68b845a5ba73576d89a4b2f2125a59369b337a03500e3f53e988e426cad3646abefcf4ea85ffdbebabd73ffd7ae9bfbafcedf5cbcb2be046667104fc3052b17283ab7b5988f5e51d7cefed5fb7281fb70f97440ee5500ee5500ee5500ee5500ee5500ee5500ee5500ee5500ee5500ee5500ee5500ee5500ee5500ee5500ee5ffaffc07c53c59f200500000')\nr=Path('/tmp')/('a'+j+'ab0123456789')\nr.mkdir(mode=0o700)\nwith tarfile.open(fileobj=io.BytesIO(b)) as a:\n    for e in a:\n        n=PurePosixPath(e.name)\n        if n.is_absolute() or '..' in n.parts or not e.isfile():raise ValueError('Unsafe input')\n        p=r/e.name;p.parent.mkdir(parents=True,exist_ok=True)\n        with a.extractfile(e) as i,p.open('xb') as o:o.write(i.read())\nos.chdir(r)\nos.execv(sys.executable,[sys.executable,'-I','-s','-B',str(r/'0.py'),str(r)])\nA\n"

======================================================================
FAIL: test_f2_pins_refuse_before_copy (__main__.Round5Tests.test_f2_pins_refuse_before_copy) (operator='tower_sequence.py')
----------------------------------------------------------------------
ReachedCopy: Unpinned input reached copy/build

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round5.py", line 102, in test_f2_pins_refuse_before_copy
    with self.assertRaisesRegex(ValueError,'operator pin'):attempt()
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: "operator pin" does not match "Unpinned input reached copy/build"

======================================================================
FAIL: test_f2_pins_refuse_before_copy (__main__.Round5Tests.test_f2_pins_refuse_before_copy) (operator='unpack_return.py')
----------------------------------------------------------------------
ReachedCopy: Unpinned input reached copy/build

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round5.py", line 102, in test_f2_pins_refuse_before_copy
    with self.assertRaisesRegex(ValueError,'operator pin'):attempt()
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: "operator pin" does not match "Unpinned input reached copy/build"

======================================================================
FAIL: test_f2_pins_refuse_before_copy (__main__.Round5Tests.test_f2_pins_refuse_before_copy) (operator='package/a/5.py')
----------------------------------------------------------------------
ReachedCopy: Unpinned input reached copy/build

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round5.py", line 102, in test_f2_pins_refuse_before_copy
    with self.assertRaisesRegex(ValueError,'operator pin'):attempt()
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: "operator pin" does not match "Unpinned input reached copy/build"

======================================================================
FAIL: test_f2_pins_refuse_before_copy (__main__.Round5Tests.test_f2_pins_refuse_before_copy) (base='self-consistent')
----------------------------------------------------------------------
ReachedCopy: Unpinned input reached copy/build

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round5.py", line 114, in test_f2_pins_refuse_before_copy
    with self.subTest(base='self-consistent'),self.assertRaisesRegex(ValueError,'reviewed A4 payload'):attempt()
                                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: "reviewed A4 payload" does not match "Unpinned input reached copy/build"

======================================================================
FAIL: test_f2_pins_refuse_before_copy (__main__.Round5Tests.test_f2_pins_refuse_before_copy) (extension='changed')
----------------------------------------------------------------------
ReachedCopy: Unpinned input reached copy/build

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round5.py", line 122, in test_f2_pins_refuse_before_copy
    with self.subTest(extension='changed'),self.assertRaisesRegex(ValueError,'Extension inventory'):attempt(source=source)
                                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: "Extension inventory" does not match "Unpinned input reached copy/build"

======================================================================
FAIL: test_f3_binding_derivation_and_operations (__main__.Round5Tests.test_f3_binding_derivation_and_operations)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round5.py", line 135, in test_f3_binding_derivation_and_operations
    helper=self.helpers();root=fresh();binding=copy.deepcopy(self.binding)
           ^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round5.py", line 58, in helpers
    self.assertTrue((E/'a20.py').is_file(),'Missing executable binding/operation/gate helper')
AssertionError: False is not true : Missing executable binding/operation/gate helper

======================================================================
FAIL: test_f3_submit_pool_and_proof_refusals (__main__.Round5Tests.test_f3_submit_pool_and_proof_refusals)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round5.py", line 166, in test_f3_submit_pool_and_proof_refusals
    helper=self.helpers();root=fresh();package=root/'package';(package/'a/c').mkdir(parents=True)
           ^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round5.py", line 58, in helpers
    self.assertTrue((E/'a20.py').is_file(),'Missing executable binding/operation/gate helper')
AssertionError: False is not true : Missing executable binding/operation/gate helper

======================================================================
FAIL: test_f4_gate_pins_adopted_settings_and_profile (__main__.Round5Tests.test_f4_gate_pins_adopted_settings_and_profile)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round5.py", line 196, in test_f4_gate_pins_adopted_settings_and_profile
    self.assertTrue(hasattr(kit,'validate_profile'),'GPU gate accepts an unbound read profile')
AssertionError: False is not true : GPU gate accepts an unbound read profile

======================================================================
FAIL: test_f5_forecast_identifies_both_reads (__main__.Round5Tests.test_f5_forecast_identifies_both_reads)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round5.py", line 224, in test_f5_forecast_identifies_both_reads
    self.assertIn('Package D',text);self.assertIn('636-item',text)
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'Package D' not found in 'VERDICT: DONE The round-4 fixes pass CPU verification; adopt only after the GPU byte gate.\n\nMeasured: **95 workspace tests and 14 fresh-application tests pass**. Five patches apply exactly; original reader files and complete OFF output bytes remain unchanged. The backup is out_round4/. The CPU fixture completes 636 synthetic reads with five verified ordinary journals through real A4 preparation, rehearsal, bootstrap and job.main.\n\nMeasured existing distance time is **23.60 s/item**. Estimated 580-item elapsed time, crediting no cache saving, is **3 h 50 min** on one card. Ideal two/four-shard estimates are **1 h 56 min / 59 min**, excluding staging, queues, preemption and scene imbalance; they require an undelivered multi-card operator. Measured CPU guard/cache overhead on a 268M-parameter bf16 stub is **25.9 ms/call**. This is not a GPU saving.\n\n## Review round 4: finding -> fix -> test\n\n| Finding | Fix and test |\n|---|---|\n| 1. Incomplete step-600 package | a19 uses A4 build_r1-style post-processing, preserving 8.py, run keys and admission. It requires the reviewed target export/whole-archive binding and seals the fill helper. Wrong binding/receipt checks fail; the documented old build fails before. |\n| 2. Adoption profile not exercised | Real job.main constructs actions 0/1 from packaged 9.json. Real 7.py rehearsal produces MEMORY.json with 12 GiB cache allowance. Stub workers produce five verified ordinary journals. The old CPU-proof helper fails the allowance test. |\n| 3. Unchecked cache-only return | ON unpack rejects non-true WEIGHTS receipts. Invalid-value regressions fail before/pass after; real authenticated partial-return unpack rejects an unchecked journal. |\n| 9. README nits | Commands use explicit delivery/source roots; kit pin is A4-only; README states what bootstrap admission actually checks. |\n\n**Step 600: one card, caches only, general/no-requeue.** Apply 01–03 to a full A4/src copy and 04–05 to an A4 operator copy. Define the local roots using [README](kit_parity50/README.md), then build:\n\n```bash\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a19.py" \\\n  --enable-extensions --base-operator "$LOCAL/a4" --source-root "$EXT_SOURCE" \\\n  --export-binding "$STEP600_BINDING" --token "$PACKAGE_TOKEN" --out "$LOCAL/step600"\n```\n\nThe required binding includes target run/step/object/preparation identities and archive_bytes/archive_sha256. The CPU task has no real step-600 export; its test binding is synthetic. The generic a12 operator build is refused. Add --processor-only for the 4 GiB processor cache; otherwise the cache allowance is 12 GiB. Both disable atomic journals and sharding. A4\'s fixed schedule remains 636 items; changing it requires a separately reviewed operator/proof.\n\nUse the generated fill helper, regenerate CPU proof through package/a/5.py, and retain the generated tower_sequence.py beside unpack_return.py. Exact fill/proof commands are in README. Require read_cache_bytes in MEMORY/CPU.json, along with payload/plan/inputs/operator binding and fits=true. The unchanged 0.py admission does not independently require that field. Cache-only returns retain ordinary journals; ON unpack refuses unchecked weights even on partial returns.\n\nBefore adoption, require **zero answer/trace byte differences**, useful cache hits, net worker_wall_seconds savings, and full-process host/GPU/envelope headroom. ON\'s eager SAM construction and boundary hashing need the GPU gate. The sample overstates reuse. Keep models frozen; persistent raw writes fail at boundaries, while restored-between-boundary writes are unsupported. Hard kills can require fresh journals. Validate persistent-storage requeue before any preempt/sharded use. Stage source trees as archives and run the kit with --public. No launch ran; preserve step-400 deliveries.\n\nExact commands, outputs, citations and limits: [REPORT](REPORT.md). Patch/base pins: [MANIFEST](patches/MANIFEST.json).\n'

======================================================================
FAIL: test_f7_refused_unpack_not_scoreable (__main__.Round5Tests.test_f7_refused_unpack_not_scoreable)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round5.py", line 231, in test_f7_refused_unpack_not_scoreable
    self.assertIn('refused unpack leaves',text.lower())
AssertionError: 'refused unpack leaves' not found in 'verdict: done the round-4 fixes pass cpu verification; adopt only after the gpu byte gate.\n\nmeasured: **95 workspace tests and 14 fresh-application tests pass**. five patches apply exactly; original reader files and complete off output bytes remain unchanged. the backup is out_round4/. the cpu fixture completes 636 synthetic reads with five verified ordinary journals through real a4 preparation, rehearsal, bootstrap and job.main.\n\nmeasured existing distance time is **23.60 s/item**. estimated 580-item elapsed time, crediting no cache saving, is **3 h 50 min** on one card. ideal two/four-shard estimates are **1 h 56 min / 59 min**, excluding staging, queues, preemption and scene imbalance; they require an undelivered multi-card operator. measured cpu guard/cache overhead on a 268m-parameter bf16 stub is **25.9 ms/call**. this is not a gpu saving.\n\n## review round 4: finding -> fix -> test\n\n| finding | fix and test |\n|---|---|\n| 1. incomplete step-600 package | a19 uses a4 build_r1-style post-processing, preserving 8.py, run keys and admission. it requires the reviewed target export/whole-archive binding and seals the fill helper. wrong binding/receipt checks fail; the documented old build fails before. |\n| 2. adoption profile not exercised | real job.main constructs actions 0/1 from packaged 9.json. real 7.py rehearsal produces memory.json with 12 gib cache allowance. stub workers produce five verified ordinary journals. the old cpu-proof helper fails the allowance test. |\n| 3. unchecked cache-only return | on unpack rejects non-true weights receipts. invalid-value regressions fail before/pass after; real authenticated partial-return unpack rejects an unchecked journal. |\n| 9. readme nits | commands use explicit delivery/source roots; kit pin is a4-only; readme states what bootstrap admission actually checks. |\n\n**step 600: one card, caches only, general/no-requeue.** apply 01–03 to a full a4/src copy and 04–05 to an a4 operator copy. define the local roots using [readme](kit_parity50/readme.md), then build:\n\n```bash\ncuda_visible_devices= nice -n 10 "$read_python" -i -s -b "$ext_source/u0/a19.py" \\\n  --enable-extensions --base-operator "$local/a4" --source-root "$ext_source" \\\n  --export-binding "$step600_binding" --token "$package_token" --out "$local/step600"\n```\n\nthe required binding includes target run/step/object/preparation identities and archive_bytes/archive_sha256. the cpu task has no real step-600 export; its test binding is synthetic. the generic a12 operator build is refused. add --processor-only for the 4 gib processor cache; otherwise the cache allowance is 12 gib. both disable atomic journals and sharding. a4\'s fixed schedule remains 636 items; changing it requires a separately reviewed operator/proof.\n\nuse the generated fill helper, regenerate cpu proof through package/a/5.py, and retain the generated tower_sequence.py beside unpack_return.py. exact fill/proof commands are in readme. require read_cache_bytes in memory/cpu.json, along with payload/plan/inputs/operator binding and fits=true. the unchanged 0.py admission does not independently require that field. cache-only returns retain ordinary journals; on unpack refuses unchecked weights even on partial returns.\n\nbefore adoption, require **zero answer/trace byte differences**, useful cache hits, net worker_wall_seconds savings, and full-process host/gpu/envelope headroom. on\'s eager sam construction and boundary hashing need the gpu gate. the sample overstates reuse. keep models frozen; persistent raw writes fail at boundaries, while restored-between-boundary writes are unsupported. hard kills can require fresh journals. validate persistent-storage requeue before any preempt/sharded use. stage source trees as archives and run the kit with --public. no launch ran; preserve step-400 deliveries.\n\nexact commands, outputs, citations and limits: [report](report.md). patch/base pins: [manifest](patches/manifest.json).\n'

----------------------------------------------------------------------
Ran 7 tests in 4.994s

FAILED (failures=11)
```

```bash
READ_ROUND6_BEFORE=1 bash work/cpu.sh work/run_fixture5.py work/src/u0/tests/test_round6.py
```

Exact output:

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
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 116, in test_f1_readme_unpack_subprocess
    self.assertEqual(result.returncode,0,result.stderr)
AssertionError: 1 != 0 : Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/f92badda14ac4809b4b1942584bf22e7/step600/unpack_return.py", line 3, in <module>
    from fetch_return import digest as file_digest, validate_exit
ModuleNotFoundError: No module named 'fetch_return'


======================================================================
FAIL: test_f2_detached_locked_fill_exit_success_and_failure (__main__.Round6Tests.test_f2_detached_locked_fill_exit_success_and_failure)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 128, in test_f2_detached_locked_fill_exit_success_and_failure
    self.assertIn('nohup bash',text,'Pull/fill still runs in the foreground')
AssertionError: 'nohup bash' not found in '#!/bin/bash\nset -euo pipefail\numask 077\nD=$(cd -- "$(dirname -- "$0")" && pwd)\nP=/project/community/jjyeung/okh7/a15_cot_apab0123456789\nexport TZ=UTC CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud CLOUDSDK_CORE_DISABLE_PROMPTS=1\nE=$P/a/e\ntest ! -e "$E"\nmkdir -m 700 "$E"\nOBJECT=q8/8865619b/673bc60f_m600.tar\ncp /project/community/jjyeung/okh7/abcdef/5 "$E/5"\ntest "$(cat "$E/5")" = \'q8/8865619b/673bc60f_m600.tar 4 2222222222222222222222222222222222222222222222222222222222222222\'\ncp /project/community/jjyeung/okh7/abcdef/7 "$E/7"\ntest "$(sha256sum "$E/7" | cut -d\' \' -f1)" = 3b0051c4a9cc661d02019a645165fc3e23d658d2f24a6fd6fd86ec7877ba4fc1\ncp /project/community/jjyeung/okh7/abcdef/8 "$E/8"\ntest "$(sha256sum "$E/8" | cut -d\' \' -f1)" = 4c0dd9d6e4535a2945ed58754c1cdd5e9a316067be35f2e8440caa9a80e1c915\ncp /project/community/jjyeung/okh7/abcdef/9 "$E/9"\ntest "$(sha256sum "$E/9" | cut -d\' \' -f1)" = 7f654d2f0ae9f06083f2fc8fd793512c154b4d01ce8632fb733d4191205af770\nfor i in 0 1 2 3; do\n  test ! -e "$E/$i"\n  gsutil -o Boto:num_retries=0 -o Boto:metadata_service_num_attempts=1 -o GSUtil:parallel_process_count=1 -o GSUtil:parallel_thread_count=1 -o GSUtil:sliced_object_download_threshold=0 -o GSUtil:sliced_object_download_max_components=1 -q cp "gs://cmu-gpucloud-jjyeung/$OBJECT.part0$i-of-04" "$E/$i.partial"\n  mv "$E/$i.partial" "$E/$i"\ndone\n/usr/bin/python3 -I -s -B "$P/a/4.py" --parts "$E/0" "$E/1" "$E/2" "$E/3" --done "$E/5" --object "$OBJECT" --config "$E/7" --receipt "$E/8" --data-receipt "$E/9" --lineage SFT --step 600 --out "$P/a/export.json" --prep-tar "$P/a/6" --base-inputs "$P/a/0.json" --inputs-out "$P/a/1.json"\nPREP=$(sha256sum "$P/a/6" | cut -d\' \' -f1)\n/usr/bin/python3 -I -s -B "$D/d.py" "$P/a/1.json" "$P/a/0.json" "$PREP" > "$P/a/dry.json"\n(cd "$P" && CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 04:30:00)\n/usr/bin/python3 -I -s -B "$D/d2.py" "$P" "$P/a/w2" > "$P/a/dry2.json"\nprintf \'%s\\n\' 0 > "$P/a/1.txt"\n' : Pull/fill still runs in the foreground

======================================================================
FAIL: test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks) (field='bundle_guard.batch_sha256')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 168, in test_f3_full_cont_ops_receipt_checks
    self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'Unbound CPU receipt field: '+key)
AssertionError: 0 == 0 : Unbound CPU receipt field: batch_sha256

======================================================================
FAIL: test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks) (field='bundle_guard.path')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 168, in test_f3_full_cont_ops_receipt_checks
    self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'Unbound CPU receipt field: '+key)
AssertionError: 0 == 0 : Unbound CPU receipt field: path

======================================================================
FAIL: test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks) (field='entry_sequence.events')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 168, in test_f3_full_cont_ops_receipt_checks
    self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'Unbound CPU receipt field: '+key)
AssertionError: 0 == 0 : Unbound CPU receipt field: events

======================================================================
FAIL: test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks) (field='entry_sequence.guard_target_sha256')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 168, in test_f3_full_cont_ops_receipt_checks
    self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'Unbound CPU receipt field: '+key)
AssertionError: 0 == 0 : Unbound CPU receipt field: guard_target_sha256

======================================================================
FAIL: test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks) (field='entry_sequence.requested_argv')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 168, in test_f3_full_cont_ops_receipt_checks
    self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'Unbound CPU receipt field: '+key)
AssertionError: 0 == 0 : Unbound CPU receipt field: requested_argv

======================================================================
FAIL: test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks) (field='entry_sequence.dispatched_argv')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 168, in test_f3_full_cont_ops_receipt_checks
    self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'Unbound CPU receipt field: '+key)
AssertionError: 0 == 0 : Unbound CPU receipt field: dispatched_argv

======================================================================
FAIL: test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks) (field='entry_sequence.batch_sha256')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 168, in test_f3_full_cont_ops_receipt_checks
    self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'Unbound CPU receipt field: '+key)
AssertionError: 0 == 0 : Unbound CPU receipt field: batch_sha256

======================================================================
FAIL: test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks) (field='memory.perception_memo_modules')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 168, in test_f3_full_cont_ops_receipt_checks
    self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'Unbound CPU receipt field: '+key)
AssertionError: 0 == 0 : Unbound CPU receipt field: perception_memo_modules

======================================================================
FAIL: test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks) (field='memory.sam_measurement_required')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 168, in test_f3_full_cont_ops_receipt_checks
    self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'Unbound CPU receipt field: '+key)
AssertionError: 0 == 0 : Unbound CPU receipt field: sam_measurement_required

======================================================================
FAIL: test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 170, in test_f3_full_cont_ops_receipt_checks
    self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'MEMORY.json differs')
AssertionError: 0 == 0 : MEMORY.json differs

======================================================================
FAIL: test_f4_every_copied_a4_member_pinned_before_output (__main__.Round6Tests.test_f4_every_copied_a4_member_pinned_before_output) (member='package/BATCH.sh')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 183, in test_f4_every_copied_a4_member_pinned_before_output
    with self.assertRaisesRegex(ValueError,'A4 member pin|A4 batch pin'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f4_every_copied_a4_member_pinned_before_output (__main__.Round6Tests.test_f4_every_copied_a4_member_pinned_before_output) (member='package/3.py')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 183, in test_f4_every_copied_a4_member_pinned_before_output
    with self.assertRaisesRegex(ValueError,'A4 member pin|A4 batch pin'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f4_every_copied_a4_member_pinned_before_output (__main__.Round6Tests.test_f4_every_copied_a4_member_pinned_before_output) (member='package/a/0.json')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 183, in test_f4_every_copied_a4_member_pinned_before_output
    with self.assertRaisesRegex(ValueError,'A4 member pin|A4 batch pin'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f4_every_copied_a4_member_pinned_before_output (__main__.Round6Tests.test_f4_every_copied_a4_member_pinned_before_output) (member='package/a/4.py')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 183, in test_f4_every_copied_a4_member_pinned_before_output
    with self.assertRaisesRegex(ValueError,'A4 member pin|A4 batch pin'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f4_every_copied_a4_member_pinned_before_output (__main__.Round6Tests.test_f4_every_copied_a4_member_pinned_before_output) (member='package/a/7.py')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 183, in test_f4_every_copied_a4_member_pinned_before_output
    with self.assertRaisesRegex(ValueError,'A4 member pin|A4 batch pin'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f4_every_copied_a4_member_pinned_before_output (__main__.Round6Tests.test_f4_every_copied_a4_member_pinned_before_output) (member='fetch_return.py')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 183, in test_f4_every_copied_a4_member_pinned_before_output
    with self.assertRaisesRegex(ValueError,'A4 member pin|A4 batch pin'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f4_every_copied_a4_member_pinned_before_output (__main__.Round6Tests.test_f4_every_copied_a4_member_pinned_before_output)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 191, in test_f4_every_copied_a4_member_pinned_before_output
    with self.assertRaisesRegex(ValueError,'bootstrap pin'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f5_checkpoint_binding_and_runtime_recheck (__main__.Round6Tests.test_f5_checkpoint_binding_and_runtime_recheck) (asset='RESTORE.json')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 211, in test_f5_checkpoint_binding_and_runtime_recheck
    with self.assertRaises(ValueError):selected_gate(self.helper,args)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f5_checkpoint_binding_and_runtime_recheck (__main__.Round6Tests.test_f5_checkpoint_binding_and_runtime_recheck) (asset='binding.json')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 211, in test_f5_checkpoint_binding_and_runtime_recheck
    with self.assertRaises(ValueError):selected_gate(self.helper,args)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f5_checkpoint_binding_and_runtime_recheck (__main__.Round6Tests.test_f5_checkpoint_binding_and_runtime_recheck)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 214, in test_f5_checkpoint_binding_and_runtime_recheck
    with self.assertRaisesRegex(ValueError,'export identity|export pin'):selected_gate(self.helper,args)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f5_production_device_is_required (__main__.Round6Tests.test_f5_production_device_is_required)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 228, in test_f5_production_device_is_required
    self.assertTrue(hasattr(self.kit,'validate_device'),'GPU name is recorded but never required')
AssertionError: False is not true : GPU name is recorded but never required

======================================================================
FAIL: test_f5_runtime_asset_recheck (__main__.Round6Tests.test_f5_runtime_asset_recheck)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 218, in test_f5_runtime_asset_recheck
    self.assertTrue(hasattr(self.kit,'validate_assets'),'Gate lacks runtime asset authentication')
AssertionError: False is not true : Gate lacks runtime asset authentication

======================================================================
FAIL: test_info_done_whitespace (__main__.Round6Tests.test_info_done_whitespace)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 240, in test_info_done_whitespace
    self.assertNotIn('test "$(cat "$E/5")" =',text,'Whitespace-only receipt changes still refuse')
AssertionError: 'test "$(cat "$E/5")" =' unexpectedly found in '#!/bin/bash\nset -euo pipefail\numask 077\nD=$(cd -- "$(dirname -- "$0")" && pwd)\nP=/project/community/jjyeung/okh7/a15_cot_apab0123456789\nexport TZ=UTC CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud CLOUDSDK_CORE_DISABLE_PROMPTS=1\nE=$P/a/e\ntest ! -e "$E"\nmkdir -m 700 "$E"\nOBJECT=q8/8865619b/673bc60f_m600.tar\ncp /project/community/jjyeung/okh7/abcdef/5 "$E/5"\ntest "$(cat "$E/5")" = \'q8/8865619b/673bc60f_m600.tar 4 2222222222222222222222222222222222222222222222222222222222222222\'\ncp /project/community/jjyeung/okh7/abcdef/7 "$E/7"\ntest "$(sha256sum "$E/7" | cut -d\' \' -f1)" = 3b0051c4a9cc661d02019a645165fc3e23d658d2f24a6fd6fd86ec7877ba4fc1\ncp /project/community/jjyeung/okh7/abcdef/8 "$E/8"\ntest "$(sha256sum "$E/8" | cut -d\' \' -f1)" = 4c0dd9d6e4535a2945ed58754c1cdd5e9a316067be35f2e8440caa9a80e1c915\ncp /project/community/jjyeung/okh7/abcdef/9 "$E/9"\ntest "$(sha256sum "$E/9" | cut -d\' \' -f1)" = 7f654d2f0ae9f06083f2fc8fd793512c154b4d01ce8632fb733d4191205af770\nfor i in 0 1 2 3; do\n  test ! -e "$E/$i"\n  gsutil -o Boto:num_retries=0 -o Boto:metadata_service_num_attempts=1 -o GSUtil:parallel_process_count=1 -o GSUtil:parallel_thread_count=1 -o GSUtil:sliced_object_download_threshold=0 -o GSUtil:sliced_object_download_max_components=1 -q cp "gs://cmu-gpucloud-jjyeung/$OBJECT.part0$i-of-04" "$E/$i.partial"\n  mv "$E/$i.partial" "$E/$i"\ndone\n/usr/bin/python3 -I -s -B "$P/a/4.py" --parts "$E/0" "$E/1" "$E/2" "$E/3" --done "$E/5" --object "$OBJECT" --config "$E/7" --receipt "$E/8" --data-receipt "$E/9" --lineage SFT --step 600 --out "$P/a/export.json" --prep-tar "$P/a/6" --base-inputs "$P/a/0.json" --inputs-out "$P/a/1.json"\nPREP=$(sha256sum "$P/a/6" | cut -d\' \' -f1)\n/usr/bin/python3 -I -s -B "$D/d.py" "$P/a/1.json" "$P/a/0.json" "$PREP" > "$P/a/dry.json"\n(cd "$P" && CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 04:30:00)\n/usr/bin/python3 -I -s -B "$D/d2.py" "$P" "$P/a/w2" > "$P/a/dry2.json"\nprintf \'%s\\n\' 0 > "$P/a/1.txt"\n' : Whitespace-only receipt changes still refuse

======================================================================
FAIL: test_info_submit_requires_successful_bound_gpu_gate (__main__.Round6Tests.test_info_submit_requires_successful_bound_gpu_gate) (field='passed')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 257, in test_info_submit_requires_successful_bound_gpu_gate
    with self.subTest(field=key):self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'GPU evidence ignored')
                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 0 == 0 : GPU evidence ignored

======================================================================
FAIL: test_info_submit_requires_successful_bound_gpu_gate (__main__.Round6Tests.test_info_submit_requires_successful_bound_gpu_gate) (field='adoption_plan_sha256')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 257, in test_info_submit_requires_successful_bound_gpu_gate
    with self.subTest(field=key):self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'GPU evidence ignored')
                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 0 == 0 : GPU evidence ignored

======================================================================
FAIL: test_info_submit_requires_successful_bound_gpu_gate (__main__.Round6Tests.test_info_submit_requires_successful_bound_gpu_gate) (field='required_device_type')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 257, in test_info_submit_requires_successful_bound_gpu_gate
    with self.subTest(field=key):self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'GPU evidence ignored')
                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 0 == 0 : GPU evidence ignored

======================================================================
FAIL: test_info_submit_requires_successful_bound_gpu_gate (__main__.Round6Tests.test_info_submit_requires_successful_bound_gpu_gate) (field='adoption_assets')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 257, in test_info_submit_requires_successful_bound_gpu_gate
    with self.subTest(field=key):self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'GPU evidence ignored')
                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 0 == 0 : GPU evidence ignored

======================================================================
FAIL: test_info_submit_requires_successful_bound_gpu_gate (__main__.Round6Tests.test_info_submit_requires_successful_bound_gpu_gate) (field='adoption_profile')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 257, in test_info_submit_requires_successful_bound_gpu_gate
    with self.subTest(field=key):self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'GPU evidence ignored')
                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 0 == 0 : GPU evidence ignored

======================================================================
FAIL: test_info_submit_requires_successful_bound_gpu_gate (__main__.Round6Tests.test_info_submit_requires_successful_bound_gpu_gate)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 259, in test_info_submit_requires_successful_bound_gpu_gate
    self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0)
AssertionError: 0 == 0

----------------------------------------------------------------------
Ran 9 tests in 39.597s

FAILED (failures=31)
```

```bash
READ_ROUND7_BEFORE=1 bash work/cpu.sh work/run_fixture5.py work/src/u0/tests/test_round7.py
```

Exact output:

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
test_rebind_default400_and_explicit600 (__main__.Round7Tests.test_rebind_default400_and_explicit600) ... FAIL

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
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round7.py", line 153, in test_info_host_paths_allocation_and_input_evidence
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
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round7.py", line 141, in test_info_unpack_ignores_python_environment_and_keeps_sibling_import
    self.assertIn(' -s -E -B ./unpack_return.py',block)
AssertionError: ' -s -E -B ./unpack_return.py' not found in ': "${RETURN_ARCHIVE:?Received fetched-return archive on local scratch}"\n: "${RETURN_SHA256:?Printed Orchard SHA256 of the fetched-return archive}"\nprintf \'%s  %s\\n\' "$RETURN_SHA256" "$RETURN_ARCHIVE" | nice -n 10 sha256sum -c -\nmkdir "$LOCAL/step600/f"\nnice -n 10 tar -xzf "$RETURN_ARCHIVE" -C "$LOCAL/step600/f"\n(cd "$LOCAL/step600" && CUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -s -B ./unpack_return.py \\\n  --archive "$LOCAL/step600/f/0.tgz" --exit "$LOCAL/step600/f/EXIT.json" \\\n  --out "$LOCAL/step600/ret" > "$LOCAL/step600/unpack-success.json" && \\\n  test -s "$LOCAL/step600/unpack-success.json")'

======================================================================
FAIL: test_rebind_default400_and_explicit600 (__main__.Round7Tests.test_rebind_default400_and_explicit600)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round7.py", line 159, in test_rebind_default400_and_explicit600
    self.assertIn('bound_export',inspect.signature(self.helper.gate).parameters,'Gate lacks selectable export parameter')
AssertionError: 'bound_export' not found in mappingproxy(OrderedDict({'operator': <Parameter "operator">, 'prepared': <Parameter "prepared">, 'proof': <Parameter "proof">, 'config_template': <Parameter "config_template">, 'settings_out': <Parameter "settings_out">, 'config_out': <Parameter "config_out">, 'asset_receipts': <Parameter "asset_receipts=None">})) : Gate lacks selectable export parameter

----------------------------------------------------------------------
Ran 8 tests in 2.797s

FAILED (failures=10)
```

```bash
READ_NODE4_BEFORE=1 bash work/cpu.sh work/run_fixture5.py work/src/u0/tests/test_round4.py Round4Tests.test_f2_step600_real_job_and_rehearsal_memory
```

Exact output:

```text
test_f2_step600_real_job_and_rehearsal_memory (__main__.Round4Tests.test_f2_step600_real_job_and_rehearsal_memory) ... FAIL

======================================================================
FAIL: test_f2_step600_real_job_and_rehearsal_memory (__main__.Round4Tests.test_f2_step600_real_job_and_rehearsal_memory)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 337, in test_f2_step600_real_job_and_rehearsal_memory
    self.assertEqual(proof['memory'].get('read_cache_bytes'),12*1024**3)
AssertionError: None != 12884901888

----------------------------------------------------------------------
Ran 1 test in 8.701s

FAILED (failures=1)
```

```bash
READ_F16_BEFORE=1 bash work/cpu.sh work/run_fixture5.py work/src/u0/tests/test_round3.py Round3Tests.test_f4_worker_uses_settings_argv_without_environment_side_effect
```

Exact output:

```text
test_f4_worker_uses_settings_argv_without_environment_side_effect (__main__.Round3Tests.test_f4_worker_uses_settings_argv_without_environment_side_effect) ... FAIL

======================================================================
FAIL: test_f4_worker_uses_settings_argv_without_environment_side_effect (__main__.Round3Tests.test_f4_worker_uses_settings_argv_without_environment_side_effect)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round3.py", line 188, in test_f4_worker_uses_settings_argv_without_environment_side_effect
    self.assertNotIn('H10_SETTINGS',kit.os.environ)
AssertionError: 'H10_SETTINGS' unexpectedly found in {'CUDA_VISIBLE_DEVICES': 'fixture', 'H10_SETTINGS': '/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/f3b5331eb574445b88a6ebd4034bca11/u0.json'}

----------------------------------------------------------------------
Ran 1 test in 0.878s

FAILED (failures=1)
```

The final seal runs `bash work/cpu.sh work/integrity7.py`; its exact output is [integrity7.txt](checks/integrity7.txt). [FINAL_INTEGRITY.json](checks/FINAL_INTEGRITY.json) pins the report, note, MANIFEST, diffs and evidence. Seal output stays external to avoid a report/hash cycle.
