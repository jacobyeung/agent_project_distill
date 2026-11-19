VERDICT: DONE The requested round-3 fixes pass CPU verification; GPU adoption remains gated.

Measured validation: **91 workspace tests and 88 fresh-application tests pass**. All prior report suites were rerun, including the eight round-1 and thirteen round-2 failing baselines. The requested round-3 failures reproduce on their reviewed implementations. Three additive reader patches and one default-OFF A4 operator patch apply with zero fuzz. Reader source files and complete ordinary OFF outputs remain byte-identical to the inputs.

Measured CPU cache-hit overhead falls from **356.5 to 25.9 ms** for a 268,435,456-parameter stub, and from **731.2 to 52.6 ms** for a 536,870,912-parameter stub. These measure validation/cache overhead on CPU, not GPU inference speedup. Credit no production saving until the complete GPU gate passes.

Measured resources: torch 2.11.0+cpu, transformers 5.12.1, eight torch threads, CUDA hidden. Peak child RSS in the suite driver was 400,650,240 bytes; the model-sized benchmark peaked at 1,321,455,616 bytes. Workspace size at the suite check was 1,192,848,601 bytes, below 3 GB. Commands use nice -n 10; the benchmark recorded effective niceness 19. No Git, SSH, scheduler, GPU, paid API or input-tree modification ran. Network access read official library documentation only.

The backup is [out_round3](../out_round3/). Work started at Thu Nov 19 12:04:06 UTC 2026; the two-hour deadline is 14:04:06 UTC. Report generated at Thu Nov 19 12:32:38 UTC 2026.

## Review round 3: finding -> fix -> test

| Finding | Fix or disposition | Fail-before / pass-after evidence |
|---|---|---|
| 1 MEDIUM: per-call weight hashing | Hash each module at cache install and at type-journal entry/exit. Check every parameter/buffer id, data_ptr, version, dtype/device/shape/stride and gradient flag per call. Preserve option/execution/input keys. Mutations fail the run through a latched BaseException; they do not become cache misses. Add processor-only settings/build switches. | test_round3.py rejects per-call weight reads, replacement, in-place updates, .data reassignment, persistent .data/NumPy writes, and counterless inference tensors. It verifies boundary failure, resume/merge rejection, and graceful-deadline/public-merge success. The fixed 50-item stub fixture also exercises processor-only and exact bytes. CPU overhead is measured below. |
| 2 MEDIUM: A4 operator path and memory | Build an a12 ON payload and dispatch A4's decoded 0.py/7.py. The patched 7.py activates overlays in its fresh action-1 process. The operator adds read_cache_bytes to its host bound only with read_extensions enabled. Optional builder arguments package the authenticated A4 bootstrap/sequence. | test_operator_round3.py runs real bootstrap admission (including rejection of a failed CPU proof) and action-0 settings/artifact construction with heavy restore/export-admission scans stubbed, then real operator/runner/action-2 dispatch with stub model workers for all 636 items. It checks pins, overlays, memory receipt and the archive under metadata/reads/0/metadata/u0. Both operator regressions fail before and pass after; the baseline specifically fails “Operator overlay not active”. |
| 3 LOW: unauthenticated base | Authenticate both non-u0 inventories against MANIFEST base_pin before any arm; the staged u4.json carries the same pin. | Both equally wrong bases, changed bytes and extra files fail. The fresh-application check authenticates all 927 original and patched base files, not only a small fixture. |
| 4 LOW: weak regressions | Run the identical behavioral lock test against round-1-before a4. Add a type-deadline test that attempts a second flock during recovery. Replace F16's evidentiary dependence on a string check with an actual worker-setup test. | lock3_before.txt records two failures: missing recovery and BlockingIOError not raised after lock release. lock3.txt passes both. The actual kit worker mutates the settings environment on the F16 baseline and fails; delivered worker setup passes. |
| 7 INFO: OFF import guard | Extend the one-line range from a0–a10 to a0–a18. | All eight omitted modules fail the guard regression before and are rejected after. The full original/OFF byte-and-source-hash fixture still passes. |

