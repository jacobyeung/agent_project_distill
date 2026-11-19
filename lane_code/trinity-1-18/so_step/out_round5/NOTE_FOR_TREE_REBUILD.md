VERDICT: DONE Round-4 kit fixes are delivered; the handed-over trainer patches are unchanged and the 31-test coordinator gate has passed.

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
that scheduling change. The 31-test coordinator gate below has passed on these exact trainer bytes.
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
calls `run.prepared(cfg)` once and writes the merged final-mode receipt to
`$AUDIT_DIR/prepared_receipt.json`. Both CPU arms read that exact pinned file,
including alignment, pointing token weights and camera overrides. This private
operational input preserves exact decoded paths and identifiers through lossless
JSON escaping, so the serialized file contains no literal model words. Keep it
private; report metadata and logs use the ordinary redacting filter. The plan writer makes the same `data.mixed_indices` call as `run_steps`, including `row_start_step`,
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
    --tree "$TREE" --receipt "$AUDIT_DIR/prepared_receipt.json" --manifest "$BASE_MANIFEST" --config "$CONFIG" \
    --plan "$AUDIT_DIR/plan.json" --steps 10 --require-coverage --rank "$rank" --arm off \
    --out "$AUDIT_DIR/data_off_rank${rank}.json" || exit "$?"
  nice -n 10 env CUDA_VISIBLE_DEVICES='' "$PYTHON" "$DELIVERY/kit_timing/data_only.py" \
    --tree "$TREE" --receipt "$AUDIT_DIR/prepared_receipt.json" --manifest "$BASE_MANIFEST" --config "$CONFIG" \
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
`observed_max_grid` and `observed_grids`. The maximum is one actual grid selected
by `t*h*w`; equal volumes keep the first observed grid. Landscape `[32,20,26]`
and portrait `[32,26,20]` both pass; no synthetic `[32,26,26]` is reported. Require augmented rows on every rank in both arms; ON must
record a `c1-row-cpu` worker. The kit observes real nonzero augmentation calls,
checks every emitted image/video grid with `0 < t <= 32` and `0 < h*w <= 520`
(and positive spatial dimensions), and refuses missing
coverage. The success sidecar is published only after coverage, encoded-row,
budget and RNG checks pass; existing output paths are refused. Do not substitute convenient rows if coverage fails. The grid check
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
unchanged training/data binding. `REPLAY_OUT` must name a fresh scratch directory.
Set `REPLAY_METRICS` explicitly to the continuation’s chosen 03 value. The command
below chooses 03 OFF (`0`); use `1` in both the replay and continuation if 03 is ON.

```bash
date -u
REPLAY_OUT="$AUDIT_DIR/replay"
REPLAY_METRICS=0
TREE="$TREE" CONFIG="$CONFIG" PYTHON="$PYTHON" \
  RESUME_PIN="$RESUME_PIN" RESUME_CONFIG="${RESUME_CONFIG:-}" \
  PLAN="$AUDIT_DIR/plan.json" AUDIT_DIR="$AUDIT_DIR" OUT="$REPLAY_OUT" \
  REPLAY_METRICS="$REPLAY_METRICS" \
  bash "$DELIVERY/kit_profile/replay.sh"
```

The wrapper runs **OFF (`off1`), OFF (`off2`), then ON (`on`)** in that order and
calls `kit_timing/replay_compare.py`. It leaves 02 and fallback OFF. Each process
has a 3,600-s cap; failure or timeout stops the sequence with no automatic retry.
**Estimated total wall time is 50–75 minutes**, including three cold starts and
checkpoint restores. The supplied log shows 8.7 minutes from trainer launch to
attempt creation, then about 440 s to the first update: roughly 16 minutes per
leg before restore overhead, or about 48 minutes for three legs. The 3,600-s cap
per leg provides more than three times that observed startup-plus-update floor.
No production replay wall time has been measured here. Outputs are disposable;
the kit writes no production checkpoints, exports or training steps.

