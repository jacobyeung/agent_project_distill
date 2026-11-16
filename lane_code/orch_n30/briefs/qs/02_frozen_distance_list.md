# Build brief 02 (TOP PRIORITY): the frozen dev-S1 distance list with step 544's native arm on it

Builder: Claude Opus, high effort. Written by lane queue_synth, 2026-11-16. Tier A is due before any guard read is submitted; ORCH wants it today, before D0's m200 export lands (about 17:50Z).

## Rules
Read `/home/jjyeung/.claude/CLAUDE.md` section "Key Trinity Cluster Rules", then `B/tools/CLAUDE_LANE_RULES.md` and `B/tools/LANE_RULES.md` (B = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30`). No Git, no deletion, no GPU, no Orchard submission without an ORCH GO naming the job. Read named files only. Lane folder `/scratch/jjyeung/orch_n30/dist_list` on the node ORCH assigns; events `B/events/dist_list/`.

## Why
`distill_design/NEXT_LEG_INIT_RULE_20261116.md` item 6: the metre-distance guard uses every metre question in a distance list that is frozen, with its sha256 appended to that record, before the guard read of any candidate is submitted. The list is the 790 primary dev-S1 distance items if the native kit covers them by then, with the unit taken from question text alone and step 544 read on the same list; otherwise it is the 150-item fixed list. No such file exists.

## Tier A (must, CPU only, today)
1. `DISTANCE_LIST_DEVS1_150.jsonl`: the 150 distance items of Orchard job 170056 (TASKS a2f3fdbd, FRAMES c5e0dad8), one line per item: question id, capture, physical room, asked unit parsed from the question text alone, metre flag. Sorted by question id; LF endings; sha256 in `LIST_150.sha256`.
2. `unit_from_question.py`: the parser (metres, centimetres, feet, inches; square metres and square feet for room items), with tests. It must reproduce the reviewed counts on the fixed list: 43 metres, 28 centimetres, 46 feet, 33 inches; room 29 square metres, 7 square feet (`B/events/review_pp/REVIEW_VERDICT_PAIRED_VS_PARENT.md`). An item whose text names no unit or two units is listed and excluded from the metre set, never guessed.
3. `STEP544_ARM_150.jsonl`: step 544's native arm on those items from the return of job 170056 (sha256 5c150bafb333117b2e026def36564b26cecf25bcdf9d536e5350c84fdef972a1; Orchard `/project/community/jjyeung/okh7/n2r/b07a20b364`, `gs://cmu-gpucloud-jjyeung/q8/n2r/b07a20b364/`, trinity-1-13 `/scratch/jjyeung/orch_n30/native_r2/work/full_c8r/`; a copy of the analysis outputs is `B/events/native_r2/native_read_outputs.tar.gz`): per item the score, whether a call was made, refusal, final answer. Check: the metre mean equals 61.628 and the all-unit mean 29.867 (`distill_design/NATIVE_ROUTED_READ_DEVS1_STEP544_20261115.md`).
4. The line to append to the init-rule record after its Registration block: UTC time from `date -u`, list name, item count, metre count, sha256, and "150-item fixed list" or "790 primary". ORCH appends it, or orders you to.

## Tier B (report first, build only on ORCH's word)
The 790-item list would cut the guard's half-width from about 14 to about 6 to 9 task points (the rule's own estimate). It needs three things; report each as a count before building anything.
1. The 790 primary dev-S1 distance items: the primary stratum of `ITEMS.jsonl` (dev-S1 manifest `devs1_masks/out/MANIFEST.json` and `devs1_direct/out` on trinity-1-18 under `/scratch/jjyeung/orch_cd/`). Count metre items with the parser.
2. Backend coverage for the 640 new items under the unchanged backend of job 170056: how many of their operand (capture, name) pairs are in the mask cache `masks_4984fac22d84e8c5.tar` and geometry `geometry_8c58df1547371bdb.tar` (GCS `q8/8865619b/evalx_native/`), and how many are in the SAM 3 candidates of `/scratch/jjyeung/devs1_mask_run` on trinity-1-18. Missing pairs need a SAM 3 pass at the frozen setting on a Trinity 48 GB card (the predicted-mask kit measured 0.6 to 1.0 GPU-h for all 152 captures): that is a new cache object, so the job's cache-bind receipt changes and step 544 must be read again on the whole list with it.
3. Cost: step 544's native arm on 640 items is about 1.3 H100-hours on Orchard general, and each candidate's guard read grows by the same amount. General holds one job per user and is contended today.
Default if ORCH does not answer: freeze the 150-item list (Tier A). The rule allows it, and which list applies may depend only on coverage at that moment, never on a score: do not look at any candidate's distance score before the list is frozen.

## Tests
Parser tests with the counts above; a schema test of both files; a recomputation of step 544's means from `STEP544_ARM_150.jsonl`; byte-stable output (two runs give the same sha256).

## Do not touch
The registered text of the init-rule record above its Registration line (its sha256 d53f9c1a... must keep verifying); job 170056's return (read only); D0 job 170111, the VSTI job, K1 and its pool; nothing staged on trinity-1-13.

## Deliver
The three files, their sha256 values, the appended-line text, a Tier B coverage table, STATUS.md and one RESULT event. Review: one independent reader recomputes the list and the parser counts from the job's TASKS file and confirms the sha256 before the line is appended.
