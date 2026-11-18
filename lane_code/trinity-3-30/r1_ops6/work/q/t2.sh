set -e
IP=$(getent hosts trinity-3-30.ib | awk '{print $1}'); echo ib=$IP; ip route get $IP | head -1
cd /scratch/jjyeung/n30_mirror/rows_r1/out && du -sh a2_vqa_v7 units_p_slice_v3 2>&1
ls -la a2_vqa_v7 | head -30
tar cf - a2_vqa_v7 | timeout 600 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-3-30.ib "cd /scratch/jjyeung/orch_n30/r1_ops6/store && tar xf -"
echo PIPE_RC=$?
cd a2_vqa_v7 && find . -type f -size +10M -exec sha256sum {} \;