The comparator requires the same checkpoint, trainables, configuration, thread
settings, step and plan, plus the matching CPU audit. Its acceptance rule is:

1. If OFF repeats agree bitwise, ON must agree bitwise for every component,
   stream mean and first-step microstep loss on every rank.
2. If OFF repeats differ, CPU `encoded_row_sha256` and `row_draws` must still match.
   On each rank, concatenate components and stream means in sorted key order,
   then the ordered microstep losses. Define `D = max_i abs(OFF2_i−OFF1_i)` and
   `M = max_i max(abs(ON_i−OFF1_i), abs(ON_i−OFF2_i))`. Accept that rank iff
   `M <= 2 × D`; the multiplier is fixed at 2 before seeing ON. All four ranks
   must pass. This pooled bound lets ON fall outside an OFF interval without
   requiring it to lie between two random repeats for every scalar. It is a
   practical screening threshold, not a calibrated confidence interval from two
   repeats; a noisy component can mask smaller discrepancies. A zero `D` allows
   zero numerical difference only, and the bitwise branch above remains strict.
3. Reject nonfinite losses, changed rows, mismatched state/plan, missing CPU
   coverage or missing ON provenance. Keep `C1_CPU_PREFETCH=0` after any rejection.

`acceptance.json` retains per-rank OFF spread, `off_max_abs`, `on_max_abs`,
`multiplier=2`, `threshold=2*off_max_abs`, and ON differences after a completed
comparison. A structural validation error exits nonzero and blocks acceptance.
OFF nondeterminism alone is not an automatic refusal when the second rule passes.

## First continuation and r1_ops readouts

After the CPU audit, ordered replay and lane gate pass, N's first continuation
sets `C1_CPU_PREFETCH=1`, with 02 and fallback OFF and the same 03 value. Compare
against the disposable OFF replays at that continuation checkpoint. Historical
launch step 1 is not a matching plan or model state.

| Readout | Exact field and comparison |
|---|---|
| Proof that ON ran | Require `metrics_<attempt>.jsonl` → `ranks[r].performance.C1_CPU_PREFETCH == "1"` on every rank. Verify `C1_BATCH_METRICS` and `C1_DECODED_CACHE_MIB` too. With fallback OFF, r1_ops must not require `C1_CPU_PREFETCH_FALLBACK`; absence means `0`. The field appears only when some switch is nonzero; all-OFF records have no `performance` field. |
| Data wait and wall time | Read `ranks[r].data_seconds` and `ranks[r].wall_seconds`. Compare matched replay steps. For normal continuation monitoring, compare per-rank and slowest-rank medians/IQR over at least 20 updates per arm; those distributions are not matched-step numerical proofs. |
| First-step logged losses | First matching `metrics_<attempt>.jsonl` record: `ranks[r].components[key]` and `ranks[r].stream_means[stream]`. `inputs/first_step_<attempt>.json` also contains rank components. There is no top-level scalar `loss`. |
| Total microstep losses | Disposable `off1`, `off2`, `on` → `rank<r>/steps.json[0].first_step_micro_losses`, in order. |
| CPU equality | Each audited step's `encoded_row_sha256`, `row_draws`, `plan_sha256` and `global_rng_unchanged`. |

Pre-register these continuation kill rules before enabling 01:

1. At `start_step + 1`, compare each rank’s `components` and `stream_means` with
   `off1` and `off2` at that exact step, checkpoint and plan. Apply the same
   `loss_acceptance` rule to this logged subset: bitwise ON equality when the OFF
   subset is bitwise equal; otherwise `M <= 2 × D`, with `D` and `M` computed
   on that subset. Require zero row-draw/plan mismatches and zero nonfinite values.
   Any failure makes 01 OFF at the next checkpoint; quarantine the failed
   continuation for training admission. The disposable replay additionally checks
   every microstep loss, which the normal metrics record does not contain.
