# Fix round 2 for the D0 read kit (work only in /scratch/jjyeung/orch_n30/cont_ops/work/d0/readk/)

Same rules as BRIEF.md and FIX_BRIEF.md in this folder: no ssh, GPU, network, Git, deletion or Slurm; tests stay behind tests/offline_guard.py; mock every publish or gcloud path. Do not touch kit/reader/ prompt or scoring bytes. Python: /scratch/jjyeung/envs/p1cpu/bin/python.

## The one authority
/data2/jjyeung/agent_project_data/distill_design/D0_STOP_RULE_20261116.md, items 1 to 3 (amended before any D0 export was read). The verdict logic in f1f2.py must equal it word for word. The current `stop_rule()` (CONTINUE_TO_400, step-100 trend exception, step 400 = "STOP if F2 fails") is the superseded rule: replace it.

## Required verdict logic
- Reads: steps 100, 200, 400, 600, 800 and the final export. CLI `--step` accepts all of them; the kit's prepare/bind/job accept the same steps (the round-1 B3 fix stopped at 400). Find the final export's step and object name from the uploader/training source this kit already cites (evidence/UPLOADER_FORMAT.txt, the run's export schedule); if it cannot be determined offline, accept `--step 1000` and say so in FIX2.md.
- Step 100: report every quantity; `verdict` is null with reason "step 100 gives no verdict".
- F1 (seven registered types only; relative_count and relative_size_object stay information only): at step 200 or any later read, a type whose paired-difference 95% interval is wholly below zero (upper bound < 0) gives STOP.
- Facing twins at step 200: STOP if the point estimate of away accuracy is not above step 544's on all three levels, i.e. STOP if any level has away200 <= away544. Step 544's point values come from --a; assert they equal 38 / 20 / 6 (easy / medium / hard) and refuse otherwise.
- Facing twins at steps 400, 600 and 800: a new required argument `--prev ITEMS.jsonl` holds the previous read (200 for 400, 400 for 600, 600 for 800; check its step and paired membership). STOP if away accuracy (point estimate) is strictly below the previous read's on at least two of the three levels AND F2 has not passed at the current read. Equal is not below.
- F2 = TRACE_RULING 2.7 lower-bound reading (lower bound of away accuracy above 54 / 40 / 36, alike share at most 20%, toward B minus A interval not wholly below zero). Report it at every read with the point-estimate reading beside it. F2 by itself stops nothing at any step, and the point reading never enters a verdict.
- Final export: report F1, F2 (the F2 decision PASS/FAIL is made here) and the facing comparison to the previous read; the leg has ended, so `verdict` is "FINAL" with the F2 decision, not STOP/CONTINUE. State this reading in FIX2.md.
- Verdicts at 200/400/600/800: "STOP" or "CONTINUE", with `reasons`: every rule that fired (F1 types named; facing levels named with both values), or "no stop condition met".
- Remove `--m100` and the CONTINUE_TO_400 path; nothing else in the kit changes behavior.

## Tests (tests/test_verdict.py), one per boundary at least
Step 100 with F1 failing gives no verdict; F1 upper bound exactly 0 vs just below 0 at 200, 400, 600, 800; at 200 away equal to 544 on one level -> STOP, just above on all three -> CONTINUE, F2 failing with away above 544 on all -> CONTINUE; at 400/600/800: two levels below previous with F2 failing -> STOP, two below with F2 passing -> CONTINUE, one below -> CONTINUE, two equal -> CONTINUE; wrong --prev step and missing --prev refused; 544 values not 38/20/6 refused; F2 lower bound exactly at threshold fails, alike exactly 20% passes; point reading differing from lower-bound reading changes no verdict; final export gives FINAL with the F2 decision; relative_count/relative_size_object failing never stops. Keep all existing tests passing (update only those that encoded the superseded rule, and list them).

## Finish
Re-pin (evidence/FINAL_PINS.json), re-run all tests into evidence/FIX2_TESTS.log, re-run the binds for each newly accepted step into evidence/FIX2_BIND_*.log. Update REPORT.md (at most 60 lines; commands for every step incl. --prev) and REVIEW.md (section "Fix round 2", file:line per rule clause).
Diffs: the tree before this round is snap/readk_fix1.tar in the parent folder (sha256 34ccc385...). Write DIFF_FIX2.patch = unified diff of every changed file against it (exclude evidence/test_* and evidence/chain_*). Write DIFF_FIX1.patch = round 1's changes against the reviewed kit, reconstructed from the patches in /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/20261116T093327Z_cont5_readk_fix1/transcript.log (read it in bounded parts); mark it reconstructed and name any file you could not reconstruct.
Write FIX2.md, at most 30 lines: each rule clause, its code line, the tests that prove it, the old and new pins, and anything unverified.
