# Lane n_review1g (Devin Opus high, session on trinity-3-30): independent pre-submission review of vehicle N's launch kit, successor of n_review1f; you post the final pre-submission verdict or refuse

First read B/tools/LANE_RULES.md and obey it, and /home/jjyeung/.claude/CLAUDE.md "Key Trinity Cluster Rules". B = /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30. Events: B/events/n_review. Session folder /scratch/jjyeung/orch_n30/n_review1g (small files; no file above 5 MB on trinity-3-30). trinity-1-18 only through `bash B/tools/tssh.sh trinity-1-18 'bash -s' < script` (batched, at most one call a minute; read-only except /scratch/jjyeung/orch_n30/n_review, where you may add small files; nothing above 200 MB on 1-18). Orchard read-only through `timeout 300 bash B/tools/ossh.sh 'bash -s' < script` (ls, stat, sha256sum, small cat, or a small read-only python over a few sqlite rows, a gzip JSON under 50 MB or a member of a tar under 20 MB; no Slurm command). No Git, no deletion (no rm, even of your own files: write new names), no GPU, no build, no fix: you check and report. Every PASS rests on something you opened yourself; a builder's RESULT or report is a pointer, not evidence. If something cannot be checked, it does not pass. No conditional pass. exec's `timeout` is in milliseconds (max 600000). Write a script file to disk before sending it through tssh.sh or ossh.sh. Long heredocs in exec can trip the deletion guard; write multi-line files with the write tool.

## Why you exist
A ~9B spatial VLM is trained on tree N; its launch job (advanced, 4 H100) starts only after your pre-submission PASS and ORCH's GO. The in-job reviewer n_review2 (brief B/briefs/n_review2.md) checks the prepared v.json and writes review.json; you keep that brief's expectations current.

## Start from (in this order; do not reread whole histories)
1. /scratch/jjyeung/orch_n30/n_review1f/STATUS.md (copy B/events/n_review/STATUS.md): everything checked since 15:22Z with hashes, scripts and evidence paths.
2. B/events/n_review/N_REVIEW_REPORT.md section "Final pre-submission" (n_review1f state). Evidence: B/events/n_review/evidence/n_review1f/.
3. Newest events in B/events/tree_rebuild (tree_rebuild23 or successor) and B/events/n_review from 1937Z on.
Scripts in /scratch/jjyeung/orch_n30/n_review1f/work. Copy them, then repoint n_review1f -> n_review1g in poll.sh and waitnew.sh and run `touch -d '<now> UTC' work/.mark`. The scripts:
- poll.sh and waitnew.sh N.
- s42.sh/s43.sh/s44.sh: item 1 on 1-18 (kit seals by launch_r1.build.verify under the T2 copy, SHA256SUMS diffs, decoded k/*.json diffs, tree tar vs the T2 copy, identity of kit_n_go k/c.json in bwrap with r1e/ident2.py). Change the W/w24x2 paths to the final kit.
- chk/taska.py (copy on 1-18 n_review/r1f/chk/taska.py): run `python -I -s -B taska.py <job dir>` on the copy of the job outputs under W/work/d<job>/<job>.
- o17.sh/o19.sh: P 5db993b1 sources; N materialization.
- o15.sh: P's original archive e5be8157, read-only.
- o10.sh/o9.sh: absence attribution against a1869ae2/969cdb56.

## Rulings in force
All rulings named in briefs n_review1c-1f, plus these:
- 1135Z, 1156Z, 1226Z, 1419Z.
- 1232Z, withdrawn by 1556Z item 5.
- 1551Z: option A. Routing rows of P's eligible sources behave as P did, and P had no extent reader. The card carries the defect counts.
- 1556Z: route T, a tree change.
- 1955Z: ENOSPC behaviour shown by a targeted test before the launch QUESTION; on the card.
- 1959Z: submission floors (discovery >= 50 GiB free, 4-GPU launch >= 100 GiB unless the ENOSPC test passed and the card says so); after any upload made under 20 GiB free, seals and sizes are re-verified on Orchard: your item 1 sha256sum -c on Orchard covers this, run it after the last upload.
- 1938Z: the job's exit follows (a)-(c); (d) is deferred to the discovery; the literal diff stays published as information; the sealed reference row is allowed for the third control on three stated conditions.

## Kit line now (verify everything yourself)
Tree T2 has 945 files, seal 9d2bbb8ad209d91e21e56121785f62b0dddf3c8d9f14db8d23daf6dcd1d3591b. It is C'' de202f58 + TREE_CHANGE_24M4X.patch db78806a (W/w24x2/out). n_review1f reproduced it on 1-18 /scratch/jjyeung/orch_n30/n_review/r1f/tcpx. On that copy its probe and compat 3/3, test_host24j 15/15 and test_carrier_c1_run 13/13 pass, so item 5 PASS on T2.
Kits 24m4x2 (W = trinity-1-18:/scratch/jjyeung/orch_n30/tree_rebuild10_w, W/w24x2): q df93cfba, n 797255ae, n_go aa2d1267, qd 8ae781f4. n_review1f verified them unarmed. kit_n_go c.json is a1fd8b40, payload 6d6fda1b, identity 4794b27f483798d3a33e8004c98cd5f9972b95d2abf7525d9951cdf6ef2c5e43 under tcpx.
24m4y2 changes the rcj helpers only (tree and kits unchanged per tree_rebuild22 1937Z/2023Z; candidate 173864 on it; then narrow review rev24m4y2, overlay, evidence run, and the discovery once /project stays above 50 GiB for 15 min; builder lane now tree_rebuild23); if any kit seal moves, redo item 1. Expect the reviewed overlay, then the evidence CPU run, the discovery, and arming.
Arming (W/w24*/out/arm_routing.py; ARM_ROUTING_USAGE.md of the final kit) requires your task-A RESULT with the word PASS and both hashes (routing_selection.json sha256, regenerated sha256). Never write both hashes and the word PASS in a file that is not a passing verdict; in evidence files rewrite helper status words (sed s/PASS/STATUS_OK/).

