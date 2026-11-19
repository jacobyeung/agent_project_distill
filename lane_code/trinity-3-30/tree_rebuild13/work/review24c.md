# Independent review (read-only, once) of build 24c of lane tree_rebuild (kit-only: no bytecode or other job-time writes into the kit dir), changed files only, versus build 24b

You review; you do not fix or design fixes. You run once, read-only, on trinity-1-18; nobody answers questions. Report only verified problems, each with file:line or artifact path and the command or reading that shows it. Your final message is the verdict. This review gates N's launch.

## Context
Orchard job 173222 refused `R1_KIT_CONTENT_DIFFERS` at `launch_r1/build.py` verify(kit): the kit's own helpers (`/usr/bin/python3 b/l.py`, w.py, o.py in the decoded `k/j.json` payload) ran without `-B` and wrote `b/__pycache__` into the kit dir. Build 24c (prompt `/scratch/jjyeung/orch_n30/tree_rebuild10_w/prompts/build24c.md`, report `w24/out/BUILD24C_REPORT.md`, package `w24/out/tree_rebuild_b24c_*.tar`) fixes this kit-only on top of 24b (`w24/out/tree_rebuild_b24b_7d7a8858.tar`, tree e1e64652, kits n efe2a12e and q 13a54582).

## Check
1. Compare the 24b and 24c packages member by member in memory (tarfile; write nothing). The tree is byte-identical (e1e64652). List the changed kit files and generator files; anything beyond the bytecode/write fix and its tests is a finding.
2. In both kits, every Python start on the host and in the view (decoded j.sh, job.sh, q.sh, q1.sh, f.sh, launcher and worker scripts) carries -B or runs with PYTHONDONTWRITEBYTECODE=1. Nothing else writes into the kit dir during a job. The new test really runs the decoded helper sequence against a writable kit copy, and it fails on 24b's kit.
3. Decoded scans PASS; each kit dir equals its SHA256SUMS plus BUILD.json and SHA256SUMS.txt; the guard is unchanged (e397ea70...); resolver identity checks are unchanged; the upload diff is pinned and complete.
4. Say what you did not check.

## Rules
Read-only. No ssh, network, GPU, Git, tmux, scheduler or another agent. Never list, search or grep on /home or /data*. Any process runs under nice -n 10, at most 8 threads, under 20 GB RAM. Verdict, first line: `GO`, `GO AFTER FIXES` (each fix MUST or SHOULD, with evidence) or `NO-GO`. Then at most 20 lines.
