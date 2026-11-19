VERDICT: DONE All requested round-5 fixes pass CPU verification; production adoption still requires the GPU byte gate.

Measured validation: **102 workspace tests and 21 fresh-application tests pass**. Five patches apply with zero fuzz; all original reader files remain unchanged. Complete original/OFF fixture output bytes match, including source hashes. ON CPU fixtures retain exact answers and traces. The seven round-5 tests produce eleven expected assertion failures against the reviewed implementation; all nine fail-before controls reproduce.

The bound step-600 package preserves A4's 636-item, single-card, cache-only profile and export binding. Its batch includes cont_ops' exclusion, EXIT log return and USR1 forwarding. Its builder authenticates the reviewed payload, patched operators, extension inventory and alias bases before copying. The handover includes executable binding/delivery/operation helpers and pins the GPU gate to the actual prepared profile.

The full-suite driver completed every test, then **failed its final workspace-size assertion**. An interim measurement was **3,004,528,639 bytes**, above the 3,000,000,000-byte cap. Identical files in completed retained fixtures now share inodes; every path and byte was preserved. The measured workspace at report generation is **2,982,384,371 bytes**. This exception is recorded, not treated as a test pass. [run_checks5.txt](checks/run_checks5.txt) retains the failed driver output; [finish_checks5.txt](checks/finish_checks5.txt) records the corrected resource check. The driver's peak RSS was not captured before its assertion.

Measured environment: torch 2.11.0+cpu, transformers 5.12.1, eight torch threads, CUDA hidden. All compute used nice -n 10 and the prescribed thread/cache environment. The separate CPU guard benchmark measured peak RSS **1,320,165,376 bytes**, below 30 GiB. No GPU, Git, SSH, scheduler action, paid API, file-deletion command or input-tree edit ran. Network reads were confined to official PyTorch documentation.

The untouched delivery backup is [out_round5](../out_round5/). Work began at 13:56:45 UTC; the deadline is 15:26:45 UTC on 2026-11-19. This report was generated at Thu Nov 19 14:30:09 UTC 2026.

## Review round 5: finding -> fix -> test


| Finding | Fix | Regression |
|---|---|---|
| 1. Dropped batch wrapper | Exact cont_ops wrapper retains exclusion, EXIT log and USR1 forwarding. | Built script equals wrap_batch output and passes the real a/5.py bundle guard. |
| 2. Unpinned build inputs | Reviewed A4 payload, operator MANIFEST pins, extension inventory and alias bases must match before copying. | Changed self-consistent payload, each operator, extensions and alias pins are refused before output. |
| 3. Incomplete operations | Binding derivation, delivery archive/SHA, place/fetch/fill/dry/allocated-proof/guarded-submit/fetch scripts and gated unpack command. | Generated shell syntax, delivery members and command order pass; actual submit checker refuses missing cache proof and an oversized pool. |
| 4. Unbound GPU profile | Prepare bytes plus operator overrides bind settings, selectors, budget and package plan. | Both cache profiles pass; changed settings, selectors, cap and plan fail. |
| 5. Forecast scope | Package D and a19's A4 schedule have separate labelled estimates. | Documentation regression requires both scopes and A4's 7,351.824 s estimate. |
| 7. Refused unpack tree | Scorers require success output after exit 0; the shell handoff uses &&. | Documentation regression checks the warning and executable success chain. |


The wrapper is vendored verbatim from cont_ops17/work/build_r10.py:73–84, without importing that script's executable body. The built wrapper equals the reference output and passes the real bundle guard. Input mutations are stopped before copying: self-consistent replacement base, each operator file, extension content/inventory, disagreement between review inventories and alias-base pins.

The operation helper derives binding fields from authenticated artifact/receipt/preparation files while preserving reviewed done/prep_paths. The generated submission checker runs as real Python in tests: it refuses missing cache-memory evidence and a simulated pool size of 75,000,001 bytes; exactly 75,000,000 passes. Generated shell syntax, Python-3.6 syntax, delivery contents and the queue/CPU/dry-check ordering are tested. No scheduler or large export fetch is exercised by those CPU tests.

The GPU gate checks both all-cache and processor-only profiles. It rejects changed run settings, selectors, numeric types, budget or plan pin. Changed prepared bytes fail the READY proof check. An additional integration check feeds the real applied A4 CPU proof and its exact SETTINGS.json into this gate. Each RUN.json records the adopted plan/profile. Finding 7 uses the review's documented success-output rule; unpack extraction behavior is unchanged. Finding 6 remains A4's reviewed fill-time whole-archive enforcement; job/unpack compare against inputs.archives[0].

## Adoption contract

Follow [README.md](kit_parity50/README.md) in order: apply patches to fresh A4 copies; derive the reviewed target binding; build; generate and place the pinned delivery; fetch/fill and run both dry checks; run the allocated CPU proof; derive/seal the exact prepared profile; pass the GPU gate; guarded submit; fetch and authenticate/unpack. A real target export and owner-authorized transport/allocation remain external inputs. The synthetic CPU binding is not production evidence.

```bash
CUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a19.py" \
  --enable-extensions --base-operator "$LOCAL/a4" --source-root "$EXT_SOURCE" \
  --manifest "$DELIVERY/patches/MANIFEST.json" --extension-pins "$DELIVERY/kit_parity50/EXTENSION_PINS.json" \
  --export-binding "$STEP600_BINDING" --token "$PACKAGE_TOKEN" --out "$LOCAL/step600"
```

Add --processor-only for the 4 GiB processor cache; the full profile uses 12 GiB. Both disable atomic journals and sharding. The intended GPU read uses general/no-requeue, one GPU and 04:30:00. The separate CPU-proof allocation uses preempt without a GPU, as in A4 operations.

The submit preflight requires CPU payload/plan/inputs/operator bindings and entry/bundle success, both dry-check passes, the exact cache allowance with fits=true, an empty general queue and a return pool at most 75,000,000 bytes. The unchanged bootstrap does not independently require read_cache_bytes. The GPU gate seals candidates_argmax, memo on, g3t, empty verify IDs, save_own_depth=false and the exact cache switches/budget from the built package. Processor-only adoption needs its own gate.

A refused unpack leaves its extracted tree behind. Scorers consume only success output after exit status 0. A successful partial return remains partial. No multi-card A4 operator is delivered; persistent-storage requeue remains a separate prerequisite for preempt/sharded adoption.

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

Each stub uses bf16 parameters shaped 2048×1024 and a 1024-element buffer per module. Forward returns a 32-element tensor without model-sized matrix work. Each implementation runs one miss and a warm hit, then seven timed hits; boundary cost is the median of three hashes. These are CPU validation/cache costs, not GPU speedups.

