# b14_k1towers removal candidates (delete nothing without an order)
- trinity-1-13 /dev/shm/jjyeung/b14 (14 GB at 13:22Z): geo_bakeoff_kit subset (runtime, work, assets/{moge2,*-src,downloads.jsonl}), k1_frames (19,200 PNGs, 5.28 GB), k1/run_tower_sam_2 slim (frame_indices + anchor_slots only), code/, K1 manifest, out/ (tower predictions), logs/, tmp/.
- trinity-1-18 /scratch/jjyeung/orch_n30/geo_k1/stage (slim towers 3.6 MB, file list, code copy).
- trinity-1-13 /dev/shm/jjyeung/b14/geo_bakeoff_kit/assets/moge2 (1.3 GB): MoGe-2 weights, removable once MoGe-2's pass is pulled to 1-18 (ORCH 1327Z: DA3 runs with a 20.8 GB peak instead).
- trinity-1-13 /dev/shm/jjyeung/b14/geo_bakeoff_kit/assets/da3 (6.3 GB): DA3 weights, after DA3's pass.
- trinity-3-30 /scratch/jjyeung/n30_mirror/b14_k1towers/geo_k1_mirror_1600Z.tar (539 MB, sha256 7b75239c...ededf): mirror of geo_k1 outputs. Written 15:52Z, after ORCH 1507Z capped new 3-30 /scratch writes at 100 MB; move it to trinity-1-3 /scratch/jjyeung/n30_mirror/ if 3-30 needs the room (the original stays on 1-18).
- trinity-1-18 /scratch/jjyeung/orch_n30/geo_k1 (about 0.8 GB: pred_cpu, pred_gpu, geom, harness/out_*, smoke, tmp): this lane's work tree; keep pred_gpu, out/, harness/out_merged_mdp.
