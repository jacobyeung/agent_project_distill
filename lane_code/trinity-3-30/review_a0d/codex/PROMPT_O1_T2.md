You are an independent read-only reviewer. Do not edit any file, run no Git command, no ssh, no GPU, no network. Read ONLY the named files below (no recursive search, no find/grep -r, no directory sweeps on /home or /data*). Bounded reads only (sed -n ranges, grep on one named file).

Files (D = /data2/jjyeung/agent_project_data/distill_design, E = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events):
- D/A0_AFTER_NATIVE_READ_DESIGN_20261116.md  (the design under review; sections 6 "O1" and "T2")
- D/REFREEZE_PREREGISTRATION_20261115.md and D/REFREEZE_PREREGISTRATION_20261115.json (decisions D1, D2, fallback, freeze, order P0-P9; last sentence of the .md on amendments)
- D/REFREEZE_AMENDMENT_1_K1_RASTERS_20261115.md, D/REFREEZE_AMENDMENT_2_K1_MANIFEST_V2_20261116.md
- D/NATIVE_ROUTED_READ_DEVS1_STEP544_20261115.md (the 150-distance/36-room native read of step 544; native vs direct and native vs parent tables)
- D/D0_STOP_RULE_20261116.md and E/cont_ops/PRELAUNCH_CARD_D0.md (D0 leg, F1/F2, confounds 1-9 incl. the 80 withheld rooms)
- D/POLICY_AUDIT_20261115.md (which choices were selected on benchmark items)

Questions (answer each with file:line evidence):
4. O1: What exactly do D1 and D2 register (arms, items, rule, default)? The design proposes amendment 3: (a) D1 takes "route" without the 640-item extension; (b) D2's default "direct (calls unserved)" is replaced by serving room calls for step-544 and D0 official reads. For (a) and (b) separately: is it a change written after seeing data that favours a preferred outcome? Would running D1/D2 as registered have produced a different decision? Is the design's statement that "the decisive distance number is E4" (an official VSI-Bench read that would decide whether distance goes direct at the next seal) consistent with the pre-registration's rule that dev-S1 decides route or direct and no benchmark item enters decisions? What must an honest amendment text disclose? Verdict per part: ACT / ACT WITH CHANGES (list) / DO NOT ACT.
5. T2: the next leg starts from "the newest D0 export that passed F1 and F2 (or F2's trend clause), else step 544". What does a D0 init change in what the next leg can claim (D0's row-form changes, procedure-only rows, routing-opener reset, room programs kept, the 80 withheld rooms that D0 still trains on in routing/pose/pointing; note the pre-registration's D2 power text about step 544 and the eligible pool)? Is the rule bindable before D0's reads exist (which exports get F1/F2 reads at all; does the trend clause count as a pass; do F1/F2 test camera or routed types)? Verdict: ACT / ACT WITH CHANGES (list) / DO NOT ACT.

Output: print your answer to stdout, at most 60 lines, findings first, each with file:line. Mark anything you could not verify.
