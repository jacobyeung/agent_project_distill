A=/scratch/jjyeung/orch_n30/sb_maskfail/teacher/auth
echo "=== auth"; ls -la $A; cat $A/SHA256SUMS | cut -c1-140
echo "=== auditfix"; ls -d /scratch/jjyeung/orch_n30/sb_auditfix* 2>/dev/null; for d in /scratch/jjyeung/orch_n30/sb_auditfix2; do ls $d 2>/dev/null | head -30; [ -f $d/STATUS.md ] && head -c 1500 $d/STATUS.md; ls $d/out 2>/dev/null | head -20; done
echo "=== K1SPLIT"; ls -la /scratch/jjyeung/orch_n30/k1_ops3/work/k1_split 2>/dev/null | head -12; ls -d /scratch/jjyeung/orch_n30/*/K1SPLIT_R0.json /scratch/jjyeung/orch_n30/*/*/K1SPLIT_R0.json /scratch/jjyeung/orch_n30/*/*/*/K1SPLIT_R0.json 2>/dev/null | head -5
ls -d /scratch/jjyeung/n30_mirror/*R0* /scratch/jjyeung/n30_mirror/*r0* 2>/dev/null | head
