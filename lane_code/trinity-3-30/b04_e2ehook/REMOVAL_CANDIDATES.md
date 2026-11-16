# b04_e2ehook removal candidates (the user deletes; nothing here is removed by the lane)
- trinity-1-13 /dev/shm/jjyeung/b04 (7.9 GB: devs1_frames, k1/g3t, host code copy, scipy overlay, parity restore + results) after the parity read is recorded.
- trinity-1-13 /dev/shm/jjyeung/exports/m544_heads (2.76 GB: heads.pt, artifact.json, full_weights.json) when no lane reads step 544 there (h1_headsft shares it).
- trinity-1-18 /scratch/jjyeung/orch_n30/b04_e2ehook_m544h (2.76 GB extracted heads) and /scratch/jjyeung/orch_n30/b04host (code copy, ~0.9 GB + CPU restore) after the read.
- trinity-3-30 L/work/eat1/code_v4..v7, run4..run7 (small), L/parity_kit/test_runs (902 MB pytest basetemps and Codex run dirs), L/work/tmp (490 MB TMPDIR leftovers), L/work/eat1 run dirs (605 MB in total, keep out/proofs/EAT1_DYNAMIC_v6) — all re-creatable; trinity-3-30 /scratch is at its floor (ORCH 1903Z).
- trinity-3-30 /dev/shm/jjyeung_b04 (<1 MB staging of lift_price scripts; copies live on 1-18 and in the 1-3 mirror).
- trinity-1-18 /scratch/jjyeung/orch_n30/b04host3 (1.5 GB code copy + restore_118 symlinks + lift_price 262 MB) after the parity read is recorded.
