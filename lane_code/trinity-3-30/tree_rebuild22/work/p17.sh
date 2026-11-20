D=/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/d173817/173817; cd $D; date -u +%TZ
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'PY'
import json
n=json.load(open('nd.json'))
print('CFC', json.dumps(n['content_field_counts'])[:2500])
print('PATHS_KEYS', list(n['paths'])[:15])
ex=n['content_examples']; print('EX', json.dumps(ex)[:1500])
PY
grep -n "task_i\b\|task_i_content\|def task\|criterion" /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24x2/out/rcj/nd.py | head -20 | cut -c1-250
