# J1 kit: SAM 3 frozen detector per frame (h1) and two oracle ceilings (h0, k), relifted inside dump 174135 (lever8, trinity-2-28, 2026-11-22)
Built by the lever8 build subagent under BUILD_J1.md. Nothing ran on a GPU, and no cell value of h1, h0 or k exists. Seal: SHA256SUMS_J1 (3,752 files, sha256 b856184224644cb735868893e1d3d6bf0e2b4034d553e55a425156ca9f258d5a; resealed after the pick gate).
## Served contract (read package of Orchard job 174135; pins in kit/j1_common.py SERVED_PINS equal lever1_c/r1/out/IMPORT_AUDIT.json)
- The detector runs through byte-identical copies in j1/served, imported unchanged: e2e_reader/stage1.py (sha b1a77424) and student_pilot/sam3_tower.py, routed_features.py and routed_candidates.py.
- Prompt: the operand name as the ground call writes it, stripped and lowercased (stage1.py:24-25, 82). All 26,286 dump proposals carry prompt == name, so no alias applies and heater stays heater (12 operands); the design's radiator rewrite belongs to vehicle N.
- Retention: queries in conditional-score order (stable), kept while score x presence >= 0.05, at most 30 (stage1.py:21, 95-99). The dump agrees: min joint 0.05, max 30 per frame, lists contiguous and score-sorted.
- Masks: bilinear to the frame size, > 0, resized to 480x640 (stage1.py:103-104; routed_features.py:8, 16-21). The relift grid is mask[::2, ::2] (routed_features.py:199).
- Lift floor: score >= 0.3 (stage1.py:134; routed_candidates.py:87, 99).
- Tower: Sam3Tower with a pinned checkpoint and sources (sam3_tower.py:149-182), bf16 on CUDA (126, 184-193), encoded once per capture (195-221). Frames: PIL RGB from PNG bytes (h1eval/native.py:94).
## Arms as built (kit/select_j1.py; masks on relift's (32,240,320) grid)
- h1: on each anchor, the top retained proposal by score x presence (float32), kept if joint >= 0.05 and score >= 0.3; otherwise empty. Ties keep the served order.
- h0: on each anchor, the retained proposal with the highest grid IoU against the bound GT instance, kept if IoU >= 0.5; empty where GT is empty.
- k: the GT tight box (normalised cx, cy, w, h) as the only prompt on every anchor with GT. It mirrors Sam3Processor.add_geometric_prompt (text "visual", dummy prompt plus one positive box; sam3_image_processor.py:128-152), takes the top query by sigmoid(logit) x presence (lines 183-196) and applies stage1's mask rule.
- Prompts (out/PROMPTS_J1.json): 170 names over 46 captures, 234 operands (2 without a ground call), 170 k units; 5,440 text and 1,064 box prompt-frames.
## Parity rule (relift_j1.parity; registered before any GPU output)
- The gate pairs J1's and the dump's retained proposals one to one, greedily by 480x640 IoU >= 0.95. An operand-frame matches when every proposal on either side with score >= 0.3 and joint >= 0.06 has a partner. Proposals below either level may stay unpaired, and two empty lists match.
- Bar: 95% of the 7,424 operand-frames (232 operands x 32). Below it, relift_j1 computes neither h1 nor h0, and the status names each cause ("h1 not read: pool parity n/N ..."); k is read.
- The strict rule (same count, every proposal paired) is reported beside the gate and does not decide.
- Why the rule changed after the rehearsal: on the rehearsal capture (CPU fp32 against the dump's bf16) the strict rule matched 50 of 64 operand-frames, and the registered rule matched 62 of 64. Every strict miss sat near the 0.05 floor, at the cap of 30, or among near-equal low-score queries.
- The GPU run uses bf16 like the dump but a different card, so parity remains the main risk. Two empty masks now count as identical (the dump holds 9 empty proposal masks).
- Pick-agreement gate (added after the fresh review, finding 3.1, before any GPU output): the pool rule exempts proposals under score 0.3 or joint 0.06 that can still win an arm, and it misses rank swaps among paired proposals. On every operand-frame, relift_j1.parity applies the h1 rule and the h0 rule (on the bound GT) to both J1's pool and the dump's pool. The two picks agree when their 480x640 masks have IoU >= 0.95 or both are empty (select_j1.pick_match).
- An arm is read only when the pool gate passes and its own picks agree on >= 95% of operand-frames. A failed arm is not computed, its status says why, and k is still read. RELIFT_J1.json holds both gates' counts (parity, parity.picks). On the rehearsal capture (CPU fp32 against bf16), the picks agreed on 62/64 operand-frames for h1 and 64/64 for h0 (work/pick_rehearsal.py, counts only).
## Reading (relift_j1.py; prints only its status)
- a and e come from relift's own code path and must equal a fresh in-process relift.run item by item, plus relift.stats; a mismatch raises without printing.
- For X in h1, h0 and k: X - a with relift's Bootstrap (10,000 room draws, seed 20261120) and the share (X-a)/(e-a). The verdict applies the registered bars on all 117 items: source (opens for h0 and k), closes, or undecided.
- Per dataset (ARKit, ScanNet, ScanNet++), the same numbers carry item and room counts and do not decide.
- Per-anchor P/R for a, e, h1, h0 and k over (item, operand, anchor) with GT or a prediction non-empty: precision over predicted anchors, recall over GT anchors. The count of anchors with a mask where GT is empty is reported.
- For each undecided arm, select_j1.needed_items gives the paired items and rooms needed to clear the nearer bar, from the room-cluster SE at the observed mean and spread. A mean between 4 and 8 clears no bar at any size, and the output says so.
- Supply: relift's 33 excluded manifest items with their reasons and rooms; R0-dev stays unspent.
- Outputs: out/RELIFT_J1.json, out/RELIFT_J1.md, out/ITEMS_J1.jsonl (one row per item and arm).
## Forecast (one card on trinity-0-13, normal priority)
- GPU: about 11 min (detect.py --forecast, 635 s from K1's rates of 0.08 s per embedded frame and 0.064 s per prompt-frame, plus load), after 5 min of nvidia-smi readings; timeout 3,600 s.
- GPU peak memory: estimated 6-8 GiB, not measured (3.4 GB fp32 weights plus bf16 activations; K1's video model peaked at 5.3 GiB). The job records it per capture.
- Host: the CPU rehearsal peaked at 12.0 GiB RSS. Output: about 30 MB.
## Transfer list (root /scratch/jjyeung/orch_n30/lever8/j1; 551,934,516 bytes in total)
- To 0-13:
  - kit/ (128,438 B, without kit/__pycache__) and served/ (77,229 B);
  - pyextra/ (153,563,554 B: scipy 1.14.1, which the SAM 3 env lacks and routed_features imports);
  - frames/ (396,983,842 B: 1,472 anchor PNGs, sha-checked against the binding);
  - out/FRAMES_J1.json (497,063 B), out/PROMPTS_J1.json (258,320 B) and SHA256SUMS_J1 (426,070 B).
- Expected on 0-13 already, because K1 and GTC-D ran there with these paths: /scratch/jjyeung/b01ec87a6f29b/d/k/sam3.pt, d/k/SAM3_RECEIPT.json, d/s/sam3 and /scratch/jjyeung/envs/sam3_capretry_native_v1. The launcher refuses if any is missing, and Sam3Tower checks their sha256.
- Back to 2-28: out/detect (about 30 MB).
## Lane commands
1. On 2-28: cd /scratch/jjyeung/orch_n30/lever8 && tar cf - --exclude=j1/kit/__pycache__ j1/kit j1/served j1/pyextra j1/frames j1/out/FRAMES_J1.json j1/out/PROMPTS_J1.json j1/SHA256SUMS_J1 | ssh -o ConnectTimeout=20 trinity-0-13.ib "mkdir -p /scratch/jjyeung/orch_n30/lever8 && cd /scratch/jjyeung/orch_n30/lever8 && tar xf - && cd j1 && sha256sum --quiet -c SHA256SUMS_J1 && echo OK"
2. On 0-13: cd /scratch/jjyeung/orch_n30/lever8/j1 && tmux new-session -d -s j1_gpu "bash kit/launch_gpu.sh"
3. On 0-13: cd /scratch/jjyeung/orch_n30/lever8/j1/out && tar cf - detect | ssh -o ConnectTimeout=20 trinity-2-28.ib "cd /scratch/jjyeung/orch_n30/lever8/j1/out && tar xf -"
4. On 2-28, after a fresh review: cd /scratch/jjyeung/orch_n30/lever8/j1/kit && CUDA_VISIBLE_DEVICES= nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B relift_j1.py (about 25 min of CPU)
## Tests (all pass; p1cpu, CPU; rerun on the sealed bytes)
- tests/test_units.py, 10 groups: top-1 rule and floors; IoU oracle and arms; box from GT; 480 to 240 resize; parity matcher (strict, boundary and empty masks); pick agreement (agreement, a rank swap caught, a sub-0.3 h0 winner caught, both empty); P/R toy with the empty-GT count; verdict bars; needed-items closed form; mask codec.
- tests/test_relift_j1.py, on the real dump with toy outputs and no value printed (1,259 s):
  - the GT store gives h1 = h0 = k = e on 117 items, with P/R of 1;
  - the served store gives h1 = a;
  - the dump pool against itself matches all 7,424 operand-frames under both pool rules and both pick gates;
  - the GT store fails parity, so no h1 or h0 appears anywhere and k = e;
  - gates() names each cause, and a failed h0 pick gate drops only h0 (rows, statistics, records), while h1 and k are still read;
  - main() on toy files writes the status "h1 not read; h0 not read; k is read", the .md and 351 per-item rows;
  - the store refuses a missing capture file and a failed INDEX.
- tests/test_launch_dry.sh, 17 checks:
  - the head node and the five barred hosts are refused, and a GPU launch off 0-13 is refused;
  - busy cards are refused, including a card busy only in the second reading;
  - both nvidia-smi readings land in EVENTS.jsonl, and only one card is visible;
  - the rehearsal runs the same inner line;
  - wrong arguments and a changed seal are refused.
## CPU rehearsal (bash kit/run_cpu_rehearsal.sh scannet/scene0642_01, the launcher's own line; the capture with the fewest operand-frames, 68)
- Exit 0 in 424 s: load 10 s, encode 339 s for 32 anchors, text 69 s for 2 names x 32, boxes 4 s for 4.
- It produced 152 text proposals and 4 box masks, all finite and non-empty, and nothing was scored. Output is in work/rehearsal_cpu.
- After the rehearsal I changed select_j1.py (the parity rule and the IoU of empty masks), which only relift uses; detect.py did not change.
## Removal candidates (nothing deleted)
- work/smoke1, work/smoke_tmp, work/probe*.py, work/diag_*.py, work/parity_*.py, work/toy_detect_*, work/toy_out_*, work/dry_launch*, work/gpu_cache, work/*_inner_*.sh and kit/__pycache__.
- The rm_guard hook queued three commands from this build in /home/jjyeung/agent_project/agent/PENDING_USER_COMMANDS.md; none is a needed deletion, and the user can drop all three.
