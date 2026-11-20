W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ
for J in 173725 173754 173796; do D=$W/work/d$J/$J; echo "=== $J"; ls $D | tr '\n' ' '; echo
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - $D <<'PY'
import json,sys,os
D=sys.argv[1]; t=json.load(open(D+'/timings.json'))
for k in ('returncode','post_returncode','aggregate_limit_status','aggregate_publication_bytes','helper_limit_status','helper_publication_bytes','publication_errors','log_tail_errors','routing_types','routing_types_refusal','nsample','task_a','proc_status','rdiff_status'):
    if k in t: print(k, json.dumps(t[k])[:700])
PY
grep -n "R1_PUBLICATION\|ValueError\|E9[0-9]\|Traceback\|exceeds\|budget" $D/job.log | grep -v '{"source\|remove_list' | tail -12 | cut -c1-300
done
