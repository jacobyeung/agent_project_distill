G=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z11b/a_zffhb1q8/armed/kits/n_go; P=/scratch/jjyeung/envs/p1cpu/bin/python
$P -I -s -B - "$G" <<'PY'
import base64,hashlib,json,sys
from pathlib import Path
G=Path(sys.argv[1])
for name in ('k/j.json',):
    v=json.loads((G/name).read_text())
    r=base64.b64decode(v['payload'],validate=True) if isinstance(v,dict) and 'payload' in v else None
    s=r.decode() if r else json.dumps(v)
    try:
        d=json.loads(s); s=d if isinstance(d,str) else json.dumps(d)
    except Exception: pass
    L=s.split('\n'); print(name,len(L),'lines')
    for i,l in enumerate(L,1):
        if any(k in l for k in ('a.py','t.py','torchrun','ulimit','rv.py','h.py','e.sh','setrlimit')): print(i,l[:220])
PY
echo ===t.py; cat -n $G/b/t.py | cut -c1-300; echo ===e.sh; cat -n $G/b/e.sh | cut -c1-200 | head -30
T=$G/k/t_e047002134f979bd.tar; m=$(tar tf $T | grep 'launch_r1/entry.py$'); echo "== $m"; tar xOf $T $m | grep -n 'def admit\|s1_admission\|setrlimit\|RLIMIT\|subprocess\|torch.distributed\|def frame_host' | head -20
m=$(tar tf $T | grep 'student_pilot/s1_admission.py$'); tar xOf $T $m | grep -n 'torch.cuda\|is_available\|device_count' | head
for f in carrier_c1_run.py r1_population.py rehearsal.py carrier_c1_data.py; do m=$(tar tf $T | grep "student_pilot/$f$"); echo "-- $f"; tar xOf $T $m | grep -n 'torch.cuda.is_available\|torch.cuda.device_count\|setrlimit' | head -5; done
