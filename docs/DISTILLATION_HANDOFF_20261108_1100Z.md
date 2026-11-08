# Distillation orchestrator handoff, 2026-11-08 11:00Z (03:00 PT Sun)

This file replaces DISTILLATION_HANDOFF_20261104_0800Z.md as the current state. Read the memory index first, then the "STATE 10:50Z 11-08" block at the top of `/scratch/jjyeung/orch_cd/ORCH_HANDOFF.md` on trinity-2-18. That block holds the lane map, the C1-r design, the GPU windows and the plan to the final run. Work from trinity-2-18; every lane dir is under `/scratch/jjyeung/orch_cd/`.

## 0. Goal and rulings in force (user, 11-08)
- **Goal:** a Qwen3.5-9B student that routes to its own perception heads (pose, depth, scale, FoV) with plan-first, head-backed traces. First a POSE-ONLY design sweep (C1 arms), then ONE final mixed run from BASE: the chosen heads + VQA + pointing + routing traces.
- **Speed:** any new experiment RUNNING within 1 h, with <= 30 min of setup. No CPU dry runs; the smoke is the training job's own first steps; no review gate unless legality, admission or scoring changes; arms launch in parallel.
- **Design:** discuss any critical design flaw with the user BEFORE it spends GPUs, using the cheapest decisive test first. Build the model we believe works best and ablate afterwards, never at every step.
- **G3T:** a training-only teacher (features precomputed in a separate job); never at inference. No point clouds or dense maps; predict features. Last layer only (3DRS). Store full-res features for ~1 TB, pooled for the rest.
- **GPUs:** every user number is the main + distillation total unless a lane is named.
  - until 16:30Z: 100 (52/48);
  - 16:30Z-02:30Z: 64, split 32/32 with main;
  - 02:30Z-16:00Z Mon: 100;
  - then the weekday rule: night only (21:30-08:00 PT), <= 32.
- **Data:** keep only first/best/last weights per run, plus logs and evals. Prune continuously through removal kits the user runs. Agents never delete. GCS is temporary staging, empty by ~12-01. Mind is the long-term store.

## 1. Survives vs dies
- **Survives a session close:** every AWS Slurm job (C1 smokes 104066/7/8; the c1r dense cache once submitted; aws_evac copies c3b..c8 and xw exports), the Mind receiver jobs, the Orchard repack chain 166805-166808, GCS objects, and all lane files under `/scratch/jjyeung/orch_cd/`.
- **The five Devin lanes also survive** a session close: each runs detached (parent bash reparented to init, own session), and they survived a session restart at ~11:00Z.
  - Their 86,000-s timeouts end them at about: heads_up5 07:12Z Mon, aws_evac2 07:23Z, c1r 08:06Z, derivgen4 09:40Z, mind_prune 09:44Z. Launch successors before then.
  - Recipe: write `BRIEF_SUCCESSOR<n>.md` next to the brief ("resume, don't restart; read every inbox note and STATUS.md"), then from the repo root: `timeout 86000 devin -p --prompt-file <brief> --permission-mode dangerous --model claude-opus-5-5-max > /scratch/jjyeung/orch_cd/<lane>/<out> 2>&1` (run_in_background).
- **Dies with an orchestrator session:** only its own event waiter (`/scratch/jjyeung/orch_cd/evwait.sh`, run_in_background) and any Claude subagents.

## 2. Lanes: where, how to check, what next
Health checks on 2-18: `pgrep -f <brief>`; `tail -c 800 /scratch/jjyeung/orch_cd/<lane>/STATUS.md`; `ls -t /scratch/jjyeung/orch_cd/<lane>/events | head -3`. AWS: `timeout 40 ssh -o ConnectTimeout=20 -o BatchMode=yes code-aws 'squeue -u jyeung -h -o "%i %j %T %M %b" | grep _ap'`.

| Lane (brief) | Now | On completion |
|---|---|---|
| heads_up5 (`agent/scratch/devin_lanes/heads_up/BRIEF_SUCCESSOR5.md`) | C1-a/b/c smokes queued, with the OOM fix (model.train + gradient checkpointing; kernel check). Fusion probe being built. f17 contiguous readout next | When the probe reads, pick the layout (rule in ORCH_HANDOFF), then release the HOLD on the three 800-step trainings |
| c1r (`.../c1r/BRIEF.md`) | Dense G3T cache: N=224, built from anchors + exact +0.5/+1.0 s partners, last layer only; submit ETA ~11:45Z. C1-r trainer switching to the dense shards | Train C1-r (8 GPUs) once cache chunk 1 lands |
| derivgen4 (`.../derivgen/BRIEF_SUCCESSOR4.md`) | 26 trace fixes + >=300 scenes; style references | 'REVIEW POOL v2 READY' -> readers re-read (`/scratch/jjyeung/orch_cd/trace_readers/`), plus the orchestrator's own 5-per-type read |
| aws_evac2 (`.../aws_evac/BRIEF_SUCCESSOR.md`) | AWS->Mind copies; HX 1483 extraction; owes the REMAINING census | Queue its kits for the user; report numbers |
| mind_prune (`.../mind_prune/BRIEF.md`) | Mind census, repacks, MIND_PRUNE kit | Queue the kit for the user; report free space |

## 3. Open risks to settle before GPUs
- **G3T convention:** its local camera head outputs a gravity-to-camera quaternion + FoV, and its global head world-to-gravity translation + yaw. Check whether G3T is gravity-aligned rather than frame-1-referenced before relying on the "clips include the run's frame 1" rule.
- **Frame layout:** settled by the fusion probe. Patch alignment only with paired or duplicate frames.

## 4. Open user questions (asked once; don't repeat)
1. ANSWERED (USER): trainers save a resume state every ~30 min, keep the newest 2 complete states and delete older ones automatically; milestone weights still go through user-run kits.
2. Project-level best? Default: per-run first/best/last.
3. Mind floor 5% or another store? Default: 10% floor, rest held in GCS; decide by 11-24.
