<!-- recovered by seal_plan: transcript=71f94277 line=8070 utc=2026-11-12T00:29:07.536Z kind=commands original_path=(bash command)  -->
M=/home/jjyeung/.claude/projects/-scratch-jjyeung-orch-home-distill/memory
cat > $M/orchard-queue-facts-20261112.md <<'EOF'
---
name: orchard-queue-facts-20261112
description: Orchard Slurm limits measured 2026-11-12 - advanced gives 4 GPUs at once; preempt 8-GPU waits ~7 days; no scontrol top; no CPU-only node
metadata:
  type: reference
---

Orchard queue facts (orchard_cp2 read-only queries, 2026-11-12; file `/scratch/jjyeung/orch_cd/orchard_cp2/events/20261112T0030Z_RESULT_queue_options.md`):

- Per-user caps (user jjyeung is shared with main): `advanced` (adv_4gpu_qos) 4 GPUs, 1 node, 24 h max; `general` 1 GPU, 12 h max; `preempt` 32 GPUs, 4 nodes.
- A 4-GPU `advanced` job (48 CPUs, 800G) had a start estimate of "now"; a fresh 8-GPU `preempt` job waited about 7 days. Partition weight dominates priority (preempt factor 1, general 900, advanced 1000).
- `scontrol top` is off for users; every pending job accrues age (no accrue limits); a dependent job accrues none until released.
- No CPU-only node exists: a job without GPUs shares a GPU node (208 CPUs, 1.8 TB RAM) on `general`.
- `/project/community` is about 98% full; large files go to `/home/jjyeung/okit` or node-local `/tmp`.

**How to apply:** plan Orchard training as 4-GPU `advanced` legs of at most 24 h chained by exact resume, unless a pending 8-GPU job is already near the front. Check with main before taking the 4-GPU cap ([[gemini-key-main-priority]]). Re-measure before relying on the estimates; they move by days.
EOF
printf '%s\n' '- **Reference 11-12:** [Orchard queue facts](orchard-queue-facts-20261112.md) advanced = 4 GPUs/user starting at once (24 h legs); fresh 8-GPU preempt waits ~7 days; no scontrol top; no CPU-only node; project space full' >> $M/MEMORY.md
cd /scratch/jjyeung/orch_cd; grep -n "HARD DEADLINE on Orchard" ORCH_STATE_20261111T0935Z.md | cut -c1-80