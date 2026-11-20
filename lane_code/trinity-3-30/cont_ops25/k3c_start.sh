G=/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild
cat > $G/BRIEF_K3C.md <<'BRIEFEOF'
# Round K3c (cont_ops25): package arms A' and B (A replaced by T1's served cameras) and make it runnable

Same workspace, limits and write roots as gbuild/BRIEF_K3.md; read orchard_tower2x_b/REPORT_K3.md (K3 and K3b sections) first and keep what passed.
Decisions (binding):
1. Recipe: use the near-exact decode K3b found: Up and Down unrotated, Left rotated clockwise, upscale 2.5x with the filter that minimizes mean absolute error over all 320 anchors under that orientation rule (report the filter, per-capture mean and max error). It is not pixel-exact; that is accepted, and the control below measures its effect.
2. Arms: A' = the 32 anchors decoded by the recipe from lowres; B = 63 frames (anchors + 3/6 points) decoded by the same recipe. Arm A (served PNGs) is dropped because T1's capture already holds the served tower cameras for these ten captures (cap/t1.gz), which K2 showed reproducible.
3. Control (replaces the arm-A control): A' vs T1's served cameras, relative-rotation RMS difference per capture. Decode adequate if <= 1.0 deg on >= 8 of 10 captures; otherwise the verdict is void and the report says the decode, not coverage, moved the cameras.
4. Verdict (pre-registered thresholds unchanged, baseline A' instead of A): coverage confirmed if B moves >= 4 of 5 failing captures out of gross and cuts their median relative-rotation RMS by >= 50% vs A', with no reference capture rising by > 2 deg; refuted if <= 1 of 5 leaves gross and the median falls by < 20%; else partial. Also report each arm's class by the similarity fit and the rigid fit, scale ratio B/A', and gravity transport error, as K3 specified.
5. Budget: forecast must be <= 25 min (A'+B is about 24.4 by K3b's model; re-derive it); /project placement < 50 MB including the 630 lowres PNGs (~44.3 MB) and code.
6. Placement transport: the lane moves the placement bytes through one rate-limited governed stream, so build it as ONE archive file (place.tar, sha256 recorded) plus o_place.sh that reads that archive from stdin (`cat place.tar | ratelimit | ssh orchard 'bash -s' < ...` will not work, so: o_place.sh must be small and self-contained, read the archive from its stdin after a fixed header, or provide o_place_head.sh that the lane concatenates with the archive: `cat o_place_head.sh place.tar | ssh orchard 'bash -s'`). Document the exact byte-stream command and the expected byte count. Keep o_cpu.sh, o_check_sub.sh (the submit, with an empty-general-queue guard and --exclude=orchard-community-4 as the existing kits do) and o_fetch.sh small.
7. Tests: real-capture CPU dry run of the package on one capture (decode recipe on its anchors reproducing the reported per-capture error, B frame list, return schema) with a stub tower; the opaque-word scan over every Orchard-bound byte (archive members included); scorer tests for the new control.
Deliverable: append a K3c section to REPORT_K3.md with the lane commands in order (place via the byte stream, CPU check, submit, fetch, score), bytes, forecast, tests, SHA256SUMS_K3c. Final message: recipe filter and error, forecast, bytes, commands.
BRIEFEOF
md5sum $G/BRIEF_K3C.md
sed -e 's/BRIEF_K3B.md/BRIEF_K3C.md/g; s/c25_k3c/c25_k3d/g; s/K3B_DONE/K3C_DONE/' /scratch/jjyeung/orch_n30/cont_ops25_c/k3b_run.sh > /scratch/jjyeung/orch_n30/cont_ops25_c/k3c_run.sh
grep dispatch /scratch/jjyeung/orch_n30/cont_ops25_c/k3c_run.sh | head -1
tmux new-session -d -s c25_k3c "bash /scratch/jjyeung/orch_n30/cont_ops25_c/k3c_run.sh > /scratch/jjyeung/orch_n30/cont_ops25_c/k3c_run.log 2>&1"
sleep 2; tmux ls | grep c25
