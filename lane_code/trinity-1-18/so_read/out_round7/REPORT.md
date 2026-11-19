VERDICT: DONE All five LOW findings and the two actionable INFO items pass CPU verification; production adoption requires the bound H100 GPU byte gate.

Measured validation: **111 workspace tests and 30 fresh-application tests pass**. The nine round-6 regressions fail on the reviewed snapshot with **31 expected assertion failures**, then pass on the delivered implementation. The baseline includes the actual `ModuleNotFoundError` from the README unpack subprocess. All retained before-fix controls reran. Five diffs apply with zero fuzz; all original reader files and original/OFF output bytes remain unchanged. ON CPU fixtures retain exact answers and traces. GPU ON/OFF equality remains unmeasured and mandatory.

Measured resources: the suite's largest child-process peak RSS was **400,371,712 bytes**; the separate guard benchmark peak was **1,334,685,696 bytes**. These are process peaks, not GPU memory measurements. The workspace measured **2,811,877,501 unique-inode bytes** at report generation, below 3,000,000,000. Immutable completed fixtures share identical bytes through hard links; all paths were preserved. [STORAGE6.json](checks/STORAGE6.json) and [storage6.txt](checks/storage6.txt) record the sharing. The task observed no workspace-cap violation.

The supplied existing A4 timings support an **estimate** of **7,351.824 s for the 636-item read**, with zero credited cache saving. The separate Package D estimate is **13,813.069 s for 580 distance items**; a19 has **no ON route** for Package D. Neither number measures a step-600 GPU run.

Work began at **15:13:03 UTC on 2026-11-19**; the deadline is **16:13:03 UTC**. This report was generated at Thu Nov 19 15:37:41 UTC 2026. The original delivery is preserved in [out_round6](../out_round6/). CPU execution used torch 2.11.0+cpu, transformers 5.12.1, eight torch threads, nice -n 10, and CUDA hidden. No Git, SSH, scheduler action, GPU execution, paid API, input-tree edit or deletion command ran. Network reads covered official PyTorch documentation only.

## Review round 6: finding -> fix -> test


| Finding | Fix | Regression |
|---|---|---|
| 1. Unpack import fails | Run `-s -B` from the operator directory. | Execute the README command as a subprocess on an authenticated fixture return. |
| 2. Foreground pull/fill | Detached nohup worker, permanent attempt lock, PID/log and exit file; no retries. | Success 0 and failure 17 both report completion; duplicate launch refuses. |
| 3. Weak submit receipt | Embed every cont_ops A4 CPU assertion, then enforce cache and pool checks. | Batch/guard/action/argv/events/memory tampering and a resealed stale batch fail. |
| 4. Unpinned copied members | Pin all A4 copied members, base batch and decoded bootstrap before output. | Mutations of each additional member and bootstrap pin refuse before writing. |
| 5. Unbound checkpoint/device | READY restore/binding pins and export identity bind step-600 assets; workers recheck assets and require H100 80 GB. | Changed receipts, wrong step, changed staged files and non-production GPU properties fail. |
| INFO: receipt whitespace | Compare the three whitespace-separated fields. | Tabs/newlines pass; extra fields fail. |
| INFO: manual GPU handoff | Submit requires the successful token-only GPU receipt for the same plan/profile/assets/device. | Failed, absent, stale or mismatched evidence refuses. |

The binding retains Orchard `done`/`prep_paths` as authenticated operation metadata; admission still checks its fixed identity keys. Persistent raw writes remain boundary-checked; restored-between-boundary raw writes remain unsupported and require frozen model ownership. These informational limits do not change reader behavior.


The two remaining INFO notes stay documented. `done` and `prep_paths` are inert, authenticated operation metadata; removing them would disrupt the operation plan without improving admission. Restored-between-boundary raw writes cannot be caught by the reviewed identity/counter checks; detecting them would require stronger interception or per-call content hashing, which changes the reviewed cost contract. Existing path-preservation and weight-guard regressions still run.

The detached fill is a single attempt. Its permanent `a/0.lock` prevents concurrent or repeated launches; nohup detaches the entire pull/fill/dry sequence; the EXIT trap records success or failure in `a/1.txt`. Tests exercise the generated launcher, lock, log and exit trap with tiny success/failure commands. They do not fetch the roughly 21.6 GB production export. A hard kill can leave no exit receipt; the owner inspects the log and starts a fresh token rather than retrying the same attempt.

The submit checker embeds the complete assertion block from `cont_ops17/work/o_sub_A4.sh:7-37` verbatim. It retains cache-budget and return-pool checks. The added GPU receipt is token-only and binds success, plan, profile, restore/binding/export pins and the H100 80 GB requirement. The CPU integration uses the actual fixture CPU proof, verifies its emitted asset receipts, exercises receipt serialization and proves that a failed GPU receipt refuses submission. Its synthetic receipt is a test control, not GPU evidence.

The gate checks exact RESTORE.json and artifact-binding hashes against CPU READY, plus run/step/member/lineage/object/config/archive/preparation identity against the adopted binding. Workers recheck staged receipt bytes and the manifest hash. The original loader then verifies every pinned checkpoint/component file before model loading (`b/e2e_reader/parity.py:190-196`, `b/e2e_reader/artifact.py:109-120`). Preserving the CPU logical root keeps those pinned paths valid. The README stages a neutral byte-identical binding alias at `d/7.json`; private settings must map to the same file.

Device checks use the CUDA properties for device 0 and refuse a non-H100 name, a capability other than 9.0, or total memory outside 79–86 billion bytes. This is a production device-class policy; MIG and the 94 GB NVL variant fail closed. CPU tests supply explicit property stubs. Actual H100 compatibility and performance remain unrun.

## Adoption contract

Follow [README](kit_parity50/README.md) in order. Apply reader patches 01–03 and operator patches 04–05 to fresh A4 copies. Derive the real reviewed step-600 binding; build with `u0/a19.py --enable-extensions --manifest ... --extension-pins ...`; generate and place the pinned operations; run detached fill and require exit 0; obtain the allocated CPU proof and emitted receipts; stage the same assets; pass the GPU gate; authenticate/install its `ue.json` as `a/g.json`; submit; fetch and unpack.

The default profile is A4's 636 items, one GPU, general/no-requeue, caches only, with a 12 GiB host-cache allowance. `--processor-only` selects 4 GiB and requires its own gate. Both leave scene sharding and atomic journals disabled. No multi-card A4 operator is delivered. Owner transport, allocations, the real target binding and storage capacity remain external inputs.

A refused unpack leaves its extracted tree behind. Scorers must use only success output after unpack exit status 0; `complete=false` remains partial. The documented command runs `-s -B` from the operator directory and gates its handoff with `&&`.

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

**Estimate for what a19 builds:** the 636-item A4 schedule takes about **7,351.824 s (2 h 02 min 32 s; 11.559 s/item including fixed overhead)** if the supplied A4 throughput carries forward, with zero assumed cache saving. This is not a step-600 measurement. Target weights, cache guard/copy costs, actual reuse and staging can change it.

**Separate Package D estimate:** the 580-item distance read is a B5 fork with a 03:30 walltime and has **no ON route in a19**. Using 23.599762 s/item plus 75.446133 s loading and 49.761372 s overhead gives an estimate of **13,813.069 s (3 h 50 min)** on one card. Ideal two/four balanced-shard estimates are 6,969.138 / 3,547.173 s; they require an undelivered multi-card operator and exclude scene imbalance, staging, queues and preemption. The fixed 50-item reuse-heavy sample cannot establish these throughput estimates.



## Measured CPU guard overhead

Each stub uses bf16 parameters shaped 2048×1024 and a 1024-element buffer per module. Forward returns a 32-element tensor without model-sized matrix work. Each implementation runs one miss and a warm hit, then seven timed hits; boundary cost is the median of three hashes. These are CPU cache costs, not GPU speedups. Exact samples are in [CACHE_COST3.json](checks/CACHE_COST3.json).

| Parameters | Parameter/buffer tensors | Weight+buffer bytes | Per-call hashing ms | Boundary guard ms/call | Install s | Boundary s |
|---:|---:|---:|---:|---:|---:|---:|
| 268435456 | 128/128 | 537133056 | 394.252 | 28.902 | 0.392 | 0.430 |
| 536870912 | 256/256 | 1074266112 | 797.468 | 60.229 | 0.829 | 0.781 |

## Framework and source evidence

