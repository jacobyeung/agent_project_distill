# Codex task cov24c1 of lane tree_rebuild: coverage ground for each of the 22 files that differ from the loop rehearsals (ORCH RULING 0239Z), read-only

You run once, on trinity-1-18; nobody answers questions. Read-only everywhere except the new folder `O=/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/cov24c1/` (under 20 MB). Python: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B`. Time limit: 40 minutes.

## Inputs (under /scratch/jjyeung/orch_n30/tree_rebuild10_w)
- Ruling text (copy): the 22 files are tree launch_r1/entry.py, launch_r1/production_proof.py, student_pilot/r1_handover.py, student_pilot/r1_launch22.py and kit b/{a,cs,ep,h,i,o,pc,pl,px,rb,rd,rg,rv,sc,sv,z}.py, b/ep.sh, b/pc.sh. Each passes on exactly one ground: (i) the discovery job runs it for real: its bytes in kit qd equal its bytes in kit n / n_go (or the tree file is the same file) and the discovery path executes it (show the call site from job.sh / decoded k/j.json / x.py and which log line proves it ran); (ii) its first execution in the launch job comes before the preparation starts and a failure refuses by name (show the call order in job.sh / decoded k/j.json / entry.py); (iii) a targeted test on the final kit's bytes (the lane runs one for the copier shutdown path: pc.sh/pc.py/ep.py/z.py through tk_live_finish).
- Launch kits (24m4e = 24m4f): `w24e/out/kit_n_go`, `w24e/work/build24/kits/n`, `w24e/work/build24/kits/q`, discovery kit `w24e/out/kit_qd`; tree `w24c/work/tree_r1` (seal 0c7614c8; same in all kits' k/t_*.tar). Discovery run 173555's log (kit qd of 24m3): `work/pin_eac5f9f0/d173555.log`, `.steps`. Configs in k/*.json are base64-json (`json.loads(base64.b64decode(json.load(open(f))['payload']))`); k/j.json is the decoded staging shell.
- n_review1c's recompute: `/scratch/jjyeung/orch_n30/n_review/r1c/hc_out.json` and `hc.py` (read only); 24h1 `work/hash24h1/LOOP_HASHES.json`.

## Do
1. For each of the 22 files: sha256 in qd, q, n, n_go (and tree); where it runs in the discovery path (mode r, then q-mode preparation, census, h.py, rv.py until WAITING_REVIEW, exit trap) and in the launch path (job.sh order: staging, a.py q (preparation inside), d.py, h.py, rv.py wait, t.py -> u.py admit/train, pc.sh copier, o.py at exit); the first point in the launch job it executes, before or after the preparation start; whether a failure refuses by name.
2. Propose the ground (i), (ii) or (iii) per file with the evidence; for (i), note which discovery log line will prove execution (the current discovery job 173567 runs kit qd e7f32394 of 24m4e; say what line to look for). Mark every file that has none: they need a targeted test (iii) and say what minimal test would cover it.
3. State explicitly when r1_handover.py's check runs in the launch job relative to the preparation (call chain with file:line).
4. Write `O/COVERAGE.md` (table, one row per file) and `O/COVERAGE.json`, and `O/REPORT.md` under 12 lines.

## Rules
Read-only outside O. No ssh, network, Orchard, GPU, Git, tmux, scheduler or other agents. Never list, search or grep on /home or /data*. nice -n 10, at most 4 threads, under 8 GB RAM. No deletion.
