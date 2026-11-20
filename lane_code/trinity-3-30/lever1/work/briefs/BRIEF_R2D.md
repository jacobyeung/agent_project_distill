# Build and run: deployable box and centre rules on K1 under deployed masks (rank 2 follow-up, CPU)

Continue in `/scratch/jjyeung/orch_n30/lever1_c/r2/` with the served-reader factorial code `k1x.py` (rules of `/scratch/jjyeung/orch_n30/lever1_c/BRIEF_R2.md`, `BRIEF_R2B.md`, `BRIEF_R2C.md` hold; reads of this node's local /scratch are approved at any volume, do not stop to ask about them). Write new outputs to `r2/out_box/`; leave `r2/out/` untouched. CPU only, nice 10, at most 16 processes.

## Question
The served program reaches 79.07 with all ground truth against E3's 91.99; the voted box adds +8.47 at GT geometry and the oracle centre +6.06 at deployed masks. Do deployable versions of a better box/centre rule pay under deployed masks and served geometry?

## Arms (deployed masks, served geometry G3T x own scale, reader guard, deployed selector; all else as the served reader)
- base: the served best-frame rule (`lift_bestspread` + `min_area_box`), = cell deployed/G3T/G3T/own (held-out 63.29).
- (a) multi-frame fused centre and box: the E3 program's rule (its fusion/vote over grounded frames as in `/scratch/jjyeung/orch_n30/e3_geom/work/harness` and the ladder's frozen `vote_10_3_best`; use the frozen constants as they are, fit nothing).
- (b) robust centre: median of the lifted mask points over all grounded frames as the box centre, with the served extent (lengths and axes of the served box).
- (c) the served rule restricted to frames above a mask-area floor: the best frame chosen only among frames whose mask area is at least F pixels; F is chosen on K1 TRAIN only (grid {0, 50, 100, 200, 400, 800} pixels at the served grid, room-grouped 5-fold CV on train), then frozen and applied once to held-out.
Same for GT masks as a report-only column.

## Registered reading (written in the plan record before any number is read; mechanical)
A rule that gains 3 or more MRA points over base on K1 held-out (216 rows / 48 rooms) with the paired room-bootstrap lower bound above 0 (10,000 draws, seed 20261120), and that does not lose on the dev items once rank 1's depth dump exists, becomes a reader change to propose; otherwise the box rule waits for better masks too. Report the train 1,012-row figures beside, ARKit vs ScanNet/ScanNet++, and the dev-item check as "pending rank 1 dump".
Deliver `out_box/BOX.json`, `out_box/REPORT_BOX.md` (max 50 lines), `out_box/SHA256SUMS`, a test that arm base reproduces the cell deployed/G3T/G3T/own per row. Final message: the table, verdicts, files.