[FRAMEWORK_EVIDENCE](FRAMEWORK_EVIDENCE.md) provides installed torch/transformers file:line citations and official documentation links. The new device guard relies on `torch/cuda/__init__.py:641-695` and `torch/_C/__init__.pyi:12448-12453`. [SOURCE_EVIDENCE6.json](checks/SOURCE_EVIDENCE6.json) pins those files and the cont_ops submit reference. The official [device-properties](https://docs.pytorch.org/docs/2.11/generated/torch.cuda.get_device_properties.html) and [capability](https://docs.pytorch.org/docs/2.11/generated/torch.cuda.get_device_capability.html) pages were checked on 2026-11-19. [TORCH_VERSIONS3.json](checks/TORCH_VERSIONS3.json) contains the rerun mutation-counter probes. No GPU property was queried locally.

## Patches and authentication

A4 source base: `813fe4c57b2deed4bd731dd1e3493b6b0bed8d31e7bff92ff112cf5c9df823c3` over 927 files. Reviewed payload: `4498fca72a8e4b476b38f097ffdf3ff88b5aa20fc036bd196b18a5706e9fe46d` (5252958 bytes). B5 base archive: `ac2e259025d6a821aa5eb13e236f0635bd970313859086fc2f3ce3276647f2f0`. B5 validation proves applicability; the GPU kit authenticates A4.

| Patch | Bytes | SHA256 |
|---|---:|---|
| [01_bounded_read_caches.diff](patches/01_bounded_read_caches.diff) | 90430 | `369af9663fbc1008f9ecf5a32c5067ba4a5f4cd31412f07db8263b13b23fd4c3` |
| [02_atomic_scene_shards.diff](patches/02_atomic_scene_shards.diff) | 218841 | `5f76cf79e29471138161e476daf3920ec2bcbf751586fc47528fbd7388530cfa` |
| [03_production_integration.diff](patches/03_production_integration.diff) | 193367 | `070a12fee6fc24a9a691e78fa48f9f3768b0138234608faf55a091030bcaa79b` |
| [04_operator_cache_bound.diff](patches/04_operator_cache_bound.diff) | 2723 | `0d3bdc2d943554cd525627466d2d71f30881884e76df95204ede6c1accdb9061` |
| [05_operator_return_and_proof.diff](patches/05_operator_return_and_proof.diff) | 3779 | `35322b12677d59487181a28a070352526816d8ab11f581f9344f466d1c71f5cb` |

Reader patches add 36 files under `u0/`, including the regression tests. Operator patches remain behind `read_extensions`; the ON CPU helper additionally exports the small asset receipts. The original bootstrap bytes remain unchanged. MANIFEST records the six additional copied-member pins, base batch and decoded-bootstrap pins, patched operator hashes, complete source inventories, kit and operation files. The builder requires all those applicable pins before copying. Fresh-application OFF, round-4/5/6 and comparator suites pass; the applied extension bytes equal the workspace-tested bytes.

The development source copy contains 85 original reader files; their bytes match the base, and tests obtain the remaining immutable resources through READ_INPUT_SRC. The fresh applied source contains and authenticates all 927 original files. The final seal checks both inventories explicitly.

## What could go wrong and how we would notice

| Risk | Detection and action |
|---|---|
| Wrong A4 member, base batch, bootstrap or extension | Builder refuses the pin mismatch before creating output. |
| Interrupted fill or duplicate launch | Permanent attempt lock refuses duplicates; log and exit receipt distinguish completion. Missing receipt requires inspection and a fresh token. |
| Stale CPU proof or jointly resealed batch/package | Full cont_ops receipt assertions compare the proof with current batch, dispatch, guard, input, operator and memory bytes. |
| Wrong checkpoint or modified staged files | READY/identity checks, per-worker receipt/manifest checks and original component hash verification refuse. |
| Missing, failed or unrelated GPU evidence | Submit requires `a/g.json` for this plan/profile/assets/device. A CPU proof alone cannot authorize the read. |
| Namespace or alias differs from CPU staging | Path validation, asset checks or the original loader fails before reading; preserve the logical root and neutral alias bytes. |
| GPU kernels or eager SAM change answer/trace bytes | Require zero byte differences; equal scores do not waive the gate. |
| Cache overhead erases savings or process memory exceeds cache caps | Compare full worker wall time and measure host/GPU peaks on the real allocation. |
| Raw tensor write restored between boundaries | Frozen ownership remains required; that sequence is outside guard coverage. Persistent raw writes fail a boundary check. |
| Refused or partial return is scored | Require unpack exit 0 and success JSON, then inspect complete status. |

## Not done

No real step-600 export/binding, large pull, production restore, namespace/transport/storage run, GPU parity/performance/memory measurement, scheduler submission, upload, return publication or persistent-storage requeue ran. No batching or multi-card A4 operator is delivered. The array policy remains approved=false. Delivered CPU suites need no local OS sockets.

The first complete-suite attempt caught a non-opaque path in the staging example; [run_checks6_development.txt](checks/run_checks6_development.txt) retains that failure. The corrected example passes the full rerun. No cluster kill or automatic relaunch occurred. The requested review audit sections below are retained because the binding prompts explicitly require them.

## Required review audit sections

## Review round 5: finding -> fix -> test


| Finding | Fix | Regression |
|---|---|---|
| 1. Dropped batch wrapper | Exact cont_ops wrapper retains exclusion, EXIT log and USR1 forwarding. | Built script equals wrap_batch output and passes the real a/5.py bundle guard. |
| 2. Unpinned build inputs | Reviewed A4 payload, operator MANIFEST pins, extension inventory and alias bases must match before copying. | Changed self-consistent payload, each operator, extensions and alias pins are refused before output. |
| 3. Incomplete operations | Binding derivation, delivery archive/SHA, place/fetch/fill/dry/allocated-proof/guarded-submit/fetch scripts and gated unpack command. | Generated shell syntax, delivery members and command order pass; actual submit checker refuses missing cache proof and an oversized pool. |
| 4. Unbound GPU profile | Prepare bytes plus operator overrides bind settings, selectors, budget and package plan. | Both cache profiles pass; changed settings, selectors, cap and plan fail. |
| 5. Forecast scope | Package D and a19's A4 schedule have separate labelled estimates. | Documentation regression requires both scopes and A4's 7,351.824 s estimate. |
| 7. Refused unpack tree | Scorers require success output after exit 0; the shell handoff uses &&. | Documentation regression checks the warning and executable success chain. |



## Review round 4: finding -> fix -> test

| Finding | Fix | Evidence |
|---|---|---|
| 1 MEDIUM: step-600 build drops A4 run keys, export binding and compatible helper | The explicit a19 builder uses cont_ops' build_r1-style post-processing over A4's authenticated payload. It retains 8.py, admission/vendor bytes and every A4 run key, installs the ON overlays, and seals the reviewed target binding into 9.json. It retargets A4's fill-helper object/size/hash constants and rebuilds every affected pin. The incomplete a12 operator route is refused. | test_f1 checks target binding, payload pins, A4 keys and helper bytes/compatibility. The real admission rejects changed run, step, member, lineage, object, config, archive or preparation hashes. The fill helper rejects changed whole-tar identity/receipt. The documented reviewed build fails this test on the missing stage1 rule. |
| 2 LOW: hand-built action config and generic profile hide adoption failures | A4's CPU-proof helper propagates read_extensions into the real 7.py rehearsal. The test reads packaged 9.json as-is and runs real job.main to construct a/0.json and a/1.json; it only translates namespace paths and stubs storage/device/model work. | test_f2 runs real preparation, rehearsal, bootstrap admission, operator and runner/action-2 dispatch. MEMORY.json contains 12,884,901,888 cache bytes. All 636 items complete in five ordinary journals, each with verified=true; no atomic commit store or canonical merge exists. The old route fails preparation. Independently, the original CPU-proof helper fails with None != 12884901888. |
| 3 LOW: cache-only return accepts unchecked weights | With read_extensions=true, unpack_return refuses an existing WEIGHTS.json unless verified is exactly JSON true. OFF retains its existing path. | The same test accepts missing/true receipts, refuses false/null/0/1/string values, and retains OFF behavior. All five invalid-value assertions fail on reviewed code. The real authenticated unpack entry accepts a verified partial return and rejects an unverified partial return. |
| 9 INFO: non-delivery paths, B5 base claim, proof-field wording | README uses explicit delivery/source/scratch variables; the kit is A4-only. It distinguishes the generated cache-memory proof from unchanged bootstrap admission. | The CPU integration uses the delivered Python tools and asserts the generated cache allowance. The kit authenticates complete A4 inventories; B5 applicability is limited to the separate patch-application check. |


### Review round 1: finding -> fix -> test

Typed keys, complete parity schemas, original/OFF provenance, frozen identity, lock-held recovery, opaque transport and bounded storage retain passing tests. All eight reviewed-baseline regressions fail as expected.

### Review round 2: finding -> fix -> test

Isolated entry, path policy, bounded array retries, pinned overlays, SAM capacity, deadline counts, lock waits, cache bypass accounting, source-root checks and worker setup retain passing tests. All thirteen reviewed-baseline regressions reproduce, including both CLI variants.

### Review round 3: finding -> fix -> test

Install/type-boundary hashes and cheap fatal live guards, processor-only mode, operator memory/overlay dispatch, full base authentication, behavioral lock/worker regressions and the OFF import guard retain passing tests. The generic operator test checks the atomic nested merge; the round-4 test checks the actual cache-only adoption profile. The OFF guard now includes a0–a19. All round-3 failing baselines reproduce.

These audit sections retain finding history only because the dispatch explicitly requires it. Other sections state the delivered behavior and current evidence.



## Commands and exact outputs

Commands ran from `/scratch/jjyeung/orch_n30/so_read`. `work/cpu.sh` exports CUDA_VISIBLE_DEVICES="", OMP/MKL/OPENBLAS threads=8, TOKENIZERS_PARALLELISM=false, PYTHONDONTWRITEBYTECODE=1 and scratch caches, then executes the required Python with `nice -n 10 -I -s -B`. Tests set eight torch threads. Child commands inherit priority and environment. Fixture storage shares identical immutable input bytes and detaches shared files before edits.

The README unpack subprocess intentionally uses `-s -B` without `-I`, as finding 1 requires, so the authenticated sibling helper can import. Its interpreter, CPU environment and priority remain the same.

Test commands additionally use READ_INPUT_SRC=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/A4/src and READ_TEST_TMP=/scratch/jjyeung/orch_n30/so_read/work/test-artifacts. Applied commands use READ_OPERATOR_SOURCE and READ_OPERATOR4_SOURCE from the fresh verification root. Every output below is literal; baseline failures are expected regression controls.

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
round4: CPU step-600 fixture: /scratch/jjyeung/orch_n30/so_read/work/test-artifacts/9bf19b9fec6744d7a063f2a3f1489cc3
round5: All CPU receipt checks passed
round6: Detached fill: success=0, failure=17, duplicate launch refused.
kit: OK
kit_launch: OK
PASS: all 8 round-1 regressions fail against the round-1 reviewed implementation.
PASS: all 13 round-2 regressions fail against the round-2 reviewed implementation (14 failures including both CLI variants).
PASS: round3_before reproduces FAILED (failures=15).
PASS: operator3_before reproduces FAILED (failures=2).
PASS: lock3_before reproduces FAILED (failures=2).
PASS: round5_before reproduces FAILED (failures=11).
PASS: round6_before reproduces FAILED (failures=31).
PASS: round4_before reproduces FAILED (failures=7, skipped=1).
PASS: node4_before reproduces FAILED (failures=1).
PASS: f16_behavior_before reproduces FAILED (failures=1).
PASS: Python syntax, shell syntax, and default-off execution guards.
{"cuda_visible_devices": "", "max_child_rss_bytes": 400371712, "torch": "2.11.0+cpu", "torch_threads": 8, "transformers": "5.12.1", "workspace_bytes": 2771577384}
```

```bash
bash work/cpu.sh work/run_fixture5.py work/build_patches.py
```

Exact output:

```text
PASS: 3 additive reader diffs (36 files) plus 2 default-OFF A4 operator diffs; zero-fuzz application; unchanged original reader hash trees.
PASS: OFF, round-4/5 integration and comparator suites pass from the fresh applied A4 tree; both complete 927-file base inventories authenticate.
Applied verification root: /scratch/jjyeung/orch_n30/so_read/work/apply-round6/751d7f0734d3447783f9b391cfd4d0f2
```

```bash
bash work/cpu.sh work/gate_integration6.py
```

Exact output:

```text
All CPU receipt checks passed
{"passed": true, "pool_bytes": 0}
PASS: exact CPU-emitted restore/binding/export receipts feed the gate; staged bytes and manifest recheck.
PASS: real bundle/entry/memory CPU proof passes cont_ops assertions; synthetic failed GPU receipt refuses.
No GPU evidence was measured: receipt serialization used explicit synthetic pass/fail controls.
{"assets": {"binding": "9637c68a4c624249ad55ee5922c177466c155c3c4cddd9077b5b0fb4bbf7ed04", "export_pin": "094d8d36773012097318172d96befb844805aae9e4a785e65a4f9454d2c7ec9e", "restore": "44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a"}, "plan": "3a271f9f0b5263eec6f3cc0f1eb58482bd69b6919ad2eee5209d1b5c26bd56ec", "required_device_type": "H100_80GB"}
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
        "data_ptr": 132456256,
        "object_id": 139840171418448,
        "version": 1
      },
      "before": {
        "data_ptr": 132456256,
        "object_id": 139840171418448,
        "version": 0
      },
      "object_changed": false,
      "operation": "parameter.add_",
      "pointer_changed": false,
      "version_changed": true
    },
    {
      "after": {
        "data_ptr": 132466752,
        "object_id": 139840171418768,
        "version": 1
      },
      "before": {
        "data_ptr": 132466752,
        "object_id": 139840171418768,
        "version": 0
      },
      "object_changed": false,
      "operation": "detach().add_",
      "pointer_changed": false,
      "version_changed": true
    },
    {
      "after": {
        "data_ptr": 132467392,
        "object_id": 139840171418448,
        "version": 0
      },
      "before": {
        "data_ptr": 132467392,
        "object_id": 139840171418448,
        "version": 0
      },
      "object_changed": false,
      "operation": "parameter.data.add_",
      "pointer_changed": false,
      "version_changed": false
    },
    {
      "after": {
        "data_ptr": 132470016,
        "object_id": 139840171418768,
        "version": 0
      },
      "before": {
        "data_ptr": 132467776,
        "object_id": 139840171418768,
        "version": 0
      },
      "object_changed": false,
      "operation": "parameter.data assignment to cloned storage",
      "pointer_changed": true,
      "version_changed": false
    },
    {
      "after": {
        "data_ptr": 132470336,
        "object_id": 139840171418448,
        "version": 0
      },
      "before": {
        "data_ptr": 132470336,
        "object_id": 139840171418448,
        "version": 0
      },
      "object_changed": false,
      "operation": "parameter.data assignment to same storage",
      "pointer_changed": false,
      "version_changed": false
    },
    {
      "after": {
        "data_ptr": 132470528,
        "object_id": 139840171418768,
        "version": 0
      },
      "before": {
        "data_ptr": 132470528,
        "object_id": 139840171418768,
        "version": 0
      },
      "object_changed": false,
      "operation": "numpy raw storage write",
      "pointer_changed": false,
      "version_changed": false
    },
    {
      "after": {
        "data_ptr": 132470592,
        "object_id": 139840171418448,
        "version": 1
      },
      "before": {
        "data_ptr": 132470592,
        "object_id": 139840171418448,
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
      "after_install_seconds": 0.3923319079913199,
      "after_per_call": {
        "max_seconds": 0.032248938921839,
        "median_seconds": 0.028901728335767984,
        "min_seconds": 0.028460956178605556,
        "seconds": [
          0.029457141179591417,
          0.029063791036605835,
          0.028901728335767984,
          0.028482078574597836,
          0.028460956178605556,
          0.028683640994131565,
          0.032248938921839
        ]
      },
      "before_install_seconds": 5.37908636033535e-05,
      "before_per_call": {
        "max_seconds": 0.537929771002382,
        "median_seconds": 0.39425168791785836,
        "min_seconds": 0.3768933368846774,
        "seconds": [
          0.389938126783818,
          0.3983989697881043,
          0.537929771002382,
          0.3854467491619289,
          0.3768933368846774,
          0.4312117942608893,
          0.39425168791785836
        ]
      },
      "blocks": 128,
      "boundary": {
        "max_seconds": 0.4415983557701111,
        "median_seconds": 0.4302190849557519,
        "min_seconds": 0.4018775480799377,
        "seconds": [
          0.4018775480799377,
          0.4302190849557519,
          0.4415983557701111
        ]
      },
      "buffer_shape": [
        1024
      ],
      "buffer_tensors": 128,
      "dtype": "bfloat16",
      "median_speed_ratio": 13.641111124483974,
      "parameter_count": 268435456,
      "parameter_shape": [
        2048,
        1024
      ],
      "parameter_tensors": 128,
      "weight_and_buffer_bytes": 537133056
    },
    {
      "after_install_seconds": 0.8292312738485634,
      "after_per_call": {
        "max_seconds": 0.06197645561769605,
        "median_seconds": 0.060229025315493345,
        "min_seconds": 0.05963139794766903,
        "seconds": [
          0.05963139794766903,
          0.06004501832649112,
          0.05970699107274413,
          0.060229025315493345,
          0.061858517583459616,
          0.06197645561769605,
          0.06118130311369896
        ]
      },
      "before_install_seconds": 5.66849485039711e-05,
      "before_per_call": {
        "max_seconds": 0.8657932351343334,
        "median_seconds": 0.7974681537598372,
        "min_seconds": 0.7501520323567092,
        "seconds": [
          0.8657932351343334,
          0.811951152049005,
          0.7910035462118685,
          0.7974681537598372,
          0.7501520323567092,
          0.7751497533172369,
          0.8183510722592473
        ]
      },
      "blocks": 256,
      "boundary": {
        "max_seconds": 0.8283837935887277,
        "median_seconds": 0.7812584768980742,
        "min_seconds": 0.7713759420439601,
        "seconds": [
          0.8283837935887277,
          0.7812584768980742,
          0.7713759420439601
        ]
      },
      "buffer_shape": [
        1024
      ],
      "buffer_tensors": 256,
      "dtype": "bfloat16",
      "median_speed_ratio": 13.240595370463284,
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
  "max_rss_bytes": 1334685696,
  "nice": 19,
  "threads": 8,
  "torch": "2.11.0+cpu"
}
```

```bash
bash work/cpu.sh work/docs_check6.py
```

Exact output:

```text
PASS: 15 README shell blocks parse; owner operations were not executed.
PASS: complete cont_ops A4 CPU assertion block is verbatim; SUBMIT_CHECK parses as Python 3.6.
PASS: changed operator helpers parse as Python 3.6.
PASS: source hashes and official device-property references recorded; no CUDA call executed.
```

```bash
bash work/cpu.sh work/share_storage6.py
```

Exact output:

```text
Immutable fixture paths preserved: 7501 unique bytes shared: 220399888
2661710793	/scratch/jjyeung/orch_n30/so_read
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
Ran 15 tests in 2.895s

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
Ran 13 tests in 0.126s

OK
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_off.py
```

Exact output:

```text
test_every_output_byte_and_source_hash_matches_original (__main__.OffContractTests.test_every_output_byte_and_source_hash_matches_original) ... ok

----------------------------------------------------------------------
Ran 1 test in 5.755s

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
Ran 17 tests in 4.593s

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
Ran 13 tests in 4.169s

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
Ran 9 tests in 2.009s

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
Ran 2 tests in 10.905s

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
test_f1_step600_package_preserves_a4_contract_and_binding (__main__.Round4Tests.test_f1_step600_package_preserves_a4_contract_and_binding) ... ok
test_f2_step600_real_job_and_rehearsal_memory (__main__.Round4Tests.test_f2_step600_real_job_and_rehearsal_memory) ... ok
test_f3_cache_only_return_refuses_unverified_journals (__main__.Round4Tests.test_f3_cache_only_return_refuses_unverified_journals) ... ok
test_f9_off_builder_guard_and_processor_only (__main__.Round4Tests.test_f9_off_builder_guard_and_processor_only) ... ok

----------------------------------------------------------------------
Ran 4 tests in 25.325s

OK
{"output": "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/9bf19b9fec6744d7a063f2a3f1489cc3/verified-return", "complete": false, "status": "FAILED", "sha256": "b8459fd3f75d9df163d8c1062d4714ab47f7bd714e7c04717f29172c5f5ec117"}
CPU step-600 fixture: /scratch/jjyeung/orch_n30/so_read/work/test-artifacts/9bf19b9fec6744d7a063f2a3f1489cc3
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
Ran 7 tests in 9.925s

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
Ran 9 tests in 31.205s

OK
README unpack command: exit 0; authenticated partial return accepted.
Detached fill: success=0, failure=17, duplicate launch refused.
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
Ran 9 tests in 0.279s

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
Ran 3 tests in 0.064s

OK
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/apply-round6/751d7f0734d3447783f9b391cfd4d0f2/src/u0/tests/test_off.py
```

Exact output:

```text
test_every_output_byte_and_source_hash_matches_original (__main__.OffContractTests.test_every_output_byte_and_source_hash_matches_original) ... ok

----------------------------------------------------------------------
Ran 1 test in 6.328s

OK
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/apply-round6/751d7f0734d3447783f9b391cfd4d0f2/src/u0/tests/test_round4.py
```

Exact output:

```text
test_f1_step600_package_preserves_a4_contract_and_binding (__main__.Round4Tests.test_f1_step600_package_preserves_a4_contract_and_binding) ... ok
test_f2_step600_real_job_and_rehearsal_memory (__main__.Round4Tests.test_f2_step600_real_job_and_rehearsal_memory) ... ok
test_f3_cache_only_return_refuses_unverified_journals (__main__.Round4Tests.test_f3_cache_only_return_refuses_unverified_journals) ... ok
test_f9_off_builder_guard_and_processor_only (__main__.Round4Tests.test_f9_off_builder_guard_and_processor_only) ... ok

----------------------------------------------------------------------
Ran 4 tests in 24.895s

OK
{"output": "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/59e7e14702904a8e81bf774dfc11f833/verified-return", "complete": false, "status": "FAILED", "sha256": "6eba4584a212633a47e9c152ed5fa6770d5d825188daeffb473f119c2d9651a3"}
CPU step-600 fixture: /scratch/jjyeung/orch_n30/so_read/work/test-artifacts/59e7e14702904a8e81bf774dfc11f833
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/apply-round6/751d7f0734d3447783f9b391cfd4d0f2/src/u0/tests/test_round5.py
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
Ran 7 tests in 10.073s

OK
All CPU receipt checks passed
{"passed": true, "pool_bytes": 75000000}
All CPU receipt checks passed
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/apply-round6/751d7f0734d3447783f9b391cfd4d0f2/src/u0/tests/test_round6.py
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
Ran 9 tests in 30.602s

OK
README unpack command: exit 0; authenticated partial return accepted.
Detached fill: success=0, failure=17, duplicate launch refused.
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/apply-round6/751d7f0734d3447783f9b391cfd4d0f2/src/u0/tests/test_compare.py
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
Ran 9 tests in 0.301s

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
Ran 8 tests in 0.018s

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
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/af2e284d2c524a6f9395f9b2a5231138/u0/a8.py", line 65, in <module>
    raise SystemExit(main())
                     ^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/af2e284d2c524a6f9395f9b2a5231138/u0/a8.py", line 61, in main
    return launch(rest)
           ^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/af2e284d2c524a6f9395f9b2a5231138/u0/a4.py", line 2, in main
    from a8 import source_hash
ModuleNotFoundError: No module named 'a8'


======================================================================
FAIL: test_f1_actual_isolated_script_plain_and_opaque (__main__.Round2Tests.test_f1_actual_isolated_script_plain_and_opaque) (opaque=True)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round2.py", line 67, in test_f1_actual_isolated_script_plain_and_opaque
    self.assertEqual(result.returncode,0,result.stdout+result.stderr)
AssertionError: 1 != 0 : Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/9b748703c78a4990a6a65395fa730abf/u0/a8.py", line 65, in <module>
    raise SystemExit(main())
                     ^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/9b748703c78a4990a6a65395fa730abf/u0/a8.py", line 56, in main
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
Ran 13 tests in 0.178s

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
AssertionError: 139877540414880 unexpectedly found in {139877540414880, 139877540415200} : Per-call weight hashing

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
Ran 9 tests in 0.899s

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
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/36a60c0f3d0941d29a1ec28e9b72f3c1/0.py", line 44, in main
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
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/36a60c0f3d0941d29a1ec28e9b72f3c1/0.py", line 18, in dispatch
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
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/36a60c0f3d0941d29a1ec28e9b72f3c1/7.py", line 139, in main
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
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/36a60c0f3d0941d29a1ec28e9b72f3c1/7.py", line 87, in run
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
Ran 2 tests in 9.691s

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
Ran 2 tests in 0.016s

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
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 289, in test_f1_step600_package_preserves_a4_contract_and_binding
    self.assertEqual(cfg.get(key),old[key],key)
AssertionError: None != 'candidates_argmax' : stage1_select_rule

======================================================================
FAIL: test_f2_step600_real_job_and_rehearsal_memory (__main__.Round4Tests.test_f2_step600_real_job_and_rehearsal_memory)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 332, in test_f2_step600_real_job_and_rehearsal_memory
    self.assertEqual(result.returncode,0,str(root)+'\n'+result.stdout+result.stderr+logs+'\n'+'\n'.join(p.read_text() for p in (root/'job/sandbox/r').glob('FAILED.json')))
AssertionError: 1 != 0 : /scratch/jjyeung/orch_n30/so_read/work/test-artifacts/92b5356764844076b676be7c76b460fd
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 425, in <module>
    elif len(sys.argv)>1 and sys.argv[1]=='--control':control_child(Path(sys.argv[2]),Path(sys.argv[3]),sys.argv[4])
                                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 273, in control_child
    node.main()
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/92b5356764844076b676be7c76b460fd/built/package/a/5.py", line 147, in main
    raise ValueError('Prepared default settings differ')
ValueError: Prepared default settings differ
PASS action 0 rehearsal False



======================================================================
FAIL: test_f3_cache_only_return_refuses_unverified_journals (__main__.Round4Tests.test_f3_cache_only_return_refuses_unverified_journals) (verified=False)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 401, in test_f3_cache_only_return_refuses_unverified_journals
    with self.subTest(verified=value),self.assertRaisesRegex(ValueError,'Unverified weight journal'):validate()
                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f3_cache_only_return_refuses_unverified_journals (__main__.Round4Tests.test_f3_cache_only_return_refuses_unverified_journals) (verified=None)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 401, in test_f3_cache_only_return_refuses_unverified_journals
    with self.subTest(verified=value),self.assertRaisesRegex(ValueError,'Unverified weight journal'):validate()
                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f3_cache_only_return_refuses_unverified_journals (__main__.Round4Tests.test_f3_cache_only_return_refuses_unverified_journals) (verified=0)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 401, in test_f3_cache_only_return_refuses_unverified_journals
    with self.subTest(verified=value),self.assertRaisesRegex(ValueError,'Unverified weight journal'):validate()
                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f3_cache_only_return_refuses_unverified_journals (__main__.Round4Tests.test_f3_cache_only_return_refuses_unverified_journals) (verified=1)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 401, in test_f3_cache_only_return_refuses_unverified_journals
    with self.subTest(verified=value),self.assertRaisesRegex(ValueError,'Unverified weight journal'):validate()
                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f3_cache_only_return_refuses_unverified_journals (__main__.Round4Tests.test_f3_cache_only_return_refuses_unverified_journals) (verified='true')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 401, in test_f3_cache_only_return_refuses_unverified_journals
    with self.subTest(verified=value),self.assertRaisesRegex(ValueError,'Unverified weight journal'):validate()
                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 4 tests in 11.365s

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
AssertionError: '#SBATCH --exclude=orchard-community-2\n' not found in "#!/bin/bash\nset -euo pipefail\nexec /usr/bin/python3 -I -s -B - <<'A'\nimport hashlib,io,json,os,sys,tarfile\nfrom pathlib import Path,PurePosixPath\nj=os.environ.get('SLURM_JOB_ID','')\nif not j.isdigit():raise ValueError('Allocation required')\nb=bytes.fromhex('1f8b08000000000002ffed5ae96fdb4616cf67fd15acfb81a43ca1255197e5b2409ab8db2c9a03715260210804458e24c614c9e5503e1ae47fdff7de0c0f51b2e345d12e16e5c09644cecc9b37effccdd1b33e8b247ef6a7961e9471af47dfbdc3ef9e3d9c94bfe5fbf164623fd37acffe82b213b997c190cffe9ee54b47d34e52ef3e4abcc05ddee75c9cccb4913d1ef7ce6d56af131b6f301a43e509e7c3516f3cf047237f6cf3e970706e4fecf130584ea7c3e9747c6e4feda06ff7ecb16d4f57038f8f46bde160e88f569cf7bcc924389174232fae11f53c1ef479609ffb13dfe7fe24383fb7c7fe6a3a982ecffb3e1f4fa7fd89eddbe7e3e53008ce6d3b9840e3e58a4f82be373a1ff525d13cb9e631915bf6fa037b381a4fa6e7279daf9d676d79c037adf4fe4f1fe371ff1f0efbe3a6ff0f47adffff25e5e4e4e47dc605cf6eb8966649b0f3f33089352fd88642c02fa6817cd661bc669a174589ef51f532d9c581805771a041ef5d94c357becb620be875c26d9a64b9b6f1c4260a970c130c0321afc28833712f3aab2cd96aa99763ada61abf87c74ea713f095b6f5aeb91b84025af81b234b929c69491602135e04bf529e797992a9d861ce3a1ad14b327fe36581bbe9f72c3fd96e814b451a1a7634245cd2f4b2f50debc2a760ddeef52dfe403adaf7dabb38ba87a94070f2b9966fe03f499f47fc8647f5e9178478760142e3a997c9f7288edb24bbe69940b1dd6b6918c73cb08074b8d2221ed3c8e68fce809ae2c3fcf960b6709cb9c8339aea99ee9d8dc0277593d55ff5294debe602d9d4fcd5dac1670b23b3300e5a591987889df3bbdc304dece009d0708efde6ba471ad661d0bea235d7fd245e856b7d31d71be285668d37d8e770c0db2cccb91c91180b76db5418405b8e0fb387deaadb84a6f75d9330cd4ccbbc5070ed372fdaf1cb2c4b3243ff094c2de241a9780df41cafe185b7ca798672cef25daacb7982449d7997043b7b3e58d464387944a8d0559a6f6967474da453b42af45f1a6c181b684048d8414b36c0cc2de2a2bf302fd2dd320afd231aeb1dd717c823e38124a49f81577ee67e7e8646bd8bc3fcfeecf3e77bbe8bd767c9f566a29b6786eef547ae9fe4ae97eaa772b0b94ea9505f0039a57ce58e9694b661c85190897cfd7bc103210060c2daf0bb205c73011c394e41731f0be820b7db30df68cab72dd050dc240ba3633d2a7705badb6a615c3ca355c449ae6dadd8db728b142990a0a1d79cf94c3767609e7918eff85ea750e0a086093ad374cbd29132894cd233ad14e9cd0e0dea532cbc15d7fc24e0d26a5247aa23d5cf64df8b143bf338b7b6d7419819f241381fb31d67fc2e14b99b5cd3132857d9be941cccc1023566e064c4dd56ca55aa156c02a39e15c6a810a3573346b05ff330901511ec73b27c5a946bb894d374ba0ec6f864b5678a85c2bc33ffece5fb4fc74d5249dda0ee6808605381bed042a1a118289c519db5e6b9a12fc967ddf50e79558dcd871a8368b37b57f07fef78ecf3479a970688c1eb619b2c4abd1f80cdbd4e15f88449d41a8671bacb053645d155a22942c551ea8731f358d06c749373dff26d92ddebeccb575349ce13a180c93b8ea6afc23b1eb86b3b472a2917fad1d1158985ec0fe3fa3cc508ef6285bb85941e714571ae03b10744b44f46785be8ef895dc6b7a01f3703ed8459a1969fbd48f027505985b9a814691ef1c59f7751a481d54150e7fe3504d6d50a9227ca196cdea29720826c173b475041a3096b42034984a233b637215c831dbb2ebab8eb3a8eeeba58e9bafa4c86f0bfe13261f23fc7fffdc9706c1fe0ff49afc5ff7f11fe7f5700abc2bb2853e7b709386e127939478c0fa982923d24d924e635305c47fc84f421cdb13cdc72a600c72370ffc3a75f2faf1c43f7218284018c245c004d5bef4e6766e7e5bb4f6f3f426d7fd463f57f1b1cfbeae52f97afa0b3634016b54d069f3dfaecd3e7803e8790b8089f055cf85998c21405a472ffda5b73426b12cccd83d0cf01ef6d1dc04cb73cd319c44c2e9cb91ec34c75c490d0a10f092a0218068126e2ce318e8577c3dde436760388bf1b876224ab82249546747674c829ec8190eda8687d507fc3b37075ef860134593447c8ef53ec6a3390051bb0e102f04a0a7c039e1c83e4165222827b00a95d422e06aa86dd60507ec2628aba101e20284360080023e5801aaaa0ca3a84f8cea1118ea4800fd04a0b03c832806deb19e0803bc9bb5c707143ae599ec0f2bb0faf2e3f30d0581287be177534c8b15ca26b490332f82e87bc0f68f942f01ca0e65ad421d25ed3a201343ec448b2914c7e09a9cc8b74f328062dd4a215ed34c21e7a0103f980bb489f6756c3004ac4a73841884d8651bce8ec3f1ac50f566471095d89e3a20e267660e6008d10f481cb93a31e99c62ebe8ed1e48ff445c00b33144eddfb0a212a2f4481179a77c80d11983965ab3a4a63129a9595f2b1aa463f68c2df52bd4d8006d69081fbf419053687186502b0047a9e53441798c2f7da3fafdebd85851d00da1c66a1adc31b0e12c765e732e25a04e68ffb05b88512e7721700a3276e8a6cb9443502d6ffe52c6b66555b2817d5261a60cd35d152cf0054e51ec41aefecf5abcbb71f5f7ffc9704a3acecd55186279c2f5f3b347ec8704ea83a1e0323307b6ed02c699f83d6a90dda2409fd0c972421c25c7f93c0949c2fdd6e693ec74c6486548f1b0fb4df0b89faec202676bb5fae2585eb05f17d8d2c1fa0589de90f07c1239525e8fd0ae2a040a55678e56cd5cafbe23010ca79a304f6ea1afd3f5cbe78e536d44106dced165a21db7240114a7ca5511681c85043d1168952e03c5ca0c8e5132be2d2ac58289aac8a3ff41259360b894256028373b1a1ac952aa6b785664da681b292d4c5e569bd5539b5ab8fefdeeb154d0183c1524e6e6be9335a02eb902d8181b94a98a0694a99f846e54c9df210bca0e03bcfa5762996488391f58b4535ce7f675b553798cb16727018ebb3feb4d763baccebd5cb01bcec76f743a212fdd74e09039402648ec9f8867b99401d3d9c6560c911f3ac88c6b84791251193824254209e96992ae76d64b60bb9b30a49bef0697fb54609aaf616d8e556d0c693963b44cb0ae380df19b4a7a7243cef2d947d217bb425d7a18d32e1d45835c878256107da30ecede48ce839bd325e92b8bd1c7eadc238141b7779ef0cc880d52e13129be38762457ffe9c8cc53cedc3b25819cca3cda529a9f6644e8f3697d354cd996e7d4e60255717c0e3cce1849e932f4812e810c7a1c1818b54749b58e1d83885dbe230fbc8e1b8853b0e255d08085530fe63e354fc4a72f383308b228448f6cd86f5e80b7d1ecff03083c709d0ee2b5abae5a5298f03698b2a7a4a3c5bd72723dba59dd912ac493ef7a12e65efcb3b1818510b8720a84901e37a0644ace51b48ebeb0d6df3c3689146c6a989c4bfe6b9dcd914f96ea9ddf270bdc9318b933be31e2ce0fedcda42c3c293e576b06c407c161557f01df1b7de96c3daca47e42cdfe718150ea05e09edc820308344d2f789e1128881c4b6d09c22039d6c802fe646b2fccc029ec30c1944af80ad7902169b4122a2254bbc8ba262b1423143830e16d5e1c7053e613f073fe82908bd759c883cf411585ce090858aa01aed89da37a668a0e45c1ccd89bced32f0b4ae37a3e95a398f05c0c679df62038bf57b3d6b416649b226115a4018266048015857f8f52e868ce3ba3847d705d403df26db6b8d7262fa4754df3fec8f3a531980560dce5b0821aabda1d75075211e6b95e17e900f102f6f74b5075250f2094741878adcca9a0da40e52bf097d5c15a6bb6f2fe784b7b55d323547b16f32699800504b051c5b75e28759f2634943951cd0242bbf455541e097daa57e877592b274b63b472ae8779e25c218b0d1d464b84be6e8602b269d14a934293d5565c95dacfc9d814dc81cc1645624a9333f02161ddc0cb0f0e30959149e7039c3efb8bfc375e69357a378b8460cc04ab38f4702b872a11730d7a3ab4e5a0ac1489e9f47f772534388701d4378c07ebaf9adc48ccbef8b951746bb4c5a994ad304617b8c4c07d7842804c3fcd101193d478482dc3d35c7940becd9122cefba23cffe2ab058c64ec7508204e24a7a26a641a515d40fcc6215dec9582a7fcbe4a866f3c4e8dbedcaf6e4b8e14af59eeb4a10b06654c22f2a4063101e72a8215f2a0476d0ef42cd502ec92ad013933c41a018d4995abfdc428b4c4646ac5653207ee63a52c0bc2453a71a3e7060456664153f787c5111008a521630f831495464ca5f55ba89cbeaaad671623af4d96d0188aad5ed1379411eccbd64d6dce52987f3a2a84ee7089942deea5bad78e913c2ce7a4b075b4a7ee5a6cb43d679f5e9cd9b171f8a058f9a5b752eaa5ea853513a0a70e9aa80d165e0542934027332a64366d6af13c8b33307707ab7df1b0cbb5d9b11f72ee016c818d042a8ed34f95a2e7364a71e1a843a9d6af4991d36a6a668c946b38e4e29e46e475e5870ef07a7d9ec07a73f2e98244b3c082caf6388cea1dc32d5a8a79284bc34a1132cf9194f7634c855129743089a691e846648b6da78a8a58066c824695bcdc6db028070326d9d0160b2b44bc4231af183c452042db09ef432a07683770f9609e4d31500c55c11938410e8ac4003aa0ee822414dea17f10d2428c7180fbbe7a7e3e1a93d80bfeea84f7fa7a3fee9c0ec4e3b389aab54e940fb53298c41074337067917f57a0b0c7307282951955ebde7528541c48c12a5d451dcad8dd0b07b6a96463be182cc40c97832257b19f1a96d3ed213f02134dd056bfe608fd383099c1e1a492d24551b2bc544f02241794300e6496779cee131de3721c23eeff22cae14508f3d7438a79c0447522cc92eee0ee25986da6a504eeff30df08046b3294fffddba8695765925ef82b29fa421706337481e0851717df01e4fef5ca9166ad00c077b816a7f8c6ed7f8a23775a31fb8fb57999ef66282c64142da97af6683249e5416c1f4c056f4c50f07ec35e3acd9d98b7a69962ceb5bd42727272fe984532e36722f8c5500a0a8400818fc50c3c51dac683002490de3c3d58b3774caf24434f4c7b6b0ab0de18776d516df15867afc7205581b7053bfb143bbd6e5a65c476d79cbddcac6ae79435fd5e931dd20696c8c571a2f77612af533bc4b024f024180973ab5aa7247dcc4e171c94b1b53aa7d556b11d0c6e30d321b481f25eb6520ab2729da1c3bc83a3038a5488269fb59b1abc87d33f196b0f0cde59b7765025648ac960015a6c273f763da795faa54ea84dff99c0782c26391a6e8ae847900f8f76f3a356ea01ddc79dab3ab8b549db6acf63606aa1b31f3596f21afc0a567fa52ddd2829f79c679f184c1156da57e5ded092673fcd20dd0def5e8ca8db4296f5a1810de8ebbf1725a2fa99f068f71afbf3c35f98617c24039440b0c013e17425e82e91c7f7d547022896eb861aa2b486631ed62b26a6752aee19f1611f68cab71dfafb2b10f97bf5cbef870f5e2d7d2baca4dd07a9f02f81fd1844a4aaeba0562cef6a3e11e95f2ce5db9259288d24b6865596fcee8094039fc4c84c5e39b304be2b9fef2d3ab17ee6fafaf5efff4eba5fbeaf2b7d72f2faf801b914621f0c348c5d20daeee45ceb79777f0be7f7cdd227ddc6c2f89b4a52d6d694b5bdad296b6b4a52d6d694b5bdad296b6b4a52d6d694b5bdad296b6b4a52d6d694b5bfeffca7f002a07d30500500000')\nr=Path('/tmp')/('a'+j+'ab0123456789')\nr.mkdir(mode=0o700)\nwith tarfile.open(fileobj=io.BytesIO(b)) as a:\n    for e in a:\n        n=PurePosixPath(e.name)\n        if n.is_absolute() or '..' in n.parts or not e.isfile():raise ValueError('Unsafe input')\n        p=r/e.name;p.parent.mkdir(parents=True,exist_ok=True)\n        with a.extractfile(e) as i,p.open('xb') as o:o.write(i.read())\nos.chdir(r)\nos.execv(sys.executable,[sys.executable,'-I','-s','-B',str(r/'0.py'),str(r)])\nA\n"

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
Ran 7 tests in 5.106s

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
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 102, in test_f1_readme_unpack_subprocess
    self.assertEqual(result.returncode,0,result.stderr)
AssertionError: 1 != 0 : Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/ea3587775273481bac24d663b7f2e2df/step600/unpack_return.py", line 3, in <module>
    from fetch_return import digest as file_digest, validate_exit
ModuleNotFoundError: No module named 'fetch_return'


======================================================================
FAIL: test_f2_detached_locked_fill_exit_success_and_failure (__main__.Round6Tests.test_f2_detached_locked_fill_exit_success_and_failure)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 114, in test_f2_detached_locked_fill_exit_success_and_failure
    self.assertIn('nohup bash',text,'Pull/fill still runs in the foreground')
AssertionError: 'nohup bash' not found in '#!/bin/bash\nset -euo pipefail\numask 077\nD=$(cd -- "$(dirname -- "$0")" && pwd)\nP=/project/community/jjyeung/okh7/a15_cot_apab0123456789\nexport TZ=UTC CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud CLOUDSDK_CORE_DISABLE_PROMPTS=1\nE=$P/a/e\ntest ! -e "$E"\nmkdir -m 700 "$E"\nOBJECT=q8/8865619b/673bc60f_m600.tar\ncp /project/community/jjyeung/okh7/abcdef/5 "$E/5"\ntest "$(cat "$E/5")" = \'q8/8865619b/673bc60f_m600.tar 4 2222222222222222222222222222222222222222222222222222222222222222\'\ncp /project/community/jjyeung/okh7/abcdef/7 "$E/7"\ntest "$(sha256sum "$E/7" | cut -d\' \' -f1)" = 3b0051c4a9cc661d02019a645165fc3e23d658d2f24a6fd6fd86ec7877ba4fc1\ncp /project/community/jjyeung/okh7/abcdef/8 "$E/8"\ntest "$(sha256sum "$E/8" | cut -d\' \' -f1)" = 4c0dd9d6e4535a2945ed58754c1cdd5e9a316067be35f2e8440caa9a80e1c915\ncp /project/community/jjyeung/okh7/abcdef/9 "$E/9"\ntest "$(sha256sum "$E/9" | cut -d\' \' -f1)" = 7f654d2f0ae9f06083f2fc8fd793512c154b4d01ce8632fb733d4191205af770\nfor i in 0 1 2 3; do\n  test ! -e "$E/$i"\n  gsutil -o Boto:num_retries=0 -o Boto:metadata_service_num_attempts=1 -o GSUtil:parallel_process_count=1 -o GSUtil:parallel_thread_count=1 -o GSUtil:sliced_object_download_threshold=0 -o GSUtil:sliced_object_download_max_components=1 -q cp "gs://cmu-gpucloud-jjyeung/$OBJECT.part0$i-of-04" "$E/$i.partial"\n  mv "$E/$i.partial" "$E/$i"\ndone\n/usr/bin/python3 -I -s -B "$P/a/4.py" --parts "$E/0" "$E/1" "$E/2" "$E/3" --done "$E/5" --object "$OBJECT" --config "$E/7" --receipt "$E/8" --data-receipt "$E/9" --lineage SFT --step 600 --out "$P/a/export.json" --prep-tar "$P/a/6" --base-inputs "$P/a/0.json" --inputs-out "$P/a/1.json"\nPREP=$(sha256sum "$P/a/6" | cut -d\' \' -f1)\n/usr/bin/python3 -I -s -B "$D/d.py" "$P/a/1.json" "$P/a/0.json" "$PREP" > "$P/a/dry.json"\n(cd "$P" && CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 04:30:00)\n/usr/bin/python3 -I -s -B "$D/d2.py" "$P" "$P/a/w2" > "$P/a/dry2.json"\nprintf \'%s\\n\' 0 > "$P/a/1.txt"\n' : Pull/fill still runs in the foreground

======================================================================
FAIL: test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks) (field='bundle_guard.batch_sha256')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 154, in test_f3_full_cont_ops_receipt_checks
    self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'Unbound CPU receipt field: '+key)
