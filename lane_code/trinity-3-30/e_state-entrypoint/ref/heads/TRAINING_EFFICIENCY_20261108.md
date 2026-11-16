# Training efficiency: why C1 and final-run training is slow, and what to change (2026-11-08)

**Question (USER 11-08, via the orchestrator).** Why is training slow, and can we make it more efficient? Scope: the C1 pose-only arms (trainer 6f974710), C1-r (trainer 9f6c1dee), and the final run (c1mix trainer in `p3_build/work/c1mix`, kit root f1a2c7e9, world 32). The final run's T0 is now 02:30Z (18:30 PT), with the data freeze at ~01:30Z (ORCH 1545Z), not 10-12 PT.

**Status.** Design review done 11-08 ~16:45Z (Claude Opus). It merges two independent reviews (A and B below) with my own code, log and CPU checks. loss_doctor's live step-time breakdown (ORCH 1537Z, due ~16:45Z) had not been published by 16:45Z; its newest event (1639Z) is the G1 hang root cause, cited below. The shares below therefore come from code and logs, and LT1 and LT3 replace them with measurements.

## Answer

A C1 step does about 1.06e15 FLOP per GPU (4 rows of ~2.65e14 each, including recompute) in 39.4 s. That is ~27 TFLOP/s, about 3% of an H100's bf16 peak. Three causes explain most of the gap, and a fourth would roughly double the final run's update time if the run launched as staged.

1. **Gated DeltaNet (24 of 32 layers) runs on HF's pure-torch fallback.** It costs an estimated 14-20 s of the 39.4 s C1 step (35-50%). Per-op Python and launch overhead binds the step, not FLOPs.
2. **Each rank decodes its next row on the training thread, using one CPU thread.** This costs 6.2-6.4 s of each C1 step (16%, measured) and 8.7 s of each C1-r step (18.5%).
3. **Legs waste time.** Pose-only legs stop at step 170 after ~2 h because their schedule is stale. Final-mode legs lose ~25-30 min of every 4-h allocation to serialized startup, USR1 at 3:40 and a fixed 900-s stop reserve. The total cost is ~3-12% of wall clock.
4. **(Final run, latent) The world-32 kit carries no NCCL EFA plugin.** NCCL would therefore run over TCP, which measured 2.7-3.0 GB/s busbw on these hosts, against 215-246 GB/s with the plugin a lane already built. FSDP traffic would cost ~24 s per microstep, or ~120 s per 5-microstep update, on top of the 70-130 s projection.

**Expected effect (estimates for LT1, LT3 and LT4 to confirm).** EFA, the fla fast path, prefetch (or 4 CPU threads) and the leg trims together would take the C1 step from 39 s to ~17-24 s. The final update would fall to ~35-60 s, against 70-130 s with EFA alone or ~190-250 s without it. That roughly doubles the updates per night.

## Evidence

### Measured step times (loss_doctor `data/check_*.out` M/O lines, de-duplicated by run and step)

| Run | Steps read | Median wall (s) | p95 (s) | Median data wait (s) | Checkpoint (s) | Export (s) |
|---|---|---|---|---|---|---|
| C1-a b343a001 | 1-267 | 39.37 | 43.46 | 6.39 | 40.3-44.1 | 84.9-86.2 |
| C1-b b343b001 | 1-153 | 39.57 | 43.10 | 6.42 | 41.5-44.5 | 69.2 |
| C1-c b343c001 | 1-217 | 38.95 | 42.69 | 6.17 | 35.6-38.9 | 60.0-85.0 |
| C1-r f60e3512 | 1-34 | 47.17 | 54.62 | 8.74 | none yet | none yet |

Rows are 4 per rank per step, 4,528-4,568 tokens each, at a peak of 39.75 GiB. No final-mode step exists yet: G1 failed or hung in all three attempts before completing step 1 (p3_build events 1555Z and 1635Z).

