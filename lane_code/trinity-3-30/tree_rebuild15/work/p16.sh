W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; O=$W/w24/out; C=$W/work/conf24k; P="nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B"; export CUDA_VISIBLE_DEVICES="" OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1
date -u +%TZ; free -g | sed -n 2p; df -BG --output=avail /scratch | tail -1
B=$W/w24/work/build24f; K=$W/w24/work/build24k; head -30 $K/go_rehearsal_k.sh
tmux new -d -s tr15_rehk "cd $W/w24 && nice -n 10 bash work/build24k/go_rehearsal_k.sh > $K/rehearsal_k_run1.log 2>&1; echo RC=\$? >> $K/rehearsal_k_run1.log; nice -n 10 bash work/build24f/go_rehearsal5.sh out/kit_n_go > $B/rehearsal_run5.log 2>&1; echo RC=\$? >> $B/rehearsal_run5.log"
T=$O/tree_rebuild_b24k_2ace1de4.tar; test -e $C && echo "C EXISTS" || { mkdir -p $C/pkg; sha256sum $T; (cd $C/pkg && tar xf $T); }
ls $C/pkg $C/pkg/work 2>/dev/null | head
for d in $W/w24/work/tree_r1 $C/pkg/work/tree_r1; do (cd $d && $P -c "import sys; sys.path.insert(0,'.'); from student_pilot.source_seal import inventory; from student_pilot.p3_provenance import digest; f=inventory('.'); print(len(f), digest(f))"); done
for k in q n; do (cd $C/pkg/out/kits/$k 2>/dev/null || cd $C/pkg/kits/$k 2>/dev/null || cd $O/../work/build24k/kits/$k 2>/dev/null; pwd; sha256sum SHA256SUMS.txt | cut -c1-16; sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$'); done
(cd $O/kit_n_go && sha256sum SHA256SUMS.txt | cut -c1-16)
echo "==== a.py"; cat $O/kit_n_go/b/a.py | cut -c1-260 | head -70
echo "==== x.py"; ls $O/kit_n_go/b/; cat $O/kit_n_go/b/x.py 2>/dev/null | cut -c1-260 | head -60
sleep 5; tmux ls | grep tr15