AssertionError: 0 == 0 : Unbound CPU receipt field: batch_sha256

======================================================================
FAIL: test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks) (field='bundle_guard.path')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 154, in test_f3_full_cont_ops_receipt_checks
    self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'Unbound CPU receipt field: '+key)
AssertionError: 0 == 0 : Unbound CPU receipt field: path

======================================================================
FAIL: test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks) (field='entry_sequence.events')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 154, in test_f3_full_cont_ops_receipt_checks
    self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'Unbound CPU receipt field: '+key)
AssertionError: 0 == 0 : Unbound CPU receipt field: events

======================================================================
FAIL: test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks) (field='entry_sequence.guard_target_sha256')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 154, in test_f3_full_cont_ops_receipt_checks
    self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'Unbound CPU receipt field: '+key)
AssertionError: 0 == 0 : Unbound CPU receipt field: guard_target_sha256

======================================================================
FAIL: test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks) (field='entry_sequence.requested_argv')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 154, in test_f3_full_cont_ops_receipt_checks
    self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'Unbound CPU receipt field: '+key)
AssertionError: 0 == 0 : Unbound CPU receipt field: requested_argv

======================================================================
FAIL: test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks) (field='entry_sequence.dispatched_argv')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 154, in test_f3_full_cont_ops_receipt_checks
    self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'Unbound CPU receipt field: '+key)
