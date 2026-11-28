# Lane: w1_student_state (Read-Only Recon)

## Goal
Produce a concise, verified ground-truth dossier of where our specialized fine-tuned spatial understanding model (the distillation student) stands TODAY (2026-11-28): current architecture, best verified scores across benchmarks, active or recently stopped training/eval runs, available checkpoints & compute (Trinity + Orchard), and exact open blockers.

## Hard Cluster & Safety Rules
- READ-ONLY research. Do NOT edit repo code, do NOT delete anything, do NOT run `git` commands, do NOT run broad NFS scans (`find`, `du`, `ls -R`, `grep -r`, bare `rg` over `/home` or `/data*`). Use explicit file paths and bounded reads (`head`, `tail`, `rg -n` on a single file).
- At most 1 quick batched SSH check to `orchard` (with `timeout 15 ssh -o BatchMode=yes -o ConnectTimeout=8 orchard 'squeue -u $USER'`), NEVER SSH to Trinity head node or loop SSH.

## Exact Files / Places to Inspect
1. `/data2/jjyeung/agent_project_data/distill_design/ARCHITECTURE_CURRENT.md`
2. `/home/jjyeung/agent_project_distill/docs/DISTILLATION_HANDOFF_20261110_0110Z.md` (skim key architecture/checkpoint pointers only)
3. Recent design records in `/data2/jjyeung/agent_project_data/distill_design/`:
   - `NEXT_LEG_DECISION_20261117.md`
   - `R1_M200_TRACE_ANALYSIS_20261119.md`
   - `ROUTED_READER_LEVER_PLAN_20261120.md`
   - `N_174444_RESUME_KIT_20261122.md`
   - `N_W35_LAUNCH_REVIEW_20261122.md`
   - `MASK_SOURCE_AFTER_TRACKER_DESIGN_20261122.md`
4. Latest status events in `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/n_ops/` (list top 15 newest files with `ls -lt`, read only the 2-3 newest summary/status/score files!) and `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/lever/` (top 10 newest, read latest result/summary).
5. `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/ORCHARD_LEDGER.jsonl` (tail -n 30 only).
6. `/home/jjyeung/distill-paper/FACTS.md` (check top headings / summary tables only, bounded reads).
7. One single `timeout 15 ssh -o BatchMode=yes -o ConnectTimeout=8 orchard 'squeue -u $USER -o "%.10i %.9P %.20j %.8T %.10M %.6D %R"'` to see if any Orchard training/eval jobs are live right now.
8. Check `/home/jjyeung/agent_project_distill/agent/handoff_liveness.json` (if non-empty).

## Deliverable
Write a crisp, high-signal markdown report (max ~250 lines) to:
`/scratch/jjyeung/orch_home_distill/bluesky_20261128/reports/w1_student_state.md`
Include:
1. **Current Student Architecture** (base model, heads: depth/pose/gravity/selector/grounding, frozen towers like G3T/SAM3, frame count, routing vs direct paths).
2. **Verified Benchmark & Dev Numbers Table** (exact numbers + citations: VSI-Bench, ReVSI, VSTI, dev-S1, R0-dev, K1, E0 nav, LIBERO/VLA status; compare base vs student vs SOTA open/closed targets).
3. **Active / Queued / Recently Stopped Runs** (Orchard squeue, latest leg N / R1 / lever status, Trinity GPU/node availability).
4. **Top 5 Structural Ceilings Right Now** (with exact numbers showing where points are lost).

Print a concise <=20-line summary to stdout when done.
