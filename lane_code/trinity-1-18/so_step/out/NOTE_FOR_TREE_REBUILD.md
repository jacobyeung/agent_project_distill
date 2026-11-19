VERDICT: DONE Build-21 fixes, bounded CPU audit and ordered continuation replay are delivered; the updated lane gate and production checks remain required.

## Build and switches

Apply `patches_b21/01_cpu_prefetch.diff`, `02_decoded_rgb_cache.diff`,
`03_batch_metrics.diff`, then `04_test_joint_hash_0dim.diff` with
`patch --batch --fuzz=0 -p1`. The base is build 21, seal
`b262e7a757d93e2485a523765916507b2bf3305fe3213cffca100007d19f2ce8`.
`patches_b21/manifest.json` pins each input, patch and output. `patches/` is an
identical build-21 entry point. The orchestrator must seal and admit the rebuilt tree.
The tested copy is `/scratch/jjyeung/orch_n30/so_step/work/b21_final/work/tree_r1`.

All switches default OFF: `C1_CPU_PREFETCH=0`, `C1_DECODED_CACHE_MIB=0`,
`C1_BATCH_METRICS=0`, `C1_CPU_PREFETCH_FALLBACK=0`. With all OFF, records and the
startup preparation payload retain the input structure; numerical parity excludes
elapsed-time and allocator diagnostics.

N's first launch keeps 01, 02 and fallback OFF. It may use 03 ON: the independent
review and both supplied build-21 two-rank runs establish numerical equality for
that scheduling change. Run the updated gate below before deploying this series.
Keep the chosen 03 value constant in every CPU-prefetch GPU comparison.

03's expected gain is **about zero, at most 0.1 s/update (estimate)**. Finite-loss,
grid and carrier-count reads still wait on the GPU each microstep. The timing kit's
roughly 3-s minimum detectable difference at three repeats and assumed 1-s repeat
SD cannot resolve this estimate. 02 stays OFF; its expected gain is **at most zero
at low reuse (estimate)** because misses add a read and SHA-256.

For 03, exclude `memory.microbatches[*].after_forward.allocated_bytes`,
`memory.microbatches[*].after_backward.allocated_bytes`, and allocator `peak_*`
fields, including top-level `peak_allocated_bytes` and `peak_reserved_bytes`,
from numerical equality. Retained scalar blocks can add about 0.2 MB per rank
(estimate). Continue checking these fields for practical memory headroom.

## CPU checks before the first continuation

Use the production processor and receipt on staged local scratch data. Audit the
**first 10 continuation updates × 4 ranks × 2 arms**, serially, including actual
augmented pose rows. `write_plan.py` reads the step from the pinned checkpoint and
makes the same `data.mixed_indices` call as `run_steps`, including `row_start_step`,
world, mix and R2 settings. No model loads to write the plan.

**Estimated runtime:** `10 × 4 × 2 × 31.7 s = 2,536 s`, about **42 minutes**, using
the supplied measured data timer. Allow roughly 45–60 minutes for processor startup,
row hashing and host variation; this audit's runtime has not been measured here.
The first updates already contain the large VQA/routing/pointing grids described
in the supplied log. This is a bounded audit, not a proof over every future row.

Set `DELIVERY` to this bundle's `out`, `TREE` to the admitted rebuilt source,
`PYTHON` to the production interpreter, `CONFIG`, `RECEIPT` and `BASE_MANIFEST`
to their admitted local files, and `AUDIT_DIR` to a fresh scratch directory.
`RESUME_PIN` must name a JSON file containing the native `{path, sha256}` pin of
**the exact checkpoint used for the first continuation**, never `latest`.
Inherit production thread settings for both arms.

```bash
date -u
mkdir "$AUDIT_DIR"
nice -n 10 env CUDA_VISIBLE_DEVICES='' "$PYTHON" "$DELIVERY/kit_timing/write_plan.py" \
  --tree "$TREE" --config "$CONFIG" --receipt "$RECEIPT" \
  --resume-pin "$RESUME_PIN" --steps 10 --out "$AUDIT_DIR/plan.json"
for rank in 0 1 2 3; do
  date -u
  nice -n 10 env CUDA_VISIBLE_DEVICES='' "$PYTHON" "$DELIVERY/kit_timing/data_only.py" \
    --tree "$TREE" --receipt "$RECEIPT" --manifest "$BASE_MANIFEST" --config "$CONFIG" \
    --plan "$AUDIT_DIR/plan.json" --steps 10 --require-coverage --rank "$rank" --arm off \
    --out "$AUDIT_DIR/data_off_rank${rank}.json" || exit "$?"
  nice -n 10 env CUDA_VISIBLE_DEVICES='' "$PYTHON" "$DELIVERY/kit_timing/data_only.py" \
    --tree "$TREE" --receipt "$RECEIPT" --manifest "$BASE_MANIFEST" --config "$CONFIG" \
    --plan "$AUDIT_DIR/plan.json" --steps 10 --require-coverage --rank "$rank" --arm prefetch \
    --baseline "$AUDIT_DIR/data_off_rank${rank}.json" \
    --out "$AUDIT_DIR/data_prefetch_rank${rank}.json" || exit "$?"
done
```

