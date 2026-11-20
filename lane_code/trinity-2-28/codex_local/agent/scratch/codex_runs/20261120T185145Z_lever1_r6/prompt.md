# Build and run: LEDGER, CPU re-analysis of existing captures (rank 6 of the routed-reader plan)

You are a Codex builder on trinity-2-28. Work only inside `/scratch/jjyeung/orch_n30/lever1_c/r6/`. Everything else is read-only. CPU only; no ssh, git, network, GPU, kill, deletion outside r6/, and no reads or writes of /home or /data*. Reads of this node's local /scratch are approved at any volume; do not stop to ask about them. Python `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B`, nice 10, at most 8 processes. Nothing is rerun; no model is called.

## Questions
1. Do the 2026-11-20 step-544 results on the 150 dev-S1 routed-distance items split by dataset (ARKit against ScanNet/ScanNet++): T2 (closed-model points), the 64-frame ground arm, and the T1 funnel stages?
2. What does a no-information constant score beside the served 58.6 on the 150: a per-class constant gap (one constant per object-name pair class, or per class of the object pair as the items define it; fit leave-one-room-out on the other rooms of the 150 so no item sees its own label; also report the global median constant)?
3. Does the routed answer beat the direct one on the R0-dev twins: the twin ledger at steps 200 and 400, metres first, feet apart.

## Inputs
- Captures and scores (2-28): `/scratch/jjyeung/orch_n30/cont_ops24_c/cap/` (t1.gz, t2.gz, dense.gz; score_t1/, score_t2/, score_dense/, score_conf/ with per-item JSON; JOIN_T1.jsonl, FUNNEL_T1.json, CAMERA_SPLIT.json) and the scorer/code in `/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/` (round7_common.py and the analyze_ scripts); items/labels/rooms as that scorer uses them (`/scratch/jjyeung/orch_n30/grd_funnel1/kit/rerun2/items544.json` is a copy).
- Trace corpus copy `/scratch/jjyeung/orch_n30/lever1_c/r6/in/corpus/` (from trinity-3-30 /scratch/jjyeung/orch_n30/corpus/stage2): `INDEX.jsonl`, `meta/`, `tool/`, and reads `673bc60f_s200_R0dev_D580_173243` (routed, step 200), `673bc60f_s200_devS1R0_direct_a8102c3207b` (direct, step 200), `6ed2c7aa_s400_R0dev_D580_173241` (routed, step 400), `6ed2c7aa_s400_devS1R0_direct_a59a7bff4c4` (direct, step 400), `469ddece_s544_R0dev_D580_seg*` (step 544, for reference). Find in INDEX.jsonl/meta how D580 defines the 290 template items, their twins (82 twin pairs at step 400 per the plan) and units (metres vs feet), and how the corpus scores items; use the corpus scorer if it exists, else the MRA definition the scores in INDEX.jsonl reproduce (state the reproduction).
- Plan lines (this rank): `/scratch/jjyeung/orch_n30/lever1_c/r6/in/PLAN_RANK6.md`.

## Registered reading (mechanical, before interpretation)
- Routed minus direct >= 0 at both steps and no gate above always-route by 2: the route table stays (distance routed with the "not seen" fallback, camera routed, room direct). "Gate" = any per-item route/fallback gate the reads record (e.g. route only when the call returns a box; fallback on "not seen"); compare each gate's score with always-route on the same items.
- Below -3 at step 400: report that the forced-direct diagnostic read (20 min) is triggered (do not run it).
- A parser review is spent only on those two triggers: say whether either fired.
- Dataset splits stay hypotheses: label them so.
Statistics: paired room bootstrap, 10,000 draws, seed 20261120, 95% intervals; metres and feet items separately and together.

## Deliverables in r6/
`ledger.py` (one CLI), a small test (the scorer reproduces 58.6 on the 150 and the INDEX.jsonl mean scores of the four corpus reads), `out/LEDGER.json`, `out/REPORT_R6.md` (max 70 lines: the dataset split table for T1/T2/dense with intervals, the constant cells, the twin ledger at 200 and 400 with gates, the verdicts), `out/SHA256SUMS`. Final message: verdict lines, main tables, files, deviations.
