# Fresh review of kit K5 (lane lever6, trinity-2-28). Read-only review; write one report file.

Check `hostname -s` prints trinity-2-28; stop if it prints `trinity`.

## Rules (binding)
- /home/jjyeung/.claude/CLAUDE.md section "Key Trinity Cluster Rules" and /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md bind you.
- Every stream over 20 MB that crosses the head node or touches /home or /data* registers with the IO governor first; Orchard calls keep the spacing LANE_RULES states; a dropped Orchard connection is retried once after 60 s. For you: NO stream, NO ssh, NO Orchard call, NO Git, NO GPU, no deletion, no edit of kit files.
- No recursive grep/find/du/ls -R on /home or /data*. Write only /scratch/jjyeung/orch_n30/lever6/k5rev/REVIEW_K5.md. Python, if you run tests: /scratch/jjyeung/envs/p1cpu/bin/python -I -B, threads <= 8, nice -n 10, run from a copy under /scratch/jjyeung/orch_n30/lever6/k5rev/tmp if a test writes files.

## Files (read these; nothing else is needed)
- The build brief: /scratch/jjyeung/orch_n30/lever5/k5/BRIEF_K5.md
- The kit: /scratch/jjyeung/orch_n30/lever5/k5/kit/ (REPORT_K5.md, 0.py, 2.py, 9.py, 1.json, 3.json, build_k5.py, score_k5.py, test_k5.py, dry_run_k5.py, scan_k5.py, cpu_real_k5.sh, o_*.sh, SHA256SUMS_K5, BUILD.json, FORECAST.json, REFERENCE_K5.json, TESTS_K5.log, CPU_REAL_K5.json)
- The rank 1 package it reuses (conventions and served tower call): /scratch/jjyeung/orch_n30/lever1_c/r1 (REPORT.md, PLACE.md, the payload's tower_read.py, orchard/o_*.sh). Read only what a criterion needs.
- Evidence of the effect: /scratch/jjyeung/orch_n30/lever5/out/HISTORY_DIAG.txt

## Criteria (verdict GO or NO-GO, with file:line for every defect)
1. The question is answerable: four arms (A1 production order default, A2 reverse default, D1/D2 the same with deterministic settings), each a fresh process; the two orders really differ in order and cover the same captures; each arm recomputes capture 0 at the end.
2. Deterministic switches are set before the first CUDA call, each is named, and nothing else in the tower code is left to chance unnamed (TF32, SDPA backend, cuBLAS workspace, seeds, allocator). bf16 autocast stays as served. A strict refusal is recorded and the arm rerun with warn_only, and the report says so.
3. Default arms are served numerics: same package, weights, interpreter, frame bytes and frame order binding as rank 1 (byte-identical sources; frame binding hash per capture). Note the two declared deviations (two GPU jobs pinned to one node; scale as a stand-in with gravity fixed) and judge whether either can bias answer (1) or (2).
4. The scorer's rules are fixed before any run, and match the brief: bit-equality and deviations per dataset; answer (1) yes only if D1 and D2 are bit-equal on all captures and both D recomputes match; answer (2) the D/A time ratio with rebuilds excluded. Check the synthetic tests actually exercise equal, perturbed and missing cases.
5. Job hygiene: Orchard opacity (no project/benchmark/dataset/model/method word in shipped files or job names; scan covers every shipped file); partition general only, never advanced; --exclude=orchard-community-4, --mem=200G, 50-min limit with forecast x1.5 under it, in-job guard; the CPU check runs the real first unit; write test, error record, sacct-based fetch and return authentication follow rank 1's kit; new /project bytes <= 50 MB; returns under 20 MB; job 1's node pin reads job 0's node correctly.
6. SHA256SUMS_K5 matches the files (run `sha256sum --check --quiet SHA256SUMS_K5` in the kit dir).

## Output
Write REVIEW_K5.md (<= 60 lines): first line `VERDICT: GO` or `VERDICT: NO-GO`; then per criterion a pass/defect line with file:line; then blocking defects with the smallest fix; then non-blocking notes. Your final message: the verdict line and the blocking defects only.