Require identical ordered `row_draws` and `encoded_row_sha256` arrays, verified
by `kit_timing/row_hash.py`, and `global_rng_unchanged=true` on every update.
Each sidecar records `start_step`, `resume`, `plan_sha256`, `rank`, `world_size`,
`plans_checked=10`, `peak_group_tensor_bytes`, `group_budget_bytes`,
`peak_rss_bytes`, `augmented_pose_rows`, `augmentation_threads`, `grid_rows` and
`observed_max_grid`. Require augmented rows on every rank in both arms; ON must
record a `c1-row-cpu` worker. The kit observes real nonzero augmentation calls,
checks every emitted image/video grid against `[32,20,26]`, and refuses missing
coverage. Do not substitute convenient rows if coverage fails. The grid check
covers the audited outputs; it does not establish a universal processor bound.

The tensor peak includes batch, targets and tensor-valued audits, with shared
storage counted per reference. It must be at most **1,073,741,824 bytes**.
`peak_rss_bytes` is the Linux process lifetime peak for that arm, including the
worker's receipt/processor copies and startup. Run each arm in its own process;
RSS is not a worker-only measurement or a 2-GiB total-memory promise.
Teacher alignment in the receipt also activates the real pose-target check.

Clip mixes remain refused. That refusal occurs during the first group's factory
setup, after model load, then propagates through the original group admission.
Geometry, MDG and gf1 remain outside the prefetched path. Local torchvision is
absent, so actual augmented production rows must pass this host audit.

## Exact disposable replay: OFF, OFF, ON

Run `kit_profile/replay.sh` on the already admitted, exclusive four-GPU production
host. It uses **`--mode replay`, exactly one optimizer update per leg, zero warmup**,
without the profiler or the profile mode's 895-s cap. Every leg restores the same
`RESUME_PIN`. `PLAN` names the CPU-audited plan above; the replay uses its first
update, at `start_step + 1`. Set `RESUME_CONFIG` to the checkpoint's original
configuration when the source seal differs; the read-only bridge checks the
unchanged training/data binding. `OUT` must be a fresh scratch directory.

```bash
date -u
TREE="$TREE" CONFIG="$CONFIG" PYTHON="$PYTHON" \
  RESUME_PIN="$RESUME_PIN" RESUME_CONFIG="${RESUME_CONFIG:-}" \
  PLAN="$AUDIT_DIR/plan.json" AUDIT_DIR="$AUDIT_DIR" OUT="$REPLAY_OUT" \
  REPLAY_METRICS="${C1_BATCH_METRICS:-0}" \
  bash "$DELIVERY/kit_profile/replay.sh"
```

The wrapper runs **OFF (`off1`), OFF (`off2`), then ON (`on`)** in that order and
calls `kit_timing/replay_compare.py`. It leaves 02 and fallback OFF. Each process
has a 3,600-s cap; failure or timeout stops the sequence with no automatic retry.
**Estimated total wall time is 30–60 minutes**, including three cold starts and
checkpoint restores; three supplied 440-s cold updates alone imply about 22 minutes.
No production replay wall time has been measured here. Outputs are disposable;
the kit writes no production checkpoints, exports or training steps.

The comparator requires the same checkpoint, trainables, configuration, thread
settings, step and plan, plus the matching CPU audit. Its acceptance rule is:

1. If OFF repeats agree bitwise, ON must agree bitwise for every component,
   stream mean and first-step microstep loss on every rank.
2. If OFF repeats differ, CPU `encoded_row_sha256` and `row_draws` must still match.
   For each scalar, both `abs(ON−OFF1)` and `abs(ON−OFF2)` must be no larger than
   `abs(OFF1−OFF2)`. A zero OFF spread requires zero numerical difference.
3. Reject nonfinite losses, changed rows, mismatched state/plan, missing CPU
   coverage or missing ON provenance. Keep `C1_CPU_PREFETCH=0` after any rejection.

`acceptance.json` retains per-rank OFF spread and ON differences after a completed
comparison. A structural validation error exits nonzero and blocks acceptance.
OFF nondeterminism alone is not an automatic refusal when the second rule passes.

## First continuation and r1_ops readouts

After the CPU audit, ordered replay and lane gate pass, N's first continuation
sets `C1_CPU_PREFETCH=1`, with 02 and fallback OFF and the same 03 value. Compare
against the disposable OFF replays at that continuation checkpoint. Historical
launch step 1 is not a matching plan or model state.