All requested findings have a fix and regression evidence. Finding 2 uses the dispatch's permitted single-card alternative: no multi-card operator variant is delivered. A standalone variant preserving preparation, fixed descriptors, card-bound identities, scheduling and memory-proof handling is estimated to exceed about 80 lines; no validated smaller implementation is claimed. Sharded reads need that operator. Step 600 remains single-card ON with caches only.

INFO 5 is handled operationally: source trees travel as archives, extract node-locally, and the kit requires --public. The README states these rules. INFO 6 remains unvalidated because the array path has no production staging/requeue exercise or owner approval; its example stays approved=false. INFO 8's existing checks are rerun; INFO 9's integrity receipt is regenerated. No scheduler, upload or deployment ran.

## Measured cache cost and mutation contract

Each stub has bf16 parameters of shape 2048×1024 and one 1024-element bf16 buffer per parameter tensor. The stubs have 128 or 256 child modules. Their forward returns a 32-element tensor and performs no model-sized matrix work. Both implementations run a miss and a warm hit, then seven timed hits. The boundary statistic is the median of three hashes. The same frozen-state guards protect vision and SAM; the benchmark invokes the vision wrapper to isolate their shared validation cost.

| Parameters | Parameter / buffer tensors | Weight+buffer bytes | Before ms/call | After ms/call | After install s | Boundary s |
|---:|---:|---:|---:|---:|---:|---:|
| 268,435,456 | 128 / 128 | 537,133,056 | 356.487 | 25.889 | 0.340 | 0.338 |
| 536,870,912 | 256 / 256 | 1,074,266,112 | 731.201 | 52.606 | 0.708 | 0.730 |

Exact samples, environment and peak RSS: [CACHE_COST3.json](checks/CACHE_COST3.json). The full weight hash still costs time at install and boundaries; GPU transfer/synchronization costs are unmeasured. No forecast below credits these CPU ratios.

The torch counter tracks in-place data/size changes, not arbitrary storage writes: [TensorImpl.h:291](/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/include/c10/core/TensorImpl.h:291). Views/detach share it; .data does not: [TensorImpl.h:303](/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/include/c10/core/TensorImpl.h:303). Data reassignment preserves the destination counter: [TensorImpl.h:2051](/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/include/c10/core/TensorImpl.h:2051). The pointer guard catches reassignment to new storage. The installed SGD step calls an in-place parameter update at [sgd.py:379](/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/optim/sgd.py:379); the measured foreach=False test increments the counter.

