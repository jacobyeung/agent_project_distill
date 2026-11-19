VERDICT: DONE The round-4 packaging, adoption-profile and return-validation fixes pass CPU checks; GPU adoption remains gated.

Measured validation: **95 workspace tests pass**, including every prior suite. All requested fail-before regressions reproduce. **14 tests pass from a fresh patch application**: the OFF, round-4 integration and comparator suites. Every applied file matches the tested workspace bytes; every original reader file remains unchanged. Five patches apply with zero fuzz.

The A4 build preserves its reviewed run keys, Python-3.6-compatible submit helper and export-admission code. It requires a target export binding, including the whole-archive size/hash. Its CPU fixture builds a synthetic step-600 cache-only package, runs A4's real CPU-proof helper, bootstrap and job.main, completes 636 stub items, and verifies five ordinary weight journals. No real step-600 export was supplied or claimed.

Measured environment: torch 2.11.0+cpu, transformers 5.12.1, 8 torch threads, CUDA hidden. The suite driver's maximum child RSS was 400,351,232 bytes. The CPU benchmark's peak RSS was 1,310,048,256 bytes. The workspace occupies 2,865,156,832 bytes including directory metadata, below 3,000,000,000 bytes. All compute used nice -n 10 and the required thread/environment limits. No Git, SSH, scheduler, GPU, paid API, deletion or input-tree edit ran. Network access read official library documentation only.

The untouched delivery backup is [out_round4](../out_round4/). Work began at Thu Nov 19 13:02:02 UTC 2026; the deadline is 14:32:02 UTC. This report was generated at Thu Nov 19 13:18:07 UTC 2026.

## Review round 4: finding -> fix -> test

| Finding | Fix | Evidence |
|---|---|---|
| 1 MEDIUM: step-600 build drops A4 run keys, export binding and compatible helper | The explicit a19 builder uses cont_ops' build_r1-style post-processing over A4's authenticated payload. It retains 8.py, admission/vendor bytes and every A4 run key, installs the ON overlays, and seals the reviewed target binding into 9.json. It retargets A4's fill-helper object/size/hash constants and rebuilds every affected pin. The incomplete a12 operator route is refused. | test_f1 checks target binding, payload pins, A4 keys and helper bytes/compatibility. The real admission rejects changed run, step, member, lineage, object, config, archive or preparation hashes. The fill helper rejects changed whole-tar identity/receipt. The documented reviewed build fails this test on the missing stage1 rule. |
| 2 LOW: hand-built action config and generic profile hide adoption failures | A4's CPU-proof helper propagates read_extensions into the real 7.py rehearsal. The test reads packaged 9.json as-is and runs real job.main to construct a/0.json and a/1.json; it only translates namespace paths and stubs storage/device/model work. | test_f2 runs real preparation, rehearsal, bootstrap admission, operator and runner/action-2 dispatch. MEMORY.json contains 12,884,901,888 cache bytes. All 636 items complete in five ordinary journals, each with verified=true; no atomic commit store or canonical merge exists. The old route fails preparation. Independently, the original CPU-proof helper fails with None != 12884901888. |
| 3 LOW: cache-only return accepts unchecked weights | With read_extensions=true, unpack_return refuses an existing WEIGHTS.json unless verified is exactly JSON true. OFF retains its existing path. | The same test accepts missing/true receipts, refuses false/null/0/1/string values, and retains OFF behavior. All five invalid-value assertions fail on reviewed code. The real authenticated unpack entry accepts a verified partial return and rejects an unverified partial return. |
| 9 INFO: non-delivery paths, B5 base claim, proof-field wording | README uses explicit delivery/source/scratch variables; the kit is A4-only. It distinguishes the generated cache-memory proof from unchanged bootstrap admission. | The CPU integration uses the delivered Python tools and asserts the generated cache allowance. The kit authenticates complete A4 inventories; B5 applicability is limited to the separate patch-application check. |

The requested findings are fixed. The new builder adapts the reviewed packaging logic because build_r1.py itself hard-codes step-200 bindings and output paths outside this writable workspace. It preserves the inspected A4 package instead of rebuilding unported helpers. Binding generation and production staging remain owner operations; the builder cannot manufacture review evidence.

The round-4 before output contains seven assertion failures across the three required regressions: two packaging/profile failures and five weight-state subtests. The one skipped test is the new builder's OFF/processor-only interface, which does not exist in the reviewed baseline. A separate old-node-helper run fails the memory-field assertion. Exact outputs are included below.

## Delivered build and adoption contract

**Step 600 is a single-card, cache-only candidate on general with no requeue, after the GPU gate.** Apply reader patches 01–03 to the full A4/src copy and operator patches 04–05 to an A4 directory copy. Follow the exact preparation/build/fill/proof commands in [README.md](kit_parity50/README.md). The explicit build command is:

