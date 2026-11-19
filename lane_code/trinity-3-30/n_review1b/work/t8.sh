X=/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/x24l3_back; P=/scratch/jjyeung/envs/p1cpu/bin/python
cd $X/out; sha256sum *
echo "== seal of work/tree_r1"; cd $X/work/tree_r1 && nice -n 10 $P -I -s -B -c "import sys; sys.path.insert(0,'.'); from student_pilot.source_seal import inventory; from student_pilot.p3_provenance import digest; f=inventory('.'); print(len(f), digest(f))"
M=/scratch/jjyeung/orch_n30/n_review/r1b/t3; mkdir -p $M && tar xf $X/out/tree_rebuild_b24l3_96ff9a03.tar -C $M && ls $M | head
T3=$(dirname $(ls -d $M/*/student_pilot $M/student_pilot $M/*/*/student_pilot 2>/dev/null | head -1)); echo T3=$T3
cd $T3 && nice -n 10 $P -I -s -B -c "import sys; sys.path.insert(0,'.'); from student_pilot.source_seal import inventory; from student_pilot.p3_provenance import digest; f=inventory('.'); print(len(f), digest(f))"
cd /scratch/jjyeung/orch_n30/n_review && nice -n 10 $P -I -s -B r1b/fh.py $T3
echo "== reports"; cat $X/out/TREE24L3_SEAL.json; echo; head -c 4000 $X/out/UNCHANGED24L3.json; echo; cat $X/out/BUILD24L3_REPORT.md
