# Inventory: whole-object mask source (SAM 3 video track), lever5. Read-only, 2026-11-21, trinity-2-28.
D=/data2/jjyeung/agent_project_data/distill_design; P=D/ROUTED_READER_LEVER_PLAN_20261120.md; M=/scratch/jjyeung/orch_n30

## 1. What the plan registered
- P:47 question: "what does a perfect 2D mask buy at today's lift, and is the gain selection (an existing candidate) or completeness (a fragment against the whole object)?"
- P:50 reading: "...an oracle-candidate gain of 6 or more with lower bound > 0 opens arm A, and otherwise completeness binds and the next price is a whole-object mask source (SAM 3's video track on K1 train)."
- P:212 verdict (117 items / 46 captures): grounding binds (G=e-a +13.8 [+5.5,+22.3]); completeness binds (oracle-candidate gain -0.2 < 6); arm A closed; "The next price is a whole-object mask source (SAM 3's video track on K1 train)."
- P:108-114 arms: A (selection repair) closed. B (depth head) opens on rank 2 (GT depth alone >= 5, C1 >= 2, ...). The plan names no arm, item count, bar or GPU cost for the SAM 3 video-track price itself: no "items/set", "reading", "bars" or "cost" line exists for it. Rank 1 cost line (P:51): "one general H100 job of 0.5 h".
- P:27: K1 train GT masks 56.8 -> 74.0 (+17.2), with fusion 78.6; "gathered fragments add 0".
- P:49-50: more SAM 3 prompt/frame arms and own-pointing prompts are deferred; own-pointing "reopens if rank 1 finds completeness binding".

