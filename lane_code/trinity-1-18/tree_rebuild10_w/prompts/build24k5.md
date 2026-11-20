# Codex build 24k5 of lane tree_rebuild: rehearsal harness fix for the scene-rebuild stage, run once more

You run once, on trinity-1-18; nobody answers questions. Writable: new files under `L=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24k/` (never edit existing files; new versions get new names, e.g. `*_k5.py`, `go_rehearsal_k5.sh`) and the new rehearsal root `L/rehearsal_k5` only (a kit build 24m4d runs at the same time in `.../w24c`: never write there). New disk space under 3 GB. Read first: `L/REHEARSAL_K4_REPORT.md`, `L/rehearsal_k4/CHECK.json`, `L/rehearsal_k4/SCENE_REFUSAL_DETAIL.json`, `L/rehearsal_k4/canary.log`, `L/rehearsal_k4/STAGES.json`, `L/rehearsal_k4/FIXTURE_CLOSURE.json`, the k4 harness files you find named in that report, and `/scratch/jjyeung/orch_n30/tree_rebuild10_w/prompts/build24k4.md` (binding). Python: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B`. Time limit: 80 minutes.

## Problem
Rehearsal k4 on kit n_go 36c32012 (tree C) passed fixture closure, native routing and dbb2, then the native scene-rebuild child refused the 16,000-row camera pin 38e7f9c5... at its Trinity 2,000-row limit, so nothing after it ran.

## Do
1. Supply the scene rebuild a fixture camera/routing population within the limit the native code enforces on this host, through the same fixture boundary the harness already uses (fixture bytes, authenticated pins in the planner source map); never raise or bypass the limit, never change the kit, the tree or a native gate. If the limit cannot be met without changing native code or the kit, stop and say exactly where and why.
2. Run once into `L/rehearsal_k5` on `/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24c/out/kit_n_go` and record every row of the k4 report (PROVED / NOT PROVED with evidence). If a stage refuses with a kit defect (not a harness gap), stop there and report it with the log lines; do not retry.
3. Report `L/REHEARSAL_K5_REPORT.md` under 20 lines (line 1: verdict and kit seal), `L/rehearsal_k5/CHECK.json`, and `L/go_rehearsal_k5.sh` that takes a kit path and a fresh root so the lane can rerun it on the fixed kit 24m4d.

## Rules (restating build 21's)
No ssh, network, Orchard, GPU, Git, tmux, scheduler or other agents. Never list, search or grep on /home or /data*: read only named files there. Write only where allowed above. No deletion. Every CPU process runs under `nice -n 10` with at most 8 threads in total, under 20 GB RAM (`ulimit -v 19000000`). Do not change any kit, the tree, admission, legality, removals or the resolver identity checks.
