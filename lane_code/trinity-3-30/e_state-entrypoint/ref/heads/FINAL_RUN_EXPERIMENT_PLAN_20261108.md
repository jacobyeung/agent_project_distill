# Final-run experiment plan: what decides the training, and how to trust each answer (2026-11-08, Sun 05:00 PT)

This record lists the experiments that decide how the final run trains, how to run each so that its answer can be trusted, and what not to run. It merges three planner lenses (attribution, measurement, risk/cost) and settles their disagreements on the evidence cited. T0 is the Mon 08:00 PT design freeze; the final run starts Mon 21:30 PT from base on 32 AWS H100s, with one attempt. Once the orchestrator adopts §2, its rules are the pre-registration: log any change before the read it affects, and let a read that misses its deadline leave the default in place.

Sources: distill_design/{INDEX, C1R_G3T_DESIGN_MERGED, C1_TRAINER_REVIEW, C1_DELTA_REVIEW_6f974710, C1R_TRAINER_REVIEW, FRAME_LAYOUT_FP1, FOV_INTRINSICS_EXTRINSICS, ARKIT_ORIENTATION, MIX_STREAMS_DESIGN, C1_PLACEMENT_SWEEP}_20261108.md; /scratch/jjyeung/orch_cd/{ORCH_HANDOFF.md, head_acc/REPORT.md, toolprog/events/20261107T0946Z_OWN_HEAD_RESULT.md, p3_build/inbox/20261108T1229Z_ORCH_answer_owners.md, p3_build/inbox/20261108T1232Z_USER_8_more_gpus_mixed_test_daytime.md, p3_build/events/20261108T1235Z_p3_resumed_plan_and_question.md, heads_up/events/20261108T1239Z_blocker_governor_kit_push.md, train_review/C1R_V2_READY.md}; DATA_MAP.md (ARKit rows); the memory notes the brief lists.

**Schedule** (PT, AWS GPUs for distillation; read times depend on the queue)

| Window | GPUs | Runs |
|---|---|---|
| now to 08:30 Sun | 62 per the brief (the handoff says 48: confirm) | c1r cache until ~05:45; C1-a/b/c (24) and C1-r (8) start; spare GPUs go to V-SD generation if its kit is ready |
| 08:30 to 18:30 | 32, plus 8 for the mixed test by day (USER 12:32Z) | C1-a/b/c, C1-r, G1 |
| 18:30 Sun to 08:00 Mon | ~48 | C1-b, C1-r, G2 (32) once C1-a/c stop at m400 |
| from Mon 08:00 | 32, 21:30-08:00 only | the final run, Mon 21:30 |

Expected reads: C1 m400 15:00-18:30 Sun and m800 00:00-08:30 Mon; C1-r m400 16:00-22:00 Sun, with m800 probably after T0; G1 m200 17:00-21:00 Sun; G2 m100 21:00-00:00. Readouts and evals move to trinity-0-13 or Orchard when AWS is full.

## 1. Decisions the final run needs

| # | Decision | Default if the evidence is late | Deadline (PT) | Settled by |
|---|---|---|---|---|
| D1 | Which question families route through the heads; the rest get V-SD traces (base's own reasoning) | Route only camera displacement and movement, where f17's heads already beat its language answers on held-out rows (51.8 MRA / 83.2% vs 40.6 / 56.8%). Easy direction, obj-obj position, cam-obj absolute distance and route stay direct, because direct beats even the GT program there | first cut Sun 15:00, so it reaches derivgen and mixdata before G2's 17:00 data freeze; final at T0 | E3, E4 |
| D2 | Exposure: update count, one night or two, pose share, a pose-only opening phase | one night, flat 1:2:1:1 microsteps | early cut Sun 18:00 (G2's config); final T0-2 h | E4, E6, E7 |
| D3 | Camera-token placement | C1-b | Sun 18:00 (m400); confirm T0-2 h | E9 |
| D4 | G3T teacher package (C1-r) | in G2 unless C1-r shows harm; in the final run only on a speed GO | Sun 18:00 for G2; T0-2 h | E10 |
| D5 | Frame layout | duplicate (64 frames, 32 viewpoints) | Sun 17:00 | E11 |
| D6 | VQA anchor form and pointing share | V-SD; pointing as in MIX_STREAMS (65/35 visible/absent, one microstep in five) | G1 read ~21:00 Sun; G2 read ~02:00 Mon | E6, E7 |
| D7 | Heads in the build | gravity on; one FoV (pose slots 7:9) for unprojection and depth; a depth-supervised stream present; the scale loss dropped if nothing reads it | Sun 17:00 | E2 |
| D8 | The final run's step-100/200 canary bars | taken from G2's curve at equal steps | T0 | E7 |
| D9 | Eval path and headline protocol | the official 5,130, run once on the pre-registered final checkpoint | parity before G1's VQA read; official-path slice by T0 | E5 |
