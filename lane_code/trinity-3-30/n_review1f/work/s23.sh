W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; PY=/scratch/jjyeung/envs/p1cpu/bin/python; date -u +%TZ
for t in $W/w24t/work/tree_r1_base; do (cd $t && nice -n 10 $PY -I -s -B -c "import sys; sys.path.insert(0,'.'); from student_pilot.source_seal import inventory; from student_pilot.p3_provenance import digest; f=inventory('.'); print('$t',len(f), digest(f))"); done
P=$W/w24t/work/tree_r1_base; ls $P/student_pilot/extent_receipt.py 2>&1; grep -n -i "extent" $P/student_pilot/s1_routing.py $P/student_pilot/carrier_c1_run.py | head -20; sed -n 1066,1085p $P/student_pilot/carrier_c1_run.py
grep -rln "b83a8a35" $W/w24t/out/*.md 2>/dev/null | head -5; grep -h -o ".\{80\}b83a8a35.\{60\}" $W/w24t/out/BUILD24M4T_REPORT.md $W/w24t/out/CHAIN_24M4Q.md 2>/dev/null | head -4
