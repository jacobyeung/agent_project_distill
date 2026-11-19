VERDICT: DONE All round-8 fixes pass CPU verification; production adoption requires the step-400 H100 byte-parity gate.

**Measured validation:** 129 workspace tests and 48 fresh-application tests pass. All ten round-8 tests fail on the reviewed implementation with 29 expected assertion failures and pass on the delivered implementation. All twelve retained fail-before controls reran. Five diffs apply with zero fuzz. Original reader files and OFF output bytes remain unchanged; ON CPU fixtures preserve exact answers and traces. GPU byte equality remains unmeasured and mandatory.

**Bound export, read from supplied pins:** step **400 only**, read A/job **173060**, source package **a15_cot_apdc76460c3a164**, artifact SHA256 **5083243cfedd2a389dfca579c5452e7d0c73b03a58e1cb7d204292ddd10e67cd**. Every later export is diagnostic and cannot authorize adoption through this kit. The builder refuses a different identity before reading the base; the gate requires the complete supplied export pin.

**Estimated storage:** the uncompressed asset archive is **about 33 GB**, based on **32,606,120,583 expanded bytes read from the six archives declared in the supplied a10b_pins/1.json**, plus tar headers ([source pin](checks/ARCHIVE_ESTIMATE8.json)). The links preserve shared shard/head targets. No production-size archive was measured. Reserve additional space for extraction, source trees and runtime outputs.

**Measured local resources:** largest suite child RSS 399,253,504 bytes; guard benchmark peak RSS 1,326,075,904 bytes. Workspace usage at report generation: 2,940,861,788 unique-inode bytes, below 3,000,000,000. [STORAGE8.json](checks/STORAGE8.json) records 164,251,867 identical bytes shared across 4,198 completed pre-task fixture paths, preserving each path and its bytes. No workspace-cap violation was observed.

Work started **17:30:31 UTC, 2026-11-19**; deadline **18:30:31 UTC**. Report generated at Thu Nov 19 17:52:25 UTC 2026. [out_round8](../out_round8/) preserves the complete reviewed delivery. CPU checks used torch 2.11.0+cpu, transformers 5.12.1, eight torch threads, CUDA hidden and `nice -n 10` (benchmark effective nice 19). No Git, SSH, scheduler action, GPU execution, paid API, input-tree edit or deletion command ran. Network reads were limited to official library documentation.

## Review round 8: finding -> fix -> test

| Finding | Fix | Regression test |
|---|---|---|
| MEDIUM 1: dereferenced restore links fail loader admission | Validate all links inside the live namespace, then `tar -cf - -C <logical>/d .`; preserve in-tree links and reject escaping targets, dangling links and cycles. Archive estimate: about 33 GB. | `test_f1_preserved_absolute_link_passes_real_artifact_and_load_native` extracts `e/heads.pt -> <logical>/d/m400/heads.pt`, calls real Artifact.verify and real load_native, and reaches the stub processor only after the real resolve() checks. Six link-refusal cases pass. |
| LOW 2: GPU interpreter/environment unbound | README uses d/v/py, explicit opaque XDG/HF/Triton caches and executable version/CUDA preflight. ON prepare adds CUDA and READY.environment. CPU evidence includes ENVIRONMENT.json; gate, workers, ue.json and submit compare exact torch/transformers/CUDA values and its SHA256. | Runtime/receipt, executable shell preflight, CPU-bound gate and submit mutation tests reject changed versions/hash and missing CUDA. CUDA imports/device availability are explicit test doubles. |
| LOW 3: another export fails late | a19 admits only the reviewed step-400 identity, archive pin/size, base/frame identity and preparation hashes before reading the base. Gate accepts only the complete reviewed export; no selection flag remains. | Eleven binding mutations refuse before base access/output. Fixed step-400 build and complete CPU operator path pass; changed artifact refuses at the gate. |
| LOW 4: unresolved package path | Resolve both recorded and package archive paths. | Execute the README archive-validation heredoc through a symlinked package parent. |
| INFO 5: aliases, stderr and job name | Require symlink aliases; keep stderr in results/4.err; generate a fresh a15_cot_ap hexadecimal job token. | Real tar failure diagnostic survives; README alias/environment/token commands are checked. |


## Staging and adoption contract

The ON CPU-proof job opens `$P/a/4.tar` outside bwrap, then runs link validation and tar inside its live `J.namespace(root)`. Validation walks `logical/d` without following directory symlinks and resolves every symlink strictly. A target outside that root, a broken chain or a cycle aborts. The same namespace process executes `/bin/tar -cf - -C <logical>/d .`. Absolute in-tree links therefore reach their original targets when the GPU host restores the same logical root. Tar stderr persists at `results/4.err`; a failed attempt has no successful CPU.json. The job flushes/fsyncs and hashes the archive before publishing its path, bytes, logical root and SHA256. OFF performs none of this staging.

The tiny archive/loader regression uses real Artifact and load_native admission; it stubs only model construction after admission. The complete A4 CPU fixture executes the patched CPU helper, preparation, rehearsal, bootstrap and 636 stub reads. Its data, namespace/storage and model work are synthetic. Applied-tree integration reconstructs READY-identical assets from the produced archive after the original fixture data directory becomes unavailable.

ON prepare records torch/transformers and compiled CUDA versions in ENVIRONMENT.json and pins its exact bytes in READY. The CPU helper copies that file into proof evidence. `a20 gate` checks the evidence against CPU READY before GPU work; the parent, each worker and receipt writer compare the actual library/build versions and hash again. `ue.json` carries those checked values, and SUBMIT_CHECK compares them with the CPU-bound file. The real CPU fixture records cuda=null, so it cannot pass the production environment check. A separate, explicitly synthetic version-import double exercises successful receipt serialization and submit checks; it is not GPU evidence.

On the H100 host, `/scratch/jjyeung` must physically exist and be writable outside bwrap. Preserve the exact logical root; its destination must be absent before extraction. The README sets `READ_PYTHON="$GPU_LOGICAL/d/v/py"` and preflights that executable, versions and CUDA availability before starting the gate. If that interpreter depends on an unavailable external path, the preflight fails; no substitute interpreter is accepted. XDG_CACHE_HOME, HF_HOME and TRITON_CACHE_DIR live under the opaque kit root. Neutral asset aliases must be symlinks because the loader admits resolved manifest targets. The binding/environment examples use symlinks too.

The gate allocation is one H100, eight CPUs, 200G, five hours, general/no-requeue, named `a15_cot_ap` plus a fresh opaque hexadecimal token. Preserve the allocation's actual CUDA_VISIBLE_DEVICES. Device admission requires **NVIDIA H100 80GB HBM3**, **132 SMs**, capability **9.0**, and **79–86 billion bytes** of memory.

Follow [README](kit_parity50/README.md): apply reader patches 01–03 and operator patches 04–05; build with `u0/a19.py --enable-extensions --manifest ... --extension-pins ...` and the delivered step-400 binding; generate operations; place; run detached fill; wait at most 14,400 seconds; run CPU proof; stage and run the zero-difference GPU gate; return its receipt; submit; fetch and unpack. Failed/killed attempts require inspection and a fresh token, never automatic retry.

Submit keeps cont_ops' complete CPU assertions verbatim and checks cache memory, both dry checks, an empty general queue, the bounded return pool, and matching gate plan/profile/assets/device/environment/kit hashes. A refused unpack leaves its extracted tree behind. Scorers require **success output after exit status 0**; complete=false remains partial. The documented unpack command uses `-s -E -B` from the operator directory and an `&&` handoff.

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

**Estimate for what a19 builds:** the 636-item A4 schedule takes about **7,351.824 s (2 h 02 min 32 s; 11.559 s/item including fixed overhead)** if the supplied A4 throughput carries forward, with zero assumed cache saving. This does not measure the step-400 export. Target weights, cache guard/copy costs, actual reuse and staging can change it.

**Separate Package D estimate:** the 580-item distance read is a B5 fork with a 03:30 walltime and has **no ON route in a19**. Using 23.599762 s/item plus 75.446133 s loading and 49.761372 s overhead gives an estimate of **13,813.069 s (3 h 50 min)** on one card. Ideal two/four balanced-shard estimates are 6,969.138 / 3,547.173 s; they require an undelivered multi-card operator and exclude scene imbalance, staging, queues and preemption. The fixed 50-item reuse-heavy sample cannot establish these throughput estimates.





## Measured CPU guard overhead

Each bf16 stub has 2048×1024 parameter tensors and a 1024-element buffer per module. Forward returns a 32-element tensor without model-sized matrix work. After one miss and a warm hit, each implementation runs seven timed hits; the boundary median covers three hashes. These CPU measurements do not predict GPU speedup. Raw samples: [CACHE_COST3.json](checks/CACHE_COST3.json).

| Parameters | Parameter/buffer tensors | Weight+buffer bytes | Full hashing ms/call | Live guard ms/call | Install s | Boundary s |
|---:|---:|---:|---:|---:|---:|---:|
| 268435456 | 128/128 | 537133056 | 381.157 | 38.085 | 0.378 | 0.365 |
| 536870912 | 256/256 | 1074266112 | 852.952 | 57.091 | 0.724 | 0.809 |

## Framework evidence

[FRAMEWORK_EVIDENCE.md](FRAMEWORK_EVIDENCE.md) supplies installed-source file:line citations and official documentation for retained framework assumptions. Environment-version evidence comes from torch/__init__.py:60, torch/torch_version.py:66, torch/version.py:4–6 and transformers/__init__.py:21. CUDA availability comes from torch/cuda/__init__.py:161–180; device properties from :673–695 and torch/_C/__init__.pyi:12448–12453. [SOURCE_EVIDENCE8.json](checks/SOURCE_EVIDENCE8.json) pins those installed files and documentation URLs. [TORCH_VERSIONS3.json](checks/TORCH_VERSIONS3.json) records rerun mutation probes. No GPU call was executed locally.

## Patches and authentication

Base SHA256: `813fe4c57b2deed4bd731dd1e3493b6b0bed8d31e7bff92ff112cf5c9df823c3` over **927 files**. Reviewed A4 payload SHA256: `4498fca72a8e4b476b38f097ffdf3ff88b5aa20fc036bd196b18a5706e9fe46d` (5252958 bytes). B5 checks establish patch applicability; this GPU kit authenticates A4.

| Patch | Bytes | SHA256 |
|---|---:|---|
| [01_bounded_read_caches.diff](patches/01_bounded_read_caches.diff) | 90430 | `369af9663fbc1008f9ecf5a32c5067ba4a5f4cd31412f07db8263b13b23fd4c3` |
| [02_atomic_scene_shards.diff](patches/02_atomic_scene_shards.diff) | 218841 | `5f76cf79e29471138161e476daf3920ec2bcbf751586fc47528fbd7388530cfa` |
| [03_production_integration.diff](patches/03_production_integration.diff) | 228258 | `a8759582c4335a0c17d3c9e1a5eb7664a8c95af6832e27d01d138a0b8c76ffaa` |
| [04_operator_cache_bound.diff](patches/04_operator_cache_bound.diff) | 2723 | `0d3bdc2d943554cd525627466d2d71f30881884e76df95204ede6c1accdb9061` |
| [05_operator_return_and_proof.diff](patches/05_operator_return_and_proof.diff) | 6754 | `5369d7a7b2442a00a63bf318904a5e60ba972f6a6512500241c64019c77778cd` |

Reader patches add **38 files** under u0/, including tests, and preserve all original reader bytes. Operator changes remain behind read_extensions. MANIFEST pins full original inventories, copied A4 members, batch/bootstrap, patched operators, extension bytes, kit, operation files and export provenance. The 85 original development files and all 927 original fresh-application files match their input hashes.

## What could go wrong and how we would notice

| Risk | Detection and response |
|---|---|
| Restore/environment includes a symlink outside d, or tar/storage fails | Namespace validation or tar fails before CPU.json; results/4.err preserves the error. Inspect and use a fresh attempt. |
| Exact logical path or interpreter is unavailable outside bwrap | Host-path checks and the executable GPU preflight fail before gate work. |
| Environment changes after CPU proof | Gate/runtime/receipt/submit hash and exact version comparisons refuse. |
| Different export, changed filled pin, source, operator or kit | Builder, CPU evidence, worker and submit pins refuse. |
| GPU kernels or eager SAM change answer/trace bytes | Zero-difference gate refuses; equal scores cannot waive it. |
| Cache overhead or working memory outweighs savings | Measure full worker wall time and host/GPU peaks; cache limits exclude model/caller memory. |
| A raw write is restored between boundaries | Frozen ownership remains required; the guard cannot detect this sequence. |
| A partial/refused return is scored | Require successful unpack output and complete status. |

## Not done

No production GPU parity, throughput or peak-memory measurement; large archive; real bwrap/restore; interpreter execution on H100; transport/upload/submit; return publication; persistent-storage requeue; or multi-card A4 operator was run or delivered here. No numerical tolerance or batching is offered. The array prototype remains approved=false. CPU tests need no local OS sockets. Archive size is an estimate, and host storage/interpreter readiness remain external preconditions.

## Review round 7: finding -> fix -> test

CPU-job staging, bounded fill waits, exact SXM admission, kit/input evidence and host-safe receipt/unpack commands pass their regressions. The decision export is step 400 only. The retained before-fix control reproduces ten assertion failures.

## Review round 6: finding -> fix -> test

Executable unpack, detached locked fill, complete cont_ops assertions, copied-member pins and checkpoint/device admission pass. The reviewed implementation reproduces 31 expected assertion failures.

## Review round 5: finding -> fix -> test

The batch matches cont_ops wrap_batch and passes the real bundle guard. Payload/operator/extension authentication, operations, profile, pool, forecast and unpack checks pass; the before-fix control reproduces eleven failures.

## Review round 4: finding -> fix -> test

The A4 route preserves run keys, binding, fill admission and compatible helpers; CPU preparation/rehearsal/bootstrap/action dispatch pass. The fixed step-400 fixture completes 636 stub reads in five verified ordinary journals. Return checks reject invalid weight receipts. Both retained failure controls reproduce.

## Review round 3: finding -> fix -> test

Install/type-boundary hashes, cheap fatal live guards, processor-only mode, operator memory/dispatch, base authentication, lock/worker and OFF-import checks pass. Retained failure controls reproduce.

## Review round 2: finding -> fix -> test

Entry isolation, path policy, bounded array attempts, overlay pins, SAM capacity, deadline/lock/accounting and worker setup pass. The before-fix control reproduces thirteen assertions and the expected CLI import error.

## Review round 1: finding -> fix -> test

Typed keys, parity schemas, original/OFF provenance, frozen identity, lock-held recovery, opaque transport and bounded storage pass; all eight before-fix regressions reproduce.

The review sections are retained because the binding prompts explicitly request them. Historical test-control labels identify the preserved defect demonstrations; they do not offer additional adoption targets.

## Commands and exact outputs

Commands ran from `/scratch/jjyeung/orch_n30/so_read`. `work/cpu.sh` exports CUDA_VISIBLE_DEVICES="", OMP/MKL/OPENBLAS threads=8, TOKENIZERS_PARALLELISM=false, PYTHONDONTWRITEBYTECODE=1 and scratch caches; it executes the approved Python through `nice -n 10` and `-I -s -B`. Children inherit these limits. Tests set torch threads to eight. The documented unpack command uses `-s -E -B` for sibling imports.

