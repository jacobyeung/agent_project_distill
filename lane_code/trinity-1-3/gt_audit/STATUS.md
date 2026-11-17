# gt_audit STATUS (lane on trinity-1-3) — 20261117T1655Z, DONE, lane exits
Brief: evaluation-set audit for the ScanNet++ v1 half-extent box defect. RESULT posted: events/gt_audit/20261117T1652Z_RESULT_eval_gt_half_extent_audit.md. Record: distill_design/EVAL_GT_HALF_EXTENT_AUDIT_20261117.md (+ INDEX.md line 231; INDEX backup work/INDEX_before_gt_audit.md).

## Findings
- Only K1 carries the defect: distance labels = box_grid_5cm on K1 GT raster boxes at stored length (replay 1,253/1,253); ScanNet++ boxes 313 half / 88 unknown / 0 full (75 scenes half); ScanNet 4/25 scenes half; ARKit full. Held-out 109/216, train 639/1,037 rows inflated.
- Clean: dev-S1 (released VSI-590K labels, full-box; H1-0 canonical within 10%, 0.200 vs 0.197 released), R0-dev (mesh-vertex labels), VSTI rel dev (0 half of 8,402 boxes), official kit (no extent code).
- K1 rescored: E3 deployed 68.0->75.1, GT 77.9->92.0; kill rows stands (.213->.250); refit unaffected (mask IoU); scale head still misses (66.90 vs 66.94); bestspread -0.6 -> -2.9 [-6.8,-0.0]; GEO distance winner G3T -> Pi3X (corrected) / DA3 (drop).
- R1: no gate correction or drop list (out/audit/R1_GATE_DROP_LISTS.json d6dbc80f); ORCH ruling owed on the distance-tower pin.

## Files (trinity-1-3 /scratch/jjyeung/orch_n30/gt_audit)
- out/audit/ deliverables + SHA256SUMS: k1/K1_LABELS_CORRECTED.jsonl d781ac7b, k1/K1_DROP_AFFECTED.tsv 720b7d70, k1/K1_RESCORE.json, k1/K1_KILL_RESCORE.json, k1/GEO_decide_{stored,corrected,drop}.json, k1/LIFT_*, k1/SCALEHEAD_*, devs1/DEVS1_LABEL_CHECK.jsonl a50accf7, r0dev/R0_CONVENTION_*, vsti/VSTI_BOX_CHECK.json.
- work/codeA/ scripts (k1_audit, k1_rescore, k1_kill_rescore, geo_rescore, lift_rescore, scalehead_rescore, r0_convention, vsti_check, build_out); audit.py is a read-only copy of rows_r1 build D (a3edbcc0).
- Inputs pulled from trinity-1-18 over IB: work/k1, work/k1b, work/k1r (296 K1 rasters, sha = pins). Removal candidates: REMOVAL_CANDIDATES.md.
- Mirror: trinity-1-18 /scratch/jjyeung/n30_mirror/gt_audit/mirror_gt_audit_1651Z.tar sha256 d6de7e42edf9efb4b0c761ae7e45310a4cc3fc9d73356737b00e95fd422c5cb8 (equal both ends; extracted there).

## Notes
- rm_guard queued two of this lane's shell commands in /home/jjyeung/agent_project/agent/PENDING_USER_COMMANDS.md (a remote survey script and the first RESULT heredoc); neither needs running.
- Nothing running: tmux sessions gtaudit_k1, gtaudit_r0, gtaudit_vsti, gtaudit_vsti2 exited after their runs. Nothing owed.
