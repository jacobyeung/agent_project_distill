W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; C=$W/work/conf19; P="/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B"; export CUDA_VISIBLE_DEVICES="" OMP_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1
mkdir -p $C/pkg; cd $C; sha256sum $W/w19/out/tree_rebuild_b19_8ea1fe6b.tar; stat -c %s $W/w19/out/tree_rebuild_b19_8ea1fe6b.tar
(cd pkg && tar xf $W/w19/out/tree_rebuild_b19_8ea1fe6b.tar)
for d in $W/w19/work/tree_r1 $C/pkg/work/tree_r1; do (cd $d && $P -c "import sys; sys.path.insert(0,'.'); from student_pilot.source_seal import inventory; from student_pilot.p3_provenance import digest; f=inventory('.'); print(len(f), digest(f))"); done
echo SEALDONE
