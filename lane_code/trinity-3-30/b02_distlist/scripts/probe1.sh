cd /scratch/jjyeung/orch_n30/native_r2/work || exit 1
ls -la full_c8r/ full_c8r/x full_c8r/x/native | head -40
T=meta/sj/orch_cd/legs1_reads/work/vendor/r3
ls -la $T parent/r3 2>&1 | head -20
sha256sum $T/TASKS.jsonl $T/FRAMES.json full_c8r/x/native/R1.json full_c8r/result.tar.gz
/scratch/jjyeung/orch_n30/native_r2/env312/bin/python3.12 -I -s -B - <<'PY'
import json
T='meta/sj/orch_cd/legs1_reads/work/vendor/r3/TASKS.jsonl'
rows=[json.loads(l) for l in open(T)]
print('TASKS rows',len(rows)); 
from collections import Counter
print(Counter(r.get('question_type') for r in rows))
d=[r for r in rows if r.get('question_type')=='object_abs_distance']
print(json.dumps(d[0])[:1500]); print(json.dumps([r for r in rows if r.get('question_type')=='room_size_estimation'][0])[:800])
R=json.load(open('full_c8r/x/native/R1.json'))
def sk(o,dep=0,pre=''):
    if dep>3: return
    if isinstance(o,dict):
        for k,v in list(o.items())[:25]:
            print(pre+k, type(v).__name__, (len(v) if hasattr(v,'__len__') else v) if not isinstance(v,(int,float)) else v)
            sk(v,dep+1,pre+'  ')
    elif isinstance(o,list) and o:
        sk(o[0],dep+1,pre+'  [0] ')
sk(R)
PY