Test subprocesses set READ_INPUT_SRC=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/A4/src and READ_TEST_TMP=/scratch/jjyeung/orch_n30/so_read/work/test-artifacts. Applied suites set READ_OPERATOR_SOURCE and READ_OPERATOR4_SOURCE beneath `/scratch/jjyeung/orch_n30/so_read/work/apply-round8/7bad3024af544e60b7370835bb10f7cb/operator`. Immutable fixture sharing detaches shared files before edits. All outputs below are literal. Before-fix failures are expected controls. No cluster kill or automatic relaunch occurred.

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
round4: CPU bound-export fixture: /scratch/jjyeung/orch_n30/so_read/work/test-artifacts/d18b78d68ff04ed89f95f8173c9ed0f8
round5: All CPU receipt checks passed
round6: Detached fill: success=0, failure=17, duplicate launch refused.
round7: Only reviewed step-400 export passes; changed artifact and selectable-export API refuse.
round8: Runtime torch/transformers/CUDA and environment SHA256 are exact; changed versions, bytes and CPU build refuse.
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
PASS: round8_before reproduces FAILED (failures=29).
PASS: round4_before reproduces FAILED (failures=7, skipped=1).
PASS: node4_before reproduces FAILED (failures=1).
PASS: f16_behavior_before reproduces FAILED (failures=1).
PASS: Python syntax, shell syntax, and default-off execution guards.
{"cuda_visible_devices": "", "max_child_rss_bytes": 399253504, "torch": "2.11.0+cpu", "torch_threads": 8, "transformers": "5.12.1", "workspace_bytes": 2957955790}
```

```bash
bash work/cpu.sh work/run_fixture5.py work/build_patches.py
```

Exact output:

```text
PASS: 3 additive reader diffs (38 files) plus 2 default-OFF A4 operator diffs; zero-fuzz application; unchanged original reader hash trees.
PASS: OFF, round-4/5/6/7/8 integration and comparator suites pass from the fresh applied A4 tree; both complete 927-file base inventories authenticate.
Applied verification root: /scratch/jjyeung/orch_n30/so_read/work/apply-round8/7bad3024af544e60b7370835bb10f7cb
```

```bash
bash work/cpu.sh work/gate_integration8.py
```

Exact output:

```text
PASS: actual CPU fixture environment refuses before synthetic GPU receipt serialization.
All CPU receipt checks passed
{"passed": true, "pool_bytes": 0}
PASS: CPU helper produced the archive before CPU.json; its recorded hash/bytes and exact a/1.json match.
PASS: archive reconstructs READY-identical assets after the fixture private data path becomes unavailable.
PASS: public stage-kit bytes match MANIFEST-derived pins; changed driver, comparator and sealed sample each refuse.
PASS: exact CPU evidence feeds gate and full submit assertions; only reviewed step400 passes; synthetic environment evidence binds submit.
PASS: failed synthetic GPU receipt refuses; no GPU evidence was measured or submitted.
{"archive_bytes": 20480, "archive_sha256": "789efaf638b91b70a6193a23c236fd6802f869b8cdde069016bf64b62f2f08cb", "assets": {"binding": "4e4cbf9cb04ec6d1fe6efcba26a6316662fdf2769a7d33b2278471904cef6e80", "export_pin": "3ecf348301576174e3322b7105b6c3cab87606ef906226dab7cdb6073d651a5e", "restore": "44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a"}, "environment": {"cuda": "12.9", "sha256": "437dd3df35eac78affdb22dacee5045ea803d23f451d95fa4590fb321782af6d", "torch": "2.11.0+cpu", "transformers": "5.12.1"}, "kit": {"compare.py": "73858354fe8d366880873246e6256393ea2b27d5979af4e128e93c569a92f50e", "run.py": "82357dffb4611336220008e75b05e9f59a20c9bcb866d2f128445cb9939ff71a", "sample50.json": "1fdb65050f933d8578c849fbaa1010515ed07ad959234afd2d90cefdd946531b"}, "plan": "faecc4a21ca3ecff24167d8b6e320b19b3b2d5c79fd674dc92d5d7b93625805b", "required_device_type": "H100_80GB"}
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
        "data_ptr": 141078912,
        "object_id": 139768179614544,
        "version": 1
      },
      "before": {
        "data_ptr": 141078912,
        "object_id": 139768179614544,
        "version": 0
      },
      "object_changed": false,
      "operation": "parameter.add_",
      "pointer_changed": false,
      "version_changed": true
    },
    {
      "after": {
        "data_ptr": 141089408,
        "object_id": 139768179614864,
        "version": 1
      },
      "before": {
        "data_ptr": 141089408,
        "object_id": 139768179614864,
        "version": 0
      },
      "object_changed": false,
      "operation": "detach().add_",
      "pointer_changed": false,
      "version_changed": true
    },
    {
      "after": {
        "data_ptr": 141090112,
        "object_id": 139768179614544,
        "version": 0
      },
      "before": {
        "data_ptr": 141090112,
        "object_id": 139768179614544,
        "version": 0
      },
      "object_changed": false,
      "operation": "parameter.data.add_",
      "pointer_changed": false,
      "version_changed": false
    },
    {
      "after": {
        "data_ptr": 141092736,
        "object_id": 139768179614864,
        "version": 0
      },
      "before": {
        "data_ptr": 141090624,
        "object_id": 139768179614864,
        "version": 0
      },
      "object_changed": false,
      "operation": "parameter.data assignment to cloned storage",
      "pointer_changed": true,
      "version_changed": false
    },
    {
      "after": {
        "data_ptr": 141093120,
        "object_id": 139768179614544,
        "version": 0
      },
      "before": {
        "data_ptr": 141093120,
        "object_id": 139768179614544,
        "version": 0
      },
      "object_changed": false,
      "operation": "parameter.data assignment to same storage",
      "pointer_changed": false,
      "version_changed": false
    },
    {
      "after": {
        "data_ptr": 141093248,
        "object_id": 139768179614864,
        "version": 0
      },
      "before": {
        "data_ptr": 141093248,
        "object_id": 139768179614864,
        "version": 0
      },
      "object_changed": false,
      "operation": "numpy raw storage write",
      "pointer_changed": false,
      "version_changed": false
    },
    {
      "after": {
        "data_ptr": 141093440,
        "object_id": 139768179614544,
        "version": 1
      },
      "before": {
        "data_ptr": 141093440,
        "object_id": 139768179614544,
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
      "after_install_seconds": 0.37753095710650086,
      "after_per_call": {
        "max_seconds": 0.04523695819079876,
        "median_seconds": 0.03808464715257287,
        "min_seconds": 0.031626817770302296,
        "seconds": [
          0.031626817770302296,
          0.034481871873140335,
          0.03762305388227105,
          0.03808464715257287,
          0.04367958102375269,
          0.04523695819079876,
          0.04367376212030649
        ]
      },
      "before_install_seconds": 6.081210449337959e-05,
      "before_per_call": {
        "max_seconds": 0.5183775341138244,
        "median_seconds": 0.38115734700113535,
        "min_seconds": 0.36364213982596993,
        "seconds": [
          0.46960617415606976,
          0.38115734700113535,
          0.36364213982596993,
          0.5183775341138244,
          0.3796976371668279,
          0.39939274499192834,
          0.3713282709941268
        ]
      },
      "blocks": 128,
      "boundary": {
        "max_seconds": 0.3655566619709134,
        "median_seconds": 0.364585654810071,
        "min_seconds": 0.35290226712822914,
        "seconds": [
          0.35290226712822914,
          0.364585654810071,
          0.3655566619709134
        ]
      },
      "buffer_shape": [
        1024
      ],
      "buffer_tensors": 128,
      "dtype": "bfloat16",
      "median_speed_ratio": 10.008162750574037,
      "parameter_count": 268435456,
      "parameter_shape": [
        2048,
        1024
      ],
      "parameter_tensors": 128,
      "weight_and_buffer_bytes": 537133056
    },
    {
      "after_install_seconds": 0.7241286048665643,
      "after_per_call": {
        "max_seconds": 0.06026602489873767,
        "median_seconds": 0.05709055112674832,
        "min_seconds": 0.055647526402026415,
        "seconds": [
          0.06026602489873767,
          0.05890423199161887,
          0.05700187757611275,
          0.056477099657058716,
          0.05709055112674832,
          0.055647526402026415,
          0.058933827094733715
        ]
      },
      "before_install_seconds": 5.6263990700244904e-05,
      "before_per_call": {
        "max_seconds": 1.056832719128579,
        "median_seconds": 0.8529518940486014,
        "min_seconds": 0.7361530251801014,
        "seconds": [
          0.8529518940486014,
          1.056832719128579,
          0.9871446690522134,
          0.794601493049413,
          0.9360874486155808,
          0.7819303632713854,
          0.7361530251801014
        ]
      },
      "blocks": 256,
      "boundary": {
        "max_seconds": 0.8288969350978732,
        "median_seconds": 0.8085775999352336,
        "min_seconds": 0.8060437492094934,
        "seconds": [
          0.8288969350978732,
          0.8085775999352336,
          0.8060437492094934
        ]
      },
      "buffer_shape": [
        1024
      ],
      "buffer_tensors": 256,
      "dtype": "bfloat16",
      "median_speed_ratio": 14.940333859362106,
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
  "max_rss_bytes": 1326075904,
  "nice": 19,
  "threads": 8,
  "torch": "2.11.0+cpu"
}
```

```bash
bash work/cpu.sh work/docs_check8.py
```

Exact output:

```text
PASS: 15 README shell blocks parse; archive-validation heredoc parses as Python 3.6; host paths and allocation documented.
PASS: cont_ops CPU assertion block remains verbatim; submit and operator helpers parse as Python 3.6.
PASS: installed device-property declarations and official 2.11 documentation recorded; no CUDA query executed.
PASS: step-400-only handoff, symlink archive, version preflight, retained stderr and 33 GB estimate documented.
```

```bash
bash work/cpu.sh work/verify_archive_command8.py
```

Exact output:

```text
PASS: link-validation/tar argv passes the real production opaque-command guard; namespace script parses as Python 3.6.
```

```bash
bash work/cpu.sh work/share_storage8.py
bash work/cpu.sh work/share_storage8_more.py  # first additional pass
bash work/cpu.sh work/share_storage8_more.py  # second additional pass
bash work/cpu.sh work/share_known8.py
```

Exact output:

```text
{"changed_files": 2277, "paths_preserved": true, "read_bytes": 77477050, "scope": "completed pre-task fixtures only; replacements checked byte-for-byte; bounded 100 MB local candidate reads", "unique_bytes_shared": 60001929, "workspace_bytes": 2873281091}
{"changed_files": 1555, "paths_preserved": true, "read_bytes": 99095642, "scope": "completed pre-task fixtures only; replacements checked byte-for-byte; bounded 100 MB local candidate reads", "unique_bytes_shared": 41343325, "workspace_bytes": 2933410474}
Cumulative: {"changed_files": 3832, "passes": 2, "paths_preserved": true, "read_bytes": 176572692, "scope": "completed pre-task fixtures only; replacements checked byte-for-byte; each pass bounded to 100 MB local candidate reads", "unique_bytes_shared": 101345254, "workspace_bytes": 2933410474}
{"changed_files": 188, "paths_preserved": true, "read_bytes": 99002953, "scope": "completed pre-task fixtures only; replacements checked byte-for-byte; bounded 100 MB local candidate reads", "unique_bytes_shared": 12527259, "workspace_bytes": 2945444620}
Cumulative: {"changed_files": 4020, "passes": 3, "paths_preserved": true, "read_bytes": 275575645, "scope": "completed pre-task fixtures only; replacements checked byte-for-byte; each pass bounded to 100 MB local candidate reads", "unique_bytes_shared": 113872513, "workspace_bytes": 2945444620}
Known-reference pass: {"changed_files": 178, "read_bytes": 99933615, "unique_bytes_shared": 50379354, "workspace_bytes": 2940420340}
Cumulative: {"changed_files": 4198, "passes": 4, "paths_preserved": true, "read_bytes": 375509260, "scope": "completed pre-task fixtures only; replacements checked byte-for-byte; each pass bounded to 100 MB local candidate reads", "unique_bytes_shared": 164251867, "workspace_bytes": 2940420340}
```

Patch subprocess output:

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
patching file u0/tests/test_round8.py
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
patching file u0/tests/test_round8.py
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
Ran 15 tests in 2.625s

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
Ran 13 tests in 0.131s

OK
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_off.py
```

Exact output:

```text
test_every_output_byte_and_source_hash_matches_original (__main__.OffContractTests.test_every_output_byte_and_source_hash_matches_original) ... ok

----------------------------------------------------------------------
Ran 1 test in 5.002s

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
Ran 17 tests in 3.879s

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
Ran 13 tests in 3.829s

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
Ran 9 tests in 1.838s

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
Ran 2 tests in 9.717s

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
Ran 2 tests in 0.018s

OK
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py
```

Exact output:

```text
test_f1_bound_package_preserves_a4_contract_and_binding (__main__.Round4Tests.test_f1_bound_package_preserves_a4_contract_and_binding) ... ok
test_f2_bound_real_job_and_rehearsal_memory (__main__.Round4Tests.test_f2_bound_real_job_and_rehearsal_memory) ... ok
test_f3_cache_only_return_refuses_unverified_journals (__main__.Round4Tests.test_f3_cache_only_return_refuses_unverified_journals) ... ok
test_f9_off_builder_guard_and_processor_only (__main__.Round4Tests.test_f9_off_builder_guard_and_processor_only) ... ok

----------------------------------------------------------------------
Ran 4 tests in 21.795s

OK
{"output": "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/d18b78d68ff04ed89f95f8173c9ed0f8/verified-return", "complete": false, "status": "FAILED", "sha256": "79bc8cb5e395a636f9bfa900a218546d1ca18a2a81d74c4d42178726e026667a"}
CPU bound-export fixture: /scratch/jjyeung/orch_n30/so_read/work/test-artifacts/d18b78d68ff04ed89f95f8173c9ed0f8
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
Ran 7 tests in 9.665s

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
Ran 9 tests in 29.103s

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
test_rebind_step400_only (__main__.Round7Tests.test_rebind_step400_only) ... ok

----------------------------------------------------------------------
Ran 8 tests in 6.011s

OK
Live namespace tar: regular file and symlink preserved; archive survives namespace loss; duplicate and OFF guarded.
Fill wait: missing token, dead worker, deadline and exit 17 refuse; exit 0 passes; production maximum 14400 seconds.
Only reviewed step-400 export passes; changed artifact and selectable-export API refuse.
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py
```

Exact output:

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
Ran 10 tests in 7.314s

OK
Absolute e/heads.pt symlink survives tar/extract; real Artifact.verify and load_native admission pass before model loading.
README GPU block runs d/v/py and refuses each version mismatch or unavailable CUDA; CUDA imports are test doubles.
Runtime torch/transformers/CUDA and environment SHA256 are exact; changed versions, bytes and CPU build refuse.
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
Ran 9 tests in 0.292s

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
Ran 3 tests in 0.069s

OK
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/apply-round8/7bad3024af544e60b7370835bb10f7cb/src/u0/tests/test_off.py
```

Exact output:

```text
test_every_output_byte_and_source_hash_matches_original (__main__.OffContractTests.test_every_output_byte_and_source_hash_matches_original) ... ok

----------------------------------------------------------------------
Ran 1 test in 5.748s

OK
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/apply-round8/7bad3024af544e60b7370835bb10f7cb/src/u0/tests/test_round4.py
```

Exact output:

```text
test_f1_bound_package_preserves_a4_contract_and_binding (__main__.Round4Tests.test_f1_bound_package_preserves_a4_contract_and_binding) ... ok
test_f2_bound_real_job_and_rehearsal_memory (__main__.Round4Tests.test_f2_bound_real_job_and_rehearsal_memory) ... ok
test_f3_cache_only_return_refuses_unverified_journals (__main__.Round4Tests.test_f3_cache_only_return_refuses_unverified_journals) ... ok
test_f9_off_builder_guard_and_processor_only (__main__.Round4Tests.test_f9_off_builder_guard_and_processor_only) ... ok

----------------------------------------------------------------------
Ran 4 tests in 22.938s

OK
{"output": "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/94d0bb20e51c4e45a7f4d079a9e636e6/verified-return", "complete": false, "status": "FAILED", "sha256": "53e1b8f79c8a7522d43a1ee76d0aa13a505de28a79810aac877a8b6bfb0d90ec"}
CPU bound-export fixture: /scratch/jjyeung/orch_n30/so_read/work/test-artifacts/94d0bb20e51c4e45a7f4d079a9e636e6
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/apply-round8/7bad3024af544e60b7370835bb10f7cb/src/u0/tests/test_round5.py
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
Ran 7 tests in 9.810s

OK
All CPU receipt checks passed
{"passed": true, "pool_bytes": 75000000}
All CPU receipt checks passed
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/apply-round8/7bad3024af544e60b7370835bb10f7cb/src/u0/tests/test_round6.py
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
Ran 9 tests in 28.841s

OK
README unpack command: exit 0; authenticated partial return accepted.
Detached fill: success=0, failure=17, duplicate launch refused.
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/apply-round8/7bad3024af544e60b7370835bb10f7cb/src/u0/tests/test_round7.py
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
test_rebind_step400_only (__main__.Round7Tests.test_rebind_step400_only) ... ok

----------------------------------------------------------------------
Ran 8 tests in 6.055s

OK
Live namespace tar: regular file and symlink preserved; archive survives namespace loss; duplicate and OFF guarded.
Fill wait: missing token, dead worker, deadline and exit 17 refuse; exit 0 passes; production maximum 14400 seconds.
Only reviewed step-400 export passes; changed artifact and selectable-export API refuse.
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/apply-round8/7bad3024af544e60b7370835bb10f7cb/src/u0/tests/test_round8.py
```

Exact output:

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
Ran 10 tests in 7.329s

OK
Absolute e/heads.pt symlink survives tar/extract; real Artifact.verify and load_native admission pass before model loading.
README GPU block runs d/v/py and refuses each version mismatch or unavailable CUDA; CUDA imports are test doubles.
Runtime torch/transformers/CUDA and environment SHA256 are exact; changed versions, bytes and CPU build refuse.
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/apply-round8/7bad3024af544e60b7370835bb10f7cb/src/u0/tests/test_compare.py
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
Ran 9 tests in 0.295s

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
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/d2bda1c9788a4df5ad4aa198ce664724/u0/a8.py", line 65, in <module>
    raise SystemExit(main())
                     ^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/d2bda1c9788a4df5ad4aa198ce664724/u0/a8.py", line 61, in main
    return launch(rest)
           ^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/d2bda1c9788a4df5ad4aa198ce664724/u0/a4.py", line 2, in main
    from a8 import source_hash
ModuleNotFoundError: No module named 'a8'


======================================================================
FAIL: test_f1_actual_isolated_script_plain_and_opaque (__main__.Round2Tests.test_f1_actual_isolated_script_plain_and_opaque) (opaque=True)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round2.py", line 67, in test_f1_actual_isolated_script_plain_and_opaque
    self.assertEqual(result.returncode,0,result.stdout+result.stderr)
AssertionError: 1 != 0 : Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/05569808ed0c4bc29ac678e99b6be981/u0/a8.py", line 65, in <module>
    raise SystemExit(main())
                     ^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/05569808ed0c4bc29ac678e99b6be981/u0/a8.py", line 56, in main
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
Ran 13 tests in 0.211s

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
AssertionError: 140136670512624 unexpectedly found in {140136670512624, 140136670512944} : Per-call weight hashing

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
Ran 9 tests in 0.818s

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
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/298e8db9916442d28279dfc9f32a1cb2/0.py", line 44, in main
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
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/298e8db9916442d28279dfc9f32a1cb2/0.py", line 18, in dispatch
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
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/298e8db9916442d28279dfc9f32a1cb2/7.py", line 139, in main
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
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/298e8db9916442d28279dfc9f32a1cb2/7.py", line 87, in run
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
Ran 2 tests in 9.253s

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
Ran 2 tests in 0.012s

FAILED (failures=2)
```

```bash
READ_ROUND4_BEFORE=1 bash work/cpu.sh work/run_fixture5.py work/src/u0/tests/test_round4.py
```

Exact output:

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
AssertionError: 1 != 0 : /scratch/jjyeung/orch_n30/so_read/work/test-artifacts/146db46e5ba84dd2807cae082ab5b01c
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 436, in <module>
    elif len(sys.argv)>1 and sys.argv[1]=='--control':control_child(Path(sys.argv[2]),Path(sys.argv[3]),sys.argv[4])
                                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 284, in control_child
    node.main()
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/146db46e5ba84dd2807cae082ab5b01c/built/package/a/5.py", line 147, in main
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
Ran 4 tests in 9.547s

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
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round5.py", line 66, in test_f1_batch_wrapper_and_real_bundle_guard
    self.assertIn('#SBATCH --exclude=orchard-community-2\n',batch)
AssertionError: '#SBATCH --exclude=orchard-community-2\n' not found in "#!/bin/bash\nset -euo pipefail\nexec /usr/bin/python3 -I -s -B - <<'A'\nimport hashlib,io,json,os,sys,tarfile\nfrom pathlib import Path,PurePosixPath\nj=os.environ.get('SLURM_JOB_ID','')\nif not j.isdigit():raise ValueError('Allocation required')\nb=bytes.fromhex('1f8b08000000000002ffed5aeb6fdbba15ef67ff15bad907490eabc8efc4b91ad0b5b95b87db079af602836108b444d96a644913e53c56f47fdf3987942ccb4e9a61d81d8699486c4b240f0fcff3c787eb7c9559fae23f5a5c2863d7a56f77ffdb1d0c27f56ff57e3c990c5e18ee8bdfa16c64c90b18f2c5ff67f9d6318c939c3f24190ffdc54329e4c9d4180d2683d1a4c79a7572c5fba331549e5c4cdcf3b0175d885e6fd41fb90b3e0cc4a277cec7d1f9641cf5fb9351e02e06e164b0182c865c8cfbe717e360310afa9321bfe8f1e044d14d78da201a4617a3453fe80d2f461783e87c38106e6fc4c110c6bd09f4bd80bf68713e70c3de45042ff8c80d841847a1887814c1d08a6899dd8814c9f185dbeb0f86a3f1e4fce2a4f3bdf3e2581ef14d277ff88f8ff1b4ff0f87bd71dbff87a3a3ffff2ee5e4e4e46321a4286e85911759b809ca384b0d1eae6329e11733403ecb385d328327491670aa5e649b3494f02a0d0de8bd494af82a3745ea00bd4ebcceb3a234565cae9278c130c1301072142782c907d9898a6c6de4bcc45a4337fe088f9d4e07fcd958f31be187b18416c1ca2ab2ac644656c4c0044fe0572e0a5e66858e1df6b46310bdac0856bc08fd55cf75826cbd062e356968d83190704d9317cb5bd6854fc9badd9b3bfc81748c3f181fd2e401a602c1291046b982ff2c7f99885b9134a75f1112c525084de4bc50ef511c775971230a89627b30f2384d45e800e938321291d2c8f61fbd3e35c587d9cbfe74ee7933591634d533939f8dc0274d9b355ff5284d9bf61cd9348268e9e1b38391595a7bad9c4240c42ec57d69d93676e012345c62bf99c949c3260cdad3b4666690a551bc34e733b3255e68d67a837df607bc2be252a81189b170b3cea505b4d5f8307be8adbb4d687a3fb509d3cc8c82c75218bff16423ae8a222b2cf34f606a89086bc51ba0e774092f78548a02e55c949bdc54f304897ab32e0976fab23f6fc870f28450a1ab32dfdace0e9a48a76a55e9bf36d838b5d08090b087966c81993bc4456f6e5fe69b4512070734e61ed617c8a310a122649e81577e1541798646bd49e3f2e1ecebd707b1499767d9cd6a62da6796c97b233fc84a9fe7e6a91a6c66522a34e7404e2b5fbba3a3a46d596a1464a25cfea3e281100030e1acc47d182f85048e3cafa2b98b054c90db5d5cae0ceddb0e68286d9385d1b11e951b81eed6469c56cf681569561a6b27e56be190222512b4cc86339f99f614ccb38cd38dd8e9144b1cd4b2416786e93826522691297ab69323bde9be417d49258f841164a15056937b4a1db979a6fa5ee6d859a4a5b3be09e3c2520fd2fb5c6c0413f7b12cfdec869e40b9daf695e4600e0ea8b1002723eed64aae4aad601318f59c384585586ec318c17eedfd405645b0afd9e27951aee5525edbe93a18e3b368c7142b85f1b3e0ecf5c72f874d524bdda2ee68086053a139376269a018289c519db314a5652ec867fde50679d58dedc71a83688b075f8abf6f441a88279ad70688c1eb719bac4ab31f80cd9d4e5bf0099368348cd37c534a6c8aa2db8aa60a1507a9efc7cc4341b3d54dcd7d2dd659f160b26fdf6d2d392e630993f73cc38ce27b11facb4189547221cd83a36b1273d51fc60d448e11dec70a7f0d293d119ae2cc04628f8868978ce46be8cfe5a6106bd08f5f8076e2a252cb2f3c91e21954a2b8945b45da077cf1974d9218607510d445700381358a2079a29cc1e61d7a09222836a9770015b49ab036345044283a637b1bc235d8b1efa38bfbbee799be8f95be6f4e5508ff3f5c264cfeebf8bf37198e077bf87fe21ef1ffef84ff3f54c0aaf22ecad4e55d068e9b25bc1488f1215550b287249ba5a201869b889f903ea43956c66bc134e07802ee7ffaf2ebd5b56799014490388491a40fa069cdef4d66775e7ff8f2fe33d4f6462e6bfe0fc0b1af5fffe5ea0d74f62cc8a2039bc1a74b9f3dfaecd3e7101217e1b350c8a0887398a284541edcf0a520b4a6c0dc2c8c8312f0deda03cc74270a9341cc14d29b9929ccd4440c091d7a90a0128061106812e11de258f25be16777a91f42fc5d791423d9364852694567cf849cc21e09d99e8ed67bf5b7a288a3073f0ea1c9bc3d42f99063d7010359b03e1bce01afe4c037e0c931486eae2422050748ed1372b15035ec1683f2331653d485f0004119024300182907345005553621c44f1e8d7020057c8256461c4296016cdbcc007bdc29ded5824b586acdf20c963f7c7a73f58981c6b2340e78d23120c70a85ae150dc8e09b12f23ea0e54b294a809a4bd984483b4dab06d0781f23a9462af965a4329e98f6410c5aa9c5a8da19843dcc0a068abef091be289c9601d4884f7382109b0ca37ad1d97db4aa1faccae20aba12c7551d4c6ccfcc011a21e8039727473d308d4d7a93a2c91fe88b80176628bda6f75542d45e8802af34ef911b2230f3ea564d94c61434ab2bd5e3b61afda00d7f6bf5b6011a584301eed36314d83c629449c012e8795e155d600a7f30fe7afde13d2cec00d096300b6319df0a90382e3b17893012307fdc2fc02d94b454bb00183d7153642d14aa91b0feaf67d930abc642b9aab6d1001bae89967a06a0aae4106bf8d9db3757ef3fbffdfc37054659ddaba30d4f7adfbe7768fc98e19c507522054660f6c2a259d23e07ad535bb44912e6192e496284b9c12a832979dfbaddda7c0e99c814a91e361e68bf1312cde95e4cec76bfdd280a3773e2fb0659de43b126331f0f82072a6bd0fb1dc441814aaff0ead9ea95f7e57e2054f34609ecd4b5fa7fba7af5c66fa9830cb8dbadb442b6e58122b4f86aa3ac0291a587a22d12adc0593c4791ab2756c5a569b550b4d936fed04b64d9ae240a59090ccec786aa56a998de569ab59901caca721f97a7cd56f5d4ae3f7ff8686e694a180c96726a5bcb9cd212d8846c090ccc74c2044d53cac4373a679a9487e00505df59a9b44bb144198caa9fcfb7e3fc6bb6b5ed067359430e8e5373da3b775d66aabcbe7dd98797ddee6e48d4a2ffdea961805680ca318558095e48d4d1e35906961ca928aa688c7b1445963025284405f2799969ebbcadcc76a9765621c9573e1d444b94a06eef805dae256d3c19a547b49c380dc5bd457b7a5ac23377aeed0bd9a32db90e6d9449afc1aa45c6ab087bd086616faf6444cf73eb7849e2e625fc8ae234962b7ff1e0f5c980f52e13129be18766c57cf9928cc53eedc1b2581bcc93cd9529e9f6644e4f3657d3d4cd99e97ccd6025d714c0d3cce1845e922f2812e81087a1c19e8b6ce9b6b1c2a1712ab7c5617691c3610bf73c4aba1010b6c1f8df1b67cbaf2237db0bb3284288643f6cd88cbed0e7e90c0f33789a00edbea2a53b3ccf451a2a5bd4d153e1d9a63e19d92eedccd6604df1b90b75297b5fddc3c0885a040441430918d7332062a35c415a5fae689b1f464b0c324e4366c18d28d5cea62c370be34ec4cb5589599cdc19f76001f797ce1a1a569eacb6835503e2b3aab886ef44bce76b016bab0091b37a5f6254d8837a35b42383c00c9228df27866b2006125b43738a0c74b201be585ad9e22b0b4509336410bd42b61419586c018988962ce92649aac50ac50c033a3854871f97f884fd3cfca0a730e6cb3493651c20b0b8c4212b154135da13b56f4dd142c9f9389a97f0f522e446974f69ba4e295209b071d67358df613dd775e66496246b12a103846102961280738d5f1f52c838be8f73f47d403df06db39dd62827667e46f5fd79f0d9643a03d0aac17b0f2144b7b7cc06aaaec4e34405ee070500f1ca56d7415f094a3de128e85089bfb5660ba983d46fe3005785f9e6c7cb39c9d7039f4ccdd3ecdb4c192600d45a0187569df861d7fc38ca50150734c9addfa2aa20f02bed52bffd3a455939dbbda714f40f5164d2eab3d1b9cd7097cc33c1566c3a29d2695279aace929b54fb3b039b503982a9ac48526741022c7ab819e0e0c733b2283ce17246dc8b6083ebcc67af46f1708d188095660f8f0470e5422f60ae07579db41482917850260f6a5343ca78994278c07ea6fda3c48ccbefcb88c7c9a65056a6d33441589791e9e09a108560d97ff440462f11a12077cfcd31f5027bba00cbbbe9a8b3bf2d58ac63a767694102712d3d1bd3a0d60aea076611c5f72a96aadf2a39ead93c33fa76bbaa3d396e1ce9de33530b02d68c5af85505680cc2430935e44b95c0f6fa5dea19aa25d916f4a4244f10280675a6d72f77d0a2509111abf514889f998914302fa9d4a9870f3d589159c5961f3cbed812008a4a1630f821496cc9d4bfb6e926adabb7b59e97d2a1cf660d4054af6e9fc90bf260ef24b3f62e4f3d1c4f92269d03642a79eb6fbde2a54f083bcb351d6c69f9d59b2e8f59e7f59777ef5e7daa163c7a6edb7351fd429f8ad251804f5705ac2e03a7caa1119893753e6476f33a813a3bf300a7777b6e7fd8ed0e1871ef036e818c012da4de4e53afd532477572d120f4e954abcf74bf3135454bb6da75744aa1763bcaca82dd9fbd76b39fbddeb862922c712fb0bc4d213ac76acbd4a09e5a12ead28449b0e4173cd9312057295c0e21686a7008cd906c8df1d0c801cd9049d2b6da006f0b00c2298c650180c931ae108f18c40f12cb11b4c07a921740ed16ef1e2c32c8a71100c55213538410e844a0015d077491a0a1f48bf8061294678d87dd8bd3f1f074d087bfeea8477fa7a3de69dfee9e7770345fabd283f6a74a18fd0e866e0cf23eeaf50e18161e50d2a2aabd7ac7a52a834819254aa5a3b4db18a165f7d42c4f36d207998192f1644af5b2d2d381fd444fc087d074132ec5a33d4ef72670ba6f248d90b4dd58a926821709ea1b02304f3acbf3f68ff17e08117679576771b5805cf6d8e19c76121c49b3a4baf81b8867056aab45397f2857c0031acdaa3efdf79b1ad6da655b795794832c8f819b418be49e1035d77beff1f4ce576aa106ed70b013a876c7e876ad6f665b37e69ebb7f57e9692726180224647cfb6eb748e24965154cf76cc59cffbcc75e3bceda9d9da89717d9a2b9457d7272f29a4e38d562a3e471aa0300450542c0e087062eee604583114869181fae5fbda3539667a2a17f6f0b7bbb21fcd8aedafca7ca500f5fae006b036e9a377668d7bade94ebe82d6fb55bd9da356fe96b7b7a4c37485a1be35b8dd7bb305bf533bc4b024f124100cfbd4655bd236ee3f0b8e4a58d29dd7e5beb10d0c6e30d321b481f35eb75206b2629da1cdbcb3a3038a5488269bb59b1abc9fd30f1d6b0f0ddd5bb0f7502d648ac910035a6c273f743daf958ab54e944dc07428492c26395a6e8ae84bd07f8776f3ab56ea0eddd79dab1abcb5c9fb6443b1b03db1b31b3a93b5757e0f23373a16f69c1cfb210a27ac2e08ab6d2bcaef60c93397ce906686f5cba72a36c8a9f570684b7e36e7949eb25fdd31229eef5d7a7263ff04218a884688121201052aa4b309dc3af0f0a4e66c9adb06c7d05c9aea65d4d56ef4caa35fcf322c28e71b5eefb6d6decd3d55fae5e7dba7ef56b6d5df52668b34f05fc0f684227255fdf02b1a7bbd170874a7de7aede12c964ed25b4b26c3667f404a01c7e66d211e96d5c64e9cc7cfde5cd2bffb7b7d76ffff4eb95ffe6eab7b7afafae811b992731f0c348c5ca0dae1f6429d657f7f0be7778dda27cdc3e5e123996633996633996633996633996633996633996633996633996633996633996633996633996633996633996ffbdf24fc3695a7200500000')\nr=Path('/tmp')/('a'+j+'ab0123456789')\nr.mkdir(mode=0o700)\nwith tarfile.open(fileobj=io.BytesIO(b)) as a:\n    for e in a:\n        n=PurePosixPath(e.name)\n        if n.is_absolute() or '..' in n.parts or not e.isfile():raise ValueError('Unsafe input')\n        p=r/e.name;p.parent.mkdir(parents=True,exist_ok=True)\n        with a.extractfile(e) as i,p.open('xb') as o:o.write(i.read())\nos.chdir(r)\nos.execv(sys.executable,[sys.executable,'-I','-s','-B',str(r/'0.py'),str(r)])\nA\n"

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
Ran 7 tests in 5.098s

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
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 126, in test_f1_readme_unpack_subprocess
    self.assertEqual(result.returncode,0,result.stderr)
AssertionError: 1 != 0 : Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/9db12c62fbbe4f13a631c1f7aa6e01aa/step600/unpack_return.py", line 3, in <module>
    from fetch_return import digest as file_digest, validate_exit
ModuleNotFoundError: No module named 'fetch_return'


======================================================================
FAIL: test_f2_detached_locked_fill_exit_success_and_failure (__main__.Round6Tests.test_f2_detached_locked_fill_exit_success_and_failure)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 138, in test_f2_detached_locked_fill_exit_success_and_failure
    self.assertIn('nohup bash',text,'Pull/fill still runs in the foreground')
AssertionError: 'nohup bash' not found in '#!/bin/bash\nset -euo pipefail\numask 077\nD=$(cd -- "$(dirname -- "$0")" && pwd)\nP=/project/community/jjyeung/okh7/a15_cot_apab0123456789\nexport TZ=UTC CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud CLOUDSDK_CORE_DISABLE_PROMPTS=1\nE=$P/a/e\ntest ! -e "$E"\nmkdir -m 700 "$E"\nOBJECT=q8/8865619b/673bc60f_m600.tar\ncp /project/community/jjyeung/okh7/abcdef/5 "$E/5"\ntest "$(cat "$E/5")" = \'q8/8865619b/673bc60f_m600.tar 4 2222222222222222222222222222222222222222222222222222222222222222\'\ncp /project/community/jjyeung/okh7/abcdef/7 "$E/7"\ntest "$(sha256sum "$E/7" | cut -d\' \' -f1)" = 3b0051c4a9cc661d02019a645165fc3e23d658d2f24a6fd6fd86ec7877ba4fc1\ncp /project/community/jjyeung/okh7/abcdef/8 "$E/8"\ntest "$(sha256sum "$E/8" | cut -d\' \' -f1)" = 4c0dd9d6e4535a2945ed58754c1cdd5e9a316067be35f2e8440caa9a80e1c915\ncp /project/community/jjyeung/okh7/abcdef/9 "$E/9"\ntest "$(sha256sum "$E/9" | cut -d\' \' -f1)" = 7f654d2f0ae9f06083f2fc8fd793512c154b4d01ce8632fb733d4191205af770\nfor i in 0 1 2 3; do\n  test ! -e "$E/$i"\n  gsutil -o Boto:num_retries=0 -o Boto:metadata_service_num_attempts=1 -o GSUtil:parallel_process_count=1 -o GSUtil:parallel_thread_count=1 -o GSUtil:sliced_object_download_threshold=0 -o GSUtil:sliced_object_download_max_components=1 -q cp "gs://cmu-gpucloud-jjyeung/$OBJECT.part0$i-of-04" "$E/$i.partial"\n  mv "$E/$i.partial" "$E/$i"\ndone\n/usr/bin/python3 -I -s -B "$P/a/4.py" --parts "$E/0" "$E/1" "$E/2" "$E/3" --done "$E/5" --object "$OBJECT" --config "$E/7" --receipt "$E/8" --data-receipt "$E/9" --lineage SFT --step 600 --out "$P/a/export.json" --prep-tar "$P/a/6" --base-inputs "$P/a/0.json" --inputs-out "$P/a/1.json"\nPREP=$(sha256sum "$P/a/6" | cut -d\' \' -f1)\n/usr/bin/python3 -I -s -B "$D/d.py" "$P/a/1.json" "$P/a/0.json" "$PREP" > "$P/a/dry.json"\n(cd "$P" && CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 04:30:00)\n/usr/bin/python3 -I -s -B "$D/d2.py" "$P" "$P/a/w2" > "$P/a/dry2.json"\nprintf \'%s\\n\' 0 > "$P/a/1.txt"\n' : Pull/fill still runs in the foreground

======================================================================
FAIL: test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks) (field='bundle_guard.batch_sha256')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 178, in test_f3_full_cont_ops_receipt_checks
    self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'Unbound CPU receipt field: '+key)
