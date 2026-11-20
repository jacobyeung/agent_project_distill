# Codex task rt24h of lane tree_rebuild: rerun the two ground-(iii) test harnesses on the 24m4h launch kit bytes, run once

You run once, on trinity-1-18; nobody answers questions. Writable: `R=/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/rt24h/` only (under 1 GB). Python: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B`. Time limit: 45 minutes.

## Target
New launch kit `/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24h/out/kit_n_go` (seal 60d24119d5844d9b89376e340a5d2f0ef86ec9edd31247dd5af0bb60b936d19c; same b/ bytes as `w24h/work/build24/kits/n`, seal fec34c9d...). Versus the 24m4e kit (`w24e/out/kit_n_go`, c992c930) these b/ files changed: a.py, ep.py, i.py, pl.py, rb.py, rd.py, rg.py, z.py (plus k/c.json, k/n.json, k/p.json). Copy the kit into R and verify SHA256SUMS before and after; test its bytes, never edited; record every executable's sha256.

## Harnesses to rerun (read-only sources; copy what you need into R)
- `/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/cps24t1/` (REPORT.md, RESULT.json, run_*.py, trap_driver.sh, seccomp.bpf, execute_once.py, finalize.py): copier shutdown pc.sh tk_live_finish via EXIT/TERM/USR1 -> pc.py --final -> ep.py, z.py load/screen, ckstop/checkpoint tar, no-sessions marker, separate o.py test.
- `/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/tt24t2/` (REPORT.md, RESULT.json, case.py, cases/): h.py (valid init policy -> v.json; E85; R1_HOST_RECEIPT_INVALID), rd.py (publish; R1_ROUTING_SELECTION_MISSING; R1_ROUTING_JOB_ID_REQUIRED), rv.py review-wait branch (timeout, PASS match, identity mismatch, malformed, non-PASS, mode 0644), pc.py refused endpoint with a 0600 synthetic sessions file.

## Do
1. Point both harnesses at the new kit bytes and rerun every case unchanged in intent. If a case's fixture must change because the new bytes changed an interface (e.g. rd.py or ep.py publish lists, z.py screening), adapt the fixture only, state exactly what and why, never the kit.
2. Add one case for the new publication path (24m4h D): ep.py / the kit caller publishes materialization.json, receipt.json and refresh r.json to the output folder also when the routing build raises (use the 24m4h fixtures under w24h/work/build24m4h/ if present).
3. Write `R/RESULT.json` (commands, exit codes, executable sha256s, assertions) and `R/REPORT.md` under 15 lines: line 1 PASS or FAIL with the failing case; one line per file pc.sh, pc.py, ep.py, z.py, o.py, h.py, rd.py, rv.py with its verdict on the new bytes.

## Rules (restating build 21's)
No ssh, network (beyond a refused local connection), Orchard, GPU, Git, tmux, scheduler or other agents. Never list, search or grep on /home or /data*: read only named files there. Write only under R. No deletion. Every CPU process under `nice -n 10`, at most 4 threads, under 8 GB RAM. Never use or read any real sess.json, never real GCS. Do not change the kit, the tree, or any file outside R.
