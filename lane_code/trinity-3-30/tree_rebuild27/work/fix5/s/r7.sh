J=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w28jn7
tmux ls 2>&1 | grep fix5; ls $J $J/work/build27 | head -60
echo "=== t7.log"; cat $J/t7.log 2>&1 | head -150
echo "=== tests.log"; tail -c 3000 $J/work/build27/tests.log 2>&1
