# Codex task cb24m4e of lane tree_rebuild: planner closure of launch kit 24m4e against the REAL Orchard staging inventory (ORCH ANSWER 0210Z Condition B), read-only

You run once, on trinity-1-18; nobody answers questions. Read-only everywhere except the new folder `O=/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/cb24m4e/` (create it; under 50 MB). Python: `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B`. Time limit: 30 minutes. Another build (24m4f) may write `.../w24e/out/arm_routing.py` and package files at the same time; read the kits only (their SHA256SUMS must verify when you start and when you finish; say if not).

## Inputs (under /scratch/jjyeung/orch_n30/tree_rebuild10_w)
- Kits of build 24m4e: `w24e/out/kit_qd`, `w24e/out/kit_n_go`, `w24e/work/build24/kits/{q,n}` (seals in `w24e/out/BUILD24M4E_REPORT.md` line 1), `w24e/out/ORCHARD_COPIES_24M4E.json`, `w24e/out/STILL_MISSING_24M4E.md` if present.
- The real Orchard state, fetched by the lane: `work/pin_eac5f9f0/ORCHARD_U_LIST.txt` (size and name of every file in Orchard x_22c714e1/u/ at 02:19Z; names are sha256; includes eac5f9f0), `work/pin_eac5f9f0/d173555.log` and `d173555.steps` (the job log of discovery 173555 with kit qd 44aeea13: every archive id, joined file and frame shard it staged, "stage full done" 01:57:47Z, then mode r refused at the catalog), `work/pin_eac5f9f0/P_SHA256SUMS.txt` and `P_k_sizes.txt` (P's kit x_ee227714).
## Do
1. With the kits' own planner and resolver code (the closure functions pl.py/px.py use; no new resolution rules), enumerate every pin the planner asks for in mode r (kit qd and kit n) and in mode q (kits q, n and n_go), before preparation.
2. Resolve each against the real inventory: (a) a file in Orchard u/ by sha256 (and size where the kit records it); (b) a member of an archive or joined file that job 173555 staged, authenticated through the kit's own inventories (k/l.json and the archive member lists the kit carries); (c) a file listed in ORCHARD_COPIES_24M4E.json that the lane will copy from P's kit before submission (count these separately). Anything else is a MISS.
3. Write `O/CLOSURE.json` (every pin: field, sha256, mode, kit, resolution a/b/c or MISS) and `O/REPORT.md` under 12 lines: pin counts per mode and kit, the misses with their config fields, and whether any resolution relied on a Trinity fixture (it must not).

## Rules
Read-only outside O. No ssh, network, Orchard, GPU, Git, tmux, scheduler or other agents. Never list, search or grep on /home or /data*. nice -n 10, at most 4 threads, under 8 GB RAM. No deletion.
