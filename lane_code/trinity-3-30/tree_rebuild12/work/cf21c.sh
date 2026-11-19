W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; C=$W/work/conf21c; P="nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B"; export CUDA_VISIBLE_DEVICES="" OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1
T=$(ls $W/w21/out/tree_rebuild_b21c_*.tar | head -1); mkdir -p $C/pkg; cd $C; sha256sum $T; stat -c %s $T
(cd pkg && tar xf $T)
for d in $W/w21/work/tree_r1 $C/pkg/work/tree_r1; do (cd $d && $P -c "import sys; sys.path.insert(0,'.'); from student_pilot.source_seal import inventory; from student_pilot.p3_provenance import digest; f=inventory('.'); print(len(f), digest(f))"); done
echo SEALDONE
ls $C/pkg/work | tr '\n' ' '; echo
cd $C/pkg && $P work/build21/focused.py > $C/focused_untar.log 2>&1; echo "focused_untar rc $?"; cat $C/pkg/work/build21/FINAL_CHECKS.json | tr -d '\n '; echo
for f in final_focused edges producer_edges; do tail -3 $C/pkg/work/build21/$f.log | tr '\n' ' '; echo; done
echo CFDONE
