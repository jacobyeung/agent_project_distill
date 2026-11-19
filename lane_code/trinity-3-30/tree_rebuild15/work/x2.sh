J=/scratch/jjyeung/orch_n30/tree_rebuild15_w24l; date -u +%TZ; tmux ls 2>/dev/null | grep tr15; ls $J $J/out $J/work
cd $J/work && diff -rq tree_r1_base tree_r1 | head -20
tail -5 $J/build24l_dispatch.log | cut -c1-200
