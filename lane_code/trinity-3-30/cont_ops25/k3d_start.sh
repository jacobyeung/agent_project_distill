G=/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild
cat > $G/BRIEF_K3D.md <<'BRIEFEOF'
# Round K3d (cont_ops25): fix the K3c kit after its Orchard CPU check failed; same arms and verdict

Same workspace, limits and write roots as gbuild/BRIEF_K3.md and BRIEF_K3C.md; read orchard_tower2x_b/REPORT_K3.md (K3c section) first. Write a new kit directory gbuild/orchard_tower2x_c (do not modify orchard_tower2x_b; it is placed on Orchard as token ac794e028b16f and must stay byte-identical).

## What happened on Orchard (facts)
- CPU check 173681 (--mem=20G) FAILED after 5:09 with MaxRSS 20.97 GB; rerun 173683 with --mem=200G FAILED after 5:17 (MaxRSS 103 GB). Staging itself works; the prior passing CPU check of the parent kit used --mem=200G.
- A diagnostic wrapper (patched copy of 2.py in the job's /tmp root, traceback printed) showed: 2.py images() raises ValueError('E10') on the first frame: the raw RGB sha256 of the recipe-decoded frame (OpenCV bicubic in the Orchard environment) differs from the expected hash computed on trinity-2-28. 0.py then raises E29. The Orchard environment's OpenCV/PIL produce different bytes from the local ones.
- Both 0.py and 2.py swallow tracebacks and send job output to /dev/null, so the lane could not see E10 without patching.

## Fix (binding)
1. Decoding: keep the same recipe (OpenCV bicubic, Up/Down unrotated, Left clockwise, 2.5x). Replace the exact raw-hash requirement with recording: per frame, the raw hash, whether it equals the trinity-2-28 hash, and the library versions (cv2, PIL, numpy) used; keep the PNG input sha256 check (E-codes for corrupt or wrong inputs stay fatal). Report in the return the count of matching raw hashes. The A' vs T1 control (<= 1.0 deg on >= 8 of 10 captures) remains the decode-adequacy authority.
2. Memory: --mem=200G for both the CPU check and the GPU job (as the parent kit's jobs).
3. Diagnostics: write a short error log (exception type, E-code, the traceback's file:line list without source text, no payload paths beyond the token dir) to a small file in the token directory for both the CPU check and the GPU job, and keep stdout/stderr of sbatch in the token directory instead of /dev/null. Run the opaque-word scan over everything that can appear in those logs.
4. Placement without new bytes for frames: the new token directory must reuse the already-placed 8.tgz (44,374,984 bytes, sha256 in orchard_tower2x_b/3.json) by a hard link from /project/community/jjyeung/ac794e028b16f/8.tgz, verified by sha256 before use. Ship only the changed small files (0.py, 2.py, 1.json, 3.json, BATCH.sh and whatever else changed) in a small placement script (< 1 MB, single file, o_place.sh run as `ssh orchard 'bash -s' < o_place.sh`). The new token is a new opaque hex; job names a15_cot_ap + token.
5. Forecast <= 25 min; arms A' and B; verdict and scorer unchanged except the new decode fields.
6. Tests: the real-capture CPU dry run on one capture with a stub tower, now also with a deliberately different resize backend (simulate a hash mismatch) to show the job records and continues; scan; scorer tests.
Deliverable: REPORT_K3D.md in orchard_tower2x_c (at most 60 lines) with lane commands in order (place, CPU check, submit, fetch, score), bytes added (should be < 1 MB), forecast, tests, SHA256SUMS_K3D. Final message: commands and bytes.
BRIEFEOF
md5sum $G/BRIEF_K3D.md; mkdir -p $G/orchard_tower2x_c
sed -e 's/BRIEF_K3C.md/BRIEF_K3D.md/g; s/c25_k3d/c25_k3e/g; s/K3C_DONE/K3D_DONE/' /scratch/jjyeung/orch_n30/cont_ops25_c/k3c_run.sh > /scratch/jjyeung/orch_n30/cont_ops25_c/k3d_run.sh
grep dispatch /scratch/jjyeung/orch_n30/cont_ops25_c/k3d_run.sh | head -1
tmux new-session -d -s c25_k3d "bash /scratch/jjyeung/orch_n30/cont_ops25_c/k3d_run.sh > /scratch/jjyeung/orch_n30/cont_ops25_c/k3d_run.log 2>&1"
sleep 2; tmux ls | grep c25
