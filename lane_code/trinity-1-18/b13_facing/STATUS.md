# b13_facing STATUS (Devin lane 2 on trinity-1-18; session started 17:47Z, rotate by 23:30Z)
Goal: queue brief briefs/qs/13_facing_diag.md: classify why facing-away answers fail (classes a-f), one table per D0 milestone read, three alternative away renderings (built and validated, not admitted), and a one-page rule for the rows lane.

## Done (lane folder /scratch/jjyeung/orch_n30/b13_facing on trinity-1-18)
- Inputs, copied over IB:
  - work/in/t13/: cont_ops readk, evalx27 e193 merged away+forward (step 544), rows_rebuild3 d0_v5 + validator a41ba191.
  - work/in/revsi/x: ReVSI official999 step-544 return.
  - work/data/facing_v5.jsonl.gz (sha 2eaa8c25): 34,958 rows = 17,479 pairs. The brief's 33,985 is stale.
- Classifier: code/classify_away.py (sha 0d42a1f8). Tests: code/test_classify_away.py (sha 32ffc21f), 22 OK; f1f2 pair classes agree (74/41/35).
- Step-544 tables: out/m544/dev544.md (a12 b62 c38 d6 e32) and revsi544.md (a11 b12 c6 d0 e4). out/TREND.md holds all milestones (code/trend.py sha 01f9fe55).
- Milestone runner: code/run_milestone.sh STEP RETURN_ROOT [REVSI_B2048_JOURNAL] (sha fe1221d0). It reads <fam>/a0/results/budget_2048/0/items_*.jsonl, asserts budget 2048, uses RETURN_ROOT/ITEMS.jsonl as the --items cross-check, and writes out/m<STEP>/ plus TREND.md. I tested it on the step-544 data laid out like a read return (work/test_m): the summaries match out/m544 exactly.
- Renderings in out/renderings/. code/render_away.py (sha 6b469d44) now also builds composites, and its re-render of ra/rb/rc is byte-identical. All five files have 34,958 rows, 0 validator a41ba191 failures, 0 label differences and 0 re-derivation failures (CHECK_*.json, code/check_renderings.py sha 0f933c85).
  - ra 9d7080ae, rb 1ea55d30, rc 8ca80f0f
  - rab 79049965 = ra + rb; rac ba092c05 = ra + rc
- Finding: D0 v5's away rows never use ReVSI's only wording, "facing in the opposite direction of" (nor "facing directly away from"). The split is 5,889 turned away from / 5,809 facing away from / 5,781 with my back to.
- Rows-lane rule: out/RULE_rows_lane.md (sha 667f9c63; follows ORCH RULING 1416Z). Design record: distill_design/FACING_AWAY_DIAGNOSIS_20261116.md, plus an INDEX.md line.
- Mirror: trinity-1-3:/scratch/jjyeung/n30_mirror/b13_facing/ holds code, out/m544, all five renderings with manifests and checks, the RULE, TREND and STATUS. sha256 matches (out/MIRROR*_LOCAL/REMOTE.sha256).
- R0 check (ORCH NOTE 1307Z): 0 rows removed. All 1,049 scene keys of the facing rows (and so of every rendering, 34,958 rows) are in b10_reserve/in/stream_scenes/d0v5_vqa.txt, and R0_SCENES.json (f7c45817) proves every R0 capture absent from stream_d0v5_vqa.txt, aliases included. The renderings keep scene and frames unchanged.
- D0 m200 (read job 170320, f1f2 verdict STOP on F1 size; F2 toward delta fails): return copied over IB to work/in/d0_m200_raw/fetched/x (layout <fam>/a0/results/budget_2048/0/items_a0.jsonl). out/m200/dev200.md (sha 809453bd): a 11, b 1, c 0, d 17, e 121; all 11 class-a items use "facing in the opposite direction of". Rule 5 applies (d leads): no away rendering. Design record + INDEX line updated. Mirrored out/m200 + TREND to trinity-1-3 (out/MIRROR_m200_*.sha256 match).
- Events: RESULT 1227Z m544_classes, RESULT 1227Z checkpoint, RESULT renderings_composites, RESULT 1842Z m200_classes.

## In flight
- Nothing. The lane is finished: ORCH NOTE 1842Z (b13_facing) cancels the m400 table because D0 stopped at m200 (ORCH RULING 1842Z, cont_ops). The m200 class table is posted (RESULT 1842Z m200_classes).

## Next steps
- None owed. If ORCH later orders a table for another read, run `bash code/run_milestone.sh <STEP> <RETURN_ROOT> [REVSI_B2048_JOURNAL]` (copy pattern: work/scripts/pull_m200.sh).

## Rulings in force
- ORCH NOTE 1842Z: D0 stopped at m200; no m400 table; exit after the m200 table.
- ORCH RULING 1416Z (cont_ops): no official ReVSI or VSI-Bench read of a mid-leg D0 export.
- ORCH NOTE 1307Z: exclude R0 rooms from every stream (done, 0 removed).
- ORCH NOTE 1228Z: events only for questions, blockers, final results and rotate.

## Open questions / defaults
- None.

## Successor reads
This file; events/b13_facing/*_ORCH_*; briefs/b13_facing.md; briefs/qs/13_facing_diag.md; tools/LANE_RULES.md; out/RULE_rows_lane.md.
Updated 20261116T1843Z