## 2. What exists
Weights (SAM 3, 3,450,062,241 B, sha256 9999e234...c8cf9c):
- /scratch/jjyeung/b01ec87a6f29b/d/k/sam3.pt (+SAM3_RECEIPT.json; upstream rev 5dd401d1); staged source /scratch/jjyeung/b01ec87a6f29b/d/s/sam3 (carry kit ran from it).
- /scratch/jjyeung/orch_cd/ttower/work/sam3_weights/sam3.pt (hardlink, same size).
- Envs: /scratch/jjyeung/envs/sam3_capretry_native_v1, sam3_scipy_ovl. Source of record (NFS, not read): /home/jjyeung/agent_project/agent/third_party/sam3.
- Orchard / GCS / other nodes: not checked (no Orchard, ssh or GCS calls allowed).
- M/cont_ops24_c/gbuild/sam3_ref holds only 5 image-model .py files (no README/REPORT; no tracker code). REPORT2.md:3 says the SAM env's `sam3` maps to the NFS source outside the authorized read set.
Prior SAM 3 video-track run (this IS the plan's "SAM 3 video track on K1 train", already done 2026-11-19):
- D/MASK_CARRY_K1_TRAIN_20261119.md (swarm_build, kit sb_cachk.tar 224fbcf4). Tracker seeded by the served best mask (S_A0) over 64 dense frames (D64); masks kept at the 32 anchors.
- Result, decision population 204 captures / 1,012 rows: carry precision 0.7306 (bar 0.90) FAIL; fusion C_fused - A0 -3.19 [-6.47,+0.18] (bar +2.0) FAIL; size +5.87 [+3.34,+8.50] PASS; first-seen 0.7071 (bar 0.90) FAIL. ARKit prec 0.660 fusion -4.51; ScanNet 0.866 / +0.00; ScanNet++ 0.784 / -2.71, size +9.00.
- NOT done: S_GT/D64 (GT-seeded ceiling; 38 of 209 captures finished, killed by vnice at 15:30:43Z, unpriced), A32 sets, S_PHR (phrase seeds). Doc lines 25, 35: a GT-seeded carry "could still reach the precision bar" (then the seed, not the tracker, fails). Resume waited on a saved user question (2026-11-19T15:34Z); no answer found in the files read.
- Files (on 2-28): M/sb_cachk/out/v2/{track/TIMING_RECEIPT.json, track/BUDGET.json, track/EVENTS.jsonl, track/S_A0_D64, track/S_GT_D64, seeds/SEEDS.json, FRAME_SETS.json, BARS_FROZEN.json, GUARD.json, POPULATION.json}; kit M/sb_cachk/kit_v2. Pricing outputs (CARRY_REPORT.md, K1_CARRY.json, price/) are on trinity-1-18 only, per the doc.
- Related: D/MASK_QUALITY_DESIGN_20261119.md (carry = candidate 2, SAM 3 fine-tune = candidate 3, own box head = candidate 4); D/MASK_FAILURE_K1_TRAIN_20261119.md (no-proposal frames carry +8.18 of the 17.2 gap; selection smaller).
- No SAM 3 video-track run on dev items found.

## 3. Data
- K1 train: 239 pinned captures with rasters (ARKit 127, ScanNet++ 71, ScanNet 41), 32 anchors each (7,648 anchors); 64 dense frames per capture on disk; 209 carry priced rows, 204 decision captures / 1,012 rows (MASK_QUALITY_DESIGN:41; MASK_CARRY:7). Rasters live on trinity-1-18 (paths in sb_kbox4/pinned_train.json), per the doc, not verified here.
- On 2-28: /scratch/jjyeung/k1_frames (256 shard dirs, sha-named PNGs), /scratch/jjyeung/k1 (g3t, own_170235, run_convert_2, run_tower_sam_2), M/sb_cachk/out/v2/STAGING_FRAMES.txt lists the staged frames; the carry GPU pass read them here.
- Dev: /scratch/jjyeung/devs1_frames (256 shards) is dev-S1 (152 captures), not the 60 rank-1 captures. Rank-1 package a3b73b53d92a7 (Orchard jobs 174135/174200/174208) reads "the exact served PNGs" of 60 captures (P:3 / PLAN_RANK1.md:3). Local copies: M/lever1_c/r1_fixtures_old/*/work/a3b73b53d92a7 (fixtures only, tiny).
- Answer: the frames the dump read are on Orchard inside that package, but I cannot confirm from local files that they are the 32/64 PNGs per capture, that they are retrievable, or that the 64 tracker frames (vs 32 tower frames) exist there. An e-like cell with SAM 3 masks needs masks on the dump's 32 anchors, plus tracker seeds from them: either run on Orchard in-package (SAM 3 weights there unverified) or stage the 60 captures' PNGs to a node (small; size not measured). Unknown.
- GT masks/NPZ for the 60 captures: Orchard package (rank 1 e/f/g cells); not local.

## 4. GPU time and memory (measured, not estimated, from sb_cachk)
- Card: RTX 6000 Ada, card_bytes 50,867,404,800 (~47.4 GiB), trinity-2-28. Pass: 247 units in 1,964.7 s = 7.95 s/unit (unit = one capture x arm; the doc rounds to 8.0). 15,808 frames embedded at 0.0801 s/frame (1,310 s = 67%); 55,168 object-frames tracked at 0.01006 s each (547 s); overhead 0.427 s/unit; model load 8.9 s.
- Per frame of tracker input: ~0.08 s embed + ~0.01 s per tracked object. 64 frames ~5.1 s embed + objects x 0.64 s + 0.4 s.
- (ii) K1 train, S_A0/D64: all 209 captures done in that pass (~1,600-1,980 s, ~0.5 GPU-h). S_GT/D64 remainder: 171 captures, ~0.4 GPU-h (MASK_CARRY:35); full S_GT ~1,656 s (TIMING_RECEIPT). Full six-arm projection 1.46 GPU-h.
- (i) 60 dev captures: no measurement. Scaling by 8 s/unit and 1 arm gives ~8 min; with 32 or 64 frames per capture and ~2-4 objects per capture, ~5-8 s/capture, ~5-8 min total (estimate, not measured; ARKit captures and larger object counts raise it).
- Peak GPU memory: not recorded in TIMING_RECEIPT/BUDGET (only card size). The run fit a 47.4 GiB card, but was it near the limit is unknown. The 3.45 GB weights plus a 64-frame tracker state fit on this card (the pass completed 247 units without OOM; BUDGET.json failures: []). Same card class (A6000/6000 Ada 49 GB) therefore holds it; an H100 is not needed.

## 5. Unknowns
1. Whether the plan intends a rerun of the already-failed S_A0 carry, or the S_GT/D64 ceiling (whole-object masks from GT seeds), or SAM 3 re-prompted per frame; the plan names no arm, bar or cost for the price. The existing carry result (precision 0.73, fusion -3.19) says seeded tracking is not whole-object; the plan does not cite it (P has no mention of MASK_CARRY: grep not done beyond the lines in section 1).
2. S_GT/D64 and any user answer to the 2026-11-19T15:34Z saved question (SAVED_USER_QUESTIONS.md, not read).
3. Peak GPU memory; dev-capture timing; object counts per dev capture.
4. Whether Orchard holds SAM 3 weights/env and the 60 captures' PNGs at tracker resolution; whether the dump's 32 anchors are a subset of 64 frames.
5. Pricing outputs and rasters sit on trinity-1-18; 2-28 holds track files (S_A0_D64, S_GT_D64 partial) but not the CPU pricing code outputs.
6. Fine-tuned SAM 3 detector (MASK_QUALITY_DESIGN candidate 3) is a different weight; its status is unbuilt/unlaunched per the doc.
