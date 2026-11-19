# Independent review (read-only, once) of builds 24d and 24e of lane tree_rebuild: vehicle N's final launch kit, changed files only, versus build 24c

You review; you do not fix or design fixes. You run once, read-only, on trinity-1-18; nobody answers questions. Report only verified problems, each with file:line or artifact path and the command or reading that shows it. Your final message is the verdict. This review gates N's launch on 4 H100; prioritise problems that would let a wrong launch admit or a correct launch refuse.

## Context
Build 24c (`/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/out/tree_rebuild_b24c_22859833.tar`, tree e1e64652, kit q edb324ff, kit n bff6d42c) is reviewed (`codex_runs/*_tree_rebuild_rev24c`). Build 24d (prompt `prompts/build24d.md`, report `w24/out/BUILD24D_REPORT.md`, package `w24/out/tree_rebuild_b24d_*.tar`) fixes review 24's MUST: kit n must not require or stage P's post-step-400 files (step-414 complete.json, rng*.pt). It also runs the full decoded job-sequence look-ahead and adds `out/kit_n_go` (k/a.json GO=true) with a CPU rehearsal of the training path. Build 24e (prompt `prompts/build24e.md`, report `w24/out/BUILD24E_REPORT.md`, package `w24/out/tree_rebuild_b24e_*.tar`) fixes review 24c's f.sh and job.sh findings.

## Check
1. Compare 24c with 24e (and 24d) in memory (tarfile; write nothing). The tree is byte-identical (e1e64652). List every changed kit and generator file; anything beyond the three fixes and their tests is a finding.
2. Kit n requires, stages and hashes no member produced after P's step 400. The pinned small archive is authenticated without extracting such members. The RP checkpoint pointer is never resolved. Resolver identity checks are unchanged, and the failing-before test is real.
3. kit_n_go differs from kit n only in k/a.json GO=true and the reseal (SHA256SUMS.txt, BUILD.json). The CPU rehearsal actually ran the canary, v.json, t.py, u.py and torch.distributed.run on 4 gloo workers for 2 steps, with a fresh optimizer, counter 0 to 2 and finite losses. Say exactly what produces v.json.
4. The full decoded job-sequence look-ahead for q and n reaches the stages claimed, with stand-ins only at the GPU, weights, production stores and frame host.
5. f.sh validates before any mkdir or cd; job.sh makes the request absolute before cd. Decoded scans PASS; each kit dir equals its SHA256SUMS plus BUILD.json and SHA256SUMS.txt; the guard is unchanged (e397ea70); the upload diffs are pinned and complete.
6. Say what you did not check.

## Rules
Read-only. No ssh, network, GPU, Git, tmux, scheduler or another agent. Never list, search or grep on /home or /data*. Any process runs under nice -n 10, at most 8 threads, under 20 GB RAM. Verdict, first line: `GO`, `GO AFTER FIXES` (each fix MUST or SHOULD, with evidence) or `NO-GO`. Then at most 30 lines.
