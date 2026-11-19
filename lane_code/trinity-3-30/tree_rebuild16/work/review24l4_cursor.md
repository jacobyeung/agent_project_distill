# Independent delta re-review (read-only, once) of TREE build 24l4 of lane tree_rebuild: the removal-order gate accepts one more pinned list (vehicle N; ORCH RULING 2216Z)

You review; you do not fix or design fixes. You are a different model family from the builder; this change touches an admission gate (which removal lists a launch may bind). You run once, read-only, on trinity-2-28. Report only verified problems, each with file:line and the command or reading that shows it. Your final message is the verdict.

## What changed
- Base: FINAL TREE 96ff9a03ae3be43972e060050ab411967e99dc312dc1380fe1c73435bbecebbf at `/scratch/jjyeung/orch_n30/tree_rebuild15_w24l/work/tree_r1_24l3` (you reviewed it: `/scratch/jjyeung/orch_n30/tr15_rev24l3/VERDICT.md`). Changed: `/scratch/jjyeung/orch_n30/tree_rebuild15_w24l/work/tree_r1`. Patch `../out/HOST24L4.patch`; report `../out/BUILD24L4_REPORT.md`; seal `../out/TREE24L4_SEAL.json`; per-file hashes `../out/UNCHANGED24L4.json`. Prompt `../prompts/build24l4.md`.
- Intent: `student_pilot/r1_launch22.validate_removals` accepted exactly the 12 pins of REMOVAL_ORDER (naming list d1454a44 last). The pointing stream admits 320 rows in two K1 held-out rooms; ORCH ruled they are removed by one more list (sha256 d21e374f39048c0e142680e0d3b26e5b2b774138747610c1fc4a00da0ec580e1). The gate now accepts the old order and exactly REMOVAL_ORDER[:-1] + (d21e374f, naming), nothing else.

## Verify
1. Only the files the report names differ from 96ff9a03 (recompute every sha256); the gate accepts exactly the two orders; any other 13th sha, position, duplicate or spec mismatch refuses by the old name; naming stays last and pinned.
2. Every other consumer of remove_files / removal_order (position-based use, union verification, coverage, room audit, receipts) works with the 13-list order; the new list removes only its listed keys and nothing from other streams.
3. Tests cover each case and fail on the base tree where they should.
4. Nothing else in admission, exclusions, routing, sampling, scoring or the host receipt changed.
5. Say what you did not check.

## Rules
Read-only. No ssh, network, GPU, Git, tmux, scheduler or another agent. Never list, search or grep on /home or /data*. Any process runs under nice -n 10, at most 8 threads, under 20 GB RAM; use `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B` to run the tree's tests if you need to. Write your verdict to `VERDICT.md` in this folder and nowhere else. First line: `GO`, `GO AFTER FIXES` (each fix MUST or SHOULD, with evidence) or `NO-GO`. Then at most 20 lines.
