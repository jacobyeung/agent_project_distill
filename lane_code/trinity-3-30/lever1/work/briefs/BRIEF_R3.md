# Build and run: DEV-POSE, per-frame transport ladder and all-pairs audit (rank 3 of the routed-reader plan)

You are a Codex builder on trinity-2-28. Work only inside `/scratch/jjyeung/orch_n30/lever1_c/r3/` (create it; code, tests, outputs, logs). Everything else is read-only. CPU only: no GPU, no ssh, no git, no kill, no network, no deletion outside your folder, no writes to /home or /data*. Search only inside the folders named here (no recursive search of /scratch, /home or /data*). Python: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B` (check it exists; if not, use the python the gbuild scripts use, see `cont_ops24_c/gbuild/setup.sh`). Keep the folder under 300 MB.

## Question
On step 544's 150 dev-S1 routed-distance items, does the relative pose between the two operands' frames cost distance, and how often do the operands use different frames?

## Inputs (all on this node, read-only)
- G = `/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild` (round 6-10 code: camera self-consistency and rigid alignment, T1 funnel join, scorer; read REPORT6.md, REPORT7.md, round7_common.py, the analyze_/render_ scripts, test_round*.py first).
- C = `/scratch/jjyeung/orch_n30/cont_ops24_c/cap`: `t1.gz` (sha256 fe9f10b875283b02e3c376b69c3601a4086312ac56ba77fbebedce4eb21e51b7; the trusted T1 capture: per call raw/linked/selected masks, final lift support, centroid, extent, the unrounded fitted box, camera/intrinsic/canvas/scale metadata per anchor, printed gaps), `score_t1/` (JOIN_T1.jsonl = item/object to GT instance join, CAMERA_SPLIT.json = per-capture rigid residuals, FUNNEL_T1.json = per-object stage).
- GT NPZ: `/scratch/jjyeung/orch_n30/cont_ops24_c/gt/{t1_gt,arkit_gt}/gt/*.npz` (38 captures: 15 ScanNet/ScanNet++, 23 ARKit; masks on the 32 anchors, full GT boxes, GT poses, bindings).
- Item manifest and labels: whatever G's scorer uses for the 150 items (find it from round7_common.py / the scorer; `/scratch/jjyeung/orch_n30/grd_funnel1/kit/rerun2/items544.json` is the rerun kit's copy). Rooms for bootstrap clustering come from the same source (46 physical rooms).
- The reader's own box fit and gap formula: reuse the exact functions G's code uses to recompute printed gaps (the reader source the T1 capture replayed; G's code or `/scratch/jjyeung/orch_n30/grd_funnel1/kit/rerun2/fixtures/` points to it). Do not re-implement them if an importable copy exists; if you must copy, add a test that your copy reproduces the T1 printed gaps.

## Ladder (72 items / 38 captures expected: items whose two operands both bind to a GT instance; report the actual count and why it differs)
- L0: the served printed gap (T1).
- L1: each operand's GT box carried into the served world through ONE anchor's served camera: anchor a = that operand's printed best frame in T1 (if its GT instance is not visible there, use the instance's largest-mask anchor and flag the operand). Transform the GT box (8 corners, or points sampled on it) by GT world -> GT camera of a (inverse GT pose) -> served world (served camera-to-world of a, served scale), refit the box exactly as the reader does (served gravity), then the reader's gap formula.
- L2: the GT gap: the same box fit and gap formula on the GT boxes in the GT world (GT gravity).
- Pose term = score(L2) - score(L1), routed-distance MRA x100 against the item label, raw and with served translations rescaled per capture (one similarity-scale factor per capture fitted between served and GT camera centres of the 32 anchors; record the fit).
- Split every cell by pair class: same-anchor (both operands' anchors equal) and different-anchor; and by dataset (ARKit vs ScanNet/ScanNet++).
- Report-only: printed longest box side against GT longest side by T1 stage (FUNNEL_T1); track count against visible GT instances if the NPZ names classes.

## All-pairs audit
Every pair of GT instances of 154 px or more (mask pixel count in the instance's largest anchor; if the gt_ceiling "154 px" rule is defined differently in G's code, use that definition and say so) in each of the 38 captures, each instance through its own largest anchor; L1 and L2 as above; audit pose term = 100 x (1 - MRA(L1 against L2 as reference)); same- vs different-anchor; by dataset. Weighted pose term = s x term_same + (1 - s) x term_diff, where s = share of ladder items whose two operands share their anchor. Also report the label-free form of the item ladder (L1 against L2) so the audit and the ladder compare.

## Statistics
Paired room bootstrap, 10,000 draws, seed 20261120, item-weighted (audit: cluster by room as well); 95% percentile intervals. Undefined draws are counted and omitted.

## Registered reading (state each verdict mechanically, before any interpretation)
1. Parity stop: stop (report, no interpretation) unless same-anchor pairs give a pose term of 0 +- 0.5 AND L2 lies within 10% of the label on 95% of items.
2. Different-anchor pairs 10 or more below same-anchor pairs with lower bound > 0, AND a weighted pose term >= 5: pose binds on dev.
3. Weighted pose term <= 2: pose costs no distance (the ARKit camera thread closes for distance).
4. An ARKit term >= 10 with lower bound > 0 reopens dense ARKit tower work.
Otherwise: undecided (middle band).

## Deliverables in /scratch/jjyeung/orch_n30/lever1_c/r3/
`devpose.py` (one CLI, all paths as arguments with the defaults above), `test_devpose.py` (synthetic: identical cameras give pose term 0; a known rotation on one anchor gives the expected gap change; the gap formula reproduces T1 printed gaps on at least 20 real items), `out/DEVPOSE.json` (every per-item and per-pair row, all cells and intervals, input sha256s), `out/REPORT_R3.md` (max 80 lines: counts, the ladder table L0/L1/L2 by pair class and dataset, raw and rescaled, the audit table, the weighted term, the four verdicts, what might not work), `out/SHA256SUMS`. Run the tests and the full run; it should take minutes. Final message: the verdict lines, the main table, file paths, and any deviation from this brief.