```bash
CUDA_VISIBLE_DEVICES= nice -n 10 "$READ_PYTHON" -I -s -B "$EXT_SOURCE/u0/a19.py" \
  --enable-extensions --base-operator "$LOCAL/a4" --source-root "$EXT_SOURCE" \
  --export-binding "$STEP600_BINDING" --token "$PACKAGE_TOKEN" --out "$LOCAL/step600"
```

The binding must include run, step, member directory, lineage, object, configuration/base/frame identities, preparation hashes and whole-archive size/hash. Add --processor-only for a 4 GiB processor cache; the full cache profile uses 12 GiB. Both profiles disable atomic journals and scene sharding. The builder copies A4's numeric CPU/fill/fetch helpers, keeps a/ private, invalidates old input/export receipts, and carries no old CPU proof or submission ledger. Its output includes the exact tower_sequence.py that the unpacker hashes.

A4's descriptors still bind 636 items. A different item set requires a separately reviewed schedule and proof. No multi-card A4 operator is delivered. The two/four-shard estimates below require one and are not step-600 launch instructions. Real persistent-storage requeue remains required before any preempt/sharded adoption.

The actual CPU proof comes from a/5.py invoking 7.py with rehearsal and measure_memory. It must bind the new payload, plan, inputs and operator; require both bundle/entry checks and fits=true. Inspect read_cache_bytes: 12,884,901,888 for all caches or 4,294,967,296 for processor-only. The unchanged bootstrap verifies proof binding and fits, but does not independently require that field. The fixed CPU helper emits it and the regression checks it.

Cache-only returns use ordinary per-type journals. The ON unpacker refuses unverified weight receipts even in an authenticated partial return. The separate generic atomic validation path retains its nested archive at metadata/reads/0/metadata/u0/answer_trace_return.tgz.

## Equality and mutation limits

The ordinary reader imports no extension and parses no new settings. The OFF fixture compares complete output files/stdout, including source hashes and controlled timing fields, against the original without exclusions. [OFF_BYTES.json](checks/OFF_BYTES.json) records the byte proof. The operator memory/return additions are guarded by read_extensions, whose default is OFF.

The 50-item CPU fixture compares original/OFF/processor+vision/processor-only answers and traces exactly with stub generation. Separate SAM fixtures check cached values, geometry recomputation and mutation rejection. Production adoption requires the unrun ORIGINAL/OFF/OFF_REPEAT/ON/journal/sharded GPU gates, useful hits in every enabled cache, and **zero answer/trace byte differences**. Only clocks and explicit telemetry are excluded; equal scores cannot hide changed answers. No batching implementation or numeric tolerance is delivered.

Calls check every parameter/buffer identity, pointer and version. Full hashes run at installation and type boundaries. Persistent .data/NumPy/raw-storage writes fail at boundaries; a raw write restored before the next boundary can evade detection. Private tensor attributes and arbitrary non-tensor module state are outside the guard's coverage. Models must remain frozen. A hard worker death can leave WEIGHTS.json false; graceful stops validate it. Processor-only runs install no weight guard.

ON eagerly constructs SAM outside inference mode; OFF constructs it lazily inside inference mode. This changes load timing and potentially RNG use. Only the GPU byte gate can clear the difference. Per-item timing omits installation and boundary costs; judge net performance using RUN.json worker_wall_seconds. The sample overstates reuse: its ten distance items share one clip, while A4 has 150 distance items over 60 clips (review finding 7). No production saving is credited.

## Measured CPU guard overhead

Each stub has bf16 parameters of shape 2048×1024 and one 1024-element bf16 buffer per tensor, with 128 or 256 child modules. Forward returns a 32-element tensor without model-sized matrix work. Each implementation runs a miss and warm hit, then seven timed hits; the boundary figure is the median of three hashes. These are CPU validation/cache costs, not GPU speedups.

| Parameters | Parameter/buffer tensors | Weight+buffer bytes | Reviewed per-call hash ms | Boundary-guard ms/call | Install s | Boundary s |
|---:|---:|---:|---:|---:|---:|---:|
| 268435456 | 128 / 128 | 537133056 | 344.500 | 25.861 | 0.340 | 0.338 |
| 536870912 | 256 / 256 | 1074266112 | 700.883 | 51.622 | 0.678 | 0.704 |

Exact samples and environment: [CACHE_COST3.json](checks/CACHE_COST3.json). The filename retains its test lineage; this task reran the benchmark. Actual H100 hash/copy/synchronization costs and full-process host/GPU memory remain unmeasured.

## Measured profile and forecast

The profile was recomputed from the supplied journals. These are existing step-200 GPU measurements, not new GPU runs. Exact recomputation output is in [profile_rerun.txt](checks/profile_rerun.txt); [profile.json](profile.json) records each source path and SHA256.

