W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; K=$W/w28fix/n_go; T=/scratch/jjyeung/orch_n30/n_review/r1f/tcpx
(cd $T && /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "import sys; sys.path.insert(0,'.'); from launch_r1.build import verify; print('verify',verify('$K'))" < /dev/null 2>&1 | tail -1)
diff -rq $W/w27fix/n_go $K < /dev/null; sha256sum $W/w28fix/s28fix_n_go.tar $K/b/a.py $K/b/mg.py < /dev/null
grep -n "str(" $T/launch_r1/production_proof.py < /dev/null | cut -c1-160
