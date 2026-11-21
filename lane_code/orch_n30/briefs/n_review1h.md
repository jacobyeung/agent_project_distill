# Lane n_review1h (Devin Opus high, session on trinity-3-30): independent pre-submission review of vehicle N's launch kit, successor of n_review1g; you post the final pre-submission verdict or refuse

First read B/tools/LANE_RULES.md and obey it, and /home/jjyeung/.claude/CLAUDE.md "Key Trinity Cluster Rules". B = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30. Events: B/events/n_review. Session folder /scratch/jjyeung/orch_n30/n_review1h (small files; no file above 5 MB on trinity-3-30). trinity-1-18 only through `bash B/tools/tssh.sh trinity-1-18 'bash -s' < script` (batched, at most one call a minute; read-only except /scratch/jjyeung/orch_n30/n_review, where you may add small files; nothing above 200 MB on 1-18). Orchard read-only through `timeout 300 bash B/tools/ossh.sh 'bash -s' < script` (ls, stat, sha256sum, small cat, or a small read-only python over a few sqlite rows, a gzip JSON under 50 MB or a member of a tar under 20 MB; no Slurm command). Host-key rule (ORCH RULING 2152Z): never pass host-key options; on a host-key warning stop Orchard calls and post a BLOCKER with the fingerprint line. No Git, no deletion (no rm, even of your own files: write new names), no GPU, no build, no fix: you check and report. Every PASS rests on something you opened yourself; a builder's RESULT or report is a pointer, not evidence. If something cannot be checked, it does not pass. No conditional pass. exec's `timeout` is in milliseconds (max 600000). Write a script file to disk before sending it through tssh.sh or ossh.sh, and give every command inside that could read stdin `< /dev/null` (a child that reads stdin eats the rest of the script). Long heredocs in exec can trip the deletion guard; write multi-line files with the write tool.

## Why you exist
A ~9B spatial VLM is trained on tree N; its launch job (advanced, 4 H100) starts only after your pre-submission PASS and ORCH's GO. The in-job reviewer n_review2 (brief B/briefs/n_review2.md) checks the prepared v.json and writes review.json; you keep that brief's expectations current.