2. For each update, take the maximum `ranks[r].wall_seconds` across four ranks.
   Compute its median over continuation updates 2–21. It must be **strictly below**
   the same statistic over the first launch’s **last 20** completed updates:
   `continuation_median / launch_median < 1.00`. Equality or a larger value makes
   01 OFF at the next checkpoint. Missing ranks or fewer than 20 usable updates
   cannot pass. Use step wall time, excluding separate export/checkpoint timers.
3. Record the same 20-update slowest-rank `data_seconds` medians and their ratio;
   they diagnose overlap but do not override either kill rule. A smaller data wait
   with a wall ratio of `1.00` or more still fails.

The 1.00 wall ratio is an operational no-regression threshold, not a statistical
speedup claim. Host/GIL contention can increase whole-step wall time.

The optional **`C1_CPU_PREFETCH_FALLBACK=1`** requires 01 ON. It discards an
over-budget prepared group and performs the original synchronous main-thread
fetch/admission, with unchanged OFF outputs. It records cumulative
`ranks[r].cpu_prefetch.budget_fallback_groups` and its switch value in `performance`.
Frequent fallback adds duplicate CPU work and can erase gains. It stays OFF in
this acceptance experiment. It removes the prepared-group cap for the synchronous
fallback group, so monitor RSS; it does not impose a total-RAM limit.

## Lane command: build-21 two-rank gloo gate

The coordinator passed **31 tests in 880.158 s**, `OK`, `EXIT=0`, at
**2026-11-19 12:55:19 UTC**, including both GX tests and the asymmetric fallback
proof. The evidence is `work/round3_b21_gloo_by_coordinator.txt:55-60`.
All handed-over patch and trainer bytes remain unchanged. The command below is
retained for reproducibility; no new gloo run is required by these kit-only edits.
Sockets are unavailable in this sandbox.

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

## Review round 4: finding -> fix -> test

| Finding | Fix | Regression or evidence |
|---|---|---|
| 1 HIGH | Cap temporal size and spatial area independently of orientation; report actual grids and the maximum observed volume. | Real 72-row shapes at steps 100/101/102/200; 5/7/9/6 portraits; oversize temporal/spatial refusals. |
| 2 MEDIUM | Fixed per-rank maximum bound with multiplier 2; strict bitwise branch. | ON outside the OFF interval passes within the bound; boundary, over-bound, signed-zero and nonfinite controls. |
| 3 LOW | Plan writer calls trainer `prepared(cfg)` once and pins the merged receipt consumed by both arms. | CLI calls the trainer preparation path; real pointing encoding contains `aux_token_weights`; alignment survives. |
| 4 LOW | First-update subset uses the replay rule; 20-update wall ratio must be <1.00. | Documentation regression checks both references, the numeric threshold and checkpoint action. |
| 5 INFO | Record the completed 31-test coordinator gate. | Log reports 880.158 s, OK, EXIT=0, 12:55:19 UTC; patch hashes unchanged. |
| 6 INFO | Define replay output and explicit 03 choice. | Command regression rejects ambient-shell metrics selection. |
| 7 INFO | Missing fallback key means OFF. | Documentation regression checks that r1_ops does not require it. |
| 8 INFO | Estimate 50–75 minutes from the observed startup floor. | Runtime regression checks 8.7-minute startup and the corrected range. |
| 9 INFO | Publish sidecar only after success; refuse existing outputs; recheck worker/grid coverage at replay. | Failed real coverage cannot publish a sidecar; invalid replay coverage is refused. |
| 10 INFO | Standalone test mixes large fallback and small prefetched groups on one rank. | Exact rows, losses, gradients, optimizer state, counters and return to prefetch; deliberate all-fallback mutation fails. No trainer patch change. |

Exact commands and outputs are in REPORT and `out/evidence/round4_*`.
The mirrored production log has eight extra config lines: review lines 694–706
correspond to mirror lines 702–714. Tests also pin step numbers to avoid ambiguity.
