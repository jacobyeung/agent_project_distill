# Fix K5 after CPU-check death 174236 (lane lever6, trinity-2-28)

You are a build subagent of lane lever6. Check `hostname -s` prints trinity-2-28; stop if it prints `trinity`.

## Rules (binding)
- /home/jjyeung/.claude/CLAUDE.md section "Key Trinity Cluster Rules" and /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md bind you.
- Every stream over 20 MB that crosses the head node or touches /home or /data* registers with the IO governor first; Orchard calls keep the spacing LANE_RULES states; a dropped Orchard connection is retried once after 60 s. For you: NO stream, NO ssh, NO Orchard call, NO Git, NO GPU, no deletion. If you need an Orchard fact, list the exact read-only command in your final message.
- No recursive grep/find/du/ls -R on /home or /data*. Write only under /scratch/jjyeung/orch_n30/lever6/k5b. lever5/k5/kit is read-only (copy it). Python /scratch/jjyeung/envs/p1cpu/bin/python, nice -n 10, threads <= 8.
- Orchard opacity: no project, benchmark, dataset, model or method word in any shipped file or job name; job name `a15_cot_ap` + token; keep and rerun the kit's opaque-word scan.

## Facts
- Kit: /scratch/jjyeung/orch_n30/lever5/k5/kit (REPORT_K5.md, build_k5.py builds every shipped file and o_*.sh from a token). Its review: /scratch/jjyeung/orch_n30/lever6/k5rev/REVIEW_K5.md (GO; read its non-blocking notes).
- Death: CPU check 174236 staged the package and verified 4,384 frames, then the CPU arm's process exited 1 after 6 ms with no 9.err (returned files: lever5/k5/ret/cpu/4.1.json, 4.err). Cause, reproduced locally by /scratch/jjyeung/orch_n30/lever6/work/k5fix/nstest.py: bwrap refuses "Can't find source path <root>/fsw" because K5's 0.py never creates root/sj, root/fsw and root/m/ap. Rank 1's runner does, after stage() and before the namespace launch: /scratch/jjyeung/orch_n30/lever1_c/r1/out/review8_sources/job.py:215-236 (also note its env handling there). The placed package's namespace(): review8_sources/orchard_job.py:119-139.
- o_cfetch.sh (and any fetch script with the same line) fails when Slurm has purged the job id: `squeue -j` errors. A tolerant copy is /scratch/jjyeung/orch_n30/lever6/work/o_cfetch_fix.sh.

## Do
1. Copy the kit to lever6/k5b/kit. Choose a new opaque 13-hex token (the old placement a51f1ee88f0c9 exists on Orchard and refuses overwrite).
2. 0.py: create root/sj, root/fsw, root/m/ap (parents, exist_ok) after staging and before any namespace launch, exactly as rank 1 does; compare everything else rank 1's runner does between stage() and its namespace launch (job.py:215-236) and apply anything else K5 misses, naming each in the report.
3. Diagnostics: when an arm's process exits nonzero without an error record, record an opaque code that classifies the child's stderr (e.g. bwrap source path missing, interpreter not found, Python traceback, other) plus the exit code and wall time; no raw text on Orchard.
4. Every fetch script: tolerate a purged job id. o_sub1.sh: check job 0's final state is COMPLETED before pinning to its node; refuse otherwise.
5. Record the GPU's UUID (or PCI bus id) per arm.
6. Rebuild with build_k5.py (new token, paths, sha pins, o_place.sh), keep bytes and forecast lines current.
7. Tests: all existing tests; plus a new test that executes 0.py's own launch path (its real namespace argv from the package's namespace(), real /usr/bin/bwrap standing in for root/bwrap, fixture /scratch/jjyeung/orch_n30/lever1_c/r1_fixtures_old/real_cl2opr5g/j/sj for sj) on a root built by 0.py's own code after a stubbed stage, and proves the namespace starts (the test must fail on the old 0.py and pass on the new one; show both). Then rerun the stub dry run, the opaque scan, bash -n, and write SHA256SUMS_K5.
8. REPORT_K5.md updated in place in k5b/kit (state the current kit only), plus FIX_NOTES.md (<= 20 lines): what changed and why, test results, new token, place bytes.
Final message under 15 lines: token, changes, test results (old fails/new passes), o_place bytes and sha.
