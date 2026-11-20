# Codex build cps24t1 of lane tree_rebuild: targeted test of the final kit's copier shutdown path (ORCH RULING 0239Z item 2), run once

You run once, on trinity-1-18; nobody answers questions. Writable: new folder `T=/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/cps24t1/` only (under 500 MB). Python: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B`. Time limit: 45 minutes.

## Target
The final launch kit `/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24e/out/kit_n_go` (seal c992c930; same b/ bytes as `w24e/work/build24/kits/n`, seal 240f8c17). Copy the kit into T and verify its SHA256SUMS before and after; test its bytes, never edited.

## Do
1. Read b/pc.sh, b/pc.py, b/ep.py, b/ep.sh, b/z.py, b/sr.py, b/o.py, job.sh and the decoded k/*.json the copier reads; describe the tk_live_finish path (trap on EXIT/TERM/USR1 -> pc.sh tk_live_finish -> ep.py ... -> o.py) and every external it calls.
2. Build a small fake job tree in T that looks like a run at exit: Q_ROOT with r/ (an m<step>/artifact.json export of a few KB with the files the copier expects, a checkpoint_<step>/complete.json, metrics, attempt/run JSON), live/ target dir standing in for x_22c714e1/o/<job>/live, h/o/<job>.steps; no admission, no training, no fixture population, no model.
3. Run the final kit's own pc.sh / pc.py / ep.py / z.py through tk_live_finish against it: upload in the copier's own dry or no-session mode if it has one (state the exact switch from code); if it has none, give it a sessions file that points to an unreachable local endpoint and show the copier records "export not uploaded" markers without crashing; never use real GCS sessions and never read or copy any sess.json. Also run the TERM and USR1 variants of the trap. Check: exit codes, done/marker files written (gcs_m<step>.json or .done, ckstop.json, live copies of logs and .steps), o.py output (o.tar, RESULT.json), and that nothing writes outside T.
4. Record every command, exit code and produced file in `T/RESULT.json`, and `T/REPORT.md` under 15 lines (line 1: PASS or FAIL with the failing step).

## Rules (restating build 21's)
No ssh, network (beyond a refused local connection), Orchard, GPU, Git, tmux, scheduler or other agents. Never list, search or grep on /home or /data*: read only named files there. Write only under T. No deletion. Every CPU process under `nice -n 10`, at most 4 threads, under 8 GB RAM. Do not change the kit, the tree, or any file outside T.
