<!-- recovered by seal_plan: transcript=71f94277 line=31805 utc=2026-11-14T14:24:39.257Z kind=commands original_path=(bash command)  -->
F=/scratch/jjyeung/orch_cd/evalx/work/milestone/s23/ifp0_aded62aed7218d81a/OBSERVATION_20261114T141443Z.json; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "
import json
d=json.load(open('$F'))
print(json.dumps(d['queue'])[:300])
a=d['allocation']; print(type(a), (list(a.keys())[:20] if isinstance(a,dict) else str(a)[:300]))
s=json.dumps(a)
import re
print(s[:1800])
"; cat /scratch/jjyeung/orch_cd/evalx/work/milestone/s23/ifp0_aded62aed7218d81a/GUARD_STATE.json | cut -c1-600