| Package/type | Items | Mean s/item | Median | p90 | Tokens/item: total / ordinary | Calls/item | G3T s/item | Factory load s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A4/camera_displacement | 150 | 9.553 | 7.641 | 15.357 | 164.05 / 124.05 | 1.00 | 2.000 | 0 (reused) |
| A4/camera_movement_direction | 150 | 9.045 | 8.963 | 9.604 | 203.61 / 163.60 | 1.00 | 0.055 | 0 (reused) |
| A4/camera_rotation | 150 | 5.088 | 5.008 | 5.266 | 89.93 / 79.02 | 1.00 | 0.103 | 0 (reused) |
| A4/object_abs_distance | 150 | 23.600 | 18.275 | 29.181 | 354.53 / 239.33 | 1.76 | 1.998 | 75.446 |
| A4/room_size_estimation | 36 | 3.667 | 3.642 | 3.856 | 65.25 / 65.25 | 0.00 | 0 (no call) | 0 (reused) |
| B5/room_size_estimation | 134 | 3.942 | 3.524 | 4.505 | 66.66 / 66.66 | 0.00 | 0 (no call) | 78.961 |

Total tokens include forced tool responses and budget tokens. Factory loading covers processor/model restore/setup, not deferred tower loading. A4 reuses one generator across five types. G3T timings cover lookup/restore or fresh execution; they do not measure SAM or total tower time. SAM has no independent timer.

A4 records 7,351.824 seconds from start to exit: 7,224.888 in items, 75.446 in loading, 1.729 in journal/control windows, and 49.761 outside type timers. B5 records 645.735 seconds, including 528.164 in items and 78.961 in loading. Residual wall time does not establish GPU idle time.

The distance profile retains one unexplained 648.397-second, 2,056-token item. There are 88 routed and 62 direct distance items. Source inspection implies 88 SAM encodes and 176 raw-name detections; those call counts are inferred. Camera items each serve one move/turn call; room items serve none.

A4 already records 461 G3T memo hits and 77 misses, retaining 128,553,354 payload bytes. This saving cannot be counted again. The new caches store video processor outputs, visual outputs and raw SAM values. They do not store question text, language/KV/recurrent state, own-depth scale, geometry or full tool responses.

**Estimated forecast:** 580 × 23.599762 / shards + 75.446133 + 49.761372 seconds gives 13,813.069 / 6,969.138 / 3,547.173 seconds for one/two/four balanced simultaneous shards. Whole scenes stay together, so the largest shard sets elapsed time. The fixed 50-item sample stresses reuse and does not establish representative throughput.



## Framework evidence

The implementation's framework contract and installed file:line citations are in [FRAMEWORK_EVIDENCE.md](FRAMEWORK_EVIDENCE.md). This task reread TensorImpl.h:291–305, 413–418 and 2050–2054, autograd/graph.py:242–258 and optim/sgd.py:378–380 under `/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/`. Tracked in-place operations increment counters; detach shares them; .data/storage replacement need not share/increment them. The pointer guard catches new storage; boundary hashes cover persistent untracked writes. Inference tensors lack counters and are refused for model caching.

