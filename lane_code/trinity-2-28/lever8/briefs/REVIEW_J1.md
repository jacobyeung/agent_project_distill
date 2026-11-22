# Fresh review of the J1 kit before its GPU run (lane lever8). Files and criteria only
You review by reading and by running the kit's own CPU tests; you run no GPU, no ssh and no real scorer.
Files:
- The brief the builder had: /scratch/jjyeung/orch_n30/lever8/briefs/BUILD_J1.md (sections Arms, Reading). The design: /scratch/jjyeung/orch_n30/lever8/design/MASK_SOURCE_DESIGN.md (candidate 1, Registered bars).
- The kit: /scratch/jjyeung/orch_n30/lever8/j1/kit/*.py, launch_gpu.sh, run_cpu_rehearsal.sh, seal.sh, tests/; the builder's report /scratch/jjyeung/orch_n30/lever8/j1/REPORT_J1.md (or j1/work/REPORT_J1.md); seal j1/SHA256SUMS_J1.
- Reviewed code it imports unchanged: /scratch/jjyeung/orch_n30/lever5/r1x/r1/relift.py; pattern kit /scratch/jjyeung/orch_n30/lever7/gtcd/kit.
Criteria (numbered findings with file:line; verdict GO or NO-GO):
1. Arms as specified: h1 = the served top proposal per anchor per operand (served ranking and floor, no linker); h0 = the pool proposal with best IoU against the bound GT instance, kept only at IoU >= 0.5, empty where GT is empty; k = the GT tight box as SAM 3 box prompt where GT is non-empty. No GT information leaks into h1 (check every path that builds h1).
2. Served contract: the prompt text, aliases, floors, cap and mask resize match the served path; check each file:line the report cites against the served code.
3. Parity stop: the rule changed after the CPU rehearsal (score >= 0.3 and score x presence >= 0.06 proposals need an IoU >= 0.95 partner). Judge whether this rule still tests that J1's pass reproduces the dump's pool for the proposals that can win h1 and h0, and whether the 95% threshold and the refusal (h1 and h0 not read below it; k read) are coded as stated. Say whether the change is defensible as fixed before any arm value was read.
4. Reading: paired room bootstrap identical to relift's for cells a and e (a and e asserted equal to relift.py's own); bars (>= 8 with LB > 0 source/opens; <= 4 with UB < 8 closes; else undecided) on all 117 items; per dataset ARKit, ScanNet, ScanNet++ separately with item and room counts; P/R definitions; false-positive anchor counts; the items-needed computation for undecided arms is sound (state its formula); ITEMS_J1.jsonl rows have the fields the brief lists.
5. Launcher: refuses head node and trinity-1-13, 0-23, 0-8, 3-23, 0-18 and paths off /scratch; checks the seal; two nvidia-smi readings of the chosen card 300 s apart inside the launching command, card <= 100 MiB both times, recorded; normal priority on 0-13; timeout; every child's exit code and stderr kept. The CPU rehearsal used the same inner line.
6. Run `cd /scratch/jjyeung/orch_n30/lever8/j1 && sha256sum --quiet -c SHA256SUMS_J1` and the kit's CPU tests (CUDA_VISIBLE_DEVICES='', nice -n 10, the env the report names); report pass or fail. Print no real arm value.
Write the review to /scratch/jjyeung/orch_n30/lever8/j1/review/REVIEW_J1.md (under 50 lines; create the folder).
## Rules for this subagent (copy of the lane's rules of the road; obey all)
- Read /home/jjyeung/.claude/CLAUDE.md section "Key Trinity Cluster Rules" and /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md first; they win over this brief.
- Every stream over 20 MB that crosses the head node or touches /home or /data* registers with the IO governor first. You need none: read only the named files, in bounded parts (sed -n, head, tail); no recursive grep/find/du/ls -R on /home or /data*; grep inside one named file is fine.
- No Git command. No ssh, no Orchard call, no GPU use, no job submission, no Gemini/OpenRouter/NV call. Nothing is run or built except what this brief names.
- Trinity cards (for reference only; you launch nothing): trinity-0-13 at normal priority, another shared node only under vnice, never trinity-1-13, 0-23, 0-8, 3-23 or 0-18.
- A local rehearsal of any kit runs the job's own launcher line, and a child that dies must leave its cause.
- Work from /scratch; write your report to the file this brief names; your final message is 5 lines at most and names the file.
- Write no files outside /scratch/jjyeung/orch_n30/lever8/. Delete nothing.
- Prose: complete sentences, characters as subjects, actions as verbs; no metadiscourse.
