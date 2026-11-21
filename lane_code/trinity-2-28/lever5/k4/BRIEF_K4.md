# Build K4: ARKit tower coverage kit, arms at 32/63/94 frames with a passable noise-floor control (lever5, ORDER 1620Z)

You are a build subagent of lane lever5 on trinity-2-28. Check `hostname -s` prints trinity-2-28; if it prints `trinity`, stop and report.

## Rules (binding)
- Read /home/jjyeung/.claude/CLAUDE.md section "Key Trinity Cluster Rules" and /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md; both bind you.
- Every stream over 20 MB that crosses the head node or touches /home or /data* registers with the IO governor first; Orchard calls keep the spacing LANE_RULES states. For you: run NO stream, NO ssh, NO Orchard call, NO Git, NO GPU, no deletion. If you need an Orchard fact, stop and list the exact read-only command in your final message; lever5 runs it.
- No recursive grep/find/du/ls -R on /home or /data*. Read named files only.
- Write only under /scratch/jjyeung/orch_n30/lever5/k4. Run Python with /scratch/jjyeung/envs/p1cpu/bin/python, OMP/MKL/OPENBLAS threads <= 8, nice -n 10.
- Orchard opacity: no project, benchmark, dataset, model or method word in any file shipped to Orchard or any job name; job names `a15_cot_ap` + new opaque hex token. Keep K3d's opaque-word scan and extend it to your files.

## Starting point (read first)
- K3d kit (ran as Orchard job 173701 on 11-20, COMPLETE): /scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/orchard_tower2x_c (REPORT_K3D.md, 0.py, 2.py, 9.py, score.py, build_k3d.py, dry_run_k3d.py, scan_k3d.py, test_k3d.py, o_*.sh, returned/, REFERENCE.json). Its briefs: gbuild/BRIEF_K2.md (pre-registration), BRIEF_K3.md, BRIEF_K3C.md, BRIEF_K3D.md. Its scored result: returned/scored/TOWER2X_B.md. The K2 kit (gbuild/orchard_tower2x) ran an arm A on the served manifest PNGs already on Orchard; find from it and the package how the served PNGs are read on Orchard.
- Frames: /scratch/jjyeung/orch_n30/cont_ops25_c/arkit_lowres (10 captures x 125 lowres_wide frames + .traj; INPUTS_K3.json lists per capture anchors (32), B (63) and C (94) frame indices; RECIPE_K3.json). Served PNGs: /scratch/jjyeung/devs1_frames.
- Do not modify anything outside lever5/k4. orchard_tower2x_b and _c are placed on Orchard and must stay byte-identical.

## What K4 must do
Same 10 captures, tower alone, same package environment and weights as K3d. Arms per capture:
1. A: the 32 served manifest PNGs exactly as T1 read them.
2. A2: A again, same input, same process settings (run-to-run repeat on identical input).
3. A': 32 anchors decoded from lowres_wide by the K3d recipe on Orchard (as 173701).
4. B': 63 frames, all decoded (as 173701's B).
5. C': 94 frames, all decoded (new).
6. Bm: the 32 served anchor PNGs + 31 decoded midpoints (63).
7. Cm: the 32 served anchor PNGs + 62 decoded thirds (94).
Poses are scored at the 32 anchors in every arm, against the same GT and T1 references K3d's scorer uses (REFERENCE.json).

Scorer (pre-registered; write it into the report before any run):
- Per capture and arm: rigid and similarity class (K3d rules), relative-rotation RMS, translation RMS, similarity scale and scale ratio vs A, gravity mean/max error.
- A vs T1 served cameras (should be ~identical; report it), A vs A2 (repeat deviation: rel-rot RMS deg and camera translation m), A vs A' (decode perturbation).
- Noise floor per capture = max(|A-A2|, |A-A'|) in rel-rot RMS vs GT.
- Coverage verdict at 63 (Bm) and 94 (Cm), each vs A: a gross capture is repaired if it leaves gross AND its rel-rot RMS falls by more than its noise floor. Confirm: >= 3/5 gross captures repaired at Cm or Bm, no reference capture rises by > 2 deg beyond its floor. Refute: <= 1/5 repaired at both. Else inconclusive. B'/C' vs A' reported the same way as a continuity check with 173701.
- The verdict is complete only if every arm returned for every capture; no void rule on A' (A' is now a measured perturbation, not a gate).

Job terms: Orchard general, 1 H100, --exclude=orchard-community-4, --mem=200G, 8 CPUs, --no-requeue, time limit at most 60 min (forecast it from K3d's measured 7.5 min for 20 arm runs, scaled by frames; keep forecast x1.5 under the limit). The Orchard CPU check (sbatch on general, no GPU) must run the REAL first unit: capture 1, arm A, the real tower forward on CPU in the package environment, finite outputs, poses converted, plus staging and decode of every shipped frame (hash recording as K3d). Error records, logs in token dir, sacct-based fetch, numeric filenames, as K3d.

Placement: new token dir; reuse the placed 8.tgz (44,374,984 B, sha e8072d95...) by hard link from /project/community/jjyeung/ac794e028b16f/8.tgz verified by sha256; ship the new C-only lowres PNGs (the 31 extra per capture not in 8.tgz; check which frames 8.tgz holds) and changed small files. New bytes on /project at most 50 MB total. o_place.sh as one transport file; if it exceeds 20 MB say so (lever5 then registers it with the IO governor; give the exact byte count and sha256).

Tests (local, CPU): scorer tests incl. synthetic noise-floor cases (repaired / not repaired / inconclusive); a real-capture dry run with a stub tower over all 7 arms on one capture; installer tests; opaque-word scan; shell syntax.

Deliverable: /scratch/jjyeung/orch_n30/lever5/k4/kit/REPORT_K4.md (<= 70 lines: arms, scorer rules, bytes added, forecast, tests run with results, lane commands in order: place, CPU check, submit, fetch, score), SHA256SUMS_K4, all kit files under k4/kit. Final message: commands, bytes, forecast, any Orchard fact you need. Do not narrate history in the report.