| Parameters | Parameter/buffer tensors | Weight+buffer bytes | Per-call hashing ms | Boundary guard ms/call | Install s | Boundary s |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 268435456 | 128/128 | 537133056 | 392.806 | 31.730 | 0.380 | 0.402 |
| 536870912 | 256/256 | 1074266112 | 782.072 | 59.309 | 0.816 | 0.741 |

Exact samples are in [CACHE_COST3.json](checks/CACHE_COST3.json), rerun during this task. Actual H100 costs and full-process GPU/host peaks remain unmeasured. Cache caps bound cache-owned storage and transient copies, not all model/caller memory.

## Framework evidence

[FRAMEWORK_EVIDENCE.md](FRAMEWORK_EVIDENCE.md) records installed torch/transformers file:line citations. This task reread torch TensorImpl.h:291–305, 413–418 and 2046–2056; autograd/graph.py:242–258; optim/sgd.py:378–380; and InferenceMode.h:30–50 under `/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/`. Tracked in-place operations update counters; detach shares them; .data/set_data and raw storage writes need additional guards. Inference tensors lack counters.

The official [increment_version documentation](https://docs.pytorch.org/docs/2.11/generated/torch.autograd.graph.increment_version.html) and [inference_mode reference](https://docs.pytorch.org/docs/2.11/generated/torch.autograd.grad_mode.inference_mode.html) were checked on 2026-11-19. [TORCH_VERSIONS3.json](checks/TORCH_VERSIONS3.json) contains the rerun probes and source hashes. Packaging and profile validation introduce no new framework behavior.

## Patches and authentication

A4 source base: `813fe4c57b2deed4bd731dd1e3493b6b0bed8d31e7bff92ff112cf5c9df823c3` over 927 files. Reviewed A4 payload: `4498fca72a8e4b476b38f097ffdf3ff88b5aa20fc036bd196b18a5706e9fe46d`, 5252958 bytes. B5 archive: `ac2e259025d6a821aa5eb13e236f0635bd970313859086fc2f3ce3276647f2f0`. B5 application proves patch applicability; the GPU kit authenticates A4 only.

| Patch | Bytes | SHA256 |
|---|---:|---|
| [01_bounded_read_caches.diff](patches/01_bounded_read_caches.diff) | 90430 | `369af9663fbc1008f9ecf5a32c5067ba4a5f4cd31412f07db8263b13b23fd4c3` |
| [02_atomic_scene_shards.diff](patches/02_atomic_scene_shards.diff) | 218841 | `5f76cf79e29471138161e476daf3920ec2bcbf751586fc47528fbd7388530cfa` |
| [03_production_integration.diff](patches/03_production_integration.diff) | 171470 | `f9345e2e537fcdfb80e3cf296d46b9691cf9e69bd252e7ccf1fc52362a57188b` |
| [04_operator_cache_bound.diff](patches/04_operator_cache_bound.diff) | 2723 | `0d3bdc2d943554cd525627466d2d71f30881884e76df95204ede6c1accdb9061` |
| [05_operator_return_and_proof.diff](patches/05_operator_return_and_proof.diff) | 3490 | `4e5a76f83eefc22505b8949ee6e83c920d8d3e2670ce669372e48b2041caf116` |

Reader patches 01–03 add 35 files under u0; original reader bytes remain unchanged. Operator patches 04–05 apply outside src and affect tower_sequence.py, unpack_return.py and package/a/5.py behind read_extensions. The bootstrap remains byte-identical. Tests ship in the reader patches. The kit and verbatim cont_ops dry helpers are separately pinned in [MANIFEST.json](patches/MANIFEST.json).

Every workspace suite ran. The affected round-5 suite reran after strict profile-type checks were added. Fresh-application OFF, round-4, round-5 and comparator suites pass; other applied source bytes match their tested workspace counterparts. The fixture storage wrapper shares reviewed immutable source bytes and repeated archives, detaching shared files before edits. Retained fixtures were also shared without removing any path. [FIXTURE_STORAGE5.json](checks/FIXTURE_STORAGE5.json) and the storage command outputs document the resource correction.

## What could go wrong and how to notice

| Risk | Detection/action |
|---|---|
| Wrong base, skipped operator patch or modified overlay | a19 refuses payload/operator/extension/alias mismatches before copying. |
| Wrong target export/preparation or stale CPU proof | Binding derivation, sealed fill constants, package/admission pins and submit preflight reject mismatches. Never use the synthetic binding. |
| GPU gate tests a different read/cache profile | Prepared-settings proof and parent/worker validation reject it; RUN.json retains the plan/profile. |
| Pool full, queue occupied or memory allowance missing | Generated submit refuses before submission. Pool tests simulate stat sizes. |
| Refused or partial return gets scored | Require unpack exit 0 and success JSON; treat complete=false separately. A directory alone is not admission. |
| GPU kernels, eager SAM, layout or RNG change bytes | Require zero answer/trace differences; equal scores do not waive the gate. |
| Hash/copy cost erases savings or cache caps miss process memory | Require useful hits, lower full worker_wall_seconds and measured full-process headroom. |
| Hard death or untracked mutation | Unverified receipts fail ON unpack; fresh journals may be needed. Restored-between-boundary raw writes remain unsupported. |
| Real transport, restore, namespace or requeue differs from stubs | Validate on the intended system; no preempt/sharded adoption before persistent-storage requeue checks. |
| Fixture storage approaches the cap | Check unique-inode bytes with du -sb. The aggregate driver caught an overrun; the exact failure is retained and corrected checks pass. |

## Not done

No real step-600 export/binding build, weight restore, production namespace/storage/transport, GPU parity/performance/memory, scheduler action, upload, return publication or persistent-storage requeue ran. No batching or multi-card A4 operator is delivered. The array policy remains approved=false. No delivered CPU suite requires local OS sockets; socket-backed integrations remain unrun. The ON GPU byte gate remains required.

## Required review audit sections

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

Commands ran from `/scratch/jjyeung/orch_n30/so_read`. work/cpu.sh exports CUDA_VISIBLE_DEVICES="", OMP/MKL/OPENBLAS threads=8, TOKENIZERS_PARALLELISM=false, PYTHONDONTWRITEBYTECODE=1 and scratch caches, then runs nice -n 10 with the required Python -I -s -B. Children inherit the environment/priority. Tests also receive READ_INPUT_SRC=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/A4/src and READ_TEST_TMP=/scratch/jjyeung/orch_n30/so_read/work/test-artifacts. Fresh-application commands additionally set READ_OPERATOR_SOURCE and READ_OPERATOR4_SOURCE from MANIFEST's verification root/operator. work/run_fixture5.py changes only fixture storage while preserving bytes.

```bash
bash work/cpu.sh work/gate_integration5.py
```

Exact output:

```text
PASS: real applied A4 a/5.py CPU proof and exact prepare SETTINGS.json feed the adopted GPU profile.
{"enable_caches": [0, 1, 2], "plan": "1c2cc3e1c0a2a0a0402c6274aade636e96aff5f7266488bf1159768c849fae27", "read_cache_bytes": 12884901888}
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
        "data_ptr": 136182784,
        "object_id": 140471083279184,
        "version": 1
      },
      "before": {
        "data_ptr": 136182784,
        "object_id": 140471083279184,
        "version": 0
      },
      "object_changed": false,
      "operation": "parameter.add_",
      "pointer_changed": false,
      "version_changed": true
    },
    {
      "after": {
        "data_ptr": 136193280,
        "object_id": 140471083279504,
        "version": 1
      },
      "before": {
        "data_ptr": 136193280,
        "object_id": 140471083279504,
        "version": 0
      },
      "object_changed": false,
      "operation": "detach().add_",
      "pointer_changed": false,
      "version_changed": true
    },
    {
      "after": {
        "data_ptr": 136193856,
        "object_id": 140471083279184,
        "version": 0
      },
      "before": {
        "data_ptr": 136193856,
        "object_id": 140471083279184,
        "version": 0
      },
      "object_changed": false,
      "operation": "parameter.data.add_",
      "pointer_changed": false,
      "version_changed": false
    },
    {
      "after": {
        "data_ptr": 136196480,
        "object_id": 140471083279504,
        "version": 0
      },
      "before": {
        "data_ptr": 136194304,
        "object_id": 140471083279504,
        "version": 0
      },
      "object_changed": false,
      "operation": "parameter.data assignment to cloned storage",
      "pointer_changed": true,
      "version_changed": false
    },
    {
      "after": {
        "data_ptr": 136196864,
        "object_id": 140471083279184,
        "version": 0
      },
      "before": {
        "data_ptr": 136196864,
        "object_id": 140471083279184,
        "version": 0
      },
      "object_changed": false,
      "operation": "parameter.data assignment to same storage",
      "pointer_changed": false,
      "version_changed": false
    },
    {
      "after": {
        "data_ptr": 136196928,
        "object_id": 140471083279504,
        "version": 0
      },
      "before": {
        "data_ptr": 136196928,
        "object_id": 140471083279504,
        "version": 0
      },
      "object_changed": false,
      "operation": "numpy raw storage write",
      "pointer_changed": false,
      "version_changed": false
    },
    {
      "after": {
        "data_ptr": 136197120,
        "object_id": 140471083279184,
        "version": 1
      },
      "before": {
        "data_ptr": 136197120,
        "object_id": 140471083279184,
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
      "after_install_seconds": 0.38022057013586164,
      "after_per_call": {
        "max_seconds": 0.03383130906149745,
        "median_seconds": 0.031729504000395536,
        "min_seconds": 0.029925306793302298,
        "seconds": [
          0.03334116330370307,
          0.03383130906149745,
          0.031425859313458204,
          0.031729504000395536,
          0.029925306793302298,
          0.030812188051640987,
          0.03337936010211706
        ]
      },
      "before_install_seconds": 3.722589462995529e-05,
      "before_per_call": {
        "max_seconds": 0.5000445619225502,
        "median_seconds": 0.39280625712126493,
        "min_seconds": 0.36223123501986265,
        "seconds": [
          0.44469010503962636,
          0.36223123501986265,
          0.36275877617299557,
          0.5000445619225502,
          0.36780836433172226,
          0.39280625712126493,
          0.3995287148281932
        ]
      },
      "blocks": 128,
      "boundary": {
        "max_seconds": 0.4871786837466061,
        "median_seconds": 0.4015554361976683,
        "min_seconds": 0.38842458138242364,
        "seconds": [
          0.38842458138242364,
          0.4871786837466061,
          0.4015554361976683
        ]
      },
      "buffer_shape": [
        1024
      ],
      "buffer_tensors": 128,
      "dtype": "bfloat16",
      "median_speed_ratio": 12.379842342205169,
      "parameter_count": 268435456,
      "parameter_shape": [
        2048,
        1024
      ],
      "parameter_tensors": 128,
      "weight_and_buffer_bytes": 537133056
    },
    {
      "after_install_seconds": 0.8156947563402355,
      "after_per_call": {
        "max_seconds": 0.060988201294094324,
        "median_seconds": 0.05930854007601738,
        "min_seconds": 0.055995688773691654,
        "seconds": [
          0.060988201294094324,
          0.058708999771624804,
          0.055995688773691654,
          0.05732167884707451,
          0.059572746977210045,
          0.05930854007601738,
          0.059885415714234114
        ]
      },
      "before_install_seconds": 9.682495146989822e-05,
      "before_per_call": {
        "max_seconds": 0.8367672781459987,
        "median_seconds": 0.7820721101015806,
        "min_seconds": 0.7260872782208025,
        "seconds": [
          0.8128574178554118,
          0.7620659181848168,
          0.7820721101015806,
          0.738831892143935,
          0.8367672781459987,
          0.7260872782208025,
          0.8002524022012949
        ]
      },
      "blocks": 256,
      "boundary": {
        "max_seconds": 0.7416171422228217,
        "median_seconds": 0.741004372946918,
        "min_seconds": 0.7291732891462743,
        "seconds": [
          0.7416171422228217,
          0.7291732891462743,
          0.741004372946918
        ]
      },
      "buffer_shape": [
        1024
      ],
      "buffer_tensors": 256,
      "dtype": "bfloat16",
      "median_speed_ratio": 13.186500782166908,
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
  "max_rss_bytes": 1320165376,
  "nice": 19,
  "threads": 8,
  "torch": "2.11.0+cpu"
}
```

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
round4: CPU step-600 fixture: /scratch/jjyeung/orch_n30/so_read/work/test-artifacts/cec5e6f9e5794ff197ad5f449345ec32
round5: {"passed": true, "pool_bytes": 75000000}
kit: OK
kit_launch: OK
PASS: all 8 round-1 regressions fail against the round-1 reviewed implementation.
PASS: all 13 round-2 regressions fail against the round-2 reviewed implementation (14 failures including both CLI variants).
PASS: round3_before reproduces FAILED (failures=15).
PASS: operator3_before reproduces FAILED (failures=2).
PASS: lock3_before reproduces FAILED (failures=2).
PASS: round5_before reproduces FAILED (failures=11).
PASS: round4_before reproduces FAILED (failures=7, skipped=1).
PASS: node4_before reproduces FAILED (failures=1).
PASS: f16_behavior_before reproduces FAILED (failures=1).
PASS: Python syntax, shell syntax, and default-off execution guards.
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/run_checks.py", line 96, in <module>
    assert report['workspace_bytes']<3_000_000_000
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError
```

```bash
bash work/cpu.sh work/finish_checks5.py
```

Exact output:

```text
PASS: 102 tests in 13 workspace suites; all nine fail-before controls reproduced in run_checks5.txt.
PASS: corrected workspace 2945804279 bytes < 3,000,000,000; all fixture paths and bytes retained.
NOTE: full-suite driver exit 1 was its storage assertion after all tests passed; its RSS was not recorded.
```

```bash
bash work/cpu.sh work/dedup_fixture5.py
```

Exact output:

```text
Preserved bytes at 1882 fixture paths; shared identical inodes. No path removed.
2994873569	/scratch/jjyeung/orch_n30/so_read
```

```bash
bash work/cpu.sh work/share_retained5.py
```

Exact output:

```text
Preserved all paths and bytes; shared 2766 unchanged files across three named retained fixtures.
Unique file bytes released: 73581990
2921292863	/scratch/jjyeung/orch_n30/so_read
```

```bash
bash work/cpu.sh work/run_fixture5.py work/build_patches.py
```

Exact output:

```text
PASS: 3 additive reader diffs (35 files) plus 2 default-OFF A4 operator diffs; zero-fuzz application; unchanged original reader hash trees.
PASS: OFF, round-4/5 integration and comparator suites pass from the fresh applied A4 tree; both complete 927-file base inventories authenticate.
Applied verification root: /scratch/jjyeung/orch_n30/so_read/work/apply-round5/a2f354ad3b124ac7ab58b9fe4e4e04df
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
Ran 15 tests in 2.963s

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
Ran 13 tests in 0.180s

OK
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_off.py
```

Exact output:

```text
test_every_output_byte_and_source_hash_matches_original (__main__.OffContractTests.test_every_output_byte_and_source_hash_matches_original) ... ok

----------------------------------------------------------------------
Ran 1 test in 5.943s

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
Ran 7 tests in 0.005s

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
Ran 17 tests in 4.316s

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
Ran 13 tests in 4.087s

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
Ran 9 tests in 2.031s

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
Ran 2 tests in 10.708s

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
Ran 2 tests in 0.016s

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
Ran 4 tests in 23.783s

OK
{"output": "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/cec5e6f9e5794ff197ad5f449345ec32/verified-return", "complete": false, "status": "FAILED", "sha256": "c2e9c1b1c400e36a20b24ca1cb3146e178a7b4d1702fcc4f7e58918836e7ca0f"}
CPU step-600 fixture: /scratch/jjyeung/orch_n30/so_read/work/test-artifacts/cec5e6f9e5794ff197ad5f449345ec32
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
Ran 7 tests in 9.422s

OK
{"passed": true, "pool_bytes": 75000000}
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
Ran 9 tests in 0.342s

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
Ran 3 tests in 0.062s

OK
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/apply-round5/a2f354ad3b124ac7ab58b9fe4e4e04df/src/u0/tests/test_off.py
```

Exact output:

```text
test_every_output_byte_and_source_hash_matches_original (__main__.OffContractTests.test_every_output_byte_and_source_hash_matches_original) ... ok

----------------------------------------------------------------------
Ran 1 test in 6.952s

OK
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/apply-round5/a2f354ad3b124ac7ab58b9fe4e4e04df/src/u0/tests/test_round4.py
```

Exact output:

```text
test_f1_step600_package_preserves_a4_contract_and_binding (__main__.Round4Tests.test_f1_step600_package_preserves_a4_contract_and_binding) ... ok
test_f2_step600_real_job_and_rehearsal_memory (__main__.Round4Tests.test_f2_step600_real_job_and_rehearsal_memory) ... ok
test_f3_cache_only_return_refuses_unverified_journals (__main__.Round4Tests.test_f3_cache_only_return_refuses_unverified_journals) ... ok
test_f9_off_builder_guard_and_processor_only (__main__.Round4Tests.test_f9_off_builder_guard_and_processor_only) ... ok

----------------------------------------------------------------------
Ran 4 tests in 29.251s

OK
{"output": "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/5a365504dce84c1badfa495d5920ce38/verified-return", "complete": false, "status": "FAILED", "sha256": "eed1d247e230ecff6dc94d1be65627650121ec260f5e18dd458b62178e1edede"}
CPU step-600 fixture: /scratch/jjyeung/orch_n30/so_read/work/test-artifacts/5a365504dce84c1badfa495d5920ce38
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/apply-round5/a2f354ad3b124ac7ab58b9fe4e4e04df/src/u0/tests/test_round5.py
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
Ran 7 tests in 10.904s

OK
{"passed": true, "pool_bytes": 75000000}
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/run_fixture5.py /scratch/jjyeung/orch_n30/so_read/work/apply-round5/a2f354ad3b124ac7ab58b9fe4e4e04df/src/u0/tests/test_compare.py
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
Ran 9 tests in 0.404s

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
Ran 8 tests in 0.017s

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
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/7ab03c7df616426fa02cc568f5d33de3/u0/a8.py", line 65, in <module>
    raise SystemExit(main())
                     ^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/7ab03c7df616426fa02cc568f5d33de3/u0/a8.py", line 61, in main
    return launch(rest)
           ^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/7ab03c7df616426fa02cc568f5d33de3/u0/a4.py", line 2, in main
    from a8 import source_hash
ModuleNotFoundError: No module named 'a8'


======================================================================
FAIL: test_f1_actual_isolated_script_plain_and_opaque (__main__.Round2Tests.test_f1_actual_isolated_script_plain_and_opaque) (opaque=True)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round2.py", line 67, in test_f1_actual_isolated_script_plain_and_opaque
    self.assertEqual(result.returncode,0,result.stdout+result.stderr)
AssertionError: 1 != 0 : Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/82c94cf615d8411281b393d0efcbd28c/u0/a8.py", line 65, in <module>
    raise SystemExit(main())
                     ^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/82c94cf615d8411281b393d0efcbd28c/u0/a8.py", line 56, in main
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
Ran 13 tests in 0.190s

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
AssertionError: 139702181627456 unexpectedly found in {139702181627456, 139702181627776} : Per-call weight hashing

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
Ran 9 tests in 0.919s

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
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/c25ea9ec5e5f46c488e6b3994e1d16d9/0.py", line 44, in main
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
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/c25ea9ec5e5f46c488e6b3994e1d16d9/0.py", line 18, in dispatch
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
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/c25ea9ec5e5f46c488e6b3994e1d16d9/7.py", line 139, in main
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
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/c25ea9ec5e5f46c488e6b3994e1d16d9/7.py", line 87, in run
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
Ran 2 tests in 9.761s

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
Ran 2 tests in 0.011s

FAILED (failures=2)
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
AssertionError: '#SBATCH --exclude=orchard-community-2\n' not found in "#!/bin/bash\nset -euo pipefail\nexec /usr/bin/python3 -I -s -B - <<'A'\nimport hashlib,io,json,os,sys,tarfile\nfrom pathlib import Path,PurePosixPath\nj=os.environ.get('SLURM_JOB_ID','')\nif not j.isdigit():raise ValueError('Allocation required')\nb=bytes.fromhex('1f8b08000000000002ffed5aeb6fdbba15ef67ff15bad907490eabf8edc4b91ad0b5b95b87db079af602836108b244db6a644913e93c56f47fdf3987d4c3b29366187687612212db12c9c3c3f3fcf1d173be8a3479f11f2d3d28935e8fbe7b87dfbde1685afe56ef27d3e9f085d17bf13b949d907e0e43bef8ff2cdf3a867192f90f71ea87def24172713233c6c349ef623865f53ab1f107e309549e9c071717531e8ca7c3d1f9ea7c1c4e06d3fe64381ef656ab492f3cef2f838bdec89f8cfc8bf1c5e09c5f9cafc2fef9007aaf26e3e5b83f395174633fa911ed71ee8fce07cb8b7eb81c4d07cb657f32e5637fc0a7c341182e2ff8743098fa237fd9eb8d277c74319a0efdd5f945180ef868391e8c145199def004c941bbfe60381a4fa6e717279def9d176d79c4379dece13f3ec6d3fe3f1af5274dff1f8d5bffff5dcac9c9c9c79c0b9edf7223cbd37017c8284d0c3fdc4642c02f66807cd651b266861fc769e053f532dd25a18057496840ef5d2ce14beef2c4017a9d689ba5b93436bed8c4d19261826120e4551473261e446795a75b23f325d61abaf14778ec743a215f195bff867b6124a045b0b1f23495cc48f30898f063f895f1dc9769ae63873deb18442fcd838d9f87dea6df738274bb052e356968d831907049d3cfd7b7ac0b9f8275bb3777f803e9187f303e24f1034c058253c00db981ff347b19f35b1ed7a75f10e2f925088d677eaedea338eed2fc86e702c5f660645192f0d001d2d1ca88794223db7f7407d4141fe62f07b385ebce85cc69aa67a67f36069f346d567fd5a7346dda0b64d308566b179f1d8cccc23a68e5e41c22b6e4f7d2b26dece00bd0b0c47e73d3270d9b30685fd39a9b419aaca2b5b9989b0df142b3c61bec7338e05d1e49ae4624c6c2dd361316d056e3c3eca1b7ee36a5e9fdd4244c3333723f12dcf8cd8f77fc2acfd3dc32ff04a616f3b054bc017a4ed6f0c25f499ea39c73b9cb4c354f90a83bef9260672f078b9a0ca74f0815ba2af32dedeca889748a5685fe4b838d120b0d0809bb68c91698b9435cf417f665b65bc651704463bde3fa0279e43c5484cc33f0caaf3c906768d4bb24920f675fbf3ef05db23e4b6f3653d33eb34cbf3ff682547a7e669eaac1e626a5427301e4b4f2b53b3a4ada96a5464126e4fa1f050f8400800967c3efc368cd0570e4ba05cd7d2c6082dcee22b931b46f3ba0a1a4491646c77a54ee0a74b735a2a47846ab4852696c9dc4df7287142990a065d69cf9ccb467609e324a767caf53247050cb069d19a6e398489944a6e8d94e86f4668706f52511fe8a1b411a72653599abd4919967aaef65869d79229ded4d18e5967a10eee77cc719bf8f84f4d21b7a02e56adb5792833938a0c61c9c8cb8db2ab92ab5824d60d473a2041562f56ac608f66b1f06b222827d4d97cf8b720d97729b4ed7c1189faef64cb150987f169cbdfef8e5b8496aa95bd41d0d016c2a341746240c14038533aa73d65c5ae6927cd65bef9057ddd87eac3188367ff004fffb8e27017fa279698018bc1eb7c9a2d4fb01d8dceb54814f9844ad6194643b29b0298aae124d112a8e523f8c99c78266a39b9afb966fd3fcc164dfbedb5a72be88044cde750d7315ddf3d05b0f2552c9b8308f8eae492c547f1837e01946780f2bbc2da4f4986b8a7313883d22a27d32c2df427f5fec72be05fd78396827ca0bb5fce2c7823f83ca2a92a252a47dc4177fd9c5b1015607419d07371058572b489e2867b079875e8208f25de21e41058d26ac090d14118aced8de86700d76ec79e8e29ee7baa6e761a5e7993315c2ff0f9709d3ff3afeef4f4793e101fe9ff65afcff3be1ff0f05b02abc8b32b5bc4bc171d3d8971c313ea40a4af69064d384d7c0701df113d28734c764b4e54c038e27e0fea72fbf5e5dbb961940048942184978009ab6febdc9ecceeb0f5fde7f86dafeb8c7eaff4370ecebd77fb97a039d5d0bb2e8d066f0d9a3cf3e7d0ee87304898bf059c8459047194c51402a0f6efc3527b4a6c0dc3c8c0209786feb0266bae3b9c9206672e1cecd04666a2286840e7d485031c030083431778f712cfc5beea577891742fcddb81423591524a934a2b36b424e618f846c5747eb83fa5b9e47ab072f0aa1c9a239827cc8b0eb90812cd8808d16805732e01bf0e40424b7501211dc0748ed1172b15035ec1683f2331653d485f0004119024300182907d4500555d621c44f2e8d7024057c825646144296016c5bcf0007dc29ded5828b5b6acdf20c963f7c7a73f58981c6d2240afcb863408ee50a5d2b1a90c17712f23ea0e54bc12540cdb5a843a4bda64503687c8891542395fc5252991f9bf6510c5aa8c528da19843dcc0206f201f7903ecf9d860194884f7382109b0ca378d1d97fb48a1facc8e20aba12c7451d4cecc0cc011a21e8039727473d328d5d7293a0c91fe98b80176628dcbaf71542d45e88022f34ef921b223073cb567594c614342b2bd563558d7ed084bfa57a9b000dac2107f7e9330a6c2e31ca046009f43cb7882e30853f187fbdfef01e1676006825ccc25847b71c248ecbce65cc8d18cc1ff70b700b25916a1700a3276e8a6cb9423502d6ffe52c6b66555b2817d5361a60cd35d152cf0054491f628d7ff6f6cdd5fbcf6f3fff4d815156f6ea68c313eeb7ef1d1a3f623827541d4f8011983db76896b4cf41ebd4066d928479864b9208616eb049614aeeb76eb7349f63263243aac78d07daef854473761013bbdd6f378ac2cd82f8be41960f50acc9ccc783e091ca12f47e077150a0d22bbc72b67ae57d791808d5bc51027b758dfe9fae5ebdf11aea2003ee760bad906db9a0082dbed2288b4064e9a1688b442b701e2d50e4ea89157169562c146d56c51f7a892cdb8544212b81c179d850d52a15d3db42b33633405969e6e1f2b4deaa9cdaf5e70f1fcd8aa680c16029a7b6b5cc192d814dc896c0c05c274cd034a54c7ca373a64979085e50f09d4ba55d8a25ca6054fd62518df3afd956d50de6b2851c1c25e6ac7fdeeb3153e5f5eae5005e76bbfb21518bfe7ba784015a012ac7e47cc3fd5ca08e1ecf32b0e448785e4463dca3c8d3982941212a10cfcb4c95f33632dba5da5985245ff874b05aa304757b07ec722b68e3c9902ed172a224e4f716ede96909cf7b0b6d5fc81e6dc97568a34cb835562d325e45d885360c7bbb92113db757c64b12b72fe1d72a4a22b1f1960fee800c58ef3221b1397e6856cc972fc958ecd33e2c8bb5c13cd95c99926e4fe6f46473354ddd9c99ced714567275013ccd1c4ee825f98222810e711c1a1cb84845b789158e8d53b82d0eb38f1c8e5bb8eb52d285805005e37f6f9c8a5f456e7e1066518410c97ed8b01e7da1cfd3191e66f03401da7d454b77fc2ce349a86c51474f8567ebfa6464bbb4335b8235c5e73ed4a5ec7d750f03236ae110040d25605ccf80880db981b4beded0363f8c161b649c8648831b2ed5cea690bba571c7a3f54662162777c63d58c0fdd2d942c3c293d576b06a407c1615d7f01df3f7fe96c3da2a40e4acde4b8c0a0750af84766410984162e5fbc47009c440625b684e91814e36c017a5952ebfb2904b982183e815b2354fc162734844b4644976715c2c56286618d0c1a13afcb8c427ece7e2073d8591bf4e5221a30081c5250e59a808aad19ea87d638a164acec3d1dcd8df2e43dfe8fa339aae2379220036cefb0e1b38acdfeb390b324b923589d001c230014b09c0b9c6af0f09641ccfc3397a1ea01ef8b6d95e6b9413333fa3fafe3cfc6c329d0168d5e0be8710a2db5b660d5517e2715639ee070500f164a3eb70a004a59e701474a8d8abacd942ea20f5db28c05561b6fbf1724ef8dba147a6e66af66da60c13006aa98063ab4efcb04b7e1c65a88a039a64e5b7a82a08fc4abbd4efb04e5156ce76ef2a05fd83e7a9b0066c7c6e33dc25734db0159b4e8a749a549eaab3e42ed1fecec026548e602a2b92d45910038b2e6e0638f8f18c2c0a4fb89ce1f73cd8e13af3d9ab513c5c230660a5d9c723015cb9d00b98ebd155272d8560243f90f183dad410225a27101eb09f69ff2831e3f2fb72e547f12e5756a6d33441d81e23d3c135210ac1b2ffe8828c5e224241ee9e9b63ca05f66c099677d351677f15582c63a76b694102712d3d1bd3a0d60aea0766b18aee552c55bf5572d4b37966f4ed76557b72dc68a57bcf4d2d0858336ae11715a031080f126ac8970a811df4bbd433544bb20af424244f10280675a6d72f77d022579111abf514889fb98914302fa9d4a9870f5d58915979c50f1e5f540480a292050c7e4c121599f257956e92b2baaa75dd840e7d765b00a27a75fb4c5e90077b2f99357779cae1fc38aed33942a690b7fed62b5efa84b0b3ded2c196965fb9e9f298755e7f79f7eed5a762c1a3e7569d8bea17fa54948e023cba2a6075193855068dc09cacf311b3ebd709d4d9990b38bddbef0d46ddee9011f71ee016c818d042e8ed34f55a2d7354a71e1a843e9d6af4991d36a6a668c956b38e4e29d46e872c2cb8f7b3db6cf6b3db9f144c92251e0496b70944e7486d991ad4534b425d9a300996fc82273b06e42a85cb2104cd0c1f4233245b6332323240336492b4ad36c4db02807072639d0360728c2bc42306f183c432042db09ef473a0768b770f9629e4d3150045a9892942087456a0015d077491a0a1f48bf80612946b4d46dd8bd3c9e8743880bfeeb84f7fa7e3fee9c0ee9e7770344fabd285f6a74a18830e866e0cf21eeaf50e18e62e50d2a22abd7acfa50a834818254aa5a3a45b1ba161f7d42c8b77c203998192f1644af5b292d3a1fd444fc087d07417aef9a33d4e0f26707a6824b590546dac1413c18b04e50d0198279de5b987c7783f8408fbbcabb3b852403df6d8e19c76121c49b3a4ba783b8867396aab41397b901be0018d66539efe7b750d6bedb24ade05e520cd22e066d820792044cdf5c17b3cbdf3945aa841331cec05aafd31ba5deb9bd9d48d79e0eedf557ada8b0906070919dfbedb0d9278525904d3035b31173f1fb0d78cb376672fea6579baac6f519f9c9cbca6134eb5d8907e94e8004051811030f8a1818b3b58d16004521ac687eb57efe894e59968e8dfdbc2ae36841fdb555bfc5418eaf1cb15606dc04dfdc60eed5a979b721dbde5ad762b1bbbe60d7d55a7c77483a4b1315e69bcdc85a9d4cff02e093c0904017ee6d6aaca1d711b87c7252f6d4ce9f655ad43401b8f37c86c207d94ac9781ac9ea46873ec20ebc0e0942209a6ed67c5ae26f7c3c45bc2c27757ef3e94095823b15a02d4980acfdd8f69e763a952a5137e1f701e0a0a8f459aa2bb12f601e0dfbfe9d4b8817670e769cfae2e337ddab2dadb18a86ec4cc67bd85ba02979d994b7d4b0b7eca9cf3e209832bda4afdbada334ce6f8a51ba0bdebd1951b6553fe796140783beed697b45ed23f2d9ee05e7f796af2032f848124440b0c010117425d82e91c7f7d5470228d6fb965eb2b487631ed62b27a6752ade19f1711f68cab71dfafb2b14f577fb97af5e9fad5afa575959ba0f53e05f03fa2099d943c7d0bc49eed47c33d2ae59dbb724b2415a597d0cab2de9cd1138072f8990a8727b7519e2673f3f59737afbcdfde5ebffdd3af57de9babdfdebebeba066e441647c00f23152b37b87e10926fafeee17dfff8ba45f9b8dd5e12694b5bdad296b6b4a52d6d694b5bdad296b6b4a52d6d694b5bdad296b6b4a52d6d694b5bdad296b6fcef957f02760bc5e700500000')\nr=Path('/tmp')/('a'+j+'ab0123456789')\nr.mkdir(mode=0o700)\nwith tarfile.open(fileobj=io.BytesIO(b)) as a:\n    for e in a:\n        n=PurePosixPath(e.name)\n        if n.is_absolute() or '..' in n.parts or not e.isfile():raise ValueError('Unsafe input')\n        p=r/e.name;p.parent.mkdir(parents=True,exist_ok=True)\n        with a.extractfile(e) as i,p.open('xb') as o:o.write(i.read())\nos.chdir(r)\nos.execv(sys.executable,[sys.executable,'-I','-s','-B',str(r/'0.py'),str(r)])\nA\n"

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
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round5.py", line 191, in test_f4_gate_pins_adopted_settings_and_profile
    self.assertTrue(hasattr(kit,'validate_profile'),'GPU gate accepts an unbound read profile')
AssertionError: False is not true : GPU gate accepts an unbound read profile

======================================================================
FAIL: test_f5_forecast_identifies_both_reads (__main__.Round5Tests.test_f5_forecast_identifies_both_reads)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round5.py", line 217, in test_f5_forecast_identifies_both_reads
    self.assertIn('Package D',text);self.assertIn('636-item',text)
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'Package D' not found in 'VERDICT: DONE The round-4 fixes pass CPU verification; adopt only after the GPU byte gate.\n\nMeasured: **95 workspace tests and 14 fresh-application tests pass**. Five patches apply exactly; original reader files and complete OFF output bytes remain unchanged. The backup is out_round4/. The CPU fixture completes 636 synthetic reads with five verified ordinary journals through real A4 preparation, rehearsal, bootstrap and job.main.\n\nMeasured existing distance time is **23.60 s/item**. Estimated 580-item elapsed time, crediting no cache saving, is **3 h 50 min** on one card. Ideal two/four-shard estimates are **1 h 56 min / 59 min**, excluding staging, queues, preemption and scene imbalance; they require an undelivered multi-card operator. Measured CPU guard/cache overhead on a 268M-parameter bf16 stub is **25.9 ms/call**. This is not a GPU saving.\n\n## Review round 4: finding -> fix -> test\n\n| Finding | Fix and test |\n|---|---|\n| 1. Incomplete step-600 package | a19 uses A4 build_r1-style post-processing, preserving 8.py, run keys and admission. It requires the reviewed target export/whole-archive binding and seals the fill helper. Wrong binding/receipt checks fail; the documented old build fails before. |\n| 2. Adoption profile not exercised | Real job.main constructs actions 0/1 from packaged 9.json. Real 7.py rehearsal produces MEMORY.json with 12 GiB cache allowance. Stub workers produce five verified ordinary journals. The old CPU-proof helper fails the allowance test. |\n| 3. Unchecked cache-only return | ON unpack rejects non-true WEIGHTS receipts. Invalid-value regressions fail before/pass after; real authenticated partial-return unpack rejects an unchecked journal. |\n| 9. README nits | Commands use explicit delivery/source roots; kit pin is A4-only; README states what bootstrap admission actually checks. |\n\n**Step 600: one card, caches only, general/no-requeue.** Apply 01–03 to a full A4/src copy and 04–05 to an A4 operator copy. Define the local roots using [README](kit_parity50/README.md), then build:\n\n```bash\nCUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a19.py" \\\n  --enable-extensions --base-operator "$LOCAL/a4" --source-root "$EXT_SOURCE" \\\n  --export-binding "$STEP600_BINDING" --token "$PACKAGE_TOKEN" --out "$LOCAL/step600"\n```\n\nThe required binding includes target run/step/object/preparation identities and archive_bytes/archive_sha256. The CPU task has no real step-600 export; its test binding is synthetic. The generic a12 operator build is refused. Add --processor-only for the 4 GiB processor cache; otherwise the cache allowance is 12 GiB. Both disable atomic journals and sharding. A4\'s fixed schedule remains 636 items; changing it requires a separately reviewed operator/proof.\n\nUse the generated fill helper, regenerate CPU proof through package/a/5.py, and retain the generated tower_sequence.py beside unpack_return.py. Exact fill/proof commands are in README. Require read_cache_bytes in MEMORY/CPU.json, along with payload/plan/inputs/operator binding and fits=true. The unchanged 0.py admission does not independently require that field. Cache-only returns retain ordinary journals; ON unpack refuses unchecked weights even on partial returns.\n\nBefore adoption, require **zero answer/trace byte differences**, useful cache hits, net worker_wall_seconds savings, and full-process host/GPU/envelope headroom. ON\'s eager SAM construction and boundary hashing need the GPU gate. The sample overstates reuse. Keep models frozen; persistent raw writes fail at boundaries, while restored-between-boundary writes are unsupported. Hard kills can require fresh journals. Validate persistent-storage requeue before any preempt/sharded use. Stage source trees as archives and run the kit with --public. No launch ran; preserve step-400 deliveries.\n\nExact commands, outputs, citations and limits: [REPORT](REPORT.md). Patch/base pins: [MANIFEST](patches/MANIFEST.json).\n'

======================================================================
FAIL: test_f7_refused_unpack_not_scoreable (__main__.Round5Tests.test_f7_refused_unpack_not_scoreable)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round5.py", line 224, in test_f7_refused_unpack_not_scoreable
    self.assertIn('refused unpack leaves',text.lower())
AssertionError: 'refused unpack leaves' not found in 'verdict: done the round-4 fixes pass cpu verification; adopt only after the gpu byte gate.\n\nmeasured: **95 workspace tests and 14 fresh-application tests pass**. five patches apply exactly; original reader files and complete off output bytes remain unchanged. the backup is out_round4/. the cpu fixture completes 636 synthetic reads with five verified ordinary journals through real a4 preparation, rehearsal, bootstrap and job.main.\n\nmeasured existing distance time is **23.60 s/item**. estimated 580-item elapsed time, crediting no cache saving, is **3 h 50 min** on one card. ideal two/four-shard estimates are **1 h 56 min / 59 min**, excluding staging, queues, preemption and scene imbalance; they require an undelivered multi-card operator. measured cpu guard/cache overhead on a 268m-parameter bf16 stub is **25.9 ms/call**. this is not a gpu saving.\n\n## review round 4: finding -> fix -> test\n\n| finding | fix and test |\n|---|---|\n| 1. incomplete step-600 package | a19 uses a4 build_r1-style post-processing, preserving 8.py, run keys and admission. it requires the reviewed target export/whole-archive binding and seals the fill helper. wrong binding/receipt checks fail; the documented old build fails before. |\n| 2. adoption profile not exercised | real job.main constructs actions 0/1 from packaged 9.json. real 7.py rehearsal produces memory.json with 12 gib cache allowance. stub workers produce five verified ordinary journals. the old cpu-proof helper fails the allowance test. |\n| 3. unchecked cache-only return | on unpack rejects non-true weights receipts. invalid-value regressions fail before/pass after; real authenticated partial-return unpack rejects an unchecked journal. |\n| 9. readme nits | commands use explicit delivery/source roots; kit pin is a4-only; readme states what bootstrap admission actually checks. |\n\n**step 600: one card, caches only, general/no-requeue.** apply 01–03 to a full a4/src copy and 04–05 to an a4 operator copy. define the local roots using [readme](kit_parity50/readme.md), then build:\n\n```bash\ncuda_visible_devices= nice -n 10 "$read_python" -i -s -b "$ext_source/u0/a19.py" \\\n  --enable-extensions --base-operator "$local/a4" --source-root "$ext_source" \\\n  --export-binding "$step600_binding" --token "$package_token" --out "$local/step600"\n```\n\nthe required binding includes target run/step/object/preparation identities and archive_bytes/archive_sha256. the cpu task has no real step-600 export; its test binding is synthetic. the generic a12 operator build is refused. add --processor-only for the 4 gib processor cache; otherwise the cache allowance is 12 gib. both disable atomic journals and sharding. a4\'s fixed schedule remains 636 items; changing it requires a separately reviewed operator/proof.\n\nuse the generated fill helper, regenerate cpu proof through package/a/5.py, and retain the generated tower_sequence.py beside unpack_return.py. exact fill/proof commands are in readme. require read_cache_bytes in memory/cpu.json, along with payload/plan/inputs/operator binding and fits=true. the unchanged 0.py admission does not independently require that field. cache-only returns retain ordinary journals; on unpack refuses unchecked weights even on partial returns.\n\nbefore adoption, require **zero answer/trace byte differences**, useful cache hits, net worker_wall_seconds savings, and full-process host/gpu/envelope headroom. on\'s eager sam construction and boundary hashing need the gpu gate. the sample overstates reuse. keep models frozen; persistent raw writes fail at boundaries, while restored-between-boundary writes are unsupported. hard kills can require fresh journals. validate persistent-storage requeue before any preempt/sharded use. stage source trees as archives and run the kit with --public. no launch ran; preserve step-400 deliveries.\n\nexact commands, outputs, citations and limits: [report](report.md). patch/base pins: [manifest](patches/manifest.json).\n'

----------------------------------------------------------------------
Ran 7 tests in 5.214s

FAILED (failures=11)
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
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 288, in test_f1_step600_package_preserves_a4_contract_and_binding
    self.assertEqual(cfg.get(key),old[key],key)
AssertionError: None != 'candidates_argmax' : stage1_select_rule

======================================================================
FAIL: test_f2_step600_real_job_and_rehearsal_memory (__main__.Round4Tests.test_f2_step600_real_job_and_rehearsal_memory)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 331, in test_f2_step600_real_job_and_rehearsal_memory
    self.assertEqual(result.returncode,0,str(root)+'\n'+result.stdout+result.stderr+logs+'\n'+'\n'.join(p.read_text() for p in (root/'job/sandbox/r').glob('FAILED.json')))
AssertionError: 1 != 0 : /scratch/jjyeung/orch_n30/so_read/work/test-artifacts/5588e151179541b0befb8b4b741b9eb0
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 424, in <module>
    elif len(sys.argv)>1 and sys.argv[1]=='--control':control_child(Path(sys.argv[2]),Path(sys.argv[3]),sys.argv[4])
                                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 272, in control_child
    node.main()
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/5588e151179541b0befb8b4b741b9eb0/built/package/a/5.py", line 147, in main
    raise ValueError('Prepared default settings differ')
ValueError: Prepared default settings differ
PASS action 0 rehearsal False



======================================================================
FAIL: test_f3_cache_only_return_refuses_unverified_journals (__main__.Round4Tests.test_f3_cache_only_return_refuses_unverified_journals) (verified=False)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 400, in test_f3_cache_only_return_refuses_unverified_journals
    with self.subTest(verified=value),self.assertRaisesRegex(ValueError,'Unverified weight journal'):validate()
                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f3_cache_only_return_refuses_unverified_journals (__main__.Round4Tests.test_f3_cache_only_return_refuses_unverified_journals) (verified=None)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 400, in test_f3_cache_only_return_refuses_unverified_journals
    with self.subTest(verified=value),self.assertRaisesRegex(ValueError,'Unverified weight journal'):validate()
                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f3_cache_only_return_refuses_unverified_journals (__main__.Round4Tests.test_f3_cache_only_return_refuses_unverified_journals) (verified=0)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 400, in test_f3_cache_only_return_refuses_unverified_journals
    with self.subTest(verified=value),self.assertRaisesRegex(ValueError,'Unverified weight journal'):validate()
                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f3_cache_only_return_refuses_unverified_journals (__main__.Round4Tests.test_f3_cache_only_return_refuses_unverified_journals) (verified=1)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 400, in test_f3_cache_only_return_refuses_unverified_journals
    with self.subTest(verified=value),self.assertRaisesRegex(ValueError,'Unverified weight journal'):validate()
                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f3_cache_only_return_refuses_unverified_journals (__main__.Round4Tests.test_f3_cache_only_return_refuses_unverified_journals) (verified='true')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 400, in test_f3_cache_only_return_refuses_unverified_journals
    with self.subTest(verified=value),self.assertRaisesRegex(ValueError,'Unverified weight journal'):validate()
                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 4 tests in 10.448s

FAILED (failures=7, skipped=1)
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
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 333, in test_f2_step600_real_job_and_rehearsal_memory
    self.assertEqual(proof['memory'].get('read_cache_bytes'),12*1024**3)
AssertionError: None != 12884901888

----------------------------------------------------------------------
Ran 1 test in 10.796s

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
AssertionError: 'H10_SETTINGS' unexpectedly found in {'CUDA_VISIBLE_DEVICES': 'fixture', 'H10_SETTINGS': '/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/36f442f49135449286ee9bfb46e878b8/u0.json'}

----------------------------------------------------------------------
Ran 1 test in 0.841s

FAILED (failures=1)
```

The final seal is checked by `bash work/cpu.sh work/integrity5.py`. Its exact output is in [integrity5.txt](checks/integrity5.txt); [FINAL_INTEGRITY.json](checks/FINAL_INTEGRITY.json) pins the report, NOTE, README, framework evidence, MANIFEST, patches, operations and checks. The integrity output remains external to avoid a report/hash cycle.
