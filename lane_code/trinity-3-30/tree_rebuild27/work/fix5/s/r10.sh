J=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w28jn7
date -u; ls $J/t7.DONE $J/work/build27/DONE 2>&1; cat $J/t7.log
echo "=== tests.log"; grep -c PASS\" $J/work/build27/tests.log 2>/dev/null; grep -v '"PASS": true' $J/work/build27/tests.log | cut -c1-400 | tail -20
echo "=== extra"; grep -v '"PASS": true' $J/work/build27/extra.log 2>/dev/null | cut -c1-400 | tail -10
