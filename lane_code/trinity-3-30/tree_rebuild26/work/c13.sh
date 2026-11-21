W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; J=$W/w26t; date -u +%TZ; test -e $J && { echo EXISTS; exit 1; }
cp -a $W/w24z13b $J && cp $W/w26jn6b/jn6.sh $J/out/jn6.sh && sha256sum $J/out/jn6.sh $J/out/jn5.sh | cut -c1-16
mkdir -p $J/lane && cd $J/lane && tar xf - && /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B adapt.py $J && diff $J/work/build24m4z13b/test_jn5.py $J/work/build26/test_jn6.py | head -40
tmux new-session -d -s tr26_t6 "bash $J/lane/run26.sh"; sleep 30; tail -3 $J/work/build26/tests.log | cut -c1-200
