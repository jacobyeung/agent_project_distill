GO

1. **H3 uses the correct level.** `level_for()` selects 99.29% at 200 and 99.82% at 400/600. The two-sided quantiles are `[0.00355, 0.99645]` and `[0.0009, 0.9991]`. The room grouping, seed 17, 10,000 draws, and ratio estimator are unchanged from the [old bootstrap](/scratch/jjyeung/orch_n30/cont_ops/work/r1route/out4s/score_r5_400.py:20); the [new bootstrap](/scratch/jjyeung/orch_n30/cont_ops/work/r1route/out4s/score_r5_look.py:23) adds quantiles from those same samples. [`compare()`](/scratch/jjyeung/orch_n30/cont_ops/work/r1route/out4s/score_r5_look.py:100) checks the upper endpoint, and [H3](/scratch/jjyeung/orch_n30/cont_ops/work/r1route/out4s/score_r5_look.py:165) consumes `harm_look`, retaining the camera-call condition.

   All 11 lines of the [new step-400 output](/scratch/jjyeung/orch_n30/cont_ops20/work/scoresAB_look400/scores.txt:1) exactly match the [old output](/scratch/jjyeung/orch_n30/cont_ops19/work/post_A10b/scoresAB/scores.txt:1) after removing only added look fields and labels. H3 remains `True`; camera displacement’s new upper endpoint is −0.070922 pp.

2. **The regression test behaves as requested.** Using the specified Python from `out4s`, with bytecode writes disabled:
   - Old scorer: exit 1 at assertion line 20; decisions `True/True/True`.
   - New scorer: exit 0, `PASS`; decisions `True/False/False`.

   The [test](/scratch/jjyeung/orch_n30/cont_ops/work/r1route/out4s/test_score_r5_look.py:11) stubs metrics but calls the real `compare()` and bootstrap. It exercises the per-type decision consumed by H3; it does **not** execute the final `score()['h3_stop']` aggregation.

3. **The export-pin check covers every non-544 step**, including 600, against the supplied package’s `READ_PLAN.json` ([lines 46–51](/scratch/jjyeung/orch_n30/cont_ops/work/r1route/out4s/score_r5_look.py:46)). No other STEP-dependent path is wrong for 600: [current loads](/scratch/jjyeung/orch_n30/cont_ops/work/r1route/out4s/score_r5_look.py:131) receive `STEP`, [journal validation](/scratch/jjyeung/orch_n30/cont_ops/work/r1route/out4s/score_r5_look.py:65) checks that step, and [baseline environment selection](/scratch/jjyeung/orch_n30/cont_ops/work/r1route/out4s/score_r5_look.py:61) correctly retains read 0 for current returns.

   **Deployment prerequisite:** the inspected [A binding](/scratch/jjyeung/orch_n30/cont_ops/work/r1route/out4s/A/READ_PLAN.json:31) and [B binding](/scratch/jjyeung/orch_n30/cont_ops/work/r1route/out4s/B/READ_PLAN.json:40) still pin step 400. Step-600 returns require matching step-600 packages; `--step 600` does not rebind them.

4. **CLI runs cannot silently choose a level.** [`--step` is required](/scratch/jjyeung/orch_n30/cont_ops/work/r1route/out4s/score_r5_look.py:172), accepts only 200/400/600, and resets both globals before scoring. Omitting it returned exit 2 with “required: --step.” Imported API use still has the module’s initial step-400 default.

No files were written.