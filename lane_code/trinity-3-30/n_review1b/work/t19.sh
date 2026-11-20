W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; C=$W/w24c; P=/scratch/jjyeung/envs/p1cpu/bin/python; M=/scratch/jjyeung/orch_n30/n_review/r1b
seal(){ (cd $1 && nice -n 10 $P -I -s -B -c "import sys; sys.path.insert(0,'.'); from student_pilot.source_seal import inventory; from student_pilot.p3_provenance import digest; f=inventory('.'); print(len(f), digest(f))"); }
echo "== tree C seal (kit workspace)"; seal $C/work/tree_r1
ls -la $W/work/x24l4c_back $W/work/x24l4c_back/out; sha256sum $W/work/x24l4c_back/out/*.tar $C/out/tree_rebuild_b24m4c_b7be125e.tar
mkdir -p $M/tc && tar xf $W/work/x24l4c_back/out/tree_rebuild_b24l4_0c7614c8.tar -C $M/tc; TC=$(dirname $(ls -d $M/tc/*/*/student_pilot $M/tc/*/student_pilot $M/tc/student_pilot 2>/dev/null | head -1)); echo TC=$TC; seal $TC
cd /scratch/jjyeung/orch_n30/n_review && nice -n 10 $P -I -s -B r1b/fh.py $TC | grep -v '"student_pilot/r2_\|s1_routing' 
echo "== kit seals"; for k in $C/work/build24/kits/q $C/work/build24/kits/n $C/out/kit_n_go $C/out/kit_qd; do echo $k; cat $k/BUILD.json 2>/dev/null | head -c 400; echo; (cd $C/work/tree_r1 && nice -n 10 $P -I -s -B -c "import sys; sys.path.insert(0,'.'); from launch_r1.build import verify; print(verify('$k'))" 2>&1 | tail -1); done
ls $C/out | head -40