AssertionError: 0 == 0 : Unbound CPU receipt field: dispatched_argv

======================================================================
FAIL: test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks) (field='entry_sequence.batch_sha256')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 154, in test_f3_full_cont_ops_receipt_checks
    self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'Unbound CPU receipt field: '+key)
AssertionError: 0 == 0 : Unbound CPU receipt field: batch_sha256

======================================================================
FAIL: test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks) (field='memory.perception_memo_modules')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 154, in test_f3_full_cont_ops_receipt_checks
    self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'Unbound CPU receipt field: '+key)
AssertionError: 0 == 0 : Unbound CPU receipt field: perception_memo_modules

======================================================================
FAIL: test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks) (field='memory.sam_measurement_required')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 154, in test_f3_full_cont_ops_receipt_checks
    self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'Unbound CPU receipt field: '+key)
AssertionError: 0 == 0 : Unbound CPU receipt field: sam_measurement_required

======================================================================
FAIL: test_f3_full_cont_ops_receipt_checks (__main__.Round6Tests.test_f3_full_cont_ops_receipt_checks)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 156, in test_f3_full_cont_ops_receipt_checks
    self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'MEMORY.json differs')
AssertionError: 0 == 0 : MEMORY.json differs

======================================================================
FAIL: test_f4_every_copied_a4_member_pinned_before_output (__main__.Round6Tests.test_f4_every_copied_a4_member_pinned_before_output) (member='package/BATCH.sh')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 169, in test_f4_every_copied_a4_member_pinned_before_output
    with self.assertRaisesRegex(ValueError,'A4 member pin|A4 batch pin'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f4_every_copied_a4_member_pinned_before_output (__main__.Round6Tests.test_f4_every_copied_a4_member_pinned_before_output) (member='package/3.py')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 169, in test_f4_every_copied_a4_member_pinned_before_output
    with self.assertRaisesRegex(ValueError,'A4 member pin|A4 batch pin'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f4_every_copied_a4_member_pinned_before_output (__main__.Round6Tests.test_f4_every_copied_a4_member_pinned_before_output) (member='package/a/0.json')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 169, in test_f4_every_copied_a4_member_pinned_before_output
    with self.assertRaisesRegex(ValueError,'A4 member pin|A4 batch pin'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f4_every_copied_a4_member_pinned_before_output (__main__.Round6Tests.test_f4_every_copied_a4_member_pinned_before_output) (member='package/a/4.py')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 169, in test_f4_every_copied_a4_member_pinned_before_output
    with self.assertRaisesRegex(ValueError,'A4 member pin|A4 batch pin'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f4_every_copied_a4_member_pinned_before_output (__main__.Round6Tests.test_f4_every_copied_a4_member_pinned_before_output) (member='package/a/7.py')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 169, in test_f4_every_copied_a4_member_pinned_before_output
    with self.assertRaisesRegex(ValueError,'A4 member pin|A4 batch pin'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f4_every_copied_a4_member_pinned_before_output (__main__.Round6Tests.test_f4_every_copied_a4_member_pinned_before_output) (member='fetch_return.py')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 169, in test_f4_every_copied_a4_member_pinned_before_output
    with self.assertRaisesRegex(ValueError,'A4 member pin|A4 batch pin'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f4_every_copied_a4_member_pinned_before_output (__main__.Round6Tests.test_f4_every_copied_a4_member_pinned_before_output)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 177, in test_f4_every_copied_a4_member_pinned_before_output
    with self.assertRaisesRegex(ValueError,'bootstrap pin'):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f5_checkpoint_binding_and_runtime_recheck (__main__.Round6Tests.test_f5_checkpoint_binding_and_runtime_recheck) (asset='RESTORE.json')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 197, in test_f5_checkpoint_binding_and_runtime_recheck
    with self.assertRaises(ValueError):self.helper.gate(*args)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f5_checkpoint_binding_and_runtime_recheck (__main__.Round6Tests.test_f5_checkpoint_binding_and_runtime_recheck) (asset='binding.json')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 197, in test_f5_checkpoint_binding_and_runtime_recheck
    with self.assertRaises(ValueError):self.helper.gate(*args)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f5_checkpoint_binding_and_runtime_recheck (__main__.Round6Tests.test_f5_checkpoint_binding_and_runtime_recheck)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 200, in test_f5_checkpoint_binding_and_runtime_recheck
    with self.assertRaisesRegex(ValueError,'export identity'):self.helper.gate(*args)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f5_production_device_is_required (__main__.Round6Tests.test_f5_production_device_is_required)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 214, in test_f5_production_device_is_required
    self.assertTrue(hasattr(self.kit,'validate_device'),'GPU name is recorded but never required')
AssertionError: False is not true : GPU name is recorded but never required

======================================================================
FAIL: test_f5_runtime_asset_recheck (__main__.Round6Tests.test_f5_runtime_asset_recheck)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 204, in test_f5_runtime_asset_recheck
    self.assertTrue(hasattr(self.kit,'validate_assets'),'Gate lacks runtime asset authentication')
AssertionError: False is not true : Gate lacks runtime asset authentication

======================================================================
FAIL: test_info_done_whitespace (__main__.Round6Tests.test_info_done_whitespace)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 226, in test_info_done_whitespace
    self.assertNotIn('test "$(cat "$E/5")" =',text,'Whitespace-only receipt changes still refuse')
AssertionError: 'test "$(cat "$E/5")" =' unexpectedly found in '#!/bin/bash\nset -euo pipefail\numask 077\nD=$(cd -- "$(dirname -- "$0")" && pwd)\nP=/project/community/jjyeung/okh7/a15_cot_apab0123456789\nexport TZ=UTC CLOUDSDK_CONFIG=/project/community/jjyeung/gcloud CLOUDSDK_CORE_DISABLE_PROMPTS=1\nE=$P/a/e\ntest ! -e "$E"\nmkdir -m 700 "$E"\nOBJECT=q8/8865619b/673bc60f_m600.tar\ncp /project/community/jjyeung/okh7/abcdef/5 "$E/5"\ntest "$(cat "$E/5")" = \'q8/8865619b/673bc60f_m600.tar 4 2222222222222222222222222222222222222222222222222222222222222222\'\ncp /project/community/jjyeung/okh7/abcdef/7 "$E/7"\ntest "$(sha256sum "$E/7" | cut -d\' \' -f1)" = 3b0051c4a9cc661d02019a645165fc3e23d658d2f24a6fd6fd86ec7877ba4fc1\ncp /project/community/jjyeung/okh7/abcdef/8 "$E/8"\ntest "$(sha256sum "$E/8" | cut -d\' \' -f1)" = 4c0dd9d6e4535a2945ed58754c1cdd5e9a316067be35f2e8440caa9a80e1c915\ncp /project/community/jjyeung/okh7/abcdef/9 "$E/9"\ntest "$(sha256sum "$E/9" | cut -d\' \' -f1)" = 7f654d2f0ae9f06083f2fc8fd793512c154b4d01ce8632fb733d4191205af770\nfor i in 0 1 2 3; do\n  test ! -e "$E/$i"\n  gsutil -o Boto:num_retries=0 -o Boto:metadata_service_num_attempts=1 -o GSUtil:parallel_process_count=1 -o GSUtil:parallel_thread_count=1 -o GSUtil:sliced_object_download_threshold=0 -o GSUtil:sliced_object_download_max_components=1 -q cp "gs://cmu-gpucloud-jjyeung/$OBJECT.part0$i-of-04" "$E/$i.partial"\n  mv "$E/$i.partial" "$E/$i"\ndone\n/usr/bin/python3 -I -s -B "$P/a/4.py" --parts "$E/0" "$E/1" "$E/2" "$E/3" --done "$E/5" --object "$OBJECT" --config "$E/7" --receipt "$E/8" --data-receipt "$E/9" --lineage SFT --step 600 --out "$P/a/export.json" --prep-tar "$P/a/6" --base-inputs "$P/a/0.json" --inputs-out "$P/a/1.json"\nPREP=$(sha256sum "$P/a/6" | cut -d\' \' -f1)\n/usr/bin/python3 -I -s -B "$D/d.py" "$P/a/1.json" "$P/a/0.json" "$PREP" > "$P/a/dry.json"\n(cd "$P" && CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B 3.py check --gpus 1 --time 04:30:00)\n/usr/bin/python3 -I -s -B "$D/d2.py" "$P" "$P/a/w2" > "$P/a/dry2.json"\nprintf \'%s\\n\' 0 > "$P/a/1.txt"\n' : Whitespace-only receipt changes still refuse

======================================================================
FAIL: test_info_submit_requires_successful_bound_gpu_gate (__main__.Round6Tests.test_info_submit_requires_successful_bound_gpu_gate) (field='passed')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 243, in test_info_submit_requires_successful_bound_gpu_gate
    with self.subTest(field=key):self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'GPU evidence ignored')
                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 0 == 0 : GPU evidence ignored

======================================================================
FAIL: test_info_submit_requires_successful_bound_gpu_gate (__main__.Round6Tests.test_info_submit_requires_successful_bound_gpu_gate) (field='adoption_plan_sha256')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 243, in test_info_submit_requires_successful_bound_gpu_gate
    with self.subTest(field=key):self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'GPU evidence ignored')
                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 0 == 0 : GPU evidence ignored

======================================================================
FAIL: test_info_submit_requires_successful_bound_gpu_gate (__main__.Round6Tests.test_info_submit_requires_successful_bound_gpu_gate) (field='required_device_type')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 243, in test_info_submit_requires_successful_bound_gpu_gate
    with self.subTest(field=key):self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'GPU evidence ignored')
                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 0 == 0 : GPU evidence ignored

======================================================================
FAIL: test_info_submit_requires_successful_bound_gpu_gate (__main__.Round6Tests.test_info_submit_requires_successful_bound_gpu_gate) (field='adoption_assets')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 243, in test_info_submit_requires_successful_bound_gpu_gate
    with self.subTest(field=key):self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'GPU evidence ignored')
                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 0 == 0 : GPU evidence ignored

======================================================================
FAIL: test_info_submit_requires_successful_bound_gpu_gate (__main__.Round6Tests.test_info_submit_requires_successful_bound_gpu_gate) (field='adoption_profile')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 243, in test_info_submit_requires_successful_bound_gpu_gate
    with self.subTest(field=key):self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0,'GPU evidence ignored')
                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 0 == 0 : GPU evidence ignored

======================================================================
FAIL: test_info_submit_requires_successful_bound_gpu_gate (__main__.Round6Tests.test_info_submit_requires_successful_bound_gpu_gate)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round6.py", line 245, in test_info_submit_requires_successful_bound_gpu_gate
    self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0)
AssertionError: 0 == 0

----------------------------------------------------------------------
Ran 9 tests in 43.231s

FAILED (failures=31)
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
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 334, in test_f2_step600_real_job_and_rehearsal_memory
    self.assertEqual(proof['memory'].get('read_cache_bytes'),12*1024**3)
AssertionError: None != 12884901888

----------------------------------------------------------------------
Ran 1 test in 10.308s

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
AssertionError: 'H10_SETTINGS' unexpectedly found in {'CUDA_VISIBLE_DEVICES': 'fixture', 'H10_SETTINGS': '/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/f7f1a8584a33452d8b0e8497dd36696c/u0.json'}

----------------------------------------------------------------------
Ran 1 test in 0.903s

FAILED (failures=1)
```

The final seal is verified by `bash work/cpu.sh work/integrity6.py`; its exact output is [integrity6.txt](checks/integrity6.txt). [FINAL_INTEGRITY.json](checks/FINAL_INTEGRITY.json) pins the documents, MANIFEST, diffs, kit, operations and evidence. The seal output stays external to avoid a report/hash cycle.
