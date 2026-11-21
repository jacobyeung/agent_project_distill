W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
hostname -s; date -u +%TZ; df -h /scratch | tail -1; nproc; free -g | head -2
ls -la /scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/ 2>&1
ls $W | tr '\n' ' '; echo
ls -la $W/w28fix/n_go/k 2>&1 | head -30
ls $W/w28fix 2>&1 | head; ls $W/w18/work/build18/inputs 2>&1 | head -40
ls /scratch/jjyeung/orch_n30/n_review/r1j 2>&1 | head; ls /scratch/jjyeung/orch_n30/n_review1j/work 2>&1 | head -40
for d in $W/w24z11b $W/w24z12 $W/w27fix $W/w28fix; do echo "== $d"; ls $d 2>&1 | head -30; done
ls $W/w28fix/n_go 2>&1
for d in u stage staged pool; do ls -d $W/*/$d $W/*/*/$d 2>/dev/null | head; done
