# tree_rebuild12: build-21 performance patches and N acceptance

Apply `patches_b21/01_cpu_prefetch.diff`, `02_decoded_rgb_cache.diff`,
`03_batch_metrics.diff`, then `04_test_joint_hash_0dim.diff`. The base pin is
`b262e7a757d93e2485a523765916507b2bf3305fe3213cffca100007d19f2ce8` (936 files).
`patches_b21/manifest.json` contains patch SHA-256s and input/output file pins.
The delivered series replays with zero fuzz and zero offsets. It requires a new
source seal and the normal admission for the rebuilt tree.

The locally tested tree is
`/scratch/jjyeung/orch_n30/so_step/work/b21_final/work/tree_r1`.
Read-only fixture links from READY sit beside this tree, outside its sealed source.
The three switches default to OFF; the OFF startup collective sequence and
preparation broadcast payload are unchanged.

## N's first launch

Set `C1_CPU_PREFETCH=0` and `C1_DECODED_CACHE_MIB=0`. Set
`C1_BATCH_METRICS=0` unless the review and completed build-21 tests establish
bitwise equality of every logged training number and trained value with 03 ON.
Only then may the first launch use `C1_BATCH_METRICS=1`. The source review supports
03; the updated build-21 two-rank gate below remains a lane prerequisite.
The numerical gate covers losses, components, stream means, gradient diagnostics,
gates, row metadata, every gradient and updated tensor. Timing and allocator
diagnostics measure the optimization and are not loss-parity fields.

Keep the same 03 setting throughout the launch/continuation prefetch comparison.
02 stays OFF until its hit rate and end-to-end benefit have been measured.

## CPU checks before the first continuation

On staged scratch data, run `kit_timing/data_only.py`; it calls
`kit_timing/row_hash.py` to compare encoded tensors and row draws. Use the real
production processor, frozen receipt and base manifest. Supply a complete epoch
row plan, including the largest groups; a 10- or 40-update kit plan is insufficient.
Run all four rank projections serially. Use the same production thread settings
for OFF and ON; do not infer the production setting from this lane's eight-thread
CPU tests.

With `KIT` pointing to this delivery's `out/kit_timing`, `TREE` to the rebuilt
source, and the other variables pointing to the admitted local inputs:

```bash
for rank in 0 1 2 3; do
  nice -n 10 "$PYTHON" "$KIT/data_only.py" --tree "$TREE" \
    --receipt "$RECEIPT" --manifest "$BASE_MANIFEST" --config "$CONFIG" \
    --plan "$EPOCH_PLAN" --full-plan --rank "$rank" --arm off \
    --out "$OUT/data_off_rank${rank}.json" || exit "$?"
  nice -n 10 "$PYTHON" "$KIT/data_only.py" --tree "$TREE" \
    --receipt "$RECEIPT" --manifest "$BASE_MANIFEST" --config "$CONFIG" \
    --plan "$EPOCH_PLAN" --full-plan --rank "$rank" --arm prefetch \
    --baseline "$OUT/data_off_rank${rank}.json" \
    --out "$OUT/data_prefetch_rank${rank}.json" || exit "$?"
done
```

Require identical `row_draws` and `encoded_row_sha256`, and
`global_rng_unchanged=true` for every step. Check each sidecar's `full_plan`,
`plans_checked`, `plans_available`, `rank`, `world_size` and
`peak_group_tensor_bytes`. The latter must not exceed `group_budget_bytes`
(1,073,741,824). It counts batch, targets and tensor-valued audit fields using
the producer's conservative storage accounting, including repeated references.
`--full-plan` audits every supplied plan; r1_ops must verify that the supplied
plan covers the complete epoch. No real-data peak has been measured in this lane.

## First continuation and r1_ops acceptance

After the CPU and build-21 gates pass, N's first continuation sets
`C1_CPU_PREFETCH=1`. It leaves 02 OFF and keeps 03 at the first launch's setting.
r1_ops compares data-wait seconds per step and first-step losses against the
first launch's OFF baseline on the same frozen row plan.

The acceptance replay must also start from identical model/optimizer/RNG state,
world size and processor assets. Retain that state with the launch baseline.
If a normal continuation has advanced its checkpoint or sampler, use a disposable
OFF replay at the continuation's checkpoint to establish the matched reference;
comparing its next step with historical step 1 would confound learning with
prefetch. Do not publish replay updates as additional training steps.

| Readout | Exact location and fields |
|---|---|
| Data wait | `metrics_<attempt>.jsonl`: match `step`, then read every `ranks[r].data_seconds`. Compare per-rank values and the maximum across ranks per matched step. Retain `ranks[r].wall_seconds` to detect host contention. |
| First-step logged losses | First matching record in `metrics_<attempt>.jsonl`: compare every `ranks[r].components[key]` and `ranks[r].stream_means[stream]` bitwise. The trainer has no top-level scalar `loss` field. `inputs/first_step_<attempt>.json` also contains `ranks[r].components`. |
| Exact total loss per microstep | Disposable kit `rank<r>/steps.json`: first record's `first_step_micro_losses`, in microstep order. Match `plan_sha256`, `start_step`, checkpoint/RNG and trainables before comparing. |
| Rows and CPU tensors | CPU kit step records: `row_draws` (stream, planned index, admitted candidate) and `encoded_row_sha256`; require equal arrays in order on every rank. |

**Kill rule:** any first-step loss difference or row-draw difference turns
`C1_CPU_PREFETCH=0` again. Preserve the failed comparison and stop the ON arm;
do not relax the tolerance or substitute rows. If OFF repeats differ, the
comparison is invalid and prefetch remains OFF until a matched reference exists.
Lower data wait alone does not establish a speedup; check whole-step wall time
for a GIL or CPU-thread slowdown.

## Lane command: build-21 two-rank gloo gate

Run outside the socket-restricted sandbox, on eight cores. This lane did not run
the command. It exercises positive controls for worker threads, cache misses and
deferred metric rows, plus first/middle/last admission failures on both ranks.

```bash
cd /scratch/jjyeung/orch_n30/so_step
nice -n 10 taskset -c 0-7 env CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 \
  OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false \
  SO_TEST_TREE=/scratch/jjyeung/orch_n30/so_step/work/b21_final/work/tree_r1 \
  /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/run_cpu_tests.py \
  tests.test_so_prefetch tests.test_so_cache tests.test_so_metrics \
  tests.test_so_joint tests.test_so_review tests.test_so_round2 \
  > work/round2_b21_gloo_by_coordinator.txt 2>&1
result=$?
printf '\nEXIT=%s\n' "$result" >> work/round2_b21_gloo_by_coordinator.txt
exit "$result"
```

The full GPU timing kit checks co-location and free memory before training.
Its default 840 updates cost an estimated 31 hours at the supplied 133 s/update;
it is separate from this continuation acceptance test. Real CUDA timing,
production-processor equality and production memory peaks remain host checks.
