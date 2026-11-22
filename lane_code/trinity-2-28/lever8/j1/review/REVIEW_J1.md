# Fresh review of the J1 kit before its GPU run (lever8, trinity-2-28, 2026-11-22)
Verdict: **NO-GO until one CPU-only fix lands (finding 3.1)**; every other criterion passes. The GPU pass (detect.py) needs no change, but the gate must be fixed and re-sealed before any GPU output exists, so that it stays registered.

## 1. Arms
1.1 h1 (kit/select_j1.py:55-66, 138-145; relift_j1.py:200-202) takes the proposal with the highest float32 score x presence and keeps it only when joint >= 0.05 and score >= 0.3. Because presence is constant within a frame, this ordering equals the served conditional-score order (served/b/e2e_reader/stage1.py:98). No linker runs. Pass.
1.2 GT cannot reach h1. arm_h1 reads only det['text'][name] (score, presence, mask). detect.py:249-260 runs the text prompts before the box prompts and gives each call a fresh backbone dict (stage1.py:87-90; detect.py:129-131). The prompt is the operand name (prompts_j1.py:36-41), not a GT label. Pass.
1.3 h0 (select_j1.py:69-76) picks the highest grid IoU against the bound instance, keeps it at IoU >= 0.5, and leaves the frame empty where GT is empty. Pass.
1.4 k (detect.py:122-150) mirrors Sam3Processor.add_geometric_prompt: text 'visual', the dummy prompt plus one positive box in normalised cx, cy, w, h (sam3/model/sam3_image_processor.py:128-152). It takes the top query by sigmoid x presence (lines 183-189) and runs only on anchors with a box, i.e. non-empty GT (prompts_j1.py:45-47). Pass.
1.5 (non-blocking) The 2 operands without a T1 ground call get an h1 detector pass under the question's name, although cell a is empty for them because the served path never called ground. Report this beside the reading.

## 2. Served contract
2.1 I checked the cited lines against the pinned served copies. stage1.py:21 sets joint 0.05 and cap 30; :24-25 and :82 strip and lowercase the name; :95-99 order and retain; :103-104 resize bilinearly and threshold at > 0. routed_features.py:8 sets SHAPE 480x640, :16-21 hold resize, and :199 keeps mask[::2, ::2]. routed_candidates.py:87 and :99 set the lift floor score >= 0.3. Pass.
2.2 The aliases follow served code, not the design. The design asks for "heater as radiator", but stage1.py bypasses the singular and alias map, and the report states that all dump proposals carry prompt == name. The kit uses no alias, which matches the brief's "served contract exactly". sam3_tower.py line numbers are off by one (encode is at :196), which is cosmetic. Pass.

