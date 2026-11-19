# Independent review (read-only, once) of build 23c of lane tree_rebuild (kit-only GPU guard fix), changed files only, versus build 23b

You review; you do not fix or design fixes. You run once, read-only, on trinity-1-18; nobody answers questions. Report only verified problems, each with file:line or artifact path and the command or reading that shows it. Your final message is the verdict.

## Context
Orchard job 173076 (kit q bb04241c, 1 GPU, preempt, orchard-community-2) passed resolver and all staging, then died at `RuntimeError: E42` from the kit's GPU guard `q/b/g.py`: `if not torch.cuda.is_available() or torch.cuda.get_device_properties(0).total_memory < 80*(1<<30)`. An 80 GB H100 reports about 79.6 GiB. Build 23c (prompt `/scratch/jjyeung/orch_n30/tree_rebuild10_w/prompts/build23c.md`, report `w23/out/BUILD23C_REPORT.md`, package `w23/out/tree_rebuild_b23c_*.tar`) changes the guard kit-only on top of build 23b (`w23/out/tree_rebuild_b23b_cb24ed96.tar`, tree 5b349b18, kit q 67ce92f6).

## Check
1. Compare the 23b and 23c packages member by member in memory (tarfile; write nothing). The sealed tree must be byte-identical (5b349b18); list every changed kit file; anything beyond the guard, its diagnostics, NVIDIA binds (if changed) and tests is a finding.
2. The guard: an 80 GB-class GPU passes (threshold 75 GiB), missing CUDA or a device below 75 GiB still refuses E42; the diagnostic line holds no project, benchmark, dataset, model or method word and cannot leak paths or secrets; it runs before the decision and cannot itself fail the job on a missing attribute in a way that hides the cause.
3. If the view's NVIDIA device/driver binds were changed: they match P's tk_bwrap (`/scratch/jjyeung/orch_n30/tree_rebuild10_w/ext/pwrap/b/c.sh` lines 339-366) and write nothing outside node-local job storage.
4. Tests are real (failing-before with the stubbed torch at 85,520,809,984 bytes, passing-after); decoded scan PASS; kit dir file list equals SHA256SUMS plus BUILD.json and SHA256SUMS.txt; resolver identity checks unchanged; upload diff versus 67ce92f6 small and pinned.
5. Say what you did not check.

## Rules
Read-only. No ssh, network, GPU, Git, tmux, scheduler or another agent. Never list, search or grep on /home or /data*. Any process under nice -n 10, at most 8 threads, under 20 GB RAM. Verdict, first line: `GO`, `GO AFTER FIXES` (each fix MUST or SHOULD, with evidence) or `NO-GO`. Then at most 25 lines.
