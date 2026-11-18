<!-- recovered by seal_plan: transcript=71f94277 line=15091 utc=2026-11-12T21:07:06.182Z kind=commands original_path=(bash command)  -->
M=/home/jjyeung/.claude/projects/-scratch-jjyeung-orch-home-distill/memory; cat >> $M/lesson-launch-kit-must-run-as-in-job-20261112.md <<'EOF'

A fourth defect of the same day: the third job passed the import preflight and the staging, then died in data preparation because files that training rows point to (the pointing stream's target masks) were never staged. The kit's input list names archives and stores, not the assets referenced inside rows, and every rehearsal used synthetic images and geometry. So add a fourth question before any GO: (4) has a stat-only walk of every path pinned inside every stream's rows been run against the staged data on the target cluster, with zero missing.
EOF
cat > $M/pointing-masks-lost-on-aws-20261112.md <<'EOF'
---
name: pointing-masks-lost-on-aws-20261112
description: "code-aws's ap/ tree is empty since about 2026-11-12; the pointing target masks of sets pa3 and pa3b (logical stores p6q2, p6q3) existed only there and are lost; set b2a's masks (p5x9, 28 MB) survive on trinity-2-18 /scratch"
metadata:
  type: project
---

Checked 2026-11-12 (lane orchard_port, read-only): code-aws's `ap/` tree has no entries on /lustre and /scratch/fsw, so nothing can be fetched from AWS any more. The pointing stream's receipt (pc1) pins target masks in three logical stores: p5x9 (set b2a) survives on trinity-2-18 at `/scratch/jjyeung/orch_cd/mixdata/out/pointing_v2/data2root/p5x9` (8,704 files) and `/scratch/jjyeung/orch_cd/streams2/work/extra/x1/point/data2root/p5x9` (3,840 files), 28 MB together; p6q2 (pa3) and p6q3 (pa3b) were written on AWS by streams2's `sb.py`, never copied off (the copy-off covered their receipts and rows only), and exist nowhere.

**Why:** the masks are referenced only inside training rows, so no staging inventory listed them; rows pin each mask's sha256, so a re-render would have to be byte-identical or the receipt must be rebuilt.

**How to apply:** a leg that derives the pointing stream in the job can use only rows whose masks exist (b2a) until pa3/pa3b are re-rendered and their receipt rebuilt. The 2-18 copies are on /scratch (7-day cleanup): archive p5x9 to durable storage. Before relying on any other row-referenced store, check that it exists off AWS. Related: [[lesson-launch-kit-must-run-as-in-job-20261112]], [[scratch-7day-cleanup]].
EOF
echo "- **READ FIRST, 11-12:** [Pointing masks lost on AWS](pointing-masks-lost-on-aws-20261112.md) code-aws ap/ is empty; pa3/pa3b masks (p6q2, p6q3) gone; b2a (p5x9, 28 MB) only on 2-18 /scratch: archive it" >> $M/MEMORY.md; echo ok