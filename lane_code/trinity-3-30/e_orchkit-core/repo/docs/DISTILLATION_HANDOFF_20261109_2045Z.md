# Distillation orchestrator handoff, 2026-11-09 20:45Z (12:45 PT Mon)

This file replaces DISTILLATION_HANDOFF_20261108_1100Z.md as the current state. Read the memory index first, then the entries from 13:15Z on in `/scratch/jjyeung/orch_cd/ORCH_HANDOFF.md` on trinity-2-18. Work from trinity-2-18; every lane dir is under `/scratch/jjyeung/orch_cd/`.

## 0. Goal and rulings in force (user)
- **Goal:** make the student's own pose, depth and grounding accurate enough that routing to them beats direct answering on the hard VSI-Bench and ReVSI questions. Reach SOTA on ReVSI and VSTI, then on dynamic and multi-view benchmarks. Always run the highest-signal experiment, read it within hours, and leave no GPU idle.
- **Product (11-09):** one end-to-end model that runs locally, ~9-11B, with no agentic loops.
  - Tower calls inside one generation pass are fine (G3T; SAM 3 if needed).
  - The user would prefer the base vision encoder at higher resolution, but for pose the evidence below rules that out.
- **Freedom (11-09):** drastic architecture changes and other bases of ~9-13B are allowed, and so are 64 or 96 frames.
- **GPUs:**
  - **AWS: NO MORE (USER 11-09 ~12:51 PT "stop aws gpus", then ~12:54 PT "no more aws").** No AWS use of any kind: GPU or CPU jobs, copies, ssh, sbatch. All distillation AWS jobs were cancelled at 20:52-20:54Z: CP1 137064 (resumable checkpoint_000346 left on AWS), the CPU array 135321, the sender 109470 and the dry run 137085. Plan only on Trinity, Mind and Orchard.
  - **Orchard:** one serial advanced-QOS 4-GPU slot, full tonight.
  - **Trinity:** 0-13 at normal priority, other nodes only under vnice, never 3-23.
- **Keep (11-09):** best and last weights per run, plus the full resumable state of each line's strongest checkpoint.
- **Effort (11-09):** max effort is allowed until Mon 18:00 PT when quality matters; Argon cross-checks are welcome.

## 1. What today settled
- **Pose: the Qwen encoder is the limit** (record `distill_design/POSE_PLATEAU_DIAGNOSIS_20261109.md`).
  - A probe on Qwen's ViT tokens reads pose at chance (63-81 deg direction) at 1x and 2x pixels. The LM rebuilds pose only to T0's level (13-25 deg).
  - G3T's camera tokens read 7.5-11 deg, and G3T's own pose 3.1-3.6 deg.
  - Capacity (overfit to 5.7 deg), labels and generalization are ruled out.
  - So pose and depth come from G3T x s (decode), not from pixel or readout levers.
- **GX arms at m200:** frozen G3T inputs gave 10.4 deg and native resolution 9.8 deg (+0.6 only); ft gave 9.8 deg. A student head on G3T features still sits at ~2.7x G3T's own error, so camera types keep decoding from G3T's own head.
- **TOWER-0 = PARTIAL-1** (record `DRASTIC_ARCHITECTURE_20261109.md`).
  - Pose passes, including unseen scans_test. Depth: G3T x s reaches AbsRel 0.063.
  - Grounding fails: SAM 3 zero-shot gives 74% in-mask with 66% null, and the A1 fine-tune 67.6% / 79.7%. A1 masks in the routing programs win 0 of 4 types with CI > 0.
  - T0's V-C depth reads ARKit 21% long, so CP2 adds ARKit depth rows.
- **CP1** (B+C config, started early at 12:46Z) **passes its m200 floor:** VSI-500 +0.3 [-3.0, +3.7] and dev 858 +5.2 [+2.5, +7.9] against T0 m800. Room size recovered (MRA 0.680, ratio 1.000). Two open issues:
  - route-planning loops: the direction template took over 50 of 50 route items, with 9 capped (-16.0);
  - a training pose rise (1.21x its best), with a ~5% held-out translation slip.
- **T0 m1200:** the best direct read (+3.8 dev), but its pointing canary fails (null 42.0 vs 58.9), so it is not used as an init.
- **Baselines verified** (memory `sota-bars-9b-20261109`): GeoWeaver-10B 75.05 VSI / 57.5 ReVSI; Cambrian-P 73.7 at 128 frames; SpatialAxiom-9B unverified.