AssertionError: 0 == 0 : Unbound CPU receipt field: batch_sha256

======================================================================
FAIL: test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks) (field='bundle_guard.path')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 178, in test_f3_full_cont_ops_receipt_checks
    self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'Unbound CPU receipt field: '+key)
AssertionError: 0 == 0 : Unbound CPU receipt field: path

======================================================================
FAIL: test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks) (field='entry_sequence.events')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 178, in test_f3_full_cont_ops_receipt_checks
    self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'Unbound CPU receipt field: '+key)
AssertionError: 0 == 0 : Unbound CPU receipt field: events

======================================================================
FAIL: test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks) (field='entry_sequence.guard_target_sha256')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 178, in test_f3_full_cont_ops_receipt_checks
    self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'Unbound CPU receipt field: '+key)
AssertionError: 0 == 0 : Unbound CPU receipt field: guard_target_sha256

======================================================================
FAIL: test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks) (field='entry_sequence.requested_argv')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 178, in test_f3_full_cont_ops_receipt_checks
    self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'Unbound CPU receipt field: '+key)
AssertionError: 0 == 0 : Unbound CPU receipt field: requested_argv

======================================================================
FAIL: test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks) (field='entry_sequence.dispatched_argv')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 178, in test_f3_full_cont_ops_receipt_checks
    self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'Unbound CPU receipt field: '+key)
AssertionError: 0 == 0 : Unbound CPU receipt field: dispatched_argv

======================================================================
FAIL: test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks) (field='entry_sequence.batch_sha256')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 178, in test_f3_full_cont_ops_receipt_checks
    self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'Unbound CPU receipt field: '+key)
AssertionError: 0 == 0 : Unbound CPU receipt field: batch_sha256

======================================================================
FAIL: test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks) (field='memory.perception_memo_modules')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 178, in test_f3_full_cont_ops_receipt_checks
    self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'Unbound CPU receipt field: '+key)
AssertionError: 0 == 0 : Unbound CPU receipt field: perception_memo_modules

======================================================================
FAIL: test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks) (field='memory.sam_measurement_required')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 178, in test_f3_full_cont_ops_receipt_checks
    self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'Unbound CPU receipt field: '+key)
AssertionError: 0 == 0 : Unbound CPU receipt field: sam_measurement_required

======================================================================
FAIL: test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 180, in test_f3_full_cont_ops_receipt_checks
    self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'MEMORY.json differs')
AssertionError: 0 == 0 : MEMORY.json differs

