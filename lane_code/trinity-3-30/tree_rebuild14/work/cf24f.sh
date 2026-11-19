W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; C=$W/work/conf24f; P="nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B"; export CUDA_VISIBLE_DEVICES="" OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1
date -u +%TZ; free -g | sed -n 2p; df -BG --output=avail /scratch | tail -1
tmux new -d -s tr14_reh "cd $W/w24 && bash work/build24f/go_rehearsal.sh > $W/w24/work/build24f/rehearsal_run.log 2>&1; echo RC=\$? >> $W/w24/work/build24f/rehearsal_run.log"
T=$W/w24/out/tree_rebuild_b24f_449bc1fc.tar; mkdir -p $C/pkg; cd $C; sha256sum $T; stat -c %s $T
(cd pkg && tar xf $T)
for d in $W/w24/work/tree_r1 $C/pkg/work/tree_r1; do (cd $d && $P -c "import sys; sys.path.insert(0,'.'); from student_pilot.source_seal import inventory; from student_pilot.p3_provenance import digest; f=inventory('.'); print(len(f), digest(f))"); done
cat $W/w24/out/DELIVERY_24F.json | head -c 1500; echo
K=$W/w24/out/kit_n_go; sed -n 1,40p $K/job.sh
tmux ls | grep tr14
