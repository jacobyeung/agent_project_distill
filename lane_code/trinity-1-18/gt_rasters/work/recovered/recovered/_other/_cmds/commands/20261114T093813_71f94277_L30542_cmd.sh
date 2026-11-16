<!-- recovered by seal_plan: transcript=71f94277 line=30542 utc=2026-11-14T09:38:13.739Z kind=commands original_path=(bash command)  -->
D=/scratch/jjyeung/orch_cd/leg_s1_canary/out; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'EOF'
import json,tarfile,hashlib,io
d=json.load(open('/scratch/jjyeung/orch_cd/leg_s1_canary/out/CONTINUATION_DELIVERY_20261114T092849Z.json'))
print({k:(v if not isinstance(v,(dict,list)) else type(v).__name__+str(len(v))) for k,v in d.items()})
t=tarfile.open('/scratch/jjyeung/orch_cd/leg_s1_canary/out/continuation_check_20261114T092849Z.tgz')
names=[m.name for m in t.getmembers()]
print(len(names)); print([n for n in names if n.endswith('.py')][:40])
m=[n for n in names if n.endswith('loss_alarm.py')][0]
src=t.extractfile(m).read().decode()
print(hashlib.sha256(src.encode()).hexdigest()[:16])
for i,l in enumerate(src.splitlines(),1):
    if 'skipped' in l or 'def ' in l: print(i,l[:200])
EOF