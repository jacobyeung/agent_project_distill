exec 3>&1 1>&2
G=/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild; C=/scratch/jjyeung/orch_n30/cont_ops24_c/cap
cat > $G/BRIEF_K2.md <<'BRIEFEOF'
# Round K2 (cont_ops25): kit for one Orchard GPU job: the tower alone on ten ARKit captures at served 32 frames vs 64 frames (build + CPU dry run only)

Workspace: /scratch/jjyeung/orch_n30/cont_ops24_c/gbuild on trinity-2-28. Read REPORT3.md (the 64-frame dense kit, orchard_dense*/), REPORT5-REPORT9 (camera rule, CAMERA_SPLIT, CAPTURE_FEATURES_R8, binding), and the existing Orchard kits (orchard_t1/, orchard_dense/, orchard_dense_r3/, their o_place.sh, o_cpu.sh, BATCH and submit scripts) first. Write only new files: gbuild/orchard_tower2x/ and /scratch/jjyeung/orch_n30/cont_ops24_c/cap/score_tower2x. Python /scratch/jjyeung/envs/p1cpu/bin/python. No ssh, Git, GPU, network, deletion or submission: you build, test and dry-run; the lane submits.

## Purpose and pre-registered reading (do not change)
Round 8: sparse coverage separates the tower's gross camera failures from passing captures better than orientation (translation-gap share > 1 m: AUC 0.858 gross/pass; native portrait 0.517; GT up direction is upright on >= 84% of anchors in every ARKit capture). ARKit captures get 32 tower frames; ScanNet and ScanNet++ mostly 64. The job tests whether doubling the tower's frames repairs the ARKit cameras.
- Failing (5): arkitscenes/41069054, 41291643, 42899535, 45663051 (portrait), 47332598 (portrait).
- Reference (5): arkitscenes/41159782 and 45261332 (pass), 43828368, 43649603, 44358634 (lowest-error moderate).
- Arm A: the served 32 frames, exactly as the deployed reader feeds the tower (tower_read.py path, NATIVE_INPUT native_square_pad_bicubic_1024_bilinear_518_v1). Arm B: 64 frames = the same 32 anchors plus the 32 nested intermediate frames the dense package already holds for these captures (DENSE_MANIFEST.json); if a capture lacks them, say so and substitute nothing.
- Arm C (only if possible without copying new frames to Orchard): 96 frames = arm B plus 32 more nested frames, if the dense package or another of our existing Orchard package dirs already holds decodable frames for these captures (list what exists; never add frames to /project). If not possible, say exactly why and skip arm C.
- Also answer: for a served read, where would ARKit's extra tower frames come from (which manifest, package or source decode produces 64 frames for ScanNet/ScanNet++ today, and why ARKit gets 32)? Cite files.
- Score: the tower's cameras on the 32 GT anchors only, against the GT c2w, with the round-5 rigid rule (no scale; pass = trans RMS <= 0.10 m and every anchor rotation <= 5 deg; gross = rigid rotation max > 60 deg) and REPORT6's relative errors over all anchor pairs.
- Control: arm A must reproduce the T1 capture's served cameras for these captures (relative rotation RMS difference <= 0.5 deg per capture); if not, the job's tower path differs from the served one and the result is void.
- Confirm coverage: arm B moves >= 4 of 5 failing captures out of gross and cuts their median relative-rotation RMS by >= 50%, while no reference capture's relative-rotation RMS rises by > 2 deg. Refute: <= 1 of 5 leaves gross and the median falls by < 20%. Anything else is partial.

## Build
1. A job script that loads the frozen tower exactly as the served path does (reuse the dense or T1 package's payload and weights on Orchard by hard link or path; no new weights, no new environment), runs arms A, B (and C if possible) per capture, and writes per capture the decoded metric cameras (c2w for every input frame plus the anchor binding), scale, gravity, input frame ids and PNG sha256s, timings and peak memory, into one small JSON return (< 5 MB) plus a receipt. One GPU, at most 30 minutes wall clock including model load; estimate it from the dense job's timings and refuse to start if the estimate exceeds 25 minutes.
2. Placement and submission scripts in the pattern of the existing kits: adds < 2 MB to /project (code only; frames and weights are the existing package's), job name a15_cot_ap + opaque hex, no project, benchmark, dataset, model or method word in any name, path, argument, comment or log line on Orchard (capture ids go inside the input JSON under opaque keys).
3. A scorer (cap/score_tower2x) that reads the return, applies the rule above, writes TOWER2X.{json,md} with the control, per-capture classes and residuals for both arms, and the confirm/refute verdict.
4. Tests: CPU dry run of the job script on one capture with a stub tower (shapes, binding, return schema), scorer unit tests on synthetic cameras including the control and both verdicts, the name/word scan over every Orchard-bound file.

## Deliverable
REPORT_K2.md (at most 80 lines): files, what the lane runs (place, CPU check, submit, fetch, score) with exact commands, /project bytes added, runtime estimate, test results, SHA256SUMS_K2. Final message: the run commands and the estimate.
BRIEFEOF
md5sum $G/BRIEF_K2.md
mkdir -p $C/score_tower2x $G/orchard_tower2x
sed -e 's/BRIEF_R9/BRIEF_K2/g; s/c25_r9/c25_k2/g; s/R9_DONE/K2_DONE/' /scratch/jjyeung/orch_n30/cont_ops25_c/r9_run.sh > /scratch/jjyeung/orch_n30/cont_ops25_c/k2_run.sh
grep -n dispatch /scratch/jjyeung/orch_n30/cont_ops25_c/k2_run.sh
tmux new-session -d -s c25_k2 "bash /scratch/jjyeung/orch_n30/cont_ops25_c/k2_run.sh > /scratch/jjyeung/orch_n30/cont_ops25_c/k2_run.log 2>&1"
sleep 2; tmux ls
ls -la $C/score_bind
cd / && tar czf - $G/REPORT9.md $C/score_bind/*.md >&3