| Readout | Exact field and comparison |
|---|---|
| Proof that ON ran | Require `metrics_<attempt>.jsonl` → `ranks[r].performance.C1_CPU_PREFETCH == "1"` on every rank. Verify `C1_BATCH_METRICS` and `C1_DECODED_CACHE_MIB` too. The field appears only when some switch is nonzero; all-OFF records have no `performance` field. |
| Data wait and wall time | Read `ranks[r].data_seconds` and `ranks[r].wall_seconds`. Compare matched replay steps. For normal continuation monitoring, compare per-rank and slowest-rank medians/IQR over at least 20 updates per arm; those distributions are not matched-step numerical proofs. |
| First-step logged losses | First matching `metrics_<attempt>.jsonl` record: `ranks[r].components[key]` and `ranks[r].stream_means[stream]`. `inputs/first_step_<attempt>.json` also contains rank components. There is no top-level scalar `loss`. |
| Total microstep losses | Disposable `off1`, `off2`, `on` → `rank<r>/steps.json[0].first_step_micro_losses`, in order. |
| CPU equality | Each audited step's `encoded_row_sha256`, `row_draws`, `plan_sha256` and `global_rng_unchanged`. |

Any failed acceptance criterion turns prefetch OFF. Lower data wait alone does
not establish a gain; host/GIL contention can increase whole-step wall time.

The optional **`C1_CPU_PREFETCH_FALLBACK=1`** requires 01 ON. It discards an
over-budget prepared group and performs the original synchronous main-thread
fetch/admission, with unchanged OFF outputs. It records cumulative
`ranks[r].cpu_prefetch.budget_fallback_groups` and its switch value in `performance`.
Frequent fallback adds duplicate CPU work and can erase gains. It stays OFF in
this acceptance experiment. It removes the prepared-group cap for the synchronous
fallback group, so monitor RSS; it does not impose a total-RAM limit.

## Lane command: build-21 two-rank gloo gate

The coordinator's supplied round-2 build-21 log reports **23 tests OK in
1016.666 s**; the independent review reports **23 tests OK in 871.372 s**, plus
**2 GX tests OK in 12.606 s**. Those results cover the reviewed round-2 bytes.
The following command covers this delivered series, including the new asymmetric
fallback test and both GX tests. Sockets are unavailable here; the lane runs it.

```bash
cd /scratch/jjyeung/orch_n30/so_step
date -u
nice -n 10 taskset -c 0-7 env CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 \
  OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false \
  C1_CPU_PREFETCH=0 C1_DECODED_CACHE_MIB=0 C1_BATCH_METRICS=0 C1_CPU_PREFETCH_FALLBACK=0 \
  SO_TEST_TREE=/scratch/jjyeung/orch_n30/so_step/work/b21_final/work/tree_r1 \
  /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/run_cpu_tests.py \
  tests.test_so_prefetch tests.test_so_cache tests.test_so_metrics \
  tests.test_so_joint tests.test_so_review tests.test_so_round2 tests.test_so_round3 \
  tests.test_gx_carrier.GXPTests.test_two_rank_gxp_first_batch_forward_backward \
  tests.test_gx_carrier.GXTests.test_two_rank_fsdp_replicas_checkpoint_and_exports \
  > work/round3_b21_gloo_by_coordinator.txt 2>&1
result=$?
printf '\nEXIT=%s\n' "$result" >> work/round3_b21_gloo_by_coordinator.txt
exit "$result"
```

Require `SO_GLOO_PROOF`, `SO_ADMISSION_PROOF`, `SO_FALLBACK_PROOF`, `OK` and `EXIT=0`.

## Review round 3: finding -> fix -> test

| Finding | Fix | Test or evidence |
|---|---|---|
| 1 MEDIUM | Bounded continuation plan writer, 10×4×2 audit, grid/augmentation coverage, runtime; separate default-OFF synchronous fallback and counter. | `KitRound3` sampler/coverage tests; `Round3.test_budget_fallback_is_bitwise_off_and_logged`; lane asymmetric fallback test. |
| 2 MEDIUM | Exact one-step replay command; OFF, OFF, ON; bitwise-or-OFF-spread rule; matched continuation checkpoint. | Replay decision and complete gate regressions, including signed zero, NaN, wrong audit plan and silent OFF. |
| 3 MEDIUM | Conditional `performance` step field; require it for ON. | ON-only logging regression and real `train()` startup smoke. |
| 4 LOW | Exercise real train startup payload and worker. | `_frozen == ('1','0','1')`, third payload item, `c1-row-cpu_0`, and ON provenance asserted. |
| 5–7 LOW | 03 gain ≈0; 02 gain ≤0 at low reuse; matched replay or ≥20-update distributions. | Source review and corrected commands/readouts above. No speedup measurement claimed. |
| 8 INFO | Name allocator fields excluded from numerical equality. | Retained-scalar accounting and numerical parity scope. |
| 9 INFO | State supplied coordinator/reviewer results and their source scope. | Named logs in REPORT; this changed series has its own lane command. |
| 10 INFO | Include both GX tests in the lane gate. | Exact command above; review's two-test pass. |
| 11 INFO | Record Linux peak RSS per arm/process. | CPU data-audit sidecar regression. |
| 12 INFO | Explain late clip-mix refusal. | Existing refusal regression; factory callsite. |
| 13 INFO | Require actual augmented pose execution on the production host. | Coverage observer tested with a controlled augmentation function; real torchvision unavailable locally. |
| 14 INFO | Carry receipt alignment into the audit descriptor. | Real pose-row validation rejects missing aligned targets. |
| 15 INFO | Restore `ExportLeg`'s class docstring. | Docstring regression. |
