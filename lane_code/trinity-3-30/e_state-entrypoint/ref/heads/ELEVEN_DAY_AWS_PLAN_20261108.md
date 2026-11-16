# Eleven-day AWS plan: one final lineage on 32 H100s, faster updates, more rows (Sun 11-08 to Thu 11-19)

Merged design, 2026-11-08 17:02Z (Sun 09:02 PT), for orchestrator session cdb578de. It merges three independent designers (D1 throughput, D2 two-stage specialists, D3 data and evacuation) with the TRAINING_EFFICIENCY review that landed at 16:50Z, and it settles their disagreements on evidence. Times are PT (UTC-8). Every update time below is an estimate: no final-mode step has run yet.

Sources: distill_design/{INDEX, TRAINING_EFFICIENCY, FINAL_RUN_EXPERIMENT_PLAN, FRAME_DENSITY_DESIGN, POSE_DATA_AT_SCALE_PLAN, POSE_DATA_SOURCES, POSE_ACCURACY_BRIDGE, TRACE_POOL_V2_READ, TRACE_POOL_V3, MIX_STREAMS_DESIGN, SOTA_TARGETS, HEADS_COVERAGE_ALL_BENCHMARKS, DYNAMIC_SCENES_VLA_PLAN, UNIFIED_SPATIAL_BENCHMARK_DESIGN, C1_PLACEMENT_SWEEP, C1R_LAUNCH}_20261108.md; /scratch/jjyeung/orch_cd/ on 2-18: ORCH_HANDOFF.md (GPU windows, lines 320-327), aws_evac/{STATUS,SKIPPED}.md, p3_build/inbox/20261108T{1545Z,1605Z,1611Z,1618Z,1627Z}, p3_build/events/20261108T1635Z, heads_up/events/20261108T1614Z, c1r/events/20261108T1625Z, posedata/events/20261108T1604Z, partners/events/20261108T1616Z, streams2/events/20261108T1618Z, evalx/events/20261108T1622Z, loss_doctor/events/20261108T{1604Z,1639Z}; p3_build/work/c1mix/student_pilot/{carrier_c1_sweep.py:47-80, decoupled_v.py:195-199, carrier_c1_run.py:903-912}; agent/scratch/devin_lanes/posedata/BRIEF.md; memory notes aws-down-until-user-says, gpu-numbers-are-shared-totals, aws-to-mind-evac-route, orchard-cluster-ruling, stack-best-then-ablate, higher-signal-takes-gpus.

## Question
User, 11-08: "hopefully we can train on more, quicker :) only 11 more days with these h100s before we are back to just orchard and trinity". The orchestrator asked for a day-by-day calendar to Thu 11-19 (GPUs, runs, owners, the gate each read decides), the GPU split rule, the data each night needs, evacuation and Orchard portability, and the three biggest risks with their early signals.

## Answer
1. **The budget is larger than two designers assumed.** At ~16:10Z the user said "monday 12pm start using 32 gpus again for training" (ORCH_HANDOFF.md:327; memory aws-down-until-user-says; p3_build inbox 1611Z). Distillation therefore trains on 32 AWS GPUs day and night from Mon 12:00, after 48 tonight. That is ~8,500 GPU-h to Thu 11-19 08:00, about 1.7x the weekday-nights plan that D1 and D2 priced (~5,100). The nights-only calendar remains the fallback.
2. **Train one final lineage on all 32 GPUs.** Resume binds the config (schedule, steps, mix), the preparation, the trainer commit and the world size (TRAINING_EFFICIENCY, "Resume binding"). Each daily change point (CP) therefore starts a new run that is warm-started from the previous run's last state. This chain of runs is the model we ship. It has no planned restart from a specialist and no parallel variant.
3. **Faster: EFA first, then the GDN kernel, then the loader.** The world-32 kit has no EFA NCCL plugin, and NCCL over TCP would add ~120 s to every update. EFA, the fla overlay (if LT1 and LT2 pass), prefetch or 4 OMP threads, and the leg trims should cut an update from 70-130 s to ~35-60 s. That means ~13-23K updates by Wed 11-18 instead of ~6-11K, against ~4-7K in the nights-only plan. D1's (P,X) update slicing waits for LT5, the rows-versus-updates test.
4. **More rows: the small streams limit us, not pose.** Every update reads 32 rows of each non-pose stream. At 13-23K updates, today's routing (~9,900 rows), pointing (17,408) and VQA (23,883) streams would each repeat 18-73 times. Grow every non-pose stream to at least 150K rows by Wed 11-11 and pose to at least 0.56M rows (A3, built from ScanNet `.sens` and the ARKit extras) by Tue 11-10. Hold each non-pose stream to 4 epochs and pose to 2 at the projected update count.
5. **Learning-rate schedule.** Night 1 anneals to 0 by Mon 07:45 (TRAINING_EFFICIENCY T0-5), so Monday's decision reads see an annealed checkpoint. From CP1 the lineage runs at constant LR (warmup-stable-decay). One decay run covers Tue 11-17 18:00 to Wed 11-18 18:00, and the headline reads run once, Wed 19:00 to Thu 08:00, on the same 32 GPUs.
6. **Evacuation.** aws_evac must move its floor from the 10% rule (4.98 TB) to the user's 1 TB free on Mind. It copies AWS-only items first, including every frame tar that training rows reference: SKIPPED.md skips the 238 GB A1 bank as rebuildable, but nobody has shown that a rebuild reproduces the pinned PNG sha256s. The lineage's newest state goes to GCS twice a day, and every AWS-only item is verified on Mind by Mon 11-16.
7. **Orchard portability.** The final-mode trainer accepts world 8, 16 or 32 only (carrier_c1_sweep.py `recipe_for`), and no c1mix state has ever been resharded. The daily warm-start path must therefore also reshard to world 4 or 8. Stage a 0.3-0.6 TB kit in GCS and drill it on Orchard advanced on Tue 11-10.

## Budget and update counts

| Window (PT) | Distillation AWS GPUs | GPU-h | Elsewhere |
|---|---|---|---|
| Sun 08:30-18:30 | 32; main's idle share only for checkpointable work | ~320 | Orchard: advanced 4 + general 1 (shared with main, ~120 GPU-h/day), preempt up to 32 when its queue allows (training only). Trinity: 0-13 (8 x 48 GB, normal priority) |
| Sun 18:30-Mon 08:00 | 48 | ~650 | same |
| Mon 08:00-12:00 | 0 (CPU jobs only, at most 90 min each, cores sized to need) | 0 | Orchard and 0-13 read night 1 |
| Mon 12:00-Thu 11-19 08:00 | 32 day and night; main may lend more on 30-min notice | ~7,550 | same |
| Total | | ~8,500 | |

| Final update time | Updates per day | Updates T0 to Wed 11-18 18:00 (~221 h of steps after leg overhead) |
|---|---|---|
