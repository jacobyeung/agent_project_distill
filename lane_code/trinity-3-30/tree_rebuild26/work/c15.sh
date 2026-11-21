W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; J=$W/w26t3; T=$W/w26jn6d; date -u +%TZ; tmux kill-session -t tr26_t6b; tmux kill-session -t tr26_t6; sleep 1; pgrep -f 'w26t/work|w26t2/work' | wc -l
test -e $J -o -e $T && { echo EXISTS; exit 1; }
mkdir -p $T && cd $T && tar xf - && sha256sum jn6.sh j6.py
cp -a $W/w24z13b $J && cp $T/jn6.sh $J/out/jn6.sh && mkdir -p $J/lane && cp $T/adapt.py $T/run26.sh $J/lane/ && /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B $J/lane/adapt.py $J
tmux new-session -d -s tr26_t6c "bash $J/lane/run26.sh $J"
timeout 400 bash $T/t6.sh $T > $T/t6.log 2>&1; echo T6_RC $?; grep 'rc=\|ALARM\|OOM_\|^job\|^limit\|TAIL_EQ\|LOOP_KILLED\|"phase"' $T/t6.log | cut -c1-200
