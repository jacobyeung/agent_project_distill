W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; J=$W/w26t5; T=$W/w26jn6f; date -u +%TZ; tmux kill-session -t tr26_t6d
test -e $J -o -e $T && { echo EXISTS; exit 1; }
mkdir -p $T && cd $T && tar xf - && sha256sum jn6.sh j6.py
cp -a $W/w24z13b $J && cp $T/jn6.sh $J/out/jn6.sh && mkdir -p $J/lane && cp $T/adapt.py $T/run26.sh $J/lane/ && /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B $J/lane/adapt.py $J
tmux new-session -d -s tr26_t6e "bash $J/lane/run26.sh $J"
timeout 500 bash $T/t6.sh $T > $T/t6.log 2>&1; echo T6_RC $?; grep 'rc=\|ALARM\|OOM_\|^limit\|TAIL_EQ\|LOOP_KILLED\|"phase"\|GATE\|gz\|skipped\|absent\|  [a-z_]*\.json$\|gate_copy' $T/t6.log | cut -c1-200
