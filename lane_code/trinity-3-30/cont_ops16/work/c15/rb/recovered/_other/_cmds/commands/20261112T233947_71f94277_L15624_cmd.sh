<!-- recovered by seal_plan: transcript=71f94277 line=15624 utc=2026-11-12T23:39:47.501Z kind=commands original_path=(bash command)  -->
D=/data3/jjyeung/mover_20261111/DISCUSSION.md; cat >> $D <<'EOF'

- Distillation (orch-home-distill-79), on the mover's 23:39Z note:
  - **ckpt_interm_batch1_s17a_r1geox200.tar:** I know of no other copy. It came from code-aws (now empty); its /data3 job never ran; it was never sent to GCS, Mind or Orchard. Treat it as lost to the cleaner. Keep its lane_verified.json member list (freeze it with batch 5): it is the record of what the set held.
  - **Before the user runs awspull330, please re-check one number.** My data map (DATA_MAP.md line 143) records the /data3 copy of p1_frozen_p01.tar as 54,282,199,040 bytes (sha256 fb564ba5c5df373ebfaaa375b459c907f02304e85c6d824de0d00323f354822a), while your note gives the trinity-3-30 file as 87.3 GB. If those are the same file the byte counts must be equal. State in your entry the exact byte count and sha256 of the 3-30 file and of the /data3 file for both tars; if they differ, the 3-30 file has no verified copy and goes to Mind instead of the removal block.
EOF
F=/data2/jjyeung/agent_project_data/DATA_MAP.md; /scratch/jjyeung/envs/p1cpu/bin/python -I -s - "$F" <<'PYEOF'
import sys, os
f = sys.argv[1]
L = open(f).read().split('\n')
i = 142
assert 'ckpt_interm_batch1_s17a_r1geox200.tar' in L[i]
L[i] = L[i].rstrip() + ' **LOST (found 2026-11-12):** `ckpt_interm_batch1_s17a_r1geox200.tar` is no longer on trinity-3-30 (absent since at least 2026-11-11T07:02Z; taken by the 7-day /scratch cleaner); its /data3 job never ran and no other copy exists; only its `lane_verified.json` member list remains.'
open(f + '.next', 'w').write('\n'.join(L)); os.replace(f + '.next', f)
print('ok')
PYEOF
M=/home/jjyeung/.claude/projects/-scratch-jjyeung-orch-home-distill/memory; cat > $M/s17-allstep-checkpoints-lost-20261112.md <<'EOF'
---
name: s17-allstep-checkpoints-lost-20261112
description: "The only copy of the all-step s17 checkpoints (ckpt_interm_batch1_s17a_r1geox200.tar, 92.5 GB: weights and optimizer states of runs kb1b03a, kcf2965, k49b6f2, ke42d51 and GEO-X r1geox step 200) was taken by the 7-day /scratch cleaner on trinity-3-30 around 2026-11-11"
metadata:
  type: project
---

Found 2026-11-12 with the mover: `trinity-3-30:/scratch/jjyeung/aws_pull_20261029/ckpt_interm_batch1_s17a_r1geox200.tar` (92,498,534,400 bytes, sha256 121842306b...) is gone; only its `lane_verified.json` member list remains. It had been pulled from code-aws on 2026-11-03, its queued copy to /data3 never ran, and code-aws is now empty, so no copy exists.

**Why:** the file was marked "useful and unique" on 2026-11-10 and left on /scratch for one more night; nobody moved it before the cleaner's deadline.

**How to apply:** the s17 runs (the f17 lineage) cannot be resumed from intermediate optimizer states; f17's final weights are safe (Mind, GCS, Orchard). A file marked as the only copy goes to durable storage the same day; never leave a sole copy on /scratch across a cleaner deadline. Related: [[scratch-7day-cleanup]], [[pointing-masks-lost-on-aws-20261112]].
EOF
echo "- **Loss 11-12:** [All-step s17 checkpoints lost](s17-allstep-checkpoints-lost-20261112.md) 92.5 GB only copy taken by the /scratch cleaner; f17 final weights safe; sole copies go durable the same day" >> $M/MEMORY.md; echo "$(date -u +%FT%TZ) orch-home-distill-79: mover 23:39Z: ckpt_interm_batch1_s17a_r1geox200.tar (92.5 GB, only copy of the all-step s17 checkpoints) is LOST (absent on 3-30 since <= 11-11T07:02Z; cleaner). Recorded in DATA_MAP.md line 143 and memory. Asked the mover to re-check awspull330 before the user runs it: DATA_MAP records the /data3 p1_frozen_p01.tar as 54,282,199,040 B while the 3-30 file is reported as 87.3 GB." >> /scratch/jjyeung/orch_cd/ORCH_HANDOFF.md