## Start from (in this order; do not reread whole histories)
1. /scratch/jjyeung/orch_n30/n_review1g/STATUS.md (copy B/events/n_review/STATUS.md): everything checked since 20:24Z with hashes, scripts and evidence paths.
2. B/events/n_review/N_REVIEW_REPORT.md section "Final pre-submission" (n_review1g state). Evidence: B/events/n_review/evidence/n_review1g/ (taskA_evidence_run_173881.md).
3. Newest events in B/events/tree_rebuild (builder lane tree_rebuild24 or successor) and B/events/n_review from the time of n_review1g's rotate RESULT on.
Scripts in /scratch/jjyeung/orch_n30/n_review1g/work. Copy them, then repoint n_review1g -> n_review1h in poll.sh and waitnew.sh and run `touch -d '<now> UTC' work/.mark`. The scripts:
- poll.sh and waitnew.sh N (waitnew.sh 570 fits one exec call).
- s58full.sh (item 1 on a kit line: verify under the T2 copy, SHA256SUMS diffs, decoded k/*.json diffs, tree tar vs T2 copy) and s59.sh (identity of kit_n_go k/c.json in bwrap with r1e/ident2.py, stdin from /dev/null). Change the w24y2/w24z4 paths to the kits you check.
- s53.sh (task A reader chk/taska.py on a 1-18 job copy; 1-18 copy n_review/r1f/chk/taska.py), s57.sh (selection receipt digest), o21b.sh (absence attribution on Orchard), o22.sh/o23.sh (discovery outputs, selection compare vs P 5db993b1), o24.sh (pinned discovery kit vs qd).

## Rulings in force
All rulings named in briefs n_review1c-1g, plus these: 2055Z (kit change beside the line; launch uses it; jn2/jn3 wrapper), 2058Z (hold/mint/release; my nine points required), 2132Z (archive last; legacy copier tests pass), 2152Z (host key), 2211Z (logs/archive never wait on the stop upload; stop margin from measured rate), 2232Z (strict GCS-protocol sink; per-attempt upload log; e3 with readback), 2256Z (second discovery), 2258Z (option B: discovery kit pinned without a PASS; the launch kit is armed only from the full task-A PASS), 2345Z (stop window: measured write and rate; stop_before_seconds change authorized with one narrow review).

## State at 00:25Z (verify everything yourself)
- Tree T2 945 files, seal 9d2bbb8ad209d91e21e56121785f62b0dddf3c8d9f14db8d23daf6dcd1d3591b; my copy 1-18 /scratch/jjyeung/orch_n30/n_review/r1f/tcpx; item 5 PASS on it.
- Reviewed overlay 24m4y2: q df93cfba, n 797255ae, qd 8ae781f4. Evidence run 173881: task A evidence part holds (taskA_evidence_run_173881.md). Arming hashes: routing_selection.json a49f117f60add326e1ef3e8eb2b92a73ec299425e8efb477fa9e84d462789e73; regenerated_sha256 522a3be39b90d6fd8ec4dd599d89e1d5762c3a1a150e198c0c0bbb70f931ba39 (compact digest of receipt.json 38c52f00); N routing DB 5e35c3ce600a867be194911642caccb23098035b4bf08909e519a170a1c243df. arm_routing.py 1a4b900b:42 compares the reviewed regenerated hash with the receipt's database hash, so the verdict file must contain a49f117f and 5e35c3ce (name 522a3be3 too).
- Selection receipt pinned by a49f117f is 74640a29 (not 655b953d): same 14 sources and statuses as P 5db993b1 (o23.out). Judge that item on 74640a29.
- Second discovery 173964 on pinned kit X/qp_11386117 (I checked: only k/a,h,p,r.json differ from qd; pins a49f117f/522a3be3/5e35c3ce; authorization = ANSWER 2258Z). Its outputs: X/o/173964/j7/ (j7.json index: e0 population, e2 + b* reader_filters, e4-e6/e10 receipts and census, e7/e9 + live/f1.json first batch, e8 host receipt).
- Launch kit line: ENOSPC kit round. 24m4z4 (n 54729156, n_go 8052ce08), 24m4z7 (n bd20a9fe, n_go f392c95e, tar 7daf1570; rev24m4z7 NO-GO 5 findings), 24m4z10 fixing (W/w24z10). Only b/o.py, b/pc.py, b/pc.sh, k/y.json (and possibly k/n.json stop_before_seconds via set_stop.py) may change. kit_n_go c.json a1fd8b40, payload 6d6fda1b, identity 4794b27f483798d3a33e8004c98cd5f9972b95d2abf7525d9951cdf6ef2c5e43 on 24m4z4 under tcpx; a k/n.json change moves n.json identity, never c.json.
- Real GCS: Trinity runs tgcs_900001b, tgcs_900002b, e3t_900003 each 16 receipts; I matched the lists with n_ops8's raw readback (/scratch/jjyeung/orch_n30/n_ops8/work/gcs/readback_*.out). e3 on Orchard (held, minted, released; rate; readback) is still owed.
- My point 3 settled: z.py:603/607 Q_ROOT = resolved boot node N; o.py --final keeps the existing RESULT.json (real rc and rr from k/j.json:438).
- Launch wrapper: jn2.sh (events/tree_rebuild/N_LAUNCH_WRAPPER_jn2.sh 12227869) or its successor jn3.sh from 24m4z7/z10; my RESULT 2054Z points are required (job name a15_cot_ap + opaque token, final publish on the exit path, SLURM_TMPDIR logged, broad exception catch).
- Forecast launch QUESTION ~03:30Z or later.

## Your tasks
A. Task A discovery part on 173964, then the verdict:
- (d) The sampler population equals N's DB 5e35c3ce in count (43,101) and key set (c2ba56c5).
- Cursor P1: reader_filters routing refusals are {}.
- Selection receipt 74640a29 versus P 5db993b1 (done on 173912's copy; confirm the same file in 173964).
- If all hold with the evidence-run part, post a RESULT titled PASS naming a49f117f, 522a3be3 and 5e35c3ce in full. Otherwise post FAIL without the word PASS. Never write both hashes and the word PASS in any other file; in evidence files rewrite helper status words (sed s/PASS/STATUS_OK/).
B. Final pre-submission verdict on all 8 items, on T2 and the armed final launch kit (items as in brief n_review1f.md, with n_review1g's additions):
- Item 1: recompute it on the final launch kit (24m4z10 or successor) and on the armed kit. The armed kit's decoded diff is limited to the routing selection pin; the Orchard kit equals the armed seal by sha256sum -c, run after the last upload (RULING 1959Z item 3).
- Item 2: init on the armed c.json.
- Item 3: task A plus the discovery census (j7/e4-e6/e10, live/c0..c4 and s2: 0 admitted protected rows in every stream; pose lists have no native producer, so hits go to ORCH first) and the selection table counts (VQA relative_distance, five alias sources attributed).
- Item 5: recheck only if the tree changes.
- Item 6: the card, with the defect counts (ScanNet++ v1 3,362/11,663; exact 7,232 matches, 0 repaired; normalized 9,324 matches, 1,892 repaired), ORDER 1955Z free space and pre-training bytes, ENOSPC behaviour per path, hold/mint/release steps and minutes, stop checkpoint size, measured write time (65-77 s checkpoint, 56-66 s export) and e3's GCS rate with the window and file:line of stop_before_seconds, exit-archive cap 50 MB, the stop-marker limit (ANSWER 2345Z item 3).
- Item 7: the launch wrapper bytes on Orchard x_22c714e1 against the published draft.
- Item 8: Astra GO on the final kit; grounds for every changed file (o.py, pc.py, pc.sh, y.json, any n.json change) from the strict-sink ENOSPC rerun, fail-before/pass-after tests, e3 on Orchard with readback; ground (iii) admit legacy-branch test on 173964's v.json; first_batch_check / live/f1.json per stream; grounds (i) witnesses.
C. Output.
- Update the rows of the "Final pre-submission" table in B/events/n_review/N_REVIEW_REPORT.md; do not rewrite the sections above it.
- Then post a RESULT titled PASS, only if every item passes, naming the tree seal, the armed kit seal, the armed kit_n_go c.json payload sha256 and identity, the audited store hashes and the approved routing hashes. Otherwise post FAIL with the failing items.
- Update the expectations in B/briefs/n_review2.md (sha256 still 70c03ecba5d09e226aef20f577e616a4817a5f31305b1fad62023ac68290608e): item 1 tree T2 9d2bbb8a and its copy 1-18 r1f/tcpx with r1e/ident2.py; item 2 the routing criterion of RULING 1135Z / ANSWER 1226Z with the routing DB hash you approve (5e35c3ce if task A passes); item 4 the pre-preparation payload 6d6fda1b / identity 4794b27f (or the armed successor), extent_pool_sources and the exemption counts (10,945 exempted, 718 receipt-entry); item 6 the pose census counts, the pointing count after the shape filter, routing 43,101; item 7 the armed kit seal. State its new sha256 in your RESULT.
- If the kit or config changes after your PASS, your verdict is void: re-check what the change touches plus item 1, and post again.
D. Message only for results, questions and blockers. A question never blocks: state your default and continue. Near your hard limit (21,600 s) or 300K tokens, write a successor brief the same way, start it with `bash B/tools/devin_bg.sh <lane> <brief> claude-opus-5-5-high 21600`, add a line to B/tools/LANES.txt, confirm it by pgrep, post a RESULT rotate, and end. End without a successor once your final verdict is posted and ORCH has acknowledged it.

## Expected counts and hashes
- Store hashes: pose 6d5914404ecbe3205263df6e2d885ecd586c63283e78070191f1588b02d1f2f0, P routing 4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84, N routing 5e35c3ce (approved by task A), pointing c09bb5ca44158df467449f3c5fed865d81eb5520fb704785b19e73abc5536938, vqa 210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443.
- Routing: P 47,898 rows. N 43,101: camera_displacement 12,428, camera_movement_direction 10,883, camera_rotation 8,127, absolute_distance 10,945, units 718.
- Pointing: source 25,020; list d21e374f removes 320; scene exclusions 6,584; 18,116 before the shape filter; 0 K1.
- VQA: 181,098 admitted by the lists plus 7,971 twins.
- Pose: from the discovery census.
- Removal lists in order: 62113ff3, 4701e195, 6eb00a2d, 8a97fcc4, e3b0c442, e3b0c442, 6add0ad5, 43853165, 1c7c930d, 02315a74, caba6a56, d21e374f, d1454a44.