======================================================================
FAIL: test_f4_every_copied_a4_member_pinned_before_output (__main__.Round6Tests.test_f4_every_copied_a4_member_pinned_before_output) (member='package/BATCH.sh')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 193, in test_f4_every_copied_a4_member_pinned_before_output
    with self.assertRaisesRegex(ValueError,'A4 member pin|A4 batch pin'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f4_every_copied_a4_member_pinned_before_output (__main__.Round6Tests.test_f4_every_copied_a4_member_pinned_before_output) (member='package/3.py')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 193, in test_f4_every_copied_a4_member_pinned_before_output
    with self.assertRaisesRegex(ValueError,'A4 member pin|A4 batch pin'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f4_every_copied_a4_member_pinned_before_output (__main__.Round6Tests.test_f4_every_copied_a4_member_pinned_before_output) (member='package/a/0.json')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 193, in test_f4_every_copied_a4_member_pinned_before_output
    with self.assertRaisesRegex(ValueError,'A4 member pin|A4 batch pin'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f4_every_copied_a4_member_pinned_before_output (__main__.Round6Tests.test_f4_every_copied_a4_member_pinned_before_output) (member='package/a/4.py')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 193, in test_f4_every_copied_a4_member_pinned_before_output
    with self.assertRaisesRegex(ValueError,'A4 member pin|A4 batch pin'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f4_every_copied_a4_member_pinned_before_output (__main__.Round6Tests.test_f4_every_copied_a4_member_pinned_before_output) (member='package/a/7.py')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 193, in test_f4_every_copied_a4_member_pinned_before_output
    with self.assertRaisesRegex(ValueError,'A4 member pin|A4 batch pin'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f4_every_copied_a4_member_pinned_before_output (__main__.Round6Tests.test_f4_every_copied_a4_member_pinned_before_output) (member='fetch_return.py')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 193, in test_f4_every_copied_a4_member_pinned_before_output
    with self.assertRaisesRegex(ValueError,'A4 member pin|A4 batch pin'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f4_every_copied_a4_member_pinned_before_output (__main__.Round6Tests.test_f4_every_copied_a4_member_pinned_before_output)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 201, in test_f4_every_copied_a4_member_pinned_before_output
    with self.assertRaisesRegex(ValueError,'bootstrap pin'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f5_checkpoint_binding_and_runtime_recheck (__main__.Round6Tests.test_f5_checkpoint_binding_and_runtime_recheck) (asset='RESTORE.json')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 221, in test_f5_checkpoint_binding_and_runtime_recheck
    with self.assertRaises(ValueError):selected_gate(self.helper,args)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f5_checkpoint_binding_and_runtime_recheck (__main__.Round6Tests.test_f5_checkpoint_binding_and_runtime_recheck) (asset='binding.json')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 221, in test_f5_checkpoint_binding_and_runtime_recheck
    with self.assertRaises(ValueError):selected_gate(self.helper,args)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f5_checkpoint_binding_and_runtime_recheck (__main__.Round6Tests.test_f5_checkpoint_binding_and_runtime_recheck)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 224, in test_f5_checkpoint_binding_and_runtime_recheck
    with self.assertRaisesRegex(ValueError,'export identity|export pin'):selected_gate(self.helper,args)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f5_production_device_is_required (__main__.Round6Tests.test_f5_production_device_is_required)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 238, in test_f5_production_device_is_required
    self.assertTrue(hasattr(self.kit,'validate_device'),'GPU name is recorded but never required')
AssertionError: False is not true : GPU name is recorded but never required

======================================================================
FAIL: test_f5_runtime_asset_recheck (__main__.Round6Tests.test_f5_runtime_asset_recheck)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 228, in test_f5_runtime_asset_recheck
    self.assertTrue(hasattr(self.kit,'validate_assets'),'Gate lacks runtime asset authentication')
AssertionError: False is not true : Gate lacks runtime asset authentication

======================================================================
FAIL: test_info_done_whitespace (__main__.Round6Tests.test_info_done_whitespace)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 250, in test_info_done_whitespace
    self.assertNotIn('test "$(cat "$E/5")" =',text,'Whitespace-only receipt changes still refuse')
AssertionError: 'test "$(cat "$E/5")" =' unexpectedly found in '#!/bin/bash\nset -euo pipefail\numask 077\nD=$(cd -- "$(dirname -- "$0")" && pwd)\nP=/project/community/jjyeung/okh7/a15_cot_apab0123456789\nexport TZ=UTC CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud CLOUDSDK_CORE_DISABLE_PROMPTS=1\nE=$P/a/e\ntest ! -e "$E"\nmkdir -m 700 "$E"\nOBJECT=q8/8865619b/673bc60f_m600.tar\ncp /project/community/jjyeung/okh7/abcdef/5 "$E/5"\ntest "$(cat "$E/5")" = \'q8/8865619b/673bc60f_m600.tar 4 2222222222222222222222222222222222222222222222222222222222222222\'\ncp /project/community/jjyeung/okh7/abcdef/7 "$E/7"\ntest "$(sha256sum "$E/7" | cut -d\' \' -f1)" = 3b0051c4a9cc661d02019a645165fc3e23d658d2f24a6fd6fd86ec7877ba4fc1\ncp /project/community/jjyeung/okh7/abcdef/8 "$E/8"\ntest "$(sha256sum "$E/8" | cut -d\' \' -f1)" = 4c0dd9d6e4535a2945ed58754c1cdd5e9a316067be35f2e8440caa9a80e1c915\ncp /project/community/jjyeung/okh7/abcdef/9 "$E/9"\ntest "$(sha256sum "$E/9" | cut -d\' \' -f1)" = 7f654d2f0ae9f06083f2fc8fd793512c154b4d01ce8632fb733d4191205af770\nfor i in 0 1 2 3; do\n  test ! -e "$E/$i"\n  gsutil -o Boto:num_retries=0 -o Boto:metadata_service_num_attempts=1 -o GSUtil:parallel_process_count=1 -o GSUtil:parallel_thread_count=1 -o GSUtil:sliced_object_download_threshold=0 -o GSUtil:sliced_object_download_max_components=1 -q cp "gs://cmu-gpucloud-jjyeung/$OBJECT.part0$i-of-04" "$E/$i.partial"\n  mv "$E/$i.partial" "$E/$i"\ndone\n/usr/bin/python3 -I -s -B "$P/a/4.py" --parts "$E/0" "$E/1" "$E/2" "$E/3" --done "$E/5" --object "$OBJECT" --config "$E/7" --receipt "$E/8" --data-receipt "$E/9" --lineage SFT --step 600 --out "$P/a/export.json" --prep-tar "$P/a/6" --base-inputs "$P/a/0.json" --inputs-out "$P/a/1.json"\nPREP=$(sha256sum "$P/a/6" | cut -d\' \' -f1)\n/usr/bin/python3 -I -s -B "$D/d.py" "$P/a/1.json" "$P/a/0.json" "$PREP" > "$P/a/dry.json"\n(cd "$P" && CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 04:30:00)\n/usr/bin/python3 -I -s -B "$D/d2.py" "$P" "$P/a/w2" > "$P/a/dry2.json"\nprintf \'%s\\n\' 0 > "$P/a/1.txt"\n' : Whitespace-only receipt changes still refuse

======================================================================
FAIL: test_info_submit_requires_successful_bound_gpu_gate (__main__.Round6Tests.test_info_submit_requires_successful_bound_gpu_gate) (field='passed')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 267, in test_info_submit_requires_successful_bound_gpu_gate
    with self.subTest(field=key):self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'GPU evidence ignored')
                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 0 == 0 : GPU evidence ignored

======================================================================
FAIL: test_info_submit_requires_successful_bound_gpu_gate (__main__.Round6Tests.test_info_submit_requires_successful_bound_gpu_gate) (field='adoption_plan_sha256')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 267, in test_info_submit_requires_successful_bound_gpu_gate
    with self.subTest(field=key):self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'GPU evidence ignored')
                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 0 == 0 : GPU evidence ignored

======================================================================
FAIL: test_info_submit_requires_successful_bound_gpu_gate (__main__.Round6Tests.test_info_submit_requires_successful_bound_gpu_gate) (field='required_device_type')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 267, in test_info_submit_requires_successful_bound_gpu_gate
    with self.subTest(field=key):self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'GPU evidence ignored')
                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 0 == 0 : GPU evidence ignored

======================================================================
FAIL: test_info_submit_requires_successful_bound_gpu_gate (__main__.Round6Tests.test_info_submit_requires_successful_bound_gpu_gate) (field='adoption_assets')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 267, in test_info_submit_requires_successful_bound_gpu_gate
    with self.subTest(field=key):self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'GPU evidence ignored')
                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 0 == 0 : GPU evidence ignored

======================================================================
FAIL: test_info_submit_requires_successful_bound_gpu_gate (__main__.Round6Tests.test_info_submit_requires_successful_bound_gpu_gate) (field='adoption_profile')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 267, in test_info_submit_requires_successful_bound_gpu_gate
    with self.subTest(field=key):self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'GPU evidence ignored')
                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 0 == 0 : GPU evidence ignored

======================================================================
FAIL: test_info_submit_requires_successful_bound_gpu_gate (__main__.Round6Tests.test_info_submit_requires_successful_bound_gpu_gate)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 269, in test_info_submit_requires_successful_bound_gpu_gate
    self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0)
AssertionError: 0 == 0

----------------------------------------------------------------------
Ran 9 tests in 38.393s

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
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round7.py", line 162, in test_rebind_step400_only
    self.assertIn('bound_export',inspect.signature(self.helper.gate).parameters,'Gate lacks reviewed export binding')
AssertionError: 'bound_export' not found in mappingproxy(OrderedDict({'operator': <Parameter "operator">, 'prepared': <Parameter "prepared">, 'proof': <Parameter "proof">, 'config_template': <Parameter "config_template">, 'settings_out': <Parameter "settings_out">, 'config_out': <Parameter "config_out">, 'asset_receipts': <Parameter "asset_receipts=None">})) : Gate lacks reviewed export binding

----------------------------------------------------------------------
Ran 8 tests in 2.718s

FAILED (failures=10)
```

```bash
READ_ROUND8_BEFORE=1 bash work/cpu.sh work/run_fixture5.py work/src/u0/tests/test_round8.py
```

Exact output:

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
ValueError: restore input missing from artifact: /scratch/jjyeung/orch_n30/so_read/work/test-artifacts/823db48b3d6543e29186165905d36b44/logical/d/e/heads.pt

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 69, in test_f1_preserved_absolute_link_passes_real_artifact_and_load_native
    except ValueError as error:self.fail('Real load_native rejected extracted link: '+str(error))
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Real load_native rejected extracted link: restore input missing from artifact: /scratch/jjyeung/orch_n30/so_read/work/test-artifacts/823db48b3d6543e29186165905d36b44/logical/d/e/heads.pt

======================================================================
FAIL: test_f2_gate_authenticates_environment_before_gpu (__main__.Round8Tests.test_f2_gate_authenticates_environment_before_gpu)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 157, in test_f2_gate_authenticates_environment_before_gpu
    self.assertIn('environment',inspect.getsource(self.helper.gate),'Gate omits CPU environment receipt binding')
AssertionError: 'environment' not found in "def gate(operator, prepared, proof, config_template, settings_out, config_out, asset_receipts=None, bound_export=None):\n    package, public, cfg = package_config(operator)\n    receipt = read(proof); raw = Path(prepared).read_bytes()\n    if (receipt.get('passed') is not True or receipt['plan'] != public['plan_sha256']\n            or receipt['payload'] != public['payload_sha256'] or receipt['ready']['settings'] != sha(raw)\n            or receipt['operator_sha256'] != sha((package/'a/6.py').read_bytes())):\n        raise ValueError('Prepared settings proof differs from adopted package')\n    settings = json.loads(raw)\n    spec = importlib.util.spec_from_file_location('adopted_operator', package/'a/6.py')\n    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)\n    descriptor, = module.descriptors(str(package))\n    for key in PROFILE_KEYS[:5]:settings[key] = descriptor[key]\n    expected = {key:cfg[key] for key in PROFILE_KEYS}\n    if {key:settings.get(key) for key in PROFILE_KEYS} != expected:\n        raise ValueError('Prepared/adopted read profile differs')\n    slots = [i for i,name in enumerate(('processor','vision','sam')) if settings['read_'+name+'_cache']=='on']\n    config = read(config_template)\n    paths = (dict(restore=Path(asset_receipts)/'RESTORE.json',binding=Path(asset_receipts)/'binding.json',\n                  export_pin=Path(asset_receipts)/'EXPORT_PIN.json') if asset_receipts else\n             dict(restore=Path(config['export'])/'RESTORE.json',binding=Path(config['artifact_manifest']),\n                  export_pin=Path(config['export_pin'])))\n    assets = {key:sha(path.read_bytes()) for key,path in paths.items()}\n    inputs_path = Path(asset_receipts)/'1.json' if asset_receipts else package/'a/1.json'\n    if sha(inputs_path.read_bytes()) != receipt['inputs']:\n        raise ValueError('Gate input evidence differs from CPU proof')\n    export_pin = read(inputs_path)['export_pin']\n    if (export_pin['path'] != 'a/export.json' or assets['export_pin'] != export_pin['sha256']\n            or paths['export_pin'].stat().st_size != export_pin['bytes']):\n        raise ValueError('Staged export pin bytes differ from CPU inputs')\n    if any(assets[key] != receipt['ready'][key] for key in ('restore','binding')):\n        raise ValueError('Staged assets differ from CPU READY pins')\n    identity = read(paths['export_pin']); binding = cfg['export_binding']\n    if any(identity.get(key) != binding[key] for key in\n           ('run','step','member_directory','lineage','object','config_sha256','archive_sha256')) or any(\n            identity.get('preparation',{}).get(key,{}).get('sha256') != digest\n            for key,digest in binding['preparation_sha256'].items()):\n        raise ValueError('Staged export identity differs from adopted step binding')\n    selected = read(bound_export) if bound_export else DEFAULT_BOUND_EXPORT\n    if identity != selected:\n        raise ValueError('Staged export differs from selected export (default: reviewed step 400)')\n    config.update(enable_caches=slots, read_cache_bytes=settings['read_cache_bytes'],\n                  adoption_profile=expected, adoption_plan_sha256=public['plan_sha256'],\n                  adoption_kit=cfg['gate_kit_sha256'],\n                  adoption_assets=assets, required_device_type='H100_80GB')\n    write(settings_out, settings); write(config_out, config)\n    return config\n" : Gate omits CPU environment receipt binding

======================================================================
FAIL: test_f2_gpu_shell_preflight_executes_archived_interpreter (__main__.Round8Tests.test_f2_gpu_shell_preflight_executes_archived_interpreter)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 127, in test_f2_gpu_shell_preflight_executes_archived_interpreter
    self.assertIn('# BEGIN GPU_ENVIRONMENT',text,'GPU shell preflight is missing')
AssertionError: '# BEGIN GPU_ENVIRONMENT' not found in 'The GPU kit is unrun. It requires zero answer/trace byte differences. Its 50 items cover ten items per type and twelve captures; this reuse-heavy sample does not predict full-read throughput.\n\nUse the full **A4/src** base pinned by `BASE_PIN.json`. The reader patches also apply to the inspected B5 source subset, but this kit does not authenticate a B5 base. Apply patches 01–03 to a separate source copy. They add `u0/`; all original reader files remain byte-identical. Apply 04–05 to a separate A4 operator copy, outside `src`.\n\nThe ordinary entrypoint stays OFF and imports no extension. `u0/a8.py --enable-extensions` explicitly selects the extensions; individual cache settings then default OFF. The ON environment records an extension source hash. Rebuild payload and artifact pins before deployment.\n\n## Local preparation\n\nThese commands use paths supplied by the operator; they do not depend on the author\'s `work/` directory. Set `DELIVERY` to the delivered `out/`, `A4_BASE` to the full supplied A4 directory on local scratch, `LOCAL` to a fresh local scratch directory, and `READ_PYTHON` to the approved Python executable. Both source roots and all outputs must stay on local scratch. The package contains code, not model/data archives.\n\n```bash\nset -euo pipefail\n: "${DELIVERY:?Absolute path to delivered out directory}"\n: "${A4_BASE:?Absolute path to the full pinned A4 directory on local scratch}"\n: "${LOCAL:?Fresh local scratch directory}"\n: "${READ_PYTHON:?Approved Python executable}"\nexport PYTHONDONTWRITEBYTECODE=1 TOKENIZERS_PARALLELISM=false\nexport OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8\nexport XDG_CACHE_HOME="$LOCAL/cache" HF_HOME="$LOCAL/cache/hf" TRITON_CACHE_DIR="$LOCAL/cache/triton"\nmkdir -p "$LOCAL/source" "$LOCAL/a4"\nnice -n 10 tar -cf - -C "$A4_BASE/src" . | nice -n 10 tar -xf - -C "$LOCAL/source"\nnice -n 10 tar -cf - -C "$A4_BASE" package tower_sequence.py fetch_return.py unpack_return.py |\n  nice -n 10 tar -xf - -C "$LOCAL/a4"\nnice -n 10 patch --batch --fuzz=0 -p1 -d "$LOCAL/source" < "$DELIVERY/patches/01_bounded_read_caches.diff"\nnice -n 10 patch --batch --fuzz=0 -p1 -d "$LOCAL/source" < "$DELIVERY/patches/02_atomic_scene_shards.diff"\nnice -n 10 patch --batch --fuzz=0 -p1 -d "$LOCAL/source" < "$DELIVERY/patches/03_production_integration.diff"\nnice -n 10 patch --batch --fuzz=0 -p1 -d "$LOCAL/a4" < "$DELIVERY/patches/04_operator_cache_bound.diff"\nnice -n 10 patch --batch --fuzz=0 -p1 -d "$LOCAL/a4" < "$DELIVERY/patches/05_operator_return_and_proof.diff"\nEXT_SOURCE="$LOCAL/source"\n```\n\nKeep the private kit, original manifests and reverse maps on Trinity. Stage each source tree as one archive and extract it only on node-local scratch. Both parity source roots must remain pristine: no build outputs, extra files or symlinks. Public paths, submission names, configuration and logs must use opaque tokens. Never transfer private reverse maps to Orchard.\n\n## Bound export, build and operations\n\nThe candidate uses **A4\'s 636-item schedule, one card, caches only, general/no-requeue**. A4\'s export admission, submit helper and run settings remain intact. `a19` requires the reviewed payload hash `4498fca72a8e4b476b38f097ffdf3ff88b5aa20fc036bd196b18a5706e9fe46d`, the patched operator hashes, all copied A4 members, the base BATCH.sh and decoded bootstrap pins from MANIFEST, the exact extension inventory and the four original alias bases. It authenticates them before copying. Its batch uses cont_ops\' exact `build_r10.wrap_batch`: excluded node, EXIT log return and USR1 forwarding.\n\nThe gate defaults to **step 400**, read A of job **173060**, source package **a15_cot_apdc76460c3a164**. Its artifact SHA256 is **5083243cfedd2a389dfca579c5452e7d0c73b03a58e1cb7d204292ddd10e67cd**. `operations/BOUND_EXPORT.json` preserves the supplied export pin. `operations/binding.default.json` combines that identity, the four archive-part sizes in the supplied `a/1.json`, and the reviewed `bind400_partial.json` operation paths. `DEFAULT_EXPORT_PROVENANCE.json` records all source hashes. These are authenticated metadata; production weights were not restored here.\n\n`BOUND_EXPORT` selects the gate\'s exact reviewed export.json; `EXPORT_BINDING` selects the matching build/fill binding. For another reviewed export, including step 600, supply both parameters. The gate refuses a package whose export differs from the selected pin. A fresh package token identifies the ON build; it does not reuse the source package\'s token.\n\n```bash\nset -euo pipefail\nBOUND_EXPORT=${BOUND_EXPORT:-"$DELIVERY/operations/BOUND_EXPORT.json"}\nEXPORT_BINDING=${EXPORT_BINDING:-"$DELIVERY/operations/binding.default.json"}\n: "${PACKAGE_TOKEN:?Fresh 11-16 hex characters starting with a-f}"\nPROFILE_ARGS=()  # All three caches, 12 GiB. For processor-only: PROFILE_ARGS=(--processor-only)\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a19.py" \\\n  --enable-extensions --base-operator "$LOCAL/a4" --source-root "$EXT_SOURCE" \\\n  --manifest "$DELIVERY/patches/MANIFEST.json" --extension-pins "$DELIVERY/kit_parity50/EXTENSION_PINS.json" \\\n  --export-binding "$EXPORT_BINDING" --token "$PACKAGE_TOKEN" --out "$LOCAL/adopted" "${PROFILE_ARGS[@]}"\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a20.py" --enable-extensions operations \\\n  --operator "$LOCAL/adopted" --binding "$EXPORT_BINDING" --dry-root "$DELIVERY/operations" --out "$LOCAL/ops"\nnice -n 10 tar -czf "$LOCAL/0.tgz" -C "$LOCAL/ops" .\nnice -n 10 sha256sum "$LOCAL/0.tgz"\n```\n\nFor a different target, derive `EXPORT_BINDING` from its reviewed template and authenticated local receipts before the build block above, and set `BOUND_EXPORT` to that target\'s reviewed export.json:\n\n```bash\nset -euo pipefail\n: "${TARGET_TEMPLATE:?Reviewed target template, including Orchard done and prep_paths}"\n: "${TARGET_ARTIFACT:?Authenticated local artifact.json}"\n: "${TARGET_DONE:?Authenticated local whole-tar done receipt}"\n: "${TARGET_CONFIG:?Authenticated preparation config.json}"\n: "${TARGET_RECEIPT:?Authenticated preparation receipt}"\n: "${TARGET_DATA_RECEIPT:?Authenticated data receipt}"\n: "${EXPORT_BINDING:?Fresh output binding path for the selected target}"\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a20.py" --enable-extensions binding \\\n  --template "$TARGET_TEMPLATE" --artifact "$TARGET_ARTIFACT" --done "$TARGET_DONE" \\\n  --config "$TARGET_CONFIG" --receipt "$TARGET_RECEIPT" --data-receipt "$TARGET_DATA_RECEIPT" \\\n  --out "$EXPORT_BINDING"\n```\n\n`adopted` retains the exact local source/operator/unpacker. `ops/1.tgz` is the package delivery, with `ops/SHA256`; the outer archive carries it and five inert scripts. The commands below are **owner operations on Orchard, unrun here**. Transfer the single outer archive through the owner\'s existing authorized transport. Set `OPS_ARCHIVE` to its received opaque path, `OPS_SHA256` to the printed local hash, and `D` to a fresh opaque operation directory. These are transport endpoints, not generated receipt values.\n\n```bash\nset -euo pipefail\n: "${OPS_ARCHIVE:?Received outer archive on Orchard}"\n: "${OPS_SHA256:?Printed local SHA256 of that archive}"\n: "${D:?Fresh opaque operation directory on Orchard}"\n: "${PACKAGE_TOKEN:?Copy the fresh build token to this Orchard shell}"\nprintf \'%s  %s\\n\' "$OPS_SHA256" "$OPS_ARCHIVE" | sha256sum -c -\ntest ! -e "$D"\nmkdir -m 700 "$D"\ntar -xzf "$OPS_ARCHIVE" -C "$D"\nbash "$D/o_place.sh"\nbash "$D/o_pull_fill.sh"\n# BEGIN FILL_WAIT\n: "${PACKAGE_TOKEN:?Copy the fresh build token to this Orchard shell}"\nP=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}\nFILL_MAX_SECONDS=${FILL_MAX_SECONDS:-14400}\n[[ "$FILL_MAX_SECONDS" =~ ^[0-9]+$ ]] && (( FILL_MAX_SECONDS >= 1 && FILL_MAX_SECONDS <= 14400 )) || exit 1\nFILL_DEADLINE=$((SECONDS + FILL_MAX_SECONDS))\nwhile test ! -f "$P/a/1.txt"; do\n  FILL_PID=$(cat "$P/a/0.txt") || exit 1\n  [[ "$FILL_PID" =~ ^[1-9][0-9]*$ ]] || exit 1\n  if ! kill -0 "$FILL_PID" 2>/dev/null && test ! -f "$P/a/1.txt"; then\n    echo \'Fill worker is gone without an exit receipt\' >&2; exit 1\n  fi\n  if (( SECONDS >= FILL_DEADLINE )); then\n    echo \'Fill wait exceeded its maximum\' >&2; exit 1\n  fi\n  FILL_REMAIN=$((FILL_DEADLINE - SECONDS))\n  sleep "$(( FILL_REMAIN < 60 ? FILL_REMAIN : 60 ))"\ndone\ntest "$(cat "$P/a/1.txt")" = 0\n# END FILL_WAIT\nbash "$D/o_cpu.sh"\n```\n\n`o_place.sh` verifies the inner archive and places it at `$P=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}`. `o_pull_fill.sh` acquires the permanent attempt lock `$P/a/0.lock`, launches one detached nohup worker, and returns its PID in `$P/a/0.txt`. The worker logs to `$P/a/0.log` and writes its exit status to `$P/a/1.txt` on success or failure. Run the wait on the same host that launched the detached worker. It checks at most once per minute, refuses a vanished PID without `1.txt`, and stops after at most 14,400 seconds (four hours). A duplicate launch refuses; a failed or interrupted attempt requires a fresh package/token, never an automatic retry. The worker copies the reviewed `done` and `prep_paths` files to `$P/a/e/{5,7,8,9}`, authenticates their pins (the `.done` receipt uses whitespace-separated fields), fetches export parts `0..3` once with retries disabled, fills through `a/4.py`, and runs cont_ops\' verbatim `dryres2.py` and `dry2.py`. A failed transfer stops; the scripts do not retry it.\n\n`o_cpu.sh` requests the A4 CPU allocation explicitly: preempt, eight CPUs, 200G, four hours, no GPU, no requeue, and the excluded nodes. The **CPU allocation** is separate from the intended **general GPU read**. Wait for the CPU job to finish successfully. Preserve `$P/a/c/CPU.json`, `MEMORY.json` and the exact `SETTINGS.json` emitted by A4 prepare. Bring these small files back as one archive through the authorized transport to `$LOCAL/adopted/proof/` before the parity preparation below. Before writing CPU.json, the ON proof streams `logical/d` through its live `J.namespace(root)` to the named shared staging path `$P/a/4.tar`, outside the capped return pool. It dereferences symlinks and records `gate_assets.path`, `logical`, `sha256` and `bytes` in CPU.json. The output file is opened outside bwrap and tar writes to that descriptor. This uses the same preparation/READY as the proof, without a second staging job. A tar failure leaves no successful CPU.json and is not retried. The proof also emits exact `a/1.json`, restore, artifact-binding, manifest and export-pin receipts. These small files authenticate staging; they do not contain model weights. The proof binds payload/plan/inputs/operator, must pass bundle/entry checks and contain `memory.read_cache_bytes=12884901888` (4294967296 for processor-only), `basis=fixed_g3t_shapes`, and `fits=true`.\n\nArchive the CPU evidence on Orchard after its successful completion, using the package token printed by the build:\n\n```bash\nset -euo pipefail\nP=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}\ntar -czf "$D/2.tgz" -C "$P/a/c" CPU.json MEMORY.json SETTINGS.json RESTORE.json binding.json manifest.json EXPORT_PIN.json 1.json\nsha256sum "$D/2.tgz"\n```\n\nAfter authorized transport, authenticate and extract that archive on local scratch:\n\n```bash\nset -euo pipefail\n: "${PROOF_ARCHIVE:?Received CPU-evidence archive on local scratch}"\n: "${PROOF_SHA256:?Printed Orchard SHA256 of the CPU-evidence archive}"\nprintf \'%s  %s\\n\' "$PROOF_SHA256" "$PROOF_ARCHIVE" | nice -n 10 sha256sum -c -\nmkdir "$LOCAL/adopted/proof"\nnice -n 10 tar -xzf "$PROOF_ARCHIVE" -C "$LOCAL/adopted/proof"\n```\n\nAfter the zero-difference GPU parity gate passes, transfer its token-only `ue.json` through the authorized transport as one archive, preserving the SHA256 printed on the GPU host. The authorized owner authenticates that archive and installs the receipt before submission:\n\n```bash\nset -euo pipefail\n: "${GATE_ARCHIVE:?Received archive containing ue.json}"\n: "${GATE_SHA256:?SHA256 printed on the GPU host}"\nprintf \'%s  %s\\n\' "$GATE_SHA256" "$GATE_ARCHIVE" | sha256sum -c -\nmkdir "$D/g"\ntar -xf "$GATE_ARCHIVE" -C "$D/g"\nP=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}\ntest ! -e "$P/a/g.json"\ncp "$D/g/ue.json" "$P/a/g.json"\n```\n\nThen run:\n\n```bash\nset -euo pipefail\nbash "$D/o_sub.sh"\n# After the GPU job finishes:\nbash "$D/o_fetch.sh"\nP=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}\ntar -czf "$D/3.tgz" -C "$P/a/f" 0.tgz EXIT.json\nsha256sum "$D/3.tgz"\n```\n\n`o_sub.sh` embeds cont_ops’ A4 CPU-receipt assertions verbatim, including batch/dispatch/guard pins and MEMORY.json equality, then checks cache memory and the successful GPU receipt at `$P/a/g.json`, requires both dry checks to pass, requires an empty general queue, and refuses a return pool over **75,000,000 bytes** (including errors/symlinks). It then runs `3.py check` and one `3.py submit --gpus 1 --time 04:30:00`, saving the job ID. The GPU receipt must match the CPU restore/binding pins, filled export pin, adopted plan/profile and H100 80 GB requirement. The unchanged bootstrap itself does not require the cache-memory field; this submit preflight does. `o_fetch.sh` derives the authenticated return token and fetches `$P/a/f/{0.tgz,EXIT.json}`.\n\nTransfer `$D/3.tgz` through the authorized transport, preserving the local operator directory. Authenticate, extract and unpack it locally:\n\n```bash\nset -euo pipefail\n: "${RETURN_ARCHIVE:?Received fetched-return archive on local scratch}"\n: "${RETURN_SHA256:?Printed Orchard SHA256 of the fetched-return archive}"\nprintf \'%s  %s\\n\' "$RETURN_SHA256" "$RETURN_ARCHIVE" | nice -n 10 sha256sum -c -\nmkdir "$LOCAL/adopted/f"\nnice -n 10 tar -xzf "$RETURN_ARCHIVE" -C "$LOCAL/adopted/f"\n(cd "$LOCAL/adopted" && CUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -s -E -B ./unpack_return.py \\\n  --archive "$LOCAL/adopted/f/0.tgz" --exit "$LOCAL/adopted/f/EXIT.json" \\\n  --out "$LOCAL/adopted/ret" > "$LOCAL/adopted/unpack-success.json" && \\\n  test -s "$LOCAL/adopted/unpack-success.json")\n```\n\nA refused unpack leaves its extracted tree behind. Scorers must consume only unpack\'s **success output after exit status 0**, never a directory merely because it exists; the command\'s `&&` chain enforces that handoff. A successful partial return still has `complete=false` and must not be scored as complete. The ON unpacker refuses any existing weight receipt whose verified value is not JSON true. Processor-only journals need no weight receipt. OFF behavior remains unchanged. Whole-archive identity follows A4\'s design: fill checks the sealed whole-tar constants; job/unpack admission compare against inputs.archives[0].\n\n**Forecasts:** Package D is the 580-item distance read (B5 fork, 03:30 walltime); it has **no ON route** in a19. Its one-card **estimate** is 13,813.069 s (3 h 50 min), using the measured 23.600 s/item and crediting no cache saving. The **636-item** A4 read that a19 actually builds has an **estimate** of **7,351.824 s (2 h 02 min 32 s; 11.559 s/item)**, obtained by carrying forward the supplied A4 total, with zero assumed saving. Target weights, cache costs and staging/queue delays can change it; neither forecast measures the selected export.\n\n## GPU parity staging and acceptance\n\nThe gate must seal **A4 prepare\'s actual output plus the operator\'s per-read overrides** for the package being adopted. Do not supply an unrelated PRIVATE_SETTINGS.json. `a20 gate` checks the prepared bytes and exact RESTORE.json/artifact-binding bytes against CPU.json’s READY pins, checks export identity against the adopted step binding, checks the export-pin hash and byte count against the exact `a/1.json` bytes authenticated by CPU.json, and checks payload, plan and operator bindings. The selected export defaults to the pinned step-400 export; `--bound-export` explicitly changes it. Every GPU worker rechecks those asset bytes and the artifact manifest before reading; changing paths cannot substitute another checkpoint. It applies the authenticated operator descriptor and derives `enable_caches`, `read_cache_bytes` and the full adoption profile: candidates_argmax, memo on, g3t, empty verify IDs, save_own_depth=false, and the exact cache switches. Both the parent driver and every worker refuse a different profile. Processor-only adoption is explicitly gated with slots `[0]` and 4 GiB; all-cache adoption uses `[0,1,2]` and 12 GiB.\n\nThe **owner-only commands below are unrun here**. The shared asset archive already exists when CPU.json appears; never try to reopen the CPU job\'s private `/tmp`. Reserve storage for the archive before running `o_cpu.sh`. Its size is recorded by the job; no production archive size was measured here.\n\nAllocate the gate on Orchard, then enter its compute task. This is one non-requeued H100 job, eight CPUs, 200G and a five-hour maximum. Preserve its actual `CUDA_VISIBLE_DEVICES`; the Python guard requires exactly `NVIDIA H100 80GB HBM3`, 132 SMs, capability 9.0 and the 80 GB memory class.\n\n```bash\nset -euo pipefail\nsalloc --account=mt01 --partition=general --nodes=1 --ntasks=1 --cpus-per-task=8 \\\n  --mem=200G --gres=gpu:1 --time=05:00:00 --no-requeue \\\n  --exclude=orchard-community-2 --job-name=ab0123456789 \\\n  srun --ntasks=1 --pty bash --noprofile --norc\n```\n\nOn that H100 host, `/scratch/jjyeung` must **physically exist and be writable** outside bwrap. A4 creates `/scratch` only inside its namespace; it does not satisfy this host requirement. The operator must provision the host path before the gate. The exact logical root (currently `/scratch/jjyeung/b01ec87a6f29b`) must be absent so extraction cannot overlay another run. Preserve it so manifests and restore paths remain valid. Provision the separate opaque kit/source directories there too. Stage the source trees and public kit as single authenticated archives; keep private inputs and reverse maps on Trinity.\n\nThe shared path `$P/a/4.tar` is visible directly on Orchard. If approved transport copies it, set `ASSET_ARCHIVE` to that received path; CPU.json still supplies the expected hash and bytes. Run inside the allocation:\n\n```bash\nset -euo pipefail\n: "${PACKAGE_TOKEN:?Fresh package token from the build}"\nP=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}\nASSET_ARCHIVE=${ASSET_ARCHIVE:-"$P/a/4.tar"}\nGPU_LOGICAL=$(/usr/bin/python3 -I -s -B - "$P" "$ASSET_ARCHIVE" <<\'PYASSET\'\nimport hashlib,json,sys,tarfile\nfrom pathlib import Path\np=Path(sys.argv[1]);archive=Path(sys.argv[2]);proof=json.loads((p/\'a/c/CPU.json\').read_text())\nassert proof[\'passed\'] is True\nwith tarfile.open(p/\'0.tgz\') as t:cfg=json.load(t.extractfile(\'9.json\'))\nasset=proof[\'gate_assets\'];assert asset[\'logical\']==cfg[\'logical\']\nassert asset[\'path\']==str(p/\'a/4.tar\') and archive.stat().st_size==asset[\'bytes\']\nh=hashlib.sha256()\nwith archive.open(\'rb\') as stream:\n    for chunk in iter(lambda:stream.read(1024**2),b\'\'):h.update(chunk)\nassert h.hexdigest()==asset[\'sha256\']\nprint(cfg[\'logical\'])\nPYASSET\n)\ntest -d /scratch/jjyeung && test -w /scratch/jjyeung\ntest ! -e "$GPU_LOGICAL"\nmkdir -p "$GPU_LOGICAL/d" "$GPU_LOGICAL/p"\ntar -xf "$ASSET_ARCHIVE" -C "$GPU_LOGICAL/d"\ntar -xzf "$P/0.tgz" -C "$GPU_LOGICAL/p"\ntest ! -e "$GPU_LOGICAL/d/7.json"\ncp "$GPU_LOGICAL/d/binding.json" "$GPU_LOGICAL/d/7.json"\n```\n\nCreate a private neutral configuration from `config.example.json` with separate authenticated A4 original/patched source roots. Set `export=$GPU_LOGICAL/d/e`, `export_pin=$GPU_LOGICAL/d/6.json`, and `artifact_manifest=$GPU_LOGICAL/d/7.json`. The last file is a byte-identical neutral alias for the CPU binding. Include that exact `binding.json` to `7.json` mapping in `PRIVATE_ALIASES.json`; map the other private prepared asset paths to staged opaque aliases of those same files. Keep private settings and reverse maps on Trinity. The following commands use files under `$LOCAL`:\n\n```bash\nset -euo pipefail\n: "${PRIVATE_CONFIG_TEMPLATE:?Private neutral GPU configuration with staged asset paths}"\n: "${PRIVATE_ALIASES:?Private JSON mapping preparation paths to staged opaque paths}"\nPRIVATE_SETTINGS="$LOCAL/PRIVATE_SETTINGS.json"\nPRIVATE_CONFIG="$LOCAL/PRIVATE_NEUTRAL_CONFIG.json"\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a20.py" --enable-extensions gate \\\n  --operator "$LOCAL/adopted" --prepared "$LOCAL/adopted/proof/SETTINGS.json" \\\n  --proof "$LOCAL/adopted/proof/CPU.json" --config "$PRIVATE_CONFIG_TEMPLATE" \\\n  --asset-receipts "$LOCAL/adopted/proof" --bound-export "$BOUND_EXPORT" \\\n  --settings-out "$PRIVATE_SETTINGS" --config-out "$PRIVATE_CONFIG"\n```\n\n```bash\nset -euo pipefail\nmkdir -p "$LOCAL/public"\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a11.py" seal \\\n  --source-root "$EXT_SOURCE" --input "$PRIVATE_SETTINGS" --aliases "$PRIVATE_ALIASES" \\\n  --out "$LOCAL/public/u3"\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a11.py" stage-kit \\\n  --source-root "$EXT_SOURCE" --input "$DELIVERY/kit_parity50" \\\n  --config "$PRIVATE_CONFIG" --out "$LOCAL/public/u0"\n```\n\nThe package embeds the driver/comparator SHA256 and the deterministically sealed sample SHA256 from MANIFEST `kit_files`. The driver and every worker authenticate those executing bytes, and `ue.json` carries them to SUBMIT_CHECK. The staged `u3.json` pins every extension; `u4.json` authenticates both full 927-file base inventories. The driver rejects changed bases, equal original/patched roots, and an original root containing extensions. It authenticates the sealed sample bytes and the logical sample pin. Transfer only the staged directory through the approved transport under an opaque root.\n\nOn an assigned **H100 80 GB** GPU, run the acceptance command below; it is **unrun here**. Preserve that allocation\'s actual `CUDA_VISIBLE_DEVICES`.\n\n```bash\nset -euo pipefail\nnice -n 10 "$READ_PYTHON" -I -s -B /scratch/jjyeung/ab0123456789/u0/u0.py \\\n  /scratch/jjyeung/ab0123456789/u0/u2.json --out /scratch/jjyeung/ab0123456789/u9 \\\n  --enable-gpu --public --repeat-baseline --shards 4\n```\n\nEvery arm starts a fresh process. ORIGINAL/OFF/OFF_REPEAT use ordinary journals and modulo shards. ON tests caches; ON_JOURNAL and sequential whole-scene shards test separate journal/shard features. Sequential shards establish equality, not parallel speed. Public logs tokenize item/native/room identities and arbitrary stdout/stderr. No reverse map is written on Orchard.\n\nAcceptance requires all 50 expected IDs, complete production output schemas, nonempty text/tokens/heads, scale even when null, every served response and forced-token count, matching call counters, and **zero semantic byte differences**. ORIGINAL/OFF must also retain every production source hash. Each enabled cache must report its memory bound and useful hits; SAM needs both feature and detection hits. Empty or all-miss runs fail. Only clocks and explicit audit/cache/memo telemetry are excluded from semantic comparison; audit violations fail. There is no answer/trace tolerance.\n\nEach RUN.json records the adopted package plan, read profile, asset pins, required device type, actual device, cache slots and budget. The worker checks CUDA device properties before model loading and refuses a different exact name, SM count, compute capability or memory class. `ue.json` is written only after all comparisons finish and records whether they all passed; failed or missing receipts cannot authorize submit. On the H100 host, archive it with `tar -cf /scratch/jjyeung/ab0123456789/5.tar -C /scratch/jjyeung/ab0123456789/u9 ue.json` and print `sha256sum /scratch/jjyeung/ab0123456789/5.tar` for authenticated return transport. Judge net time from `RUN.json`\'s `worker_wall_seconds`, which includes install/boundary hashing and eager SAM loading. Per-item timing alone cannot establish savings. ON constructs SAM outside inference mode to obtain tracked parameters; that changes loading time and potentially RNG use. The GPU byte gate must clear it. The sample overrepresents clip reuse: its ten distance items share one clip, while A4 has 150 distance items across 60 clips (review finding 7).\n\nThe cache cap covers retained cache storage and transient copies, not model/caller working memory. Measure full-process host/GPU peaks. Models must remain frozen: calls check parameter/buffer identities, pointers and counters; install/type boundaries hash content. Persistent raw writes fail at a boundary. Raw writes restored between boundaries, private tensor attributes and arbitrary non-tensor state are outside this guard\'s coverage. Graceful stops verify journals; a hard kill can leave an unchecked journal that requires fresh output.\n\nOutput directories u0–u5 represent ORIGINAL/OFF/OFF_REPEAT/ON/ON_JOURNAL/SHARDED. Reports u6–ua compare arms; ub.json checks merge equality; uc/ud contain canonical single/sharded returns. Restore on Trinity with the private inputs:\n\n```bash\nset -euo pipefail\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a11.py" restore \\\n  --source-root "$EXT_SOURCE" --input PRIVATE_RETURN --out "$LOCAL/restored" \\\n  --private-source "$DELIVERY/kit_parity50/sample50.json" \\\n  --private-source "$PRIVATE_CONFIG" --private-source "$PRIVATE_SETTINGS"\n```\n\nRestoration authenticates committed rows before rebuilding private IDs/checksums. Merge with the original manifest through the explicit extension entrypoint. The canonical answer/trace archive must match exactly; transport-envelope clocks remain variable.\n\n## Array validation\n\nNo multi-card A4 operator is delivered. The array helper is a separate inert prototype. Its example has `approved=false`: two one-hour shards, at most two attempts, four GPU-hours total. Approval must bind the exact partition, shards, time and attempts, with no more than five allocated GPU-hours over all attempts. Before any sharded/preempt adoption, validate real persistent-storage preemption/requeue.\n\n```bash\nset -euo pipefail\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a15.py" PRIVATE_ARRAY_CONFIG.json \\\n  --enable-array --token ab0123456789 --out "$LOCAL/array-plan" \\\n  --python /scratch/jjyeung/ab0123456789/u1 --source /scratch/jjyeung/ab0123456789/u2 \\\n  --staged-config /project/community/jjyeung/okh7/a15_cot_apab0123456789/u3.json\n```\n\nThis writes commands without running them. Exit 75 requests bounded requeue; other errors remain failures. Lock waits stop after 60 seconds, and the attempt limit forbids more work. Public paths must use approved roots and pass the forbidden-word screen; name checks do not establish storage permissions or capacity.\n\nNo delivered CPU suite or single-GPU kit requires a local OS socket. StageOneSocket is a Python callback. Real restore, bwrap isolation, remote transport, GPU parity/performance/memory and persistent requeue remain unrun.\n\n## Review round 7: finding -> fix -> test\n\n| Finding | Fix | Regression |\n|---|---|---|\n| 1. Private root disappears | Archive inside CPU proof to `$P/a/4.tar` before CPU.json; record hash/bytes. | Real fixture tar runs through a namespace wrapper, survives loss of the root, and the CPU operator fixture executes staging. |\n| 2. Fill wait hangs | Guard PACKAGE_TOKEN, check PID and cap wait at four hours. | Missing token, dead PID, timeout and failed exit refuse; success passes. |\n| 3. PCIe accepted | Require exact HBM3 name and 132 SMs. | SXM stub passes; PCIe and wrong-SM stubs refuse. |\n| 4. Evidence/host nits | Bind executing kit/comparator/sample; include a/1.json; unpack with -s -E -B; use an H100-local archive path. | Mutated pins refuse, environment-polluted unpack succeeds, allocation/evidence blocks are checked. |\n| 5. Decision export | Default to the supplied step-400 export; require an explicit parameter for other exports. | Step 400 passes by default; synthetic step 600 passes only when selected; wrong artifact refuses. |\n\nFrozen weights remain required. Persistent raw writes are boundary-checked; writes restored between boundaries remain outside the guard. GPU byte equality and performance remain unrun.\n' : GPU shell preflight is missing

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
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 179, in test_f2_submit_checks_environment_versions_and_sha
    with self.subTest(field=field):self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'Submit ignored '+field)
                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 0 == 0 : Submit ignored sha256

