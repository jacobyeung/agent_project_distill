Verdict: NO-GO
The run, the gates and the registered verdicts check out (h1 closes, h0 closes, k opens). Findings 1-4 found no fault. Before RESULT_J1_draft.md goes out, delete or rewrite the two interpretive claims in finding 5 (draft lines 10-11). With that edit the verdict becomes GO. No rerun or recompute is needed.
Reviewer: fresh post-run reviewer on trinity-2-28 (`hostname -s` = trinity-2-28), 2026-11-22. Every check below was run by the reviewer. Scripts: lever9/work/review_tmp/check_items.py and pool_iou.py.

1. Sealed bytes and GPU pass: pass (non-blocking).
   - `sha256sum SHA256SUMS_J1` = b8561842...5a, and `sha256sum --quiet -c SHA256SUMS_J1` in lever8/j1 exits 0 now (3,752 lines). The START contract hashes in EVENTS.jsonl:7 (detect.py f9b8f38b, j1_common.py f9ad78c4, select_j1.py 64ee2475, stage1.py b1a77424) equal the sealed hashes. The FRAMES/PROMPTS shas in INDEX.json equal the sealed out/FRAMES_J1.json and out/PROMPTS_J1.json.
   - EVENTS.jsonl:1 shows the seal check (CHILD sha256sum exit 0) on trinity-0-13. Lines 3 and 5 show two nvidia-smi readings at 11:09:05Z and 11:14:06Z (seconds_after_1=300), with card 0 at 2 MiB used in both. Line 6 launches gpu=0 priority=normal. Line 8: bf16 on an RTX 6000 Ada. Lines 9-54 hold 46 CAPTURE events with 32 anchors each. Line 55 is END with done 46/46, failed [], stopped null and 412.7 s. Line 57 is PASS_DONE exit=0. The launch log lines 1-9 agree.
   - My recompute of the out/detect digest gives 4c01af31...89c8, which matches the stated value (54 files, 46 capture .json.gz).
   - stderr: three of the four .err files are empty. pass.err (1,058 B) holds the pkg_resources and timm deprecation warnings plus "kernel cache directory could not be created (.../lever8/j1/work/gpu_cache/xdg/torch/kernels)". work/ was not in the transfer list (REPORT_J1.md:36-40), so on 0-13 this only disabled the JIT kernel cache. It affects nothing in the outputs.
   - Outside the seal: relift.py is not under SHA256SUMS_J1. RELIFT_J1.json input_sha256 records bbc97331, which equals the current lever5/r1x/r1/relift.py. The a/e reproduction check (finding 2) covers it.

2. Relift computed what was registered: pass (non-blocking).
   - Pool gate: matched 7,410 of 7,424 (0.998 >= 0.95). The 7,424 operand-frames are 232 operands x 32 (2 of 234 operands have no ground call). Strict matches: 6,636 (0.894), reported and not gating.
   - Pick gates: h1 7,394 and h0 7,411 (both >= 0.95). The parity.by_dataset counts sum to these totals.
   - gates() (relift_j1.py:47-57) reads an arm only when both of its gates pass. arms_read is [h1, h0, k].
   - Bars: select_j1.verdict (select_j1.py:162-171) matches REPORT_J1.md:25, and the ruling's item 2 bars match REPORT_J1.md:25.
   - Applied to the all-117 numbers:
     - h1 -11.97 [-21.70, -2.64]: closes.
     - h0 -12.31 [-22.97, -1.94]: closes.
     - k +11.03 [+0.66, +20.90]: opens.
     - needed is {}, which is correct because no arm is undecided.
   - Per-dataset rows carry items and rooms: 33/10, 24/7, 60/18 (decides=false).
   - reproduction.a_e_rows_equal and relift_stats_equal are true. compute() sets these flags only after the asserts at relift_j1.py:255-264 pass, and the run exited 0, so the flags mean the checks ran.

3. Internal consistency: pass (non-blocking).
   - ITEMS_J1.jsonl has 585 rows, 117 items x {a, e, h1, h0, k}, with no duplicate (item, arm). On every row, score, printed_gap_m, room and dataset equal RELIFT_J1.json rows: 0 mismatches.
   - Means recomputed from ITEMS_J1.jsonl: a 55.81, e 69.57, h1 43.85, h0 43.50, k 66.84. Differences from a: h1 -11.97, h0 -12.31, k +11.03, e +13.76. Shares: -0.870, -0.894, 0.801.
   - Per dataset (n/rooms, recomputed): ARKit 33/10, ScanNet 24/7, ScanNet++ 60/18. Each X - a mean equals RELIFT_J1.md:9-11.
   - The P/R counts summed over operand rows equal precision_recall in the JSON and .md (pred_on_empty_gt: a 121, h1 1,098, the others 0; GT frames 1,422).

