# Fresh re-check of the J1 kit after the fix for review finding 3.1 (lane lever8). Files and criteria only
Files: the first review /scratch/jjyeung/orch_n30/lever8/j1/review/REVIEW_J1.md; the kit /scratch/jjyeung/orch_n30/lever8/j1/kit (select_j1.py pick_h1, pick_h0, pick_match; relift_j1.py parity and parity.picks; tests/test_units.py, tests/test_relift_j1.py); the report j1/REPORT_J1.md (parity section, tests); the seal j1/SHA256SUMS_J1; the brief the builder had /scratch/jjyeung/orch_n30/lever8/briefs/BUILD_J1.md.
Criteria:
1. Finding 3.1 is closed: on both pools (J1's pass and the dump's), h1's and h0's rules pick the same mask (480x640 IoU >= 0.95 or both empty) on >= 95% of operand-frames, gated separately per arm; a failed arm is not computed anywhere (no path prints or writes its value); k is read regardless. The picks use exactly the code that builds the arms (no second implementation that could drift).
2. The pool gate is unchanged; both gates' counts are written to RELIFT_J1.json.
3. Tests cover agreement, a rank swap, a sub-0.3 h0 winner and both empty; run `cd /scratch/jjyeung/orch_n30/lever8/j1 && sha256sum --quiet -c SHA256SUMS_J1` and kit/tests/test_units.py (CUDA_VISIBLE_DEVICES='', nice -n 10, the env the report names); you need not rerun the 20-minute test_relift_j1 unless criterion 1 depends on it.
4. detect.py and launch_gpu.sh unchanged from the first review (compare their sha256 to the first review's seal if it lists them, else read them for any change).
5. Any other finding of the first review that was blocking.
Verdict GO or NO-GO with numbered findings (file:line) to /scratch/jjyeung/orch_n30/lever8/j1/review/REVIEW_J1b.md, under 30 lines. Print no real arm value.
## Rules for this subagent (copy of the lane's rules of the road; obey all)
- Read /home/jjyeung/.claude/CLAUDE.md section "Key Trinity Cluster Rules" and /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md first; they win over this brief.
- Every stream over 20 MB that crosses the head node or touches /home or /data* registers with the IO governor first. You need none: read only the named files, in bounded parts (sed -n, head, tail); no recursive grep/find/du/ls -R on /home or /data*; grep inside one named file is fine.
- No Git command. No ssh, no Orchard call, no GPU use, no job submission, no Gemini/OpenRouter/NV call. Nothing is run or built except what this brief names.
- Trinity cards (for reference only; you launch nothing): trinity-0-13 at normal priority, another shared node only under vnice, never trinity-1-13, 0-23, 0-8, 3-23 or 0-18.
- A local rehearsal of any kit runs the job's own launcher line, and a child that dies must leave its cause.
- Work from /scratch; write your report to the file this brief names; your final message is 5 lines at most and names the file.
- Write no files outside /scratch/jjyeung/orch_n30/lever8/. Delete nothing.
- Prose: complete sentences, characters as subjects, actions as verbs; no metadiscourse.
