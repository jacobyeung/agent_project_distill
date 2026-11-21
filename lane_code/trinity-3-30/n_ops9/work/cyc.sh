#!/bin/bash
# wait up to $1 s for events/alerts, then stage witness extra.sh, let it run, print compact witness summary
L=/scratch/jjyeung/orch_n30/n_ops9; M=/scratch/jjyeung/orch_n30/n_ops1/work/mon
bash $L/work/wait.sh ${1:-480}
[ -e $M/extra.sh ] || cp $L/work/wit.sh $M/extra.sh
for i in $(seq 1 16); do sleep 10; [ -e $M/extra.sh ] || break; done; sleep 15
f=$(ls -t $M/extra.out.* | head -1); echo "== $f"
awk '/^--date/||/^r.log:|^q.log:/||/^\{"ok"/||/sha256=/||/missing|protected_keys/||/status/' $f | cut -c1-250
sed -n '/^--logtail/,/^--steps/p' $f | tail -8 | cut -c1-200
sed -n '/^== dr\/q.log/,$p' $f | tail -8 | cut -c1-200