4. Plausibility of the scoring path: no bug found (non-blocking).
   - Scoring is identical across arms. relift_j1.py:226-249 sends every cell, a included, through R.fit_lift, R.gap_value, R.round_gap and official_mra, on the same capture's restored depth g.
   - An operand without a lift gives gap None (relift.py:83, 123-124), and the item scores 0. That holds equally for a (8 no-lift items) and h0 (52), and in the data every no-lift item scores 0 in every arm.
   - Every arm uses the same grid and frames:
     - a: R.masks_array(selected_masks) on (32,240,320).
     - h1 and h0: mask480[::2, ::2] (select_j1.py:44-49).
     - k: the same to_grid, with each mask placed at its PROMPTS_J1 slot (relift_j1.py:131-133).
     - A shape check runs at relift_j1.py:236.
   - Text-pool frame and canvas alignment: the dump pool pairs at IoU >= 0.95 on 99.8% of operand-frames.
   - k alignment: k's mask frames equal the GT frames on all 234 operands, with P/R 0.72/0.74 against GT. A misaligned box would not give that.
   - k is built as registered:
     - The box comes from box_from_mask on the GT grid (prompts_j1.py:45).
     - detect.py:122-151 uses the 'visual' text, the dummy prompt plus one positive box, the top query by sigmoid(logit) x presence, and stage1's bilinear > 0 then 480x640 rule.
     - k is prompted only where GT is non-empty (REPORT_J1.md:13), so it gets visibility for free: pred_on_empty_gt is 0 by construction.
   - h0 is an IoU >= 0.5 per-frame pool oracle (REPORT_J1.md:12), not a ceiling over a. Served tracks lift from masks below 0.5 IoU; h0 abstains. On the 52 h0 no-lift items, a averages 42.9 and h0 scores 0. Its "closes" verdict means this registered arm, not "the best possible pick from the pool".
   - ScanNet's per-dataset intervals rest mostly on one room: d1/scene0515 holds 16 of 24 items. That explains the skewed intervals in RELIFT_J1.md:10 (a [7.5, 69.6], h0 - a [-9.5, +78.3]). These rows do not decide, but the draft could say so.

5. Draft lines 10-11: two interpretive claims are unsupported, and one contradicts the draft's own numbers (BLOCKING for the draft).
   - The numbers in line 10 are correct (recomputed):
     - h0 has 52 no-lift items, and each has an operand empty on all 32 anchors; a has 8 such items.
     - On the 65 items where h0 lifts: h0 - a +12.15, e - a +9.69.
   - 5a. "picking is not the binding part" (line 10) is contradicted. On those same 65 items, h1 - a is -16.9, about 29 points below h0, so score-based picking binds there as well. The subset is also selected on a GT-dependent event (h0 lifts), and there h0 beats true masks (+12.2 vs +9.7), which points to selection or noise. Fix: drop the sentence, or report h1 - a on the same subset beside it, labelled descriptive.
   - 5b. "The frozen detector's pool misses whole objects" (line 10) is only partly true. pool_iou.py checked the 61 h0-empty operand-item cases (40 distinct capture/prompt/instance units). Best pool IoU over all anchors:
     - < 0.1 in 37 cases (6 with no proposal at all).
     - 0.1-0.3 in 7 cases.
     - 0.3-0.5 in 17 cases. Many of these cover >= 60% of GT, i.e. oversized or merged masks rather than misses. Examples: stove 42446097 IoU 0.36 / coverage 1.00; tv 42446117 0.49/1.00; headphones ad562ce09b 0.49/1.00; mirror in scene0515 0.28/0.92.
     - Six of the zero-IoU units are the ScanNet++ prompt "heater", the known name issue (REPORT_J1.md:5, radiator rewrite deferred). That is vocabulary, not detector recall.
   - 5c. "h0 says recall binds: a fine-tune limited to the score and presence heads cannot reach k" (line 11) does not follow, and it steers the pricing of candidate 2:
     - h0 only sees the retained pool, and retention is score x presence >= 0.05 with a cap of 30 (REPORT_J1.md:6). The score and presence heads therefore shape the pool h0 is bounded by.
     - Part of h0's loss comes from the registered 0.5 IoU abstention (5b).
     - The ruling's item 5 assigns h0 no decision.
     - Fix: remove the sentence, or state it as an open question for the pricing of candidate 2.

6. The rest of the draft matches the files and covers the ruling (non-blocking).
   - Line 2 matches EVENTS.jsonl: card 0, normal priority, readings at 11:09Z and 11:14Z, 46/46, 413 s (412.7), exit 0, CUDA peak alloc 3.93 GiB (reserved 4.22).
   - Line 3 gate counts match RELIFT_J1.md:3-4.
   - Lines 5-7: all intervals and shares match RELIFT_J1.md:8 and :13, and the 35 rooms match.
   - Line 8: every per-dataset number and item/room count matches RELIFT_J1.md:9-11. The draft omits the per-dataset e intervals; that is acceptable.
   - Line 9: correct, since needed = {}.
   - Line 10: the h1 numbers (1,098 anchors; precision 0.32 vs 0.61) match RELIFT_J1.md:20 and :28.
   - The line 11 decisions follow the ruling's item 5: h1 is not a source, so it is not served; h1 falls short and k opens, so candidates 2 and 3 are priced next, with candidate 3 serving the own-encoder goal. No ranking is read into overlapping intervals (ruling item 2).
   - Line 4: the NF-A floor quote ("0.00 on every type, RESULT 1031Z") matches events/lever/20261122T1031Z_RESULT_nfa...md: four types, +0.00 [+0.00, +0.00]. That floor measures item-order noise of the served read, so "order-noise floor" would be more exact.
   - Line 12: 585 rows is correct. Three claims are not verified by this review:
     - that the corpus schema does not fit (ANSWER 0533Z item 3 allows leaving the rows uningested with a one-line note);
     - the files/j1/ copy;
     - the plan-record and MASK_SOURCE design-record entries.
     Confirm that these exist before posting.
   - The <VERDICT> placeholder is expected.
