J=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w28jn7
n=0; while [ ! -e $J/t7c.DONE ] && [ $n -lt 50 ]; do sleep 10; n=$((n+1)); done
date -u; ls $J/t7c.DONE; grep -v '^  ok ' $J/t7c.log