======================================================================
FAIL: test_f2_submit_checks_environment_versions_and_sha (__main__.Round8Tests.test_f2_submit_checks_environment_versions_and_sha) (field='torch')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 179, in test_f2_submit_checks_environment_versions_and_sha
    with self.subTest(field=field):self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'Submit ignored '+field)
                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 0 == 0 : Submit ignored torch

======================================================================
FAIL: test_f2_submit_checks_environment_versions_and_sha (__main__.Round8Tests.test_f2_submit_checks_environment_versions_and_sha) (field='transformers')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 179, in test_f2_submit_checks_environment_versions_and_sha
    with self.subTest(field=field):self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'Submit ignored '+field)
                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 0 == 0 : Submit ignored transformers

======================================================================
FAIL: test_f2_submit_checks_environment_versions_and_sha (__main__.Round8Tests.test_f2_submit_checks_environment_versions_and_sha) (field='cuda')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 179, in test_f2_submit_checks_environment_versions_and_sha
    with self.subTest(field=field):self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'Submit ignored '+field)
                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 0 == 0 : Submit ignored cuda

======================================================================
FAIL: test_f3_builder_refuses_other_export_before_reading_base (__main__.Round8Tests.test_f3_builder_refuses_other_export_before_reading_base) (field='step')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 195, in test_f3_builder_refuses_other_export_before_reading_base
    self.builder.build(root/'absent-base',SRC,root/'binding.json',root/'output','ab0123456789',enable_extensions=True)
  File "/scratch/jjyeung/orch_n30/so_read/work/round8-before-u0/a19.py", line 152, in build
    original = (base/'package/0.tgz').read_bytes()
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/pathlib.py", line 1019, in read_bytes
    with self.open(mode='rb') as f:
         ^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py", line 26, in open_path
    return original_open(path,mode,*args,**kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/pathlib.py", line 1013, in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/52eca773ec314e39ac0841a06cd4abb5/absent-base/package/0.tgz'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 196, in test_f3_builder_refuses_other_export_before_reading_base
    except FileNotFoundError:self.fail('Builder read the base before rejecting another export: '+key)
                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Builder read the base before rejecting another export: step

======================================================================
FAIL: test_f3_builder_refuses_other_export_before_reading_base (__main__.Round8Tests.test_f3_builder_refuses_other_export_before_reading_base) (field='run')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 195, in test_f3_builder_refuses_other_export_before_reading_base
    self.builder.build(root/'absent-base',SRC,root/'binding.json',root/'output','ab0123456789',enable_extensions=True)
  File "/scratch/jjyeung/orch_n30/so_read/work/round8-before-u0/a19.py", line 152, in build
    original = (base/'package/0.tgz').read_bytes()
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/pathlib.py", line 1019, in read_bytes
    with self.open(mode='rb') as f:
         ^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py", line 26, in open_path
    return original_open(path,mode,*args,**kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/pathlib.py", line 1013, in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/7fd1581d5db246f6b7dbc5d3470e21a4/absent-base/package/0.tgz'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 196, in test_f3_builder_refuses_other_export_before_reading_base
    except FileNotFoundError:self.fail('Builder read the base before rejecting another export: '+key)
                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Builder read the base before rejecting another export: run

======================================================================
FAIL: test_f3_builder_refuses_other_export_before_reading_base (__main__.Round8Tests.test_f3_builder_refuses_other_export_before_reading_base) (field='member_directory')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 195, in test_f3_builder_refuses_other_export_before_reading_base
    self.builder.build(root/'absent-base',SRC,root/'binding.json',root/'output','ab0123456789',enable_extensions=True)
  File "/scratch/jjyeung/orch_n30/so_read/work/round8-before-u0/a19.py", line 152, in build
    original = (base/'package/0.tgz').read_bytes()
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/pathlib.py", line 1019, in read_bytes
    with self.open(mode='rb') as f:
         ^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py", line 26, in open_path
    return original_open(path,mode,*args,**kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/pathlib.py", line 1013, in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/20606ae9342a43079da8cef9957bc1f7/absent-base/package/0.tgz'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 196, in test_f3_builder_refuses_other_export_before_reading_base
    except FileNotFoundError:self.fail('Builder read the base before rejecting another export: '+key)
                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Builder read the base before rejecting another export: member_directory

======================================================================
FAIL: test_f3_builder_refuses_other_export_before_reading_base (__main__.Round8Tests.test_f3_builder_refuses_other_export_before_reading_base) (field='lineage')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 195, in test_f3_builder_refuses_other_export_before_reading_base
    self.builder.build(root/'absent-base',SRC,root/'binding.json',root/'output','ab0123456789',enable_extensions=True)
  File "/scratch/jjyeung/orch_n30/so_read/work/round8-before-u0/a19.py", line 152, in build
    original = (base/'package/0.tgz').read_bytes()
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/pathlib.py", line 1019, in read_bytes
    with self.open(mode='rb') as f:
         ^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py", line 26, in open_path
    return original_open(path,mode,*args,**kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/pathlib.py", line 1013, in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/cbdaf2ce90c742448b725cd29803a7b0/absent-base/package/0.tgz'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 196, in test_f3_builder_refuses_other_export_before_reading_base
    except FileNotFoundError:self.fail('Builder read the base before rejecting another export: '+key)
                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Builder read the base before rejecting another export: lineage

======================================================================
FAIL: test_f3_builder_refuses_other_export_before_reading_base (__main__.Round8Tests.test_f3_builder_refuses_other_export_before_reading_base) (field='object')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 195, in test_f3_builder_refuses_other_export_before_reading_base
    self.builder.build(root/'absent-base',SRC,root/'binding.json',root/'output','ab0123456789',enable_extensions=True)
  File "/scratch/jjyeung/orch_n30/so_read/work/round8-before-u0/a19.py", line 152, in build
    original = (base/'package/0.tgz').read_bytes()
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/pathlib.py", line 1019, in read_bytes
    with self.open(mode='rb') as f:
         ^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py", line 26, in open_path
    return original_open(path,mode,*args,**kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/pathlib.py", line 1013, in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/33f52f353b0944d3beedcb0dab1fb1de/absent-base/package/0.tgz'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 196, in test_f3_builder_refuses_other_export_before_reading_base
    except FileNotFoundError:self.fail('Builder read the base before rejecting another export: '+key)
                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Builder read the base before rejecting another export: object

======================================================================
FAIL: test_f3_builder_refuses_other_export_before_reading_base (__main__.Round8Tests.test_f3_builder_refuses_other_export_before_reading_base) (field='config_sha256')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 195, in test_f3_builder_refuses_other_export_before_reading_base
    self.builder.build(root/'absent-base',SRC,root/'binding.json',root/'output','ab0123456789',enable_extensions=True)
  File "/scratch/jjyeung/orch_n30/so_read/work/round8-before-u0/a19.py", line 152, in build
    original = (base/'package/0.tgz').read_bytes()
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/pathlib.py", line 1019, in read_bytes
    with self.open(mode='rb') as f:
         ^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py", line 26, in open_path
    return original_open(path,mode,*args,**kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/pathlib.py", line 1013, in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/16b189aa15a64dbf867ee0370a4c9486/absent-base/package/0.tgz'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 196, in test_f3_builder_refuses_other_export_before_reading_base
    except FileNotFoundError:self.fail('Builder read the base before rejecting another export: '+key)
                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Builder read the base before rejecting another export: config_sha256

======================================================================
FAIL: test_f3_builder_refuses_other_export_before_reading_base (__main__.Round8Tests.test_f3_builder_refuses_other_export_before_reading_base) (field='archive_sha256')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 195, in test_f3_builder_refuses_other_export_before_reading_base
    self.builder.build(root/'absent-base',SRC,root/'binding.json',root/'output','ab0123456789',enable_extensions=True)
  File "/scratch/jjyeung/orch_n30/so_read/work/round8-before-u0/a19.py", line 152, in build
    original = (base/'package/0.tgz').read_bytes()
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/pathlib.py", line 1019, in read_bytes
    with self.open(mode='rb') as f:
         ^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py", line 26, in open_path
    return original_open(path,mode,*args,**kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/pathlib.py", line 1013, in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/b370c9c1e7514065a1aaa23b37135bc1/absent-base/package/0.tgz'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 196, in test_f3_builder_refuses_other_export_before_reading_base
    except FileNotFoundError:self.fail('Builder read the base before rejecting another export: '+key)
                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Builder read the base before rejecting another export: archive_sha256

======================================================================
FAIL: test_f3_builder_refuses_other_export_before_reading_base (__main__.Round8Tests.test_f3_builder_refuses_other_export_before_reading_base) (field='archive_bytes')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 195, in test_f3_builder_refuses_other_export_before_reading_base
    self.builder.build(root/'absent-base',SRC,root/'binding.json',root/'output','ab0123456789',enable_extensions=True)
  File "/scratch/jjyeung/orch_n30/so_read/work/round8-before-u0/a19.py", line 152, in build
    original = (base/'package/0.tgz').read_bytes()
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/pathlib.py", line 1019, in read_bytes
    with self.open(mode='rb') as f:
         ^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py", line 26, in open_path
    return original_open(path,mode,*args,**kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/pathlib.py", line 1013, in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/b486f15e63734b4c84a643c74dded25e/absent-base/package/0.tgz'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 196, in test_f3_builder_refuses_other_export_before_reading_base
    except FileNotFoundError:self.fail('Builder read the base before rejecting another export: '+key)
                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Builder read the base before rejecting another export: archive_bytes

======================================================================
FAIL: test_f3_builder_refuses_other_export_before_reading_base (__main__.Round8Tests.test_f3_builder_refuses_other_export_before_reading_base) (field='base_identity')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 195, in test_f3_builder_refuses_other_export_before_reading_base
    self.builder.build(root/'absent-base',SRC,root/'binding.json',root/'output','ab0123456789',enable_extensions=True)
  File "/scratch/jjyeung/orch_n30/so_read/work/round8-before-u0/a19.py", line 152, in build
    original = (base/'package/0.tgz').read_bytes()
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/pathlib.py", line 1019, in read_bytes
    with self.open(mode='rb') as f:
         ^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py", line 26, in open_path
    return original_open(path,mode,*args,**kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/pathlib.py", line 1013, in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/40068fcf51de4ad2910741e01cc6bb42/absent-base/package/0.tgz'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 196, in test_f3_builder_refuses_other_export_before_reading_base
    except FileNotFoundError:self.fail('Builder read the base before rejecting another export: '+key)
                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Builder read the base before rejecting another export: base_identity

======================================================================
FAIL: test_f3_builder_refuses_other_export_before_reading_base (__main__.Round8Tests.test_f3_builder_refuses_other_export_before_reading_base) (field='frame_layout')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 195, in test_f3_builder_refuses_other_export_before_reading_base
    self.builder.build(root/'absent-base',SRC,root/'binding.json',root/'output','ab0123456789',enable_extensions=True)
  File "/scratch/jjyeung/orch_n30/so_read/work/round8-before-u0/a19.py", line 152, in build
    original = (base/'package/0.tgz').read_bytes()
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/pathlib.py", line 1019, in read_bytes
    with self.open(mode='rb') as f:
         ^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py", line 26, in open_path
    return original_open(path,mode,*args,**kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/pathlib.py", line 1013, in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/eaaa413e68e9494ca54b78774280054d/absent-base/package/0.tgz'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 196, in test_f3_builder_refuses_other_export_before_reading_base
    except FileNotFoundError:self.fail('Builder read the base before rejecting another export: '+key)
                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Builder read the base before rejecting another export: frame_layout

======================================================================
FAIL: test_f3_builder_refuses_other_export_before_reading_base (__main__.Round8Tests.test_f3_builder_refuses_other_export_before_reading_base) (field='preparation_sha256')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 195, in test_f3_builder_refuses_other_export_before_reading_base
    self.builder.build(root/'absent-base',SRC,root/'binding.json',root/'output','ab0123456789',enable_extensions=True)
  File "/scratch/jjyeung/orch_n30/so_read/work/round8-before-u0/a19.py", line 152, in build
    original = (base/'package/0.tgz').read_bytes()
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/pathlib.py", line 1019, in read_bytes
    with self.open(mode='rb') as f:
         ^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py", line 26, in open_path
    return original_open(path,mode,*args,**kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu/lib/python3.12/pathlib.py", line 1013, in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/fdf38f83fa374eb2acac1c65ad7a4a5b/absent-base/package/0.tgz'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 196, in test_f3_builder_refuses_other_export_before_reading_base
    except FileNotFoundError:self.fail('Builder read the base before rejecting another export: '+key)
                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Builder read the base before rejecting another export: preparation_sha256

======================================================================
FAIL: test_f3_builder_refuses_other_export_before_reading_base (__main__.Round8Tests.test_f3_builder_refuses_other_export_before_reading_base)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 198, in test_f3_builder_refuses_other_export_before_reading_base
    self.assertNotIn('--bound-export',(OUT/'kit_parity50/README.md').read_text())
AssertionError: '--bound-export' unexpectedly found in 'The GPU kit is unrun. It requires zero answer/trace byte differences. Its 50 items cover ten items per type and twelve captures; this reuse-heavy sample does not predict full-read throughput.\n\nUse the full **A4/src** base pinned by `BASE_PIN.json`. The reader patches also apply to the inspected B5 source subset, but this kit does not authenticate a B5 base. Apply patches 01–03 to a separate source copy. They add `u0/`; all original reader files remain byte-identical. Apply 04–05 to a separate A4 operator copy, outside `src`.\n\nThe ordinary entrypoint stays OFF and imports no extension. `u0/a8.py --enable-extensions` explicitly selects the extensions; individual cache settings then default OFF. The ON environment records an extension source hash. Rebuild payload and artifact pins before deployment.\n\n## Local preparation\n\nThese commands use paths supplied by the operator; they do not depend on the author\'s `work/` directory. Set `DELIVERY` to the delivered `out/`, `A4_BASE` to the full supplied A4 directory on local scratch, `LOCAL` to a fresh local scratch directory, and `READ_PYTHON` to the approved Python executable. Both source roots and all outputs must stay on local scratch. The package contains code, not model/data archives.\n\n```bash\nset -euo pipefail\n: "${DELIVERY:?Absolute path to delivered out directory}"\n: "${A4_BASE:?Absolute path to the full pinned A4 directory on local scratch}"\n: "${LOCAL:?Fresh local scratch directory}"\n: "${READ_PYTHON:?Approved Python executable}"\nexport PYTHONDONTWRITEBYTECODE=1 TOKENIZERS_PARALLELISM=false\nexport OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8\nexport XDG_CACHE_HOME="$LOCAL/cache" HF_HOME="$LOCAL/cache/hf" TRITON_CACHE_DIR="$LOCAL/cache/triton"\nmkdir -p "$LOCAL/source" "$LOCAL/a4"\nnice -n 10 tar -cf - -C "$A4_BASE/src" . | nice -n 10 tar -xf - -C "$LOCAL/source"\nnice -n 10 tar -cf - -C "$A4_BASE" package tower_sequence.py fetch_return.py unpack_return.py |\n  nice -n 10 tar -xf - -C "$LOCAL/a4"\nnice -n 10 patch --batch --fuzz=0 -p1 -d "$LOCAL/source" < "$DELIVERY/patches/01_bounded_read_caches.diff"\nnice -n 10 patch --batch --fuzz=0 -p1 -d "$LOCAL/source" < "$DELIVERY/patches/02_atomic_scene_shards.diff"\nnice -n 10 patch --batch --fuzz=0 -p1 -d "$LOCAL/source" < "$DELIVERY/patches/03_production_integration.diff"\nnice -n 10 patch --batch --fuzz=0 -p1 -d "$LOCAL/a4" < "$DELIVERY/patches/04_operator_cache_bound.diff"\nnice -n 10 patch --batch --fuzz=0 -p1 -d "$LOCAL/a4" < "$DELIVERY/patches/05_operator_return_and_proof.diff"\nEXT_SOURCE="$LOCAL/source"\n```\n\nKeep the private kit, original manifests and reverse maps on Trinity. Stage each source tree as one archive and extract it only on node-local scratch. Both parity source roots must remain pristine: no build outputs, extra files or symlinks. Public paths, submission names, configuration and logs must use opaque tokens. Never transfer private reverse maps to Orchard.\n\n## Bound export, build and operations\n\nThe candidate uses **A4\'s 636-item schedule, one card, caches only, general/no-requeue**. A4\'s export admission, submit helper and run settings remain intact. `a19` requires the reviewed payload hash `4498fca72a8e4b476b38f097ffdf3ff88b5aa20fc036bd196b18a5706e9fe46d`, the patched operator hashes, all copied A4 members, the base BATCH.sh and decoded bootstrap pins from MANIFEST, the exact extension inventory and the four original alias bases. It authenticates them before copying. Its batch uses cont_ops\' exact `build_r10.wrap_batch`: excluded node, EXIT log return and USR1 forwarding.\n\nThe gate defaults to **step 400**, read A of job **173060**, source package **a15_cot_apdc76460c3a164**. Its artifact SHA256 is **5083243cfedd2a389dfca579c5452e7d0c73b03a58e1cb7d204292ddd10e67cd**. `operations/BOUND_EXPORT.json` preserves the supplied export pin. `operations/binding.default.json` combines that identity, the four archive-part sizes in the supplied `a/1.json`, and the reviewed `bind400_partial.json` operation paths. `DEFAULT_EXPORT_PROVENANCE.json` records all source hashes. These are authenticated metadata; production weights were not restored here.\n\n`BOUND_EXPORT` selects the gate\'s exact reviewed export.json; `EXPORT_BINDING` selects the matching build/fill binding. For another reviewed export, including step 600, supply both parameters. The gate refuses a package whose export differs from the selected pin. A fresh package token identifies the ON build; it does not reuse the source package\'s token.\n\n```bash\nset -euo pipefail\nBOUND_EXPORT=${BOUND_EXPORT:-"$DELIVERY/operations/BOUND_EXPORT.json"}\nEXPORT_BINDING=${EXPORT_BINDING:-"$DELIVERY/operations/binding.default.json"}\n: "${PACKAGE_TOKEN:?Fresh 11-16 hex characters starting with a-f}"\nPROFILE_ARGS=()  # All three caches, 12 GiB. For processor-only: PROFILE_ARGS=(--processor-only)\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a19.py" \\\n  --enable-extensions --base-operator "$LOCAL/a4" --source-root "$EXT_SOURCE" \\\n  --manifest "$DELIVERY/patches/MANIFEST.json" --extension-pins "$DELIVERY/kit_parity50/EXTENSION_PINS.json" \\\n  --export-binding "$EXPORT_BINDING" --token "$PACKAGE_TOKEN" --out "$LOCAL/adopted" "${PROFILE_ARGS[@]}"\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a20.py" --enable-extensions operations \\\n  --operator "$LOCAL/adopted" --binding "$EXPORT_BINDING" --dry-root "$DELIVERY/operations" --out "$LOCAL/ops"\nnice -n 10 tar -czf "$LOCAL/0.tgz" -C "$LOCAL/ops" .\nnice -n 10 sha256sum "$LOCAL/0.tgz"\n```\n\nFor a different target, derive `EXPORT_BINDING` from its reviewed template and authenticated local receipts before the build block above, and set `BOUND_EXPORT` to that target\'s reviewed export.json:\n\n```bash\nset -euo pipefail\n: "${TARGET_TEMPLATE:?Reviewed target template, including Orchard done and prep_paths}"\n: "${TARGET_ARTIFACT:?Authenticated local artifact.json}"\n: "${TARGET_DONE:?Authenticated local whole-tar done receipt}"\n: "${TARGET_CONFIG:?Authenticated preparation config.json}"\n: "${TARGET_RECEIPT:?Authenticated preparation receipt}"\n: "${TARGET_DATA_RECEIPT:?Authenticated data receipt}"\n: "${EXPORT_BINDING:?Fresh output binding path for the selected target}"\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a20.py" --enable-extensions binding \\\n  --template "$TARGET_TEMPLATE" --artifact "$TARGET_ARTIFACT" --done "$TARGET_DONE" \\\n  --config "$TARGET_CONFIG" --receipt "$TARGET_RECEIPT" --data-receipt "$TARGET_DATA_RECEIPT" \\\n  --out "$EXPORT_BINDING"\n```\n\n`adopted` retains the exact local source/operator/unpacker. `ops/1.tgz` is the package delivery, with `ops/SHA256`; the outer archive carries it and five inert scripts. The commands below are **owner operations on Orchard, unrun here**. Transfer the single outer archive through the owner\'s existing authorized transport. Set `OPS_ARCHIVE` to its received opaque path, `OPS_SHA256` to the printed local hash, and `D` to a fresh opaque operation directory. These are transport endpoints, not generated receipt values.\n\n```bash\nset -euo pipefail\n: "${OPS_ARCHIVE:?Received outer archive on Orchard}"\n: "${OPS_SHA256:?Printed local SHA256 of that archive}"\n: "${D:?Fresh opaque operation directory on Orchard}"\n: "${PACKAGE_TOKEN:?Copy the fresh build token to this Orchard shell}"\nprintf \'%s  %s\\n\' "$OPS_SHA256" "$OPS_ARCHIVE" | sha256sum -c -\ntest ! -e "$D"\nmkdir -m 700 "$D"\ntar -xzf "$OPS_ARCHIVE" -C "$D"\nbash "$D/o_place.sh"\nbash "$D/o_pull_fill.sh"\n# BEGIN FILL_WAIT\n: "${PACKAGE_TOKEN:?Copy the fresh build token to this Orchard shell}"\nP=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}\nFILL_MAX_SECONDS=${FILL_MAX_SECONDS:-14400}\n[[ "$FILL_MAX_SECONDS" =~ ^[0-9]+$ ]] && (( FILL_MAX_SECONDS >= 1 && FILL_MAX_SECONDS <= 14400 )) || exit 1\nFILL_DEADLINE=$((SECONDS + FILL_MAX_SECONDS))\nwhile test ! -f "$P/a/1.txt"; do\n  FILL_PID=$(cat "$P/a/0.txt") || exit 1\n  [[ "$FILL_PID" =~ ^[1-9][0-9]*$ ]] || exit 1\n  if ! kill -0 "$FILL_PID" 2>/dev/null && test ! -f "$P/a/1.txt"; then\n    echo \'Fill worker is gone without an exit receipt\' >&2; exit 1\n  fi\n  if (( SECONDS >= FILL_DEADLINE )); then\n    echo \'Fill wait exceeded its maximum\' >&2; exit 1\n  fi\n  FILL_REMAIN=$((FILL_DEADLINE - SECONDS))\n  sleep "$(( FILL_REMAIN < 60 ? FILL_REMAIN : 60 ))"\ndone\ntest "$(cat "$P/a/1.txt")" = 0\n# END FILL_WAIT\nbash "$D/o_cpu.sh"\n```\n\n`o_place.sh` verifies the inner archive and places it at `$P=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}`. `o_pull_fill.sh` acquires the permanent attempt lock `$P/a/0.lock`, launches one detached nohup worker, and returns its PID in `$P/a/0.txt`. The worker logs to `$P/a/0.log` and writes its exit status to `$P/a/1.txt` on success or failure. Run the wait on the same host that launched the detached worker. It checks at most once per minute, refuses a vanished PID without `1.txt`, and stops after at most 14,400 seconds (four hours). A duplicate launch refuses; a failed or interrupted attempt requires a fresh package/token, never an automatic retry. The worker copies the reviewed `done` and `prep_paths` files to `$P/a/e/{5,7,8,9}`, authenticates their pins (the `.done` receipt uses whitespace-separated fields), fetches export parts `0..3` once with retries disabled, fills through `a/4.py`, and runs cont_ops\' verbatim `dryres2.py` and `dry2.py`. A failed transfer stops; the scripts do not retry it.\n\n`o_cpu.sh` requests the A4 CPU allocation explicitly: preempt, eight CPUs, 200G, four hours, no GPU, no requeue, and the excluded nodes. The **CPU allocation** is separate from the intended **general GPU read**. Wait for the CPU job to finish successfully. Preserve `$P/a/c/CPU.json`, `MEMORY.json` and the exact `SETTINGS.json` emitted by A4 prepare. Bring these small files back as one archive through the authorized transport to `$LOCAL/adopted/proof/` before the parity preparation below. Before writing CPU.json, the ON proof streams `logical/d` through its live `J.namespace(root)` to the named shared staging path `$P/a/4.tar`, outside the capped return pool. It dereferences symlinks and records `gate_assets.path`, `logical`, `sha256` and `bytes` in CPU.json. The output file is opened outside bwrap and tar writes to that descriptor. This uses the same preparation/READY as the proof, without a second staging job. A tar failure leaves no successful CPU.json and is not retried. The proof also emits exact `a/1.json`, restore, artifact-binding, manifest and export-pin receipts. These small files authenticate staging; they do not contain model weights. The proof binds payload/plan/inputs/operator, must pass bundle/entry checks and contain `memory.read_cache_bytes=12884901888` (4294967296 for processor-only), `basis=fixed_g3t_shapes`, and `fits=true`.\n\nArchive the CPU evidence on Orchard after its successful completion, using the package token printed by the build:\n\n```bash\nset -euo pipefail\nP=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}\ntar -czf "$D/2.tgz" -C "$P/a/c" CPU.json MEMORY.json SETTINGS.json RESTORE.json binding.json manifest.json EXPORT_PIN.json 1.json\nsha256sum "$D/2.tgz"\n```\n\nAfter authorized transport, authenticate and extract that archive on local scratch:\n\n```bash\nset -euo pipefail\n: "${PROOF_ARCHIVE:?Received CPU-evidence archive on local scratch}"\n: "${PROOF_SHA256:?Printed Orchard SHA256 of the CPU-evidence archive}"\nprintf \'%s  %s\\n\' "$PROOF_SHA256" "$PROOF_ARCHIVE" | nice -n 10 sha256sum -c -\nmkdir "$LOCAL/adopted/proof"\nnice -n 10 tar -xzf "$PROOF_ARCHIVE" -C "$LOCAL/adopted/proof"\n```\n\nAfter the zero-difference GPU parity gate passes, transfer its token-only `ue.json` through the authorized transport as one archive, preserving the SHA256 printed on the GPU host. The authorized owner authenticates that archive and installs the receipt before submission:\n\n```bash\nset -euo pipefail\n: "${GATE_ARCHIVE:?Received archive containing ue.json}"\n: "${GATE_SHA256:?SHA256 printed on the GPU host}"\nprintf \'%s  %s\\n\' "$GATE_SHA256" "$GATE_ARCHIVE" | sha256sum -c -\nmkdir "$D/g"\ntar -xf "$GATE_ARCHIVE" -C "$D/g"\nP=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}\ntest ! -e "$P/a/g.json"\ncp "$D/g/ue.json" "$P/a/g.json"\n```\n\nThen run:\n\n```bash\nset -euo pipefail\nbash "$D/o_sub.sh"\n# After the GPU job finishes:\nbash "$D/o_fetch.sh"\nP=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}\ntar -czf "$D/3.tgz" -C "$P/a/f" 0.tgz EXIT.json\nsha256sum "$D/3.tgz"\n```\n\n`o_sub.sh` embeds cont_ops’ A4 CPU-receipt assertions verbatim, including batch/dispatch/guard pins and MEMORY.json equality, then checks cache memory and the successful GPU receipt at `$P/a/g.json`, requires both dry checks to pass, requires an empty general queue, and refuses a return pool over **75,000,000 bytes** (including errors/symlinks). It then runs `3.py check` and one `3.py submit --gpus 1 --time 04:30:00`, saving the job ID. The GPU receipt must match the CPU restore/binding pins, filled export pin, adopted plan/profile and H100 80 GB requirement. The unchanged bootstrap itself does not require the cache-memory field; this submit preflight does. `o_fetch.sh` derives the authenticated return token and fetches `$P/a/f/{0.tgz,EXIT.json}`.\n\nTransfer `$D/3.tgz` through the authorized transport, preserving the local operator directory. Authenticate, extract and unpack it locally:\n\n```bash\nset -euo pipefail\n: "${RETURN_ARCHIVE:?Received fetched-return archive on local scratch}"\n: "${RETURN_SHA256:?Printed Orchard SHA256 of the fetched-return archive}"\nprintf \'%s  %s\\n\' "$RETURN_SHA256" "$RETURN_ARCHIVE" | nice -n 10 sha256sum -c -\nmkdir "$LOCAL/adopted/f"\nnice -n 10 tar -xzf "$RETURN_ARCHIVE" -C "$LOCAL/adopted/f"\n(cd "$LOCAL/adopted" && CUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -s -E -B ./unpack_return.py \\\n  --archive "$LOCAL/adopted/f/0.tgz" --exit "$LOCAL/adopted/f/EXIT.json" \\\n  --out "$LOCAL/adopted/ret" > "$LOCAL/adopted/unpack-success.json" && \\\n  test -s "$LOCAL/adopted/unpack-success.json")\n```\n\nA refused unpack leaves its extracted tree behind. Scorers must consume only unpack\'s **success output after exit status 0**, never a directory merely because it exists; the command\'s `&&` chain enforces that handoff. A successful partial return still has `complete=false` and must not be scored as complete. The ON unpacker refuses any existing weight receipt whose verified value is not JSON true. Processor-only journals need no weight receipt. OFF behavior remains unchanged. Whole-archive identity follows A4\'s design: fill checks the sealed whole-tar constants; job/unpack admission compare against inputs.archives[0].\n\n**Forecasts:** Package D is the 580-item distance read (B5 fork, 03:30 walltime); it has **no ON route** in a19. Its one-card **estimate** is 13,813.069 s (3 h 50 min), using the measured 23.600 s/item and crediting no cache saving. The **636-item** A4 read that a19 actually builds has an **estimate** of **7,351.824 s (2 h 02 min 32 s; 11.559 s/item)**, obtained by carrying forward the supplied A4 total, with zero assumed saving. Target weights, cache costs and staging/queue delays can change it; neither forecast measures the selected export.\n\n## GPU parity staging and acceptance\n\nThe gate must seal **A4 prepare\'s actual output plus the operator\'s per-read overrides** for the package being adopted. Do not supply an unrelated PRIVATE_SETTINGS.json. `a20 gate` checks the prepared bytes and exact RESTORE.json/artifact-binding bytes against CPU.json’s READY pins, checks export identity against the adopted step binding, checks the export-pin hash and byte count against the exact `a/1.json` bytes authenticated by CPU.json, and checks payload, plan and operator bindings. The selected export defaults to the pinned step-400 export; `--bound-export` explicitly changes it. Every GPU worker rechecks those asset bytes and the artifact manifest before reading; changing paths cannot substitute another checkpoint. It applies the authenticated operator descriptor and derives `enable_caches`, `read_cache_bytes` and the full adoption profile: candidates_argmax, memo on, g3t, empty verify IDs, save_own_depth=false, and the exact cache switches. Both the parent driver and every worker refuse a different profile. Processor-only adoption is explicitly gated with slots `[0]` and 4 GiB; all-cache adoption uses `[0,1,2]` and 12 GiB.\n\nThe **owner-only commands below are unrun here**. The shared asset archive already exists when CPU.json appears; never try to reopen the CPU job\'s private `/tmp`. Reserve storage for the archive before running `o_cpu.sh`. Its size is recorded by the job; no production archive size was measured here.\n\nAllocate the gate on Orchard, then enter its compute task. This is one non-requeued H100 job, eight CPUs, 200G and a five-hour maximum. Preserve its actual `CUDA_VISIBLE_DEVICES`; the Python guard requires exactly `NVIDIA H100 80GB HBM3`, 132 SMs, capability 9.0 and the 80 GB memory class.\n\n```bash\nset -euo pipefail\nsalloc --account=mt01 --partition=general --nodes=1 --ntasks=1 --cpus-per-task=8 \\\n  --mem=200G --gres=gpu:1 --time=05:00:00 --no-requeue \\\n  --exclude=orchard-community-2 --job-name=ab0123456789 \\\n  srun --ntasks=1 --pty bash --noprofile --norc\n```\n\nOn that H100 host, `/scratch/jjyeung` must **physically exist and be writable** outside bwrap. A4 creates `/scratch` only inside its namespace; it does not satisfy this host requirement. The operator must provision the host path before the gate. The exact logical root (currently `/scratch/jjyeung/b01ec87a6f29b`) must be absent so extraction cannot overlay another run. Preserve it so manifests and restore paths remain valid. Provision the separate opaque kit/source directories there too. Stage the source trees and public kit as single authenticated archives; keep private inputs and reverse maps on Trinity.\n\nThe shared path `$P/a/4.tar` is visible directly on Orchard. If approved transport copies it, set `ASSET_ARCHIVE` to that received path; CPU.json still supplies the expected hash and bytes. Run inside the allocation:\n\n```bash\nset -euo pipefail\n: "${PACKAGE_TOKEN:?Fresh package token from the build}"\nP=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}\nASSET_ARCHIVE=${ASSET_ARCHIVE:-"$P/a/4.tar"}\nGPU_LOGICAL=$(/usr/bin/python3 -I -s -B - "$P" "$ASSET_ARCHIVE" <<\'PYASSET\'\nimport hashlib,json,sys,tarfile\nfrom pathlib import Path\np=Path(sys.argv[1]);archive=Path(sys.argv[2]);proof=json.loads((p/\'a/c/CPU.json\').read_text())\nassert proof[\'passed\'] is True\nwith tarfile.open(p/\'0.tgz\') as t:cfg=json.load(t.extractfile(\'9.json\'))\nasset=proof[\'gate_assets\'];assert asset[\'logical\']==cfg[\'logical\']\nassert asset[\'path\']==str(p/\'a/4.tar\') and archive.stat().st_size==asset[\'bytes\']\nh=hashlib.sha256()\nwith archive.open(\'rb\') as stream:\n    for chunk in iter(lambda:stream.read(1024**2),b\'\'):h.update(chunk)\nassert h.hexdigest()==asset[\'sha256\']\nprint(cfg[\'logical\'])\nPYASSET\n)\ntest -d /scratch/jjyeung && test -w /scratch/jjyeung\ntest ! -e "$GPU_LOGICAL"\nmkdir -p "$GPU_LOGICAL/d" "$GPU_LOGICAL/p"\ntar -xf "$ASSET_ARCHIVE" -C "$GPU_LOGICAL/d"\ntar -xzf "$P/0.tgz" -C "$GPU_LOGICAL/p"\ntest ! -e "$GPU_LOGICAL/d/7.json"\ncp "$GPU_LOGICAL/d/binding.json" "$GPU_LOGICAL/d/7.json"\n```\n\nCreate a private neutral configuration from `config.example.json` with separate authenticated A4 original/patched source roots. Set `export=$GPU_LOGICAL/d/e`, `export_pin=$GPU_LOGICAL/d/6.json`, and `artifact_manifest=$GPU_LOGICAL/d/7.json`. The last file is a byte-identical neutral alias for the CPU binding. Include that exact `binding.json` to `7.json` mapping in `PRIVATE_ALIASES.json`; map the other private prepared asset paths to staged opaque aliases of those same files. Keep private settings and reverse maps on Trinity. The following commands use files under `$LOCAL`:\n\n```bash\nset -euo pipefail\n: "${PRIVATE_CONFIG_TEMPLATE:?Private neutral GPU configuration with staged asset paths}"\n: "${PRIVATE_ALIASES:?Private JSON mapping preparation paths to staged opaque paths}"\nPRIVATE_SETTINGS="$LOCAL/PRIVATE_SETTINGS.json"\nPRIVATE_CONFIG="$LOCAL/PRIVATE_NEUTRAL_CONFIG.json"\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a20.py" --enable-extensions gate \\\n  --operator "$LOCAL/adopted" --prepared "$LOCAL/adopted/proof/SETTINGS.json" \\\n  --proof "$LOCAL/adopted/proof/CPU.json" --config "$PRIVATE_CONFIG_TEMPLATE" \\\n  --asset-receipts "$LOCAL/adopted/proof" --bound-export "$BOUND_EXPORT" \\\n  --settings-out "$PRIVATE_SETTINGS" --config-out "$PRIVATE_CONFIG"\n```\n\n```bash\nset -euo pipefail\nmkdir -p "$LOCAL/public"\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a11.py" seal \\\n  --source-root "$EXT_SOURCE" --input "$PRIVATE_SETTINGS" --aliases "$PRIVATE_ALIASES" \\\n  --out "$LOCAL/public/u3"\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a11.py" stage-kit \\\n  --source-root "$EXT_SOURCE" --input "$DELIVERY/kit_parity50" \\\n  --config "$PRIVATE_CONFIG" --out "$LOCAL/public/u0"\n```\n\nThe package embeds the driver/comparator SHA256 and the deterministically sealed sample SHA256 from MANIFEST `kit_files`. The driver and every worker authenticate those executing bytes, and `ue.json` carries them to SUBMIT_CHECK. The staged `u3.json` pins every extension; `u4.json` authenticates both full 927-file base inventories. The driver rejects changed bases, equal original/patched roots, and an original root containing extensions. It authenticates the sealed sample bytes and the logical sample pin. Transfer only the staged directory through the approved transport under an opaque root.\n\nOn an assigned **H100 80 GB** GPU, run the acceptance command below; it is **unrun here**. Preserve that allocation\'s actual `CUDA_VISIBLE_DEVICES`.\n\n```bash\nset -euo pipefail\nnice -n 10 "$READ_PYTHON" -I -s -B /scratch/jjyeung/ab0123456789/u0/u0.py \\\n  /scratch/jjyeung/ab0123456789/u0/u2.json --out /scratch/jjyeung/ab0123456789/u9 \\\n  --enable-gpu --public --repeat-baseline --shards 4\n```\n\nEvery arm starts a fresh process. ORIGINAL/OFF/OFF_REPEAT use ordinary journals and modulo shards. ON tests caches; ON_JOURNAL and sequential whole-scene shards test separate journal/shard features. Sequential shards establish equality, not parallel speed. Public logs tokenize item/native/room identities and arbitrary stdout/stderr. No reverse map is written on Orchard.\n\nAcceptance requires all 50 expected IDs, complete production output schemas, nonempty text/tokens/heads, scale even when null, every served response and forced-token count, matching call counters, and **zero semantic byte differences**. ORIGINAL/OFF must also retain every production source hash. Each enabled cache must report its memory bound and useful hits; SAM needs both feature and detection hits. Empty or all-miss runs fail. Only clocks and explicit audit/cache/memo telemetry are excluded from semantic comparison; audit violations fail. There is no answer/trace tolerance.\n\nEach RUN.json records the adopted package plan, read profile, asset pins, required device type, actual device, cache slots and budget. The worker checks CUDA device properties before model loading and refuses a different exact name, SM count, compute capability or memory class. `ue.json` is written only after all comparisons finish and records whether they all passed; failed or missing receipts cannot authorize submit. On the H100 host, archive it with `tar -cf /scratch/jjyeung/ab0123456789/5.tar -C /scratch/jjyeung/ab0123456789/u9 ue.json` and print `sha256sum /scratch/jjyeung/ab0123456789/5.tar` for authenticated return transport. Judge net time from `RUN.json`\'s `worker_wall_seconds`, which includes install/boundary hashing and eager SAM loading. Per-item timing alone cannot establish savings. ON constructs SAM outside inference mode to obtain tracked parameters; that changes loading time and potentially RNG use. The GPU byte gate must clear it. The sample overrepresents clip reuse: its ten distance items share one clip, while A4 has 150 distance items across 60 clips (review finding 7).\n\nThe cache cap covers retained cache storage and transient copies, not model/caller working memory. Measure full-process host/GPU peaks. Models must remain frozen: calls check parameter/buffer identities, pointers and counters; install/type boundaries hash content. Persistent raw writes fail at a boundary. Raw writes restored between boundaries, private tensor attributes and arbitrary non-tensor state are outside this guard\'s coverage. Graceful stops verify journals; a hard kill can leave an unchecked journal that requires fresh output.\n\nOutput directories u0–u5 represent ORIGINAL/OFF/OFF_REPEAT/ON/ON_JOURNAL/SHARDED. Reports u6–ua compare arms; ub.json checks merge equality; uc/ud contain canonical single/sharded returns. Restore on Trinity with the private inputs:\n\n```bash\nset -euo pipefail\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a11.py" restore \\\n  --source-root "$EXT_SOURCE" --input PRIVATE_RETURN --out "$LOCAL/restored" \\\n  --private-source "$DELIVERY/kit_parity50/sample50.json" \\\n  --private-source "$PRIVATE_CONFIG" --private-source "$PRIVATE_SETTINGS"\n```\n\nRestoration authenticates committed rows before rebuilding private IDs/checksums. Merge with the original manifest through the explicit extension entrypoint. The canonical answer/trace archive must match exactly; transport-envelope clocks remain variable.\n\n## Array validation\n\nNo multi-card A4 operator is delivered. The array helper is a separate inert prototype. Its example has `approved=false`: two one-hour shards, at most two attempts, four GPU-hours total. Approval must bind the exact partition, shards, time and attempts, with no more than five allocated GPU-hours over all attempts. Before any sharded/preempt adoption, validate real persistent-storage preemption/requeue.\n\n```bash\nset -euo pipefail\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a15.py" PRIVATE_ARRAY_CONFIG.json \\\n  --enable-array --token ab0123456789 --out "$LOCAL/array-plan" \\\n  --python /scratch/jjyeung/ab0123456789/u1 --source /scratch/jjyeung/ab0123456789/u2 \\\n  --staged-config /project/community/jjyeung/okh7/a15_cot_apab0123456789/u3.json\n```\n\nThis writes commands without running them. Exit 75 requests bounded requeue; other errors remain failures. Lock waits stop after 60 seconds, and the attempt limit forbids more work. Public paths must use approved roots and pass the forbidden-word screen; name checks do not establish storage permissions or capacity.\n\nNo delivered CPU suite or single-GPU kit requires a local OS socket. StageOneSocket is a Python callback. Real restore, bwrap isolation, remote transport, GPU parity/performance/memory and persistent requeue remain unrun.\n\n## Review round 7: finding -> fix -> test\n\n| Finding | Fix | Regression |\n|---|---|---|\n| 1. Private root disappears | Archive inside CPU proof to `$P/a/4.tar` before CPU.json; record hash/bytes. | Real fixture tar runs through a namespace wrapper, survives loss of the root, and the CPU operator fixture executes staging. |\n| 2. Fill wait hangs | Guard PACKAGE_TOKEN, check PID and cap wait at four hours. | Missing token, dead PID, timeout and failed exit refuse; success passes. |\n| 3. PCIe accepted | Require exact HBM3 name and 132 SMs. | SXM stub passes; PCIe and wrong-SM stubs refuse. |\n| 4. Evidence/host nits | Bind executing kit/comparator/sample; include a/1.json; unpack with -s -E -B; use an H100-local archive path. | Mutated pins refuse, environment-polluted unpack succeeds, allocation/evidence blocks are checked. |\n| 5. Decision export | Default to the supplied step-400 export; require an explicit parameter for other exports. | Step 400 passes by default; synthetic step 600 passes only when selected; wrong artifact refuses. |\n\nFrozen weights remain required. Persistent raw writes are boundary-checked; writes restored between boundaries remain outside the guard. GPU byte equality and performance remain unrun.\n'

======================================================================
FAIL: test_f4_readme_archive_path_accepts_symlinked_parent (__main__.Round8Tests.test_f4_readme_archive_path_accepts_symlinked_parent)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 209, in test_f4_readme_archive_path_accepts_symlinked_parent
    self.assertEqual(result.returncode,0,result.stderr)
AssertionError: 1 != 0 : Traceback (most recent call last):
  File "<stdin>", line 7, in <module>
AssertionError


======================================================================
FAIL: test_info_gpu_commands_and_aliases (__main__.Round8Tests.test_info_gpu_commands_and_aliases)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 214, in test_info_gpu_commands_and_aliases
    self.assertIn('READ_PYTHON="$GPU_LOGICAL/d/v/py"',text)
AssertionError: 'READ_PYTHON="$GPU_LOGICAL/d/v/py"' not found in 'The GPU kit is unrun. It requires zero answer/trace byte differences. Its 50 items cover ten items per type and twelve captures; this reuse-heavy sample does not predict full-read throughput.\n\nUse the full **A4/src** base pinned by `BASE_PIN.json`. The reader patches also apply to the inspected B5 source subset, but this kit does not authenticate a B5 base. Apply patches 01–03 to a separate source copy. They add `u0/`; all original reader files remain byte-identical. Apply 04–05 to a separate A4 operator copy, outside `src`.\n\nThe ordinary entrypoint stays OFF and imports no extension. `u0/a8.py --enable-extensions` explicitly selects the extensions; individual cache settings then default OFF. The ON environment records an extension source hash. Rebuild payload and artifact pins before deployment.\n\n## Local preparation\n\nThese commands use paths supplied by the operator; they do not depend on the author\'s `work/` directory. Set `DELIVERY` to the delivered `out/`, `A4_BASE` to the full supplied A4 directory on local scratch, `LOCAL` to a fresh local scratch directory, and `READ_PYTHON` to the approved Python executable. Both source roots and all outputs must stay on local scratch. The package contains code, not model/data archives.\n\n```bash\nset -euo pipefail\n: "${DELIVERY:?Absolute path to delivered out directory}"\n: "${A4_BASE:?Absolute path to the full pinned A4 directory on local scratch}"\n: "${LOCAL:?Fresh local scratch directory}"\n: "${READ_PYTHON:?Approved Python executable}"\nexport PYTHONDONTWRITEBYTECODE=1 TOKENIZERS_PARALLELISM=false\nexport OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8\nexport XDG_CACHE_HOME="$LOCAL/cache" HF_HOME="$LOCAL/cache/hf" TRITON_CACHE_DIR="$LOCAL/cache/triton"\nmkdir -p "$LOCAL/source" "$LOCAL/a4"\nnice -n 10 tar -cf - -C "$A4_BASE/src" . | nice -n 10 tar -xf - -C "$LOCAL/source"\nnice -n 10 tar -cf - -C "$A4_BASE" package tower_sequence.py fetch_return.py unpack_return.py |\n  nice -n 10 tar -xf - -C "$LOCAL/a4"\nnice -n 10 patch --batch --fuzz=0 -p1 -d "$LOCAL/source" < "$DELIVERY/patches/01_bounded_read_caches.diff"\nnice -n 10 patch --batch --fuzz=0 -p1 -d "$LOCAL/source" < "$DELIVERY/patches/02_atomic_scene_shards.diff"\nnice -n 10 patch --batch --fuzz=0 -p1 -d "$LOCAL/source" < "$DELIVERY/patches/03_production_integration.diff"\nnice -n 10 patch --batch --fuzz=0 -p1 -d "$LOCAL/a4" < "$DELIVERY/patches/04_operator_cache_bound.diff"\nnice -n 10 patch --batch --fuzz=0 -p1 -d "$LOCAL/a4" < "$DELIVERY/patches/05_operator_return_and_proof.diff"\nEXT_SOURCE="$LOCAL/source"\n```\n\nKeep the private kit, original manifests and reverse maps on Trinity. Stage each source tree as one archive and extract it only on node-local scratch. Both parity source roots must remain pristine: no build outputs, extra files or symlinks. Public paths, submission names, configuration and logs must use opaque tokens. Never transfer private reverse maps to Orchard.\n\n## Bound export, build and operations\n\nThe candidate uses **A4\'s 636-item schedule, one card, caches only, general/no-requeue**. A4\'s export admission, submit helper and run settings remain intact. `a19` requires the reviewed payload hash `4498fca72a8e4b476b38f097ffdf3ff88b5aa20fc036bd196b18a5706e9fe46d`, the patched operator hashes, all copied A4 members, the base BATCH.sh and decoded bootstrap pins from MANIFEST, the exact extension inventory and the four original alias bases. It authenticates them before copying. Its batch uses cont_ops\' exact `build_r10.wrap_batch`: excluded node, EXIT log return and USR1 forwarding.\n\nThe gate defaults to **step 400**, read A of job **173060**, source package **a15_cot_apdc76460c3a164**. Its artifact SHA256 is **5083243cfedd2a389dfca579c5452e7d0c73b03a58e1cb7d204292ddd10e67cd**. `operations/BOUND_EXPORT.json` preserves the supplied export pin. `operations/binding.default.json` combines that identity, the four archive-part sizes in the supplied `a/1.json`, and the reviewed `bind400_partial.json` operation paths. `DEFAULT_EXPORT_PROVENANCE.json` records all source hashes. These are authenticated metadata; production weights were not restored here.\n\n`BOUND_EXPORT` selects the gate\'s exact reviewed export.json; `EXPORT_BINDING` selects the matching build/fill binding. For another reviewed export, including step 600, supply both parameters. The gate refuses a package whose export differs from the selected pin. A fresh package token identifies the ON build; it does not reuse the source package\'s token.\n\n```bash\nset -euo pipefail\nBOUND_EXPORT=${BOUND_EXPORT:-"$DELIVERY/operations/BOUND_EXPORT.json"}\nEXPORT_BINDING=${EXPORT_BINDING:-"$DELIVERY/operations/binding.default.json"}\n: "${PACKAGE_TOKEN:?Fresh 11-16 hex characters starting with a-f}"\nPROFILE_ARGS=()  # All three caches, 12 GiB. For processor-only: PROFILE_ARGS=(--processor-only)\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a19.py" \\\n  --enable-extensions --base-operator "$LOCAL/a4" --source-root "$EXT_SOURCE" \\\n  --manifest "$DELIVERY/patches/MANIFEST.json" --extension-pins "$DELIVERY/kit_parity50/EXTENSION_PINS.json" \\\n  --export-binding "$EXPORT_BINDING" --token "$PACKAGE_TOKEN" --out "$LOCAL/adopted" "${PROFILE_ARGS[@]}"\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a20.py" --enable-extensions operations \\\n  --operator "$LOCAL/adopted" --binding "$EXPORT_BINDING" --dry-root "$DELIVERY/operations" --out "$LOCAL/ops"\nnice -n 10 tar -czf "$LOCAL/0.tgz" -C "$LOCAL/ops" .\nnice -n 10 sha256sum "$LOCAL/0.tgz"\n```\n\nFor a different target, derive `EXPORT_BINDING` from its reviewed template and authenticated local receipts before the build block above, and set `BOUND_EXPORT` to that target\'s reviewed export.json:\n\n```bash\nset -euo pipefail\n: "${TARGET_TEMPLATE:?Reviewed target template, including Orchard done and prep_paths}"\n: "${TARGET_ARTIFACT:?Authenticated local artifact.json}"\n: "${TARGET_DONE:?Authenticated local whole-tar done receipt}"\n: "${TARGET_CONFIG:?Authenticated preparation config.json}"\n: "${TARGET_RECEIPT:?Authenticated preparation receipt}"\n: "${TARGET_DATA_RECEIPT:?Authenticated data receipt}"\n: "${EXPORT_BINDING:?Fresh output binding path for the selected target}"\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a20.py" --enable-extensions binding \\\n  --template "$TARGET_TEMPLATE" --artifact "$TARGET_ARTIFACT" --done "$TARGET_DONE" \\\n  --config "$TARGET_CONFIG" --receipt "$TARGET_RECEIPT" --data-receipt "$TARGET_DATA_RECEIPT" \\\n  --out "$EXPORT_BINDING"\n```\n\n`adopted` retains the exact local source/operator/unpacker. `ops/1.tgz` is the package delivery, with `ops/SHA256`; the outer archive carries it and five inert scripts. The commands below are **owner operations on Orchard, unrun here**. Transfer the single outer archive through the owner\'s existing authorized transport. Set `OPS_ARCHIVE` to its received opaque path, `OPS_SHA256` to the printed local hash, and `D` to a fresh opaque operation directory. These are transport endpoints, not generated receipt values.\n\n```bash\nset -euo pipefail\n: "${OPS_ARCHIVE:?Received outer archive on Orchard}"\n: "${OPS_SHA256:?Printed local SHA256 of that archive}"\n: "${D:?Fresh opaque operation directory on Orchard}"\n: "${PACKAGE_TOKEN:?Copy the fresh build token to this Orchard shell}"\nprintf \'%s  %s\\n\' "$OPS_SHA256" "$OPS_ARCHIVE" | sha256sum -c -\ntest ! -e "$D"\nmkdir -m 700 "$D"\ntar -xzf "$OPS_ARCHIVE" -C "$D"\nbash "$D/o_place.sh"\nbash "$D/o_pull_fill.sh"\n# BEGIN FILL_WAIT\n: "${PACKAGE_TOKEN:?Copy the fresh build token to this Orchard shell}"\nP=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}\nFILL_MAX_SECONDS=${FILL_MAX_SECONDS:-14400}\n[[ "$FILL_MAX_SECONDS" =~ ^[0-9]+$ ]] && (( FILL_MAX_SECONDS >= 1 && FILL_MAX_SECONDS <= 14400 )) || exit 1\nFILL_DEADLINE=$((SECONDS + FILL_MAX_SECONDS))\nwhile test ! -f "$P/a/1.txt"; do\n  FILL_PID=$(cat "$P/a/0.txt") || exit 1\n  [[ "$FILL_PID" =~ ^[1-9][0-9]*$ ]] || exit 1\n  if ! kill -0 "$FILL_PID" 2>/dev/null && test ! -f "$P/a/1.txt"; then\n    echo \'Fill worker is gone without an exit receipt\' >&2; exit 1\n  fi\n  if (( SECONDS >= FILL_DEADLINE )); then\n    echo \'Fill wait exceeded its maximum\' >&2; exit 1\n  fi\n  FILL_REMAIN=$((FILL_DEADLINE - SECONDS))\n  sleep "$(( FILL_REMAIN < 60 ? FILL_REMAIN : 60 ))"\ndone\ntest "$(cat "$P/a/1.txt")" = 0\n# END FILL_WAIT\nbash "$D/o_cpu.sh"\n```\n\n`o_place.sh` verifies the inner archive and places it at `$P=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}`. `o_pull_fill.sh` acquires the permanent attempt lock `$P/a/0.lock`, launches one detached nohup worker, and returns its PID in `$P/a/0.txt`. The worker logs to `$P/a/0.log` and writes its exit status to `$P/a/1.txt` on success or failure. Run the wait on the same host that launched the detached worker. It checks at most once per minute, refuses a vanished PID without `1.txt`, and stops after at most 14,400 seconds (four hours). A duplicate launch refuses; a failed or interrupted attempt requires a fresh package/token, never an automatic retry. The worker copies the reviewed `done` and `prep_paths` files to `$P/a/e/{5,7,8,9}`, authenticates their pins (the `.done` receipt uses whitespace-separated fields), fetches export parts `0..3` once with retries disabled, fills through `a/4.py`, and runs cont_ops\' verbatim `dryres2.py` and `dry2.py`. A failed transfer stops; the scripts do not retry it.\n\n`o_cpu.sh` requests the A4 CPU allocation explicitly: preempt, eight CPUs, 200G, four hours, no GPU, no requeue, and the excluded nodes. The **CPU allocation** is separate from the intended **general GPU read**. Wait for the CPU job to finish successfully. Preserve `$P/a/c/CPU.json`, `MEMORY.json` and the exact `SETTINGS.json` emitted by A4 prepare. Bring these small files back as one archive through the authorized transport to `$LOCAL/adopted/proof/` before the parity preparation below. Before writing CPU.json, the ON proof streams `logical/d` through its live `J.namespace(root)` to the named shared staging path `$P/a/4.tar`, outside the capped return pool. It dereferences symlinks and records `gate_assets.path`, `logical`, `sha256` and `bytes` in CPU.json. The output file is opened outside bwrap and tar writes to that descriptor. This uses the same preparation/READY as the proof, without a second staging job. A tar failure leaves no successful CPU.json and is not retried. The proof also emits exact `a/1.json`, restore, artifact-binding, manifest and export-pin receipts. These small files authenticate staging; they do not contain model weights. The proof binds payload/plan/inputs/operator, must pass bundle/entry checks and contain `memory.read_cache_bytes=12884901888` (4294967296 for processor-only), `basis=fixed_g3t_shapes`, and `fits=true`.\n\nArchive the CPU evidence on Orchard after its successful completion, using the package token printed by the build:\n\n```bash\nset -euo pipefail\nP=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}\ntar -czf "$D/2.tgz" -C "$P/a/c" CPU.json MEMORY.json SETTINGS.json RESTORE.json binding.json manifest.json EXPORT_PIN.json 1.json\nsha256sum "$D/2.tgz"\n```\n\nAfter authorized transport, authenticate and extract that archive on local scratch:\n\n```bash\nset -euo pipefail\n: "${PROOF_ARCHIVE:?Received CPU-evidence archive on local scratch}"\n: "${PROOF_SHA256:?Printed Orchard SHA256 of the CPU-evidence archive}"\nprintf \'%s  %s\\n\' "$PROOF_SHA256" "$PROOF_ARCHIVE" | nice -n 10 sha256sum -c -\nmkdir "$LOCAL/adopted/proof"\nnice -n 10 tar -xzf "$PROOF_ARCHIVE" -C "$LOCAL/adopted/proof"\n```\n\nAfter the zero-difference GPU parity gate passes, transfer its token-only `ue.json` through the authorized transport as one archive, preserving the SHA256 printed on the GPU host. The authorized owner authenticates that archive and installs the receipt before submission:\n\n```bash\nset -euo pipefail\n: "${GATE_ARCHIVE:?Received archive containing ue.json}"\n: "${GATE_SHA256:?SHA256 printed on the GPU host}"\nprintf \'%s  %s\\n\' "$GATE_SHA256" "$GATE_ARCHIVE" | sha256sum -c -\nmkdir "$D/g"\ntar -xf "$GATE_ARCHIVE" -C "$D/g"\nP=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}\ntest ! -e "$P/a/g.json"\ncp "$D/g/ue.json" "$P/a/g.json"\n```\n\nThen run:\n\n```bash\nset -euo pipefail\nbash "$D/o_sub.sh"\n# After the GPU job finishes:\nbash "$D/o_fetch.sh"\nP=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}\ntar -czf "$D/3.tgz" -C "$P/a/f" 0.tgz EXIT.json\nsha256sum "$D/3.tgz"\n```\n\n`o_sub.sh` embeds cont_ops’ A4 CPU-receipt assertions verbatim, including batch/dispatch/guard pins and MEMORY.json equality, then checks cache memory and the successful GPU receipt at `$P/a/g.json`, requires both dry checks to pass, requires an empty general queue, and refuses a return pool over **75,000,000 bytes** (including errors/symlinks). It then runs `3.py check` and one `3.py submit --gpus 1 --time 04:30:00`, saving the job ID. The GPU receipt must match the CPU restore/binding pins, filled export pin, adopted plan/profile and H100 80 GB requirement. The unchanged bootstrap itself does not require the cache-memory field; this submit preflight does. `o_fetch.sh` derives the authenticated return token and fetches `$P/a/f/{0.tgz,EXIT.json}`.\n\nTransfer `$D/3.tgz` through the authorized transport, preserving the local operator directory. Authenticate, extract and unpack it locally:\n\n```bash\nset -euo pipefail\n: "${RETURN_ARCHIVE:?Received fetched-return archive on local scratch}"\n: "${RETURN_SHA256:?Printed Orchard SHA256 of the fetched-return archive}"\nprintf \'%s  %s\\n\' "$RETURN_SHA256" "$RETURN_ARCHIVE" | nice -n 10 sha256sum -c -\nmkdir "$LOCAL/adopted/f"\nnice -n 10 tar -xzf "$RETURN_ARCHIVE" -C "$LOCAL/adopted/f"\n(cd "$LOCAL/adopted" && CUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -s -E -B ./unpack_return.py \\\n  --archive "$LOCAL/adopted/f/0.tgz" --exit "$LOCAL/adopted/f/EXIT.json" \\\n  --out "$LOCAL/adopted/ret" > "$LOCAL/adopted/unpack-success.json" && \\\n  test -s "$LOCAL/adopted/unpack-success.json")\n```\n\nA refused unpack leaves its extracted tree behind. Scorers must consume only unpack\'s **success output after exit status 0**, never a directory merely because it exists; the command\'s `&&` chain enforces that handoff. A successful partial return still has `complete=false` and must not be scored as complete. The ON unpacker refuses any existing weight receipt whose verified value is not JSON true. Processor-only journals need no weight receipt. OFF behavior remains unchanged. Whole-archive identity follows A4\'s design: fill checks the sealed whole-tar constants; job/unpack admission compare against inputs.archives[0].\n\n**Forecasts:** Package D is the 580-item distance read (B5 fork, 03:30 walltime); it has **no ON route** in a19. Its one-card **estimate** is 13,813.069 s (3 h 50 min), using the measured 23.600 s/item and crediting no cache saving. The **636-item** A4 read that a19 actually builds has an **estimate** of **7,351.824 s (2 h 02 min 32 s; 11.559 s/item)**, obtained by carrying forward the supplied A4 total, with zero assumed saving. Target weights, cache costs and staging/queue delays can change it; neither forecast measures the selected export.\n\n## GPU parity staging and acceptance\n\nThe gate must seal **A4 prepare\'s actual output plus the operator\'s per-read overrides** for the package being adopted. Do not supply an unrelated PRIVATE_SETTINGS.json. `a20 gate` checks the prepared bytes and exact RESTORE.json/artifact-binding bytes against CPU.json’s READY pins, checks export identity against the adopted step binding, checks the export-pin hash and byte count against the exact `a/1.json` bytes authenticated by CPU.json, and checks payload, plan and operator bindings. The selected export defaults to the pinned step-400 export; `--bound-export` explicitly changes it. Every GPU worker rechecks those asset bytes and the artifact manifest before reading; changing paths cannot substitute another checkpoint. It applies the authenticated operator descriptor and derives `enable_caches`, `read_cache_bytes` and the full adoption profile: candidates_argmax, memo on, g3t, empty verify IDs, save_own_depth=false, and the exact cache switches. Both the parent driver and every worker refuse a different profile. Processor-only adoption is explicitly gated with slots `[0]` and 4 GiB; all-cache adoption uses `[0,1,2]` and 12 GiB.\n\nThe **owner-only commands below are unrun here**. The shared asset archive already exists when CPU.json appears; never try to reopen the CPU job\'s private `/tmp`. Reserve storage for the archive before running `o_cpu.sh`. Its size is recorded by the job; no production archive size was measured here.\n\nAllocate the gate on Orchard, then enter its compute task. This is one non-requeued H100 job, eight CPUs, 200G and a five-hour maximum. Preserve its actual `CUDA_VISIBLE_DEVICES`; the Python guard requires exactly `NVIDIA H100 80GB HBM3`, 132 SMs, capability 9.0 and the 80 GB memory class.\n\n```bash\nset -euo pipefail\nsalloc --account=mt01 --partition=general --nodes=1 --ntasks=1 --cpus-per-task=8 \\\n  --mem=200G --gres=gpu:1 --time=05:00:00 --no-requeue \\\n  --exclude=orchard-community-2 --job-name=ab0123456789 \\\n  srun --ntasks=1 --pty bash --noprofile --norc\n```\n\nOn that H100 host, `/scratch/jjyeung` must **physically exist and be writable** outside bwrap. A4 creates `/scratch` only inside its namespace; it does not satisfy this host requirement. The operator must provision the host path before the gate. The exact logical root (currently `/scratch/jjyeung/b01ec87a6f29b`) must be absent so extraction cannot overlay another run. Preserve it so manifests and restore paths remain valid. Provision the separate opaque kit/source directories there too. Stage the source trees and public kit as single authenticated archives; keep private inputs and reverse maps on Trinity.\n\nThe shared path `$P/a/4.tar` is visible directly on Orchard. If approved transport copies it, set `ASSET_ARCHIVE` to that received path; CPU.json still supplies the expected hash and bytes. Run inside the allocation:\n\n```bash\nset -euo pipefail\n: "${PACKAGE_TOKEN:?Fresh package token from the build}"\nP=/project/community/jjyeung/okh7/a15_cot_ap${PACKAGE_TOKEN}\nASSET_ARCHIVE=${ASSET_ARCHIVE:-"$P/a/4.tar"}\nGPU_LOGICAL=$(/usr/bin/python3 -I -s -B - "$P" "$ASSET_ARCHIVE" <<\'PYASSET\'\nimport hashlib,json,sys,tarfile\nfrom pathlib import Path\np=Path(sys.argv[1]);archive=Path(sys.argv[2]);proof=json.loads((p/\'a/c/CPU.json\').read_text())\nassert proof[\'passed\'] is True\nwith tarfile.open(p/\'0.tgz\') as t:cfg=json.load(t.extractfile(\'9.json\'))\nasset=proof[\'gate_assets\'];assert asset[\'logical\']==cfg[\'logical\']\nassert asset[\'path\']==str(p/\'a/4.tar\') and archive.stat().st_size==asset[\'bytes\']\nh=hashlib.sha256()\nwith archive.open(\'rb\') as stream:\n    for chunk in iter(lambda:stream.read(1024**2),b\'\'):h.update(chunk)\nassert h.hexdigest()==asset[\'sha256\']\nprint(cfg[\'logical\'])\nPYASSET\n)\ntest -d /scratch/jjyeung && test -w /scratch/jjyeung\ntest ! -e "$GPU_LOGICAL"\nmkdir -p "$GPU_LOGICAL/d" "$GPU_LOGICAL/p"\ntar -xf "$ASSET_ARCHIVE" -C "$GPU_LOGICAL/d"\ntar -xzf "$P/0.tgz" -C "$GPU_LOGICAL/p"\ntest ! -e "$GPU_LOGICAL/d/7.json"\ncp "$GPU_LOGICAL/d/binding.json" "$GPU_LOGICAL/d/7.json"\n```\n\nCreate a private neutral configuration from `config.example.json` with separate authenticated A4 original/patched source roots. Set `export=$GPU_LOGICAL/d/e`, `export_pin=$GPU_LOGICAL/d/6.json`, and `artifact_manifest=$GPU_LOGICAL/d/7.json`. The last file is a byte-identical neutral alias for the CPU binding. Include that exact `binding.json` to `7.json` mapping in `PRIVATE_ALIASES.json`; map the other private prepared asset paths to staged opaque aliases of those same files. Keep private settings and reverse maps on Trinity. The following commands use files under `$LOCAL`:\n\n```bash\nset -euo pipefail\n: "${PRIVATE_CONFIG_TEMPLATE:?Private neutral GPU configuration with staged asset paths}"\n: "${PRIVATE_ALIASES:?Private JSON mapping preparation paths to staged opaque paths}"\nPRIVATE_SETTINGS="$LOCAL/PRIVATE_SETTINGS.json"\nPRIVATE_CONFIG="$LOCAL/PRIVATE_NEUTRAL_CONFIG.json"\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a20.py" --enable-extensions gate \\\n  --operator "$LOCAL/adopted" --prepared "$LOCAL/adopted/proof/SETTINGS.json" \\\n  --proof "$LOCAL/adopted/proof/CPU.json" --config "$PRIVATE_CONFIG_TEMPLATE" \\\n  --asset-receipts "$LOCAL/adopted/proof" --bound-export "$BOUND_EXPORT" \\\n  --settings-out "$PRIVATE_SETTINGS" --config-out "$PRIVATE_CONFIG"\n```\n\n```bash\nset -euo pipefail\nmkdir -p "$LOCAL/public"\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a11.py" seal \\\n  --source-root "$EXT_SOURCE" --input "$PRIVATE_SETTINGS" --aliases "$PRIVATE_ALIASES" \\\n  --out "$LOCAL/public/u3"\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a11.py" stage-kit \\\n  --source-root "$EXT_SOURCE" --input "$DELIVERY/kit_parity50" \\\n  --config "$PRIVATE_CONFIG" --out "$LOCAL/public/u0"\n```\n\nThe package embeds the driver/comparator SHA256 and the deterministically sealed sample SHA256 from MANIFEST `kit_files`. The driver and every worker authenticate those executing bytes, and `ue.json` carries them to SUBMIT_CHECK. The staged `u3.json` pins every extension; `u4.json` authenticates both full 927-file base inventories. The driver rejects changed bases, equal original/patched roots, and an original root containing extensions. It authenticates the sealed sample bytes and the logical sample pin. Transfer only the staged directory through the approved transport under an opaque root.\n\nOn an assigned **H100 80 GB** GPU, run the acceptance command below; it is **unrun here**. Preserve that allocation\'s actual `CUDA_VISIBLE_DEVICES`.\n\n```bash\nset -euo pipefail\nnice -n 10 "$READ_PYTHON" -I -s -B /scratch/jjyeung/ab0123456789/u0/u0.py \\\n  /scratch/jjyeung/ab0123456789/u0/u2.json --out /scratch/jjyeung/ab0123456789/u9 \\\n  --enable-gpu --public --repeat-baseline --shards 4\n```\n\nEvery arm starts a fresh process. ORIGINAL/OFF/OFF_REPEAT use ordinary journals and modulo shards. ON tests caches; ON_JOURNAL and sequential whole-scene shards test separate journal/shard features. Sequential shards establish equality, not parallel speed. Public logs tokenize item/native/room identities and arbitrary stdout/stderr. No reverse map is written on Orchard.\n\nAcceptance requires all 50 expected IDs, complete production output schemas, nonempty text/tokens/heads, scale even when null, every served response and forced-token count, matching call counters, and **zero semantic byte differences**. ORIGINAL/OFF must also retain every production source hash. Each enabled cache must report its memory bound and useful hits; SAM needs both feature and detection hits. Empty or all-miss runs fail. Only clocks and explicit audit/cache/memo telemetry are excluded from semantic comparison; audit violations fail. There is no answer/trace tolerance.\n\nEach RUN.json records the adopted package plan, read profile, asset pins, required device type, actual device, cache slots and budget. The worker checks CUDA device properties before model loading and refuses a different exact name, SM count, compute capability or memory class. `ue.json` is written only after all comparisons finish and records whether they all passed; failed or missing receipts cannot authorize submit. On the H100 host, archive it with `tar -cf /scratch/jjyeung/ab0123456789/5.tar -C /scratch/jjyeung/ab0123456789/u9 ue.json` and print `sha256sum /scratch/jjyeung/ab0123456789/5.tar` for authenticated return transport. Judge net time from `RUN.json`\'s `worker_wall_seconds`, which includes install/boundary hashing and eager SAM loading. Per-item timing alone cannot establish savings. ON constructs SAM outside inference mode to obtain tracked parameters; that changes loading time and potentially RNG use. The GPU byte gate must clear it. The sample overrepresents clip reuse: its ten distance items share one clip, while A4 has 150 distance items across 60 clips (review finding 7).\n\nThe cache cap covers retained cache storage and transient copies, not model/caller working memory. Measure full-process host/GPU peaks. Models must remain frozen: calls check parameter/buffer identities, pointers and counters; install/type boundaries hash content. Persistent raw writes fail at a boundary. Raw writes restored between boundaries, private tensor attributes and arbitrary non-tensor state are outside this guard\'s coverage. Graceful stops verify journals; a hard kill can leave an unchecked journal that requires fresh output.\n\nOutput directories u0–u5 represent ORIGINAL/OFF/OFF_REPEAT/ON/ON_JOURNAL/SHARDED. Reports u6–ua compare arms; ub.json checks merge equality; uc/ud contain canonical single/sharded returns. Restore on Trinity with the private inputs:\n\n```bash\nset -euo pipefail\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a11.py" restore \\\n  --source-root "$EXT_SOURCE" --input PRIVATE_RETURN --out "$LOCAL/restored" \\\n  --private-source "$DELIVERY/kit_parity50/sample50.json" \\\n  --private-source "$PRIVATE_CONFIG" --private-source "$PRIVATE_SETTINGS"\n```\n\nRestoration authenticates committed rows before rebuilding private IDs/checksums. Merge with the original manifest through the explicit extension entrypoint. The canonical answer/trace archive must match exactly; transport-envelope clocks remain variable.\n\n## Array validation\n\nNo multi-card A4 operator is delivered. The array helper is a separate inert prototype. Its example has `approved=false`: two one-hour shards, at most two attempts, four GPU-hours total. Approval must bind the exact partition, shards, time and attempts, with no more than five allocated GPU-hours over all attempts. Before any sharded/preempt adoption, validate real persistent-storage preemption/requeue.\n\n```bash\nset -euo pipefail\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a15.py" PRIVATE_ARRAY_CONFIG.json \\\n  --enable-array --token ab0123456789 --out "$LOCAL/array-plan" \\\n  --python /scratch/jjyeung/ab0123456789/u1 --source /scratch/jjyeung/ab0123456789/u2 \\\n  --staged-config /project/community/jjyeung/okh7/a15_cot_apab0123456789/u3.json\n```\n\nThis writes commands without running them. Exit 75 requests bounded requeue; other errors remain failures. Lock waits stop after 60 seconds, and the attempt limit forbids more work. Public paths must use approved roots and pass the forbidden-word screen; name checks do not establish storage permissions or capacity.\n\nNo delivered CPU suite or single-GPU kit requires a local OS socket. StageOneSocket is a Python callback. Real restore, bwrap isolation, remote transport, GPU parity/performance/memory and persistent requeue remain unrun.\n\n## Review round 7: finding -> fix -> test\n\n| Finding | Fix | Regression |\n|---|---|---|\n| 1. Private root disappears | Archive inside CPU proof to `$P/a/4.tar` before CPU.json; record hash/bytes. | Real fixture tar runs through a namespace wrapper, survives loss of the root, and the CPU operator fixture executes staging. |\n| 2. Fill wait hangs | Guard PACKAGE_TOKEN, check PID and cap wait at four hours. | Missing token, dead PID, timeout and failed exit refuse; success passes. |\n| 3. PCIe accepted | Require exact HBM3 name and 132 SMs. | SXM stub passes; PCIe and wrong-SM stubs refuse. |\n| 4. Evidence/host nits | Bind executing kit/comparator/sample; include a/1.json; unpack with -s -E -B; use an H100-local archive path. | Mutated pins refuse, environment-polluted unpack succeeds, allocation/evidence blocks are checked. |\n| 5. Decision export | Default to the supplied step-400 export; require an explicit parameter for other exports. | Step 400 passes by default; synthetic step 600 passes only when selected; wrong artifact refuses. |\n\nFrozen weights remain required. Persistent raw writes are boundary-checked; writes restored between boundaries remain outside the guard. GPU byte equality and performance remain unrun.\n'

======================================================================
FAIL: test_info_tar_stderr_is_retained (__main__.Round8Tests.test_info_tar_stderr_is_retained)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round8.py", line 99, in test_info_tar_stderr_is_retained
    err=root/'results/4.err';self.assertTrue(err.exists(),'Tar stderr was discarded')
                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: False is not true : Tar stderr was discarded

----------------------------------------------------------------------
Ran 10 tests in 4.169s

FAILED (failures=29)
```

```bash
READ_NODE4_BEFORE=1 bash work/cpu.sh work/run_fixture5.py work/src/u0/tests/test_round4.py Round4Tests.test_f2_bound_real_job_and_rehearsal_memory
```

Exact output:

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
Ran 1 test in 8.718s

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
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round3.py", line 189, in test_f4_worker_uses_settings_argv_without_environment_side_effect
    self.assertNotIn('H10_SETTINGS',kit.os.environ)
AssertionError: 'H10_SETTINGS' unexpectedly found in {'CUDA_VISIBLE_DEVICES': 'fixture', 'H10_SETTINGS': '/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/c598a3cc708f44869f19e78cf64a4b3e/u0.json'}

----------------------------------------------------------------------
Ran 1 test in 0.843s

FAILED (failures=1)
```

The final seal runs `bash work/cpu.sh work/integrity8.py`. Its exact output is [integrity8.txt](checks/integrity8.txt); [FINAL_INTEGRITY.json](checks/FINAL_INTEGRITY.json) pins this report, the note, MANIFEST, diffs and evidence. Seal output stays external to avoid a report/hash cycle.
