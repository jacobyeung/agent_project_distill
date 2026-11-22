# Fresh review: the preempt fallback submit script, fixes R1 and R2
You review a bash script that runs on an Orchard Slurm login node (you cannot reach it; review by reading). Files only, criteria below.
Files:
- Original: /scratch/jjyeung/orch_n30/lever7/nfa/kit/o_sub_preempt.sh
- Patched: /scratch/jjyeung/orch_n30/lever8/nfa/o_sub_preempt_r12.sh
- The earlier review that asked for R1/R2: /scratch/jjyeung/orch_n30/lever7/nfa/fix2/REVIEW_FIX2.md (lines 1-20)
- The general-partition submit for comparison: /scratch/jjyeung/orch_n30/lever7/nfa/kit/o_sub.sh
Criteria:
1. R1: partition and node exclusion are set in one scontrol update, or any partial failure cancels the job; no path leaves a job held/half-moved, or released on preempt without the pin to orchard-community-0..3 (orchard-community-4 excluded).
2. R2: before release the script verifies Requeue=0 from scontrol show job, and cancels otherwise. Check the parse (scontrol show job prints space- and newline-separated Key=Value tokens).
3. No new failure path under `set -euo pipefail` (a command substitution or test that kills the script after submit but before hold/cancel, leaving a live job unaccounted). List each line where the script can exit with a job submitted and say what state the job is in.
4. Nothing else changed from the original except R1/R2 and messages.
Also check that each finding of the first re-review /scratch/jjyeung/orch_n30/lever8/nfa/rev12/REVIEW_R12.md (findings 3, 4, 8) is closed and that the fixes add no new path that leaves a job held or exits without an E-code after submit.
Verdict GO or NO-GO with numbered findings (line numbers), to /scratch/jjyeung/orch_n30/lever8/nfa/rev12/REVIEW_R12b.md, under 40 lines.
## Rules for this subagent (copy of the lane's rules of the road; obey all)
- Read /home/jjyeung/.claude/CLAUDE.md section "Key Trinity Cluster Rules" and /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md first; they win over this brief.
- Every stream over 20 MB that crosses the head node or touches /home or /data* registers with the IO governor first. You need none: read only the named files, in bounded parts (sed -n, head, tail); no recursive grep/find/du/ls -R on /home or /data*; grep inside one named file is fine.
- No Git command. No ssh, no Orchard call, no GPU use, no job submission, no Gemini/OpenRouter/NV call. Nothing is run or built except what this brief names.
- Trinity cards (for reference only; you launch nothing): trinity-0-13 at normal priority, another shared node only under vnice, never trinity-1-13, 0-23, 0-8, 3-23 or 0-18.
- A local rehearsal of any kit runs the job's own launcher line, and a child that dies must leave its cause.
- Work from /scratch; write your report to the file this brief names; your final message is 5 lines at most and names the file.
- Write no files outside /scratch/jjyeung/orch_n30/lever8/. Delete nothing.
- Prose: complete sentences, characters as subjects, actions as verbs; no metadiscourse.
