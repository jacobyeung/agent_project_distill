hostname -s; df -h /scratch | tail -1
ls -la /scratch/jjyeung/orch_n30/notseen_diag/work/replay2.py /scratch/jjyeung/orch_n30/tower_redecide/work/reprice.py /scratch/jjyeung/orch_n30/tower_redecide/work/reprice2.py /scratch/jjyeung/orch_n30/tower_redecide/work/pose_k1.py /scratch/jjyeung/orch_n30/tower_redecide/work/remote/poses_118.npz 2>&1
for f in $(ls /scratch/jjyeung/orch_n30/gt_audit/ 2>/dev/null); do echo "gt_audit/$f"; done | head -20
ls /scratch/jjyeung/orch_n30/gt_audit/work 2>/dev/null | head -40
for c in /scratch/jjyeung/orch_n30/gt_audit/work/K1_LABELS_CORRECTED.jsonl /scratch/jjyeung/orch_n30/gt_audit/out/K1_LABELS_CORRECTED.jsonl /scratch/jjyeung/orch_n30/gt_audit/K1_LABELS_CORRECTED.jsonl; do [ -f $c ] && { ls -la $c; sha256sum $c | cut -c1-16; head -c 600 $c; echo; }; done
ls /scratch/jjyeung/orch_n30/notseen_diag/work | head -60 | tr '\n' ' '
echo; ls /scratch/jjyeung/orch_n30/reader_r1/work/b1/in/pkg 2>&1 | head -12