## Your tasks
A. Task A on the reviewed kit's evidence run, never a candidate (ORDER 1419Z). Run chk/taska.py on its outputs. A pass needs all of these:
- (B) P's DB 4e8e6c04 is equal.
- (a) content_field_counts has no key outside {/i, /row, /row/s1_source, nine copied fields}. No encode path and no /target appear. The newly published (a) list agrees with f.json's reader list.
- (b) unclassified is empty, every leaf path is in one of the four classes, and the s1_source leaves are only the four paths plus fps_source.
- (c) The chain shows routing refused 0, rows_checked = database_rows = 43,101 and complete true. extent_exempted_rows is exactly 10,945 (Cursor Q6; any other count blocks), still checked is 32,156, and the three controls are published per ANSWER 1938Z.
- (ii) All 4,797 absences are attributed: 4,768 to a1869ae2 scenes and 29 to list 6add0ad5. Re-derive this with o10.sh.
- (iii) U_Faithful goes from 747 to 718.
- routing_types PASS within 10%, proc_check PASS on real rows, and rdiff script bc2db774.
Then, on the discovery:
- (d) The sampler population equals N's DB in count and key set.
- Cursor P1: the reader_filters routing refusals are {}.
- N's selection receipt 655b953d (published as k_*receipt*.json) has the same sources as P's 5db993b1. Five are DEFERRED: ROUTE_direct, SCENE_room, T0_room and T1H1_room with source_not_final (the C'' s1_pool.py:44-47 wording for P's moved_to_vqa_store), and SCENE_room_sppK with room_set_not_authorized. The same nine are ELIGIBLE.
Then post a RESULT titled PASS naming routing_selection.json's sha256, the regenerated sha256 and N's routing DB sha256 (5e35c3ce on candidates). Otherwise post FAIL without the word PASS.
B. Final pre-submission verdict on all 8 items, on T2 and the armed final kit (items as in brief n_review1f.md):
- Item 1: recompute it on the final kit and on the armed kit. The armed kit's decoded diff is limited to the routing selection pin, and the Orchard kit equals the armed seal by sha256sum -c.
- Item 2: init.
- Item 3: task A plus the discovery census (live/c0..c4.json and s2.json show 0 admitted protected rows in every stream). Pose lists have no native producer, so hits go to ORCH first. Also check the selection table counts, with VQA relative_distance and the five alias sources attributed.
- Item 5: recheck only if the tree changes.
- Item 6: the card. Besides n_review1f's list, it carries the defect counts: ScanNet++ v1 3,362/11,663; exact 7,232 matches, 0 repaired; normalized 9,324 matches, 1,892 repaired.
- ORDER 1955Z (Orchard project filesystem near full): the card states free space at submission, the job's pre-training needs in bytes, and the tested ENOSPC behaviour of live publication, stdout/stderr, pre-training receipts (v.json, host receipt, review wait), checkpoints/stop checkpoint/exports (GCS, no project-filesystem byte) and the exit archive. A targeted test on the final kit's bytes is a ground under item 8; any wrapper change (logs to node-local disk) is re-read under item 7, and any kit change voids item 1.
- Item 7: the jn.sh bytes on Orchard x_22c714e1/jn.sh against the draft events/tree_rebuild/N_LAUNCH_WRAPPER_jn.sh 73c7cb3f.
- Item 8: the Astra review of the final kit; Cursor tr21_revT; grounds for every changed executable, including ground (iii), the admit legacy-branch test on the discovery's real v.json; the discovery's first_batch_check / live/f1.json per stream; the changed kit b/ files pl.py, sc.py, qd a.py and f0.py; and the ground (i) witnesses.
C. Output.
- Update the rows of the "Final pre-submission" table in B/events/n_review/N_REVIEW_REPORT.md; do not rewrite the sections above it.
- Then post a RESULT titled PASS, only if every item passes, naming the tree seal, the armed kit seal, the armed kit_n_go c.json payload sha256 and identity, the audited store hashes and the approved routing hashes. Otherwise post FAIL with the failing items.
- Update the expectations in B/briefs/n_review2.md (sha256 still 70c03ecba5d09e226aef20f577e616a4817a5f31305b1fad62023ac68290608e; n_review1f did not edit it):
  - item 1: tree T2 9d2bbb8a and its copy 1-18 /scratch/jjyeung/orch_n30/n_review/r1f/tcpx with r1e/ident2.py;
  - item 2: the routing criterion of RULING 1135Z / ANSWER 1226Z, with the routing database hash you approve;
  - item 4: the new pre-preparation payload/identity, plus extent_pool_sources and the exemption counts;
  - item 6: the pose census counts, the pointing count after the shape filter, and routing 43,101;
  - item 7: the armed kit seal.
  State the brief's new sha256 in your RESULT.
- If the kit or config changes after your PASS, your verdict is void: re-check what the change touches plus item 1, and post again.
D. Message only for results, questions and blockers. A question never blocks: state your default and continue. Near your hard limit (21,600 s) or 300K tokens, write a successor brief the same way, start it with `bash B/tools/devin_bg.sh <lane> <brief> claude-opus-5-5-high 21600`, add a line to B/tools/LANES.txt, confirm it by pgrep, post a RESULT rotate, and end. End without a successor once your final verdict is posted and ORCH has acknowledged it.

## Expected counts and hashes
- Store hashes: pose 6d5914404ecbe3205263df6e2d885ecd586c63283e78070191f1588b02d1f2f0, P routing 4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84 (N's routing DB differs; the approved hash is the one task A names), pointing c09bb5ca44158df467449f3c5fed865d81eb5520fb704785b19e73abc5536938, vqa 210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443.
- Routing: P 47,898 rows. N 43,101: camera_displacement 12,428, camera_movement_direction 10,883, camera_rotation 8,127, absolute_distance 10,945, units 718 (U_Faithful).
- Pointing: source 25,020; list d21e374f removes 320; scene exclusions 6,584; 18,116 before the shape filter; 0 K1.
- VQA: 181,098 admitted by the lists plus 7,971 twins.
- Pose: from the discovery census.
- Removal lists in order: 62113ff3, 4701e195, 6eb00a2d, 8a97fcc4, e3b0c442, e3b0c442, 6add0ad5, 43853165, 1c7c930d, 02315a74, caba6a56, d21e374f, d1454a44.
- Forecast (tree_rebuild22, ORCH 1938Z): launch QUESTION ~23:00Z.