## 3. Parity stop
3.1 **Blocking.** The registered rule (select_j1.py:115-130) exempts every proposal with score < 0.3 or joint < 0.06 from pairing, so it leaves untested proposals that can still win an arm:
  - h0 picks from all retained proposals, including those with 0.05 <= score < 0.3 (as relift's cell c does with floor 0). Parity never checks that tail, and it is exactly where the rehearsal disagreed.
  - h1 can win with 0.05 <= joint < 0.06 and score >= 0.3, which is also exempt.
  - Parity tests set coverage only. A rank swap between two paired proposals with near-equal scores changes h1's winner and still passes.
  Fix: in relift_j1.parity, also choose h1 (top1) and h0 (iou_oracle on the GT grid) on both the J1 pool and the dump pool for every operand-frame. Count the frame as matched only when the two chosen masks agree (IoU >= 0.95 at 480x640, or both empty). Gate h1 and h0 on this winner rule >= 95% as well as the pool rule. The check reads no score or cell. Add a unit test where a swapped or exempt winner fails.
3.2 The timing is defensible. No h1, h0 or k value existed when the rule changed, and the builder compared the rehearsal only by counts (work/parity_rehearsal2.py, parity_unmatched.py). The builder did, however, choose the looser of two variants after seeing their counts (V2: score < 0.3 or joint < 0.06 exempt; V3: joint < 0.06 only), and on CPU fp32 data that the bf16 GPU run will not reproduce. The fix in 3.1 removes that dependence.
3.3 The bar and the refusal are coded as stated. passed = fraction >= 0.95 (relift_j1.py:156-159). Below the bar, compute(read_text=False) builds only a, e and k (:180-181, 200), the status names k only (:324), and the test confirms that no h1 or h0 appears anywhere. Pass.

## 4. Reading
4.1 compute() checks a and e against a fresh in-process relift.run, item by item (cells and gaps), and checks relift.stats over the fresh rows. A mismatch raises without printing a value (relift_j1.py:224-232). Bootstrap is round7_common's class: precomputed draws (10,000, random.Random(20261120), physical room, item weighting), so the call order does not change them. Pass.
4.2 The verdict bars (select_j1.py:159-168) decide on the 'all' row of 117 items (relift_j1.py:240-241). The rows for ARKit, ScanNet and ScanNet++ carry n and rooms, and they have decides=False. Pass.
4.3 P/R (j1_common.py:109-129) are computed over anchors where GT or the prediction is non-empty. Precision is the mean |P&G|/|P| over predicted anchors, recall is the mean |P&G|/|G| over GT anchors, and pred_on_empty_gt counts anchors with a mask where GT is empty. Arms a, e, h1, h0 and k are covered per dataset and over all. Pass.
4.4 needed_items (select_j1.py:171-196) uses the room-cluster SE^2 = R/(R-1) * sum_r (S_r - m n_r)^2 / N^2 and rooms_needed = R (z SE / margin)^2, where margin = m for the source bar and 8 - m for the closing bar. Items needed = rooms_needed x N/R. A mean in (4, 8) is reported as clearing neither bar. The formula is sound under the normal approximation at the observed mean and spread, while the verdict uses bootstrap percentiles, so the estimate is approximate. supply() lists relift's 33 exclusions and states that R0-dev stays unspent. Pass.
4.5 Each ITEMS_J1.jsonl row (relift_j1.py:218-221) carries item_id, arm, room, dataset, capture, type, per-operand frames_with_mask and frames_with_gt with P/R, lifted_distance_m, printed_gap_m, printed_answer, gt and score. Pass.

## 5. Launcher (kit/launch_gpu.sh)
5.1 The launcher refuses the head node, the five barred hosts and any non-Trinity host (:31), refuses a GPU launch off trinity-0-13 (:32), refuses a ROOT off /scratch (:33; detect.py:177 also checks), and refuses on a seal mismatch (:36) or a KILLED marker (:35). Pass.
5.2 It takes two nvidia-smi readings $WAIT=300 s apart inside the command (:43-45) and writes both to EVENTS.jsonl. A card qualifies only with <= 100 MiB used in both readings, >= 24e9 bytes and capability >= 8 (:51). Exactly one card is visible, in PCI_BUS_ID order (:55). The job runs at normal priority with timeout -k 30 3600 and a hard stop at 3300 s (:68). Every child's exit code and stderr file are logged (:30). Pass.
5.3 The CPU rehearsal (work/rehearsal_cpu, exit 0, 424 s) ran the same inner line. Only the device, captures and anchor limit differ, plus an outer nice -n 10, and test_launch_dry checks this by diff. Pass.

## 6. Checks run on this node (CUDA_VISIBLE_DEVICES='', nice -n 10, /scratch/jjyeung/envs/p1cpu; logs in this folder)
- sha256sum --quiet -c SHA256SUMS_J1 passed (exit 0; 3,752 files; SHA256SUMS_J1 sha256 92c7aa28...f4a1, as the report states). The seal test mutates SHA256SUMS_J1 and restores it; the sha256 is unchanged afterwards.
- tests/test_units.py: 9 of 9 PASS. tests/test_launch_dry.sh: 17 of 17 PASS.
- tests/test_relift_j1.py: RESULT_PENDING
- I printed no arm value.
