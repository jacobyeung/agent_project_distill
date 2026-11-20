# Codex build 24k6 of lane tree_rebuild: rehearsal harness, third pass: twin-consistent bounded fixtures; run once

You run once, on trinity-1-18; nobody answers questions. Writable: new files under `L=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24k/` (never edit existing files; new names `*_k6*`) and the new rehearsal root `L/rehearsal_k6` only (kit build 24m4e runs at the same time in `.../w24e`: never write there or in `.../w24c`). New disk space under 3 GB. Read first: `L/rehearsal_k5b/REHEARSAL_K5A_REPORT.md`, `L/rehearsal_k5b/REFUSAL_DETAIL.json`, `L/rehearsal_k5b/canary.log`, `L/rehearsal_k5b/CHECK.json`, `L/rehearsal_k5/CAPACITY_CONSTRAINT.json`, `L/go_rehearsal_k5b.sh` and the k5a/k5b harness files it runs, and the binding prompts `/scratch/jjyeung/orch_n30/tree_rebuild10_w/prompts/build24k5.md`, `build24k4.md`. Python: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B`. Time limit: 70 minutes.

## Problem
k5b (kit n_go e54fc1b9, tree C) proved bounded populations, fixture closure, native routing and dbb2, then the canary refused `R1_TWIN_AUGMENTATION_REQUIRED` (REFUSAL_DETAIL.json): the 2,000-row VQA subset drops the direction half-turn twins (or their sources) that the config requires. k5's CAPACITY_CONSTRAINT.json also says the unchanged sampler needs 32,000 VQA rows.

## Do
1. Build bounded fixture subsets that keep every invariant the native code checks: twin pairs complete (each kept source with its twin, as the config's direction_twins binding expects), removal lists and census consistent, within the native 2,000-row Trinity scene limit. Supply them through the same fixture boundary; never raise or bypass a native limit, never change the kit, tree or a gate.
2. Before running, decide from source whether the native sampler's 32,000-VQA-row capacity can be met by any fixture within the 2,000-row scene limit (e.g. the limit applies to the scene-rebuild camera population only, not to VQA rows). Write the answer with file:line to `L/rehearsal_k6/CAPACITY_DECISION.md`. If it cannot, run anyway to the furthest stage and stop.
3. Run once: `go_rehearsal_k6.sh /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24c/out/kit_n_go L/rehearsal_k6` and record every row of the k5b report (PROVED / NOT PROVED with evidence). A refusal that is a kit defect (not a harness gap): stop and report it with log lines. No retry.
4. Report `L/REHEARSAL_K6_REPORT.md` under 20 lines (line 1: verdict, kit seal, furthest stage), `L/rehearsal_k6/CHECK.json`.

## Rules (restating build 21's)
No ssh, network, Orchard, GPU, Git, tmux, scheduler or other agents. Never list, search or grep on /home or /data*: read only named files there. Write only where allowed above. No deletion. Every CPU process under `nice -n 10`, at most 8 threads in total, under 20 GB RAM (`ulimit -v 19000000`). Do not change any kit, the tree, admission, legality, removals or the resolver identity checks.
