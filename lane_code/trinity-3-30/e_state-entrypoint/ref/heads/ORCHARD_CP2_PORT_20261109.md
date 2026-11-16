# Orchard port of the 9B line: CP1-Rv first, CP2 pieces at leg boundaries (lane orchard_cp2, 2026-11-09)

Status: QUEUED, AT RISK (2026-11-11 20:41Z). 168042 (CP1-Rv on r9b) is pending with a Slurm estimate of 04:54Z Sun 15 Nov, but its kit authorization expires at 20:50Z Sat 14 Nov, so a start after that time fails at once. 168043 (CP2 on r10c) follows it. An in-place entry swap (out/SWAP_LEGS1_DESIGN.md, tested offline) can give the slot to LEG-S1 or to a re-sealed kit without resubmission; it runs only on ORCH's written confirm.

## Question
How does the 9B full fine-tuning line run on Orchard's 4 x H100 without AWS, and what launches first?

## Answer
- **First launch is CP1-Rv** (REPLAN_RULINGS item 4): CP1-R's recipe on the CP2 trainer at world 4, with the inputs that survived AWS.
  - Trainer: c1mix `orchard-cp2-w4` 299ad02 = cp2-20261109 fbe516c + f57eeb0 (a final-mode config sets `warmup_ratio`, `wall_seconds`, `stop_before_seconds`) + 8619839 (the first-batch check records the forward peak per row) + d0523b1 (`export_at_stop`: a leg's budget stop exports weights and heads) + 299ad02 (flag-free policy `cp2-routed-20261110`). Absent keys keep the old behaviour.
  - Recipe: world 4, `reference_world_size` 32, global batch 160, mix `[pose, vqa, vqa, pointing, routing]`, 1,000-step cosine, warmup 0.05, leg wall 84,600 s with a 3,600 s reserve, and an export at every milestone and at the budget stop. LR 1e-4/1e-5, LR scales 0.6, pose weight 1.5, depth 0.25. Leg 1 ends at its boundary; its last export warm-starts the end-to-end leg (VLM_E2E_NEXT_LEG_20261110 section 9).
  - Streams after prep (everything AWS-only is lost): pose 202,884 (A2 a2v3 22,724 + A3 a3v2 180,160 under division A3 f41d15aa, after dropping 4,880 + 23,360 benchmark-scene rows); VQA 148,876 (CP1's vxm); pointing 205,635 (pc1); routing 37,777 (rebuilt r1 from derivgen6 v3.11 camera rows over 356 scenes; CP1's stream had 66,934 rows over 4,051 scenes). Preparation receipt 32908e5f.
  - Init CP1 m200 (artifact c1a42588), heads pose + depth, depth_init 97a6a3eb. Validation = the readout bank at step 0 and each milestone (the validation slice is lost).
- **Kit:** `work/okit_cr` (root 8865619b; Orchard `/home/jjyeung/okit/x/8865619b`), built by `work/mkkit_cr.py` (`OKIT_VARIANT=dry` builds the frame-less routing key c1d5e6d0). Jobs: `jp` (prep + first-batch check, general 1 GPU), `jc`, `jt4`/`ju4` (advanced 4 GPUs, 24 h). Training modes need `cfg['preparation']` bound from jp's receipt (`bind_prep.sh`, then a rebuild).
- **CP2-only code is inert for this config:** on step 1's rows, trainer 8619839 at world 4 and CP1-R's trainer e6456bc at world 32 give bit-identical losses and components on the same receipt and GPU (jc 167660; pose, VQA and pointing, 128 rows). Routing is untested until the real key. Mode c runs this A/B (`b/ab.py`) and writes `<job>.abcmp.json`. Both trainers, and the world-8 arm, draw identical (stream, index) rows for steps 1-30 (`work/ab/plan_ab.py`, CPU).
- **World-8 leg (REPLAN item 9):** arm 2, config c1d5e801 (run c1d58a01, shares arm 1's preparation), `b/jt8.sh` in the preempt QOS with 8 GPUs for 24 h; submitted as 167705. Its states stay in node /tmp, because the trainer keeps every superseded ~110 GB state (about 2.4 TB per leg) and /project/community has 499 GB free. The job is `--no-requeue`, because attempt files are named by job ID. A preempted leg resumes as a new submission on the same node (`b/r8.py` picks u only on a parseable complete state); otherwise it warm-starts from the last GCS export.
- **Exports:** GCS `q8/8865619b/<run>_m<step>.tar` in 4 parts, through 64 sessions minted on 2-18 (Orchard `sess.json`). The budget-stop export uploads as `<run>_mstop`.
- **CP2 piece (REPLAN item 5), flag-free only:** the flagged r2 never joins (ORCH 0514Z). r3 = the same 95,932 rows of 10 routed types under policy `cp2-routed-20261110` (pin 121375c4). Arm 0's route table drops those types' direct VQA rows, so no type appears in both forms.
- **Route:** Mind -> GCS -> Orchard login -> `/project/community/jjyeung/distill/okit/in/cr` -> node /tmp; files built on 2-18 go 2-18 -> Orchard cache as governed pushes.

## Evidence
- jp-dry 167620 (orchard-community-3, 01:30-02:10Z): staging 8 min, prep 14 min, first batch 4.5 min. Pose 32/32, VQA 64/64, pointing 32/32 finite; routing 0/32 by design (no frames). No-grad forward peak 21.96 GiB, 0.72 s per row, at most 4,871 tokens.
- C1 dense cache ap/c5b61f35 (1,474 GB, 443 blobs) cannot pass through /project/community; ORCH dropped C1 clips from leg 1. C1 clips carry zero depth masks.
- Rates: Mind -> GCS 49.4 MB/s per stream; GCS -> Orchard login ~39 MB/s per stream.
- Orchard node /tmp 5.3-5.9 TB free; /project/community ~550 GB free.

## Options rejected
- Whole dense cache to Orchard: 1.47 TB through a ~550 GB shared cache.
- Six 4 h legs per 24 h allocation: ~1.3 h of restarts a day; one 22.5 h leg instead.
- CPU first-batch check: 380-740 s per row; one H100 does 0.72 s.
