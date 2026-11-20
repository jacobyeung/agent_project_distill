# Codex task 24h1 of lane tree_rebuild: hash table that ties the earlier 4-rank loop rehearsals to the launch kit (ORCH ANSWER 0210Z Condition A)

You run once, on trinity-1-18; nobody answers questions. Read-only everywhere except the new folder `O=/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/hash24h1/` (create it; under 20 MB). Python: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B`. Time limit: 30 minutes.

## Inputs (all under /scratch/jjyeung/orch_n30/tree_rebuild10_w)
- Launch kit 24m4d (tree C 0c7614c8): `w24c/out/kit_n_go` (GO variant, seal e54fc1b9), `w24c/work/build24/kits/n` (seal 0ef1e5e5), the tree tar inside the kit (`k/t_*.tar`) and `w24c/work/tree_r1` (seal 0c7614c8eff74201db275489af9c3fa11f3b418693a0239b793e6322685298de).
- Rehearsal run4 (log `w24/work/build24f/rehearsal_run4.log`: 8 of 9 rows PASS; "milestone export / local receipt / kit copier: NOT PROVED") and run5 (log `w24/work/build24f/rehearsal_run5.log`: kit copier PASS via gcs_m2.done; budget phase refused). Their roots, kit copies and trees are under `w24/work/build24f/` (find the root each runner used from the runner scripts `rehearsal_runner*.py`, `go_rehearsal*.sh`, `REHEARSAL_FIX*_REPORT.md`, `REHEARSAL_PATHS.md`, `SEQUENCE.json`, `KIT.json` in that folder; read files, do not search /home or /data*).

## Do
1. Identify, for run4 and run5, the exact kit directory and tree each executed (seal, path, the run's own record of it).
2. Define the train-loop file set from code, not by guess: every tree file the trainer imports from t.py/u.py through train() and the checkpoint/export/persistence path (at least student_pilot/carrier_c1*.py, launch_r1/*, launch_r2/persistence.py and whatever they import inside the tree), plus kit files b/pc.sh, b/pc.py, b/sr.py, b/z.py, b/u.py, b/t.py, b/e.sh and job.sh. Write how you derived it.
3. Table `O/LOOP_HASHES.md` and `O/LOOP_HASHES.json`: one row per file: sha256 in the launch kit/tree C, in run4's kit/tree, in run5's kit/tree, IDENTICAL or DIFFERS. For each DIFFERS, show the diff summary (lines changed, functions) in `O/DIFFS/`.
4. Name the run4 row that did not pass (kit copier) and whether run5 covered it with byte-identical copier files (pc.sh, pc.py, sr.py) to the launch kit.
5. `O/REPORT.md` under 12 lines: counts identical/differs, the run4 NOT PROVED row and its coverage, every differing file.

## Rules
Read-only outside O. No ssh, network, Orchard, GPU, Git, tmux, scheduler or other agents. Never list, search or grep on /home or /data*. nice -n 10, at most 4 threads, under 8 GB RAM. No deletion.