The official [increment_version documentation](https://docs.pytorch.org/docs/2.11/generated/torch.autograd.graph.increment_version.html) and [inference_mode reference](https://docs.pytorch.org/docs/2.11/generated/torch.autograd.grad_mode.inference_mode.html) were checked on 2026-11-19. [TORCH_VERSIONS3.json](checks/TORCH_VERSIONS3.json) contains the rerun operation probes and installed-source hashes. No new framework assumption was needed for the packaging/return fixes.

## Earlier required review sections

### Review round 1: finding -> fix -> test

Typed keys, complete parity schemas, original/OFF provenance, frozen identity, lock-held recovery, opaque transport and bounded storage retain passing tests. All eight reviewed-baseline regressions fail as expected.

### Review round 2: finding -> fix -> test

Isolated entry, path policy, bounded array retries, pinned overlays, SAM capacity, deadline counts, lock waits, cache bypass accounting, source-root checks and worker setup retain passing tests. All thirteen reviewed-baseline regressions reproduce, including both CLI variants.

### Review round 3: finding -> fix -> test

Install/type-boundary hashes and cheap fatal live guards, processor-only mode, operator memory/overlay dispatch, full base authentication, behavioral lock/worker regressions and the OFF import guard retain passing tests. The generic operator test checks the atomic nested merge; the round-4 test checks the actual cache-only adoption profile. The OFF guard now includes a0–a19. All round-3 failing baselines reproduce.

These audit sections retain finding history only because the dispatch explicitly requires it. Other sections state the delivered behavior and current evidence.

## Patches and measured resource bounds

A4 base SHA256: `813fe4c57b2deed4bd731dd1e3493b6b0bed8d31e7bff92ff112cf5c9df823c3` over 927 files. B5 archive SHA256: `ac2e259025d6a821aa5eb13e236f0635bd970313859086fc2f3ce3276647f2f0`. The B5 check proves reader-patch applicability, not kit compatibility. [MANIFEST.json](patches/MANIFEST.json) binds all patches, file inventories, operator inputs and delivery bytes.

| Patch | Bytes | SHA256 |
|---|---:|---|
| [01_bounded_read_caches.diff](patches/01_bounded_read_caches.diff) | 90430 | `f7ee47e3583483b998f5fed172c86ea64399c1aa7f24562431568f3efe4b1b0b` |
| [02_atomic_scene_shards.diff](patches/02_atomic_scene_shards.diff) | 218841 | `5f76cf79e29471138161e476daf3920ec2bcbf751586fc47528fbd7388530cfa` |
| [03_production_integration.diff](patches/03_production_integration.diff) | 138249 | `cd2704b68890a14d1ec9280951c3066b6b088f30b349730888a2b6e407594460` |
| [04_operator_cache_bound.diff](patches/04_operator_cache_bound.diff) | 2723 | `0d3bdc2d943554cd525627466d2d71f30881884e76df95204ede6c1accdb9061` |
| [05_operator_return_and_proof.diff](patches/05_operator_return_and_proof.diff) | 2601 | `bfab6b5487553bbad67b5860ec54dc20492ad878b633a493ba091cc5e65d1949` |

Patches 01–03 are additive under src/u0. Patches 04–05 apply from the A4 operator directory: tower_sequence.py, unpack_return.py and package/a/5.py. The bootstrap remains byte-identical to A4. Tests ship in patch 03. The explicit A4 builder and fixture are new; the generic a12 operator route rejects incomplete builds.

All workspace suites were rerun once against final source bytes. To remain below 3 GB without deleting files, fresh-application testing repeats only OFF, round-4 integration and comparator suites. Every other applied file is authenticated byte-for-byte against the already-tested source. This avoids a redundant full fixture corpus; it does not skip a requested test.

The original timing profile was recomputed from supplied journals. The cache caps are configured cache-owned storage bounds, not measured process peaks. The small allocation receipt remains in MEMORY.json; its 3 GiB capacity regression simulates accounting without allocating that tensor. Preserve full-process host/GPU headroom.

## What could go wrong and how to notice

| Risk | Detection/action |
|---|---|
| Wrong export, archive, preparation or stale helper | Required target binding, sealed fill constants, payload/plan/package pins and real export-admission checks refuse mismatches. Never reuse the test binding. |
| A4 proof omits the ON memory allowance | Generate proof through the patched a/5.py and inspect read_cache_bytes; unchanged bootstrap admission alone is insufficient for this field. |
| Untracked weight mutation or hard worker death | Boundary checks leave false receipts; ON unpack/resume/merge/comparison refuse unchecked journals. Use fresh output after an unverified hard kill. |
| GPU kernels, layouts, eager SAM load or RNG affect bytes | Require the complete zero-tolerance GPU gate before adoption. |
| Hashes/copies/cache misses erase savings | Require useful hits and lower complete worker wall time; credit no savings from the CPU ratios. |
| Cache allowance understates whole-process memory | Measure real host/GPU peaks; cache caps do not cover model/caller working storage. |
| Real namespace, transport, return capacity or requeue differs from stubs | Exercise production restore/storage/envelope checks; keep general/no-requeue until persistent-storage requeue passes. |

## Not done

No real step-600 binding/export build, real weight restore, production bwrap/storage/transport, GPU parity/performance/memory, scheduler action, upload, return publication or persistent-storage requeue ran. No multi-card operator or batching is delivered. The array policy remains approved=false. The synthetic CPU fixture is not a staging package or production proof.

No delivered CPU suite or single-GPU parity pass requires a local OS socket; StageOneSocket is a Python callback. Socket-backed integration remains unrun. These limits do not waive the zero-tolerance GPU gate.

## Commands and exact outputs

Commands below ran from `/scratch/jjyeung/orch_n30/so_read`. `work/cpu.sh` exports CUDA_VISIBLE_DEVICES="", OMP/MKL/OPENBLAS threads=8, TOKENIZERS_PARALLELISM=false, PYTHONDONTWRITEBYTECODE=1 and scratch caches, then executes nice -n 10 with the required Python -I -s -B. Tests call torch.set_num_threads(8). Child commands inherit that environment and priority. Workspace tests also receive READ_INPUT_SRC and READ_TEST_TMP; fresh-application tests additionally receive READ_OPERATOR_SOURCE and READ_OPERATOR4_SOURCE from MANIFEST's verification root.

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
        "data_ptr": 124198080,
        "object_id": 140481349575504,
        "version": 1
      },
      "before": {
        "data_ptr": 124198080,
        "object_id": 140481349575504,
        "version": 0
      },
      "object_changed": false,
      "operation": "parameter.add_",
      "pointer_changed": false,
      "version_changed": true
    },
    {
      "after": {
        "data_ptr": 124208576,
        "object_id": 140481349575824,
        "version": 1
      },
      "before": {
        "data_ptr": 124208576,
        "object_id": 140481349575824,
        "version": 0
      },
      "object_changed": false,
      "operation": "detach().add_",
      "pointer_changed": false,
      "version_changed": true
    },
    {
      "after": {
        "data_ptr": 124209280,
        "object_id": 140481349575504,
        "version": 0
      },
      "before": {
        "data_ptr": 124209280,
        "object_id": 140481349575504,
        "version": 0
      },
      "object_changed": false,
      "operation": "parameter.data.add_",
      "pointer_changed": false,
      "version_changed": false
    },
    {
      "after": {
        "data_ptr": 124211904,
        "object_id": 140481349575824,
        "version": 0
      },
      "before": {
        "data_ptr": 124209792,
        "object_id": 140481349575824,
        "version": 0
      },
      "object_changed": false,
      "operation": "parameter.data assignment to cloned storage",
      "pointer_changed": true,
      "version_changed": false
    },
    {
      "after": {
        "data_ptr": 124212288,
        "object_id": 140481349575504,
        "version": 0
      },
      "before": {
        "data_ptr": 124212288,
        "object_id": 140481349575504,
        "version": 0
      },
      "object_changed": false,
      "operation": "parameter.data assignment to same storage",
      "pointer_changed": false,
      "version_changed": false
    },
    {
      "after": {
        "data_ptr": 124212416,
        "object_id": 140481349575824,
        "version": 0
      },
      "before": {
        "data_ptr": 124212416,
        "object_id": 140481349575824,
        "version": 0
      },
      "object_changed": false,
      "operation": "numpy raw storage write",
      "pointer_changed": false,
      "version_changed": false
    },
    {
      "after": {
        "data_ptr": 124212608,
        "object_id": 140481349575504,
        "version": 1
      },
      "before": {
        "data_ptr": 124212608,
        "object_id": 140481349575504,
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
      "after_install_seconds": 0.33991962391883135,
      "after_per_call": {
        "max_seconds": 0.025952373165637255,
        "median_seconds": 0.025860584806650877,
        "min_seconds": 0.025839413981884718,
        "seconds": [
          0.02595195220783353,
          0.025839413981884718,
          0.025952373165637255,
          0.02586036454886198,
          0.025860584806650877,
          0.02592034498229623,
          0.02585511701181531
        ]
      },
      "before_install_seconds": 3.860797733068466e-05,
      "before_per_call": {
        "max_seconds": 0.36572772124782205,
        "median_seconds": 0.3445000839419663,
        "min_seconds": 0.33938317000865936,
        "seconds": [
          0.36572772124782205,
          0.34142393013462424,
          0.33938317000865936,
          0.3558313278481364,
          0.3398910607211292,
          0.36043597431853414,
          0.3445000839419663
        ]
      },
      "blocks": 128,
      "boundary": {
        "max_seconds": 0.3378346972167492,
        "median_seconds": 0.33765744091942906,
        "min_seconds": 0.337288087233901,
        "seconds": [
          0.337288087233901,
          0.33765744091942906,
          0.3378346972167492
        ]
      },
      "buffer_shape": [
        1024
      ],
      "buffer_tensors": 128,
      "dtype": "bfloat16",
      "median_speed_ratio": 13.32143439592159,
      "parameter_count": 268435456,
      "parameter_shape": [
        2048,
        1024
      ],
      "parameter_tensors": 128,
      "weight_and_buffer_bytes": 537133056
    },
    {
      "after_install_seconds": 0.6781246168538928,
      "after_per_call": {
        "max_seconds": 0.05186061002314091,
        "median_seconds": 0.0516222920268774,
        "min_seconds": 0.051589532755315304,
        "seconds": [
          0.05165274813771248,
          0.0516222920268774,
          0.05186061002314091,
          0.051637225318700075,
          0.051589532755315304,
          0.05159824574366212,
          0.051619757898151875
        ]
      },
      "before_install_seconds": 3.438116982579231e-05,
      "before_per_call": {
        "max_seconds": 0.7308662869036198,
        "median_seconds": 0.7008826076053083,
        "min_seconds": 0.6722905361093581,
        "seconds": [
          0.7308662869036198,
          0.7116063921712339,
          0.6722905361093581,
          0.6914676991291344,
          0.7008826076053083,
          0.6997527829371393,
          0.7017147559672594
        ]
      },
      "blocks": 256,
      "boundary": {
        "max_seconds": 0.7068606740795076,
        "median_seconds": 0.7040596441365778,
        "min_seconds": 0.6973642609082162,
        "seconds": [
          0.6973642609082162,
          0.7068606740795076,
          0.7040596441365778
        ]
      },
      "buffer_shape": [
        1024
      ],
      "buffer_tensors": 256,
      "dtype": "bfloat16",
      "median_speed_ratio": 13.57713073337368,
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
  "max_rss_bytes": 1310048256,
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
round4: CPU step-600 fixture: /scratch/jjyeung/orch_n30/so_read/work/test-artifacts/fb80d69ec1794efd861fd1ff4b48446b
kit: OK
kit_launch: OK
PASS: all 8 round-1 regressions fail against the round-1 reviewed implementation.
PASS: all 13 round-2 regressions fail against the round-2 reviewed implementation (14 failures including both CLI variants).
PASS: round3_before reproduces FAILED (failures=15).
PASS: operator3_before reproduces FAILED (failures=2).
PASS: lock3_before reproduces FAILED (failures=2).
PASS: round4_before reproduces FAILED (failures=7, skipped=1).
PASS: node4_before reproduces FAILED (failures=1).
PASS: f16_behavior_before reproduces FAILED (failures=1).
PASS: Python syntax, shell syntax, and default-off execution guards.
{"cuda_visible_devices": "", "max_child_rss_bytes": 400351232, "torch": "2.11.0+cpu", "torch_threads": 8, "transformers": "5.12.1", "workspace_bytes": 2638758455}
```

```bash
bash work/cpu.sh work/build_patches.py
```

Exact output:

```text
PASS: 3 additive reader diffs (33 files) plus 2 default-OFF A4 operator diffs; zero-fuzz application; unchanged original reader hash trees.
PASS: OFF, round-4 integration and comparator suites pass from the fresh applied A4 tree; both complete 927-file base inventories authenticate.
Applied verification root: /scratch/jjyeung/orch_n30/so_read/work/apply-round4/74e598e555bf413f91a03d7f9b9825af
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_read_cache.py
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
Ran 15 tests in 2.298s

OK
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_read_journal.py
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
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_off.py
```

Exact output:

```text
test_every_output_byte_and_source_hash_matches_original (__main__.OffContractTests.test_every_output_byte_and_source_hash_matches_original) ... ok

----------------------------------------------------------------------
Ran 1 test in 4.090s

OK
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_public.py
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
Ran 7 tests in 0.003s

OK
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round1.py
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
Ran 17 tests in 3.124s

OK
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round2.py
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
Ran 13 tests in 3.498s

OK
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round3.py
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
Ran 9 tests in 1.462s

OK
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_operator_round3.py
```

Exact output:

```text
test_f2_a12_payload_through_a4_actions_and_nested_return (__main__.OperatorTests.test_f2_a12_payload_through_a4_actions_and_nested_return) ... ok
test_f2_operator_memory_bound_includes_cache_only_when_enabled (__main__.OperatorTests.test_f2_operator_memory_bound_includes_cache_only_when_enabled) ... ok

----------------------------------------------------------------------
Ran 2 tests in 7.936s

OK
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_lock_round3.py
```

Exact output:

```text
test_deadline_recovery_keeps_writer_lock (lock_behavior.RunnerTests.test_deadline_recovery_keeps_writer_lock) ... ok
test_type_deadline_recovery_holds_writer_lock (__main__.TypeLockTests.test_type_deadline_recovery_holds_writer_lock) ... ok

----------------------------------------------------------------------
Ran 2 tests in 0.013s

OK
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py
```

Exact output:

```text
test_f1_step600_package_preserves_a4_contract_and_binding (__main__.Round4Tests.test_f1_step600_package_preserves_a4_contract_and_binding) ... ok
test_f2_step600_real_job_and_rehearsal_memory (__main__.Round4Tests.test_f2_step600_real_job_and_rehearsal_memory) ... ok
test_f3_cache_only_return_refuses_unverified_journals (__main__.Round4Tests.test_f3_cache_only_return_refuses_unverified_journals) ... ok
test_f9_off_builder_guard_and_processor_only (__main__.Round4Tests.test_f9_off_builder_guard_and_processor_only) ... ok

----------------------------------------------------------------------
Ran 4 tests in 18.261s

OK
{"output": "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/fb80d69ec1794efd861fd1ff4b48446b/verified-return", "complete": false, "status": "FAILED", "sha256": "13a4865436eaaeb5c39f0b97476d327b8f4e15ae7417256f961fb6187def9d35"}
CPU step-600 fixture: /scratch/jjyeung/orch_n30/so_read/work/test-artifacts/fb80d69ec1794efd861fd1ff4b48446b
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/out/kit_parity50/test_compare.py
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
Ran 9 tests in 0.268s

OK
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/out/kit_parity50/test_run.py
```

Exact output:

```text
test_durable_scene_comparison_requires_explicit_on_arm (__main__.LaunchTests.test_durable_scene_comparison_requires_explicit_on_arm) ... ok
test_original_and_off_do_not_opt_in_to_journaling_or_sharding (__main__.LaunchTests.test_original_and_off_do_not_opt_in_to_journaling_or_sharding) ... ok
test_stage_kit_uses_opaque_names_token_metadata_and_authenticated_sample_bytes (__main__.LaunchTests.test_stage_kit_uses_opaque_names_token_metadata_and_authenticated_sample_bytes) ... ok

----------------------------------------------------------------------
Ran 3 tests in 0.052s

OK
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/apply-round4/74e598e555bf413f91a03d7f9b9825af/src/u0/tests/test_off.py
```

Exact output:

```text
test_every_output_byte_and_source_hash_matches_original (__main__.OffContractTests.test_every_output_byte_and_source_hash_matches_original) ... ok

----------------------------------------------------------------------
Ran 1 test in 3.940s

OK
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/apply-round4/74e598e555bf413f91a03d7f9b9825af/src/u0/tests/test_round4.py
```

Exact output:

```text
test_f1_step600_package_preserves_a4_contract_and_binding (__main__.Round4Tests.test_f1_step600_package_preserves_a4_contract_and_binding) ... ok
test_f2_step600_real_job_and_rehearsal_memory (__main__.Round4Tests.test_f2_step600_real_job_and_rehearsal_memory) ... ok
test_f3_cache_only_return_refuses_unverified_journals (__main__.Round4Tests.test_f3_cache_only_return_refuses_unverified_journals) ... ok
test_f9_off_builder_guard_and_processor_only (__main__.Round4Tests.test_f9_off_builder_guard_and_processor_only) ... ok

----------------------------------------------------------------------
Ran 4 tests in 18.162s

OK
{"output": "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/08f1fb32a0704c15a3dd5b1381abf0cd/verified-return", "complete": false, "status": "FAILED", "sha256": "4d8545403efc9f3d8d193be516a6a84481b949e01a5e80014ddb7546497ba743"}
CPU step-600 fixture: /scratch/jjyeung/orch_n30/so_read/work/test-artifacts/08f1fb32a0704c15a3dd5b1381abf0cd
```

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /scratch/jjyeung/orch_n30/so_read/work/apply-round4/74e598e555bf413f91a03d7f9b9825af/src/u0/tests/test_compare.py
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
Ran 9 tests in 0.269s

OK
```

```bash
READ_REVIEW_BEFORE=1 bash work/round3_env.sh work/src/u0/tests/test_round1.py
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
Ran 8 tests in 0.029s

FAILED (failures=8)
```

```bash
READ_ROUND2_BEFORE=1 bash work/round3_env.sh work/src/u0/tests/test_round2.py
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
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/8e126417c8974ddfbe4623027d04a9dc/u0/a8.py", line 65, in <module>
    raise SystemExit(main())
                     ^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/8e126417c8974ddfbe4623027d04a9dc/u0/a8.py", line 61, in main
    return launch(rest)
           ^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/8e126417c8974ddfbe4623027d04a9dc/u0/a4.py", line 2, in main
    from a8 import source_hash
ModuleNotFoundError: No module named 'a8'


======================================================================
FAIL: test_f1_actual_isolated_script_plain_and_opaque (__main__.Round2Tests.test_f1_actual_isolated_script_plain_and_opaque) (opaque=True)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round2.py", line 67, in test_f1_actual_isolated_script_plain_and_opaque
    self.assertEqual(result.returncode,0,result.stdout+result.stderr)
AssertionError: 1 != 0 : Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/cb4baaf1637841509d007e25a4994c99/u0/a8.py", line 65, in <module>
    raise SystemExit(main())
                     ^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/cb4baaf1637841509d007e25a4994c99/u0/a8.py", line 56, in main
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
Ran 13 tests in 0.179s

FAILED (failures=13, errors=1)
```

```bash
READ_ROUND3_BEFORE=1 bash work/round3_env.sh work/src/u0/tests/test_round3.py
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
AssertionError: 140430406550224 unexpectedly found in {140430406550224, 140430406550384} : Per-call weight hashing

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
Ran 9 tests in 0.714s

FAILED (failures=15)
```

```bash
READ_ROUND3_BEFORE=1 bash work/round3_env.sh work/src/u0/tests/test_operator_round3.py
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
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/5f9f0bda53874345813b2143b246b8aa/0.py", line 44, in main
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
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/5f9f0bda53874345813b2143b246b8aa/0.py", line 18, in dispatch
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
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/5f9f0bda53874345813b2143b246b8aa/7.py", line 139, in main
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
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/5f9f0bda53874345813b2143b246b8aa/7.py", line 87, in run
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
Ran 2 tests in 7.099s

FAILED (failures=2)
```

```bash
READ_LOCK_BEFORE=1 bash work/round3_env.sh work/src/u0/tests/test_lock_round3.py
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
Ran 2 tests in 0.010s

FAILED (failures=2)
```

```bash
READ_F16_BEFORE=1 bash work/round3_env.sh work/src/u0/tests/test_round3.py Round3Tests.test_f4_worker_uses_settings_argv_without_environment_side_effect
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
AssertionError: 'H10_SETTINGS' unexpectedly found in {'CUDA_VISIBLE_DEVICES': 'fixture', 'H10_SETTINGS': '/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/6907b33bc2ec4bfaa3ac7eb0bffb7e66/u0.json'}

----------------------------------------------------------------------
Ran 1 test in 0.689s

FAILED (failures=1)
```

```bash
READ_ROUND4_BEFORE=1 bash work/round3_env.sh work/src/u0/tests/test_round4.py
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
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 284, in test_f1_step600_package_preserves_a4_contract_and_binding
    self.assertEqual(cfg.get(key),old[key],key)
AssertionError: None != 'candidates_argmax' : stage1_select_rule

======================================================================
FAIL: test_f2_step600_real_job_and_rehearsal_memory (__main__.Round4Tests.test_f2_step600_real_job_and_rehearsal_memory)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 327, in test_f2_step600_real_job_and_rehearsal_memory
    self.assertEqual(result.returncode,0,str(root)+'\n'+result.stdout+result.stderr+logs+'\n'+'\n'.join(p.read_text() for p in (root/'job/sandbox/r').glob('FAILED.json')))
AssertionError: 1 != 0 : /scratch/jjyeung/orch_n30/so_read/work/test-artifacts/f7a35a8ae20c4a3587714e14d6191945
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 420, in <module>
    elif len(sys.argv)>1 and sys.argv[1]=='--control':control_child(Path(sys.argv[2]),Path(sys.argv[3]),sys.argv[4])
                                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 268, in control_child
    node.main()
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/f7a35a8ae20c4a3587714e14d6191945/built/package/a/5.py", line 147, in main
    raise ValueError('Prepared default settings differ')
ValueError: Prepared default settings differ
PASS action 0 rehearsal False



======================================================================
FAIL: test_f3_cache_only_return_refuses_unverified_journals (__main__.Round4Tests.test_f3_cache_only_return_refuses_unverified_journals) (verified=False)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 396, in test_f3_cache_only_return_refuses_unverified_journals
    with self.subTest(verified=value),self.assertRaisesRegex(ValueError,'Unverified weight journal'):validate()
                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f3_cache_only_return_refuses_unverified_journals (__main__.Round4Tests.test_f3_cache_only_return_refuses_unverified_journals) (verified=None)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 396, in test_f3_cache_only_return_refuses_unverified_journals
    with self.subTest(verified=value),self.assertRaisesRegex(ValueError,'Unverified weight journal'):validate()
                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f3_cache_only_return_refuses_unverified_journals (__main__.Round4Tests.test_f3_cache_only_return_refuses_unverified_journals) (verified=0)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 396, in test_f3_cache_only_return_refuses_unverified_journals
    with self.subTest(verified=value),self.assertRaisesRegex(ValueError,'Unverified weight journal'):validate()
                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f3_cache_only_return_refuses_unverified_journals (__main__.Round4Tests.test_f3_cache_only_return_refuses_unverified_journals) (verified=1)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 396, in test_f3_cache_only_return_refuses_unverified_journals
    with self.subTest(verified=value),self.assertRaisesRegex(ValueError,'Unverified weight journal'):validate()
                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_f3_cache_only_return_refuses_unverified_journals (__main__.Round4Tests.test_f3_cache_only_return_refuses_unverified_journals) (verified='true')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 396, in test_f3_cache_only_return_refuses_unverified_journals
    with self.subTest(verified=value),self.assertRaisesRegex(ValueError,'Unverified weight journal'):validate()
                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 4 tests in 7.481s

FAILED (failures=7, skipped=1)
```

```bash
READ_NODE4_BEFORE=1 bash work/round3_env.sh work/src/u0/tests/test_round4.py Round4Tests.test_f2_step600_real_job_and_rehearsal_memory
```

Exact output:

```text
test_f2_step600_real_job_and_rehearsal_memory (__main__.Round4Tests.test_f2_step600_real_job_and_rehearsal_memory) ... FAIL

======================================================================
FAIL: test_f2_step600_real_job_and_rehearsal_memory (__main__.Round4Tests.test_f2_step600_real_job_and_rehearsal_memory)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round4.py", line 329, in test_f2_step600_real_job_and_rehearsal_memory
    self.assertEqual(proof['memory'].get('read_cache_bytes'),12*1024**3)
AssertionError: None != 12884901888

----------------------------------------------------------------------
Ran 1 test in 7.669s

FAILED (failures=1)
```

