# /scratch inputs for ranks 1-3: inventory (lever1, 2026-11-20 16:55-17:00Z; du on node-local disks)
trinity-1-3: /scratch/jjyeung does not exist any more (disk 80% used by others). Every 1-3 copy named in records is gone: K1_GT_RASTERS_259.tar mirror, gt_audit (K1_LABELS_CORRECTED d781ac7b original), reader_r1, tower_redecide.
trinity-3-30: 83 GB free (95%), below the 100-200 GB floor: no new mirrors here.
trinity-2-28: 2.9 TB free. Already holds k1/{g3t,own_170235,run_convert_2,run_tower_sam_2} (8.0 GB), k1_frames (5.0 GB), devs1_frames, orch_cd/dose_pool, cont_ops24_c/gt (38 distance GT NPZ), cont_ops24_c/cap and cont_ops25_c (T1/T2/dense captures; also on GCS and 1-18 n30_mirror).

## Held only on trinity-1-18 (MB) - the archive set
| path under /scratch/jjyeung | MB | role |
|---|---|---|
| orch_n30/e3_geom/work/harness (code + out per-capture JSON) | 1,125 | E3 harness (rank 2) |
| orch_n30/k1_ops3/work/e3gd (reviewed-guard GD harness, PER_ITEM, FITS) | 1,147 | rank 2 parity 75.05/91.99 |
| orch_n30/k1_ops3/work/codex_arkit_timing (K1 manifest) | 32 | E3 MANIFEST |
| orch_n30/gt_build/out/K1_GT_RASTERS_259.tar (+ RASTERS_SHA256SUMS, PIN_CHECK.tsv) | 1,227 | K1 GT masks |
| n30_mirror/gt_audit (mirror_gt_audit_1651Z.tar + tree; K1_LABELS_CORRECTED) | 148 | corrected labels |
| orch_n30/geo_k1 (geom, pred_gpu da3/pi3x/moge2, harness) | 2,317 | rank 2 tower row (3-30 holds a 539 MB 11-16 tar) |
| orch_n30/sb_kbox4/out/sb_kbox4.tar (+ code) | 685 | box-ladder harness, train parity 56.8/74.0 |
| orch_n30/b04host3 (lift_price harness, bestspread) | 2,690 | lift variants |
| orch_cd/leg_s1_tree | 11 | E3 TREE |
| orch_cd/evalx/.../native_package_s24_05/sources (converter geometry.py only) | <50 | E3 CONVERTER |
| core total | ~9,400 | |
Not in the set: k1/m544_parts (20,584; step-544 stop export, also on Orchard), k1_ops3/work/partb build dirs (65,939; rebuildable), b10_reserve (90,292).
