J=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w28jn7; T=$J/t7
date; cat $J/t7.log; ls -la $T/x/o/991001 2>&1; cat $T/res/H1.out; ls -la $T/tmp_991001/q_22c714e1_991001 2>&1 | head -30; cat $T/tmp_991001/q_22c714e1_991001/j2.log
ps -eo pid,pgid,etime,args | grep -v grep | grep -e 991001 -e 't7.sh' | cut -c1-200 | head -20
echo "=== tests tail"; tail -3 $J/work/build27/tests.log | cut -c1-300
