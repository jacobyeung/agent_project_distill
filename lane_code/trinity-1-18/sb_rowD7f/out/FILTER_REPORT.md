# sb_rowD7f: direction half-turn twins with review fixes B1/B2 and builder rules R1-R3

Delivery PASS: 7,971 away twins (out/NEW_ROWS.jsonl) of 8,000 rebuilt; R3 dropped 29 pairs, R1 and R2 dropped none.
B1: each twin copies its source Step 1, Step 2 and final-line form; only the Step-3 line and the label change. The Step-1 line now predicts the clause at 0.500 (D7: 0.874).
B2: no twin carries `facing`; N files all 7,971 twins and sources under `direction` (0.6504 draws per row), so expected teaching draws are 5,184 toward and 5,184 away.

| Rule | Rows checked (twins / sources) | With local raster | Removed | Re-cited | Listed without raster |
|---|---|---:|---:|---:|---:|
| R1 placeholder name | 8,000 / 8,000 | not needed (text) | 0 | n/a | 0 |
| R2 cited frame under 1% | 8,000 / 8,000 | 769 (0 rows cite a frame) | 0 | 0 | 0 |
| R3 named object in no frame | 8,000 / 8,000 | 769 | 29 pairs | n/a | 7,231 |

R1 list (whole name, case-folded): ScanNet++ markers remove, split; ScanNet raw/NYU40 catch-alls structure, object(s), stuff, misc(ellaneous), unknown, unlabeled, void, other, otherprop, otherfurniture, otherstructure; ARKitScenes' 17 classes have none.
Bare wall/floor/ceiling are on the list because the direction family (93,370 v7 rows, 1,096 names) never names them; it does name qualified surfaces ("shower wall", "false ceiling"), which stay. 0 rows in the family match.
R2: no twin or source trace cites a frame (regex `frames? <n>`); every "frame" in the traces is part of a name ("blackboard frame"). Nothing was re-cited.
R3: a name is in a frame when its instances cover >=0.2% of the 240x320 raster (the store builders' visibility rule). Dropped: 16 pairs with 0 pixels in all 32 frames, 13 with slivers only.
Also listed unchanged: 45 rows whose raster lacks one of their names (e.g. "chair" where the raster says "office chair"); qids in FILTER.json raster_unverifiable.
Rasters: 367 local rasters indexed and matched to pins (296 K1 in gt_build/gt_build2, 71 codeB in rows_r1/work/codeB); 769 sources on 98 K1 captures have the row's exact 32 frame indices. No codeB capture is a source capture.
The 7,231 rows on the other 802 captures have no local raster and are listed by qid in out/NO_RASTER_QIDS.jsonl; the store's RASTERS_v3.json pins rasters that are not on this node. The 29 dropped pairs are in FILTER.json `dropped`.

Checks (all PASS, out/CHECKS.json): pack and validators on 7,971 rows and their sources; answers and truth on every row; unique qids and recomputed candidate_ids; each source used once.
Field diff: only qid, pool, answer, question, target and added candidate_id, label_row_keys, provenance; no frame changed; every filtered row is byte-identical to its rebuilt row.
scene_division_gate admits 7,971/7,971 per population; removal lists and u_union 0 hits; tiered rooms 0 unresolved and 0 K1/R0/withheld-80/dev-S1/BENCH v2 hits; wording distance <=0.10: 0 of 7,971.
Leak on the 15,942-row teaching subset: D7 leak test best 0.500 (Step-1 and final-line forms included); rev_leak7 worst majority 0.500, worst logistic regression 0.503, sampling-weighted 0.500.
As in review sb_drev7, only question length (0.651; it contains the clause) and combinations with the answer label (an output) exceed 0.5.
Dropped pairs leave together, so every opening and family stays 50/50 and no extra rebalancing was needed.
READ30.md: 30 full rows, read; inherited source grammar kept ("is the crocs", "to the left or the right of the counter").

Commands (prefix `nice -n 10 env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1`; interpreter /scratch/jjyeung/envs/p1cpu/bin/python, rebuild with `python`):
`cd d7 && python build_rows.py` (8,000 rebuilt rows); `python raster_index.py`; `python filter_rows.py` (all rule counts); `cd d7 && python verify_filtered.py`; `cd d7 && python leak_test_filtered.py`;
`cd rev && python rev_verify7.py`, then `python rev_rooms7.py` and `python rev_leak7.py` (reviewer copies, patches marked `sb_rowD7f`); `python read30.py`; `python finalize.py`.
Not done: N binding (augmented-store room certification, review finding 3), raster checks for rows whose frames are only on Orchard, training. No GPU, network, ssh or Git was used.
