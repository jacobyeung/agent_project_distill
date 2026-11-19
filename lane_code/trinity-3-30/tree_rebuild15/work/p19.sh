O=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/out; K=$O/kit_n_go; date -u +%TZ
/usr/bin/python3 -I -s -B -c "import json,base64,sys; d=json.load(open('$K/k/j.json')); sys.stdout.write(base64.b64decode(d['payload']).decode())" > /tmp/tr15_j.sh; wc -l /tmp/tr15_j.sh
grep -n -E "Q_MODE|a\.py|bwrap|--bind|/tmp/q_22c714e1|tk_stage|mode" /tmp/tr15_j.sh | head -40 | cut -c1-300
RK=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24k; cat $RK/rehearsal_k_run1.log | grep -v "^\s*$" | head -30 | cut -c1-400
ls $RK/rehearsal_k 2>/dev/null | tr '\n' ' '; echo
for f in $(ls -t $RK/rehearsal_k/*.log 2>/dev/null | head -3); do echo "== $f"; tail -12 $f | cut -c1-400; done
test -f $RK/rehearsal_k/p2/q/RESULT.json && head -c 2000 $RK/rehearsal_k/p2/q/RESULT.json
