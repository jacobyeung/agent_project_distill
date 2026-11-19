# Task sb_scalerev: independent review of a design record (tower-arm scale drift), read-only verdict, CPU only

Workspace: /scratch/jjyeung/orch_n30/sb_scalerev on trinity-1-18. You are a reviewer from another model family than the builder (Codex built the analysis). Write only REVIEW.md (and scratch scripts under work/) in this workspace. Never edit anything outside it.

## What to review
RECORD.md in this workspace is a copy of the design record /data2/jjyeung/agent_project_data/distill_design/TOWER_ARM_SCALE_DRIFT_20261119.md. Its evidence lives on this node's local disk (read-only to you):
- /scratch/jjyeung/orch_n30/sb_scale1/out/ (SCALE_REPORT.md, NEEDS.md, BARS_FROZEN.json, SCALE_RESULT.json) and code/scale_analysis.py
- /scratch/jjyeung/orch_n30/sb_scale2/out/ (ITEMS12.md/json, SCALE_DRIFT_REPORT.md, SCALE_DRIFT.json, BARS_FROZEN.json, CAPTURE_SCORES.json, DISTANCE_ROWS.json, VALIDATION.json) and code/ (scale_drift.py, test_scale_drift.py, finish_report.py)
Context: leg R1's H3 rule stopped training at step 400 because the tower arm's camera displacement on dev-S1 fell 0.73 points against step 544; the per-read scale = median(own depth / G3T depth) grew ~1.4% as the own point-depth head trained. Vehicle N starts from the step-400 export. The orchestrator asked for the fix, priced on K1 TRAINING captures only (never K1 held-out, R0-dev, dev-S1 items, BENCH, withheld rows).

## Check, in this order
1. Legality: do the scripts read or score any K1 held-out capture/row or any dev-S1/R0-dev/BENCH item? Confirm from code paths and the fold manifests (k1_split == train only). Any violation is a REJECT.
2. Numbers: every number in RECORD.md matches the outputs (cite file and field). Recompute at least two independently from the per-capture/per-room JSON with your own short script (e.g. combined G-A displacement point estimate, pooled served/GT per dataset). Report mismatches.
3. Method: room-disjoint folds; factors fit only on fit-half rooms; bars frozen before scores; MRA definition (ten thresholds 0.50..0.95, strict); the benchmark conversion (displacement one of five VSTI groups -> /5; distance one of eight VSI groups -> /8) against the cited official.py lines; whether one scale is applied once to both translations and lifted depth.
4. Reasoning: does the recommendation (no calibration factor; frozen donor depth path at N's init for the tower-arm scale; run the 1.04 GPU-h step-400 K1 forward to choose donor 400 vs 544) follow from the evidence? Are the rejections of options b, c, c', d, e fair? Is anything claimed that the evidence does not show (e.g. about dev-S1)? Is a better option missing?
## Output
REVIEW.md: verdict on the first line, one of ACCEPT / ACCEPT WITH FINDINGS / REJECT; then numbered findings, each with severity (blocking / should-fix / note), evidence (file:line or JSON field) and the exact wording change you propose for RECORD.md. Keep it under 120 lines.
## Standing rules and answers (read first; you will get no replies, so do not wait for any)
- You run on trinity-1-18 (CMU Trinity cluster), CPU only, no GPU, no network. Never ssh, never kill a process, never touch tmux sessions, no Git, no deletion outside your workspace.
- /home and /data* are an overloaded NFS server: never search, list recursively or bulk-read there. Read only files this prompt names, each once. /scratch is local disk: bounded `rg --files`/`find` under the directories named here is fine.
- Write only inside your workspace. Every path outside it that this prompt names is read-only to you (other lanes own it).
- Local-disk IO needs no approval. Ordinary failures: debug and rerun. The sandbox has no loopback sockets. Stay under 40 GB RAM per process. CPU manners (orchestrator order): at most 8 cores per job; start every heavy process with `nice -n 10` and OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 (torch.set_num_threads(8)); never run parallel worker pools above 8 processes.
- Legality: never invent a mapping, a manifest, a scene list or a proof. A missing input is reported by its exact name and expected location; the affected output says MISSING, never a guess.
- Every output JSON records sha256 of each input it rests on, and your report states the command that produced each number. Write a STATUS.md in the workspace after each stage (one paragraph) and a final report named in the task.
