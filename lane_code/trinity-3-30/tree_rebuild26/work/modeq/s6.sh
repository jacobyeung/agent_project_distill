W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
K=$W/w24z8b/out/kit_qdp; G=$W/w24z11b/a_zffhb1q8/armed/kits/n_go
T=$K/k/t_e047002134f979bd.tar
for k in $K $G; do echo "=====CFG $k"; python3 -I - $k <<'PY'
import json,base64,sys
from pathlib import Path
k=Path(sys.argv[1])
def L(p):
  v=json.loads(p.read_text())
  if isinstance(v,dict) and v.get('encoding'): v=json.loads(base64.b64decode(v['payload']))
  return v
c=L(k/'k/c.json'); t=c.get('r1_training',{})
print('world_size',c.get('world_size'),'proof_mode',t.get('proof_mode'),'init_policy',t.get('init_policy'),'remove_files',bool(c.get('remove_files')),'r2_all',bool(c.get('r2_all_stream_exclusions')),'twins',t.get('direction_twins') is not None)
h=L(k/'k/h.json'); print('h keys',sorted(h)); print({x:h.get(x) for x in ('weights','device','memory_gib','milestone')})
a=L(k/'k/a.json'); print('a',{x:a.get(x) for x in ('GO','discovery','review_wait_seconds')})
for n in ('r.json','y.json','8.json'):
  p=k/'k'/n
  if p.exists():
    v=L(p); print(n, json.dumps(v)[:400])
PY
done
echo =====CCR; tar xOf $T student_pilot/carrier_c1_run.py | grep -n "^def first_batch_check\|^def fetch\|^def check_plan_rows\|^def processor_for_receipt\|encode_frames\|encode_layout_row\|^from \|^import " | cut -c1-220 | head -60
echo =====ENTRY; tar xOf $T launch_r1/entry.py | grep -n "def \|tmp\|TMPDIR\|environ" | cut -c1-220 | head -80
echo =====ADMIT; tar tf $T | grep -E "s1_admission|r1_loader|r1_population" ; tar xOf $T student_pilot/s1_admission.py 2>/dev/null | grep -n "memory_gib\|def admit\|prepare_only\|MemoryError\|resource\.\|RLIMIT\|tmp" | cut -c1-220 | head -40
