W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; J=$W/w26t2; T=$W/w26jn6c; date -u +%TZ; free -g | sed -n 2p; test -e $J -o -e $T && { echo EXISTS; exit 1; }
mkdir -p $T && cd $T && tar xf - && sha256sum jn6.sh j6.py
cp -a $W/w24z13b $J && cp $T/jn6.sh $J/out/jn6.sh && mkdir -p $J/lane && cp $T/adapt.py $T/run26.sh $J/lane/ && /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B $J/lane/adapt.py $J
tmux new-session -d -s tr26_t6b "bash $J/lane/run26.sh $J"
timeout 400 bash $T/t6.sh $T > $T/t6.log 2>&1; echo T6_RC $?; grep 'rc=\|ALARM\|OOM_\|^job\|^limit\|TAIL_EQ\|LOOP_KILLED\|"phase"' $T/t6.log | cut -c1-200
echo OLD; cat $W/w26t/work/build26/DONE 2>&1; tail -2 $W/w26t/work/build26/tests.log | cut -c1-200; tail -2 $W/w26t/work/build26/extra.log 2>&1 | cut -c1-200
