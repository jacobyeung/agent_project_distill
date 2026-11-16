# Trace pool v2 read: verdicts and the final-run decision (2026-11-08)

**Question.** Do the pool v2 traces (release 4c741e3, SPEC v3.9; 625 rows, 25 per type) make sense as plan-first, head-backed training targets, and which part of the 80,944-row build should tonight's final run use?

**Answer: GO-WITH-EXCLUSIONS.** Route only the three camera-motion types (12,060 build rows, about 9,900 after filters). The other 22 types answer DIRECT. T1-T4 (section 3) must land before the data freeze.

**Evidence.**
- Five reader reports covering all 625 rows of `/scratch/jjyeung/orch_cd/derivgen/review_pool_v2/POOL.jsonl` (trinity-2-18).
- My script checks on the same pool (the counts quoted below).
- `derivgen/out/scale_publish_02/MIX.md` and `NUMERIC_BIAS.json`.
- The routing builder and canary on branch p3-mixed-20261108: `/scratch/jjyeung/orch_cd/p3_build/work/c1mix/student_pilot/carrier_c1_routing.py` and `carrier_c1_canary.py`.
- COMPOSED_TRACES_COUNT_SIZE_ROOM, SELF_ROUTING_DESIGN, P3_ROUTING_IN_C1 and FINAL_RUN_EXPERIMENT_PLAN in this folder.

## 1. Verdicts

"Mism." counts the rows, of 25, whose answer differs from gt_answer. Outside counting and the distance types, gt_answer is the program's own output (absolute direction shows 0.0 signed bias over all 215 build rows). A 0 there therefore checks arithmetic, not labels. The camera labels are validated separately: the GT program scores 96 and 100 on VSTI items, against 43 and 56 for direct (SELF_ROUTING 1.3).

| Type | Verdict | Key reason | Mism. | Build rows | Tonight |
|---|---|---|---:|---:|---|
| camera_displacement | READY | One `<move>`; the answer is the printed distance | 0 | 4,226 | ROUTE |
| camera_movement_direction | FIX (filter) | `<move>`, four scores and an argmax are sound, but 7/25 labels rest on components of 0.05-0.23 m, below vertical motion or within 0.10 m of the runner-up; 3/25 substitute frames (13 to 14) | 0 | 4,849 | ROUTE after T2 (drops ~40%) |
| camera_rotation | READY (filter) | One `<turn>`; head error decides the sign at \|turn\| >= 165 deg (2/25) | 0 | 2,985 | ROUTE after T2 |
| object_rel_direction_medium | FIX | Ritual (section 2); 7/25 within 10 deg of a boundary, including +-135 | 0 | 4,115 | DIRECT |
| object_rel_direction_hard | FIX | Ritual; 4/25 within 6 deg of the front-left/front-right line; GT program 82 on benchmark items | 0 | 4,451 | DIRECT |
| relative_direction_object | FIX | Ritual; 7/25 near a boundary; faces "the object" (3363b664) | 0 | 2,494 | DIRECT |
| absolute_direction_object | FIX | Ritual accepts r = 5.92 (a 141 deg turn); \|v\| = 0.38 m decides a 134 deg answer | 0 | 215 | DIRECT |
| object_rel_direction_easy | FIX | Ritual; a -2 deg margin decides 535d55ac | 0 | 4,252 | DIRECT |
| absolute_distance_object | FIX | Answers run +4.8% high (median): visible-surface clicks cannot reach the mesh's nearest point. Also the ritual and 12 post-hoc "I selected" sentences per row; 2,777 tokens | 25 | 1,356 | DIRECT |
| object_abs_distance | FIX | Same generator and bias (max +9.6%); duplicates questions of the type above | 24 | 1,351 | DIRECT |
| relative_distance_object | FIX | 7,440 tokens median; re-clicks the reference object for every candidate; 23 exact repeat clicks and 272 click pairs under 15 px | 0 | 3,846 | DIRECT |
