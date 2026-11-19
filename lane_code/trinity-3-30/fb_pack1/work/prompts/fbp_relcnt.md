# Task fbp_relcnt: relative-count family in procedure form without stated counts, for N's first boundary (CPU only)
Workspace: /scratch/jjyeung/orch_n30/fb_pack/relcnt (write ONLY here; create it; under 1 GB). Final report out/REPORT.md (at most 80 lines), rows out/relative_count.jsonl, out/CHECKS.json, out/READ40.md, out/fbp_relcnt.tar + sha256. Due: 2 hours.

## Ruling (orchestrator RULING 2026-11-19T10:41Z item 3, binding)
"Build a relative-count family in procedure form now (two procedure steps, one per category; one comparison line without stated counts; the option letter), about 4,000 rows from ground-truth instance counts, balanced over which side is larger and over the option letters, no list of entries anywhere, N's validator, 30 rows read, one cross-family review. No trace-ruling amendment is needed for this form."
Trace ruling (memory file trace-ruling-20261115): no answer-only rows; direct rows state no measurements. Here: no number may appear in the think block except frame indices if any.
Why: at step 400 relative count fell from 64.7 to 38.1 on dev-S1 because 60 of 139 traces copy the one-line counting procedure and answer a number where the question wants an option letter (record /data2/jjyeung/agent_project_data/distill_design/R1_M200_TRACE_ANALYSIS_20261119.md, S400.4).

## Start from the existing build
/scratch/jjyeung/orch_n30/sb_rowC (read-only; copy its code into your workspace): 4,000 procedure rows from b12 v4 totals with byte-matched GT rasters, 20 new wordings x 200, ties 10%, first/second larger balanced, options balanced. It is BLOCKED_GRAMMAR because each trace states both counts (out/GRAMMAR_CONFLICT.md: 8,000 number_not_allowed). Keep its sources, sampling, wordings and balance; change only the trace: Step 1 = the store's counting procedure line for category X, Step 2 = the same for Y, then one comparison line in the question's direction without numbers ("There are more X than Y." / "There are fewer ..." / "There are as many X as Y."), then the option letter after </think> in the store's direct form. Match the store's existing counting procedure wording exactly (find it in store v7's object_counting rows).

## Checks (all in out/CHECKS.json)
- N's current tree /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/tree_r1 (record TREE_SEAL from ../../out/TREE_SEAL.json): trace_grammar.validate_trace passes on every row; r1_counting.admit, r1_training.row_check, ground_rows.pack/validate pass; unique qids and candidate_ids (kit formula).
- Ground truth recomputed independently for every row from the b12 totals; the letter matches; balance tables per template (first larger, second larger, equal) and per option letter.
- Room rule with the audit checker /scratch/jjyeung/orch_n30/sb_auditfix2 (command pattern in /scratch/jjyeung/orch_n30/sb_fullinv/work/audits_native/camera_wording/audit.json): zero R0 bdb5d402, dev-S1 969cdb56, BENCH v2 3119aa4a, withheld-80 634820b4 and K1 4d4736cf rooms.
- Wordings at normalized edit distance >= 0.4 from every dev-S1 / R0-dev relative-count wording (report counts).
- 40 rows printed in full to out/READ40.md, one per template plus ties, read by you.
- How the family enters N: find how the launch kit binds direct families (the direction twins' path (b) in /scratch/jjyeung/orch_n30/tree_rebuild10_w/w22/out build 22 report) and write the binding fields tree_rebuild must set, in out/BINDING.json. No tree change.
