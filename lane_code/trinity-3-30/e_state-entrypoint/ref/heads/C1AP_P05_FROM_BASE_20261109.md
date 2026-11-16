# C1-a-p: P0.5 partner frames from base fail the pre-registered fail-fast at step 100

## Question
loss_doctor ranked P0.5 partner frames from base (lever a) as the only input-side lever that adds motion information. f17, C1-a and T0 all sit at ~20 deg translation direction and ~49% centre error on the 312-scene harness, and short paths carry the excess (spec: `/scratch/jjyeung/orch_cd/loss_doctor/events/20261109T0333Z_direction_levers_ranked_test.md`). C1-a-sw had already tested the mid-run switch to partners and lost at m400. This test trains on partners from base instead.

## Design (pre-registered before launch)
- **Arm C1-a-p** uses C1-a's pose-only recipe from base with the same rows in the same order. It runs frame_layout paired at a 0.5 s gap, fla kernels and world 8, and it stops at m200.
  - Kit aws_c1p (root ap/a5ed51d1), config k/a14f07c2.json, identity 24cf2af7. Trainer a981cd79, run runs/e2f0a001.
  - Prep receipt arm/e2f0a001/receipt.json (sha 62b7b259).
- **Control** is C1-a (ap/7b30c1e4/runs/b343a001) at matched steps on the same rows.
- **Fail-fast rule:** stop at step 100 if C1-a-p's training pose loss over steps 81-100 is above 1.10x C1-a's on the identical rows (lt5.py method).
- **Primary bar at m200:** direction ≤ 0.85x, centre ≤ 0.85x and rotation ≤ 1.10x C1-a m200, paired per scene with 90% bootstrap CIs.
- **Kit changes for arm a only:**
  - The fla overlay ebe69df8 loads for training modes.
  - The planned p95 step time drops from 60 to 40 s. This changes only the leg-length plan; the LR horizon (800 steps) and the recipe stay identical to C1-a.
  - Partners' overlay holds 6,400 rows, so the run could not pass step 200.

## Run
TRAIN 119067 started at 04:00Z and trained from 04:14Z at ~17 s/step, with no hang. Every step used real partners: the step audit shows fallback 0 for both d3 and d2. The first resume save landed at step 86, and m100 exported (m100/artifact.json, sha dd68abc8). The pre-registered rule then fired, so I cancelled the job at step ~108 (04:50Z).

## Result: fail-fast fires
Mean online pose loss per step on the same rows (`h8/ff_aws.py`, output `h8/ff_read_119067.txt` under heads_up work/):

| steps | C1-a-p | C1-a | rel |
|---|---|---|---|
| 1-10 | 1.557 | 1.421 | 1.096 |
| 11-20 | 1.155 | 1.278 | 0.903 |
| 21-30 | 1.111 | 1.234 | 0.900 |
| 31-40 | 1.290 | 0.989 | 1.304 |
| 41-50 | 1.158 | 0.818 | 1.416 |
