W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; PY=/scratch/jjyeung/envs/p1cpu/bin/python; date -u +%TZ; P=$W/w24t/work/build24m4o/p_tree
cd $P && ls student_pilot/source_seal.py student_pilot/p3_provenance.py 2>&1; nice -n 10 $PY -I -s -B -c "import sys; sys.path.insert(0,'.'); from student_pilot.source_seal import inventory; from student_pilot.p3_provenance import digest; f=inventory('.'); print('p_tree',len(f), digest(f))" 2>&1 | tail -2
cd /scratch/jjyeung/orch_n30/n_review/r1e/tcpp && nice -n 10 $PY -I -s -B -c "import sys; sys.path.insert(0,'.'); from student_pilot.source_seal import inventory; from student_pilot.p3_provenance import digest; f=inventory('$P'); print('p_tree by C2 fn',len(f), digest(f))" 2>&1 | tail -2
ls $W/w24v $W/w24v/out 2>&1 | tail -8
