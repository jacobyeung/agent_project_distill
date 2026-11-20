exec 3>&1 1>&2
G=/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild; C=/scratch/jjyeung/orch_n30/cont_ops24_c/cap
cat > $G/BRIEF_R9.md <<'BRIEFEOF'
# Round 9 (cont_ops25): is the GT bound to the reader's frames? (CPU only)

Workspace: /scratch/jjyeung/orch_n30/cont_ops24_c/gbuild on trinity-2-28. Read REPORT5.md to REPORT8.md first. Write only in gbuild (new files only) and /scratch/jjyeung/orch_n30/cont_ops24_c/cap/score_bind (create it). Python /scratch/jjyeung/envs/p1cpu/bin/python. No ssh, Git, GPU, network, deletion or job submission; at most 8 cores and 20 GB RAM. Do not modify earlier deliveries. Append REPORT9.md (at most 120 lines) and SHA256SUMS9.

Why: 21 of 23 ARKit captures fail the camera rule in both orientations. The NPZ is self-consistent, but its masks are rendered from its own poses, so self-consistency cannot show that the NPZ poses belong to the RGB frames the reader decoded. An earlier measurement put the tower's pose within about 6 degrees on held-out ARKit. A binding fault fits the failures at least as well as a tower fault.

## 1. Image-content binding test (from the T1 capture, the one with the deployed raw proposals)
For each of the 38 GT captures and each anchor: for every GT instance bound to a queried object (the T1 join's bindings), the best IoU between its GT raster mask and any raw proposal of the same object call on the same frame (masks mapped to the GT grid exactly as the funnel join does). Repeat with the GT anchor index shifted by -2, -1, +1, +2 (GT masks of anchor k+s against proposals of reader frame k), and with the GT mask rotated 180 degrees, flipped horizontally, flipped vertically, and (portrait captures) rotated +-90 degrees with the documented portrait mapping. Also run it on the point arm's masks (cap/t2.gz), whose prompts come from a closed model looking at the reader's frames.
Report by dataset (ARKit, ScanNet, ScanNet++), and per capture: median same-frame best IoU, the best shift or transform and its median IoU, and how many captures change class (same-frame best vs some shift/transform better by > 0.2 median IoU). Separate captures that pass and fail the camera rule. If ARKit's same-frame overlap is low and recovers under a shift or transform, the GT is bound to other frames or another orientation than the reader's, and both the camera comparison and the S1 counts on ARKit are artefacts; say so plainly. If it never recovers, say that too.

## 2. Direct identity check
Where the ARKit GT carries timestamps, source frame ids, video ids or file names (NPZ members, gt/ adapter inputs, out2/GT.json, gt_staging metadata, the RGB manifest the reader uses, the T1/T2 capture's per-frame records), compare them with the reader's decode for each anchor (frame id, PNG name/hash, timestamp). Name the file that holds each field. State whether any check can hash-bind GT rows to the reader's RGB, and the result where it can.

## 3. Report ARKit apart
Re-state the T1 funnel (REPORT7 section 1-2 table) and the camera table (pass/moderate/gross) for ScanNet + ScanNet++ alone and for ARKit alone. ARKit objects are not counted in S1 until section 1 settles the binding: report them in their own row.

## Deliverable
REPORT9.md opening with the by-dataset binding table, then the identity check, then the two separated tables, then commands, input sha256s and runtime. Outputs cap/score_bind/BINDING_R9.{json,md}. Final message: the binding table in brief and one sentence: is ARKit's GT bound to the reader's frames?
BRIEFEOF
md5sum $G/BRIEF_R9.md
mkdir -p $C/score_bind
sed -e 's/R8/R9/g; s/r8/r9/g; s/c25_r9 --skip-git-check $W/c25_r9 --skip-git-check --writable-root \/scratch\/jjyeung\/orch_n30\/cont_ops24_c\/cap/; s/c25_r9b --skip-git-check $W/c25_r9b --skip-git-check --writable-root \/scratch\/jjyeung\/orch_n30\/cont_ops24_c\/cap/' /scratch/jjyeung/orch_n30/cont_ops25_c/r8_run.sh > /scratch/jjyeung/orch_n30/cont_ops25_c/r9_run.sh
cat /scratch/jjyeung/orch_n30/cont_ops25_c/r9_run.sh
tail -1 /scratch/jjyeung/orch_n30/cont_ops25_c/r8_run.log
tmux new-session -d -s c25_r9 "bash /scratch/jjyeung/orch_n30/cont_ops25_c/r9_run.sh > /scratch/jjyeung/orch_n30/cont_ops25_c/r9_run.log 2>&1"
sleep 2; tmux ls
ls -la $C/score_cam
cd / && tar czf - $G/REPORT8.md $C/score_cam/*.md >&3
