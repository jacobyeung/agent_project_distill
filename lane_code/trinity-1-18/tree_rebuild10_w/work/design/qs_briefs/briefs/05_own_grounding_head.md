# Build brief 05: own-encoder grounding head (branch O), SAM 3 as teacher, trained on Trinity 48 GB cards

Builder: Claude Opus, high effort. Written by lane queue_synth, 2026-11-16. This is the largest Trinity GPU filler in the queue; every GPU step needs ORCH's GO with the node and card.

## Rules
Read `/home/jjyeung/.claude/CLAUDE.md` section "Key Trinity Cluster Rules", then `B/tools/CLAUDE_LANE_RULES.md` and `B/tools/LANE_RULES.md` (B = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30`). GPU rules: 48 GB cards at normal priority only on trinity-0-13 (the main project has priority there and its /scratch is at its floor: stage nothing there without main's word); every other node only under `/data3/shared/scripts/vnice/vnice.sh`; never trinity-0-8, 0-23, 3-23; leave 0-18 free; two fresh `nvidia-smi` readings 5 minutes apart before a launch. Work vnice kills resumes from its own records only on ORCH's order. No Git, no deletion. Read data from /scratch only; every stream above 20 MB registers with the IO governor; announce any staging above 20 GB on a node to main first. Lane folder `/scratch/jjyeung/orch_n30/own_ground2`; events `B/events/own_ground2/`.

## Why
The end-to-end ruling (user, 2026-11-16) removes SAM 3 proposals, the fitted selector and the alias table from the claimed path. The target is grounding from the student's own vision pathway. The design exists and was never trained: `distill_design/GROUNDING_OWN_ENCODER_20261110.md` (branch O: presence head over all frames, the own frozen ViT re-reads four top frames at up to 1024x768, a decoder of about 45M parameters proposes instances, a selector head picks or abstains; SAM 3 teaches masks and ranking, scan ground truth teaches identity). The language model is not in the loop and the ViT is frozen, so the head trains on single 48 GB cards and attaches to any export of the lineage. Verify the frozen-ViT claim in the leg's config first: B6 section 3(b) says the seal fine-tunes the shared ViT, the GF-1 record says the ViT stays frozen; if the leg trains it, say so in a QUESTION event and train against the export A2 will start from.

## Inputs
- Design and gates: `GROUNDING_OWN_ENCODER_20261110.md` (sections 1.4, 3, 3.4 stop rules, 3.5), `PILOT_FULL_LABEL_PATH_20261111.md` (the r11 full-label CPU path), `B6_GROUNDING_DESIGN_20261115.md` (inventory, eligibility, brief B6-B), `OWN_GROUNDING_KITS_20261112.md`, `MASK_PROPOSAL_RECALL_DEVS1_20261112.md`.
- Lost with trinity-2-18: the head's code (`own_head_code.tar.gz`), the teacher labels (`head_teacher_full.tar`, 205 scenes). Rebuild both from the records.
- Survives: the K1 SAM 3 tower pass on 300 training captures (trinity-1-18 `/scratch/jjyeung/k1/run_tower_sam_2`; kit `orch_cd/k1_build/work/kit_k1a`; mirror trinity-3-30 `/scratch/jjyeung/n30_mirror/k1_ops3/run_tower_sam_2`), 296 GT rasters and their clean-room builder (`K1_GT_RASTER_REBUILD_20261115.md`, `B/events/gt_rasters/`), the SAM 3 tower API (record `sam3_tower`, checkpoint sha 9999e234...), the own-ViT re-read patch (record `own_reread`, 37 CPU tests), kits `own_ground_gpu/kit_{A,B}` on trinity-1-18.
- Scene eligibility: benchmark rooms (`BENCH_SCENE_EXCLUSIONS_20261108.md`, v2), the 152 dev-S1 captures and the 80 withheld rooms never train the head. The old label set held 5 dev-S1 captures: the new one must hold none.

## Steps (a RESULT event after each; stop rules are the design's)
1. Teacher and label pass (GPU, resumable per capture): SAM 3 at the frozen setting on eligible training captures, with GT instance rasters for identity. Start from K1's 300 captures (done), then extend in blocks of about 300 toward the pool's 2,189 scenes. Price from the trace ruling section 2.6: 11 to 17 A6000-hours for proposals on all scenes at the dense setting, 15 for geometry; four to eight cards for 3 to 8 hours. Frames: about 70,000 PNGs, 20 GB, staged once by a governed stream. The same cache serves the head-path rows of brief 08: write it in that brief's format too.
2. Label audit: reproduce the design's P7 numbers on a sample (positive masks 4.6% wrong, MISS rows 36.8% wrong) and train presence only where GT and SAM 3 agree.
3. Pilot (at most 4 A6000-hours, one card): the r11 path; registered stop rules of section 3.4.
4. Full training (design estimate 30 to 60 A6000-hours with the language model frozen; two to four cards if the code shards, else one card for two to three days under vnice with exact resume).
5. Read on K1 held-out rooms (58 captures) and then, once only, on dev-S1: on-target share and name-consistent share against SAM 3 plus selector on the same objects; absolute-distance program score with the head's masks through the reader of brief 04. Bars: the design's non-inferiority rule (parity with the tower at about 50M added weights), fixed before the read.
6. Attach: export the head into the artifact manifest of brief 04 and run EAT-1 (brief 03).

## Tests
CPU: the full-label path on a tiny model, a first batch of real labels through the head's forward and loss on CPU, exact resume, a scene-eligibility test that fails on any dev-S1, withheld or benchmark capture. No test writes a real-size checkpoint. Check `df -h /scratch` every step; the lane cap is 60 GB unless ORCH grants more.

## Price in benchmark points
Only absolute distance consumes masks in the route table, so at parity the head changes no score and makes the distance route claimable end to end. Below parity it costs part of the routed distance gain (+0.96 VSI points strict on the external read; +0.42 [-0.23, +1.08] off the selection scenes). The larger prize is later: with ground-truth masks the programs for relative distance, counting and direction sit 20 to 30 task points above direct, and a head trained on scan ground truth can be improved by training where a frozen segmenter cannot.

## Do not touch
D0 job 170111, the VSTI read, K1's Orchard jobs and its kit copy `kc` on trinity-1-18 while any K1 phase runs, sealed kits, dev-S1 caches as training data.

## Deliver
Code and kit with hashes, the label manifest with its eligibility proof, pilot and full-run reports with the stop-rule verdicts, the K1 and dev-S1 tables, a mirror on a second node, STATUS.md, RESULT events. Review: one independent refute review of the label pipeline's eligibility and the training code before step 3; a second reader on the dev-S1 read's analysis script before it runs.
