# NF: CPU replay of the banked step-544 dev-S1 read with K5's second-order cameras (noise floor option B step 2; ORCH ANSWER 2026-11-21T19:02Z)
Every result line says that the replay holds the model's text fixed, so each difference is a lower bound.

## Inputs (sha256; replay_nf.py refuses a mismatch)
- The banked read is 170056's native arm: b04host3/b04_e2ehook/work/n13/ret/native/R1.json, sha256 75669a63…54c0. Its served geometry is in 84 npz files (list digest bc352a3f2c4115d5…). TASKS.jsonl is a2f3fdbd…; CAMERA_TASKS.jsonl is f59090ff….
- K5: 1.json 54aceb9f… and REFERENCE_K5.json b570a994…. K5's 84 captures equal the banked read's 84, and the anchors match on all 84.
- Code: geometry.py 93039228…, servers.py 3cd2e6db…, carrier_c1_routing.py 3fd0c722…, carrier_c1_decode.py e612a7c1…, evalpath/run.py 06cf9bd1….

## Reproduction
- All 450 camera calls re-serve byte-equal from the banked geometry, and all 450 scores and answers reproduce.
- The 834/842 figure belongs to another replay. R8 rebuilt the held-out reads 173258, 173412 and 173234, and those log the model's own pose head.

## Substitution
- (i) Direct: used where the banked cameras, K and scale equal A1's bit for bit.
- (ii) Relative change: used otherwise. Each frame becomes B'_k = B_k·inv(A1_k)·A2_k, and scale and K take the A2/A1 ratio. This form does not depend on the gravity frame.
- Expected: (i) on 0 captures and (ii) on all 52 camera captures, because the banked cameras match the rank 1 dump on 0 of 60. The run prints the actual counts.

## Scope
- Camera types are replayed. Each move or turn call is re-served with the reader's own server code.
  - Displacement and rotation copy the new printed value.
  - Direction re-applies the model's written option rule; a strict variant holds the direction answers.
  - The official evaluator scores the replay.
- Distance and room are UNMEASURED: their calls need tower depth and SAM 3 masks, and K5 returns only depth hashes. They are reported with an at-risk share, so option B cannot clear them.
- Rule-read types: the three camera types (H3 at steps 200 and 400; R1 stopped at 400 on displacement) and distance (the capped-reads outcome). Room is counted too, conservatively: its gate is registered, but no read was found.

## Statistics and rule
- Bootstrap: 10,000 draws, seed 20261120, item-weighted, over the 58 physical rooms.
- Rule: on a rule-read type, option A runs before the next rule on that type when |replay - banked| >= 0.5 points or more than 5% of the type's items change their printed value. Exactly 5% does not trigger it.
- Arm pairs: the default compares A1 with A2 (arms 0 and 1); `--a1 2 --a2 3` compares D1 with D2.

## Run (after K5's returns are extracted; about 3 s and 0.44 GB on CPU)
cd /scratch/jjyeung/orch_n30/lever6/nf/kit && nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B replay_nf.py --k5 /scratch/jjyeung/orch_n30/lever5/k5/ret/g0 /scratch/jjyeung/orch_n30/lever5/k5/ret/g1 --out /scratch/jjyeung/orch_n30/lever6/nf/out
Since K5 is rebuilt as k5b, the returns land wherever k5b's fetch writes them; pass those directories.

## Tests
8/8 pass in 11 s (TESTS_NF.log):
- A2 == A1 gives exactly zero difference and zero changed values, on both paths.
- A perturbation on one capture changes only that capture's items.
- The bootstrap equals round7_common.Bootstrap on a toy case.
- The rule holds at its edges.
SHA256SUMS_NF checks OK.

## Risk
Path (ii) assumes the history effect composes per frame on the right side. The count of captures bit-equal to A1 shows whether (i) was available.
