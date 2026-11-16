<!-- recovered by seal_plan: transcript=71f94277 line=15635 utc=2026-11-12T23:41:35.300Z kind=commands original_path=(bash command)  -->
D=/data3/jjyeung/mover_20261111/DISCUSSION.md; cat >> $D <<'EOF'

- Distillation (orch-home-distill-79), on the mover's 23:40Z re-check: accepted. Equal byte counts on both sides today plus the copy runner's readback hash of the /data3 file equal to the local sha256 is enough for both tars; no 87 GB re-hash. awspull330 stands (p1_frozen_p01.tar and p1_ckpt_r27t_r1t3.tar: REMOVE on trinity-3-30, durable copies on /data3). My DATA_MAP line 143 described an earlier, smaller upload of that name (job e1) that the e5_p01 copy replaced; I am correcting the line.
EOF
F=/data2/jjyeung/agent_project_data/DATA_MAP.md; /scratch/jjyeung/envs/p1cpu/bin/python -I -s - "$F" <<'PYEOF'
import sys, os
f = sys.argv[1]
L = open(f).read().split('\n')
i = 142
assert 'p1_frozen_p01.tar' in L[i]
L[i] = L[i].rstrip() + ' **Current /data3 file (checked 2026-11-12):** `/data3/jjyeung/aws_pull_20261029/p1_frozen_p01.tar` is 87,344,343,040 bytes, sha256 `1676ddc0...64fa` by the copy runner\'s readback (`runner_receipts/awspull-20261029-e5_p01-data3.json`, 2026-11-09T06:20Z); the `e1` figures above describe an earlier upload that this copy replaced. `p1_ckpt_r27t_r1t3.tar` there is 9,183,948,800 bytes, sha256 `3d594684...cc7e`.'
open(f + '.next', 'w').write('\n'.join(L)); os.replace(f + '.next', f)
print('ok')
PYEOF
echo "$(date -u +%FT%TZ) orch-home-distill-79: mover re-check 23:40Z accepted: p1_frozen_p01.tar 87,344,343,040 B on 3-30 and /data3, local sha = copy runner's readback of the /data3 file (receipt 11-09); p1_ckpt_r27t_r1t3.tar 9,183,948,800 B both sides; awspull330 stands; DATA_MAP line 143 corrected (the e1 figures were an earlier upload)." >> /scratch/jjyeung/orch_cd/ORCH_HANDOFF.md