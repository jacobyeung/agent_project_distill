<!-- recovered by seal_plan: transcript=71f94277 line=4562 utc=2026-11-11T16:15:12.941Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd; M=/home/jjyeung/.claude/projects/-scratch-jjyeung-orch-home-distill/memory; cat > $M/lesson-eval-frame-layout-must-match-training-20261111.md <<'EOF'
---
name: lesson-eval-frame-layout-must-match-training-20261111
description: Every read must use the frame layout the checkpoint was trained on (duplicate vs spread); a mismatch costs 3-13 points and once nearly spoiled an official read
metadata:
  type: feedback
---

Before any evaluation launches, check that its frame layout equals the checkpoint's training layout, and have the kit record the layout in the request, every record and the summary.

- f17 lineage (native HF video processor): 32 distinct frames paired natively into 16 temporal groups ("spread"), about 2,300 visual tokens. Its official 63.79 on VSI-Bench 5,130 was read in that format, so it stands.
- T0 / carrier lineage (T0 m800, CP1): 32 frames, each duplicated to fill its own temporal pair ("duplicate"), 32 groups, about 4,160 visual tokens (about 130 per group).
- Measured on T0 m800 (evalx, 2026-11-11): dev 858 = 42.6 (32 spread) / 50.0 (32 duplicate) / 46.7 (64 nested spread); VSI-500 = 44.9 / 57.8 / 49.5. An earlier "+4.6 from 64 frames" compared against 32 spread, not the trained format.

**Why:** on 2026-11-11 every queued READ-0 cell used spread for a duplicate-trained checkpoint; a cross-family review of a sibling kit caught it hours before launch, after I had already told the user that 64 frames helped.

**How to apply:** ask the eval lane for a per-cell table (layout, temporal groups, visual tokens, matches training?) before the first launch of any new kit or checkpoint; more frames is a dev experiment against the trained format, never the default for an official read. Related: [[eval-frames-unrestricted-20261111]], [[eval-protocol-validity-20261030]].
EOF
echo "- **READ FIRST, lesson 11-11:** [Eval frame layout must match training](lesson-eval-frame-layout-must-match-training-20261111.md) f17 = 32 spread (16 groups), T0/CP1 = 32 duplicate (32 groups); mismatch costs 3-13 points; get a per-cell layout table before any read" >> $M/MEMORY.md
T=$(date -u +%Y%m%dT%H%MZ); cat > evalx/inbox/${T}_ORCH_f17_format_answer.md <<'EOF'
# ORCH: f17's trained format is 32 spread, so its 63.79 stands
Lane orchard_cp2 read f17's published run files (events/20261111T1614Z_RESULT_f17_training_format.md in its folder): a fixed 32 frames per row, paired natively by the processor into 16 temporal groups (frame_addressing group16), about 2,304 visual tokens, no 64 or 128 mix. The official read used the same format. No reread is needed.
So: drop the f17 cells at 32 duplicate and 128 spread. Keep ONE optional dev cell, f17 at 64 spread on dev 858 (an untrained length in its native pairing), low priority, after THINK-0; build it only if f17's weights are already on a Trinity node (a copy is on Orchard: /project/community/jjyeung/cp4tk_f17/f17.tar, 20.2 GB; do not pull it for this). Everything else in the order stands.
EOF
python3 - <<'EOF'
p='/scratch/jjyeung/orch_cd/READY_QUEUE.md'
s=open(p).read()
s=s.replace("- OPEN: which layout the f17 official read (63.79) used; if 32 spread, the baseline is an under-read (asked evalx 16:05Z).","- SETTLED 16:15Z: f17 trained on 32 frames paired natively into 16 temporal groups (spread, about 2,304 visual tokens; orchard_cp2 RESULT 1614Z) and its official 63.79 was read in that format: the baseline stands. T0 m800 and CP1 train on 32 duplicate (32 groups, about 4,160 tokens). Optional low-priority dev cell: f17 at 64 spread.")
open(p,'w').write(s)
EOF
echo "$(date -u +%Y-%m-%dT%H:%MZ) orchard_cp2 RESULT 1614Z: f17 trained on a fixed 32 frames per row, natively paired into 16 temporal groups (spread; frame_addressing group16; ~2,304 visual tokens; pixels per frame 16,384-147,456; max seq 16,384), read from /project/community/jjyeung/cp4tk_f17/f17.tar (20.2 GB) on Orchard. So f17's official 63.79 (read at 32 spread) is at its trained format and STANDS. evalx told: drop f17 32-dup and 128 cells; one optional dev cell f17 64 spread. Memory saved: lesson-eval-frame-layout-must-match-training-20261111." >> ORCH_HANDOFF.md