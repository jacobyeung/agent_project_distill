W=/scratch/jjyeung/orch_n30/tree_rebuild10_w/work; date -u +%TZ
for J in 173717 173724 173725 173754 173796 173817; do L=$W/d$J/$J/job.log; echo "=== $J $(ls $L 2>&1 | head -1)"; grep -n "find source path\|R1_PLAN_REFUSED\|R1_SCENE_BIND\|EROFS\|Read-only file system\|scene rebuild seconds\|routing seen\|R1_PUBLICATION\|EXTENT_ROW_UNAUDITED\|E96:tree\|mode r .*seconds\|work exit" $L | grep -v '{"source\|remove_list' | head -8 | cut -c1-260; done
ls $W/d173717/173717 | tr '\n' ' '