Persistent .data mutations, NumPy writes and custom pointer writes may leave the tuple unchanged. Full boundary hashes guard those persistent changes. The official [increment_version documentation](https://docs.pytorch.org/docs/2.11/generated/torch.autograd.graph.increment_version.html) and installed [graph.py:242](/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/autograd/graph.py:242) explain untracked writes. Counterless inference tensors are refused, consistent with [TensorImpl.h:413](/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/torch/include/c10/core/TensorImpl.h:413) and the official [inference_mode reference](https://docs.pytorch.org/docs/2.11/generated/torch.autograd.grad_mode.inference_mode.html). [TORCH_VERSIONS3.json](checks/TORCH_VERSIONS3.json) records actual ids, pointers, counters and source-file SHA256s. Other framework evidence is in [FRAMEWORK_EVIDENCE.md](FRAMEWORK_EVIDENCE.md).

Models must remain frozen. A raw write followed by restoration before the next boundary can evade detection; this is outside the supported ownership contract. The guards do not claim otherwise. A mismatch raises a fatal, latched exception and leaves WEIGHTS.json unverified. Resume, merge and the comparator refuse such journals. Graceful deadlines verify weights before lock-held recovery and can resume; hard termination before validation requires a fresh journal. Processor-only runs install no weight guard and retain the ordinary journal-resume contract.

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


## Equality, memory and adoption

The ordinary entrypoint imports no extension and reads no new settings. The OFF fixture compares all generated files and stdout, including source hashes and controlled timing fields, with no field exclusions. [OFF_BYTES.json](checks/OFF_BYTES.json) records its proof. The three reader diffs only add u0 files. The operator diff leaves its OFF memory receipt equal to the original; its activation flag defaults OFF.

The 50-item CPU fixture compares ORIGINAL/OFF/processor+vision ON/processor-only answers and traces exactly with stub generation. Separate SAM fixtures verify cached values, geometry recomputation and mutation rejection. This does not establish production GPU equality. The unrun kit requires independent authenticated roots, ORIGINAL/OFF/OFF_REPEAT/ON plus journal/shard runs, all requested switches ON, useful hits in each enabled cache, memory receipts and zero semantic byte differences. Only clocks and explicit telemetry are excluded. No answer/trace tolerance is allowed. Batched generation is not delivered because changed padding/kernel shapes have no bit-equality guarantee.

The cache cap is 12 GiB when SAM is enabled and 4 GiB otherwise, unless read_cache_bytes explicitly overrides it. The operator ON proof adds that cache cap to the existing G3T/runtime allowance. This is a configured bound, not a measurement of full process memory. [MEMORY.json](checks/MEMORY.json) contains the measured small allocation fixture; the 3 GiB capacity regression simulates accounting without allocating that tensor. Actual H100 host/GPU headroom remains unmeasured.

**Step-600 candidate: single-card ON with caches only.** Build with --enable-extensions --caches-only and the A4 operator inputs described in the [README](kit_parity50/README.md). Add --processor-only to enable just the processor cache; direct settings can use read_processor_only="on", which overrides both model-cache switches. The builder's processor-only profile also turns atomic journals and scene sharding OFF. Generic ON still enables those features for their separate validation gates.

The delivered A4 operator keeps its fixed 636-item descriptors; the owner must bind the target read's descriptors/counts and regenerate the payload, operator and CPU-proof pins for a different item set. No multi-card operator is included. The two/four-shard forecasts require one and are not step-600 launch plans. Real preemption/requeue also remains a separate gate.

The operator test validates the canonical archive at **metadata/reads/0/metadata/u0/answer_trace_return.tgz** when atomic journals are enabled. The unchanged transport includes that nested subtree, and the existing unpacker still binds operator_sha256. Cache-only adoption keeps the ordinary type journals and requests no canonical merge. Full transport/envelope capacity remains a deployment check.

## Review round 1: finding -> fix -> test

Typed keys, complete parity schemas, original/OFF provenance, frozen model identity, lock-held recovery, token transport and bounded cache storage all retain passing regressions. The eight original failing baseline tests reproduce. Model changes now fail a guarded run; persistent raw writes are checked at boundaries under the explicit round-3 contract.

## Review round 2: finding -> fix -> test

Isolated entry, approved paths, array policy/retry, production packaging/pins, SAM capacity, deadline counts, bounded lock waits, processor bypass counts, root checks and worker settings selection all retain passing regressions. All thirteen reviewed-baseline tests fail as expected. The per-call hashing and operator-path findings are covered by the round-3 tests above.

## Patches and base pins

Apply 01–03 in numeric order from a fresh full src tree using patch --batch --fuzz=0 -p1. Apply 04 from a separate A4 operator directory containing tower_sequence.py. Do not apply 04 from src. Tests are included in patch 03 and run against the patched operator through READ_OPERATOR_SOURCE. [MANIFEST.json](patches/MANIFEST.json) pins files, diffs, kit, operator, bases and application receipts.

A4 base SHA256: `813fe4c57b2deed4bd731dd1e3493b6b0bed8d31e7bff92ff112cf5c9df823c3` over 927 non-bytecode files. B5 input archive SHA256: `ac2e259025d6a821aa5eb13e236f0635bd970313859086fc2f3ce3276647f2f0`. Operator base SHA256: `97c8e6dfe33e7fd2988dc44e740f7a3b19627259b8f86827598ed368e1659e22`. The delivered operator/0.py is byte-identical to the bootstrap decoded from the pinned A4 BATCH.sh.

| Patch | Bytes | SHA256 |
|---|---:|---|
| [01_bounded_read_caches.diff](patches/01_bounded_read_caches.diff) | 90430 | `0017649c826b8043f77174c26d33cd6d940018be9e03259d24c642f327c64f76` |
| [02_atomic_scene_shards.diff](patches/02_atomic_scene_shards.diff) | 218841 | `5f76cf79e29471138161e476daf3920ec2bcbf751586fc47528fbd7388530cfa` |
| [03_production_integration.diff](patches/03_production_integration.diff) | 101172 | `a2913f484a080e26a65514479754aee514e43d56fb22591addc362bb34cf7963` |
| [04_operator_cache_bound.diff](patches/04_operator_cache_bound.diff) | 2723 | `0d3bdc2d943554cd525627466d2d71f30881884e76df95204ede6c1accdb9061` |

## What could go wrong and how to notice

| Risk | Detection/action |
|---|---|
| Boundary hashes, copies or cache misses erase savings | Require useful hits and a net complete-run time reduction on the GPU sample; retain the no-saving forecast until then. |
| GPU preprocessing/storage layouts/kernels change an answer | Require all-arm byte equality, not equal scores. The CPU environment lacks production torchvision/CUDA/FLA coverage. |
| Model storage mutates | Tracked changes fail on the next call; persistent raw changes fail at boundaries. Refuse unverified journals. Keep all model mutation outside guarded reads. |
| Host/GPU memory exceeds the operator allowance | Measure full-process peaks; cache caps exclude model/caller working storage. The CPU proof alone is insufficient. |
| Wrong base, payload, operator or item schedule | Kit inventories, payload/plan hashes, operator_sha256 and regenerated CPU proof must match before decode. |
| A hard kill leaves an unchecked journal, or remote locks/requeue differ | Refuse unchecked weighted journals. Verify real persistent-storage restart before preempt/sharded adoption. |
| Return capacity or public-content rules fail | Check the full production envelope, source archives, token-only staging and mandatory --public before launch. |

## Not done

No GPU parity/performance/memory run, real weight restore, bwrap isolation, scheduler action, persistent-storage requeue, remote return publication or array approval ran. No multi-card operator or batching implementation is delivered. The array helper remains an inert, separately gated prototype. These limitations do not waive the zero-tolerance acceptance gate.

No delivered CPU suite or single-GPU kit pass requires a local OS socket. StageOneSocket is a Python callback. Socket-backed distributed/transport integration remains unrun.

The named review sections retain finding history only because the dispatch explicitly requires that audit trail. Other sections state the delivered behavior and current evidence.

## Commands and exact outputs

All commands run from `/scratch/jjyeung/orch_n30/so_read`. work/cpu.sh sets CUDA_VISIBLE_DEVICES="", OMP/MKL/OPENBLAS threads to 8, TOKENIZERS_PARALLELISM=false and PYTHONDONTWRITEBYTECODE=1, then invokes nice -n 10 and the required Python -I -s -B. Tests call torch.set_num_threads(8). work/round3_env.sh also sets the read-only input and local fixture roots.

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
bash work/cpu.sh work/benchmark_round3.py
```

Exact output:

```text
{
  "cases": [
    {
      "after_install_seconds": 0.3398584281094372,
      "after_per_call": {
        "max_seconds": 0.0261009787209332,
        "median_seconds": 0.025889230892062187,
        "min_seconds": 0.02579684229567647,
        "seconds": [
          0.0261009787209332,
          0.025873016100376844,
          0.025897633284330368,
          0.02588817896321416,
          0.025889230892062187,
          0.025902551133185625,
          0.02579684229567647
        ]
      },
      "before_install_seconds": 3.226893022656441e-05,
      "before_per_call": {
        "max_seconds": 0.39679829124361277,
        "median_seconds": 0.35648695891723037,
        "min_seconds": 0.3379322290420532,
        "seconds": [
          0.39679829124361277,
          0.34083114797249436,
          0.35648695891723037,
          0.3759315740317106,
          0.3379322290420532,
          0.3958382620476186,
          0.35621425975114107
        ]
      },
      "blocks": 128,
      "boundary": {
        "max_seconds": 0.33775311103090644,
        "median_seconds": 0.33766773203387856,
        "min_seconds": 0.3376608919352293,
        "seconds": [
          0.33775311103090644,
          0.33766773203387856,
          0.3376608919352293
        ]
      },
      "buffer_shape": [
        1024
      ],
      "buffer_tensors": 128,
      "dtype": "bfloat16",
      "median_speed_ratio": 13.769700629713634,
      "parameter_count": 268435456,
      "parameter_shape": [
        2048,
        1024
      ],
      "parameter_tensors": 128,
      "weight_and_buffer_bytes": 537133056
    },
    {
      "after_install_seconds": 0.7081459369510412,
      "after_per_call": {
        "max_seconds": 0.05550167663022876,
        "median_seconds": 0.052605913020670414,
        "min_seconds": 0.052454326301813126,
        "seconds": [
          0.052671891171485186,
          0.052454326301813126,
          0.05246025510132313,
          0.05550167663022876,
          0.052605913020670414,
          0.05268519185483456,
          0.05258523114025593
        ]
      },
      "before_install_seconds": 3.171805292367935e-05,
      "before_per_call": {
        "max_seconds": 0.7916724169626832,
        "median_seconds": 0.7312010559253395,
        "min_seconds": 0.6898494539782405,
        "seconds": [
          0.7916724169626832,
          0.7312010559253395,
          0.6898494539782405,
          0.7104054749943316,
          0.7234841720201075,
          0.7582796718925238,
          0.7435773792676628
        ]
      },
      "blocks": 256,
      "boundary": {
        "max_seconds": 0.7527899681590497,
        "median_seconds": 0.7304944368079305,
        "min_seconds": 0.7303731450811028,
        "seconds": [
          0.7304944368079305,
          0.7527899681590497,
          0.7303731450811028
        ]
      },
      "buffer_shape": [
        1024
      ],
      "buffer_tensors": 256,
      "dtype": "bfloat16",
      "median_speed_ratio": 13.899598237902058,
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
  "max_rss_bytes": 1321455616,
  "nice": 19,
  "threads": 8,
  "torch": "2.11.0+cpu"
}
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
        "data_ptr": 138099648,
        "object_id": 139995510776656,
        "version": 1
      },
      "before": {
        "data_ptr": 138099648,
        "object_id": 139995510776656,
        "version": 0
      },
      "object_changed": false,
      "operation": "parameter.add_",
      "pointer_changed": false,
      "version_changed": true
    },
    {
      "after": {
        "data_ptr": 138110144,
        "object_id": 139995510776976,
        "version": 1
      },
      "before": {
        "data_ptr": 138110144,
        "object_id": 139995510776976,
        "version": 0
      },
      "object_changed": false,
      "operation": "detach().add_",
      "pointer_changed": false,
      "version_changed": true
    },
    {
      "after": {
        "data_ptr": 138110720,
        "object_id": 139995510776656,
        "version": 0
      },
      "before": {
        "data_ptr": 138110720,
        "object_id": 139995510776656,
        "version": 0
      },
      "object_changed": false,
      "operation": "parameter.data.add_",
      "pointer_changed": false,
      "version_changed": false
    },
    {
      "after": {
        "data_ptr": 138113344,
        "object_id": 139995510776976,
        "version": 0
      },
      "before": {
        "data_ptr": 138111232,
        "object_id": 139995510776976,
        "version": 0
      },
      "object_changed": false,
      "operation": "parameter.data assignment to cloned storage",
      "pointer_changed": true,
      "version_changed": false
    },
    {
      "after": {
        "data_ptr": 138113728,
        "object_id": 139995510776656,
        "version": 0
      },
      "before": {
        "data_ptr": 138113728,
        "object_id": 139995510776656,
        "version": 0
      },
      "object_changed": false,
      "operation": "parameter.data assignment to same storage",
      "pointer_changed": false,
      "version_changed": false
    },
    {
      "after": {
        "data_ptr": 138113856,
        "object_id": 139995510776976,
        "version": 0
      },
      "before": {
        "data_ptr": 138113856,
        "object_id": 139995510776976,
        "version": 0
      },
      "object_changed": false,
      "operation": "numpy raw storage write",
      "pointer_changed": false,
      "version_changed": false
    },
    {
      "after": {
        "data_ptr": 138114048,
        "object_id": 139995510776656,
        "version": 1
      },
      "before": {
        "data_ptr": 138114048,
        "object_id": 139995510776656,
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
kit: OK
kit_launch: OK
PASS: all 8 round-1 regressions fail against the round-1 reviewed implementation.
PASS: all 13 round-2 regressions fail against the round-2 reviewed implementation (14 failures including both CLI variants).
PASS: round3_before reproduces FAILED (failures=15).
PASS: operator3_before reproduces FAILED (failures=2).
PASS: lock3_before reproduces FAILED (failures=2).
PASS: f16_behavior_before reproduces FAILED (failures=1).
PASS: Python syntax, shell syntax, and default-off execution guards.
{"cuda_visible_devices": "", "max_child_rss_bytes": 400650240, "torch": "2.11.0+cpu", "torch_threads": 8, "transformers": "5.12.1", "workspace_bytes": 1192848601}
```

```bash
bash work/cpu.sh work/build_patches.py
```

Exact output:

```text
PASS: 3 additive reader diffs (31 files) plus 1 default-OFF A4 operator diff; zero-fuzz application; unchanged original reader hash trees.
PASS: all 10 CPU suites pass from the fresh applied A4 tree; both complete 927-file base inventories authenticate.
Applied verification root: /scratch/jjyeung/orch_n30/so_read/work/apply-round3/038bb8a8dd8740039dd3064e9adb57b8
```

### Workspace suites

```bash
bash work/round3_env.sh work/src/u0/tests/test_read_cache.py
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
Ran 15 tests in 3.132s

OK
```

```bash
bash work/round3_env.sh work/src/u0/tests/test_read_journal.py
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
Ran 13 tests in 0.128s

OK
```

```bash
bash work/round3_env.sh work/src/u0/tests/test_off.py
```

Exact output:

```text
test_every_output_byte_and_source_hash_matches_original (__main__.OffContractTests.test_every_output_byte_and_source_hash_matches_original) ... ok

----------------------------------------------------------------------
Ran 1 test in 5.677s

OK
```

```bash
bash work/round3_env.sh work/src/u0/tests/test_public.py
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
bash work/round3_env.sh work/src/u0/tests/test_round1.py
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
Ran 17 tests in 4.383s

OK
```

```bash
bash work/round3_env.sh work/src/u0/tests/test_round2.py
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
Ran 13 tests in 3.901s

OK
```

```bash
bash work/round3_env.sh work/src/u0/tests/test_round3.py
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
Ran 9 tests in 2.000s

OK
```

```bash
bash work/round3_env.sh work/src/u0/tests/test_operator_round3.py
```

Exact output:

```text
test_f2_a12_payload_through_a4_actions_and_nested_return (__main__.OperatorTests.test_f2_a12_payload_through_a4_actions_and_nested_return) ... ok
test_f2_operator_memory_bound_includes_cache_only_when_enabled (__main__.OperatorTests.test_f2_operator_memory_bound_includes_cache_only_when_enabled) ... ok

----------------------------------------------------------------------
Ran 2 tests in 11.731s

OK
```

```bash
bash work/round3_env.sh work/src/u0/tests/test_lock_round3.py
```

Exact output:

```text
test_deadline_recovery_keeps_writer_lock (lock_behavior.RunnerTests.test_deadline_recovery_keeps_writer_lock) ... ok
test_type_deadline_recovery_holds_writer_lock (__main__.TypeLockTests.test_type_deadline_recovery_holds_writer_lock) ... ok

----------------------------------------------------------------------
Ran 2 tests in 0.017s

OK
```

```bash
bash work/round3_env.sh out/kit_parity50/test_compare.py
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
Ran 9 tests in 0.354s

OK
```

```bash
bash work/round3_env.sh out/kit_parity50/test_run.py
```

Exact output:

```text
test_durable_scene_comparison_requires_explicit_on_arm (__main__.LaunchTests.test_durable_scene_comparison_requires_explicit_on_arm) ... ok
test_original_and_off_do_not_opt_in_to_journaling_or_sharding (__main__.LaunchTests.test_original_and_off_do_not_opt_in_to_journaling_or_sharding) ... ok
test_stage_kit_uses_opaque_names_token_metadata_and_authenticated_sample_bytes (__main__.LaunchTests.test_stage_kit_uses_opaque_names_token_metadata_and_authenticated_sample_bytes) ... ok

----------------------------------------------------------------------
Ran 3 tests in 0.063s

OK
```

### Fresh-application suites

```bash
READ_OPERATOR_SOURCE=/scratch/jjyeung/orch_n30/so_read/work/apply-round3/038bb8a8dd8740039dd3064e9adb57b8/operator/tower_sequence.py bash work/round3_env.sh /scratch/jjyeung/orch_n30/so_read/work/apply-round3/038bb8a8dd8740039dd3064e9adb57b8/src/u0/tests/test_read_cache.py
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
Ran 15 tests in 3.011s

OK
```

```bash
READ_OPERATOR_SOURCE=/scratch/jjyeung/orch_n30/so_read/work/apply-round3/038bb8a8dd8740039dd3064e9adb57b8/operator/tower_sequence.py bash work/round3_env.sh /scratch/jjyeung/orch_n30/so_read/work/apply-round3/038bb8a8dd8740039dd3064e9adb57b8/src/u0/tests/test_read_journal.py
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
Ran 13 tests in 0.120s

OK
```

```bash
READ_OPERATOR_SOURCE=/scratch/jjyeung/orch_n30/so_read/work/apply-round3/038bb8a8dd8740039dd3064e9adb57b8/operator/tower_sequence.py bash work/round3_env.sh /scratch/jjyeung/orch_n30/so_read/work/apply-round3/038bb8a8dd8740039dd3064e9adb57b8/src/u0/tests/test_off.py
```

Exact output:

```text
test_every_output_byte_and_source_hash_matches_original (__main__.OffContractTests.test_every_output_byte_and_source_hash_matches_original) ... ok

----------------------------------------------------------------------
Ran 1 test in 5.862s

OK
```

```bash
READ_OPERATOR_SOURCE=/scratch/jjyeung/orch_n30/so_read/work/apply-round3/038bb8a8dd8740039dd3064e9adb57b8/operator/tower_sequence.py bash work/round3_env.sh /scratch/jjyeung/orch_n30/so_read/work/apply-round3/038bb8a8dd8740039dd3064e9adb57b8/src/u0/tests/test_public.py
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
READ_OPERATOR_SOURCE=/scratch/jjyeung/orch_n30/so_read/work/apply-round3/038bb8a8dd8740039dd3064e9adb57b8/operator/tower_sequence.py bash work/round3_env.sh /scratch/jjyeung/orch_n30/so_read/work/apply-round3/038bb8a8dd8740039dd3064e9adb57b8/src/u0/tests/test_round1.py
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
Ran 17 tests in 4.780s

OK
```

```bash
READ_OPERATOR_SOURCE=/scratch/jjyeung/orch_n30/so_read/work/apply-round3/038bb8a8dd8740039dd3064e9adb57b8/operator/tower_sequence.py bash work/round3_env.sh /scratch/jjyeung/orch_n30/so_read/work/apply-round3/038bb8a8dd8740039dd3064e9adb57b8/src/u0/tests/test_round2.py
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
Ran 13 tests in 4.028s

OK
```

```bash
READ_OPERATOR_SOURCE=/scratch/jjyeung/orch_n30/so_read/work/apply-round3/038bb8a8dd8740039dd3064e9adb57b8/operator/tower_sequence.py bash work/round3_env.sh /scratch/jjyeung/orch_n30/so_read/work/apply-round3/038bb8a8dd8740039dd3064e9adb57b8/src/u0/tests/test_round3.py
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
Ran 9 tests in 2.185s

OK
```

```bash
READ_OPERATOR_SOURCE=/scratch/jjyeung/orch_n30/so_read/work/apply-round3/038bb8a8dd8740039dd3064e9adb57b8/operator/tower_sequence.py bash work/round3_env.sh /scratch/jjyeung/orch_n30/so_read/work/apply-round3/038bb8a8dd8740039dd3064e9adb57b8/src/u0/tests/test_operator_round3.py
```

Exact output:

```text
test_f2_a12_payload_through_a4_actions_and_nested_return (__main__.OperatorTests.test_f2_a12_payload_through_a4_actions_and_nested_return) ... ok
test_f2_operator_memory_bound_includes_cache_only_when_enabled (__main__.OperatorTests.test_f2_operator_memory_bound_includes_cache_only_when_enabled) ... ok

----------------------------------------------------------------------
Ran 2 tests in 11.599s

OK
```

```bash
READ_OPERATOR_SOURCE=/scratch/jjyeung/orch_n30/so_read/work/apply-round3/038bb8a8dd8740039dd3064e9adb57b8/operator/tower_sequence.py bash work/round3_env.sh /scratch/jjyeung/orch_n30/so_read/work/apply-round3/038bb8a8dd8740039dd3064e9adb57b8/src/u0/tests/test_lock_round3.py
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
READ_OPERATOR_SOURCE=/scratch/jjyeung/orch_n30/so_read/work/apply-round3/038bb8a8dd8740039dd3064e9adb57b8/operator/tower_sequence.py bash work/round3_env.sh /scratch/jjyeung/orch_n30/so_read/work/apply-round3/038bb8a8dd8740039dd3064e9adb57b8/src/u0/tests/test_compare.py
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
Ran 9 tests in 0.352s

OK
```

### Reviewed-baseline regressions (expected failures)

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
Ran 8 tests in 0.031s

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
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/3beccf807c314fe5a4513040f7499082/u0/a8.py", line 65, in <module>
    raise SystemExit(main())
                     ^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/3beccf807c314fe5a4513040f7499082/u0/a8.py", line 61, in main
    return launch(rest)
           ^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/3beccf807c314fe5a4513040f7499082/u0/a4.py", line 2, in main
    from a8 import source_hash
ModuleNotFoundError: No module named 'a8'


======================================================================
FAIL: test_f1_actual_isolated_script_plain_and_opaque (__main__.Round2Tests.test_f1_actual_isolated_script_plain_and_opaque) (opaque=True)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_round2.py", line 67, in test_f1_actual_isolated_script_plain_and_opaque
    self.assertEqual(result.returncode,0,result.stdout+result.stderr)
AssertionError: 1 != 0 : Traceback (most recent call last):
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/cad4a01827b54f32a100fdd099cbf792/u0/a8.py", line 65, in <module>
    raise SystemExit(main())
                     ^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/cad4a01827b54f32a100fdd099cbf792/u0/a8.py", line 56, in main
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
Ran 13 tests in 0.208s

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
AssertionError: 139697206461136 unexpectedly found in {139697206461136, 139697206461296} : Per-call weight hashing

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
Ran 9 tests in 0.923s

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
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_operator_round3.py", line 248, in <module>
    if len(sys.argv)>1 and sys.argv[1]=='--child':child(Path(sys.argv[2]),int(sys.argv[3]))
                                                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/src/u0/tests/test_operator_round3.py", line 138, in child
    boot.main();main_job.assert_called_once_with(root)
    ^^^^^^^^^^^
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/3fac77d531864eb3801acee2be6b96ee/0.py", line 44, in main
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
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/3fac77d531864eb3801acee2be6b96ee/0.py", line 18, in dispatch
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
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/3fac77d531864eb3801acee2be6b96ee/7.py", line 139, in main
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
  File "/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/3fac77d531864eb3801acee2be6b96ee/7.py", line 87, in run
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
Ran 2 tests in 10.000s

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
Ran 2 tests in 0.016s

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
AssertionError: 'H10_SETTINGS' unexpectedly found in {'CUDA_VISIBLE_DEVICES': 'fixture', 'H10_SETTINGS': '/scratch/jjyeung/orch_n30/so_read/work/test-artifacts/c298081d5e434be598ffc80336922ee0/u0.json'}

----------------------------------------------------------------------
Ran 1 test in 0.893s

FAILED (failures=1)
```