## 2. Survives vs dies
- **Survives a session close:**
  - no AWS jobs (all cancelled at the user's word);
  - the six detached Devin lanes;
  - mdg_build's governed Mind -> 0-13 pulls;
  - all lane files under `/scratch/jjyeung/orch_cd/`.
- **Lane timeouts (Tue UTC):** gx_build 09:21Z, aws_evac 12:01Z, p3_build 13:12Z, mdg_build 13:15Z, evalx 14:40Z, loss_doctor 15:35Z.
  - Rotate each lane before its timeout. Write `BRIEF_SUCCESSOR<n>.md` ("resume, don't restart"), stop the old lane at a sleep (TaskStop or kill), and confirm it is gone.
  - Launch from the repo root: `timeout 86000 devin -p --prompt-file <brief> --permission-mode dangerous --model claude-opus-5-5-high > /scratch/jjyeung/orch_cd/<lane>/<out> 2>&1`.
- **Dies with the orchestrator session:** its event waiter and lane watcher, and the queue watcher. Copies are in `/scratch/jjyeung/orch_cd/orch_tools/` (`evwait_lean3.sh`, `lanewatch.sh`; edit the BRIEF map); re-arm both with run_in_background.

## 3. Lanes: where, how to check, what next
Health check on 2-18: `pgrep -f <brief>`; `tail -n 3 /scratch/jjyeung/orch_cd/<lane>/STATUS.md`; `ls -t /scratch/jjyeung/orch_cd/<lane>/events | head -3`. CP1: `tail -n 1 /scratch/jjyeung/orch_cd/p3_build/logs/watch_cp1_137064.log`.

| Lane (brief) | Now | On completion |
|---|---|---|
| p3_build5 (`agent/scratch/devin_lanes/p3_build/BRIEF_SUCCESSOR5.md`) | **CP1** (root ap/f2ad01ad, run 49becb79) STOPPED at the user's word (job 137064 cancelled 20:52Z; resumable checkpoint_000346). **CP1-R** (root ap/9281911f: route rows 3x, room 5x, pose weight 1.5, init CP1 m200) READY, with its CPU check PASS. **CP2** kit building (trainer cp2-20261109 fbe516c = gx 45f37ec; VQA o7 158,728 rows at 64 nested frames; pose mix option (b) with 15k ARKit sensor-depth rows plus A4 rooms; pose weight 1.5) | When the user allows AWS GPUs again: resume CP1 from checkpoint_000346 (or launch CP1-R), with m400 read and loss_doctor's call as planned |
| evalx2 (`.../evalx/BRIEF_SUCCESSOR2.md`) | Every read runs on AWS: m400 in the pause, later milestones between legs, the first ReVSI dev read (cap71) in a gap. Fusion-aware reader X31 for GXP-mix. The Trinity runtime is abandoned (tunnel) | Post each read as an event; the m400 read goes to loss_doctor |
| loss_doctor2 (`.../loss_doctor/BRIEF_SUCCESSOR2.md`) | Watches CP1 every 25 steps. **m400 switch rule:** route caps >= 15/50, VSI-500 caps >= 20, uncapped VSI-500 < T0 - 3, held-out centre >= +3 pts or direction >= +1.5 deg, or pose ratio > 1.30x for 2 windows. CP1-R init by trip reason (pose/accuracy -> m200; caps -> m400) | Post the call within 30 min of the read |
| gx_build (`.../gx_build/BRIEF_SUCCESSOR.md`) | **GXP-mix** trainer 45f37ec (R8 GO); AWS kit aws_gxpm (root 56b7153a, world 8). Sized CPU array 135321 runs ~5 h. Launches only on an ORCH GO at the m400 re-plan or a USER grant | cg1 160-row 2-GPU check -> t leg -> m200 read against CP1 (evalx X31) |
| mdg_build (`.../mdg_build/BRIEF.md`) | **MDG-A** (39M mask decoder on frozen T0 m800). Data via Mind: T0 m800 ~21:40Z, frames ~22:25Z, then canaries, CPU first batch and IB stage. Launch on 0-13 GPUs 0-4 ~23:00Z; fail-fast ~23:40Z; read ~Tue 06:00Z. Backups: Orchard kit okit_mdg; AWS kit | Read against the MDG record's GO/NO-GO bars, with bar R through ttower's W10 programs |
| aws_evac3 (`.../aws_evac/BRIEF_SUCCESSOR3.md`) | AWS -> Mind: CP1 milestones under the keep rule, the 4 held arm states, held items (~1.33 TB) while Mind > 3 TB free (9.4 TB free at 17:33Z). rmkit16 dry run 2 (132671) | Post the dry-run summary for ORCH review; a kit goes to the user only after that review |

## 4. Orchestrator decisions due
- **No more AWS (USER).** Re-plan training on Orchard (one 4-GPU H100 slot when free) and Trinity 0-13 (7 RTX 6000 Ada beside main's idle SAM 3 daemons). CP2 at its designed 32-H100 scale is no longer feasible. MDG-A continues on 0-13. aws_evac lists everything of ours that is still only on AWS.
- Review the rmkit16 dry run 2.
- Rotate gx_build before Tue 09:21Z.
- When CP2 launches: after CP1/CP1-R, or replacing it once CP2 is READY and GXP-mix has read.

## 5. Infrastructure facts learned today
- **The code-aws tunnel** (the user's Mac reverse tunnel) moves bulk data at only 0.25-0.8 MB/s. Never pull big data AWS -> Trinity; route it via Mind (AWS -> Mind direct at 40-50 MB/s, then Mind -> Trinity through the governor).
- **The IO governor** serves all orch_cd lanes as one serial stream (~2-4 MB/s under main's load). Lanes order their streams by priority number.
- **A governor floor-throttle** on a stream that shares the code-aws ControlMaster freezes every AWS ssh on the node. Bulk pulls use their own ControlPath, never `ControlPath=none`.
- **AWS cpu nodes:**
  - their /tmp is RAM-backed, so CPU first-batch checks stage only the members each first batch reads;
  - a row takes 7-12 min on CPU;
  - cpu-normal allows 2 nodes per AWS user, shared with main, so our lanes hold at most 1.
  - Check scope: new trainers or streams get rank-first rows plus one row per type; a config-only variant gets only its new rows.
- **Stops:** never USR1, on AWS or Orchard. Use a plain scancel after a complete save.
- **The dense G3T cache** binds loader-module hashes (c1r_ref.py), so editing those modules breaks cache rows. A pin test now guards them.
- **Orchard:** community nodes fill up, /project/community is full, and node-side GCS reads need signed URLs that no available account can mint.

## 6. Open user questions (asked once; don't repeat)
1. May SAM 3 sit inside the model as a grounding tower? Default: yes.
2. May the read-only AWS -> Mind copy-off resume (no compute)? Default: no; AWS stays untouched.
